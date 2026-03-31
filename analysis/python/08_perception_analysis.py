"""
08_perception_analysis.py
Purpose: Analyze Likert-scale perception data from post-challenge surveys.
         - Frequency tables for each item
         - Diverging stacked bar charts
         - Comparison of perceptions between AI and noAI conditions
         - Wilcoxon signed-rank tests for ordinal paired data with Holm correction
Input:   df_clean from 01
Output:  Perception tables and plots in output/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pingouin as pg
from statsmodels.stats.multitest import multipletests

print("=== 08_perception_analysis.py: Analyzing perception data ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")

# Restore categoricals
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])

# ---------------------------------------------------------------------------
# 1. Identify and prepare Likert data
# ---------------------------------------------------------------------------

likert_cols = [c for c in df_clean.columns if c.startswith("likert_")]

if len(likert_cols) == 0:
    print("  No Likert columns found. Skipping perception analysis.")
    print("=== 08_perception_analysis.py: Skipped (no Likert data) ===\n")
else:
    print(f"  Found {len(likert_cols)} Likert items.")

    likert_labels = {
        1: "Strongly Disagree",
        2: "Disagree",
        3: "Neutral",
        4: "Agree",
        5: "Strongly Agree",
    }

    # -------------------------------------------------------------------
    # 2. Frequency tables by condition
    # -------------------------------------------------------------------

    print("\n--- Likert frequency tables by condition ---")

    freq_tables = {}
    for col in likert_cols:
        sub = df_clean[["condition", col]].dropna()
        freq = (
            sub.groupby(["condition", col], observed=True)
            .size()
            .reset_index(name="n")
        )
        freq.columns = ["condition", "response", "n"]
        totals = freq.groupby("condition")["n"].transform("sum")
        freq["pct"] = (freq["n"] / totals * 100).round(1)
        freq["response_label"] = freq["response"].map(likert_labels)
        freq_tables[col] = freq

    for col in likert_cols:
        print(f"\n  {col}:")
        pivot = freq_tables[col].pivot_table(
            index="response_label", columns="condition",
            values=["n", "pct"], aggfunc="first",
        )
        print(pivot.to_string())

    # -------------------------------------------------------------------
    # 3. Overall Likert summary by condition
    # -------------------------------------------------------------------

    print("\n--- Overall Likert means by condition ---")

    likert_means = (
        df_clean.groupby("condition", observed=True)[likert_cols]
        .mean()
        .round(2)
        .reset_index()
    )
    print("  Mean scores:")
    print(likert_means.to_string(index=False))

    likert_means.to_csv(TABLES_DIR / "likert_means_by_condition.csv", index=False)

    # -------------------------------------------------------------------
    # 4. Wilcoxon signed-rank tests for each Likert item
    # -------------------------------------------------------------------

    print("\n--- Wilcoxon signed-rank tests (paired, AI vs noAI) ---")

    # Reshape to wide format for paired tests
    df_likert_long = df_clean[["participant_id", "condition"] + likert_cols].melt(
        id_vars=["participant_id", "condition"],
        value_vars=likert_cols,
        var_name="item",
        value_name="response",
    )

    df_likert_wide = df_likert_long.pivot_table(
        index=["participant_id", "item"],
        columns="condition",
        values="response",
        aggfunc="first",
    ).reset_index()

    df_likert_wide.columns = ["participant_id", "item", "AI", "noAI"]

    wilcox_rows = []
    for col in likert_cols:
        item_data = df_likert_wide[df_likert_wide["item"] == col].dropna(
            subset=["AI", "noAI"]
        )
        if len(item_data) >= 10:
            wt = pg.wilcoxon(item_data["AI"], item_data["noAI"], alternative="two-sided")

            # Rank-biserial correlation as effect size
            n_pairs = len(item_data)
            p_val = wt["p_val"].values[0]
            rbc = wt["RBC"].values[0]

            wilcox_rows.append({
                "item": col,
                "median_AI": item_data["AI"].median(),
                "median_noAI": item_data["noAI"].median(),
                "W": wt["W_val"].values[0],
                "p_value": round(p_val, 6),
                "p_adjusted": np.nan,  # filled below
                "r_effect": round(abs(rbc), 3),
            })

    if wilcox_rows:
        wilcox_results = pd.DataFrame(wilcox_rows)

        # Holm correction for multiple comparisons
        _, p_adj, _, _ = multipletests(
            wilcox_results["p_value"], method="holm", alpha=0.05
        )
        wilcox_results["p_adjusted"] = p_adj.round(6)

        print("  Results:")
        print(wilcox_results.to_string(index=False))

        wilcox_results.to_csv(TABLES_DIR / "likert_wilcoxon_tests.csv", index=False)

    # -------------------------------------------------------------------
    # 5. Diverging stacked bar charts
    # -------------------------------------------------------------------

    print("\n--- Generating diverging stacked bar charts ---")

    for cond in ["noAI", "AI"]:
        cond_data = df_clean.loc[df_clean["condition"] == cond, likert_cols].dropna()
        if len(cond_data) < 5:
            continue

        # Compute percentages for each response level
        pct_data = {}
        for col in likert_cols:
            counts = cond_data[col].value_counts(normalize=True).sort_index() * 100
            # Ensure all levels present
            for lv in range(1, 6):
                if lv not in counts.index:
                    counts[lv] = 0.0
            pct_data[col.replace("likert_", "")] = counts.sort_index()

        pct_df = pd.DataFrame(pct_data).T
        pct_df.columns = [likert_labels[i] for i in range(1, 6)]

        # Diverging bar chart: negative side for Disagree, positive for Agree
        fig, ax = plt.subplots(figsize=(10, 6))
        items = pct_df.index.tolist()
        y_pos = np.arange(len(items))

        # Center on Neutral
        left_vals = [
            pct_df.loc[item, "Strongly Disagree"] + pct_df.loc[item, "Disagree"]
            for item in items
        ]
        neutral_vals = [pct_df.loc[item, "Neutral"] for item in items]

        # Negative bars (disagree side)
        starts = [-lv for lv in left_vals]
        ax.barh(y_pos, [-pct_df.loc[item, "Strongly Disagree"] for item in items],
                left=starts, color=LIKERT_COLORS["Strongly Disagree"], edgecolor="white",
                label="Strongly Disagree")
        ax.barh(y_pos, [-pct_df.loc[item, "Disagree"] for item in items],
                left=[-pct_df.loc[item, "Strongly Disagree"] for item in items],
                color=LIKERT_COLORS["Disagree"], edgecolor="white", label="Disagree")

        # Neutral (centered)
        ax.barh(y_pos, neutral_vals, left=[0]*len(items),
                color=LIKERT_COLORS["Neutral"], edgecolor="white", label="Neutral")

        # Positive bars (agree side)
        neutral_arr = np.array(neutral_vals)
        agree_vals = [pct_df.loc[item, "Agree"] for item in items]
        strongly_agree_vals = [pct_df.loc[item, "Strongly Agree"] for item in items]
        ax.barh(y_pos, agree_vals, left=neutral_arr,
                color=LIKERT_COLORS["Agree"], edgecolor="white", label="Agree")
        ax.barh(y_pos, strongly_agree_vals, left=neutral_arr + np.array(agree_vals),
                color=LIKERT_COLORS["Strongly Agree"], edgecolor="white",
                label="Strongly Agree")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(items)
        ax.set_xlabel("Percentage (%)")
        ax.set_title(f"Perceptions: {cond} condition", fontweight="bold")
        ax.axvline(0, color="black", linewidth=0.5)
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"likert_diverging_{cond.lower()}.png")
        plt.close(fig)

    # -------------------------------------------------------------------
    # 6. Side-by-side comparison plot
    # -------------------------------------------------------------------

    likert_pct = (
        df_clean[["condition"] + likert_cols]
        .melt(id_vars=["condition"], var_name="item", value_name="response")
        .dropna()
    )
    likert_pct["item"] = likert_pct["item"].str.replace("likert_", "")
    likert_pct["response_label"] = likert_pct["response"].map(likert_labels)

    # Compute percentages
    pct_by_group = (
        likert_pct.groupby(["condition", "item", "response_label"])
        .size()
        .reset_index(name="n")
    )
    totals = pct_by_group.groupby(["condition", "item"])["n"].transform("sum")
    pct_by_group["pct"] = (pct_by_group["n"] / totals * 100).round(1)

    # Stacked bar plot using facets
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    response_order = list(likert_labels.values())

    for ax_idx, cond in enumerate(["noAI", "AI"]):
        ax = axes[ax_idx]
        cond_pct = pct_by_group[pct_by_group["condition"] == cond]

        items_list = sorted(cond_pct["item"].unique())
        bottom = np.zeros(len(items_list))

        for resp in response_order:
            vals = []
            for item in items_list:
                row = cond_pct[
                    (cond_pct["item"] == item) & (cond_pct["response_label"] == resp)
                ]
                vals.append(row["pct"].values[0] if len(row) > 0 else 0)
            vals = np.array(vals)
            ax.barh(items_list, vals, left=bottom,
                    color=LIKERT_COLORS[resp], edgecolor="white", label=resp)
            bottom += vals

        ax.set_title(cond, fontweight="bold", fontsize=13)
        ax.set_xlabel("Percentage (%)")
        if ax_idx == 0:
            ax.set_ylabel("Survey Item")

    # Shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=9,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Perception Comparison: AI vs noAI", fontweight="bold", fontsize=14)
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    fig.savefig(FIGURES_DIR / "likert_comparison.png")
    plt.close(fig)

    print("  Saved perception plots and tables.")
    print("=== 08_perception_analysis.py: Complete ===\n")
