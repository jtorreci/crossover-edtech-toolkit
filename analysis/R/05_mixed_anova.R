# ==============================================================================
# 05_mixed_anova.R
# Purpose: Fit a mixed ANOVA for the 2x2 crossover design:
#          - Within-subjects factor: treatment (AI vs noAI)
#          - Within-subjects factor: period (1 vs 2)
#          - Between-subjects factor: sequence (AB vs BA)
#          Also fit a linear mixed model (lme4) as a robustness check.
# Input:   df_clean.rds
# Output:  ANOVA tables and model summaries in output/
# ==============================================================================

cat("=== 05_mixed_anova.R: Mixed ANOVA and linear mixed models ===\n")

df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))

# --------------------------------------------------------------------------
# 1. Check assumptions
# --------------------------------------------------------------------------

cat("\n--- Assumption checks ---\n")

# 1a. Normality of residuals by cell
cat("  Shapiro-Wilk tests by condition x period:\n")
normality_tests <- df_clean %>%
  group_by(condition, period) %>%
  rstatix::shapiro_test(score) %>%
  as.data.frame()

print(normality_tests)

# 1b. Homogeneity of variances (Levene's test)
cat("\n  Levene's test for homogeneity of variances:\n")
levene_result <- car::leveneTest(score ~ condition * sequence, data = df_clean)
print(levene_result)

# 1c. Check for outliers in each cell
cat("\n  Extreme outliers (> 3*IQR) by cell:\n")
outlier_check <- df_clean %>%
  group_by(condition, period) %>%
  rstatix::identify_outliers(score) %>%
  filter(is.extreme) %>%
  as.data.frame()

if (nrow(outlier_check) > 0) {
  print(outlier_check %>% select(participant_id, condition, period, score, is.extreme))
} else {
  cat("  No extreme outliers detected.\n")
}

# --------------------------------------------------------------------------
# 2. Mixed ANOVA using rstatix
# --------------------------------------------------------------------------

cat("\n--- Mixed ANOVA (rstatix) ---\n")
cat("  Model: score ~ treatment * period, between = sequence, id = participant_id\n")

# For the crossover design, treatment and period are within-subject in the sense
# that each participant experiences both, but they are confounded by sequence.
# We use the standard crossover parameterization.

# Prepare data: ensure proper structure for anova_test
# In the crossover, 'condition' varies within subjects across periods
anova_result <- rstatix::anova_test(
  data      = df_clean,
  dv        = score,
  wid       = participant_id,
  within    = c(condition),
  between   = sequence,
  type      = 3
)

cat("\n  ANOVA table:\n")
print(rstatix::get_anova_table(anova_result))

# Save ANOVA table
anova_table <- rstatix::get_anova_table(anova_result) %>% as.data.frame()
write_csv(anova_table, file.path(OUTPUT_DIR, "tables", "mixed_anova.csv"))

# --------------------------------------------------------------------------
# 3. Post-hoc pairwise comparisons
# --------------------------------------------------------------------------

cat("\n--- Post-hoc comparisons ---\n")

# Pairwise comparisons for condition within each sequence
posthoc <- df_clean %>%
  group_by(sequence) %>%
  rstatix::pairwise_t_test(
    score ~ condition,
    paired     = TRUE,
    p.adjust.method = "bonferroni"
  ) %>%
  as.data.frame()

cat("  Pairwise comparisons by sequence:\n")
print(posthoc)

write_csv(posthoc, file.path(OUTPUT_DIR, "tables", "posthoc_comparisons.csv"))

# --------------------------------------------------------------------------
# 4. Linear Mixed Model (lme4) - Robustness check
# --------------------------------------------------------------------------

cat("\n--- Linear Mixed Model (lme4) ---\n")
cat("  Model: score ~ condition + period + sequence + (1 | participant_id)\n")

# Recode period as numeric for the mixed model
df_clean <- df_clean %>%
  mutate(period_num = as.numeric(period))

# Fit the model
lmm_fit <- lmer(score ~ condition + period_num + sequence + (1 | participant_id),
                data = df_clean)

cat("\n  Model summary:\n")
print(summary(lmm_fit))

# Extract fixed effects with confidence intervals
cat("\n  Fixed effects with 95% CI:\n")
fixed_ci <- confint(lmm_fit, method = "Wald")
fixed_effects <- fixef(lmm_fit)
fe_table <- data.frame(
  term     = names(fixed_effects),
  estimate = round(fixed_effects, 3),
  CI_lower = round(fixed_ci[names(fixed_effects), 1], 3),
  CI_upper = round(fixed_ci[names(fixed_effects), 2], 3)
)
print(fe_table)

write_csv(fe_table, file.path(OUTPUT_DIR, "tables", "lmm_fixed_effects.csv"))

# --------------------------------------------------------------------------
# 5. Model with treatment x period interaction (to test carryover)
# --------------------------------------------------------------------------

cat("\n--- Extended model with interaction ---\n")
cat("  Model: score ~ condition * period_num + sequence + (1 | participant_id)\n")

lmm_interaction <- lmer(
  score ~ condition * period_num + sequence + (1 | participant_id),
  data = df_clean
)

cat("\n  Model summary:\n")
print(summary(lmm_interaction))

# Compare models
cat("\n  Model comparison (likelihood ratio test):\n")
anova_comparison <- anova(lmm_fit, lmm_interaction)
print(anova_comparison)

# --------------------------------------------------------------------------
# 6. Estimated marginal means (emmeans)
# --------------------------------------------------------------------------

cat("\n--- Estimated Marginal Means ---\n")

emm_condition <- emmeans(lmm_fit, ~ condition)
cat("\n  EMMs by condition:\n")
print(summary(emm_condition))

emm_pairs <- pairs(emm_condition)
cat("\n  Pairwise contrasts:\n")
print(summary(emm_pairs, infer = c(TRUE, TRUE)))

# Save EMMs
emm_df <- as.data.frame(summary(emm_condition))
write_csv(emm_df, file.path(OUTPUT_DIR, "tables", "emm_by_condition.csv"))

# Save model objects
saveRDS(lmm_fit, file.path(OUTPUT_DIR, "models", "lmm_main.rds"))
saveRDS(lmm_interaction, file.path(OUTPUT_DIR, "models", "lmm_interaction.rds"))

cat("\n  Saved models and tables.\n")
cat("=== 05_mixed_anova.R: Complete ===\n\n")
