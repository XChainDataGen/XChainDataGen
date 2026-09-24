import time

from sqlalchemy import text

from config.constants import Bridge
from generator.base_generator import BaseGenerator
from generator.common.price_generator import PriceGenerator
from repository.common.repository import (
    NativeTokenRepository,
    TokenMetadataRepository,
    TokenPriceRepository,
)
from repository.database import DBSession
from repository.polynetwork.repository import (
    PolynetworkBlockchainTransactionRepository,
    PolynetworkCrossChainTransactionsRepository,
)
from utils.utils import (
    CliColor,
    CustomException,
    build_log_message_generator,
    log_error,
    log_to_cli,
)


class PolynetworkGenerator(BaseGenerator):
    CLASS_NAME = "PolynetworkGenerator"

    def __init__(self) -> None:
        super().__init__()
        self.bridge = Bridge.POLYNETWORK
        self.price_generator = PriceGenerator()

    def bind_db_to_repos(self):
        self.transactions_repo = PolynetworkBlockchainTransactionRepository(DBSession)
        self.cross_chain_transactions_repo = PolynetworkCrossChainTransactionsRepository(DBSession)

        self.token_metadata_repo = TokenMetadataRepository(DBSession)
        self.token_price_repo = TokenPriceRepository(DBSession)
        self.native_token_repo = NativeTokenRepository(DBSession)

    def generate_cross_chain_data(self):
        func_name = "generate_cross_chain_data"

        try:
            self.match_cctxs()

            start_ts = int(self.transactions_repo.get_min_timestamp()) - 86400
            end_ts = int(self.transactions_repo.get_max_timestamp()) + 86400

            self.price_generator.populate_native_tokens(
                self.bridge,
                self.native_token_repo,
                self.token_metadata_repo,
                self.token_price_repo,
                start_ts,
                end_ts,
            )

            cctxs = self.cross_chain_transactions_repo.get_unique_src_dst_contract_pairs()
            self.populate_token_info_tables(cctxs, start_ts, end_ts)

            PriceGenerator.calculate_cctx_usd_values(
                self.bridge,
                self.cross_chain_transactions_repo,
                "polynetwork_cross_chain_transactions",
                "amount",
                "src_blockchain",
                "src_contract_address",
                "src_timestamp",
                "amount_usd",
            )
            PriceGenerator.calculate_cctx_native_usd_values(
                self.bridge,
                self.cross_chain_transactions_repo,
                "polynetwork_cross_chain_transactions",
                "src_timestamp",
                "src_blockchain",
                "src_fee",
                "src_fee_usd",
            )
            PriceGenerator.calculate_cctx_native_usd_values(
                self.bridge,
                self.cross_chain_transactions_repo,
                "polynetwork_cross_chain_transactions",
                "dst_timestamp",
                "dst_blockchain",
                "dst_fee",
                "dst_fee_usd",
            )

        except Exception as e:
            exception = CustomException(
                self.CLASS_NAME,
                func_name,
                f"Error processing cross chain transactions. Error: {e}",
            )
            log_error(self.bridge, exception)

    def match_cctxs(self):
        func_name = "match_cctxs"

        start_time = time.time()
        log_to_cli(
            build_log_message_generator(self.bridge, "Matching cross-chain token transfers...")
        )

        self.cross_chain_transactions_repo.empty_table()

        query = text(
            """
            INSERT INTO polynetwork_cross_chain_transactions (
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
                amount_usd
            )
            SELECT
                src_tx.blockchain,
                src_tx.transaction_hash,
                src_tx.from_address,
                src_tx.to_address,
                src_tx.fee,
                NULL::double precision AS src_fee_usd,
                src_tx.timestamp,
                dst_tx.blockchain,
                dst_tx.transaction_hash,
                dst_tx.from_address,
                dst_tx.to_address,
                dst_tx.fee,
                NULL::double precision AS dst_fee_usd,
                dst_tx.timestamp,
                cce.tx_id,
                COALESCE(le.from_address, cce.sender),
                ue.to_address,
                le.from_asset_hash,
                ue.to_asset_hash,
                COALESCE(ue.amount, le.amount),
                NULL::double precision AS amount_usd
            FROM polynetwork_cross_chain_event cce
            JOIN polynetwork_lock_event le
                ON le.transaction_hash = cce.transaction_hash
                AND le.blockchain = cce.blockchain
            JOIN polynetwork_blockchain_transactions src_tx
                ON src_tx.transaction_hash = cce.transaction_hash
                AND src_tx.blockchain = cce.blockchain
            JOIN polynetwork_verify_header_and_execute_tx_event vhe
                ON vhe.from_chain = cce.blockchain
                AND vhe.from_chain_tx_hash = cce.tx_id
            JOIN polynetwork_unlock_event ue
                ON ue.transaction_hash = vhe.transaction_hash
                AND ue.blockchain = vhe.blockchain
            JOIN polynetwork_blockchain_transactions dst_tx
                ON dst_tx.transaction_hash = vhe.transaction_hash
                AND dst_tx.blockchain = vhe.blockchain
        """
        )

        try:
            self.cross_chain_transactions_repo.execute(query)

            size = self.cross_chain_transactions_repo.get_number_of_records()

            end_time = time.time()
            log_to_cli(
                build_log_message_generator(
                    self.bridge,
                    (
                        f"Token transfers matched in {end_time - start_time} seconds. "
                        f"Total records inserted: {size}",
                    ),
                ),
                CliColor.SUCCESS,
            )
        except Exception as e:
            raise CustomException(
                self.CLASS_NAME,
                func_name,
                f"Error matching cross-chain token transfers. Error: {e}",
            ) from e

    def populate_token_info_tables(self, cctxs, start_ts, end_ts):
        start_time = time.time()
        log_to_cli(build_log_message_generator(self.bridge, "Fetching token prices..."))

        for cctx in cctxs:
            self.price_generator.populate_token_info(
                self.bridge,
                self.token_metadata_repo,
                self.token_price_repo,
                cctx.src_blockchain,
                None,
                cctx.src_contract_address,
                None,
                start_ts,
                end_ts,
            )

        end_time = time.time()
        log_to_cli(
            build_log_message_generator(
                self.bridge,
                f"Token prices fetched in {end_time - start_time} seconds.",
            ),
            CliColor.SUCCESS,
        )
