"""
01_data_import_clean.py
Purpose: Import the crossover study dataset, validate its structure, handle
         missing data, create derived variables, and flag potential outliers.
Input:   CSV file in sample_data/ (or user's own data)
Output:  Cleaned data files (Parquet and CSV) in output/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd

print("=== 01_data_import_clean.py: Importing and cleaning data ===")

# ---------------------------------------------------------------------------
# 1. Import data
# ---------------------------------------------------------------------------

data_file = DATA_DIR / "crossover_sample_data.csv"

if not data_file.exists():
    raise FileNotFoundError(
        f"Data file not found: {data_file}\n"
        "Run sample_data/generate_sample_data.py first, or place your data file there."
    )

df_raw = pd.read_csv(data_file)
print(f"  Loaded {len(df_raw)} rows and {len(df_raw.columns)} columns.")

# ---------------------------------------------------------------------------
# 2. Validate expected structure
# ---------------------------------------------------------------------------

required_cols = [
    "participant_id", "group", "sequence", "period", "condition",
    "score", "rubric_score", "time_spent",
]

missing_cols = [c for c in required_cols if c not in df_raw.columns]
if missing_cols:
    raise ValueError(
        f"Missing required columns: {', '.join(missing_cols)}\n"
        "See sample_data/data_dictionary.md for the expected format."
    )

print("  All required columns present.")

# ---------------------------------------------------------------------------
# 3. Set factor types (pd.Categorical)
# ---------------------------------------------------------------------------

df = df_raw.copy()
df["participant_id"] = df["participant_id"].astype(str)
df["group"] = pd.Categorical(df["group"], categories=["A", "B"], ordered=False)
df["sequence"] = pd.Categorical(df["sequence"], categories=["AB", "BA"], ordered=False)
df["period"] = pd.Categorical(
    df["period"].map({1: "Period 1", 2: "Period 2"}),
    categories=["Period 1", "Period 2"],
    ordered=True,
)
df["condition"] = pd.Categorical(
    df["condition"], categories=["noAI", "AI"], ordered=False
)

# ---------------------------------------------------------------------------
# 4. Check for missing data
# ---------------------------------------------------------------------------

missing_counts = df.isnull().sum()
missing_any = missing_counts[missing_counts > 0]

if len(missing_any) > 0:
    print("  Missing data detected:")
    for var, n_miss in missing_any.items():
        pct = round(n_miss / len(df) * 100, 1)
        print(f"    {var}: {n_miss} ({pct}%)")
else:
    print("  No missing data found.")

# Remove rows with missing primary outcome (score)
n_before = len(df)
df = df.dropna(subset=["score"]).reset_index(drop=True)
n_after = len(df)

if n_before != n_after:
    print(f"  Removed {n_before - n_after} rows with missing primary outcome (score).")

# ---------------------------------------------------------------------------
# 5. Validate data ranges
# ---------------------------------------------------------------------------

range_checks = {
    "score": (0, 100),
    "rubric_score": (0, 10),
    "time_spent": (0, 300),
}

for var, (lo, hi) in range_checks.items():
    if var in df.columns:
        vals = df[var].dropna()
        out_of_range = ((vals < lo) | (vals > hi)).sum()
        if out_of_range > 0:
            print(f"  WARNING: {out_of_range} values out of expected range "
                  f"for '{var}' [{lo}, {hi}].")

# Validate Likert items (should be 1-5)
likert_cols = [c for c in df.columns if c.startswith("likert_")]
for col in likert_cols:
    vals = df[col].dropna()
    if ((vals < 1) | (vals > 5)).any():
        print(f"  WARNING: Likert column '{col}' has values outside 1-5 range.")

print(f"  Found {len(likert_cols)} Likert columns.")

# ---------------------------------------------------------------------------
# 6. Create derived variables
# ---------------------------------------------------------------------------

# Wide format: one row per participant with AI and noAI scores side by side
score_wide = df.pivot_table(
    index=["participant_id", "sequence"],
    columns="condition",
    values=["score", "rubric_score"],
    aggfunc="first",
).reset_index()

# Flatten MultiIndex columns
score_wide.columns = [
    "_".join(col).strip("_") if isinstance(col, tuple) else col
    for col in score_wide.columns
]

# Rename for clarity
rename_map = {
    "score_AI": "score_AI",
    "score_noAI": "score_noAI",
    "rubric_score_AI": "rubric_score_AI",
    "rubric_score_noAI": "rubric_score_noAI",
}
for old, new in rename_map.items():
    if old in score_wide.columns:
        score_wide.rename(columns={old: new}, inplace=True)

# Within-subject differences
score_wide["score_diff"] = score_wide["score_AI"] - score_wide["score_noAI"]
if "rubric_score_AI" in score_wide.columns and "rubric_score_noAI" in score_wide.columns:
    score_wide["rubric_score_diff"] = (
        score_wide["rubric_score_AI"] - score_wide["rubric_score_noAI"]
    )

df_wide = score_wide.copy()
print(f"  Created wide-format data with {len(df_wide)} participants.")

# Sum of scores across periods (for carryover test)
# Map period labels back to numeric for sum
period_map = {"Period 1": 1, "Period 2": 2}
df["period_num"] = df["period"].map(period_map).astype(int)

df_period_sums = (
    df.groupby(["participant_id", "sequence"], observed=True)["score"]
    .sum()
    .reset_index()
    .rename(columns={"score": "score_sum"})
)

# ---------------------------------------------------------------------------
# 7. Outlier detection (IQR method within each condition)
# ---------------------------------------------------------------------------

def flag_outliers(group: pd.DataFrame) -> pd.DataFrame:
    q1 = group["score"].quantile(0.25)
    q3 = group["score"].quantile(0.75)
    iqr = q3 - q1
    group["is_outlier"] = (group["score"] < (q1 - 1.5 * iqr)) | (
        group["score"] > (q3 + 1.5 * iqr)
    )
    return group

df = df.groupby("condition", group_keys=False, observed=True).apply(flag_outliers)

n_outliers = df["is_outlier"].sum()
print(f"  Flagged {n_outliers} potential outliers (IQR method).")
print("  Note: Outliers are flagged but NOT removed. Review before deciding.")

# ---------------------------------------------------------------------------
# 8. Check balance between sequences
# ---------------------------------------------------------------------------

balance_table = (
    df.drop_duplicates(subset=["participant_id"])
    .groupby("sequence", observed=True)
    .size()
    .reset_index(name="n")
)
print("  Sequence balance:")
print(balance_table.to_string(index=False))

# ---------------------------------------------------------------------------
# 9. Save cleaned data
# ---------------------------------------------------------------------------

df_clean = df.copy()

# Save as Parquet (efficient binary) and CSV (portable)
df_clean.to_parquet(OUTPUT_DIR / "df_clean.parquet", index=False)
df_clean.to_csv(OUTPUT_DIR / "df_clean.csv", index=False)

df_wide.to_parquet(OUTPUT_DIR / "df_wide.parquet", index=False)
df_wide.to_csv(OUTPUT_DIR / "df_wide.csv", index=False)

df_period_sums.to_parquet(OUTPUT_DIR / "df_period_sums.parquet", index=False)
df_period_sums.to_csv(OUTPUT_DIR / "df_period_sums.csv", index=False)

print("  Saved: df_clean, df_wide, df_period_sums (.parquet + .csv)")
print("=== 01_data_import_clean.py: Complete ===\n")
