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


def rank_biserial(x, y):
    """r = 1 - 2U/(n1*n2); positive r => x tends larger than y."""
    n1, n2 = len(x), len(y)
    U1, _ = mannwhitneyu(x, y, alternative="two-sided")
    return 1 - (2 * U1) / (n1 * n2)


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


def bootstrap_median_ci(x, n_boot=N_BOOT, alpha=0.05):
    x = np.asarray(x)
    boot_medians = np.empty(n_boot)
    n = len(x)
    for i in range(n_boot):
        sample = np.random.choice(x, size=n, replace=True)
        boot_medians[i] = np.median(sample)
    lo, hi = np.percentile(boot_medians, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return lo, hi


def effect_label(r):
    ar = abs(r)
    if ar >= 0.5:
        return "large"
    if ar >= 0.3:
        return "medium"
    if ar >= 0.1:
        return "small"
    return "negligible"


desc_rows = []
kw_rows = []
pairwise_rows = []
ci_rows = []

for src, dst, direction in ROUTES:
    route_df = df[(df["src_blockchain"] == src) & (df["dst_blockchain"] == dst)]

    for metric in METRICS:
        groups = {}
        for bridge in BRIDGE_ORDER:
            vals = route_df.loc[route_df["bridge"] == bridge, metric].dropna().to_numpy()
            if len(vals) >= 5:  # need a minimally sensible sample
                groups[bridge] = vals

        for bridge, vals in groups.items():
            q1, q2, q3 = np.percentile(vals, [25, 50, 75])
            desc_rows.append(
                {
                    "route": f"{src}->{dst}",
                    "direction": direction,
                    "metric": metric,
                    "bridge": bridge,
                    "n": len(vals),
                    "Q1": q1,
                    "Q2": q2,
                    "Q3": q3,
                    "IQR": q3 - q1,
                }
            )

            if bridge == "ccip" and len(vals) >= 5:
                lo, hi = bootstrap_median_ci(vals)
                ci_rows.append(
                    {
                        "route": f"{src}->{dst}",
                        "direction": direction,
                        "metric": metric,
                        "bridge": "ccip",
                        "n": len(vals),
                        "median": q2,
                        "ci_lo": lo,
                        "ci_hi": hi,
                    }
                )

        if len(groups) < 2:
            continue

        # Kruskal-Wallis across all bridges present on this route
        H, p_kw = kruskal(*groups.values())
        kw_rows.append(
            {
                "route": f"{src}->{dst}",
                "direction": direction,
                "metric": metric,
                "n_groups": len(groups),
                "n_total": sum(len(v) for v in groups.values()),
                "H": H,
                "p": p_kw,
            }
        )

        # pairwise Mann-Whitney + Holm-Bonferroni + rank-biserial
        pairs = list(itertools.combinations(groups.keys(), 2))
        raw_p = []
        pair_meta = []
        for a, b in pairs:
            _, p = mannwhitneyu(groups[a], groups[b], alternative="two-sided")
            r = rank_biserial(groups[a], groups[b])
            raw_p.append(p)
            pair_meta.append((a, b, r))

        adj_p = holm_bonferroni(np.array(raw_p))

        for (a, b, r), p_raw, p_adj in zip(pair_meta, raw_p, adj_p, strict=True):
            pairwise_rows.append(
                {
                    "route": f"{src}->{dst}",
                    "direction": direction,
                    "metric": metric,
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

desc_df = pd.DataFrame(desc_rows)
kw_df = pd.DataFrame(kw_rows)
pairwise_df = pd.DataFrame(pairwise_rows)
ci_df = pd.DataFrame(ci_rows)

desc_df.to_csv("../data/journal_revision/desc_stats.csv", index=False)
kw_df.to_csv("../data/journal_revision/kruskal_wallis.csv", index=False)
pairwise_df.to_csv("../data/journal_revision/pairwise_mannwhitney.csv", index=False)
ci_df.to_csv("../data/journal_revision/ccip_bootstrap_ci.csv", index=False)

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 200)

print("\n================ DESCRIPTIVE STATS ================")
print(desc_df.to_string(index=False))

print("\n================ KRUSKAL-WALLIS (per route, per metric) ================")
print(kw_df.to_string(index=False))

print("\n================ CCIP BOOTSTRAP 95% CI (median, 10,000 resamples) ================")
print(ci_df.to_string(index=False))

print(
    "\n================ SIGNIFICANT PAIRWISE COMPARISONS "
    "(Holm-Bonferroni p_adj < 0.05) ================"
)
pairwise_df["abs_r"] = pairwise_df["r"].abs()
sig_df = pairwise_df[pairwise_df["sig"]].sort_values(
    ["route", "metric", "abs_r"], ascending=[True, True, False]
)
sig_df = sig_df.drop(columns=["abs_r"])
print(sig_df.to_string(index=False))

print(f"\nTotal pairwise comparisons: {len(pairwise_df)}, significant: {pairwise_df['sig'].sum()}")
