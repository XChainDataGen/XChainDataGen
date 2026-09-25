# Journal revision analysis

Scripts written during peer review for *XChainDataGen: A Cross-Chain Dataset
Generation Framework* (submitted to *Blockchain: Research and Applications*),
addressing reviewer requests to (a) test protocol comparisons per exact route
rather than pooled by L1/L2 direction, (b) report CCIP bootstrap confidence
intervals, (c) decompose user cost into its constituent components, and
(d) report extraction/matching rates per bridge. Referenced from the paper's
Appendix A and Section 6.1 (Internal Validity).

## Pipeline

Run in order from this directory. Scripts 01–05 read
`../data/grouped/all_ccc_protocols.csv` (the joined dataset produced by
`analysis/generate_csv.ipynb`) via DuckDB and require no database connection.
Scripts 06–07 connect directly to the local Postgres instance (same
convention as `analysis/generate_csv.ipynb`:
`postgresql+psycopg2://admin:pwd@localhost:5432/<bridge>`).

| # | Script | Produces | Feeds |
|---|---|---|---|
| 01 | `01_extract_routes_deduped.py` | `../data/journal_revision/routes_dedup.csv` | input to 02 |
| 02 | `02_route_stats.py` | `../data/journal_revision/{desc_stats,kruskal_wallis,pairwise_mannwhitney,ccip_bootstrap_ci}.csv` | input to 04 |
| 03 | `03_cost_decomposition.py` | `../data/journal_revision/cost_decomposition.csv` | input to 05 |
| 04 | `04_gen_latex_tables.py` | `latex_output/stats_summary.tex` | paper Appendix A, Tables A.10–A.12 |
| 05 | `05_gen_cost_decomposition_table.py` | `latex_output/cost_decomposition.tex` | paper Table 8 (Section 5.2) |
| 06 | `06_dedup_stargate_and_rematch.py` | printed report only | paper Section 6.1 (corrected Stargate Taxi/Bus counts) |
| 07 | `07_investigate_taxi_match_rate.py` | printed report only | paper Section 6.1 (Taxi match-rate explanation) |

`latex_output/` is committed since it's small and shows exactly what feeds
the paper; the `../data/journal_revision/*.csv` intermediates are not
(`analysis/data/` is gitignored) since they're multi-hundred-MB and fully
reproducible from `all_ccc_protocols.csv`.

## What 06 and 07 found

The database tables `stargate_executor_fee_paid`, `stargate_dvn_fee_paid`,
and `stargate_oft_received` are missing the `event_exists()` idempotency
guard present on every other extracted event table (see
`repository/stargate/repository.py` and `extractor/stargate/handler.py`).
A non-idempotent re-extraction can insert duplicate rows into these three
tables; because the cctx-generation queries in
`generator/stargate/generator.py` join against them without
de-duplicating, this inflates the Stargate Taxi and Bus counts reported in
`analysis/data/grouped/all_ccc_protocols.csv` and, downstream, Table 2 of
the paper (Taxi 1.98x, Bus 1.29x inflated as of this writing). `06` computes
the corrected counts by re-running the exact matching SQL from
`generator.py` against de-duplicated, indexed temp tables. `07` explains an
initially-confusing side effect of the same investigation: Stargate Taxi's
naive match rate looked like only ~37% before accounting for the fact that
`stargate_oft_sent` is shared between genuine Taxi transfers and Bus-mode
boarding transactions (the latter carry a placeholder all-zero message
identifier by design, since the real cross-chain message is only assigned
once the bus departs) -- not a bug, just a shared table. See the "Expected
record counts" section of the repository root README for the summary
table, and the paper's Section 6.1 for the full writeup.

This is a known, root-caused issue in the current data release. Fixing it
requires adding the missing idempotency guards and a full dataset
regeneration, which had not landed as of this writing.
