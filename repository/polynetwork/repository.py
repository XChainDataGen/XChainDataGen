from sqlalchemy import Index, func

from repository.base import BaseRepository

from .models import (
    PolynetworkBlockchainTransaction,
    PolynetworkCrossChainEvent,
    PolynetworkCrossChainTransactions,
    PolynetworkLockEvent,
    PolynetworkUnlockEvent,
    PolynetworkVerifyHeaderAndExecuteTxEvent,
)


class PolynetworkCrossChainEventRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(PolynetworkCrossChainEvent, session_factory)

    def event_exists(self, transaction_hash: str, cctx_hash: str):
        with self.get_session() as session:
            return (
                session.query(PolynetworkCrossChainEvent)
                .filter(
                    PolynetworkCrossChainEvent.transaction_hash == transaction_hash,
                    PolynetworkCrossChainEvent.cross_chain_tx_hash == cctx_hash
                )
                .first()
            )


class PolynetworkVerifyHeaderAndExecuteTxEventRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(PolynetworkVerifyHeaderAndExecuteTxEvent, session_factory)

    def event_exists(self, transaction_hash: str, cctx_hash: str):
        with self.get_session() as session:
            return (
                session.query(PolynetworkVerifyHeaderAndExecuteTxEvent)
                .filter(
                    PolynetworkVerifyHeaderAndExecuteTxEvent.transaction_hash
                    == transaction_hash,
                    PolynetworkVerifyHeaderAndExecuteTxEvent.cross_chain_tx_hash
                    == cctx_hash
                )
                .first()
            )


class PolynetworkLockEventRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(PolynetworkLockEvent, session_factory)

    def event_exists(self, transaction_hash, from_address, to_chain, to_asset_hash, to_address):
        with self.get_session() as session:
            return (
                session.query(PolynetworkLockEvent)
                .filter(
                    PolynetworkLockEvent.transaction_hash == transaction_hash,
                    PolynetworkLockEvent.from_address == from_address,
                    PolynetworkLockEvent.to_chain == to_chain,
                    PolynetworkLockEvent.to_asset_hash == to_asset_hash,
                    PolynetworkLockEvent.to_address == to_address,
                )
                .first()
            )


class PolynetworkUnlockEventRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(PolynetworkUnlockEvent, session_factory)

    def event_exists(self, transaction_hash, to_asset_hash, to_address):
        with self.get_session() as session:
            return (
                session.query(PolynetworkUnlockEvent)
                .filter(
                    PolynetworkUnlockEvent.transaction_hash == transaction_hash,
                    PolynetworkUnlockEvent.to_asset_hash == to_asset_hash,
                    PolynetworkUnlockEvent.to_address == to_address,
                )
                .first()
            )

class PolynetworkBlockchainTransactionRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(PolynetworkBlockchainTransaction, session_factory)

    def get_transaction_by_hash(self, transaction_hash: str):
        with self.get_session() as session:
            return session.get(PolynetworkBlockchainTransaction, transaction_hash)

    def get_min_timestamp(self):
        with self.get_session() as session:
            return session.query(func.min(PolynetworkBlockchainTransaction.timestamp)).scalar()

    def get_max_timestamp(self):
        with self.get_session() as session:
            return session.query(func.max(PolynetworkBlockchainTransaction.timestamp)).scalar()


# ########## Processed Data ##########


class PolynetworkCrossChainTransactionsRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(PolynetworkCrossChainTransactions, session_factory)

    def get_number_of_records(self):
        with self.get_session() as session:
            return session.query(func.count(PolynetworkCrossChainTransactions.id)).scalar()

    def empty_table(self):
        with self.get_session() as session:
            return session.query(PolynetworkCrossChainTransactions).delete()

    def update_amount_usd(self, transaction_hash: str, amount_usd: float):
        with self.get_session() as session:
            session.query(PolynetworkCrossChainTransactions).filter(
                PolynetworkCrossChainTransactions.src_transaction_hash == transaction_hash
            ).update({"amount_usd": amount_usd})

    def get_by_src_tx_hash(self, src_tx_hash: str):
        with self.get_session() as session:
            return (
                session.query(PolynetworkCrossChainTransactions)
                .filter(PolynetworkCrossChainTransactions.src_transaction_hash == src_tx_hash)
                .first()
            )

    def get_unique_src_dst_contract_pairs(self):
        with self.get_session() as session:
            return (
                session.query(
                    PolynetworkCrossChainTransactions.src_blockchain,
                    PolynetworkCrossChainTransactions.src_contract_address,
                )
                .group_by(
                    PolynetworkCrossChainTransactions.src_blockchain,
                    PolynetworkCrossChainTransactions.src_contract_address,
                )
                .all()
            )

    def get_total_amount_usd_transacted(self):
        with self.get_session() as session:
            return session.query(func.sum(PolynetworkCrossChainTransactions.amount_usd)).scalar()


Index("ix_polynetwork_cross_chain_event_tx_hash_cctx",
      PolynetworkCrossChainEvent.transaction_hash,
      PolynetworkCrossChainEvent.cross_chain_tx_hash)

Index("ix_polynetwork_verify_header_tx_hash_cctx",
      PolynetworkVerifyHeaderAndExecuteTxEvent.transaction_hash,
      PolynetworkVerifyHeaderAndExecuteTxEvent.cross_chain_tx_hash)

Index("ix_polynetwork_lock_event_tx_hash",
      PolynetworkLockEvent.transaction_hash)

Index("ix_polynetwork_unlock_event_tx_hash_asset_addr",
      PolynetworkUnlockEvent.transaction_hash,
      PolynetworkUnlockEvent.to_asset_hash,
      PolynetworkUnlockEvent.to_address)

Index("ix_polynetwork_cctx_src_tx_hash",
      PolynetworkCrossChainTransactions.src_transaction_hash)