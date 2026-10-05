"""
Investigate why Stargate Taxi's true (de-duplicated) match rate is only
36.7% (1,663,659 / 4,528,324). Localizes exactly which stage of
match_oft_transfers' join chain drops the most rows:

  oft_sent
    -> has a src_tx row?                          (should be ~100%)
    -> has ANY oft_received row with matching guid? (regardless of blockchain)
    -> that guid-matched oft_received satisfies the blockchain direction WHERE clause?
    -> has a dst_tx row for that oft_received.transaction_hash?
    -> has a matching executor_fee_paid / dvn_fee_paid row for oft_sent.transaction_hash?

Read-only; uses the temp tables from _stargate_dedup.py.
"""

from _stargate_dedup import DEDUP_STATEMENTS, engine, run_statements
from sqlalchemy import text

FUNNEL_QUERY = """
WITH sent AS (SELECT * FROM stargate_oft_sent),
step1 AS (
    SELECT s.*, (src_tx.transaction_hash IS NOT NULL) AS has_src_tx
    FROM sent s
    LEFT JOIN stargate_blockchain_transactions src_tx
      ON src_tx.transaction_hash = s.transaction_hash
),
step2 AS (
    SELECT s1.*, r.blockchain AS recv_blockchain, r.src_blockchain AS recv_src_blockchain,
           r.transaction_hash AS recv_tx_hash,
           (r.guid IS NOT NULL) AS has_any_received_guid
    FROM step1 s1
    LEFT JOIN oft_received_dedup r ON r.guid = s1.guid
),
step3 AS (
    SELECT *,
        (has_any_received_guid AND recv_blockchain = dst_blockchain
         AND recv_src_blockchain = blockchain) AS direction_ok
    FROM step2
),
step4 AS (
    SELECT s3.*, (dst_tx.transaction_hash IS NOT NULL) AS has_dst_tx
    FROM step3 s3
    LEFT JOIN stargate_blockchain_transactions dst_tx
      ON dst_tx.transaction_hash = s3.recv_tx_hash
),
step5 AS (
    SELECT s4.*, (ef.transaction_hash IS NOT NULL) AS has_executor_fee,
           (df.transaction_hash IS NOT NULL) AS has_dvn_fee
    FROM step4 s4
    LEFT JOIN executor_fee_dedup ef ON ef.transaction_hash = s4.transaction_hash
    LEFT JOIN dvn_fee_dedup df ON df.transaction_hash = s4.transaction_hash
)
SELECT
    count(*) AS total_oft_sent,
    sum(CASE WHEN has_src_tx THEN 1 ELSE 0 END) AS has_src_tx,
    sum(CASE WHEN has_any_received_guid THEN 1 ELSE 0 END) AS has_any_received_guid,
    sum(CASE WHEN direction_ok THEN 1 ELSE 0 END) AS direction_ok,
    sum(CASE WHEN direction_ok AND has_dst_tx THEN 1 ELSE 0 END) AS direction_ok_and_has_dst_tx,
    sum(CASE WHEN direction_ok AND has_dst_tx AND has_executor_fee
             THEN 1 ELSE 0 END) AS plus_has_executor_fee,
    sum(CASE WHEN direction_ok AND has_dst_tx AND has_executor_fee AND has_dvn_fee
             THEN 1 ELSE 0 END) AS plus_has_dvn_fee_FINAL
FROM step5;
"""

# For the rows where a guid match exists but direction_ok is false: what's actually mismatched?
MISMATCH_SAMPLE_QUERY = """
WITH sent AS (SELECT * FROM stargate_oft_sent),
joined AS (
    SELECT s.transaction_hash AS sent_tx, s.blockchain AS sent_blockchain,
           s.dst_blockchain AS sent_dst_blockchain,
           r.blockchain AS recv_blockchain, r.src_blockchain AS recv_src_blockchain,
           r.transaction_hash AS recv_tx
    FROM sent s
    JOIN oft_received_dedup r ON r.guid = s.guid
)
SELECT sent_blockchain, sent_dst_blockchain, recv_blockchain, recv_src_blockchain, count(*)
FROM joined
WHERE NOT (recv_blockchain = sent_dst_blockchain AND recv_src_blockchain = sent_blockchain)
GROUP BY 1,2,3,4
ORDER BY count(*) DESC
LIMIT 20;
"""

# For guid with NO match at all in oft_received: distribution by (blockchain -> dst_blockchain)
NO_MATCH_DIST_QUERY = """
WITH sent AS (SELECT * FROM stargate_oft_sent)
SELECT s.blockchain AS src, s.dst_blockchain AS dst, count(*)
FROM sent s
LEFT JOIN oft_received_dedup r ON r.guid = s.guid
WHERE r.guid IS NULL
GROUP BY 1,2
ORDER BY count(*) DESC
LIMIT 20;
"""

with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")

    print("=== Setup ===")
    run_statements(conn, DEDUP_STATEMENTS)

    print("\n=== Funnel ===")
    row = conn.execute(text(FUNNEL_QUERY)).mappings().first()
    total = row["total_oft_sent"]
    for k, v in row.items():
        pct = f"({v / total:.1%})" if k != "total_oft_sent" else ""
        print(f"  {k}: {v:,} {pct}")

    print("\n=== Guid matched but direction mismatch (top 20) ===")
    for row in conn.execute(text(MISMATCH_SAMPLE_QUERY)).mappings():
        print(" ", dict(row))

    print("\n=== No oft_received match at all, by (src -> dst) (top 20) ===")
    for row in conn.execute(text(NO_MATCH_DIST_QUERY)).mappings():
        print(" ", dict(row))
