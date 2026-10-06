"""Generate the LaTeX tables for the paper from the CSVs written by 02 and 03.

Writes latex_output/stats_summary.tex (Appendix A) and
latex_output/cost_decomposition.tex (Table 8, Section 5.2).
"""

import pandas as pd

DATA = "../data/journal_revision"

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


def wrap_table(caption, label, font, tabcolsep, colspec, header, body):
    """Wrap rows in a table whose local font/tabcolsep don't leak to later tables."""
    return "\n".join(
        [
            r"\begin{table}[ht]",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            r"\begingroup",
            f"\\{font}",
            f"\\setlength{{\\tabcolsep}}{{{tabcolsep}pt}}",
            f"\\begin{{tabular}}{{{colspec}}}",
            r"\toprule",
            header,
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            r"\endgroup",
            r"\end{table}",
        ]
    )


def make_table(pw, metric, table_label, caption):
    sub = pw[(pw.metric == metric) & (pw.sig)].copy()
    sub["route_order"] = sub["route"].apply(ROUTE_ORDER.index)
    sub["abs_r"] = sub["r"].abs()
    sub = sub.sort_values(["route_order", "abs_r"], ascending=[True, False])

    body = []
    prev_route = None
    for _, row in sub.iterrows():
        if prev_route is not None and row["route"] != prev_route:
            body.append(r"\midrule")
        prev_route = row["route"]
        a = BRIDGE_LABEL[row["bridge_a"]]
        b = BRIDGE_LABEL[row["bridge_b"]]
        route = ROUTE_LABEL[row["route"]]
        body.append(
            f"{route} & {a} & {b} & {fmt_p(row['p_adj'])} & {row['r']:.3f} & {row['effect']} \\\\"
        )
    header = (
        r"\textbf{Route} & \textbf{Protocol A} & \textbf{Protocol B} "
        r"& $p_{\text{adj}}$ & $r$ & \textbf{Effect} \\"
    )
    return wrap_table(caption, table_label, "tiny", 3, "lllrrl", header, body)


def make_ci_table(ci):
    ci = ci.copy()
    ci["route_order"] = ci["route"].apply(ROUTE_ORDER.index)
    ci = ci.sort_values(["route_order", "metric"])
    body = []
    for _, row in ci.iterrows():
        metric_label = "Latency (s)" if row["metric"] == "latency" else "Cost (\\$)"
        body.append(
            f"{metric_label} & {ROUTE_LABEL[row['route']]} & {int(row['n'])} "
            f"& {row['median']:.2f} & {row['ci_lo']:.2f} & {row['ci_hi']:.2f} \\\\"
        )
    header = (
        r"\textbf{Metric} & \textbf{Route} & $n$ & \textbf{Median} & "
        r"\textbf{95\% CI Low} & \textbf{95\% CI High} \\"
    )
    caption = (
        r"CCIP 95\% bootstrap confidence intervals for the median "
        r"(10,000 resamples), per route."
    )
    return wrap_table(caption, "table:ccip_bootstrap_ci", "small", 5, "llrrrr", header, body)


PROTOCOL_FORMULA = {
    "cctp": "gas only",
    "ccip": "gas $+$ fee",
    "stargate_oft": "gas $+$ fee",
    "stargate_bus": "gas $+$ fare $+\\Delta$",
    "across": "gas $+\\Delta$",
}
COST_BRIDGE_LABEL = {
    **BRIDGE_LABEL,
    "stargate_oft": "Stargate Taxi",
    "stargate_bus": "Stargate Bus",
}


def make_cost_decomposition_table(df):
    body = []
    for b in PROTOCOL_FORMULA:
        row = df.loc[b]
        body.append(
            f"{COST_BRIDGE_LABEL[b]} & {PROTOCOL_FORMULA[b]} & "
            f"\\${row['med_gas_usd']:.4f} ({row['pct_gas']:.0f}\\%) & "
            f"\\${row['med_fee_usd']:.4f} ({row['pct_fee']:.0f}\\%) & "
            f"\\${row['med_delta_usd']:.4f} ({row['pct_delta']:.0f}\\%) & "
            f"\\${row['med_total_usd']:.4f} \\\\"
        )
    header = (
        r"\textbf{Protocol} & \textbf{Formula} & \textbf{Gas} & "
        r"\textbf{Protocol Fee} & \textbf{Price $\Delta$} & \textbf{Median Total} \\"
    )
    caption = (
        r"Decomposition of \emph{user\_cost} into its constituent components, "
        r"by protocol, computed on the full de-duplicated dataset ($\text{user\_cost} > 0$ "
        r"only, i.e., excluding the negative-cost anomalies discussed in "
        r"Section~\ref{section: l2-l2}). Percentages are the median per-transaction share "
        r"of each component and, because medians are not additive across a skewed "
        r"distribution, do not necessarily sum to 100\% row-wise. $\Delta$ = price-delta "
        r"component (amount sent minus amount received, or input minus output amount). "
        r"For Stargate Taxi, the protocol fee is the LayerZero messaging fee (executor $+$ DVN) "
        r"that the sender pays together with the transaction."
    )
    return wrap_table(caption, "table:cost_decomposition", "scriptsize", 3, "llrrrr", header, body)


pw = pd.read_csv(f"{DATA}/pairwise_mannwhitney.csv")
ci = pd.read_csv(f"{DATA}/ccip_bootstrap_ci.csv")
cost = pd.read_csv(f"{DATA}/cost_decomposition.csv").set_index("bridge")

SIG_CAPTION = (
    r"Significant pairwise \textbf{{{metric}}} comparisons per exact source"
    r"$\to$destination route (Mann-Whitney U, Holm-Bonferroni corrected, "
    r"$\alpha=0.05$; computed on the de-duplicated dataset{xref}). $r$ = rank-biserial "
    r"correlation (effect size)."
)
latency_tex = make_table(
    pw,
    "latency",
    "table:stats_pairwise_latency",
    SIG_CAPTION.format(metric="latency", xref=r", cf.\ Section~\ref{sec: threats-valitidy}"),
)
cost_tex = make_table(
    pw, "user_cost", "table:stats_pairwise_cost", SIG_CAPTION.format(metric="user cost", xref="")
)

with open("latex_output/stats_summary.tex", "w") as f:
    f.write("\n\n".join([latency_tex, cost_tex, make_ci_table(ci)]) + "\n")
with open("latex_output/cost_decomposition.tex", "w") as f:
    f.write(make_cost_decomposition_table(cost) + "\n")
print("Wrote latex_output/stats_summary.tex and latex_output/cost_decomposition.tex")
