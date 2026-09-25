"""
Journal revision: decompose user_cost into gas / explicit protocol fee /
price-delta components, per bridge, on the full de-duplicated dataset.

The user_cost formula per bridge is defined in
analysis/generate_csv.ipynb (calculate_user_and_operator_cost and
calculate_user_and_operator_cost_stargate_bus). This script reproduces
that formula's components directly against
analysis/data/grouped/all_ccc_protocols.csv:

  CCTP, Stargate Taxi : user_cost = gas only
  CCIP                : user_cost = gas + fee_token_amount_usd (flat fee)
  Stargate Bus        : user_cost = adjusted_user_fee_usd (gas)
                                     + bus_fare_usd (flat fare)
                                     + (amount_sent_ld_usd - amount_received_ld_usd) (price delta)
  Across               : user_cost = adjusted_src_fee_usd (gas)
                                     + (input_amount_usd - output_amount_usd) (price delta)

Negative-cost rows (the arbitrage/price-oracle anomalies discussed in
Section 4.2.4 of the paper) are excluded, since a negative denominator
makes the percentage-of-total breakdown meaningless.

Output: cost_decomposition.csv, one row per bridge with median USD and
median per-transaction percentage share of each component. Feeds
tables/cost_decomposition.tex via gen_cost_decomposition_table.py.

Run from analysis/journal_revision/.
"""

import duckdb
import pandas as pd

OUTPUT_PATH = "../data/journal_revision/cost_decomposition.csv"

QUERY = """
WITH dedup AS (
  SELECT DISTINCT bridge,
         TRY_CAST(user_cost AS DOUBLE) AS user_cost,
         TRY_CAST(adjusted_src_fee_usd AS DOUBLE) AS adjusted_src_fee_usd,
         TRY_CAST(adjusted_user_fee_usd AS DOUBLE) AS adjusted_user_fee_usd,
         TRY_CAST(fee_token_amount_usd AS DOUBLE) AS fee_token_amount_usd,
         TRY_CAST(bus_fare_usd AS DOUBLE) AS bus_fare_usd,
         TRY_CAST(amount_sent_ld_usd AS DOUBLE) AS amount_sent_ld_usd,
         TRY_CAST(amount_received_ld_usd AS DOUBLE) AS amount_received_ld_usd,
         TRY_CAST(input_amount_usd AS DOUBLE) AS input_amount_usd,
         TRY_CAST(output_amount_usd AS DOUBLE) AS output_amount_usd
  FROM read_csv('../data/grouped/all_ccc_protocols.csv', all_varchar=true)
  WHERE bridge IN ('cctp','ccip','stargate_oft','stargate_bus','across')
),
components AS (
  SELECT bridge, user_cost,
    CASE WHEN bridge='stargate_bus' THEN adjusted_user_fee_usd
         ELSE adjusted_src_fee_usd END AS gas_usd,
    CASE
      WHEN bridge='ccip' THEN COALESCE(fee_token_amount_usd,0)
      WHEN bridge='stargate_bus' THEN COALESCE(bus_fare_usd,0)
      ELSE 0 END AS protocol_fee_usd,
    CASE
      WHEN bridge='across' THEN COALESCE(input_amount_usd,0)-COALESCE(output_amount_usd,0)
      WHEN bridge='stargate_bus'
        THEN COALESCE(amount_sent_ld_usd,0)-COALESCE(amount_received_ld_usd,0)
      ELSE 0 END AS price_delta_usd
  FROM dedup
  WHERE user_cost IS NOT NULL AND user_cost > 0
)
SELECT bridge,
  count(*) n,
  median(gas_usd) med_gas_usd,
  median(protocol_fee_usd) med_fee_usd,
  median(price_delta_usd) med_delta_usd,
  median(user_cost) med_total_usd,
  median(gas_usd/user_cost)*100 pct_gas,
  median(protocol_fee_usd/user_cost)*100 pct_fee,
  median(price_delta_usd/user_cost)*100 pct_delta
FROM components
GROUP BY bridge
ORDER BY bridge
"""

if __name__ == "__main__":
    con = duckdb.connect()
    con.execute("PRAGMA threads=8")
    df = con.execute(QUERY).df()
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nWrote {OUTPUT_PATH}")
