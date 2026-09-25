"""
Deduplicate the Stargate raw event tables affected by the missing
event_exists() guard (stargate_oft_received, stargate_executor_fee_paid,
stargate_dvn_fee_paid -- see repository/stargate/repository.py and
extractor/stargate/handler.py), then re-run the exact matching queries
from generator/stargate/generator.py (match_oft_transfers,
match_bus_transactions) against the de-duplicated data to get corrected
Taxi/Bus matched counts.

Unlike the first version of this script (which used bare CTEs and never
finished after 6+ hours -- Postgres can't index a CTE's output, so every
downstream join over tens of millions of rows fell back to slow plans),
this version materializes each de-duplicated table into an indexed TEMP
TABLE first. Everything happens inside one transaction-scoped connection
so the temp tables are visible to the later queries; nothing is written
to the permanent database.
"""

import time

from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://admin:pwd@localhost:5432/stargate")

SETUP_STATEMENTS = [
    # --- de-duplicated, indexed temp tables ---
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
    # --- helper views matching generator.py's ROW_NUMBER CTEs, materialized too ---
    """
    CREATE TEMP TABLE bus_rode_indexed AS
    SELECT *, ROW_NUMBER() OVER (PARTITION BY transaction_hash) AS event_index
    FROM stargate_bus_rode;
    """,
    "CREATE INDEX ON bus_rode_indexed (transaction_hash, event_index);",
    "CREATE INDEX ON bus_rode_indexed (dst_blockchain, blockchain, ticket_id);",
    """
    CREATE TEMP TABLE oft_sent_indexed AS
    SELECT *, ROW_NUMBER() OVER (PARTITION BY transaction_hash) AS event_index
    FROM stargate_oft_sent;
    """,
    "CREATE INDEX ON oft_sent_indexed (transaction_hash, event_index);",
    "CREATE INDEX ON oft_sent_indexed (guid);",
    """
    CREATE TEMP TABLE oft_received_bus AS
    SELECT DISTINCT blockchain, transaction_hash, guid, amount_received_ld,
           to_address, contract_address
    FROM oft_received_dedup;
    """,
    "CREATE INDEX ON oft_received_bus (guid, to_address);",
    "CREATE INDEX ON oft_received_bus (transaction_hash);",
]

TAXI_QUERY = """
SELECT count(*)
FROM stargate_oft_sent oft_sent
JOIN stargate_blockchain_transactions src_tx
  ON src_tx.transaction_hash = oft_sent.transaction_hash
JOIN executor_fee_dedup executor_fee_paid
  ON executor_fee_paid.transaction_hash = oft_sent.transaction_hash
JOIN dvn_fee_dedup dvn_fee_paid
  ON dvn_fee_paid.transaction_hash = oft_sent.transaction_hash
JOIN oft_received_dedup oft_received ON oft_received.guid = oft_sent.guid
JOIN stargate_blockchain_transactions dst_tx
  ON dst_tx.transaction_hash = oft_received.transaction_hash
WHERE oft_sent.dst_blockchain = oft_received.blockchain
AND oft_sent.blockchain = oft_received.src_blockchain;
"""

BUS_QUERY = """
SELECT count(*)
FROM stargate_bus_driven bus_driven
JOIN bus_rode_indexed bus_rode
  ON bus_rode.dst_blockchain = bus_driven.dst_blockchain
  AND bus_driven.blockchain = bus_rode.blockchain
  AND bus_rode.ticket_id BETWEEN bus_driven.start_ticket_id
    AND (bus_driven.start_ticket_id + bus_driven.num_passengers - 1)
JOIN oft_sent_indexed oft_sent
  ON oft_sent.transaction_hash = bus_rode.transaction_hash
  AND bus_rode.event_index = oft_sent.event_index
JOIN stargate_blockchain_transactions user_tx
  ON user_tx.transaction_hash = oft_sent.transaction_hash
JOIN stargate_blockchain_transactions bus_tx
  ON bus_tx.transaction_hash = bus_driven.transaction_hash
JOIN oft_received_bus oft_received
  ON oft_received.guid = bus_driven.guid
  AND lower(oft_received.to_address) = bus_rode.passenger AND (
    oft_sent.amount_received_ld = oft_received.amount_received_ld OR
    oft_sent.amount_received_ld = oft_received.amount_received_ld * 1e12 OR
    oft_sent.amount_received_ld * 1e12 = oft_received.amount_received_ld
)
JOIN executor_fee_dedup executor_fee_paid
  ON executor_fee_paid.transaction_hash = bus_driven.transaction_hash
JOIN dvn_fee_dedup dvn_fee_paid
  ON dvn_fee_paid.transaction_hash = bus_driven.transaction_hash
JOIN stargate_blockchain_transactions dst_tx
  ON dst_tx.transaction_hash = oft_received.transaction_hash
WHERE bus_rode.blockchain = oft_sent.blockchain
AND bus_rode.blockchain = bus_driven.blockchain
AND oft_sent.blockchain = bus_driven.blockchain;
"""

RAW_COUNT_QUERIES = {
    "stargate_oft_sent (extraction, Taxi+Bus deposits)": ("SELECT count(*) FROM stargate_oft_sent"),
    "stargate_bus_rode (extraction, Bus tickets -- PK-guaranteed unique)": (
        "SELECT count(*) FROM stargate_bus_rode"
    ),
    "stargate_oft_received raw": "SELECT count(*) FROM stargate_oft_received",
    "stargate_oft_received de-duplicated": "SELECT count(*) FROM oft_received_dedup",
    "stargate_executor_fee_paid raw": "SELECT count(*) FROM stargate_executor_fee_paid",
    "stargate_executor_fee_paid de-duplicated": "SELECT count(*) FROM executor_fee_dedup",
    "stargate_dvn_fee_paid raw": "SELECT count(*) FROM stargate_dvn_fee_paid",
    "stargate_dvn_fee_paid de-duplicated": "SELECT count(*) FROM dvn_fee_dedup",
    "stargate_oft_cross_chain_transactions (Taxi, CURRENT/buggy matched count)": (
        "SELECT count(*) FROM stargate_oft_cross_chain_transactions"
    ),
    "stargate_bus_cross_chain_transactions (Bus, CURRENT/buggy matched count)": (
        "SELECT count(*) FROM stargate_bus_cross_chain_transactions"
    ),
}

with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")

    print("=== Building de-duplicated, indexed temp tables ===")
    for stmt in SETUP_STATEMENTS:
        t0 = time.time()
        conn.execute(text(stmt))
        print(f"  [{time.time() - t0:6.1f}s] {stmt.strip().splitlines()[0][:80]}")

    print("\n=== Raw / de-duplicated table sizes ===")
    results = {}
    for label, q in RAW_COUNT_QUERIES.items():
        n = conn.execute(text(q)).scalar()
        results[label] = n
        print(f"{label}: {n:,}")

    print("\n=== Re-running generator.py's matching queries against de-duplicated inputs ===")

    t0 = time.time()
    taxi_corrected = conn.execute(text(TAXI_QUERY)).scalar()
    print(
        f"\n[{time.time() - t0:.1f}s] Stargate Taxi -- corrected matched count: {taxi_corrected:,}"
    )
    taxi_old = results["stargate_oft_cross_chain_transactions (Taxi, CURRENT/buggy matched count)"]
    taxi_extraction = results["stargate_oft_sent (extraction, Taxi+Bus deposits)"]
    print(
        f"  current (buggy) matched count: {taxi_old:,}  "
        f"({taxi_old / taxi_corrected:.2f}x inflation)"
    )
    print(f"  extraction (oft_sent) count:   {taxi_extraction:,}")
    print(f"  true match rate (corrected/extraction): {taxi_corrected / taxi_extraction:.1%}")

    t0 = time.time()
    bus_corrected = conn.execute(text(BUS_QUERY)).scalar()
    print(f"\n[{time.time() - t0:.1f}s] Stargate Bus -- corrected matched count: {bus_corrected:,}")
    bus_old = results["stargate_bus_cross_chain_transactions (Bus, CURRENT/buggy matched count)"]
    bus_extraction = results["stargate_bus_rode (extraction, Bus tickets -- PK-guaranteed unique)"]
    print(
        f"  current (buggy) matched count: {bus_old:,}  ({bus_old / bus_corrected:.2f}x inflation)"
    )
    print(f"  extraction (bus_rode tickets): {bus_extraction:,}")
    print(f"  true match rate (corrected/extraction): {bus_corrected / bus_extraction:.1%}")
