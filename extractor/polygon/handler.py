from collections import defaultdict
from typing import Any, Dict, List

from config.constants import ZERO_ADDRESS, Bridge
from extractor.base_handler import BaseHandler
from extractor.polygon.constants import (
    BRIDGE_CONFIG,
    ETHER_ROOT_TOKEN,
    ROOT_CHAIN_MANAGER,
    ROOT_TO_CHILD_TOKEN_SELECTOR,
    TOPIC_ADDRESS_CHUNK_SIZE,
)
from repository.database import DBSession
from repository.polygon.repository import (
    PolygonBlockchainTransactionRepository,
    PolygonBridgeWithdrawRepository,
    PolygonChildTokenBurnRepository,
    PolygonExitedTokenRepository,
    PolygonLockedTokenRepository,
    PolygonNewDepositBlockRepository,
    PolygonPOLWithdrawRepository,
    PolygonStateCommittedRepository,
    PolygonStateSyncedRepository,
    PolygonTokenDepositedRepository,
)
from rpcs.evm_rpc_client import EvmRPCClient
from utils.utils import CustomException, log_error


class PolygonHandler(BaseHandler):
    CLASS_NAME = "PolygonHandler"

    def __init__(self, rpc_client: EvmRPCClient, blockchains: list) -> None:
        super().__init__(rpc_client, blockchains)
        self.bridge = Bridge.POLYGON
        self._root_to_child_token_cache = {}

    def get_bridge_contracts_and_topics(self, bridge: str, blockchain: List[str]) -> None:
        """
        Validates the mapping between the bridge and the blockchains.

        Args:
            bridge: The bridge to validate.
            blockchain: The blockchain to validate.
        """

        if blockchain not in BRIDGE_CONFIG["blockchains"]:
            raise ValueError(f"Blockchain {blockchain} not supported for bridge {bridge}.")

        config = BRIDGE_CONFIG["blockchains"][blockchain]
        if blockchain == "polygon":
            config = self._replace_static_erc20_burn_contracts(config)

        return config

    def _replace_static_erc20_burn_contracts(self, config):
        dynamic_config = []

        for pair in config:
            if pair["abi"] != "erc20":
                dynamic_config.append(pair)
                continue

            dynamic_config.extend(self._build_child_token_burn_pairs(pair["topics"]))

        return dynamic_config

    def _build_child_token_burn_pairs(self, topics):
        root_token_exitors = self.exited_token_repo.get_distinct_root_token_exitors()
        if not root_token_exitors:
            return []

        if "ethereum" not in self.rpc_client.rpc_mapping:
            log_error(
                self.bridge,
                "Skipping Polygon child-token burn extraction: Ethereum RPC config is unavailable.",
            )
            return []

        root_to_exitors = defaultdict(set)
        for root_token, exitor in root_token_exitors:
            if root_token and exitor:
                root_to_exitors[root_token.lower()].add(exitor.lower())

        root_token_mappings = []
        for root_token, exitors in root_to_exitors.items():
            child_token = self._resolve_child_token(root_token.lower())
            if child_token is None:
                continue

            root_token_mappings.append((root_token, child_token, exitors))

        burn_pairs = []
        for root_token, child_token, exitors in sorted(root_token_mappings):
            exitor_topics = [self._address_to_topic(exitor) for exitor in sorted(exitors)]
            for exitor_topic_chunk in self._chunk(exitor_topics, TOPIC_ADDRESS_CHUNK_SIZE):
                burn_pairs.append(
                    {
                        "abi": "erc20",
                        "contracts": [child_token],
                        "topics": [
                            topics[0],
                            exitor_topic_chunk,
                            topics[2],
                        ],
                        "root_token": root_token,
                    }
                )

        return burn_pairs

    def _resolve_child_token(self, root_token):
        if root_token in self._root_to_child_token_cache:
            return self._root_to_child_token_cache[root_token]

        try:
            data = ROOT_TO_CHILD_TOKEN_SELECTOR + root_token[2:].rjust(64, "0")
            result = self.rpc_client.eth_call("ethereum", ROOT_CHAIN_MANAGER, data)
            child_token = self._decode_address_result(result)
            self._root_to_child_token_cache[root_token] = child_token
            return child_token
        except Exception as e:
            self._root_to_child_token_cache[root_token] = None
            log_error(
                self.bridge,
                f"Could not resolve Polygon child token for root token {root_token}: {e}",
            )
            return None

    def _decode_address_result(self, result):
        if not result or result == "0x":
            return None

        child_token = "0x" + result[-40:]
        if child_token.lower() == ZERO_ADDRESS:
            return None

        return child_token.lower()

    def _address_to_topic(self, address):
        return "0x" + address[2:].rjust(64, "0")

    def _chunk(self, values, chunk_size):
        for i in range(0, len(values), chunk_size):
            yield values[i : i + chunk_size]

    def bind_db_to_repos(self):
        self.state_synced_repo = PolygonStateSyncedRepository(DBSession)
        self.state_committed_repo = PolygonStateCommittedRepository(DBSession)
        self.locked_token_repo = PolygonLockedTokenRepository(DBSession)
        self.exited_token_repo = PolygonExitedTokenRepository(DBSession)
        self.child_token_burn_repo = PolygonChildTokenBurnRepository(DBSession)
        self.new_deposit_block_repo = PolygonNewDepositBlockRepository(DBSession)
        self.token_deposited_repo = PolygonTokenDepositedRepository(DBSession)
        self.pol_withdraw_repo = PolygonPOLWithdrawRepository(DBSession)
        self.bridge_withdraw_repo = PolygonBridgeWithdrawRepository(DBSession)
        self.blockchain_transaction_repo = PolygonBlockchainTransactionRepository(DBSession)

    def handle_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        func_name = "handle_transactions"
        try:
            self.blockchain_transaction_repo.create_all(transactions)
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"Error writing transactions to database: {e}",
            ) from e

    def does_transaction_exist_by_hash(self, transaction_hash: str) -> Any:
        func_name = "does_transaction_exist_by_hash"
        """
        Retrieves a transaction by its hash from the database.

        Args:
            transaction_hash: The hash of the transaction to retrieve.

        Returns:
            The transaction with the given hash.
        """
        try:
            return self.blockchain_transaction_repo.get_transaction_by_hash(transaction_hash)
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"Error reading transaction from database: {e}",
            ) from e

    def handle_events(
        self,
        blockchain: str,
        start_block: int,
        end_block: int,
        contract: str,
        topics: List[str],
        events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        included_events = []

        for event in events:
            try:
                if (
                    event["topic"]
                    == "0x103fed9db65eac19c4d870f49ab7520fe03b99f1838e5996caf47e9e43308392"
                ):  # StateSynced
                    event = self.handle_state_synced(blockchain, event)
                elif (
                    event["topic"]
                    == "0x5a22725590b0a51c923940223f7458512164b1113359a735e86e7f27f44791ee"
                ):  # StateCommitted
                    event = self.handle_state_committed(blockchain, event)
                elif (
                    event["topic"]
                    == "0x9b217a401a5ddf7c4d474074aff9958a18d48690d77cc2151c4706aa7348b401"
                ):  # LockedERC20
                    event = self.handle_locked_erc20(blockchain, event)
                elif (
                    event["topic"]
                    == "0xbb61bd1b26b3684c7c028ff1a8f6dabcac2fac8ac57b66fa6b1efb6edeab03c4"
                ):  # ExitedERC20
                    event = self.handle_exited_erc20(blockchain, event)
                elif (
                    event["topic"]
                    == "0x3e799b2d61372379e767ef8f04d65089179b7a6f63f9be3065806456c7309f1b"
                ):  # LockedEther
                    event = self.handle_locked_ether(blockchain, event)
                elif (
                    event["topic"]
                    == "0x0fc0eed41f72d3da77d0f53b9594fc7073acd15ee9d7c536819a70a67c57ef3c"
                ):  # ExitedEther
                    event = self.handle_exited_ether(blockchain, event)
                elif (
                    event["topic"]
                    == "0x1dadc8d0683c6f9824e885935c1bec6f76816730dcec148dda8cf25a7b9f797b"
                ):  # NewDepositBlock
                    event = self.handle_new_deposit_block(blockchain, event)
                elif (
                    event["topic"]
                    == "0xfeb2000dca3e617cd6f3a8bbb63014bb54a124aac6ccbf73ee7229b4cd01f120"
                ):  # Withdraw
                    event = self.handle_bridge_withdraw(blockchain, event)
                elif (
                    event["topic"]
                    == "0xec3afb067bce33c5a294470ec5b29e6759301cd3928550490c6d48816cdc2f5d"
                ):  # TokenDeposited
                    event = self.handle_token_deposited(blockchain, event)
                elif (
                    event["topic"]
                    == "0xebff2602b3f468259e1e99f613fed6691f3a6526effe6ef3e768ba7ae7a36c4f"
                ):  # Withdraw
                    event = self.handle_pol_withdraw(blockchain, event)
                elif (
                    event["topic"]
                    == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):  # Transfer (to 0x0)
                    event = self.handle_child_token_burn(blockchain, event)

                if event:
                    included_events.append(event)

            except CustomException as e:
                request_desc = (
                    f"Error processing request: {blockchain}, {start_block}, "
                    f"{end_block}, {contract}, {topics}.\n{e}"
                )
                log_error(self.bridge, request_desc)

        return included_events

    def handle_state_synced(self, blockchain, event):
        func_name = "handle_state_synced"

        try:
            if self.state_synced_repo.event_exists(event["id"]):
                return None

            self.state_synced_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "state_id": event["id"],
                    "contract_address": event["contractAddress"].lower(),
                    "data": event["data"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_state_committed(self, blockchain, event):
        func_name = "handle_state_committed"

        try:
            if self.state_committed_repo.event_exists(event["stateId"]):
                return None

            self.state_committed_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "state_id": event["stateId"],
                    "success": event["success"],
                }
            )
            return event

        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_locked_erc20(self, blockchain, event):
        func_name = "handle_locked_erc20"

        try:
            self.locked_token_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "depositor": event["depositor"].lower(),
                    "deposit_receiver": event["depositReceiver"].lower(),
                    "root_token": event["rootToken"].lower(),
                    "amount": event["amount"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_exited_erc20(self, blockchain, event):
        func_name = "handle_exited_erc20"

        try:
            self.exited_token_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "exitor": event["exitor"].lower(),
                    "root_token": event["rootToken"].lower(),
                    "amount": event["amount"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_child_token_burn(self, blockchain, event):
        func_name = "handle_child_token_burn"

        try:
            if event["topics_count"] != 3:
                return None

            if event["to"].lower() != ZERO_ADDRESS:
                return None

            amount = event.get("value", event.get("amount"))
            if amount is None:
                return None

            raw_log_index = event["log_index"]
            log_index = int(raw_log_index, 16) if isinstance(raw_log_index, str) else raw_log_index
            if self.child_token_burn_repo.event_exists(event["transaction_hash"], log_index):
                return None

            self.child_token_burn_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "log_index": log_index,
                    "root_token": event.get("root_token"),
                    "child_token": event["contract_address"].lower(),
                    "from_address": event["from"].lower(),
                    "amount": amount,
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_locked_ether(self, blockchain, event):
        func_name = "handle_locked_ether"

        try:
            self.locked_token_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "depositor": event["depositor"].lower(),
                    "deposit_receiver": event["depositReceiver"].lower(),
                    "root_token": ETHER_ROOT_TOKEN,
                    "amount": event["amount"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_exited_ether(self, blockchain, event):
        func_name = "handle_exited_ether"

        try:
            self.exited_token_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "exitor": event["exitor"].lower(),
                    "root_token": ETHER_ROOT_TOKEN,
                    "amount": event["amount"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_new_deposit_block(self, blockchain, event):
        func_name = "handle_new_deposit_block"

        try:
            if self.new_deposit_block_repo.event_exists(event["depositBlockId"]):
                return None

            self.new_deposit_block_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "owner": event["owner"].lower(),
                    "token": event["token"].lower(),
                    "amount": event["amountOrNFTId"],
                    "deposit_block_id": event["depositBlockId"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_bridge_withdraw(self, blockchain, event):
        func_name = "handle_bridge_withdraw"

        try:
            self.bridge_withdraw_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "exit_id": event["exitId"],
                    "user": event["user"].lower(),
                    "token": event["token"].lower(),
                    "amount": event["amount"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_token_deposited(self, blockchain, event):
        func_name = "handle_token_deposited"

        try:
            if self.token_deposited_repo.event_exists(event["depositCount"]):
                return None

            self.token_deposited_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "root_token": event["rootToken"].lower(),
                    "child_token": event["childToken"].lower(),
                    "user": event["user"].lower(),
                    "amount": event["amount"],
                    "deposit_count": event["depositCount"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_pol_withdraw(self, blockchain, event):
        func_name = "handle_pol_withdraw"

        try:
            self.pol_withdraw_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "token": event["token"].lower(),
                    "from_address": event["from"].lower(),
                    "amount": event["amount"],
                    "input1": event["input1"],
                    "output1": event["output1"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e
