from sqlalchemy import Index, func

from repository.base import BaseRepository

from .models import (
    NomadBlockchainTransaction,
    NomadCrossChainTransaction,
    NomadEthHelperSend,
    NomadHomeDispatch,
    NomadReplicaProcess,
    NomadRouterReceive,
    NomadRouterSend,
)


class NomadRouterSendRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadRouterSend, session_factory)
    
    # TODO Verify if arguments correct
    def event_exists(self, transaction_hash: str):
        with self.get_session() as session:
            return (
                session.query(NomadRouterSend)
                .filter(NomadRouterSend.transaction_hash == transaction_hash)
                .first()
            )
        
class NomadRouterReceiveRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadRouterReceive, session_factory)
    
    # TODO Verify if arguments correct
    def event_exists(self, nonce: int, blockchain: str, src_blockchain: str):
        with self.get_session() as session:
            return (
                session.query(NomadRouterReceive)
                .filter(NomadRouterReceive.nonce == nonce)
                .filter(NomadRouterReceive.blockchain == blockchain)
                .filter(NomadRouterReceive.src_blockchain == src_blockchain)
                .first()
            )
        
class NomadEthHelperSendRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadEthHelperSend, session_factory)
    
    # TODO Verify if arguments correct
    def event_exists(self, transaction_hash: str):
        with self.get_session() as session:
            return (
                session.query(NomadEthHelperSend)
                .filter(NomadEthHelperSend.transaction_hash == transaction_hash)
                .first()
            )
        
class NomadReplicaProcessRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadReplicaProcess, session_factory)
    
    # TODO Verify if arguments correct
    def event_exists(self, message_hash: str, blockchain: str):
        with self.get_session() as session:
            return (
                session.query(NomadReplicaProcess)
                .filter(NomadReplicaProcess.message_hash == message_hash)
                .filter(NomadReplicaProcess.blockchain == blockchain)
                .first()
            )
        
class NomadHomeDispatchRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadHomeDispatch, session_factory)
    
    # TODO Verify if arguments correct
    def event_exists(self, message_hash: str, blockchain: str):
        with self.get_session() as session:
            return (
                session.query(NomadHomeDispatch)
                .filter(NomadHomeDispatch.message_hash == message_hash)
                .filter(NomadHomeDispatch.blockchain == blockchain)
                .first()
            )

class NomadBlockchainTransactionRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadBlockchainTransaction, session_factory)

    def get_transaction_by_hash(self, transaction_hash: str):
        with self.get_session() as session:
            return session.get(NomadBlockchainTransaction, transaction_hash)

    def get_min_timestamp(self):
        with self.get_session() as session:
            return session.query(func.min(NomadBlockchainTransaction.timestamp)).scalar()

    def get_max_timestamp(self):
        with self.get_session() as session:
            return session.query(func.max(NomadBlockchainTransaction.timestamp)).scalar()


########## Processed Data ##########

class NomadCrossChainTransactionRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(NomadCrossChainTransaction, session_factory)

    def get_number_of_records(self):
        with self.get_session() as session:
            return session.query(func.count(NomadCrossChainTransaction.id)).scalar()

    def empty_table(self):
        with self.get_session() as session:
            return session.query(NomadCrossChainTransaction).delete()

    def update_amount_usd(self, transaction_hash: str, amount_usd: float):
        with self.get_session() as session:
            session.query(NomadCrossChainTransaction).filter(
                NomadCrossChainTransaction.src_transaction_hash == transaction_hash
            ).update({"amount_usd": amount_usd})

    def get_by_src_tx_hash(self, src_tx_hash: str):
        with self.get_session() as session:
            return (
                session.query(NomadCrossChainTransaction)
                .filter(NomadCrossChainTransaction.src_transaction_hash == src_tx_hash)
                .first()
            )

    def get_unique_src_dst_contract_pairs(self):
        with self.get_session() as session:
            return (
                session.query(
                    NomadCrossChainTransaction.src_blockchain,
                    NomadCrossChainTransaction.src_contract_address,
                    NomadCrossChainTransaction.dst_blockchain,
                    NomadCrossChainTransaction.dst_contract_address,
                )
                .group_by(
                    NomadCrossChainTransaction.src_blockchain,
                    NomadCrossChainTransaction.src_contract_address,
                    NomadCrossChainTransaction.dst_blockchain,
                    NomadCrossChainTransaction.dst_contract_address,
                )
                .all()
            )

    def get_total_amount_usd_transacted(self):
        with self.get_session() as session:
            return session.query(func.sum(NomadCrossChainTransaction.amount_usd)).scalar()

Index("nomad_router_receive_nonce_blockchain_idx",
      NomadRouterReceive.nonce,
      NomadRouterReceive.blockchain,
      NomadRouterReceive.src_blockchain,
)
Index("nomad_replica_process_message_hash_blockchain_idx", 
      NomadReplicaProcess.message_hash, 
      NomadReplicaProcess.blockchain
)
Index("nomad_home_dispatch_message_hash_blockchain_idx", 
      NomadHomeDispatch.message_hash, 
      NomadHomeDispatch.blockchain
)
