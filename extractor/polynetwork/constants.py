# Mapping of bridges to their supported blockchains and contracts
BRIDGE_CONFIG = {
    "blockchains": {
        "ethereum": [
            {
                # Eth Cross Chain Manager
                # Implementation Address: 0x14413419452aaf089762a0c5e95ed2a13bbc488c
                "abi": "0x14413419452aaf089762a0c5e95ed2a13bbc488c",
                "contracts": [
                    "0x14413419452aaf089762a0c5e95ed2a13bbc488c",  # Ethereum: CrossChainManager V3
                    "0xe020877e67cfaaffc33a6e7eb9e85741bbb3ea79",  # Ethereum: CrossChainManager V2
                    "0x838bf9e95cb12dd76a54c9f9d2e3082eaf928270"   # Ethereum: CrossChainManager V1 (Unverified)
                ],
                "topics": [
                    # event CrossChainEvent(address indexed sender, bytes txId, address proxyOrAssetContract, uint64 toChainId, bytes toContract, bytes rawdata)
                    "0x6ad3bf15c1988bc04bc153490cab16db8efb9a3990215bf1c64ea6e28be88483",
                    # event VerifyHeaderAndExecuteTxEvent(uint64 fromChainID, bytes toContract, bytes crossChainTxHash, bytes fromChainTxHash)
                    "0x8a4a2663ce60ce4955c595da2894de0415240f1ace024cfbff85f513b656bdae",
                ],
            },
            # {
            #     # Eth Cross Chain Manager Proxy
            #     # Implementation Address: 0x5a51e2ebf8d136926b9ca7b59b60464e7c44d2eb
            #     "abi": "0x5a51e2ebf8d136926b9ca7b59b60464e7c44d2eb",
            #     "contracts": [
            #         "0x5a51e2ebf8d136926b9ca7b59b60464e7c44d2eb",
            #     ],
            #     "topics": [] # Currently no unique event extraction exists in this contract,
            #                  # but we include it for potential future use.
            # },
            # {
            #     # Eth Cross Chain Data
            #     # Implementation Address: 0xcf2afe102057ba5c16f899271045a0a37fcb10f2
            #     "abi": "0xcf2afe102057ba5c16f899271045a0a37fcb10f2",
            #     "contracts": [
            #         "0xcf2afe102057ba5c16f899271045a0a37fcb10f2",
            #     ],
            #     "topics": [] # Currently no unique event extraction exists in this contract,
            #                  # but we include it for potential future use.
            # },
            {
                # Lock Proxy
                # Implementation Address: 0x250e76987d838a75310c34bf422ea9f1ac4cc906
                "abi": "0x250e76987d838a75310c34bf422ea9f1ac4cc906",
                "contracts": [
                    "0x250e76987d838a75310c34bf422ea9f1ac4cc906",
                    "0xf7a9fe22149ad2a077eb40a90f316a8a47525ec3",
                ],
                "topics": [
                    # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, bytes toAssetHash, bytes toAddress, uint256 amount)
                    "0x8636abd6d0e464fe725a13346c7ac779b73561c705506044a2e6b2cdb1295ea5",
                    # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount)
                    "0xd90288730b87c2b8e0c45bd82260fd22478aba30ae1c4d578b8daba9261604df",
                ]
            },
            {
                # Lock Proxy (txArgs version)
                # Implementation Address: 0x9a016ce184a22dbf6c17daa59eb7d3140dbd1c54
                "abi": "0x9a016ce184a22dbf6c17daa59eb7d3140dbd1c54",
                "contracts": [
                    "0x9a016ce184a22dbf6c17daa59eb7d3140dbd1c54",
                ],
                "topics": [
                    # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, bytes toAssetHash, bytes toAddress, uint256 amount, bytes txArgs)
                    "0x3aa1a37a3bb16943a2c97dd810c5601a4ce19bb1942a54401f821af5515c5530",
                    # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount, bytes txArgs)
                    "0x2d3f6ad356f1c408166244c68a928a722472299760d71a6de97f6057b912972c"
                ]
            }
        ],
        "bnb": [
            {
                # Eth Cross Chain Manager
                # Implementation Address: 0x1c9ca8abb5da65d94dad2e8fb3f45535480d5909
                "abi": "0x1c9ca8abb5da65d94dad2e8fb3f45535480d5909",
                "contracts": [
                    "0x1c9ca8abb5da65d94dad2e8fb3f45535480d5909",  # BSC: CrossChainManager
                ],
                "topics": [
                    # event CrossChainEvent(address indexed sender, bytes txId, address proxyOrAssetContract, uint64 toChainId, bytes toContract, bytes rawdata)
                    "0x6ad3bf15c1988bc04bc153490cab16db8efb9a3990215bf1c64ea6e28be88483",
                    # event VerifyHeaderAndExecuteTxEvent(uint64 fromChainID, bytes toContract, bytes crossChainTxHash, bytes fromChainTxHash)
                    "0x8a4a2663ce60ce4955c595da2894de0415240f1ace024cfbff85f513b656bdae",
                ],
            },
            {
                # Lock Proxy
                # Implementation Address: 0x2f7ac9436ba4b548f9582af91ca1ef02cd2f1f03
                "abi": "0x2f7ac9436ba4b548f9582af91ca1ef02cd2f1f03",
                "contracts": [
                    "0x2f7ac9436ba4b548f9582af91ca1ef02cd2f1f03",
                    "0x12682669700109ae1f3b326d74f2a5bdb63549e3",
                    "0x12bb90a4baa8fd125794e34daffec109ab63dfb4",
                    "0xfb571d4dd7039f96d34bb41e695adc92df4a332f",
                    "0x960ff3132b72e3f0b1b9f588e7122d78bb5c4946"
                ],
                "topics": [
                    # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, bytes toAssetHash, bytes toAddress, uint256 amount)
                    "0x8636abd6d0e464fe725a13346c7ac779b73561c705506044a2e6b2cdb1295ea5",
                    # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount)
                    "0xd90288730b87c2b8e0c45bd82260fd22478aba30ae1c4d578b8daba9261604df",
                ]
            },
            {
                # Lock Proxy (txArgs version)
                # Implementation Address: 0xb5d4f343412dc8efb6ff599d790074d0f1e8d430
                "abi": "0xb5d4f343412dc8efb6ff599d790074d0f1e8d430",
                "contracts": [
                    "0xb5d4f343412dc8efb6ff599d790074d0f1e8d430",
                ],
                "topics": [
                    # event LockEvent(address tokenAddress, address fromAddress, uint64 toChainId, bytes toAssetHash, bytes toAddress, uint256 amount, bytes txArgs)
                    "0x3aa1a37a3bb16943a2c97dd810c5601a4ce19bb1942a54401f821af5515c5530",
                    # event UnlockEvent(address tokenAddress, address toAddress, uint256 amount, bytes txArgs)
                    "0x2d3f6ad356f1c408166244c68a928a722472299760d71a6de97f6057b912972c"
                ]
            }
        ],
        "polygon": [
            {
                # Eth Cross Chain Manager
                # Implementation Address: 0xb16fed79a6cb9270956f045f2e7989affb75d459
                "abi": "0xb16fed79a6cb9270956f045f2e7989affb75d459",
                "contracts": [
                    "0xb16fed79a6cb9270956f045f2e7989affb75d459",  # Ethereum: CrossChainManager
                ],
                "topics": [
                    # event CrossChainEvent(address indexed sender, bytes txId, address proxyOrAssetContract, uint64 toChainId, bytes toContract, bytes rawdata)
                    "0x6ad3bf15c1988bc04bc153490cab16db8efb9a3990215bf1c64ea6e28be88483",
                    # event VerifyHeaderAndExecuteTxEvent(uint64 fromChainID, bytes toContract, bytes crossChainTxHash, bytes fromChainTxHash)
                    "0x8a4a2663ce60ce4955c595da2894de0415240f1ace024cfbff85f513b656bdae",
                ],
            },
            {
                # Lock Proxy
                # Implementation Address: 0x28ff66a1b95d7cacf8eded2e658f768f44841212
                "abi": "0x28ff66a1b95d7cacf8eded2e658f768f44841212",
                "contracts": [
                    "0x28ff66a1b95d7cacf8eded2e658f768f44841212",
                    "0x5f8517d606580d30c3bf210fa016b8916c685be8"
                ],
                "topics": [
                    # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, bytes toAssetHash, bytes toAddress, uint256 amount)
                    "0x8636abd6d0e464fe725a13346c7ac779b73561c705506044a2e6b2cdb1295ea5",
                    # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount)
                    "0xd90288730b87c2b8e0c45bd82260fd22478aba30ae1c4d578b8daba9261604df",
                ]
            }
        ],
        "arbitrum": [
            {
                # Eth Cross Chain Manager
                # Implementation Address: 0x7cea671dabfba880af6723bddd6b9f4caa15c87b
                "abi": "0x7cea671dabfba880af6723bddd6b9f4caa15c87b",
                "contracts": [
                    "0x7cea671dabfba880af6723bddd6b9f4caa15c87b",  # Ethereum: CrossChainManager
                ],
                "topics": [
                    # event CrossChainEvent(address indexed sender, bytes txId, address proxyOrAssetContract, uint64 toChainId, bytes toContract, bytes rawdata)
                    "0x6ad3bf15c1988bc04bc153490cab16db8efb9a3990215bf1c64ea6e28be88483",
                    # event VerifyHeaderAndExecuteTxEvent(uint64 fromChainID, bytes toContract, bytes crossChainTxHash, bytes fromChainTxHash)
                    "0x8a4a2663ce60ce4955c595da2894de0415240f1ace024cfbff85f513b656bdae",
                ],
            },
            {
                # Lock Proxy
                # Implementation Address: 0x2f7ac9436ba4b548f9582af91ca1ef02cd2f1f03
                "abi": "0x2f7ac9436ba4b548f9582af91ca1ef02cd2f1f03",
                "contracts": [
                    "0x2f7ac9436ba4b548f9582af91ca1ef02cd2f1f03",
                    "0x30e39786f0dd700da277a54bd9c07f7894cb5aba"
                ],
                "topics": [
                    # event LockEvent(address fromAssetHash, address fromAddress, uint64 toChainId, bytes toAssetHash, bytes toAddress, uint256 amount)
                    "0x8636abd6d0e464fe725a13346c7ac779b73561c705506044a2e6b2cdb1295ea5",
                    # event UnlockEvent(address toAssetHash, address toAddress, uint256 amount)
                    "0xd90288730b87c2b8e0c45bd82260fd22478aba30ae1c4d578b8daba9261604df",
                ]
            }
        ]
    }
}
