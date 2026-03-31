# ==============================================================================
# generate_sample_data.R
# Purpose: Generate a realistic synthetic dataset simulating 100 students in a
#          2x2 crossover design for evaluating AI impact on learning.
#
# Design:
#   - 50 students in Sequence AB: Period 1 = noAI, Period 2 = AI
#   - 50 students in Sequence BA: Period 1 = AI,   Period 2 = noAI
#   - Treatment effect: AI improves scores by ~5 points (small-medium effect)
#   - Period effect: ~3 points improvement from Period 1 to Period 2 (learning)
#   - NO carryover effect (by design)
#   - Realistic noise and some missing values (~3%)
#
# Output: crossover_sample_data.csv in sample_data/
# ==============================================================================

cat("=== generate_sample_data.R: Generating synthetic crossover data ===\n")

set.seed(2026)

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------

n_total      <- 100       # Total participants
n_per_seq    <- 50        # Per sequence (balanced)
mu           <- 65        # Grand mean score
tau          <- 5         # Treatment effect (AI advantage)
pi_effect    <- 3         # Period effect (learning/practice)
lambda       <- 0         # Carryover effect (none)
sigma_subj   <- 12        # Between-subject SD (individual differences)
sigma_resid  <- 8         # Within-subject residual SD

# --------------------------------------------------------------------------
# Generate participant-level data
# --------------------------------------------------------------------------

participants <- tibble(
  participant_id = sprintf("P%03d", 1:n_total),
  group          = rep(c("A", "B"), each = n_per_seq),
  sequence       = rep(c("AB", "BA"), each = n_per_seq),
  subject_effect = rnorm(n_total, mean = 0, sd = sigma_subj)
)

# --------------------------------------------------------------------------
# Generate observation-level data (2 rows per participant)
# --------------------------------------------------------------------------

df <- participants %>%
  crossing(period = 1:2) %>%
  mutate(
    # Assign condition based on sequence and period
    condition = case_when(
      sequence == "AB" & period == 1 ~ "noAI",
      sequence == "AB" & period == 2 ~ "AI",
      sequence == "BA" & period == 1 ~ "AI",
      sequence == "BA" & period == 2 ~ "noAI"
    ),

    # Treatment indicator (1 for AI, 0 for noAI)
    treatment_ind = ifelse(condition == "AI", 1, 0),

    # Period indicator (centered: -0.5 for period 1, +0.5 for period 2)
    period_centered = period - 1.5,

    # Carryover: only in period 2, based on what was received in period 1
    # For AB: period 2 has carryover from noAI (lambda_noAI)
    # For BA: period 2 has carryover from AI (lambda_AI)
    # With lambda = 0, this has no effect
    carryover_term = case_when(
      period == 1                     ~ 0,
      sequence == "AB" & period == 2  ~ 0,         # carryover from noAI = 0
      sequence == "BA" & period == 2  ~ lambda,    # carryover from AI
      TRUE                            ~ 0
    ),

    # Generate score from the model:
    # Y = mu + pi*period + tau*treatment + lambda*carryover + S_i + epsilon
    residual = rnorm(n(), mean = 0, sd = sigma_resid),
    score_raw = mu +
                pi_effect * period_centered +
                tau * treatment_ind +
                carryover_term +
                subject_effect +
                residual,

    # Bound score to 0-100
    score = pmin(100, pmax(0, round(score_raw, 1)))
  ) %>%
  select(-treatment_ind, -period_centered, -carryover_term,
         -subject_effect, -residual, -score_raw)

# --------------------------------------------------------------------------
# Generate rubric scores (correlated with main score)
# --------------------------------------------------------------------------

df <- df %>%
  mutate(
    # Rubric on 0-10 scale, correlated with score (~r = 0.75)
    rubric_score = pmin(10, pmax(0, round(
      score / 10 * 0.75 + rnorm(n(), mean = 0, sd = 1.0) + 0.5, 1
    )))
  )

# --------------------------------------------------------------------------
# Generate Likert scale items (1-5, perception questionnaire)
# --------------------------------------------------------------------------

# 6 Likert items measuring perception of the task/tool
# Items correlate moderately with each other (alpha ~ 0.75-0.85)
# AI condition tends to get slightly higher satisfaction scores

generate_likert <- function(n, condition, base_mean = 3.2, ai_bonus = 0.4) {
  bonus <- ifelse(condition == "AI", ai_bonus, 0)
  raw <- rnorm(n, mean = base_mean + bonus, sd = 0.9)
  pmin(5, pmax(1, round(raw)))
}

# Generate a common factor and add item-specific noise
df <- df %>%
  mutate(
    common_factor = rnorm(n(), mean = 0, sd = 0.6),

    likert_usefulness   = pmin(5, pmax(1, round(3.3 + ifelse(condition == "AI", 0.5, 0) +
                            common_factor + rnorm(n(), 0, 0.7)))),
    likert_ease         = pmin(5, pmax(1, round(3.5 + ifelse(condition == "AI", 0.3, 0) +
                            common_factor + rnorm(n(), 0, 0.8)))),
    likert_confidence   = pmin(5, pmax(1, round(3.1 + ifelse(condition == "AI", 0.4, 0) +
                            common_factor + rnorm(n(), 0, 0.7)))),
    likert_engagement   = pmin(5, pmax(1, round(3.4 + ifelse(condition == "AI", 0.3, 0) +
                            common_factor + rnorm(n(), 0, 0.8)))),
    likert_satisfaction = pmin(5, pmax(1, round(3.2 + ifelse(condition == "AI", 0.5, 0) +
                            common_factor + rnorm(n(), 0, 0.7)))),
    likert_learning     = pmin(5, pmax(1, round(3.3 + ifelse(condition == "AI", 0.2, 0) +
                            common_factor + rnorm(n(), 0, 0.8))))
  ) %>%
  select(-common_factor)

# --------------------------------------------------------------------------
# Generate time spent (minutes)
# --------------------------------------------------------------------------

df <- df %>%
  mutate(
    # AI users tend to spend slightly less time
    time_spent = round(pmax(5, rnorm(
      n(),
      mean = ifelse(condition == "AI", 35, 42),
      sd   = 10
    )), 1)
  )

# --------------------------------------------------------------------------
# Introduce realistic missing values (~3%)
# --------------------------------------------------------------------------

set.seed(999)
n_obs <- nrow(df)

# Missing rubric scores (evaluator didn't submit)
missing_rubric <- sample(n_obs, size = round(n_obs * 0.03))
df$rubric_score[missing_rubric] <- NA

# Missing Likert items (skipped questions)
likert_cols <- grep("^likert_", names(df), value = TRUE)
for (col in likert_cols) {
  missing_idx <- sample(n_obs, size = sample(1:4, 1))
  df[[col]][missing_idx] <- NA
}

# Missing time (technical issue with logging)
missing_time <- sample(n_obs, size = 2)
df$time_spent[missing_time] <- NA

# --------------------------------------------------------------------------
# Final dataset
# --------------------------------------------------------------------------

# Reorder columns for clarity
df_final <- df %>%
  select(
    participant_id, group, sequence, period, condition,
    score, rubric_score, time_spent,
    starts_with("likert_")
  ) %>%
  arrange(participant_id, period)

cat(paste0("  Generated ", nrow(df_final), " observations for ",
           n_distinct(df_final$participant_id), " participants.\n"))
cat(paste0("  Sequences: ", paste(table(participants$sequence), collapse = " / "), "\n"))
cat(paste0("  Missing values: ",
           sum(is.na(df_final$score)), " scores, ",
           sum(is.na(df_final$rubric_score)), " rubric, ",
           sum(is.na(df_final$time_spent)), " time\n"))

# Determine output path
output_path <- tryCatch({
  file.path(dirname(sys.frame(1)$ofile), "crossover_sample_data.csv")
}, error = function(e) {
  file.path("sample_data", "crossover_sample_data.csv")
})

# If running from project root, use sample_data/
if (!dir.exists(dirname(output_path))) {
  output_path <- file.path("sample_data", "crossover_sample_data.csv")
}

write_csv(df_final, output_path)
cat(paste0("  Saved to: ", output_path, "\n"))

# Quick sanity checks
cat("\n  Sanity checks:\n")
cat(paste0("    Mean score (AI):   ", round(mean(df_final$score[df_final$condition == "AI"], na.rm = TRUE), 2), "\n"))
cat(paste0("    Mean score (noAI): ", round(mean(df_final$score[df_final$condition == "noAI"], na.rm = TRUE), 2), "\n"))
cat(paste0("    Expected diff:     ~", tau, " points\n"))

cat("=== generate_sample_data.R: Complete ===\n")
