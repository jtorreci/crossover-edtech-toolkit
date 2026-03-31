# ==============================================================================
# 02_descriptive_stats.R
# Purpose: Compute and display summary statistics for the crossover dataset,
#          broken down by group, period, condition, and sequence.
# Input:   df_clean.rds from 01_data_import_clean.R
# Output:  Summary tables (CSV) and basic plots (PNG) in output/
# ==============================================================================

cat("=== 02_descriptive_stats.R: Computing descriptive statistics ===\n")

# Load cleaned data
df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))

# --------------------------------------------------------------------------
# 1. Overall summary statistics
# --------------------------------------------------------------------------

overall_summary <- df_clean %>%
  summarise(
    n          = n(),
    mean_score = mean(score, na.rm = TRUE),
    sd_score   = sd(score, na.rm = TRUE),
    median_score = median(score, na.rm = TRUE),
    min_score  = min(score, na.rm = TRUE),
    max_score  = max(score, na.rm = TRUE),
    mean_rubric = mean(rubric_score, na.rm = TRUE),
    sd_rubric   = sd(rubric_score, na.rm = TRUE),
    mean_time  = mean(time_spent, na.rm = TRUE),
    sd_time    = sd(time_spent, na.rm = TRUE)
  )

cat("  Overall summary:\n")
print(overall_summary)

# --------------------------------------------------------------------------
# 2. Summary by condition (AI vs noAI)
# --------------------------------------------------------------------------

by_condition <- df_clean %>%
  group_by(condition) %>%
  summarise(
    n          = n(),
    mean_score = round(mean(score, na.rm = TRUE), 2),
    sd_score   = round(sd(score, na.rm = TRUE), 2),
    median_score = round(median(score, na.rm = TRUE), 2),
    mean_rubric = round(mean(rubric_score, na.rm = TRUE), 2),
    sd_rubric   = round(sd(rubric_score, na.rm = TRUE), 2),
    mean_time  = round(mean(time_spent, na.rm = TRUE), 2),
    sd_time    = round(sd(time_spent, na.rm = TRUE), 2),
    .groups    = "drop"
  )

cat("\n  Summary by condition:\n")
print(by_condition)

write_csv(by_condition, file.path(OUTPUT_DIR, "tables", "summary_by_condition.csv"))

# --------------------------------------------------------------------------
# 3. Summary by condition and period (the 2x2 cell means)
# --------------------------------------------------------------------------

by_condition_period <- df_clean %>%
  group_by(condition, period) %>%
  summarise(
    n          = n(),
    mean_score = round(mean(score, na.rm = TRUE), 2),
    sd_score   = round(sd(score, na.rm = TRUE), 2),
    mean_rubric = round(mean(rubric_score, na.rm = TRUE), 2),
    sd_rubric   = round(sd(rubric_score, na.rm = TRUE), 2),
    .groups    = "drop"
  )

cat("\n  Summary by condition x period:\n")
print(by_condition_period)

write_csv(by_condition_period,
          file.path(OUTPUT_DIR, "tables", "summary_condition_period.csv"))

# --------------------------------------------------------------------------
# 4. Summary by sequence (AB vs BA)
# --------------------------------------------------------------------------

by_sequence <- df_clean %>%
  group_by(sequence, period, condition) %>%
  summarise(
    n          = n(),
    mean_score = round(mean(score, na.rm = TRUE), 2),
    sd_score   = round(sd(score, na.rm = TRUE), 2),
    .groups    = "drop"
  )

cat("\n  Summary by sequence x period x condition:\n")
print(by_sequence)

write_csv(by_sequence, file.path(OUTPUT_DIR, "tables", "summary_by_sequence.csv"))

# --------------------------------------------------------------------------
# 5. Basic plots
# --------------------------------------------------------------------------

# Boxplot: Score by condition
p1 <- ggplot(df_clean, aes(x = condition, y = score, fill = condition)) +
  geom_boxplot(alpha = 0.7, outlier.shape = 21) +
  geom_jitter(width = 0.15, alpha = 0.3, size = 1) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Score Distribution by Condition",
    x     = "Condition",
    y     = "Score (0-100)"
  ) +
  theme(legend.position = "none")

ggsave(file.path(OUTPUT_DIR, "figures", "boxplot_score_by_condition.png"),
       p1, width = 6, height = 5, dpi = 300)

# Boxplot: Score by condition and period
p2 <- ggplot(df_clean, aes(x = period, y = score, fill = condition)) +
  geom_boxplot(alpha = 0.7, position = position_dodge(0.8)) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Score by Period and Condition",
    x     = "Period",
    y     = "Score (0-100)",
    fill  = "Condition"
  )

ggsave(file.path(OUTPUT_DIR, "figures", "boxplot_score_period_condition.png"),
       p2, width = 7, height = 5, dpi = 300)

# Histogram of score differences (AI - noAI)
df_wide <- readRDS(file.path(OUTPUT_DIR, "df_wide.rds"))

p3 <- ggplot(df_wide, aes(x = score_diff)) +
  geom_histogram(binwidth = 5, fill = "steelblue", color = "white", alpha = 0.8) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "red", linewidth = 0.8) +
  geom_vline(xintercept = mean(df_wide$score_diff, na.rm = TRUE),
             linetype = "solid", color = "darkblue", linewidth = 0.8) +
  labs(
    title    = "Distribution of Within-Subject Score Differences (AI - noAI)",
    subtitle = "Blue line = mean difference; red dashed = zero",
    x        = "Score difference (AI - noAI)",
    y        = "Count"
  )

ggsave(file.path(OUTPUT_DIR, "figures", "histogram_score_diff.png"),
       p3, width = 7, height = 5, dpi = 300)

# Time spent by condition
p4 <- ggplot(df_clean, aes(x = condition, y = time_spent, fill = condition)) +
  geom_boxplot(alpha = 0.7) +
  scale_fill_brewer(palette = "Pastel1") +
  labs(
    title = "Time Spent by Condition",
    x     = "Condition",
    y     = "Time (minutes)"
  ) +
  theme(legend.position = "none")

ggsave(file.path(OUTPUT_DIR, "figures", "boxplot_time_by_condition.png"),
       p4, width = 6, height = 5, dpi = 300)

cat("  Saved tables and figures to output/\n")
cat("=== 02_descriptive_stats.R: Complete ===\n\n")
