"""
02_descriptive_stats.py
Purpose: Compute and display summary statistics for the crossover dataset,
         broken down by group, period, condition, and sequence.
Input:   df_clean from 01_data_import_clean.py
Output:  Summary tables (CSV) and basic plots (PNG) in output/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("=== 02_descriptive_stats.py: Computing descriptive statistics ===")

# ---------------------------------------------------------------------------
# Load cleaned data
# ---------------------------------------------------------------------------

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")
df_wide = pd.read_parquet(OUTPUT_DIR / "df_wide.parquet")

# Restore categoricals
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])
df_clean["period"] = pd.Categorical(df_clean["period"], categories=["Period 1", "Period 2"])
df_clean["sequence"] = pd.Categorical(df_clean["sequence"], categories=["AB", "BA"])

# ---------------------------------------------------------------------------
# 1. Overall summary statistics
# ---------------------------------------------------------------------------

overall = df_clean[["score", "rubric_score", "time_spent"]].describe().round(2)
print("  Overall summary:")
print(overall.to_string())

# ---------------------------------------------------------------------------
# 2. Summary by condition (AI vs noAI)
# ---------------------------------------------------------------------------

by_condition = (
    df_clean.groupby("condition", observed=True)
    .agg(
        n=("score", "size"),
        mean_score=("score", "mean"),
        sd_score=("score", "std"),
        median_score=("score", "median"),
        mean_rubric=("rubric_score", "mean"),
        sd_rubric=("rubric_score", "std"),
        mean_time=("time_spent", "mean"),
        sd_time=("time_spent", "std"),
    )
    .round(2)
    .reset_index()
)

print("\n  Summary by condition:")
print(by_condition.to_string(index=False))
by_condition.to_csv(TABLES_DIR / "summary_by_condition.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Summary by condition and period (the 2x2 cell means)
# ---------------------------------------------------------------------------

by_cond_period = (
    df_clean.groupby(["condition", "period"], observed=True)
    .agg(
        n=("score", "size"),
        mean_score=("score", "mean"),
        sd_score=("score", "std"),
        mean_rubric=("rubric_score", "mean"),
        sd_rubric=("rubric_score", "std"),
    )
    .round(2)
    .reset_index()
)

print("\n  Summary by condition x period:")
print(by_cond_period.to_string(index=False))
by_cond_period.to_csv(TABLES_DIR / "summary_condition_period.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Summary by sequence
# ---------------------------------------------------------------------------

by_sequence = (
    df_clean.groupby(["sequence", "period", "condition"], observed=True)
    .agg(
        n=("score", "size"),
        mean_score=("score", "mean"),
        sd_score=("score", "std"),
    )
    .round(2)
    .reset_index()
)

print("\n  Summary by sequence x period x condition:")
print(by_sequence.to_string(index=False))
by_sequence.to_csv(TABLES_DIR / "summary_by_sequence.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Basic plots
# ---------------------------------------------------------------------------

# -- Boxplot: Score by condition --
fig, ax = plt.subplots(figsize=(6, 5))
sns.boxplot(data=df_clean, x="condition", y="score", palette=PALETTE, ax=ax,
            flierprops=dict(marker="o", markerfacecolor="grey", alpha=0.5))
sns.stripplot(data=df_clean, x="condition", y="score", color="black",
              alpha=0.2, size=3, jitter=True, ax=ax)
ax.set_title("Score Distribution by Condition")
ax.set_xlabel("Condition")
ax.set_ylabel("Score (0-100)")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "boxplot_score_by_condition.png")
plt.close(fig)

# -- Boxplot: Score by condition and period --
fig, ax = plt.subplots(figsize=(7, 5))
sns.boxplot(data=df_clean, x="period", y="score", hue="condition",
            palette=PALETTE, ax=ax)
ax.set_title("Score by Period and Condition")
ax.set_xlabel("Period")
ax.set_ylabel("Score (0-100)")
ax.legend(title="Condition", loc="upper left")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "boxplot_score_period_condition.png")
plt.close(fig)

# -- Histogram of score differences (AI - noAI) --
mean_diff = df_wide["score_diff"].mean()

fig, ax = plt.subplots(figsize=(7, 5))
ax.hist(df_wide["score_diff"].dropna(), bins=15, color="steelblue",
        edgecolor="white", alpha=0.8)
ax.axvline(0, linestyle="--", color="red", linewidth=0.8, label="Zero")
ax.axvline(mean_diff, linestyle="-", color="darkblue", linewidth=0.8,
           label=f"Mean = {mean_diff:.1f}")
ax.set_title("Distribution of Within-Subject Score Differences (AI - noAI)")
ax.set_xlabel("Score difference (AI - noAI)")
ax.set_ylabel("Count")
ax.legend()
fig.tight_layout()
fig.savefig(FIGURES_DIR / "histogram_score_diff.png")
plt.close(fig)

# -- Time spent by condition --
fig, ax = plt.subplots(figsize=(6, 5))
sns.boxplot(data=df_clean, x="condition", y="time_spent",
            palette={"noAI": "#fbb4ae", "AI": "#b3cde3"}, ax=ax)
ax.set_title("Time Spent by Condition")
ax.set_xlabel("Condition")
ax.set_ylabel("Time (minutes)")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "boxplot_time_by_condition.png")
plt.close(fig)

print("  Saved tables and figures to output/")
print("=== 02_descriptive_stats.py: Complete ===\n")
