"""
05_mixed_anova.py
Purpose: Fit a mixed ANOVA for the 2x2 crossover design:
         - Within-subjects factor: condition (AI vs noAI)
         - Between-subjects factor: sequence (AB vs BA)
         Also fit a linear mixed model (statsmodels MixedLM) as a robustness check.
Input:   df_clean from 01
Output:  ANOVA tables and model summaries in output/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats
import statsmodels.formula.api as smf

print("=== 05_mixed_anova.py: Mixed ANOVA and linear mixed models ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")

# Restore categoricals
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])
df_clean["period"] = pd.Categorical(df_clean["period"], categories=["Period 1", "Period 2"])
df_clean["sequence"] = pd.Categorical(df_clean["sequence"], categories=["AB", "BA"])

# ---------------------------------------------------------------------------
# 1. Check assumptions
# ---------------------------------------------------------------------------

print("\n--- Assumption checks ---")

# 1a. Normality of residuals by cell
print("  Shapiro-Wilk tests by condition x period:")
normality_rows = []
for (cond, per), grp in df_clean.groupby(["condition", "period"], observed=True):
    scores = grp["score"].dropna()
    if len(scores) >= 8:
        w, p = stats.shapiro(scores)
        normality_rows.append({
            "condition": cond, "period": per,
            "n": len(scores), "W": round(w, 4), "p": round(p, 4),
        })

normality_df = pd.DataFrame(normality_rows)
print(normality_df.to_string(index=False))

# 1b. Levene's test for homogeneity of variances
print("\n  Levene's test for homogeneity of variances:")

# Group by condition x sequence
groups_for_levene = []
labels_for_levene = []
for (cond, seq), grp in df_clean.groupby(["condition", "sequence"], observed=True):
    groups_for_levene.append(grp["score"].dropna().values)
    labels_for_levene.append(f"{cond}_{seq}")

levene_stat, levene_p = stats.levene(*groups_for_levene)
print(f"  Levene's F = {levene_stat:.3f}, p = {levene_p:.4f}")

# 1c. Extreme outliers
print("\n  Extreme outliers (> 3*IQR) by cell:")
n_extreme = 0
for (cond, per), grp in df_clean.groupby(["condition", "period"], observed=True):
    q1 = grp["score"].quantile(0.25)
    q3 = grp["score"].quantile(0.75)
    iqr = q3 - q1
    extreme = grp[(grp["score"] < q1 - 3 * iqr) | (grp["score"] > q3 + 3 * iqr)]
    n_extreme += len(extreme)
    if len(extreme) > 0:
        for _, row in extreme.iterrows():
            print(f"    {row['participant_id']}  {cond}  {per}  score={row['score']}")

if n_extreme == 0:
    print("  No extreme outliers detected.")

# ---------------------------------------------------------------------------
# 2. Mixed ANOVA using pingouin
# ---------------------------------------------------------------------------

print("\n--- Mixed ANOVA (pingouin) ---")
print("  Model: score ~ condition (within) * sequence (between), id = participant_id")

anova_result = pg.mixed_anova(
    data=df_clean,
    dv="score",
    within="condition",
    between="sequence",
    subject="participant_id",
)

print("\n  ANOVA table:")
print(anova_result.to_string(index=False))

anova_result.to_csv(TABLES_DIR / "mixed_anova.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Post-hoc pairwise comparisons
# ---------------------------------------------------------------------------

print("\n--- Post-hoc comparisons ---")
print("  Pairwise comparisons by sequence:")

posthoc = pg.pairwise_tests(
    data=df_clean,
    dv="score",
    within="condition",
    between="sequence",
    subject="participant_id",
    padjust="bonf",
)

print(posthoc.to_string(index=False))
posthoc.to_csv(TABLES_DIR / "posthoc_comparisons.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Linear Mixed Model (statsmodels) - Robustness check
# ---------------------------------------------------------------------------

print("\n--- Linear Mixed Model (statsmodels) ---")
print("  Model: score ~ condition + period + sequence + (1 | participant_id)")

# Create numeric dummies for the formula
df_lmm = df_clean.copy()
df_lmm["cond_num"] = (df_lmm["condition"] == "AI").astype(int)
df_lmm["period_num"] = df_lmm["period"].map({"Period 1": 1, "Period 2": 2}).astype(float)
df_lmm["seq_num"] = (df_lmm["sequence"] == "BA").astype(int)

lmm_fit = smf.mixedlm(
    "score ~ cond_num + period_num + seq_num",
    data=df_lmm,
    groups=df_lmm["participant_id"],
).fit(reml=True)

print("\n  Model summary:")
print(lmm_fit.summary())

# Fixed effects with confidence intervals
fe = lmm_fit.fe_params
ci = lmm_fit.conf_int().loc[fe.index]      # keep only fixed-effect rows
pv = lmm_fit.pvalues.loc[fe.index]         # keep only fixed-effect rows
fe_table = pd.DataFrame({
    "term": fe.index,
    "estimate": fe.round(3).values,
    "CI_lower": ci[0].round(3).values,
    "CI_upper": ci[1].round(3).values,
    "p_value": pv.round(4).values,
})

print("\n  Fixed effects with 95% CI:")
print(fe_table.to_string(index=False))
fe_table.to_csv(TABLES_DIR / "lmm_fixed_effects.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Model with treatment x period interaction (to test carryover)
# ---------------------------------------------------------------------------

print("\n--- Extended model with interaction ---")
print("  Model: score ~ condition * period + sequence + (1 | participant_id)")

lmm_interaction = smf.mixedlm(
    "score ~ cond_num * period_num + seq_num",
    data=df_lmm,
    groups=df_lmm["participant_id"],
).fit(reml=True)

print("\n  Model summary:")
print(lmm_interaction.summary())

# Model comparison via AIC / BIC
print("\n  Model comparison:")
print(f"    Main model:        AIC = {lmm_fit.aic:.1f}, BIC = {lmm_fit.bic:.1f}")
print(f"    Interaction model: AIC = {lmm_interaction.aic:.1f}, BIC = {lmm_interaction.bic:.1f}")

# Likelihood ratio test
ll_main = lmm_fit.llf
ll_inter = lmm_interaction.llf
lr_stat = -2 * (ll_main - ll_inter)
lr_df = 1  # one additional parameter
lr_p = 1 - stats.chi2.cdf(lr_stat, lr_df)
print(f"    LR test: chi2({lr_df}) = {lr_stat:.3f}, p = {lr_p:.4f}")

# ---------------------------------------------------------------------------
# 6. Estimated marginal means
# ---------------------------------------------------------------------------

print("\n--- Estimated Marginal Means ---")

# EMMs by condition: predict at mean values of other covariates
emm_rows = []
for cond_val, cond_label in [(0, "noAI"), (1, "AI")]:
    pred_data = pd.DataFrame({
        "cond_num": [cond_val],
        "period_num": [1.5],  # mean period
        "seq_num": [0.5],     # mean sequence
    })
    # Manual prediction: intercept + betas * values
    b = lmm_fit.fe_params
    emm = (
        b["Intercept"]
        + b["cond_num"] * cond_val
        + b["period_num"] * 1.5
        + b["seq_num"] * 0.5
    )
    emm_rows.append({"condition": cond_label, "emmean": round(emm, 3)})

emm_df = pd.DataFrame(emm_rows)
print("  EMMs by condition:")
print(emm_df.to_string(index=False))

# Contrast
diff = emm_rows[1]["emmean"] - emm_rows[0]["emmean"]
print(f"\n  Contrast (AI - noAI): {diff:.3f}")

emm_df.to_csv(TABLES_DIR / "emm_by_condition.csv", index=False)

print("\n  Saved models and tables.")
print("=== 05_mixed_anova.py: Complete ===\n")
