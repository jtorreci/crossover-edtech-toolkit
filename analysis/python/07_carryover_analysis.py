"""
07_carryover_analysis.py
Purpose: Test for carryover effects in the crossover design.
         The standard test (Grizzle, 1965; Senn, 2002) compares the sum of
         each participant's scores across periods between the two sequence
         groups. If significant carryover is detected, analyze only Period 1
         data (parallel-group comparison).
Input:   df_clean, df_period_sums from 01
Output:  Carryover test results in output/tables/
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

print("=== 07_carryover_analysis.py: Testing for carryover effects ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")
df_period_sums = pd.read_parquet(OUTPUT_DIR / "df_period_sums.parquet")

# Restore categoricals
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])
df_clean["period"] = pd.Categorical(df_clean["period"], categories=["Period 1", "Period 2"])
df_clean["sequence"] = pd.Categorical(df_clean["sequence"], categories=["AB", "BA"])
df_period_sums["sequence"] = pd.Categorical(
    df_period_sums["sequence"], categories=["AB", "BA"]
)

# ---------------------------------------------------------------------------
# 1. Standard carryover test (Grizzle's test)
# ---------------------------------------------------------------------------

print("\n--- Grizzle's carryover test ---")
print("  H0: No carryover effect (mean sum of scores equal across sequences)")
print("  If the sum (Y_period1 + Y_period2) differs between AB and BA sequences,")
print("  this suggests a carryover effect.\n")

sums_AB = df_period_sums.loc[df_period_sums["sequence"] == "AB", "score_sum"].values
sums_BA = df_period_sums.loc[df_period_sums["sequence"] == "BA", "score_sum"].values

# Welch's two-sample t-test
t_stat, t_p = stats.ttest_ind(sums_AB, sums_BA, equal_var=False)
# Confidence interval for the difference
diff_mean = sums_AB.mean() - sums_BA.mean()
se_diff = np.sqrt(sums_AB.var(ddof=1) / len(sums_AB) + sums_BA.var(ddof=1) / len(sums_BA))
# Welch-Satterthwaite df
s1, n1 = sums_AB.var(ddof=1), len(sums_AB)
s2, n2 = sums_BA.var(ddof=1), len(sums_BA)
df_welch = ((s1 / n1 + s2 / n2) ** 2) / (
    (s1 / n1) ** 2 / (n1 - 1) + (s2 / n2) ** 2 / (n2 - 1)
)
ci_margin = stats.t.ppf(0.975, df_welch) * se_diff
ci_lower = diff_mean - ci_margin
ci_upper = diff_mean + ci_margin

print(f"  Sequence AB: mean sum = {sums_AB.mean():.3f} "
      f"(SD = {sums_AB.std(ddof=1):.3f}, n = {len(sums_AB)})")
print(f"  Sequence BA: mean sum = {sums_BA.mean():.3f} "
      f"(SD = {sums_BA.std(ddof=1):.3f}, n = {len(sums_BA)})")
print(f"  Difference: {diff_mean:.3f}")
print(f"  t({df_welch:.1f}) = {t_stat:.3f}")
print(f"  p-value = {t_p:.4f}")
print(f"  95% CI for difference: [{ci_lower:.3f}, {ci_upper:.3f}]")

carryover_significant = t_p < 0.10  # alpha = 0.10 for carryover

if carryover_significant:
    print("\n  *** CARRYOVER EFFECT DETECTED (p < 0.10) ***")
    print("  Recommendation: Analyze only Period 1 data (parallel-group comparison).")
else:
    print("\n  No significant carryover effect (p >= 0.10).")
    print("  The standard crossover analysis is valid.")

# ---------------------------------------------------------------------------
# 2. Non-parametric carryover test (Mann-Whitney U)
# ---------------------------------------------------------------------------

print("\n--- Non-parametric carryover test (Mann-Whitney U) ---")

u_stat, u_p = stats.mannwhitneyu(sums_AB, sums_BA, alternative="two-sided")
print(f"  U = {u_stat:.0f}")
print(f"  p-value = {u_p:.4f}")

# ---------------------------------------------------------------------------
# 3. Visual check: boxplot of sums by sequence
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(6, 5))
sns.boxplot(
    data=df_period_sums,
    x="sequence",
    y="score_sum",
    palette=SEQ_PALETTE,
    ax=ax,
    width=0.5,
)
sns.stripplot(
    data=df_period_sums,
    x="sequence",
    y="score_sum",
    color="black",
    alpha=0.3,
    size=4,
    jitter=True,
    ax=ax,
)
ax.set_title(f"Carryover Test: Sum of Scores by Sequence\nt-test p = {t_p:.3f}")
ax.set_xlabel("Sequence")
ax.set_ylabel("Sum of scores (Period 1 + Period 2)")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "carryover_test.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Period effect test
# ---------------------------------------------------------------------------

print("\n--- Period effect test ---")
print("  Compare the difference (Y_period1 - Y_period2) between sequences.")

df_period_diff = df_clean.pivot_table(
    index=["participant_id", "sequence"],
    columns="period",
    values="score",
    aggfunc="first",
).reset_index()

df_period_diff.columns = ["participant_id", "sequence", "P1", "P2"]
df_period_diff["period_diff"] = df_period_diff["P1"] - df_period_diff["P2"]

ab_diffs = df_period_diff.loc[df_period_diff["sequence"] == "AB", "period_diff"].dropna()
ba_diffs = df_period_diff.loc[df_period_diff["sequence"] == "BA", "period_diff"].dropna()

period_t, period_p = stats.ttest_ind(ab_diffs, ba_diffs, equal_var=False)
print(f"  t = {period_t:.3f}, p = {period_p:.4f}")

# ---------------------------------------------------------------------------
# 5. If carryover is significant: Period 1 only analysis
# ---------------------------------------------------------------------------

if carryover_significant:
    print("\n--- Period 1 only analysis (due to carryover) ---")

    df_p1 = df_clean[df_clean["period"] == "Period 1"].copy()

    ai_scores = df_p1.loc[df_p1["condition"] == "AI", "score"].values
    noai_scores = df_p1.loc[df_p1["condition"] == "noAI", "score"].values

    p1_t, p1_p = stats.ttest_ind(ai_scores, noai_scores, equal_var=False)

    print(f"  Period 1 comparison (unpaired, AI vs noAI):")
    print(f"    AI mean:   {ai_scores.mean():.3f}")
    print(f"    noAI mean: {noai_scores.mean():.3f}")
    print(f"    t = {p1_t:.3f}, p = {p1_p:.4f}")

    # Cohen's d for independent samples
    d_p1 = pg.compute_effsize(ai_scores, noai_scores, paired=False, eftype="cohen")
    print(f"    Cohen's d = {d_p1:.3f}")
else:
    print("\n  Period 1 only analysis not needed (no carryover detected).")

# ---------------------------------------------------------------------------
# 6. Save carryover test results
# ---------------------------------------------------------------------------

carryover_results = pd.DataFrame([
    {
        "Test": "Grizzle (t-test)",
        "Statistic": round(t_stat, 3),
        "df": round(df_welch, 1),
        "p_value": round(t_p, 6),
        "Significant": carryover_significant,
        "Note": "alpha = 0.10 for carryover",
    },
    {
        "Test": "Mann-Whitney U",
        "Statistic": u_stat,
        "df": np.nan,
        "p_value": round(u_p, 6),
        "Significant": u_p < 0.10,
        "Note": "Non-parametric alternative",
    },
])

carryover_results.to_csv(TABLES_DIR / "carryover_test.csv", index=False)

print("\n=== 07_carryover_analysis.py: Complete ===\n")
