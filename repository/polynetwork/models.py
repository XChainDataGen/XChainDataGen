from sqlalchemy import BigInteger, Column, Float, Integer, Numeric, String

from repository.common.models import BlockchainTransaction
from repository.database import Base


class PolynetworkCrossChainEvent(Base):
    __tablename__ = "polynetwork_cross_chain_event"

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    blockchain = Column(String(10), nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    sender = Column(String(42), nullable=False)
    tx_id = Column(String(66), nullable=False)
    proxy_or_contract_address = Column(String(42), nullable=False)
    to_chain = Column(String(10), nullable=False)
    to_contract = Column(String(66), nullable=False)

    # raw_data
    param_tx_hash = Column(String(66), nullable=False) # Same as tx_id
    cross_chain_tx_hash = Column(String(66), nullable=False)
    depositor = Column(String(42), nullable=True) # Same as sender
    target_chain = Column(String(10), nullable=True) # Same as to_chain
    target_contract_method = Column(String(100), nullable=True)
    tx_data = Column(String(5000), nullable=True)

    def __init__(
            self,
            blockchain,
            transaction_hash,
            sender,
            tx_id,
            proxy_or_contract_address,
            to_chain,
            to_contract,
            param_tx_hash,
            cross_chain_tx_hash,
            depositor,
            target_chain,
            target_contract_method,
            tx_data
    ):
        self.blockchain = blockchain
        self.transaction_hash = transaction_hash
        self.sender = sender
        self.tx_id = tx_id
        self.proxy_or_contract_address = proxy_or_contract_address
        self.to_chain = to_chain
        self.to_contract = to_contract
        self.param_tx_hash = param_tx_hash
        self.cross_chain_tx_hash = cross_chain_tx_hash
        self.depositor = depositor
        self.target_chain = target_chain
        self.target_contract_method = target_contract_method
        self.tx_data = tx_data

    def __repr__(self):
        return (
            f"<PolynetworkCrossChainEvent {self.blockchain}, "
            f"{self.transaction_hash}, "
            f"{self.sender}, "
            f"{self.tx_id}, "
            f"{self.proxy_or_contract_address}, "
            f"{self.to_chain}, "
            f"{self.to_contract}, "
            f"{self.raw_data}>"
        )

class PolynetworkVerifyHeaderAndExecuteTxEvent(Base):
    __tablename__ = "polynetwork_verify_header_and_execute_tx_event"

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    blockchain = Column(String(10), nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    from_chain = Column(String(10), nullable=False)
    to_contract = Column(String(66), nullable=False)
    cross_chain_tx_hash = Column(String(66), nullable=False)
    from_chain_tx_hash = Column(String(66), nullable=False)

    def __init__(
            self,
            blockchain,
            transaction_hash,
            from_chain,
            to_contract,
            cross_chain_tx_hash,
            from_chain_tx_hash
    ):
        self.blockchain = blockchain
        self.transaction_hash = transaction_hash
        self.from_chain = from_chain
        self.to_contract = to_contract
        self.cross_chain_tx_hash = cross_chain_tx_hash
        self.from_chain_tx_hash = from_chain_tx_hash

    def __repr__(self):
        return (
            f"<PolynetworkVerifyHeaderAndExecuteTxEvent {self.blockchain}, "
            f"{self.transaction_hash}, "
            f"{self.from_chain}, "
            f"{self.to_contract}, "
            f"{self.cross_chain_tx_hash}, "
            f"{self.from_chain_tx_hash}>"
        )

class PolynetworkLockEvent(Base):
    __tablename__ = "polynetwork_lock_event"

    # Not all chains PolyNetwork interacts with use 42-character addresses,
    # hence we use String(66) to accommodate longer identifiers for non-EVM chains.
    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    blockchain = Column(String(10), nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    from_asset_hash = Column(String(42), nullable=False)
    from_address = Column(String(42), nullable=False)
    to_chain = Column(String(10), nullable=False)
    to_asset_hash = Column(String(66), nullable=False)
    to_address = Column(String(66), nullable=False)
    amount = Column(Numeric(40, 0), nullable=False)

    # tx_args
    fee_amount = Column(Numeric(30, 0), nullable=True)
    fee_address = Column(String(66), nullable=True)
    nonce = Column(String(100), nullable=True)

    def __init__(
        self,
        blockchain,
        transaction_hash,
        from_asset_hash,
        from_address,
        to_chain,
        to_asset_hash,
        to_address,
        amount,
        fee_amount=None,
        fee_address=None,
        nonce=None
    ):
        self.blockchain = blockchain
        self.transaction_hash = transaction_hash
        self.from_asset_hash = from_asset_hash
        self.from_address = from_address
        self.to_chain = to_chain
        self.to_asset_hash = to_asset_hash
        self.to_address = to_address
        self.amount = amount
        self.fee_amount = fee_amount
        self.fee_address = fee_address
        self.nonce = nonce

    def __repr__(self):
        return (
            f"<PolynetworkLockEvent {self.blockchain}, "
            f"{self.transaction_hash}, "
            f"{self.from_asset_hash}, "
            f"{self.from_address}, "
            f"{self.to_chain}, "
            f"{self.to_asset_hash}, "
            f"{self.to_address}, "
            f"{self.amount}>"
        )

class PolynetworkUnlockEvent(Base):
    __tablename__ = "polynetwork_unlock_event"

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    blockchain = Column(String(10), nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    to_asset_hash = Column(String(66), nullable=False)
    to_address = Column(String(66), nullable=False)
    amount = Column(Numeric(40, 0), nullable=False)

    # tx_args
    from_asset_hash = Column(String(66), nullable=True)
    fee_amount = Column(Numeric(30, 0), nullable=True)
    fee_address = Column(String(66), nullable=True)
    from_address = Column(String(66), nullable=True)
    nonce = Column(String(100), nullable=True)

    def __init__(
            self,
            blockchain,
            transaction_hash,
            to_asset_hash,
            to_address,
            amount,
            from_asset_hash=None,
            fee_amount=None,
            fee_address=None,
            from_address=None,
            nonce=None
    ):
        self.blockchain = blockchain
        self.transaction_hash = transaction_hash
        self.to_asset_hash = to_asset_hash
        self.to_address = to_address
        self.amount = amount
        self.from_asset_hash = from_asset_hash
        self.fee_amount = fee_amount
        self.fee_address = fee_address
        self.from_address = from_address
        self.nonce = nonce

    def __repr__(self):
        return (
            f"<PolynetworkUnlockEvent {self.blockchain}, "
            f"{self.transaction_hash}, "
            f"{self.to_asset_hash}, "
            f"{self.to_address}, "
            f"{self.amount}>"
        )


class PolynetworkBlockchainTransaction(BlockchainTransaction):
    __tablename__ = "polynetwork_blockchain_transactions"

    def __repr__(self):
        return (
            f"<PolynetworkBlockchainTransaction(blockchain={self.blockchain}, "
            f"transaction_hash={self.transaction_hash}, "
            f"block_number={self.block_number}, "
            f"timestamp={self.timestamp} from_address={self.from_address}, "
            f"to_address={self.to_address}, "
            f"status={self.status})>"
        )


# ######### Processed Data ##########

class PolynetworkCrossChainTransactions(Base):
    __tablename__ = "polynetwork_cross_chain_transactions"

    id = Column(BigInteger, nullable=False, autoincrement=True, primary_key=True)
    src_blockchain = Column(String(10), nullable=False)
    src_transaction_hash = Column(String(66), nullable=False)
    src_from_address = Column(String(42), nullable=False)
    src_to_address = Column(String(42), nullable=False)
    src_fee = Column(Numeric(30, 0), nullable=False)
    src_fee_usd = Column(Float, nullable=True)
    src_timestamp = Column(BigInteger, nullable=False)
    dst_blockchain = Column(String(10), nullable=False)
    dst_transaction_hash = Column(String(66), nullable=False)
    dst_from_address = Column(String(42), nullable=False)
    dst_to_address = Column(String(42), nullable=False)
    dst_fee = Column(Numeric(30, 0), nullable=False)
    dst_fee_usd = Column(Float, nullable=True)
    dst_timestamp = Column(BigInteger, nullable=False)
    deposit_id = Column(String(66), nullable=False)
    depositor = Column(String(42), nullable=False)
    recipient = Column(String(42), nullable=False)
    src_contract_address = Column(String(42), nullable=False)
    dst_contract_address = Column(String(42), nullable=False)
    amount = Column(Numeric(40, 0), nullable=False)
    amount_usd = Column(Float, nullable=True)

    def __init__(
        self,
        src_blockchain,
        src_transaction_hash,
        src_from_address,
        src_to_address,
        src_fee,
        src_fee_usd,
        src_timestamp,
        dst_blockchain,
        dst_transaction_hash,
        dst_from_address,
        dst_to_address,
        dst_fee,
        dst_fee_usd,
        dst_timestamp,
        deposit_id,
        depositor,
        recipient,
        src_contract_address,
        dst_contract_address,
        amount,
        amount_usd,
    ):
        self.src_blockchain = src_blockchain
        self.src_transaction_hash = src_transaction_hash
        self.src_from_address = src_from_address
        self.src_to_address = src_to_address
        self.src_fee = src_fee
        self.src_fee_usd = src_fee_usd
        self.src_timestamp = src_timestamp
        self.dst_blockchain = dst_blockchain
        self.dst_transaction_hash = dst_transaction_hash
        self.dst_from_address = dst_from_address
        self.dst_to_address = dst_to_address
        self.dst_fee = dst_fee
        self.dst_fee_usd = dst_fee_usd
        self.dst_timestamp = dst_timestamp
        self.deposit_id = deposit_id
        self.depositor = depositor
        self.recipient = recipient
        self.src_contract_address = src_contract_address
        self.dst_contract_address = dst_contract_address
        self.amount = amount
        self.amount_usd = amount_usd