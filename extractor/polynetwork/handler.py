from typing import Any, Dict, List

from config.constants import Bridge
from extractor.base_handler import BaseHandler
from extractor.polynetwork.constants import BRIDGE_CONFIG
from repository.database import DBSession
from repository.polynetwork.repository import (
    PolynetworkBlockchainTransactionRepository,
    PolynetworkCrossChainEventRepository,
    PolynetworkLockEventRepository,
    PolynetworkUnlockEventRepository,
    PolynetworkVerifyHeaderAndExecuteTxEventRepository,
)
from rpcs.evm_rpc_client import EvmRPCClient
from utils.utils import CustomException, log_error

# PolyNetwork protocol domain IDs, as described in bridge-common:base/mainnet.go
POLYNETWORK_DOMAIN_IDS = {
    0: "poly",
    1: "bitcoin",
    2: "ethereum",
    3: "ontology",
    4: "neo",
    5: "switcheo",
    6: "bnb",
    7: "heco",
    8: "palette",
    10: "o3swap",
    12: "okxchain",
    14: "neo3",
    15: "heimdall",
    17: "polygon",
    18: "zilliqa",
    19: "arbitrum",
    20: "gnosis",
    21: "avalanche",
    22: "fantom",
    23: "optimism",
    24: "metis",
    25: "boba",
    26: "oasis",
    27: "harmony",
    28: "hsc",
    29: "bytom",
    30: "kcc",
    31: "starcoin",
    32: "kava",
    34: "milkomeda",
    35: "cube",
    36: "celo",
    37: "clover",
    38: "conflux",
    40: "astar",
    41: "aptos",
    42: "brise",
    43: "dexit",
    44: "cloudtx",
    45: "zksync",
    46: "xinfin",
    47: "ontevm",
}


class PolynetworkHandler(BaseHandler):
    CLASS_NAME = "PolynetworkHandler"

    def __init__(self, rpc_client: EvmRPCClient, blockchains: list) -> None:
        super().__init__(rpc_client, blockchains)
        self.bridge = Bridge.POLYNETWORK

    def get_bridge_contracts_and_topics(self, bridge: str, blockchain: List[str]) -> None:
        return super().get_bridge_contracts_and_topics(
            config=BRIDGE_CONFIG,
            bridge=bridge,
            blockchain=blockchain,
        )

    def bind_db_to_repos(self):
        self.blockchain_transaction_repo = PolynetworkBlockchainTransactionRepository(DBSession)
        self.cross_chain_event_repo = PolynetworkCrossChainEventRepository(DBSession)
        self.verify_header_repo = PolynetworkVerifyHeaderAndExecuteTxEventRepository(DBSession)
        self.lock_event_repo = PolynetworkLockEventRepository(DBSession)
        self.unlock_event_repo = PolynetworkUnlockEventRepository(DBSession)

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
                    == "0x6ad3bf15c1988bc04bc153490cab16db8efb9a3990215bf1c64ea6e28be88483"
                ): # event CrossChainEvent(address indexed sender, bytes txId, 
                   # address proxyOrAssetContract, uint64 toChainId, bytes toContract,
                   # bytes rawdata)
                    event = self.handle_cross_chain_event(blockchain, event)
                elif (
                    event["topic"]
                    == "0x8a4a2663ce60ce4955c595da2894de0415240f1ace024cfbff85f513b656bdae"
                ): # event VerifyHeaderAndExecuteTxEvent(uint64 fromChainID, bytes toContract,
                   # bytes crossChainTxHash, bytes fromChainTxHash)
                    event = self.handle_verify_header_and_execute_tx_event(blockchain, event)
                elif (
                    event["topic"]
                    == "0x8636abd6d0e464fe725a13346c7ac779b73561c705506044a2e6b2cdb1295ea5"
                ): # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId,
                   # bytes toAssetHash, bytes toAddress, uint256 amount)
                    event = self.handle_lock_event(blockchain, event)
                elif (
                    event["topic"]
                    == "0x3aa1a37a3bb16943a2c97dd810c5601a4ce19bb1942a54401f821af5515c5530"
                ): # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, 
                   # bytes toAssetHash, bytes toAddress, uint256 amount, bytes txArgs)
                    event = self.handle_lock_event(blockchain, event)
                elif (
                    event["topic"]
                    == "0xd90288730b87c2b8e0c45bd82260fd22478aba30ae1c4d578b8daba9261604df"
                ): # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount)
                    event = self.handle_unlock_event(blockchain, event)
                elif (
                    event["topic"]
                    == "0x2d3f6ad356f1c408166244c68a928a722472299760d71a6de97f6057b912972c"
                ): # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount, 
                   # bytes txArgs)
                    event = self.handle_unlock_event(blockchain, event)

                if event:
                    included_events.append(event)

            except CustomException as e:
                request_desc = (
                    f"Error processing request: {blockchain}, {start_block}, "
                    f"{end_block}, {contract}, {topics}.\n{e}"
                )
                log_error(self.bridge, request_desc)

        return included_events

    def _domain_to_blockchain(self, domain_id: int) -> str | None:
        return POLYNETWORK_DOMAIN_IDS.get(domain_id)

    def handle_cross_chain_event(self, blockchain, event):
        func_name = "handle_cross_chain_event"

        try:
            transaction_hash = event["transaction_hash"]

            hexData = event["rawdata"]
            if hexData.startswith("0x"):
                hexData = hexData[2:]
            
            if len(hexData) < 87: # Mininum length to contain at least the cross-chain tx hash
                request_desc = (
                    f"Error processing CrossChainEvent: {blockchain}, {event['transaction_hash']}. "
                    f"Data argument is too short."
                )
                log_error(self.bridge, request_desc)
                return None
            data = bytes.fromhex(hexData)
            
            offset, param_tx_hash = self.decode_var_bytes_at(data, 0)
            offset, cross_chain_tx_hash = self.decode_var_bytes_at(data, offset)
            
            if self.cross_chain_event_repo.event_exists(
                transaction_hash, 
                cross_chain_tx_hash
            ):
                return None
            
            offset, depositor = self.decode_var_bytes_at(data, offset)
            depositor = "0x" + depositor

            offset, target_chain_id = self.decode_var_uint_at(data, offset, 64)
            target_chain = self._domain_to_blockchain(target_chain_id) if target_chain_id else None
            
            offset, target_contract = self.decode_var_bytes_at(data, offset)
            target_contract = "0x" + target_contract

            offset, target_contract_method = self.decode_var_bytes_at(data, offset)
            target_contract_method = bytes.fromhex(target_contract_method).decode(
                'utf-8', 
                errors='ignore'
            )
            offset, tx_data = self.decode_var_bytes_at(data, offset)

            self.cross_chain_event_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": transaction_hash,
                    "sender": event["sender"],
                    "tx_id": event["txId"],
                    "proxy_or_contract_address": event["proxyOrAssetContract"],
                    "to_chain": self._domain_to_blockchain(int(event["toChainId"])),
                    "to_contract": "0x" + event["toContract"],
                    "param_tx_hash": param_tx_hash,
                    "cross_chain_tx_hash": cross_chain_tx_hash,
                    "depositor": depositor,
                    "target_chain": target_chain,
                    "target_contract_method": target_contract_method,
                    "tx_data": tx_data,
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_verify_header_and_execute_tx_event(self, blockchain, event):
        func_name = "handle_verify_header_and_execute_tx_event"

        try:
            transaction_hash = event["transaction_hash"]
            cross_chain_tx_hash = event["crossChainTxHash"]
            if self.verify_header_repo.event_exists(transaction_hash, cross_chain_tx_hash):
                return None
            
            from_chain_id = int(event["fromChainID"])
            from_chain = self._domain_to_blockchain(from_chain_id)

            self.verify_header_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": transaction_hash,
                    "from_chain": from_chain,
                    "to_contract": "0x" + event["toContract"],
                    "cross_chain_tx_hash": cross_chain_tx_hash,
                    "from_chain_tx_hash": event["fromChainTxHash"],
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_lock_event(self, blockchain, event):
        func_name = "handle_lock_event"

        try:
            transaction_hash = event["transaction_hash"]

            from_address = event["fromAddress"]
            to_chain_id = int(event["toChainId"])
            to_chain = self._domain_to_blockchain(to_chain_id)
            to_asset_hash = "0x" + event["toAssetHash"]
            to_address = "0x" + event["toAddress"]

            if self.lock_event_repo.event_exists(
                transaction_hash, 
                from_address, 
                to_chain, 
                to_asset_hash, 
                to_address
            ):
                return None
            
            from_asset_hash = (
                event["fromAssetHash"] if "fromAssetHash" in event
                else event["tokenAddress"]
            )
            amount = int(event["amount"])

            if "txArgs" in event:
                decoded_args = self.decode_tx_args(event["txArgs"])

            self.lock_event_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": transaction_hash,
                    "from_asset_hash": from_asset_hash,
                    "from_address": from_address,
                    "to_chain": to_chain,
                    "to_asset_hash": to_asset_hash,
                    "to_address": to_address,
                    "amount": amount,
                    "fee_amount": int(decoded_args["fee_amount"]) if "txArgs" in event else None,
                    "fee_address": decoded_args["fee_address"] if "txArgs" in event else None,
                    "nonce": decoded_args["nonce"] if "txArgs" in event else None,
                }
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    def handle_unlock_event(self, blockchain, event):
        func_name = "handle_unlock_event"

        try:
            transaction_hash = event["transaction_hash"]

            to_asset_hash = (
                event["toAssetHash"] if "toAssetHash" in event 
                else event["tokenAddress"]
            )
            to_address = event["toAddress"]

            if self.unlock_event_repo.event_exists(
                transaction_hash, 
                to_asset_hash, 
                to_address
            ):
                return None
            
            amount = int(event["amount"])
            if "txArgs" in event:
                decoded_args = self.decode_tx_args(event["txArgs"])

            self.unlock_event_repo.create(
                {
                    "blockchain": blockchain,
                    "transaction_hash": transaction_hash,
                    "to_asset_hash": to_asset_hash,
                    "to_address": to_address,
                    "amount": amount,
                    "from_asset_hash": (
                        decoded_args["from_asset_hash"] if "txArgs" in event 
                        else None
                    ),
                    "fee_amount": int(decoded_args["fee_amount"]) if "txArgs" in event else None,
                    "fee_address": decoded_args["fee_address"] if "txArgs" in event else None,
                    "from_address": decoded_args["from_address"] if "txArgs" in event else None,
                    "nonce": decoded_args["nonce"] if "txArgs" in event else None,
                },
            )
            return event
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"{blockchain} -- Tx Hash: {event['transaction_hash']}. Error writing to DB: {e}",
            ) from e

    # =================
    # Helper functions for decoding data from events.
    # The return value is the new offset, followed by the decoded value.
    def decode_var_bytes_at(self, data: bytes, offset: int) -> str:
        if offset > len(data):
            return offset, None
        first = data[offset]
        offset += 1

        if first < 0xFD:
            length = first
        elif first == 0xFD:
            length = int.from_bytes(data[offset : offset + 2], "little")
            offset += 2
        elif first == 0xFE:
            length = int.from_bytes(data[offset : offset + 4], "little")
            offset += 4
        else:  # 0xFF
            length = int.from_bytes(data[offset : offset + 8], "little")
            offset += 8

        return offset + length, data[offset : offset + length].hex()

    def decode_var_uint_at(self, data: bytes, offset: int, num_bits: int) -> int:
        if offset > len(data):
            return offset, None
        right = offset + (num_bits + 7) // 8
        raw = data[offset: right]
        return right, int.from_bytes(raw, "little")
    
    def decode_tx_args(self, data) -> Dict[str, Any]:
        if isinstance(data, str):
            if data.startswith("0x"):
                data = data[2:]
            data = bytes.fromhex(data)
        offset, from_asset_hash = self.decode_var_bytes_at(data, 0)
        offset, to_asset_hash = self.decode_var_bytes_at(data, offset)
        offset, amount = self.decode_var_uint_at(data, offset, 256)
        offset, fee_amount = self.decode_var_uint_at(data, offset, 256)
        offset, fee_address = self.decode_var_bytes_at(data, offset)
        offset, from_address = self.decode_var_bytes_at(data, offset)
        offset, nonce = self.decode_var_uint_at(data, offset, 256)

        return {
            "from_asset_hash": from_asset_hash,
            "to_asset_hash": to_asset_hash,
            "amount": amount,
            "fee_amount": fee_amount,
            "fee_address": fee_address,
            "from_address": from_address,
            "nonce": nonce,
        }