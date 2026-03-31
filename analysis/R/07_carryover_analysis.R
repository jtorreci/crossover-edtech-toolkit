# ==============================================================================
# 07_carryover_analysis.R
# Purpose: Test for carryover effects in the crossover design.
#          In a 2x2 crossover, carryover means that the treatment received in
#          period 1 affects the outcome in period 2. The standard test compares
#          the sum of each participant's scores across periods between the two
#          sequence groups (Grizzle, 1965; Senn, 2002).
#          If significant carryover is detected, analyze only period 1 data
#          (parallel-group comparison).
# Input:   df_clean.rds, df_period_sums.rds
# Output:  Carryover test results in output/tables/
# ==============================================================================

cat("=== 07_carryover_analysis.R: Testing for carryover effects ===\n")

df_clean       <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))
df_period_sums <- readRDS(file.path(OUTPUT_DIR, "df_period_sums.rds"))

# --------------------------------------------------------------------------
# 1. Standard carryover test (Grizzle's test)
# --------------------------------------------------------------------------

cat("\n--- Grizzle's carryover test ---\n")
cat("  H0: No carryover effect (mean sum of scores equal across sequences)\n")
cat("  If the sum (Y_period1 + Y_period2) differs between AB and BA sequences,\n")
cat("  this suggests a carryover effect.\n\n")

# Two-sample t-test on the sum of scores between sequences
sums_AB <- df_period_sums %>% filter(sequence == "AB") %>% pull(score_sum)
sums_BA <- df_period_sums %>% filter(sequence == "BA") %>% pull(score_sum)

carryover_test <- t.test(sums_AB, sums_BA, var.equal = FALSE)

cat(paste0("  Sequence AB: mean sum = ", round(mean(sums_AB), 3),
           " (SD = ", round(sd(sums_AB), 3), ", n = ", length(sums_AB), ")\n"))
cat(paste0("  Sequence BA: mean sum = ", round(mean(sums_BA), 3),
           " (SD = ", round(sd(sums_BA), 3), ", n = ", length(sums_BA), ")\n"))
cat(paste0("  Difference: ", round(carryover_test$estimate[1] - carryover_test$estimate[2], 3), "\n"))
cat(paste0("  t(", round(carryover_test$parameter, 1), ") = ",
           round(carryover_test$statistic, 3), "\n"))
cat(paste0("  p-value = ", format.pval(carryover_test$p.value, digits = 4), "\n"))
cat(paste0("  95% CI for difference: [",
           round(carryover_test$conf.int[1], 3), ", ",
           round(carryover_test$conf.int[2], 3), "]\n"))

carryover_significant <- carryover_test$p.value < 0.10  # Use alpha = 0.10 for carryover

if (carryover_significant) {
  cat("\n  *** CARRYOVER EFFECT DETECTED (p < 0.10) ***\n")
  cat("  Recommendation: Analyze only Period 1 data (parallel-group comparison).\n")
} else {
  cat("\n  No significant carryover effect (p >= 0.10).\n")
  cat("  The standard crossover analysis is valid.\n")
}

# --------------------------------------------------------------------------
# 2. Non-parametric carryover test (Wilcoxon rank-sum)
# --------------------------------------------------------------------------

cat("\n--- Non-parametric carryover test (Wilcoxon) ---\n")

wilcox_carryover <- wilcox.test(sums_AB, sums_BA, conf.int = TRUE)

cat(paste0("  W = ", wilcox_carryover$statistic, "\n"))
cat(paste0("  p-value = ", format.pval(wilcox_carryover$p.value, digits = 4), "\n"))

# --------------------------------------------------------------------------
# 3. Visual check: boxplot of sums by sequence
# --------------------------------------------------------------------------

p_carryover <- ggplot(df_period_sums, aes(x = sequence, y = score_sum, fill = sequence)) +
  geom_boxplot(alpha = 0.7, width = 0.5) +
  geom_jitter(width = 0.1, alpha = 0.4, size = 1.5) +
  scale_fill_brewer(palette = "Set1") +
  labs(
    title    = "Carryover Test: Sum of Scores by Sequence",
    subtitle = paste0("t-test p = ", format.pval(carryover_test$p.value, digits = 3)),
    x        = "Sequence",
    y        = "Sum of scores (Period 1 + Period 2)"
  ) +
  theme(legend.position = "none")

ggsave(file.path(OUTPUT_DIR, "figures", "carryover_test.png"),
       p_carryover, width = 6, height = 5, dpi = 300)

# --------------------------------------------------------------------------
# 4. Period effect test
# --------------------------------------------------------------------------

cat("\n--- Period effect test ---\n")
cat("  Compare the difference (Y_period1 - Y_period2) between sequences.\n")

df_period_diff <- df_clean %>%
  select(participant_id, sequence, period, score) %>%
  pivot_wider(names_from = period, values_from = score, names_prefix = "P") %>%
  mutate(period_diff = `PPeriod 1` - `PPeriod 2`)

period_test <- t.test(period_diff ~ sequence, data = df_period_diff)

cat(paste0("  t(", round(period_test$parameter, 1), ") = ",
           round(period_test$statistic, 3), "\n"))
cat(paste0("  p-value = ", format.pval(period_test$p.value, digits = 4), "\n"))

# --------------------------------------------------------------------------
# 5. If carryover is significant: Period 1 only analysis
# --------------------------------------------------------------------------

if (carryover_significant) {
  cat("\n--- Period 1 only analysis (due to carryover) ---\n")

  df_p1 <- df_clean %>% filter(period == "Period 1")

  # In period 1: sequence AB gets noAI, sequence BA gets AI
  p1_test <- t.test(score ~ condition, data = df_p1, var.equal = FALSE)

  cat(paste0("  Period 1 comparison (unpaired, AI vs noAI):\n"))
  cat(paste0("    AI mean:   ", round(mean(df_p1$score[df_p1$condition == "AI"]), 3), "\n"))
  cat(paste0("    noAI mean: ", round(mean(df_p1$score[df_p1$condition == "noAI"]), 3), "\n"))
  cat(paste0("    t = ", round(p1_test$statistic, 3),
             ", p = ", format.pval(p1_test$p.value, digits = 4), "\n"))

  # Cohen's d for independent samples
  d_p1 <- effectsize::cohens_d(score ~ condition, data = df_p1, ci = 0.95)
  cat("    Effect size:\n")
  print(d_p1)
} else {
  cat("\n  Period 1 only analysis not needed (no carryover detected).\n")
}

# --------------------------------------------------------------------------
# 6. Save carryover test results
# --------------------------------------------------------------------------

carryover_results <- tibble(
  Test        = c("Grizzle (t-test)", "Wilcoxon rank-sum"),
  Statistic   = c(round(carryover_test$statistic, 3), wilcox_carryover$statistic),
  df          = c(round(carryover_test$parameter, 1), NA),
  p_value     = c(carryover_test$p.value, wilcox_carryover$p.value),
  Significant = c(carryover_test$p.value < 0.10, wilcox_carryover$p.value < 0.10),
  Note        = c("alpha = 0.10 for carryover", "Non-parametric alternative")
)

write_csv(carryover_results, file.path(OUTPUT_DIR, "tables", "carryover_test.csv"))

cat("\n=== 07_carryover_analysis.R: Complete ===\n\n")
