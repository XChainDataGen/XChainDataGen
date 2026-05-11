# Mapping of bridges to their supported blockchains and contracts
BRIDGE_CONFIG = {
    "blockchains": {
        "ethereum": [
            {
                # Ethereum Bridge Router 
                # Implementation Address: 0xe0db61ac718f502b485dec66d013afbbe0b52f84
                "abi": "0x88a69b4e698a4b090df6cf5bd7b2d47325ad30a3",
                "contracts": [
                    "0x88a69b4e698a4b090df6cf5bd7b2d47325ad30a3",  # Ethereum Bridge Router Proxy
                ],
                "topics": [
                    # event Send(address indexed token, address indexed from, uint32 indexed toDomain, bytes32 toId, uint256 amount, bool toHook)
                    "0xa3d219cf126a12be40d7ad1ceef46231c987988dd4e686457b610e1b6b80a4bf",
                    # event Receive(uint64 indexed originAndNonce, address indexed token, address indexed recipient, address liquidityProvider, uint256 amount)
                    "0x9f9a97db84f39202ca3b409b63f7ccf7d3fd810e176573c7483088b6f181bbbb",
                ],
            },
            {
                "abi": "0x2d6775c1673d4ce55e1f827a0d53e62c43d1f304", # ETH Helper (Implementation Address)
                "contracts": [
                    "0x2d6775c1673d4ce55e1f827a0d53e62c43d1f304",  # ETH Helper
                ],
                "topics": [
                    # event Send(address indexed from)
                    "0x7d4b3c5c44bd8008199bb99f184426274cf24f917f4da3485d6a39f894366b10",
                ],
            },
            {
                # Replica Contract
                # Implementation Address (Post-attack): 0x7f221a1850c12b57fed1f0831dd25399a13b68c2
                "abi": "0x049b51e531fd8f90da6d92ea83dc4125002f20ef", 
                "contracts": [
                    "0x049b51e531fd8f90da6d92ea83dc4125002f20ef", # Ethereum: Nomad Withdrawals Manager Proxy
                    "0x5d94309e5a0090b165fa4181519701637b6daeba"  # Ethereum: Nomad Withdrawals Manager Fallback Proxy
                ],
                "topics": [
                    # event Process(bytes32 indexed messageHash, bool indexed success, bytes indexed returnData)
                    "0xd42de95a9b26f1be134c8ecce389dc4fcfa18753d01661b7b361233569e8fe48",
                ]
            },
            {
                # Home Contract
                # Implementation Address (Post-attack): 0xf3bb7e2d4b26ae2c3eac41171840c227f457ea06
                "abi": "0x92d3404a7e6c91455bbd81475cd9fad96acff4c8", 
                "contracts": [
                    "0x92d3404a7e6c91455bbd81475cd9fad96acff4c8", # Ethereum: Nomad Home
                ],
                "topics": [
                    # event Dispatch(index_topic_1 bytes32 messageHash, index_topic_2 uint256 leafIndex, index_topic_3 uint64 destinationAndNonce, bytes32 committedRoot, bytes message)
                    "0x9d4c83d2e57d7d381feb264b44a5015e7f9ef26340f4fc46b558a6dc16dd811a",
                ]
            }
        ],
        "moonbeam": [
            {
                # Bridge Router
                # Implementation Address: 0x0e6a3fd785f2169a086e179004710ba6b663a892
                "abi": "0xd3dfd3ede74e0dcebc1aa685e151332857efce2d",
                "contracts": [
                    "0xd3dfd3ede74e0dcebc1aa685e151332857efce2d", # Moonbeam: Nomad Bridge Router Proxy
                ],
                "topics": [
                    # event Send(address indexed token, address indexed from, uint32 indexed toDomain, bytes32 toId, uint256 amount, bool toHook)
                    "0xa3d219cf126a12be40d7ad1ceef46231c987988dd4e686457b610e1b6b80a4bf",
                    # event Receive(uint64 indexed originAndNonce, address indexed token, address indexed recipient, address liquidityProvider, uint256 amount)
                    "0x9f9a97db84f39202ca3b409b63f7ccf7d3fd810e176573c7483088b6f181bbbb",
                ]
            },
            {
                # Replica Contract
                # Implementation Address: 0x8d2c231c3522b9906b4e017c9ad658868720b436
                "abi": "0x7f58bb8311db968ab110889f2dfa04ab7e8e831b",
                "contracts": [
                    "0x7f58bb8311db968ab110889f2dfa04ab7e8e831b", # Replica Proxy Contract
                ],
                "topics": [
                    # event Process(bytes32 indexed messageHash, bool indexed success, bytes indexed returnData)
                    "0xd42de95a9b26f1be134c8ecce389dc4fcfa18753d01661b7b361233569e8fe48",
                ],
            },
            {
                # Moonbeam ETH Helper
                # Implementation Address: 0xb70588b1a51f847d13158ff18e9cac861df5fb00
                "abi": "0xb70588b1a51f847d13158ff18e9cac861df5fb00",
                "contracts": [
                    "0xb70588b1a51f847d13158ff18e9cac861df5fb00", # Moonbeam: Nomad ETH Helper Proxy
                ],
                "topics": [
                    # event Send(address indexed from)
                    "0x7d4b3c5c44bd8008199bb99f184426274cf24f917f4da3485d6a39f894366b10",
                ],
            },
            {
                # Nomad Home Contract
                # Implementation Address: 0x5b70013fbeb1211a23ea33eb681ec87196475805
                "abi": "0x8f184d6aa1977fd2f9d9024317d0ea5cf5815b6f",
                "contracts": [
                    "0x8f184d6aa1977fd2f9d9024317d0ea5cf5815b6f", # Moonbeam: Nomad Home (relay/fraud proofs)
                ],
                "topics": [
                    # event Dispatch(index_topic_1 bytes32 messageHash, index_topic_2 uint256 leafIndex, index_topic_3 uint64 destinationAndNonce, bytes32 committedRoot, bytes message)
                    "0x9d4c83d2e57d7d381feb264b44a5015e7f9ef26340f4fc46b558a6dc16dd811a",
                ]
            }
        ]
    }
}
