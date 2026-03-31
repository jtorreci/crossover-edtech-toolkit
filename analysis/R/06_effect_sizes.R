# ==============================================================================
# 06_effect_sizes.R
# Purpose: Compute effect sizes for the crossover study:
#          - Cohen's d for paired comparisons (within-subject)
#          - Partial eta-squared for ANOVA effects
#          - Confidence intervals for all effect sizes
# Input:   df_clean.rds, df_wide.rds, ANOVA/LMM results from previous scripts
# Output:  Effect size table in output/tables/
# ==============================================================================

cat("=== 06_effect_sizes.R: Computing effect sizes ===\n")

df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))
df_wide  <- readRDS(file.path(OUTPUT_DIR, "df_wide.rds"))

# --------------------------------------------------------------------------
# 1. Cohen's d for paired comparisons (Score: AI vs noAI)
# --------------------------------------------------------------------------

cat("\n--- Cohen's d (paired) ---\n")

# Using effectsize package for Cohen's d with CI
d_score <- effectsize::cohens_d(
  df_wide$score_AI,
  df_wide$score_noAI,
  paired = TRUE,
  ci     = 0.95
)

cat("  Score (AI vs noAI):\n")
print(d_score)

# Rubric score
df_wide_rubric <- df_wide %>%
  filter(!is.na(rubric_score_AI) & !is.na(rubric_score_noAI))

d_rubric <- NULL
if (nrow(df_wide_rubric) >= 10) {
  d_rubric <- effectsize::cohens_d(
    df_wide_rubric$rubric_score_AI,
    df_wide_rubric$rubric_score_noAI,
    paired = TRUE,
    ci     = 0.95
  )
  cat("\n  Rubric score (AI vs noAI):\n")
  print(d_rubric)
}

# --------------------------------------------------------------------------
# 2. Cohen's d by sequence (sensitivity analysis)
# --------------------------------------------------------------------------

cat("\n--- Cohen's d by sequence ---\n")

d_by_sequence <- list()
for (seq_level in levels(df_wide$sequence)) {
  df_seq <- df_wide %>% filter(sequence == seq_level)

  if (nrow(df_seq) >= 5) {
    d_seq <- effectsize::cohens_d(
      df_seq$score_AI,
      df_seq$score_noAI,
      paired = TRUE,
      ci     = 0.95
    )
    d_by_sequence[[seq_level]] <- d_seq
    cat(paste0("  Sequence ", seq_level, ":\n"))
    print(d_seq)
  }
}

# --------------------------------------------------------------------------
# 3. Partial eta-squared from ANOVA
# --------------------------------------------------------------------------

cat("\n--- Partial eta-squared from ANOVA ---\n")

# Refit the ANOVA to extract effect sizes
anova_result <- rstatix::anova_test(
  data    = df_clean,
  dv      = score,
  wid     = participant_id,
  within  = condition,
  between = sequence,
  type    = 3
)

anova_table <- rstatix::get_anova_table(anova_result) %>% as.data.frame()

cat("  ANOVA effects with partial eta-squared (ges = generalized eta-squared):\n")
print(anova_table)

# Compute partial eta-squared from the ANOVA table (ges column)
# Note: effectsize::eta_squared() on lmer models can fail with newer lme4/lmerTest
# versions, so we extract from the rstatix ANOVA table directly.
cat("\n  Generalized eta-squared (ges) from ANOVA table:\n")
for (i in seq_len(nrow(anova_table))) {
  cat(sprintf("    %s: ges = %.4f\n", anova_table$Effect[i], anova_table$ges[i]))
}

# --------------------------------------------------------------------------
# 4. Hedges' g (bias-corrected Cohen's d) for small samples
# --------------------------------------------------------------------------

cat("\n--- Hedges' g (bias-corrected) ---\n")

g_score <- effectsize::hedges_g(
  df_wide$score_AI,
  df_wide$score_noAI,
  paired = TRUE,
  ci     = 0.95
)

cat("  Score (AI vs noAI), Hedges' g:\n")
print(g_score)

# --------------------------------------------------------------------------
# 5. Interpretation guidelines
# --------------------------------------------------------------------------

cat("\n--- Effect size interpretation ---\n")

interpret_d <- function(d_val) {
  d_abs <- abs(d_val)
  if (d_abs < 0.2) return("negligible")
  if (d_abs < 0.5) return("small")
  if (d_abs < 0.8) return("medium")
  return("large")
}

d_val <- as.numeric(d_score$Cohens_d)
cat(paste0("  Cohen's d = ", round(d_val, 3),
           " -> ", interpret_d(d_val), " effect\n"))

# --------------------------------------------------------------------------
# 6. Compile effect size summary table
# --------------------------------------------------------------------------

effect_size_table <- tibble(
  Comparison = c(
    "Score: AI vs noAI (Cohen's d)",
    "Score: AI vs noAI (Hedges' g)",
    ifelse(!is.null(d_rubric), "Rubric: AI vs noAI (Cohen's d)", NA)
  ),
  Estimate   = c(
    round(as.numeric(d_score$Cohens_d), 3),
    round(as.numeric(g_score$Hedges_g), 3),
    ifelse(!is.null(d_rubric), round(as.numeric(d_rubric$Cohens_d), 3), NA)
  ),
  CI_lower   = c(
    round(as.numeric(d_score$CI_low), 3),
    round(as.numeric(g_score$CI_low), 3),
    ifelse(!is.null(d_rubric), round(as.numeric(d_rubric$CI_low), 3), NA)
  ),
  CI_upper   = c(
    round(as.numeric(d_score$CI_high), 3),
    round(as.numeric(g_score$CI_high), 3),
    ifelse(!is.null(d_rubric), round(as.numeric(d_rubric$CI_high), 3), NA)
  ),
  Interpretation = c(
    interpret_d(as.numeric(d_score$Cohens_d)),
    interpret_d(as.numeric(g_score$Hedges_g)),
    ifelse(!is.null(d_rubric), interpret_d(as.numeric(d_rubric$Cohens_d)), NA)
  )
) %>%
  filter(!is.na(Comparison))

# Add sequence-level effect sizes
for (seq_level in names(d_by_sequence)) {
  d_val <- as.numeric(d_by_sequence[[seq_level]]$Cohens_d)
  effect_size_table <- effect_size_table %>%
    add_row(
      Comparison     = paste0("Score: AI vs noAI, sequence ", seq_level, " (Cohen's d)"),
      Estimate       = round(d_val, 3),
      CI_lower       = round(as.numeric(d_by_sequence[[seq_level]]$CI_low), 3),
      CI_upper       = round(as.numeric(d_by_sequence[[seq_level]]$CI_high), 3),
      Interpretation = interpret_d(d_val)
    )
}

cat("\n  Summary table:\n")
print(effect_size_table)

write_csv(effect_size_table, file.path(OUTPUT_DIR, "tables", "effect_sizes.csv"))

cat("\n=== 06_effect_sizes.R: Complete ===\n\n")
