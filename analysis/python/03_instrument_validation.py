"""
03_instrument_validation.py
Purpose: Validate data collection instruments using:
         - Cronbach's alpha for internal consistency of Likert scales
         - V de Aiken for content validity (from expert ratings)
         - ICC for inter-rater reliability of rubric scores
         - Item-total correlations
Input:   df_clean from 01
Output:  Validation metrics saved to output/tables/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats

print("=== 03_instrument_validation.py: Validating instruments ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")

# ---------------------------------------------------------------------------
# 1. Cronbach's Alpha for Likert Scales
# ---------------------------------------------------------------------------

print("\n--- Cronbach's Alpha (Internal Consistency) ---")

likert_cols = [c for c in df_clean.columns if c.startswith("likert_")]

if len(likert_cols) >= 2:
    # Extract Likert data with complete cases
    likert_data = df_clean[likert_cols].dropna()
    print(f"  Analyzing {len(likert_cols)} Likert items from "
          f"{len(likert_data)} complete observations.")

    # Overall Cronbach's alpha using pingouin
    alpha_val, ci = pg.cronbach_alpha(likert_data)
    print(f"  Cronbach's alpha: {alpha_val:.3f}  95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")

    # Item-total correlations
    item_stats_rows = []
    for col in likert_cols:
        rest_cols = [c for c in likert_cols if c != col]
        total_rest = likert_data[rest_cols].sum(axis=1)
        r_drop, _ = stats.pearsonr(likert_data[col], total_rest)

        total_all = likert_data[likert_cols].sum(axis=1)
        r_cor, _ = stats.pearsonr(likert_data[col], total_all)

        item_stats_rows.append({
            "item": col,
            "r_corrected": round(r_cor, 3),
            "r_drop": round(r_drop, 3),
        })

    item_stats = pd.DataFrame(item_stats_rows)
    print("\n  Item-total correlations:")
    print(item_stats.to_string(index=False))

    # Alpha if item dropped
    alpha_drop_rows = []
    for col in likert_cols:
        rest_cols = [c for c in likert_cols if c != col]
        if len(rest_cols) >= 2:
            a_drop, _ = pg.cronbach_alpha(likert_data[rest_cols])
        else:
            a_drop = float("nan")
        alpha_drop_rows.append({"item": col, "alpha_if_dropped": round(a_drop, 3)})

    alpha_drop = pd.DataFrame(alpha_drop_rows)
    print("\n  Alpha if item dropped:")
    print(alpha_drop.to_string(index=False))

    # Alpha by condition
    print("\n  Alpha by condition:")
    for cond in ["noAI", "AI"]:
        cond_data = df_clean.loc[df_clean["condition"] == cond, likert_cols].dropna()
        if len(cond_data) > 10:
            a_cond, _ = pg.cronbach_alpha(cond_data)
            print(f"    {cond}: alpha = {a_cond:.3f} (n = {len(cond_data)})")

    # Save
    item_stats.to_csv(TABLES_DIR / "cronbach_item_stats.csv", index=False)
    alpha_drop.to_csv(TABLES_DIR / "cronbach_alpha_if_dropped.csv", index=False)
else:
    print("  Fewer than 2 Likert columns found. Skipping Cronbach's alpha.")

# ---------------------------------------------------------------------------
# 2. V de Aiken for Content Validity
# ---------------------------------------------------------------------------

print("\n--- V de Aiken (Content Validity) ---")


def compute_v_aiken(
    ratings_matrix: np.ndarray,
    item_names: list[str],
    k: int = 5,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Compute V de Aiken with Wilson confidence intervals.

    Parameters
    ----------
    ratings_matrix : 2-D array, shape (n_items, n_experts)
    item_names : list of item identifiers
    k : number of rating categories (e.g. 1 to 5)
    alpha : significance level for CI

    Returns
    -------
    DataFrame with columns: item, n_judges, mean_rating, V, CI_lower, CI_upper
    """
    from scipy.stats import norm

    z = norm.ppf(1 - alpha / 2)
    n_items, n_experts = ratings_matrix.shape
    results = []

    for i in range(n_items):
        ratings = ratings_matrix[i, :]
        ratings = ratings[~np.isnan(ratings)]
        N = len(ratings)
        M = np.mean(ratings)
        V = (M - 1) / (k - 1)

        # Wilson score interval adapted for V de Aiken
        n_eff = N * (k - 1)
        p_hat = V
        denom = 1 + z**2 / n_eff
        centre = p_hat + z**2 / (2 * n_eff)
        margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_eff)) / n_eff)
        ci_lower = max(0.0, (centre - margin) / denom)
        ci_upper = min(1.0, (centre + margin) / denom)

        results.append({
            "item": item_names[i],
            "n_judges": N,
            "mean_rating": round(M, 3),
            "V": round(V, 3),
            "CI_lower": round(ci_lower, 3),
            "CI_upper": round(ci_upper, 3),
        })

    return pd.DataFrame(results)


expert_file = DATA_DIR / "expert_ratings.csv"

if expert_file.exists():
    expert_df = pd.read_csv(expert_file)
    item_names = expert_df.iloc[:, 0].tolist()
    ratings_matrix = expert_df.iloc[:, 1:].values.astype(float)

    v_aiken_results = compute_v_aiken(ratings_matrix, item_names, k=5)
    print("  V de Aiken results:")
    print(v_aiken_results.to_string(index=False))

    below = v_aiken_results[v_aiken_results["V"] < 0.70]
    if len(below) > 0:
        print("  WARNING: Items with V < 0.70 (consider revision):")
        print(below.to_string(index=False))

    v_aiken_results.to_csv(TABLES_DIR / "v_aiken_results.csv", index=False)
else:
    print("  No expert_ratings.csv found. Demonstrating with simulated data.")

    rng = np.random.default_rng(42)
    sim_ratings = rng.choice([3, 4, 5], size=(10, 5), p=[0.15, 0.35, 0.50])
    item_names_sim = [f"Item_{i+1}" for i in range(10)]

    v_aiken_results = compute_v_aiken(sim_ratings.astype(float), item_names_sim, k=5)
    print("  Simulated V de Aiken results:")
    print(v_aiken_results.to_string(index=False))

    v_aiken_results.to_csv(TABLES_DIR / "v_aiken_simulated.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Intraclass Correlation Coefficient (ICC)
# ---------------------------------------------------------------------------

print("\n--- ICC (Inter-Rater Reliability) ---")

rater_file = DATA_DIR / "rater_scores.csv"

if rater_file.exists():
    rater_data = pd.read_csv(rater_file)
    rater_cols = [c for c in rater_data.columns if c.startswith("rater_")]

    # Reshape to long format for pingouin
    rater_long = rater_data.melt(
        id_vars=["participant_id"],
        value_vars=rater_cols,
        var_name="rater",
        value_name="rating",
    )

    icc_result = pg.intraclass_corr(
        data=rater_long,
        targets="participant_id",
        raters="rater",
        ratings="rating",
    )
    # ICC(2,k) = ICC2k
    icc2k = icc_result[icc_result["Type"] == "ICC(A,k)"].iloc[0]
    print(f"  ICC(2,k) = {icc2k['ICC']:.3f}")
    print(f"  95% CI: [{icc2k['CI95'][0]:.3f}, {icc2k['CI95'][1]:.3f}]")
    print(f"  F({icc2k['df1']},{icc2k['df2']}) = {icc2k['F']:.3f}, p = {icc2k['pval']:.4f}")

    # Interpretation
    v = icc2k["ICC"]
    if v >= 0.75:
        interp = "Excellent agreement"
    elif v >= 0.60:
        interp = "Good agreement"
    elif v >= 0.40:
        interp = "Fair agreement"
    else:
        interp = "Poor agreement"
    print(f"  Interpretation: {interp}.")
else:
    print("  No rater_scores.csv found. Demonstrating with simulated data.")

    rng2 = np.random.default_rng(123)
    true_scores = rng2.normal(7, 1.5, 30)
    sim_rater = pd.DataFrame({
        "participant_id": [f"S{i:02d}" for i in range(1, 31)],
        "rater_1": np.clip(np.round(true_scores + rng2.normal(0, 0.5, 30), 1), 0, 10),
        "rater_2": np.clip(np.round(true_scores + rng2.normal(0, 0.6, 30), 1), 0, 10),
    })

    rater_long = sim_rater.melt(
        id_vars=["participant_id"],
        value_vars=["rater_1", "rater_2"],
        var_name="rater",
        value_name="rating",
    )

    icc_result = pg.intraclass_corr(
        data=rater_long,
        targets="participant_id",
        raters="rater",
        ratings="rating",
    )
    icc2_row = icc_result[icc_result["Type"] == "ICC(A,1)"].iloc[0]
    print(f"  Simulated ICC(2,1) = {icc2_row['ICC']:.3f}")
    ci = icc2_row["CI95"]
    print(f"  95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")

print("\n=== 03_instrument_validation.py: Complete ===\n")
