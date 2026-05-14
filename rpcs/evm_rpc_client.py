from config.constants import (
    RPCS_CONFIG_FILE,
)
from rpcs.rpc_client import RPCClient


class EvmRPCClient(RPCClient):
    CLASS_NAME = "EvmRPCClient"

    def __init__(self, bridge, config_file: str = RPCS_CONFIG_FILE):
        super().__init__(bridge, config_file)

    def get_logs_emitted_by_contract(
        self,
        blockchain: str,
        contract: str,
        topics: list,
        start_block: str,
        end_block: str,
    ) -> list:
        method = "eth_getLogs"
        topic_filter = (
            topics
            if any(topic is None or isinstance(topic, list) for topic in topics)
            else [topics]
        )
        log_filter = {
            "fromBlock": hex(start_block),
            "toBlock": hex(end_block),
            "topics": topic_filter,
            "address": contract,
        }

        params = [log_filter]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else []

    def eth_call(
        self,
        blockchain: str,
        contract: str,
        data: str,
        block_number: str = "latest",
    ) -> str:
        method = "eth_call"
        params = [
            {
                "to": contract,
                "data": data,
            },
            block_number,
        ]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else None

    def process_transaction(self, blockchain: str, tx_hash: str, block_number: str) -> dict:
        import concurrent.futures

        if self.requires_transaction_by_hash_rpc_call:
            method_tx = "eth_getTransactionByHash"
            params_tx = [tx_hash]

        method_receipt = "eth_getTransactionReceipt"
        params_receipt = [tx_hash]

        method_block = "eth_getBlockByNumber"
        params_block = [block_number, True]

        rpc = self.get_next_rpc(blockchain)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            if self.requires_transaction_by_hash_rpc_call:
                future_tx = executor.submit(
                    self.make_request, rpc, blockchain, method_tx, params_tx
                )

            future_receipt = executor.submit(
                self.make_request, rpc, blockchain, method_receipt, params_receipt
            )
            future_block = executor.submit(
                self.make_request, rpc, blockchain, method_block, params_block
            )

            if self.requires_transaction_by_hash_rpc_call:
                response_tx = future_tx.result()
            else:
                response_tx = None

            response_receipt = future_receipt.result()
            response_block = future_block.result()

            if response_receipt and response_tx:
                response_receipt["result"]["value"] = response_tx["result"]["value"]
                response_receipt["result"]["input"] = response_tx["result"]["input"]

        return response_receipt["result"] if response_receipt else {}, response_block[
            "result"
        ] if response_block else {}

    def get_transaction_receipt(self, blockchain: str, tx_hash: str) -> dict:
        method = "eth_getTransactionReceipt"
        params = [tx_hash]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else {}

    def get_transaction_by_hash(self, blockchain: str, tx_hash: str) -> dict:
        method = "eth_getTransactionByHash"
        params = [tx_hash]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else {}

    def get_transaction_trace(self, blockchain: str, tx_hash: str) -> dict:
        method = "trace_transaction"
        params = [tx_hash]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else {}

    def debug_transaction(self, blockchain: str, tx_hash: str, extra_params: str) -> dict:
        method = "debug_traceTransaction"
        params = [tx_hash, extra_params] if extra_params else [tx_hash]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else {}

    def get_block(
        self, blockchain: str, block_number: str = "latest", full_transactions: bool = True
    ) -> dict:
        method = "eth_getBlockByNumber"
        params = [block_number, full_transactions]

        rpc = self.get_next_rpc(blockchain)
        response = self.make_request(rpc, blockchain, method, params)

        return response["result"] if response else {}
