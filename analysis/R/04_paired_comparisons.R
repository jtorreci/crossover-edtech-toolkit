# ==============================================================================
# 04_paired_comparisons.R
# Purpose: Perform within-subject paired comparisons of performance under AI
#          vs noAI conditions. Each student serves as their own control.
#          - Paired t-test (parametric)
#          - Wilcoxon signed-rank test (non-parametric alternative)
#          - Confidence intervals and p-values
# Input:   df_clean.rds, df_wide.rds
# Output:  Test results saved to output/tables/
# ==============================================================================

cat("=== 04_paired_comparisons.R: Paired comparisons (AI vs noAI) ===\n")

df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))
df_wide  <- readRDS(file.path(OUTPUT_DIR, "df_wide.rds"))

# --------------------------------------------------------------------------
# 1. Check normality of differences
# --------------------------------------------------------------------------

cat("\n--- Normality check for score differences ---\n")

# Shapiro-Wilk test on the within-subject differences
shapiro_result <- shapiro.test(df_wide$score_diff)
cat(paste0("  Shapiro-Wilk W = ", round(shapiro_result$statistic, 4),
           ", p = ", format.pval(shapiro_result$p.value, digits = 4), "\n"))

if (shapiro_result$p.value < 0.05) {
  cat("  Normality assumption violated (p < 0.05). Non-parametric test recommended.\n")
  normality_ok <- FALSE
} else {
  cat("  Normality assumption not violated (p >= 0.05).\n")
  normality_ok <- TRUE
}

# QQ-plot of differences
p_qq <- ggplot(df_wide, aes(sample = score_diff)) +
  stat_qq(alpha = 0.6) +
  stat_qq_line(color = "red") +
  labs(
    title = "Q-Q Plot of Within-Subject Score Differences",
    x     = "Theoretical Quantiles",
    y     = "Sample Quantiles"
  )

ggsave(file.path(OUTPUT_DIR, "figures", "qq_score_diff.png"),
       p_qq, width = 6, height = 5, dpi = 300)

# --------------------------------------------------------------------------
# 2. Paired t-test: Score
# --------------------------------------------------------------------------

cat("\n--- Paired t-test: Score (AI vs noAI) ---\n")

t_result <- t.test(df_wide$score_AI, df_wide$score_noAI, paired = TRUE)

cat(paste0("  Mean difference (AI - noAI): ",
           round(t_result$estimate, 3), "\n"))
cat(paste0("  95% CI: [", round(t_result$conf.int[1], 3), ", ",
           round(t_result$conf.int[2], 3), "]\n"))
cat(paste0("  t(", t_result$parameter, ") = ",
           round(t_result$statistic, 3), "\n"))
cat(paste0("  p-value = ", format.pval(t_result$p.value, digits = 4), "\n"))

# --------------------------------------------------------------------------
# 3. Paired t-test: Rubric Score
# --------------------------------------------------------------------------

cat("\n--- Paired t-test: Rubric Score (AI vs noAI) ---\n")

# Handle potential NAs in rubric scores
df_wide_rubric <- df_wide %>%
  filter(!is.na(rubric_score_AI) & !is.na(rubric_score_noAI))

if (nrow(df_wide_rubric) >= 10) {
  t_rubric <- t.test(df_wide_rubric$rubric_score_AI,
                     df_wide_rubric$rubric_score_noAI,
                     paired = TRUE)

  cat(paste0("  Mean difference (AI - noAI): ",
             round(t_rubric$estimate, 3), "\n"))
  cat(paste0("  95% CI: [", round(t_rubric$conf.int[1], 3), ", ",
             round(t_rubric$conf.int[2], 3), "]\n"))
  cat(paste0("  t(", t_rubric$parameter, ") = ",
             round(t_rubric$statistic, 3), "\n"))
  cat(paste0("  p-value = ", format.pval(t_rubric$p.value, digits = 4), "\n"))
} else {
  cat("  Insufficient paired rubric data. Skipping.\n")
  t_rubric <- NULL
}

# --------------------------------------------------------------------------
# 4. Wilcoxon signed-rank test (non-parametric alternative)
# --------------------------------------------------------------------------

cat("\n--- Wilcoxon signed-rank test: Score ---\n")

wilcox_result <- wilcox.test(df_wide$score_AI, df_wide$score_noAI,
                              paired = TRUE, conf.int = TRUE)

cat(paste0("  Pseudomedian difference: ",
           round(wilcox_result$estimate, 3), "\n"))
cat(paste0("  95% CI: [", round(wilcox_result$conf.int[1], 3), ", ",
           round(wilcox_result$conf.int[2], 3), "]\n"))
cat(paste0("  V = ", wilcox_result$statistic, "\n"))
cat(paste0("  p-value = ", format.pval(wilcox_result$p.value, digits = 4), "\n"))

# --------------------------------------------------------------------------
# 5. Paired comparisons by sequence (sensitivity analysis)
# --------------------------------------------------------------------------

cat("\n--- Paired comparisons by sequence ---\n")

for (seq_level in levels(df_wide$sequence)) {
  cat(paste0("\n  Sequence ", seq_level, ":\n"))

  df_seq <- df_wide %>% filter(sequence == seq_level)

  if (nrow(df_seq) >= 5) {
    t_seq <- t.test(df_seq$score_AI, df_seq$score_noAI, paired = TRUE)

    cat(paste0("    n = ", nrow(df_seq), "\n"))
    cat(paste0("    Mean diff = ", round(t_seq$estimate, 3),
               " [", round(t_seq$conf.int[1], 3), ", ",
               round(t_seq$conf.int[2], 3), "]\n"))
    cat(paste0("    t = ", round(t_seq$statistic, 3),
               ", p = ", format.pval(t_seq$p.value, digits = 4), "\n"))
  }
}

# --------------------------------------------------------------------------
# 6. Compile results table
# --------------------------------------------------------------------------

results_table <- tibble(
  Outcome     = c("Score", "Score", "Rubric"),
  Test        = c("Paired t-test", "Wilcoxon signed-rank", "Paired t-test"),
  n           = c(t_result$parameter + 1,
                  nrow(df_wide),
                  ifelse(is.null(t_rubric), NA, t_rubric$parameter + 1)),
  Estimate    = c(round(t_result$estimate, 3),
                  round(wilcox_result$estimate, 3),
                  ifelse(is.null(t_rubric), NA, round(t_rubric$estimate, 3))),
  CI_lower    = c(round(t_result$conf.int[1], 3),
                  round(wilcox_result$conf.int[1], 3),
                  ifelse(is.null(t_rubric), NA, round(t_rubric$conf.int[1], 3))),
  CI_upper    = c(round(t_result$conf.int[2], 3),
                  round(wilcox_result$conf.int[2], 3),
                  ifelse(is.null(t_rubric), NA, round(t_rubric$conf.int[2], 3))),
  Statistic   = c(round(t_result$statistic, 3),
                  wilcox_result$statistic,
                  ifelse(is.null(t_rubric), NA, round(t_rubric$statistic, 3))),
  p_value     = c(t_result$p.value,
                  wilcox_result$p.value,
                  ifelse(is.null(t_rubric), NA, t_rubric$p.value))
)

write_csv(results_table, file.path(OUTPUT_DIR, "tables", "paired_comparisons.csv"))

cat("\n  Results saved to output/tables/paired_comparisons.csv\n")
cat("=== 04_paired_comparisons.R: Complete ===\n\n")
