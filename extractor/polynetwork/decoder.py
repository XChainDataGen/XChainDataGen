from web3.contract import Contract

from extractor.base_decoder import BaseDecoder
from utils.utils import CustomException


class PolynetworkDecoder(BaseDecoder):
    CLASS_NAME = "PolynetworkDecoder"

    def __init__(self):
        super().__init__()

    def decode_event(self, contract: Contract, log: dict):
        func_name = "decode_event"

        if (
            log["topics"][0] == "0x6ad3bf15c1988bc04bc153490cab16db8efb9a3990215bf1c64ea6e28be88483"
        ): # event CrossChainEvent(address indexed sender, bytes txId, address proxyOrAssetContract,
           # uint64 toChainId, bytes toContract, bytes rawdata)
            return contract.events.CrossChainEvent().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x8a4a2663ce60ce4955c595da2894de0415240f1ace024cfbff85f513b656bdae"
        ): # event VerifyHeaderAndExecuteTxEvent(uint64 fromChainID, bytes toContract,
           # bytes crossChainTxHash, bytes fromChainTxHash)
            return contract.events.VerifyHeaderAndExecuteTxEvent().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x8636abd6d0e464fe725a13346c7ac779b73561c705506044a2e6b2cdb1295ea5"
        ): # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId,
           # bytes toAssetHash, bytes toAddress, uint256 amount)
            return contract.events.LockEvent().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x3aa1a37a3bb16943a2c97dd810c5601a4ce19bb1942a54401f821af5515c5530"
        ): # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, 
           # bytes toAssetHash, bytes toAddress, uint256 amount, bytes txArgs)
            return contract.events.LockEvent().process_log(log)["args"]
        elif (
            log["topics"][0] == "0xd90288730b87c2b8e0c45bd82260fd22478aba30ae1c4d578b8daba9261604df"
        ): # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount)
            return contract.events.UnlockEvent().process_log(log)["args"]
        elif (
            log["topics"][0] == "0x2d3f6ad356f1c408166244c68a928a722472299760d71a6de97f6057b912972c"
        ): # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount, bytes txArgs)
            return contract.events.UnlockEvent().process_log(log)["args"]

        raise CustomException(
            self.CLASS_NAME, func_name, f"Unknown event topic: {log['topics'][0]}"
        )
