import pandas as pd

BRIDGE_LABEL = {
    "cctp": "CCTP",
    "ccip": "CCIP",
    "stargate_oft": "Stargate Taxi",
    "stargate_bus": "Stargate Bus",
    "across": "Across",
}
FORMULA = {
    "cctp": "gas only",
    "ccip": "gas $+$ fee",
    "stargate_oft": "gas only",
    "stargate_bus": "gas $+$ fare $+\\Delta$",
    "across": "gas $+\\Delta$",
}
ORDER = ["cctp", "ccip", "stargate_oft", "stargate_bus", "across"]

df = pd.read_csv("../data/journal_revision/cost_decomposition.csv").set_index("bridge")

lines = []
lines.append(r"\begin{table}[ht]")
lines.append(
    r"\caption{Decomposition of \emph{user\_cost} into its constituent components, "
    r"by protocol, computed on the full de-duplicated dataset ($\text{user\_cost} > 0$ "
    r"only, i.e., excluding the negative-cost anomalies discussed in "
    r"Section~\ref{section: l2-l2}). Percentages are the median per-transaction share "
    r"of each component and, because medians are not additive across a skewed "
    r"distribution, do not necessarily sum to 100\% row-wise. $\Delta$ = price-delta "
    r"component (amount sent minus amount received, or input minus output amount).}"
)
lines.append(r"\label{table:cost_decomposition}")
lines.append(r"\begingroup")
lines.append(r"\scriptsize")
lines.append(r"\setlength{\tabcolsep}{3pt}")
lines.append(r"\begin{tabular}{llrrrr}")
lines.append(r"\toprule")
lines.append(
    r"\textbf{Protocol} & \textbf{Formula} & \textbf{Gas} & "
    r"\textbf{Protocol Fee} & \textbf{Price $\Delta$} & \textbf{Median Total} \\"
)
lines.append(r"\midrule")
for b in ORDER:
    row = df.loc[b]
    lines.append(
        f"{BRIDGE_LABEL[b]} & {FORMULA[b]} & "
        f"\\${row['med_gas_usd']:.4f} ({row['pct_gas']:.0f}\\%) & "
        f"\\${row['med_fee_usd']:.4f} ({row['pct_fee']:.0f}\\%) & "
        f"\\${row['med_delta_usd']:.4f} ({row['pct_delta']:.0f}\\%) & "
        f"\\${row['med_total_usd']:.4f} \\\\"
    )
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\endgroup")
lines.append(r"\end{table}")

tex = "\n".join(lines)
with open("latex_output/cost_decomposition.tex", "w") as f:
    f.write(tex + "\n")
print(tex)
