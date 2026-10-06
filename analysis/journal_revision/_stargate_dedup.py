"""Shared setup for scripts 05 and 06: connection to the local Stargate Postgres database and
indexed TEMP tables holding de-duplicated copies of the three Stargate event tables that lack
the event_exists() idempotency guard (stargate_oft_received, stargate_executor_fee_paid,
stargate_dvn_fee_paid; see repository/stargate/repository.py).

Postgres cannot index a CTE's output, so each de-duplicated table is materialized as an indexed
TEMP TABLE (scoped to the connection; nothing is written to the permanent database).
"""

import time

from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://admin:pwd@localhost:5432/stargate")

DEDUP_STATEMENTS = [
    """
    CREATE TEMP TABLE oft_received_dedup AS
    SELECT DISTINCT ON (blockchain, transaction_hash, guid, amount_received_ld) *
    FROM stargate_oft_received
    ORDER BY blockchain, transaction_hash, guid, amount_received_ld, id;
    """,
    "CREATE INDEX ON oft_received_dedup (guid);",
    "CREATE INDEX ON oft_received_dedup (transaction_hash);",
    """
    CREATE TEMP TABLE executor_fee_dedup AS
    SELECT DISTINCT ON (blockchain, transaction_hash) *
    FROM stargate_executor_fee_paid
    ORDER BY blockchain, transaction_hash, id;
    """,
    "CREATE INDEX ON executor_fee_dedup (transaction_hash);",
    """
    CREATE TEMP TABLE dvn_fee_dedup AS
    SELECT DISTINCT ON (blockchain, transaction_hash) *
    FROM stargate_dvn_fee_paid
    ORDER BY blockchain, transaction_hash, id;
    """,
    "CREATE INDEX ON dvn_fee_dedup (transaction_hash);",
    "CREATE INDEX IF NOT EXISTS ix_bt_txhash "
    "ON stargate_blockchain_transactions (transaction_hash);",
]


def run_statements(conn, statements):
    for stmt in statements:
        t0 = time.time()
        conn.execute(text(stmt))
        print(f"  [{time.time() - t0:6.1f}s] {stmt.strip().splitlines()[0][:80]}")
