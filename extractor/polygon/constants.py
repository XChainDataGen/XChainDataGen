# Mapping of bridges to their supported blockchains and contracts
BRIDGE_CONFIG = {
    "blockchains": {
        "ethereum": [
            {
                "abi": "0x28e4f3a7f651294b9564800b2d01f35189a5bfbe",
                "contracts": [
                    "0x28e4f3a7f651294b9564800b2d01f35189a5bfbe",  # Polygon (Matic): State Syncer
                ],
                "topics": [
                    "0x103fed9db65eac19c4d870f49ab7520fe03b99f1838e5996caf47e9e43308392",  # StateSynced
                ],
            },
            {
                "abi": "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",
                "contracts": [
                    "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",  # Polygon (Matic): ERC20 Bridge
                ],
                "topics": [
                    "0x9b217a401a5ddf7c4d474074aff9958a18d48690d77cc2151c4706aa7348b401",  # LockedERC20
                    "0xbb61bd1b26b3684c7c028ff1a8f6dabcac2fac8ac57b66fa6b1efb6edeab03c4",  # ExitedERC20
                ],
            },
            {
                "abi": "0x8484ef722627bf18ca5ae6bcf031c23e6e922b30",
                "contracts": [
                    "0x8484ef722627bf18ca5ae6bcf031c23e6e922b30",  # Polygon (Matic): Ether Bridge
                ],
                "topics": [
                    "0x3e799b2d61372379e767ef8f04d65089179b7a6f63f9be3065806456c7309f1b",  # LockedEther
                    "0x0fc0eed41f72d3da77d0f53b9594fc7073acd15ee9d7c536819a70a67c57ef3c",  # ExitedEther
                ],
            },
            {
                "abi": "0x401f6c983ea34274ec46f84d70b31c151321188b",
                "contracts": [
                    "0x401f6c983ea34274ec46f84d70b31c151321188b",  # Polygon (Matic): Plasma Bridge
                ],
                "topics": [
                    "0x1dadc8d0683c6f9824e885935c1bec6f76816730dcec148dda8cf25a7b9f797b",  # NewDepositBlock
                ],
            },
            {
                "abi": "0x2a88696e0ffa76baa1338f2c74497cc013495922",
                "contracts": [
                    "0x2a88696e0ffa76baa1338f2c74497cc013495922",  # Polygon (Matic): Withdraw Manager Proxy
                ],
                "topics": [
                    "0xfeb2000dca3e617cd6f3a8bbb63014bb54a124aac6ccbf73ee7229b4cd01f120",  # Withdraw
                ],
            },
        ],
        "polygon": [
            {
                "abi": "0x0000000000000000000000000000000000001001",
                "contracts": [
                    "0x0000000000000000000000000000000000001001",  # StateReceiver
                ],
                "topics": [
                    "0x5a22725590b0a51c923940223f7458512164b1113359a735e86e7f27f44791ee",  # StateCommitted
                ],
            },
            {
                "abi": "0xd9c7c4ed4b66858301d0cb28cc88bf655fe34861",
                "contracts": [
                    "0xd9c7c4ed4b66858301d0cb28cc88bf655fe34861",  # Polygon: Child Chain
                ],
                "topics": [
                    "0xec3afb067bce33c5a294470ec5b29e6759301cd3928550490c6d48816cdc2f5d",  # TokenDeposited
                ],
            },
            {
                "abi": "0x0000000000000000000000000000000000001010",
                "contracts": [
                    "0x0000000000000000000000000000000000001010",  # Polygon: POL Token
                ],
                "topics": [
                    "0xebff2602b3f468259e1e99f613fed6691f3a6526effe6ef3e768ba7ae7a36c4f",  # Withdraw
                ],
            },
            {
                "abi": "erc20",
                "contracts": [
                    # Filled dynamically from Ethereum exit root-token mappings.
                ],
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer
                    None,
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                ],
            },
        ],
    }
}

ETHER_ROOT_TOKEN = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
ROOT_CHAIN_MANAGER = "0xA0c68C638235ee32657e8f720a23ceC1bFc77C77"
ROOT_TO_CHILD_TOKEN_SELECTOR = "0xea60c7c4"
TOPIC_ADDRESS_CHUNK_SIZE = 100
