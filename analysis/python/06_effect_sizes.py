"""
06_effect_sizes.py
Purpose: Compute effect sizes for the crossover study:
         - Cohen's d for paired comparisons (within-subject)
         - Hedges' g (bias-corrected)
         - Partial eta-squared from ANOVA
         - 95% confidence intervals for all effect sizes
         - Interpretation labels
Input:   df_clean, df_wide, ANOVA results from previous scripts
Output:  Effect size table in output/tables/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats
import math

print("=== 06_effect_sizes.py: Computing effect sizes ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")
df_wide = pd.read_parquet(OUTPUT_DIR / "df_wide.parquet")

# Restore categoricals
df_wide["sequence"] = pd.Categorical(df_wide["sequence"], categories=["AB", "BA"])
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])
df_clean["sequence"] = pd.Categorical(df_clean["sequence"], categories=["AB", "BA"])


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def cohens_d_paired(x: np.ndarray, y: np.ndarray) -> dict:
    """Compute Cohen's d for paired samples with 95% CI (non-central t method)."""
    diffs = x - y
    n = len(diffs)
    d = diffs.mean() / diffs.std(ddof=1)

    # CI via non-central t distribution
    se_d = np.sqrt(1 / n + d**2 / (2 * n))
    t_val = d * np.sqrt(n)
    ci_t = stats.t.interval(0.95, df=n - 1, loc=t_val)
    ci_d = (ci_t[0] / np.sqrt(n), ci_t[1] / np.sqrt(n))

    return {"d": d, "CI_lower": ci_d[0], "CI_upper": ci_d[1], "n": n}


def hedges_g_correction(d: float, n: int) -> float:
    """Apply Hedges' g small-sample correction factor J."""
    df = n - 1
    # Exact J factor
    J = 1 - 3 / (4 * df - 1)
    return d * J


def interpret_d(d_val: float) -> str:
    """Interpret effect size magnitude (Cohen, 1988)."""
    d_abs = abs(d_val)
    if d_abs < 0.2:
        return "negligible"
    elif d_abs < 0.5:
        return "small"
    elif d_abs < 0.8:
        return "medium"
    else:
        return "large"


# ---------------------------------------------------------------------------
# 1. Cohen's d for paired comparisons (Score: AI vs noAI)
# ---------------------------------------------------------------------------

print("\n--- Cohen's d (paired) ---")

d_score = cohens_d_paired(
    df_wide["score_AI"].dropna().values,
    df_wide["score_noAI"].dropna().values,
)

print(f"  Score (AI vs noAI):")
print(f"    Cohen's d = {d_score['d']:.3f}  [{d_score['CI_lower']:.3f}, {d_score['CI_upper']:.3f}]")

# Also use pingouin for cross-validation
d_pg = pg.compute_effsize(
    df_wide["score_AI"], df_wide["score_noAI"], paired=True, eftype="cohen"
)
print(f"    (pingouin check: d = {d_pg:.3f})")

# Rubric score
df_wide_rubric = df_wide.dropna(subset=["rubric_score_AI", "rubric_score_noAI"])
d_rubric = None

if len(df_wide_rubric) >= 10:
    d_rubric = cohens_d_paired(
        df_wide_rubric["rubric_score_AI"].values,
        df_wide_rubric["rubric_score_noAI"].values,
    )
    print(f"\n  Rubric score (AI vs noAI):")
    print(f"    Cohen's d = {d_rubric['d']:.3f}  "
          f"[{d_rubric['CI_lower']:.3f}, {d_rubric['CI_upper']:.3f}]")

# ---------------------------------------------------------------------------
# 2. Cohen's d by sequence (sensitivity analysis)
# ---------------------------------------------------------------------------

print("\n--- Cohen's d by sequence ---")

d_by_sequence = {}
for seq_level in ["AB", "BA"]:
    df_seq = df_wide[df_wide["sequence"] == seq_level].dropna(
        subset=["score_AI", "score_noAI"]
    )
    if len(df_seq) >= 5:
        d_seq = cohens_d_paired(df_seq["score_AI"].values, df_seq["score_noAI"].values)
        d_by_sequence[seq_level] = d_seq
        print(f"  Sequence {seq_level}: d = {d_seq['d']:.3f}  "
              f"[{d_seq['CI_lower']:.3f}, {d_seq['CI_upper']:.3f}]")

# ---------------------------------------------------------------------------
# 3. Partial eta-squared from ANOVA
# ---------------------------------------------------------------------------

print("\n--- Partial eta-squared from ANOVA ---")

anova_file = TABLES_DIR / "mixed_anova.csv"
if anova_file.exists():
    anova_table = pd.read_csv(anova_file)
    print("  ANOVA effects with partial eta-squared (np2):")
    cols_show = [c for c in anova_table.columns
                 if c in ["Source", "SS", "DF1", "DF2", "MS", "F", "p-unc", "np2", "eps"]]
    print(anova_table[cols_show].to_string(index=False))
else:
    print("  ANOVA table not found. Run 05_mixed_anova.py first.")

# ---------------------------------------------------------------------------
# 4. Hedges' g (bias-corrected Cohen's d)
# ---------------------------------------------------------------------------

print("\n--- Hedges' g (bias-corrected) ---")

g_score = hedges_g_correction(d_score["d"], d_score["n"])
# Apply same correction to CIs
J = 1 - 3 / (4 * (d_score["n"] - 1) - 1)
g_ci_lower = d_score["CI_lower"] * J
g_ci_upper = d_score["CI_upper"] * J

print(f"  Score (AI vs noAI), Hedges' g:")
print(f"    g = {g_score:.3f}  [{g_ci_lower:.3f}, {g_ci_upper:.3f}]")

# ---------------------------------------------------------------------------
# 5. Interpretation guidelines
# ---------------------------------------------------------------------------

print("\n--- Effect size interpretation ---")
print(f"  Cohen's d = {d_score['d']:.3f} -> {interpret_d(d_score['d'])} effect")

# ---------------------------------------------------------------------------
# 6. Compile effect size summary table
# ---------------------------------------------------------------------------

rows = [
    {
        "Comparison": "Score: AI vs noAI (Cohen's d)",
        "Estimate": round(d_score["d"], 3),
        "CI_lower": round(d_score["CI_lower"], 3),
        "CI_upper": round(d_score["CI_upper"], 3),
        "Interpretation": interpret_d(d_score["d"]),
    },
    {
        "Comparison": "Score: AI vs noAI (Hedges' g)",
        "Estimate": round(g_score, 3),
        "CI_lower": round(g_ci_lower, 3),
        "CI_upper": round(g_ci_upper, 3),
        "Interpretation": interpret_d(g_score),
    },
]

if d_rubric is not None:
    rows.append({
        "Comparison": "Rubric: AI vs noAI (Cohen's d)",
        "Estimate": round(d_rubric["d"], 3),
        "CI_lower": round(d_rubric["CI_lower"], 3),
        "CI_upper": round(d_rubric["CI_upper"], 3),
        "Interpretation": interpret_d(d_rubric["d"]),
    })

for seq_level, d_seq in d_by_sequence.items():
    rows.append({
        "Comparison": f"Score: AI vs noAI, sequence {seq_level} (Cohen's d)",
        "Estimate": round(d_seq["d"], 3),
        "CI_lower": round(d_seq["CI_lower"], 3),
        "CI_upper": round(d_seq["CI_upper"], 3),
        "Interpretation": interpret_d(d_seq["d"]),
    })

effect_size_table = pd.DataFrame(rows)

print("\n  Summary table:")
print(effect_size_table.to_string(index=False))

effect_size_table.to_csv(TABLES_DIR / "effect_sizes.csv", index=False)

print("\n=== 06_effect_sizes.py: Complete ===\n")
