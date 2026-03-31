# ==============================================================================
# test_analysis_pipeline.R
# Purpose: Automated tests for the crossover-edtech-toolkit analysis pipeline.
#          Uses testthat to verify that:
#          1. Sample data generation produces valid output
#          2. The analysis pipeline runs without errors
#          3. Output dimensions and values are within plausible ranges
# Usage:   source("tests/test_analysis_pipeline.R") from project root
# ==============================================================================

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------

if (!requireNamespace("testthat", quietly = TRUE)) {
  install.packages("testthat", repos = "https://cran.r-project.org")
}
library(testthat)

cat("=== Running analysis pipeline tests ===\n\n")

# Set project root
PROJECT_ROOT <- tryCatch({
  script_dir <- dirname(sys.frame(1)$ofile)
  normalizePath(file.path(script_dir, ".."), winslash = "/")
}, error = function(e) {
  normalizePath(".", winslash = "/")
})

DATA_DIR   <- file.path(PROJECT_ROOT, "sample_data")
OUTPUT_DIR <- file.path(PROJECT_ROOT, "output")

# --------------------------------------------------------------------------
# Test 1: Sample data generation
# --------------------------------------------------------------------------

test_that("Sample data generation produces a valid CSV", {

  # Source the generator
  source(file.path(DATA_DIR, "generate_sample_data.R"))

  data_file <- file.path(DATA_DIR, "crossover_sample_data.csv")
  expect_true(file.exists(data_file),
              info = "Sample data CSV should be created")

  df <- read.csv(data_file, stringsAsFactors = FALSE)

  # Check dimensions: 100 participants x 2 periods = 200 rows
  expect_equal(nrow(df), 200,
               info = "Should have 200 rows (100 participants x 2 periods)")

  # Check required columns exist
  required <- c("participant_id", "group", "sequence", "period", "condition",
                 "score", "rubric_score", "time_spent")
  for (col in required) {
    expect_true(col %in% names(df),
                info = paste("Column", col, "should exist"))
  }

  # Check Likert columns
  likert_cols <- grep("^likert_", names(df), value = TRUE)
  expect_gte(length(likert_cols), 3,
             label = "Should have at least 3 Likert columns")
})

test_that("Sample data has correct structure", {

  df <- read.csv(file.path(DATA_DIR, "crossover_sample_data.csv"),
                 stringsAsFactors = FALSE)

  # Each participant should have exactly 2 rows
  obs_per_participant <- table(df$participant_id)
  expect_true(all(obs_per_participant == 2),
              info = "Each participant should have exactly 2 observations")

  # Sequences should be balanced (approximately)
  n_AB <- sum(df$sequence == "AB") / 2
  n_BA <- sum(df$sequence == "BA") / 2
  expect_equal(n_AB, 50, info = "50 participants in sequence AB")
  expect_equal(n_BA, 50, info = "50 participants in sequence BA")

  # Conditions
  expect_true(all(df$condition %in% c("AI", "noAI")),
              info = "Condition values should be AI or noAI")

  # Score range
  expect_true(all(df$score >= 0 & df$score <= 100, na.rm = TRUE),
              info = "Scores should be between 0 and 100")

  # Rubric range
  valid_rubric <- df$rubric_score[!is.na(df$rubric_score)]
  expect_true(all(valid_rubric >= 0 & valid_rubric <= 10),
              info = "Rubric scores should be between 0 and 10")

  # Likert range
  likert_cols <- grep("^likert_", names(df), value = TRUE)
  for (col in likert_cols) {
    valid_vals <- df[[col]][!is.na(df[[col]])]
    expect_true(all(valid_vals >= 1 & valid_vals <= 5),
                info = paste(col, "should be between 1 and 5"))
  }
})

test_that("Crossover design is correctly implemented", {

  df <- read.csv(file.path(DATA_DIR, "crossover_sample_data.csv"),
                 stringsAsFactors = FALSE)

  # Sequence AB: period 1 = noAI, period 2 = AI
  ab_p1 <- df[df$sequence == "AB" & df$period == 1, "condition"]
  ab_p2 <- df[df$sequence == "AB" & df$period == 2, "condition"]
  expect_true(all(ab_p1 == "noAI"),
              info = "Sequence AB, Period 1 should be noAI")
  expect_true(all(ab_p2 == "AI"),
              info = "Sequence AB, Period 2 should be AI")

  # Sequence BA: period 1 = AI, period 2 = noAI
  ba_p1 <- df[df$sequence == "BA" & df$period == 1, "condition"]
  ba_p2 <- df[df$sequence == "BA" & df$period == 2, "condition"]
  expect_true(all(ba_p1 == "AI"),
              info = "Sequence BA, Period 1 should be AI")
  expect_true(all(ba_p2 == "noAI"),
              info = "Sequence BA, Period 2 should be noAI")
})

# --------------------------------------------------------------------------
# Test 2: Setup script loads packages
# --------------------------------------------------------------------------

test_that("Setup script runs without errors", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "00_setup.R"))
  )
  # Check key packages are loaded
  expect_true("ggplot2" %in% loadedNamespaces())
  expect_true("dplyr" %in% loadedNamespaces())
  expect_true("lme4" %in% loadedNamespaces())
})

# --------------------------------------------------------------------------
# Test 3: Data import and cleaning
# --------------------------------------------------------------------------

test_that("Data import and cleaning runs without errors", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "01_data_import_clean.R"))
  )

  # Check output files exist
  expect_true(file.exists(file.path(OUTPUT_DIR, "df_clean.rds")))
  expect_true(file.exists(file.path(OUTPUT_DIR, "df_wide.rds")))
  expect_true(file.exists(file.path(OUTPUT_DIR, "df_period_sums.rds")))

  # Check df_clean structure
  df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))
  expect_gte(nrow(df_clean), 190,
             label = "Cleaned data should have at least 190 rows (some may be removed)")
  expect_true(is.factor(df_clean$condition))

  # Check df_wide structure
  df_wide <- readRDS(file.path(OUTPUT_DIR, "df_wide.rds"))
  expect_equal(nrow(df_wide), 100,
               info = "Wide data should have 100 rows (one per participant)")
  expect_true("score_diff" %in% names(df_wide))
})

# --------------------------------------------------------------------------
# Test 4: Descriptive statistics
# --------------------------------------------------------------------------

test_that("Descriptive statistics script runs and produces output", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "02_descriptive_stats.R"))
  )

  expect_true(file.exists(file.path(OUTPUT_DIR, "tables", "summary_by_condition.csv")))
  expect_true(file.exists(file.path(OUTPUT_DIR, "figures", "boxplot_score_by_condition.png")))
})

# --------------------------------------------------------------------------
# Test 5: Paired comparisons
# --------------------------------------------------------------------------

test_that("Paired comparisons produce plausible results", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "04_paired_comparisons.R"))
  )

  results <- read.csv(file.path(OUTPUT_DIR, "tables", "paired_comparisons.csv"))
  expect_gte(nrow(results), 2,
             label = "Should have at least 2 test results")

  # p-values should be between 0 and 1
  expect_true(all(results$p_value >= 0 & results$p_value <= 1, na.rm = TRUE))
})

# --------------------------------------------------------------------------
# Test 6: Mixed ANOVA and LMM
# --------------------------------------------------------------------------

test_that("Mixed ANOVA and LMM run successfully", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "05_mixed_anova.R"))
  )

  expect_true(file.exists(file.path(OUTPUT_DIR, "models", "lmm_main.rds")))

  lmm <- readRDS(file.path(OUTPUT_DIR, "models", "lmm_main.rds"))
  expect_s4_class(lmm, "lmerMod")
})

# --------------------------------------------------------------------------
# Test 7: Effect sizes are within plausible ranges
# --------------------------------------------------------------------------

test_that("Effect sizes are within plausible ranges", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "06_effect_sizes.R"))
  )

  es <- read.csv(file.path(OUTPUT_DIR, "tables", "effect_sizes.csv"))
  expect_gte(nrow(es), 1, label = "Should have at least 1 effect size")

  # Cohen's d should typically be between -3 and 3 for educational studies
  expect_true(all(abs(es$Estimate) < 3, na.rm = TRUE),
              info = "Effect sizes should be within plausible range (|d| < 3)")

  # Confidence intervals should contain the point estimate
  for (i in seq_len(nrow(es))) {
    if (!is.na(es$CI_lower[i]) && !is.na(es$CI_upper[i])) {
      expect_lte(es$CI_lower[i], es$Estimate[i])
      expect_gte(es$CI_upper[i], es$Estimate[i])
    }
  }
})

# --------------------------------------------------------------------------
# Test 8: Carryover analysis
# --------------------------------------------------------------------------

test_that("Carryover analysis runs and reports results", {
  expect_no_error(
    source(file.path(PROJECT_ROOT, "analysis", "R", "07_carryover_analysis.R"))
  )

  expect_true(file.exists(file.path(OUTPUT_DIR, "tables", "carryover_test.csv")))

  carryover <- read.csv(file.path(OUTPUT_DIR, "tables", "carryover_test.csv"))
  expect_gte(nrow(carryover), 1)

  # Since data was generated with no carryover, we expect non-significant result
  # (though randomness may occasionally produce p < 0.10)
  expect_true(all(carryover$p_value >= 0 & carryover$p_value <= 1))
})

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------

cat("\n=== All tests completed ===\n")
