"""
04_paired_comparisons.py
Purpose: Perform within-subject paired comparisons of performance under AI
         vs noAI conditions.
         - Paired t-test (parametric)
         - Wilcoxon signed-rank test (non-parametric alternative)
         - QQ plot
         - Confidence intervals and p-values
Input:   df_clean, df_wide from 01
Output:  Test results saved to output/tables/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import pingouin as pg

print("=== 04_paired_comparisons.py: Paired comparisons (AI vs noAI) ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")
df_wide = pd.read_parquet(OUTPUT_DIR / "df_wide.parquet")

# Restore categoricals
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])
df_wide["sequence"] = pd.Categorical(df_wide["sequence"], categories=["AB", "BA"])

# ---------------------------------------------------------------------------
# 1. Check normality of differences
# ---------------------------------------------------------------------------

print("\n--- Normality check for score differences ---")

diffs = df_wide["score_diff"].dropna()
shapiro_stat, shapiro_p = stats.shapiro(diffs)
print(f"  Shapiro-Wilk W = {shapiro_stat:.4f}, p = {shapiro_p:.4f}")

normality_ok = shapiro_p >= 0.05
if normality_ok:
    print("  Normality assumption not violated (p >= 0.05).")
else:
    print("  Normality assumption violated (p < 0.05). Non-parametric test recommended.")

# QQ plot
fig, ax = plt.subplots(figsize=(6, 5))
stats.probplot(diffs, dist="norm", plot=ax)
ax.set_title("Q-Q Plot of Within-Subject Score Differences")
ax.get_lines()[0].set(marker="o", markerfacecolor="steelblue", alpha=0.6)
ax.get_lines()[1].set(color="red")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "qq_score_diff.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Paired t-test: Score
# ---------------------------------------------------------------------------

print("\n--- Paired t-test: Score (AI vs noAI) ---")

# Use pingouin for rich output (CI, Cohen's d, BF)
t_result = pg.ttest(
    df_wide["score_AI"],
    df_wide["score_noAI"],
    paired=True,
    confidence=0.95,
)

mean_diff = df_wide["score_diff"].mean()
ci_low = t_result["CI95"].values[0][0]
ci_high = t_result["CI95"].values[0][1]
t_stat = t_result["T"].values[0]
t_df = t_result["dof"].values[0]
t_p = t_result["p_val"].values[0]

print(f"  Mean difference (AI - noAI): {mean_diff:.3f}")
print(f"  95% CI: [{ci_low:.3f}, {ci_high:.3f}]")
print(f"  t({t_df}) = {t_stat:.3f}")
print(f"  p-value = {t_p:.4f}")

# ---------------------------------------------------------------------------
# 3. Paired t-test: Rubric Score
# ---------------------------------------------------------------------------

print("\n--- Paired t-test: Rubric Score (AI vs noAI) ---")

df_wide_rubric = df_wide.dropna(subset=["rubric_score_AI", "rubric_score_noAI"])
t_rubric = None

if len(df_wide_rubric) >= 10:
    t_rubric = pg.ttest(
        df_wide_rubric["rubric_score_AI"],
        df_wide_rubric["rubric_score_noAI"],
        paired=True,
    )
    r_diff = (df_wide_rubric["rubric_score_AI"] - df_wide_rubric["rubric_score_noAI"]).mean()
    r_ci = t_rubric["CI95"].values[0]
    r_t = t_rubric["T"].values[0]
    r_df = t_rubric["dof"].values[0]
    r_p = t_rubric["p_val"].values[0]

    print(f"  Mean difference (AI - noAI): {r_diff:.3f}")
    print(f"  95% CI: [{r_ci[0]:.3f}, {r_ci[1]:.3f}]")
    print(f"  t({r_df}) = {r_t:.3f}")
    print(f"  p-value = {r_p:.4f}")
else:
    print("  Insufficient paired rubric data. Skipping.")

# ---------------------------------------------------------------------------
# 4. Wilcoxon signed-rank test
# ---------------------------------------------------------------------------

print("\n--- Wilcoxon signed-rank test: Score ---")

wilcox = pg.wilcoxon(
    df_wide["score_AI"],
    df_wide["score_noAI"],
    alternative="two-sided",
)

# Also get scipy result for the pseudomedian / CI
w_stat_scipy, w_p_scipy = stats.wilcoxon(
    df_wide["score_AI"].dropna(),
    df_wide["score_noAI"].dropna(),
    alternative="two-sided",
)

print(f"  W-val = {wilcox['W_val'].values[0]:.0f}")
print(f"  p-value = {wilcox['p_val'].values[0]:.4f}")
print(f"  RBC (rank-biserial correlation) = {wilcox['RBC'].values[0]:.3f}")

# ---------------------------------------------------------------------------
# 5. Paired comparisons by sequence (sensitivity analysis)
# ---------------------------------------------------------------------------

print("\n--- Paired comparisons by sequence ---")

for seq_level in ["AB", "BA"]:
    df_seq = df_wide[df_wide["sequence"] == seq_level]
    if len(df_seq) >= 5:
        t_seq = pg.ttest(df_seq["score_AI"], df_seq["score_noAI"], paired=True)
        seq_diff = (df_seq["score_AI"] - df_seq["score_noAI"]).mean()
        seq_ci = t_seq["CI95"].values[0]
        seq_t = t_seq["T"].values[0]
        seq_p = t_seq["p_val"].values[0]

        print(f"\n  Sequence {seq_level}:")
        print(f"    n = {len(df_seq)}")
        print(f"    Mean diff = {seq_diff:.3f} [{seq_ci[0]:.3f}, {seq_ci[1]:.3f}]")
        print(f"    t = {seq_t:.3f}, p = {seq_p:.4f}")

# ---------------------------------------------------------------------------
# 6. Compile results table
# ---------------------------------------------------------------------------

results_rows = [
    {
        "Outcome": "Score",
        "Test": "Paired t-test",
        "n": int(t_df + 1),
        "Estimate": round(mean_diff, 3),
        "CI_lower": round(ci_low, 3),
        "CI_upper": round(ci_high, 3),
        "Statistic": round(t_stat, 3),
        "p_value": round(t_p, 6),
    },
    {
        "Outcome": "Score",
        "Test": "Wilcoxon signed-rank",
        "n": len(df_wide),
        "Estimate": round(mean_diff, 3),
        "CI_lower": np.nan,
        "CI_upper": np.nan,
        "Statistic": float(wilcox["W_val"].values[0]),
        "p_value": round(float(wilcox["p_val"].values[0]), 6),
    },
]

if t_rubric is not None:
    results_rows.append({
        "Outcome": "Rubric",
        "Test": "Paired t-test",
        "n": int(t_rubric["dof"].values[0] + 1),
        "Estimate": round(r_diff, 3),
        "CI_lower": round(r_ci[0], 3),
        "CI_upper": round(r_ci[1], 3),
        "Statistic": round(r_t, 3),
        "p_value": round(r_p, 6),
    })

results_table = pd.DataFrame(results_rows)
results_table.to_csv(TABLES_DIR / "paired_comparisons.csv", index=False)

print("\n  Results saved to output/tables/paired_comparisons.csv")
print("=== 04_paired_comparisons.py: Complete ===\n")
