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
from repository.nomad.repository import (
    NomadBlockchainTransactionRepository,
    NomadCrossChainTransactionRepository,
)
from utils.utils import (
    CliColor,
    CustomException,
    build_log_message_generator,
    log_error,
    log_to_cli,
)


class NomadGenerator(BaseGenerator):
    CLASS_NAME = "NomadGenerator"

    def __init__(self) -> None:
        super().__init__()
        self.bridge = Bridge.NOMAD
        self.price_generator = PriceGenerator()

    def bind_db_to_repos(self):
        self.transactions_repo = NomadBlockchainTransactionRepository(DBSession)
        self.cross_chain_transactions_repo = NomadCrossChainTransactionRepository(DBSession)

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
                "nomad_cross_chain_transactions",
                "amount",
                "src_blockchain",
                "src_contract_address",
                "src_timestamp",
                "amount_usd",
            )
            PriceGenerator.calculate_cctx_usd_values(
                self.bridge,
                self.cross_chain_transactions_repo,
                "nomad_cross_chain_transactions",
                "amount",
                "dst_blockchain",
                "dst_contract_address",
                "dst_timestamp",
                "amount_usd",
            )
            PriceGenerator.calculate_cctx_native_usd_values(
                self.bridge,
                self.cross_chain_transactions_repo,
                "nomad_cross_chain_transactions",
                "src_timestamp",
                "src_blockchain",
                "src_fee",
                "src_fee_usd",
            )
            PriceGenerator.calculate_cctx_native_usd_values(
                self.bridge,
                self.cross_chain_transactions_repo,
                "nomad_cross_chain_transactions",
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
            INSERT INTO nomad_cross_chain_transactions (
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
                deposit_hash,
                depositor,
                recipient,
                src_contract_address,
                dst_contract_address,
                amount,
                amount_usd
            )
            SELECT
                dispatch.src_blockchain,
                src_tx.transaction_hash,
                src_tx.from_address,
                src_tx.to_address,
                src_tx.fee,
                NULL::double precision AS src_fee_usd,
                src_tx.timestamp,
                dispatch.dst_blockchain,
                dst_tx.transaction_hash,
                dst_tx.from_address,
                dst_tx.to_address,
                dst_tx.fee,
                NULL::double precision AS dst_fee_usd,
                dst_tx.timestamp,
                dispatch.message_hash,
                COALESCE(send.depositor, src_tx.from_address),
                dispatch.recipient,
                send.input_token,
                receive.output_token,
                dispatch.amount,
                NULL::double precision AS amount_usd
            FROM nomad_home_dispatch dispatch
            JOIN nomad_blockchain_transactions src_tx
                ON src_tx.transaction_hash = dispatch.transaction_hash
                AND src_tx.blockchain = dispatch.src_blockchain
            LEFT JOIN nomad_router_send send
                ON send.transaction_hash = dispatch.transaction_hash
                AND send.blockchain = dispatch.src_blockchain
            JOIN nomad_replica_process process
                ON process.message_hash = dispatch.message_hash
                AND process.blockchain = dispatch.dst_blockchain
            JOIN nomad_router_receive receive
                ON receive.transaction_hash = process.transaction_hash
                AND receive.src_blockchain = dispatch.src_blockchain
                AND receive.blockchain = dispatch.dst_blockchain
            JOIN nomad_blockchain_transactions dst_tx
                ON dst_tx.transaction_hash = process.transaction_hash
                AND dst_tx.blockchain = dispatch.dst_blockchain
            WHERE process.success = 1;
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
                cctx.dst_blockchain,
                cctx.src_contract_address,
                cctx.dst_contract_address,
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
