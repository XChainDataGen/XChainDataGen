from web3.contract import Contract

from extractor.base_decoder import BaseDecoder
from utils.utils import CustomException


class NomadDecoder(BaseDecoder):
    CLASS_NAME = "NomadDecoder"

    def __init__(self):
        super().__init__()

    def decode_event(self, contract: Contract, log: dict):
        func_name = "decode_event"

        if (
            log["topics"][0] == "0xa3d219cf126a12be40d7ad1ceef46231c987988dd4e686457b610e1b6b80a4bf"
        ): # event Send(address indexed token, address indexed from, uint32 indexed toDomain, 
           # bytes32 toId, uint256 amount, bool toHook)
            return contract.events.Send().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x9f9a97db84f39202ca3b409b63f7ccf7d3fd810e176573c7483088b6f181bbbb"
        ): # Receive(uint64 indexed originAndNonce, address indexed token, 
           # address indexed recipient, address liquidityProvider, uint256 amount)
            return contract.events.Receive().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x7d4b3c5c44bd8008199bb99f184426274cf24f917f4da3485d6a39f894366b10"
        ): # Send(address indexed from)
            return contract.events.Send().process_log(log)["args"]
        elif (
            log["topics"][0] == "0xd42de95a9b26f1be134c8ecce389dc4fcfa18753d01661b7b361233569e8fe48"
        ): # Process(bytes32 indexed messageHash, bool indexed success, bytes indexed returnData)
            return contract.events.Process().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x9d4c83d2e57d7d381feb264b44a5015e7f9ef26340f4fc46b558a6dc16dd811a"
        ): # Dispatch(index_topic_1 bytes32 messageHash, index_topic_2 uint256 leafIndex,
           # index_topic_3 uint64 destinationAndNonce, bytes32 committedRoot, bytes message)
            return contract.events.Dispatch().process_log(log)["args"]

        raise CustomException(
            self.CLASS_NAME, func_name, f"Unknown event topic: {log['topics'][0]}"
        )
