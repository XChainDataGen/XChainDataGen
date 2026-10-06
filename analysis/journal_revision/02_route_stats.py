"""
Same-route statistical tests for the XChainDataGen paper (reviewer-requested
extension): per exact source->destination route (not pooled by L1/L2
direction category), for each metric (latency, user_cost):
  - descriptive stats (n, Q1, Q2, Q3, IQR) per bridge
  - Kruskal-Wallis H test across all bridges present on that route
  - pairwise Mann-Whitney U tests (two-sided), Holm-Bonferroni corrected
  - rank-biserial correlation effect size for each pair
  - for CCIP specifically: 10,000-resample bootstrap 95% CI of the median

Input: routes_dedup.csv, produced from analysis/data/grouped/all_ccc_protocols.csv
via a DISTINCT (i.e. de-duplicated) query restricted to the 8 routes already
highlighted in the paper's Section 4 subsections.

Note on reproducibility: Kruskal-Wallis statistics, p-values, effect sizes,
and all descriptive quantiles are exactly reproducible across re-runs. The
CCIP bootstrap CI *bounds* (Table A.12 in the paper) can shift by a small
amount (<0.2% in testing) between separate runs of the full pipeline,
because DuckDB's DISTINCT in 01_extract_routes_deduped.py does not
guarantee a stable row order, which shifts which values np.random.choice
draws even with a fixed seed. The medians those CIs are centered on are
unaffected.
"""

import itertools

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu

np.random.seed(42)

df = pd.read_csv("../data/journal_revision/routes_dedup.csv")

ROUTES = [
    ("ethereum", "avalanche", "L1->L1"),
    ("avalanche", "ethereum", "L1->L1"),
    ("ethereum", "base", "L1->L2"),
    ("avalanche", "base", "L1->L2"),
    ("base", "ethereum", "L2->L1"),
    ("base", "avalanche", "L2->L1"),
    ("arbitrum", "base", "L2->L2"),
    ("base", "arbitrum", "L2->L2"),
]

BRIDGE_ORDER = ["cctp", "ccip", "stargate_oft", "stargate_bus", "across"]
METRICS = ["latency", "user_cost"]

N_BOOT = 10_000


def holm_bonferroni(pvals):
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running_max = 0.0
    for rank, idx in enumerate(order):
        factor = m - rank
        val = pvals[idx] * factor
        running_max = max(running_max, val)
        adj[idx] = min(running_max, 1.0)
    return adj


def bootstrap_median_ci(x):
    boot = np.empty(N_BOOT)
    for i in range(N_BOOT):
        boot[i] = np.median(np.random.choice(x, size=len(x), replace=True))
    return np.percentile(boot, [2.5, 97.5])


def effect_label(r):
    for threshold, label in [(0.5, "large"), (0.3, "medium"), (0.1, "small")]:
        if abs(r) >= threshold:
            return label
    return "negligible"


OUT = "../data/journal_revision"
desc_rows, kw_rows, pairwise_rows, ci_rows = [], [], [], []

for src, dst, direction in ROUTES:
    route_df = df[(df["src_blockchain"] == src) & (df["dst_blockchain"] == dst)]

    for metric in METRICS:
        key = {"route": f"{src}->{dst}", "direction": direction, "metric": metric}
        groups = {}
        for bridge in BRIDGE_ORDER:
            vals = route_df.loc[route_df["bridge"] == bridge, metric].dropna().to_numpy()
            if len(vals) >= 5:  # need a minimally sensible sample
                groups[bridge] = vals

        for bridge, vals in groups.items():
            q1, q2, q3 = np.percentile(vals, [25, 50, 75])
            desc_rows.append(
                {
                    **key,
                    "bridge": bridge,
                    "n": len(vals),
                    "Q1": q1,
                    "Q2": q2,
                    "Q3": q3,
                    "IQR": q3 - q1,
                }
            )
            if bridge == "ccip":
                lo, hi = bootstrap_median_ci(vals)
                ci_rows.append(
                    {
                        **key,
                        "bridge": bridge,
                        "n": len(vals),
                        "median": q2,
                        "ci_lo": lo,
                        "ci_hi": hi,
                    }
                )

        if len(groups) < 2:
            continue

        H, p_kw = kruskal(*groups.values())
        kw_rows.append(
            {
                **key,
                "n_groups": len(groups),
                "n_total": sum(map(len, groups.values())),
                "H": H,
                "p": p_kw,
            }
        )

        pairs = list(itertools.combinations(groups, 2))
        results = [mannwhitneyu(groups[a], groups[b], alternative="two-sided") for a, b in pairs]
        raw_p = np.array([res.pvalue for res in results])
        adj_p = holm_bonferroni(raw_p)
        for (a, b), res, p_raw, p_adj in zip(pairs, results, raw_p, adj_p, strict=True):
            # rank-biserial r = 1 - 2U/(n1*n2); positive => a tends larger than b
            r = 1 - 2 * res.statistic / (len(groups[a]) * len(groups[b]))
            pairwise_rows.append(
                {
                    **key,
                    "bridge_a": a,
                    "bridge_b": b,
                    "n_a": len(groups[a]),
                    "n_b": len(groups[b]),
                    "p_raw": p_raw,
                    "p_adj": p_adj,
                    "r": r,
                    "effect": effect_label(r),
                    "sig": p_adj < 0.05,
                }
            )

outputs = {
    "desc_stats": desc_rows,
    "kruskal_wallis": kw_rows,
    "pairwise_mannwhitney": pairwise_rows,
    "ccip_bootstrap_ci": ci_rows,
}
for name, rows in outputs.items():
    out_df = pd.DataFrame(rows)
    out_df.to_csv(f"{OUT}/{name}.csv", index=False)
    print(f"{name}: {len(out_df)} rows -> {OUT}/{name}.csv")

pw = pd.DataFrame(pairwise_rows)
print(f"Pairwise comparisons: {len(pw)}, significant after Holm-Bonferroni: {pw['sig'].sum()}")
