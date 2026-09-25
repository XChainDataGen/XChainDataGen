import pandas as pd

BRIDGE_LABEL = {
    "cctp": "CCTP",
    "ccip": "CCIP",
    "stargate_oft": "S.OFT",
    "stargate_bus": "S.Bus",
    "across": "Across",
}
ROUTE_LABEL = {
    "ethereum->avalanche": "Eth$\\to$Avax",
    "avalanche->ethereum": "Avax$\\to$Eth",
    "ethereum->base": "Eth$\\to$Base",
    "avalanche->base": "Avax$\\to$Base",
    "base->ethereum": "Base$\\to$Eth",
    "base->avalanche": "Base$\\to$Avax",
    "arbitrum->base": "Arb$\\to$Base",
    "base->arbitrum": "Base$\\to$Arb",
}
ROUTE_ORDER = list(ROUTE_LABEL.keys())


def fmt_p(p):
    return "$<$0.0001" if p < 0.0001 else f"{p:.4f}"


def make_table(pw, metric, metric_label, table_label, caption):
    sub = pw[(pw.metric == metric) & (pw.sig)].copy()
    sub["route_order"] = sub["route"].apply(ROUTE_ORDER.index)
    sub["abs_r"] = sub["r"].abs()
    sub = sub.sort_values(["route_order", "abs_r"], ascending=[True, False])

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{table_label}}}")
    lines.append(r"\begingroup")
    lines.append(r"\tiny")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\begin{tabular}{lllrrl}")
    lines.append(r"\toprule")
    lines.append(
        r"\textbf{Route} & \textbf{Protocol A} & \textbf{Protocol B} "
        r"& $p_{\text{adj}}$ & $r$ & \textbf{Effect} \\"
    )
    lines.append(r"\midrule")

    prev_route = None
    for _, row in sub.iterrows():
        if prev_route is not None and row["route"] != prev_route:
            lines.append(r"\midrule")
        prev_route = row["route"]
        a = BRIDGE_LABEL[row["bridge_a"]]
        b = BRIDGE_LABEL[row["bridge_b"]]
        route = ROUTE_LABEL[row["route"]]
        lines.append(
            f"{route} & {a} & {b} & {fmt_p(row['p_adj'])} & {row['r']:.3f} & {row['effect']} \\\\"
        )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\endgroup")
    lines.append(r"\end{table}")
    return "\n".join(lines)


def make_ci_table(ci):
    ci = ci.copy()
    ci["route_order"] = ci["route"].apply(ROUTE_ORDER.index)
    ci = ci.sort_values(["route_order", "metric"])

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(
        r"\caption{CCIP 95\% bootstrap confidence intervals for the median "
        r"(10,000 resamples), per route.}"
    )
    lines.append(r"\label{table:ccip_bootstrap_ci}")
    lines.append(r"\begingroup")
    lines.append(r"\small")
    lines.append(r"\setlength{\tabcolsep}{5pt}")
    lines.append(r"\begin{tabular}{llrrrr}")
    lines.append(r"\toprule")
    lines.append(
        r"\textbf{Metric} & \textbf{Route} & $n$ & \textbf{Median} & "
        r"\textbf{95\% CI Low} & \textbf{95\% CI High} \\"
    )
    lines.append(r"\midrule")
    for _, row in ci.iterrows():
        metric_label = "Latency (s)" if row["metric"] == "latency" else "Cost (\\$)"
        route = ROUTE_LABEL[row["route"]]
        lines.append(
            f"{metric_label} & {route} & {int(row['n'])} & {row['median']:.2f} "
            f"& {row['ci_lo']:.2f} & {row['ci_hi']:.2f} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\endgroup")
    lines.append(r"\end{table}")
    return "\n".join(lines)


pw = pd.read_csv("../data/journal_revision/pairwise_mannwhitney.csv")
ci = pd.read_csv("../data/journal_revision/ccip_bootstrap_ci.csv")

latency_tex = make_table(
    pw,
    "latency",
    "Latency",
    "table:stats_pairwise_latency",
    r"Significant pairwise \textbf{latency} comparisons per exact source"
    r"$\to$destination route (Mann-Whitney U, Holm-Bonferroni corrected, "
    r"$\alpha=0.05$; computed on the de-duplicated dataset, cf.\ "
    r"Section~\ref{sec: threats-valitidy}). $r$ = rank-biserial correlation "
    r"(effect size).",
)
cost_tex = make_table(
    pw,
    "user_cost",
    "Cost",
    "table:stats_pairwise_cost",
    r"Significant pairwise \textbf{user cost} comparisons per exact source"
    r"$\to$destination route (Mann-Whitney U, Holm-Bonferroni corrected, "
    r"$\alpha=0.05$; computed on the de-duplicated dataset). $r$ = "
    r"rank-biserial correlation (effect size).",
)
ci_tex = make_ci_table(ci)

with open("latex_output/stats_summary.tex", "w") as f:
    f.write(latency_tex + "\n\n" + cost_tex + "\n\n" + ci_tex + "\n")

print(latency_tex)
print()
print(cost_tex)
print()
print(ci_tex)
