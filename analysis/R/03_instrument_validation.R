# ==============================================================================
# 03_instrument_validation.R
# Purpose: Validate data collection instruments using:
#          - Cronbach's alpha for internal consistency of Likert scales
#          - V de Aiken for content validity (from expert ratings)
#          - ICC for inter-rater reliability of rubric scores
# Input:   df_clean.rds
# Output:  Validation metrics saved to output/tables/
# ==============================================================================

cat("=== 03_instrument_validation.R: Validating instruments ===\n")

df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))

# --------------------------------------------------------------------------
# 1. Cronbach's Alpha for Likert Scales
# --------------------------------------------------------------------------

cat("\n--- Cronbach's Alpha (Internal Consistency) ---\n")

# Identify Likert columns
likert_cols <- grep("^likert_", names(df_clean), value = TRUE)

if (length(likert_cols) >= 2) {

  # Extract Likert data (one row per observation, columns are items)
  likert_data <- df_clean %>%
    select(all_of(likert_cols)) %>%
    drop_na()

  cat(paste0("  Analyzing ", length(likert_cols), " Likert items from ",
             nrow(likert_data), " complete observations.\n"))

  # Overall Cronbach's alpha
  alpha_result <- psych::alpha(likert_data, check.keys = TRUE)

  cat(paste0("  Raw alpha:         ", round(alpha_result$total$raw_alpha, 3), "\n"))
  cat(paste0("  Standardized alpha: ", round(alpha_result$total$std.alpha, 3), "\n"))

  # Item-level statistics
  item_stats <- alpha_result$item.stats %>%
    as.data.frame() %>%
    rownames_to_column("item") %>%
    select(item, r.cor, r.drop) %>%
    mutate(across(where(is.numeric), ~ round(., 3)))

  cat("\n  Item-total correlations:\n")
  print(item_stats)

  # Alpha if item dropped
  alpha_drop <- alpha_result$alpha.drop %>%
    as.data.frame() %>%
    rownames_to_column("item") %>%
    select(item, raw_alpha) %>%
    mutate(raw_alpha = round(raw_alpha, 3))

  cat("\n  Alpha if item dropped:\n")
  print(alpha_drop)

  # Compute alpha separately for each condition
  cat("\n  Alpha by condition:\n")
  for (cond in levels(df_clean$condition)) {
    cond_data <- df_clean %>%
      filter(condition == cond) %>%
      select(all_of(likert_cols)) %>%
      drop_na()

    if (nrow(cond_data) > 10) {
      alpha_cond <- psych::alpha(cond_data, check.keys = TRUE)
      cat(paste0("    ", cond, ": alpha = ",
                 round(alpha_cond$total$raw_alpha, 3), " (n = ",
                 nrow(cond_data), ")\n"))
    }
  }

  # Save results
  write_csv(item_stats, file.path(OUTPUT_DIR, "tables", "cronbach_item_stats.csv"))
  write_csv(alpha_drop, file.path(OUTPUT_DIR, "tables", "cronbach_alpha_if_dropped.csv"))

} else {
  cat("  Fewer than 2 Likert columns found. Skipping Cronbach's alpha.\n")
}

# --------------------------------------------------------------------------
# 2. V de Aiken for Content Validity
# --------------------------------------------------------------------------

cat("\n--- V de Aiken (Content Validity) ---\n")

# V de Aiken formula: V = (M - 1) / (K - 1)
# where M = mean expert rating, K = number of rating categories
# Expert ratings are expected in a separate file; here we provide the function
# and demonstrate with simulated expert data.

compute_v_aiken <- function(ratings_matrix, k = 5) {
  # ratings_matrix: rows = items, columns = experts
  # k: number of categories in the rating scale (e.g., 1 to 5)
  # Returns V de Aiken per item with 95% CI (Penfield & Giacobbi, 2004)

  n_experts <- ncol(ratings_matrix)
  results <- data.frame(
    item     = rownames(ratings_matrix),
    n_judges = n_experts,
    mean_rating = NA_real_,
    V        = NA_real_,
    CI_lower = NA_real_,
    CI_upper = NA_real_
  )

  for (i in seq_len(nrow(ratings_matrix))) {
    ratings <- as.numeric(ratings_matrix[i, ])
    M <- mean(ratings, na.rm = TRUE)
    V <- (M - 1) / (k - 1)

    # Approximate 95% CI using normal approximation
    S <- sum(ratings - 1, na.rm = TRUE)
    N <- sum(!is.na(ratings))
    # Wilson score interval adapted for V de Aiken
    z <- 1.96
    p_hat <- V
    n_eff <- N * (k - 1)
    CI_lower <- (p_hat + z^2 / (2 * n_eff) -
                   z * sqrt((p_hat * (1 - p_hat) + z^2 / (4 * n_eff)) / n_eff)) /
                (1 + z^2 / n_eff)
    CI_upper <- (p_hat + z^2 / (2 * n_eff) +
                   z * sqrt((p_hat * (1 - p_hat) + z^2 / (4 * n_eff)) / n_eff)) /
                (1 + z^2 / n_eff)

    results$mean_rating[i] <- round(M, 3)
    results$V[i]           <- round(V, 3)
    results$CI_lower[i]    <- round(max(0, CI_lower), 3)
    results$CI_upper[i]    <- round(min(1, CI_upper), 3)
  }

  return(results)
}

# Check for expert ratings file
expert_file <- file.path(DATA_DIR, "expert_ratings.csv")

if (file.exists(expert_file)) {
  expert_ratings <- read_csv(expert_file, show_col_types = FALSE)
  ratings_matrix <- as.matrix(expert_ratings[, -1])
  rownames(ratings_matrix) <- expert_ratings[[1]]

  v_aiken_results <- compute_v_aiken(ratings_matrix, k = 5)
  cat("  V de Aiken results:\n")
  print(v_aiken_results)

  items_below_threshold <- v_aiken_results %>% filter(V < 0.70)
  if (nrow(items_below_threshold) > 0) {
    cat("  WARNING: Items with V < 0.70 (consider revision):\n")
    print(items_below_threshold)
  }

  write_csv(v_aiken_results, file.path(OUTPUT_DIR, "tables", "v_aiken_results.csv"))
} else {
  cat("  No expert_ratings.csv found. Demonstrating with simulated data.\n")

  # Simulated example: 10 items rated by 5 experts on a 1-5 scale
  set.seed(42)
  sim_ratings <- matrix(
    sample(3:5, 50, replace = TRUE, prob = c(0.15, 0.35, 0.50)),
    nrow = 10, ncol = 5
  )
  rownames(sim_ratings) <- paste0("Item_", 1:10)
  colnames(sim_ratings) <- paste0("Expert_", 1:5)

  v_aiken_results <- compute_v_aiken(sim_ratings, k = 5)
  cat("  Simulated V de Aiken results:\n")
  print(v_aiken_results)

  write_csv(v_aiken_results, file.path(OUTPUT_DIR, "tables", "v_aiken_simulated.csv"))
}

# --------------------------------------------------------------------------
# 3. Intraclass Correlation Coefficient (ICC) for Inter-Rater Reliability
# --------------------------------------------------------------------------

cat("\n--- ICC (Inter-Rater Reliability) ---\n")

# Check for multi-rater rubric file
rater_file <- file.path(DATA_DIR, "rater_scores.csv")

if (file.exists(rater_file)) {
  rater_data <- read_csv(rater_file, show_col_types = FALSE)
  # Expected format: participant_id, rater_1, rater_2, ..., rater_k

  rater_cols <- grep("^rater_", names(rater_data), value = TRUE)
  rater_matrix <- as.matrix(rater_data[, rater_cols])

  icc_result <- irr::icc(rater_matrix,
                          model  = "twoway",
                          type   = "agreement",
                          unit   = "average")

  cat(paste0("  ICC(2,k) = ", round(icc_result$value, 3), "\n"))
  cat(paste0("  95% CI: [", round(icc_result$lbound, 3), ", ",
             round(icc_result$ubound, 3), "]\n"))
  cat(paste0("  F(", icc_result$df1, ",", icc_result$df2, ") = ",
             round(icc_result$Fvalue, 3), ", p = ",
             format.pval(icc_result$p.value, digits = 3), "\n"))

  # Interpretation
  if (icc_result$value >= 0.75) {
    cat("  Interpretation: Excellent agreement.\n")
  } else if (icc_result$value >= 0.60) {
    cat("  Interpretation: Good agreement.\n")
  } else if (icc_result$value >= 0.40) {
    cat("  Interpretation: Fair agreement.\n")
  } else {
    cat("  Interpretation: Poor agreement.\n")
  }

} else {
  cat("  No rater_scores.csv found. Demonstrating with simulated data.\n")

  # Simulated example: 30 students scored by 2 raters
  set.seed(123)
  true_scores <- rnorm(30, mean = 7, sd = 1.5)
  rater_sim <- data.frame(
    rater_1 = pmin(10, pmax(0, round(true_scores + rnorm(30, 0, 0.5), 1))),
    rater_2 = pmin(10, pmax(0, round(true_scores + rnorm(30, 0, 0.6), 1)))
  )

  icc_result <- irr::icc(as.matrix(rater_sim),
                          model  = "twoway",
                          type   = "agreement",
                          unit   = "single")

  cat(paste0("  Simulated ICC(2,1) = ", round(icc_result$value, 3), "\n"))
  cat(paste0("  95% CI: [", round(icc_result$lbound, 3), ", ",
             round(icc_result$ubound, 3), "]\n"))
}

cat("\n=== 03_instrument_validation.R: Complete ===\n\n")
