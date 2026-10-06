"""
Journal revision, step 1: extract a de-duplicated subset of the eight
source->destination routes highlighted in the paper's Section 4 (Empirical
Analysis), from the full joined dataset (analysis/data/grouped/all_ccc_protocols.csv).

`all_ccc_protocols.csv` is affected by a known duplicate-row extraction bug
in Stargate Taxi and Bus mode (see README.md "Expected record counts" and
the paper's Internal Validity section for the root cause). This script
applies a DISTINCT over the analysis-relevant columns to remove exact
duplicate rows before any further analysis; it does not touch the source
CSV or the database.

Output: routes_dedup.csv (one row per de-duplicated cctx, restricted to the
eight routes), used as the input to 02_route_stats.py.

Run from analysis/journal_revision/ (expects ../data/grouped/all_ccc_protocols.csv).
"""

import duckdb

ROUTES = [
    ("ethereum", "avalanche"),
    ("avalanche", "ethereum"),
    ("ethereum", "base"),
    ("avalanche", "base"),
    ("base", "ethereum"),
    ("base", "avalanche"),
    ("arbitrum", "base"),
    ("base", "arbitrum"),
]

OUTPUT_PATH = "../data/journal_revision/routes_dedup.csv"

route_filter = " OR ".join(f"(src_blockchain='{s}' AND dst_blockchain='{d}')" for s, d in ROUTES)

QUERY = f"""
COPY (
  SELECT DISTINCT bridge, src_blockchain, dst_blockchain, latency, user_cost, operator_cost,
         amount_usd, amount_received_ld_usd, output_amount_usd,
         adjusted_src_fee_usd, adjusted_dst_fee_usd, bus_fare_usd, fee_token_amount_usd,
         executor_fee_usd, dvn_fee_usd, src_symbol
  FROM read_csv('../data/grouped/all_ccc_protocols.csv')
  WHERE ({route_filter})
) TO '{OUTPUT_PATH}' (HEADER, DELIMITER ',')
"""

if __name__ == "__main__":
    con = duckdb.connect()
    con.execute("PRAGMA threads=8")
    con.execute(QUERY)
    n = con.execute(f"SELECT count(*) FROM read_csv('{OUTPUT_PATH}')").fetchone()[0]
    print(f"Wrote {n:,} de-duplicated rows across {len(ROUTES)} routes to {OUTPUT_PATH}")
