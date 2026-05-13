from typing import Any, Dict, List

from config.constants import Bridge
from extractor.base_handler import BaseHandler
from extractor.nomad.constants import BRIDGE_CONFIG
from repository.database import DBSession
from repository.nomad.repository import (
    NomadBlockchainTransactionRepository,
    NomadEthHelperSendRepository,
    NomadHomeDispatchRepository,
    NomadReplicaProcessRepository,
    NomadRouterReceiveRepository,
    NomadRouterSendRepository,
)
from rpcs.evm_rpc_client import EvmRPCClient
from utils.utils import CustomException, log_error

# Nomad protocol domain IDs (0x657468="eth", 0x6265616d="beam")
NOMAD_DOMAIN_IDS = {
    6648936: "ethereum",
    1650811245: "moonbeam",
    1702260083: "evmos",
    25393: "milkomeda", # Milkomeda C1
    1635148152: "avalanche",
    2019844457: "gnosis"
}


class NomadHandler(BaseHandler):
    CLASS_NAME = "NomadHandler"

    def __init__(self, rpc_client: EvmRPCClient, blockchains: list) -> None:
        super().__init__(rpc_client, blockchains)
        self.bridge = Bridge.NOMAD

    def get_bridge_contracts_and_topics(self, bridge: str, blockchain: List[str]) -> None:
        return super().get_bridge_contracts_and_topics(
            config=BRIDGE_CONFIG,
            bridge=bridge,
            blockchain=blockchain,
        )

    def bind_db_to_repos(self):
        self.blockchain_transaction_repo = NomadBlockchainTransactionRepository(DBSession)
        self.router_send_repo = NomadRouterSendRepository(DBSession)
        self.router_receive_repo = NomadRouterReceiveRepository(DBSession)
        self.eth_helper_send_repo = NomadEthHelperSendRepository(DBSession)
        self.replica_process_repo = NomadReplicaProcessRepository(DBSession)
        self.home_dispatch_repo = NomadHomeDispatchRepository(DBSession)

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
                    == "0xa3d219cf126a12be40d7ad1ceef46231c987988dd4e686457b610e1b6b80a4bf"
                ):  # Send(address indexed token, address indexed from, uint32 indexed toDomain, 
                    # bytes32 toId, uint256 amount, bool toHook)
                    event = self.handle_router_send(blockchain, event)
                elif (
                    event["topic"]
                    == "0x9f9a97db84f39202ca3b409b63f7ccf7d3fd810e176573c7483088b6f181bbbb"
                ):  # Receive(uint64 indexed originAndNonce, address indexed token, 
                    # address indexed recipient, address liquidityProvider, uint256 amount)
                    event = self.handle_router_receive(blockchain, event)
                elif (
                    event["topic"]
                    == "0x7d4b3c5c44bd8008199bb99f184426274cf24f917f4da3485d6a39f894366b10"
                ):  # Send(address indexed from)
                    event = self.handle_eth_helper_send(blockchain, event)
                elif (
                    event["topic"]
                    == "0xd42de95a9b26f1be134c8ecce389dc4fcfa18753d01661b7b361233569e8fe48"
                ):  # Process(bytes32 indexed messageHash, bool indexed success,
                    # bytes indexed returnData)
                    event = self.handle_replica_process(blockchain, event)
                elif (
                    event["topic"]
                    == "0x9d4c83d2e57d7d381feb264b44a5015e7f9ef26340f4fc46b558a6dc16dd811a"
                ):  # Dispatch(bytes32 messageHash, uint256 leafIndex, uint64 destinationAndNonce,
                    # bytes32 committedRoot, bytes message)
                    event = self.handle_home_dispatch(blockchain, event)

                if event:
                    included_events.append(event)

            except CustomException as e:
                request_desc = (
                    f"Error processing request: {blockchain}, {start_block}, "
                    f"{end_block}, {contract}, {topics}.\n{e}"
                )
                log_error(self.bridge, request_desc)

        return included_events

    def _domain_to_blockchain(self, domain: int) -> str | None:
        return NOMAD_DOMAIN_IDS.get(domain)

    def handle_router_send(self, blockchain, event):
        func_name = "handle_router_send"

        try:
            dst_blockchain = self._domain_to_blockchain(int(event["toDomain"]))
            if dst_blockchain is None:
                return None

            if self.router_send_repo.event_exists(event["transaction_hash"]):
                return None

            self.router_send_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "input_token": event["token"],
                    "depositor": event["from"],
                    "dst_blockchain": dst_blockchain,
                    "recipient": "0x" + event["toId"][-40:],
                    "amount": event["amount"],
                    "to_hook": int(event["toHook"]) if "toHook" in event else None,
                    "fast_liquidity_enabled": int(event["fastLiquidityEnabled"]) \
                        if "fastLiquidityEnabled" in event else None,
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_router_receive(self, blockchain, event):
        func_name = "handle_router_receive"

        try:
            origin_and_nonce = int(event["originAndNonce"])
            origin_domain = (origin_and_nonce >> 32) & 0xFFFFFFFF
            nonce = origin_and_nonce & 0xFFFFFFFF

            src_blockchain = self._domain_to_blockchain(origin_domain)
            if src_blockchain is None:
                return None

            if self.router_receive_repo.event_exists(nonce, blockchain, src_blockchain):
                return None

            self.router_receive_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "src_blockchain": src_blockchain,
                    "nonce": nonce,
                    "output_token": event["token"],
                    "recipient": event["recipient"],
                    "liquidity_provider": event["liquidityProvider"],
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

    def handle_eth_helper_send(self, blockchain, event):
        func_name = "handle_eth_helper_send"

        try:
            if self.eth_helper_send_repo.event_exists(event["transaction_hash"]):
                return None

            self.eth_helper_send_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "from_address": event["from"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_replica_process(self, blockchain, event):
        func_name = "handle_replica_process"

        try:
            message_hash = event["messageHash"]

            if self.replica_process_repo.event_exists(message_hash, blockchain):
                return None

            self.replica_process_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "message_hash": message_hash,
                    "success": int(event["success"]),
                    "return_data": event["returnData"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_home_dispatch(self, blockchain, event):
        func_name = "handle_home_dispatch"

        try:
            message_hash = event["messageHash"]

            if self.home_dispatch_repo.event_exists(message_hash, blockchain):
                return None

            destination_and_nonce = int(event["destinationAndNonce"])
            dst_domain = (destination_and_nonce >> 32) & 0xFFFFFFFF
            nonce = destination_and_nonce & 0xFFFFFFFF

            dst_blockchain = self._domain_to_blockchain(dst_domain)
            if dst_blockchain is None:
                return None

            # Nomad message layout (abi.encodePacked, no version byte):
            # [0:4]    origin      (uint32, big-endian)
            # [4:36]   sender/src_router  (bytes32, address right-aligned)
            # [36:40]  nonce       (uint32)
            # [40:44]  destination (uint32)
            # [44:76]  recipient/dst_router (bytes32, address right-aligned)
            # [76:]    body
            #
            # Body layout (BridgeMessage.formatMessage = tokenId || action):
            # [76:80]   tokenId.domain  (uint32)
            # [80:112]  tokenId.id      (bytes32, address right-aligned)
            # [112]     action type     (0x01=Transfer, 0x03=FastTransfer)
            # [113:145] recipient       (bytes32, address right-aligned)
            # [145:177] amount          (uint256)
            # [177:209] details hash    (bytes32)
            message_hex = event["message"]
            msg = bytes.fromhex(message_hex[2:] if message_hex.startswith("0x") else message_hex)

            src_domain = int.from_bytes(msg[0:4], "big")
            src_blockchain = self._domain_to_blockchain(src_domain)
            if src_blockchain is None:
                return None

            src_router = "0x" + msg[16:36].hex()   # last 20 bytes of msg[4:36]
            dst_router = "0x" + msg[56:76].hex()   # last 20 bytes of msg[44:76]

            token_domain = int.from_bytes(msg[76:80], "big")
            token_blockchain = self._domain_to_blockchain(token_domain)
            if token_blockchain is None:
                return None

            # For precaution, only process if message has the expected length 
            # to avoid out-of-range errors.
            if len(msg) >= 209:
                token_address = "0x" + msg[92:112].hex()   # last 20 bytes of msg[80:112]
                action_type = msg[112]      # 0=Transfer, 1=FastTransfer, 2=TransferToHook
                recipient = "0x" + msg[125:145].hex()       # last 20 bytes of msg[113:145]
                amount = int.from_bytes(msg[145:177], "big")
                details_hash = "0x" + msg[177:209].hex()

            self.home_dispatch_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": event["transaction_hash"],
                    "message_hash": message_hash,
                    "leaf_index": event["leafIndex"],
                    "nonce": nonce,
                    "committed_root": event["committedRoot"],
                    "src_blockchain": src_blockchain,
                    "src_router": src_router,
                    "dst_blockchain": dst_blockchain,
                    "dst_router": dst_router,
                    "token_blockchain": token_blockchain,
                    "token_address": token_address,
                    "action_type": action_type,
                    "recipient": recipient,
                    "amount": amount,
                    "details_hash": details_hash,
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e
