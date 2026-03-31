# ==============================================================================
# 01_data_import_clean.R
# Purpose: Import the crossover study dataset, validate its structure, handle
#          missing data, create derived variables, and flag potential outliers.
# Input:   CSV file in sample_data/ (or user's own data)
# Output:  Cleaned data frame `df_clean` saved as RDS in output/
# ==============================================================================

cat("=== 01_data_import_clean.R: Importing and cleaning data ===\n")

# --------------------------------------------------------------------------
# 1. Import data
# --------------------------------------------------------------------------

data_file <- file.path(DATA_DIR, "crossover_sample_data.csv")

if (!file.exists(data_file)) {
  stop(paste0(
    "Data file not found: ", data_file, "\n",
    "Run sample_data/generate_sample_data.R first, or place your data file there."
  ))
}

df_raw <- read_csv(data_file, show_col_types = FALSE)

cat(paste0("  Loaded ", nrow(df_raw), " rows and ", ncol(df_raw), " columns.\n"))

# --------------------------------------------------------------------------
# 2. Validate expected structure
# --------------------------------------------------------------------------

required_cols <- c(
  "participant_id", "group", "sequence", "period", "condition",
  "score", "rubric_score", "time_spent"
)

missing_cols <- setdiff(required_cols, names(df_raw))
if (length(missing_cols) > 0) {
  stop(paste0(
    "Missing required columns: ", paste(missing_cols, collapse = ", "), "\n",
    "See sample_data/data_dictionary.md for the expected format."
  ))
}

cat("  All required columns present.\n")

# --------------------------------------------------------------------------
# 3. Set factor types and levels
# --------------------------------------------------------------------------

df <- df_raw %>%
  mutate(
    participant_id = as.factor(participant_id),
    group          = factor(group, levels = c("A", "B")),
    sequence       = factor(sequence, levels = c("AB", "BA")),
    period         = factor(period, levels = c(1, 2), labels = c("Period 1", "Period 2")),
    condition      = factor(condition, levels = c("noAI", "AI"))
  )

# --------------------------------------------------------------------------
# 4. Check for missing data
# --------------------------------------------------------------------------

missing_summary <- df %>%
  summarise(across(everything(), ~ sum(is.na(.)))) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "n_missing") %>%
  filter(n_missing > 0)

if (nrow(missing_summary) > 0) {
  cat("  Missing data detected:\n")
  print(missing_summary, n = Inf)

  # Report percentage missing per variable
  pct_missing <- missing_summary %>%
    mutate(pct = round(n_missing / nrow(df) * 100, 1))
  cat("  Percentage missing:\n")
  print(pct_missing, n = Inf)
} else {
  cat("  No missing data found.\n")
}

# For the primary outcome (score), remove rows with missing values
n_before <- nrow(df)
df <- df %>% filter(!is.na(score))
n_after <- nrow(df)

if (n_before != n_after) {
  cat(paste0("  Removed ", n_before - n_after,
             " rows with missing primary outcome (score).\n"))
}

# --------------------------------------------------------------------------
# 5. Validate data ranges
# --------------------------------------------------------------------------

range_checks <- list(
  score        = c(0, 100),
  rubric_score = c(0, 10),
  time_spent   = c(0, 300)
)

for (var in names(range_checks)) {
  if (var %in% names(df)) {
    rng <- range_checks[[var]]
    out_of_range <- df %>%
      filter(!is.na(.data[[var]]) & (.data[[var]] < rng[1] | .data[[var]] > rng[2]))

    if (nrow(out_of_range) > 0) {
      warning(paste0("  ", nrow(out_of_range), " values out of expected range for '",
                     var, "' [", rng[1], ", ", rng[2], "]."))
    }
  }
}

# Validate Likert items (should be 1-5)
likert_cols <- grep("^likert_", names(df), value = TRUE)
for (col in likert_cols) {
  vals <- df[[col]][!is.na(df[[col]])]
  if (any(vals < 1 | vals > 5)) {
    warning(paste0("  Likert column '", col, "' has values outside 1-5 range."))
  }
}

cat(paste0("  Found ", length(likert_cols), " Likert columns.\n"))

# --------------------------------------------------------------------------
# 6. Create derived variables
# --------------------------------------------------------------------------

# Within-subject differences: for each participant, compute AI score - noAI score
df_wide <- df %>%
  select(participant_id, sequence, condition, score, rubric_score) %>%
  pivot_wider(
    names_from  = condition,
    values_from = c(score, rubric_score),
    names_sep   = "_"
  ) %>%
  mutate(
    score_diff        = score_AI - score_noAI,
    rubric_score_diff = rubric_score_AI - rubric_score_noAI
  )

cat(paste0("  Created wide-format data with ", nrow(df_wide), " participants.\n"))

# Sum of scores across periods (for carryover test)
df_period_sums <- df %>%
  group_by(participant_id, sequence) %>%
  summarise(
    score_sum = sum(score, na.rm = TRUE),
    .groups   = "drop"
  )

# --------------------------------------------------------------------------
# 7. Outlier detection (based on score)
# --------------------------------------------------------------------------

# Flag outliers using IQR method (1.5 * IQR beyond Q1/Q3) within each condition
df <- df %>%
  group_by(condition) %>%
  mutate(
    Q1          = quantile(score, 0.25, na.rm = TRUE),
    Q3          = quantile(score, 0.75, na.rm = TRUE),
    IQR_val     = Q3 - Q1,
    is_outlier  = score < (Q1 - 1.5 * IQR_val) | score > (Q3 + 1.5 * IQR_val)
  ) %>%
  ungroup() %>%
  select(-Q1, -Q3, -IQR_val)

n_outliers <- sum(df$is_outlier, na.rm = TRUE)
cat(paste0("  Flagged ", n_outliers, " potential outliers (IQR method).\n"))
cat("  Note: Outliers are flagged but NOT removed. Review before deciding.\n")

# --------------------------------------------------------------------------
# 8. Check balance between sequences
# --------------------------------------------------------------------------

balance_table <- df %>%
  distinct(participant_id, sequence) %>%
  count(sequence)

cat("  Sequence balance:\n")
print(balance_table)

# --------------------------------------------------------------------------
# 9. Save cleaned data
# --------------------------------------------------------------------------

# Long format (primary)
df_clean <- df
saveRDS(df_clean, file.path(OUTPUT_DIR, "df_clean.rds"))

# Wide format (for paired comparisons)
saveRDS(df_wide, file.path(OUTPUT_DIR, "df_wide.rds"))

# Period sums (for carryover test)
saveRDS(df_period_sums, file.path(OUTPUT_DIR, "df_period_sums.rds"))

cat("  Saved: df_clean.rds, df_wide.rds, df_period_sums.rds\n")
cat("=== 01_data_import_clean.R: Complete ===\n\n")
