"""
generate_sample_data.py
Purpose: Generate a realistic synthetic dataset simulating 100 students in a
         2x2 crossover design for evaluating AI impact on learning.

Design:
  - 50 students in Sequence AB: Period 1 = noAI, Period 2 = AI
  - 50 students in Sequence BA: Period 1 = AI,   Period 2 = noAI
  - Treatment effect: AI improves scores by ~5 points (small-medium effect)
  - Period effect: ~3 points improvement from Period 1 to Period 2 (learning)
  - NO carryover effect (by design)
  - Realistic noise and some missing values (~3%)

Output: crossover_sample_data.csv in sample_data/
"""

from pathlib import Path

import numpy as np
import pandas as pd

print("=== generate_sample_data.py: Generating synthetic crossover data ===")

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------

SEED = 2026
rng = np.random.default_rng(SEED)

n_total = 100       # Total participants
n_per_seq = 50      # Per sequence (balanced)
mu = 65             # Grand mean score
tau = 5             # Treatment effect (AI advantage)
pi_effect = 3       # Period effect (learning / practice)
lam = 0             # Carryover effect (none)
sigma_subj = 12     # Between-subject SD (individual differences)
sigma_resid = 8     # Within-subject residual SD

# --------------------------------------------------------------------------
# Generate participant-level data
# --------------------------------------------------------------------------

participant_ids = [f"P{i:03d}" for i in range(1, n_total + 1)]
groups = ["A"] * n_per_seq + ["B"] * n_per_seq
sequences = ["AB"] * n_per_seq + ["BA"] * n_per_seq
subject_effects = rng.normal(0, sigma_subj, n_total)

participants = pd.DataFrame({
    "participant_id": participant_ids,
    "group": groups,
    "sequence": sequences,
    "subject_effect": subject_effects,
})

# --------------------------------------------------------------------------
# Generate observation-level data (2 rows per participant)
# --------------------------------------------------------------------------

rows = []
for _, p in participants.iterrows():
    for period in [1, 2]:
        # Assign condition based on sequence and period
        if p["sequence"] == "AB":
            condition = "noAI" if period == 1 else "AI"
        else:  # BA
            condition = "AI" if period == 1 else "noAI"

        treatment_ind = 1.0 if condition == "AI" else 0.0
        period_centered = period - 1.5

        # Carryover: only in period 2 for BA sequence
        carryover_term = 0.0
        if period == 2 and p["sequence"] == "BA":
            carryover_term = lam

        residual = rng.normal(0, sigma_resid)
        score_raw = (
            mu
            + pi_effect * period_centered
            + tau * treatment_ind
            + carryover_term
            + p["subject_effect"]
            + residual
        )
        score = round(np.clip(score_raw, 0, 100), 1)

        rows.append({
            "participant_id": p["participant_id"],
            "group": p["group"],
            "sequence": p["sequence"],
            "period": period,
            "condition": condition,
            "score": score,
        })

df = pd.DataFrame(rows)

# --------------------------------------------------------------------------
# Generate rubric scores (correlated with main score)
# --------------------------------------------------------------------------

df["rubric_score"] = np.round(
    np.clip(
        df["score"].values / 10 * 0.75
        + rng.normal(0, 1.0, len(df))
        + 0.5,
        0, 10,
    ),
    1,
)

# --------------------------------------------------------------------------
# Generate Likert scale items (1-5, perception questionnaire)
# --------------------------------------------------------------------------
# 6 items with a common factor to create inter-item correlations (alpha ~ 0.75-0.85)

common_factor = rng.normal(0, 0.6, len(df))
ai_mask = (df["condition"] == "AI").values.astype(float)

likert_specs = {
    "likert_usefulness":   (3.3, 0.5, 0.7),
    "likert_ease":         (3.5, 0.3, 0.8),
    "likert_confidence":   (3.1, 0.4, 0.7),
    "likert_engagement":   (3.4, 0.3, 0.8),
    "likert_satisfaction": (3.2, 0.5, 0.7),
    "likert_learning":     (3.3, 0.2, 0.8),
}

for col_name, (base_mean, ai_bonus, item_sd) in likert_specs.items():
    raw = (
        base_mean
        + ai_bonus * ai_mask
        + common_factor
        + rng.normal(0, item_sd, len(df))
    )
    df[col_name] = np.clip(np.round(raw), 1, 5).astype(int)

# --------------------------------------------------------------------------
# Generate time spent (minutes)
# --------------------------------------------------------------------------

time_mean = np.where(df["condition"] == "AI", 35.0, 42.0)
df["time_spent"] = np.round(np.maximum(5.0, rng.normal(time_mean, 10.0)), 1)

# --------------------------------------------------------------------------
# Introduce realistic missing values (~3%)
# --------------------------------------------------------------------------

rng_miss = np.random.default_rng(999)
n_obs = len(df)

# Missing rubric scores
missing_rubric = rng_miss.choice(n_obs, size=round(n_obs * 0.03), replace=False)
df.loc[df.index[missing_rubric], "rubric_score"] = np.nan

# Missing Likert items (1-4 missing per item)
for col_name in likert_specs:
    n_miss = rng_miss.integers(1, 5)
    missing_idx = rng_miss.choice(n_obs, size=n_miss, replace=False)
    df.loc[df.index[missing_idx], col_name] = np.nan

# Missing time (technical issue)
missing_time = rng_miss.choice(n_obs, size=2, replace=False)
df.loc[df.index[missing_time], "time_spent"] = np.nan

# --------------------------------------------------------------------------
# Final dataset
# --------------------------------------------------------------------------

col_order = [
    "participant_id", "group", "sequence", "period", "condition",
    "score", "rubric_score", "time_spent",
] + list(likert_specs.keys())

df_final = df[col_order].sort_values(["participant_id", "period"]).reset_index(drop=True)

# Convert Likert columns that may have NaN to nullable integer
for col_name in likert_specs:
    df_final[col_name] = df_final[col_name].astype("Int64")

print(f"  Generated {len(df_final)} observations for "
      f"{df_final['participant_id'].nunique()} participants.")
print(f"  Sequences: AB={sum(df_final['sequence'] == 'AB') // 2}, "
      f"BA={sum(df_final['sequence'] == 'BA') // 2}")
print(f"  Missing values: "
      f"{df_final['score'].isna().sum()} scores, "
      f"{df_final['rubric_score'].isna().sum()} rubric, "
      f"{df_final['time_spent'].isna().sum()} time")

# Output path
output_path = Path(__file__).resolve().parent / "crossover_sample_data.csv"
df_final.to_csv(output_path, index=False)
print(f"  Saved to: {output_path}")

# Sanity checks
ai_mean = df_final.loc[df_final["condition"] == "AI", "score"].mean()
noai_mean = df_final.loc[df_final["condition"] == "noAI", "score"].mean()
print(f"\n  Sanity checks:")
print(f"    Mean score (AI):   {ai_mean:.2f}")
print(f"    Mean score (noAI): {noai_mean:.2f}")
print(f"    Expected diff:     ~{tau} points")

print("=== generate_sample_data.py: Complete ===")
