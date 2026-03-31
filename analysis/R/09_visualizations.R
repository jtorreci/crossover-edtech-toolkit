# ==============================================================================
# 09_visualizations.R
# Purpose: Generate publication-quality plots for the crossover study:
#          - Interaction plot (crossover design)
#          - Individual trajectory (spaghetti) plots
#          - Forest plot of effect sizes
#          - Composite figure for publication
# Input:   df_clean.rds, df_wide.rds, effect_sizes.csv
# Output:  Publication-ready PNG and PDF figures in output/figures/
# ==============================================================================

cat("=== 09_visualizations.R: Generating publication-quality plots ===\n")

df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))
df_wide  <- readRDS(file.path(OUTPUT_DIR, "df_wide.rds"))

# --------------------------------------------------------------------------
# 1. Interaction plot (classic crossover design visualization)
# --------------------------------------------------------------------------

cat("  Generating interaction plot...\n")

# Cell means and standard errors
cell_stats <- df_clean %>%
  group_by(sequence, period, condition) %>%
  summarise(
    mean_score = mean(score, na.rm = TRUE),
    se_score   = sd(score, na.rm = TRUE) / sqrt(n()),
    n          = n(),
    .groups    = "drop"
  )

p_interaction <- ggplot(cell_stats, aes(x = period, y = mean_score,
                                         color = sequence, group = sequence)) +
  geom_point(size = 3.5) +
  geom_line(linewidth = 1.1) +
  geom_errorbar(aes(ymin = mean_score - 1.96 * se_score,
                     ymax = mean_score + 1.96 * se_score),
                width = 0.1, linewidth = 0.7) +
  scale_color_manual(
    values = c("AB" = "#0072B2", "BA" = "#D55E00"),
    labels = c("AB" = "Sequence AB (noAI -> AI)",
               "BA" = "Sequence BA (AI -> noAI)")
  ) +
  labs(
    title    = "Crossover Design: Mean Scores by Sequence and Period",
    subtitle = "Error bars represent 95% confidence intervals",
    x        = "Period",
    y        = "Mean Score",
    color    = "Sequence"
  ) +
  theme(
    legend.position = "bottom",
    legend.title    = element_text(face = "bold"),
    plot.title      = element_text(size = 14)
  )

ggsave(file.path(OUTPUT_DIR, "figures", "interaction_plot.png"),
       p_interaction, width = 8, height = 6, dpi = 300)

ggsave(file.path(OUTPUT_DIR, "figures", "interaction_plot.pdf"),
       p_interaction, width = 8, height = 6)

# --------------------------------------------------------------------------
# 2. Spaghetti plot (individual trajectories)
# --------------------------------------------------------------------------

cat("  Generating spaghetti plot...\n")

p_spaghetti <- ggplot(df_clean, aes(x = period, y = score, group = participant_id)) +
  geom_line(alpha = 0.2, color = "grey50") +
  geom_point(aes(color = condition), alpha = 0.4, size = 1.5) +
  # Add group means
  geom_line(data = cell_stats, aes(x = period, y = mean_score,
                                    group = sequence, color = NULL),
            linewidth = 1.5, color = "black", linetype = "dashed") +
  facet_wrap(~ sequence, labeller = labeller(
    sequence = c("AB" = "Sequence AB (noAI -> AI)",
                 "BA" = "Sequence BA (AI -> noAI)")
  )) +
  scale_color_manual(
    values = c("noAI" = "#E69F00", "AI" = "#009E73"),
    name   = "Condition"
  ) +
  labs(
    title    = "Individual Score Trajectories Across Periods",
    subtitle = "Dashed lines show sequence means",
    x        = "Period",
    y        = "Score"
  ) +
  theme(
    strip.text = element_text(size = 11, face = "bold")
  )

ggsave(file.path(OUTPUT_DIR, "figures", "spaghetti_plot.png"),
       p_spaghetti, width = 10, height = 6, dpi = 300)

ggsave(file.path(OUTPUT_DIR, "figures", "spaghetti_plot.pdf"),
       p_spaghetti, width = 10, height = 6)

# --------------------------------------------------------------------------
# 3. Forest plot of effect sizes
# --------------------------------------------------------------------------

cat("  Generating forest plot...\n")

# Load effect sizes table
es_file <- file.path(OUTPUT_DIR, "tables", "effect_sizes.csv")
if (file.exists(es_file)) {
  es_table <- read_csv(es_file, show_col_types = FALSE)

  p_forest <- ggplot(es_table, aes(x = Estimate, y = reorder(Comparison, Estimate))) +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey50") +
    geom_vline(xintercept = c(-0.2, 0.2), linetype = "dotted", color = "grey70") +
    geom_vline(xintercept = c(-0.5, 0.5), linetype = "dotted", color = "grey80") +
    geom_point(size = 3, color = "#0072B2") +
    geom_errorbarh(aes(xmin = CI_lower, xmax = CI_upper),
                   height = 0.2, linewidth = 0.7, color = "#0072B2") +
    annotate("text", x = 0.2, y = 0.4, label = "small", color = "grey60",
             hjust = 0, size = 3, fontface = "italic") +
    annotate("text", x = 0.5, y = 0.4, label = "medium", color = "grey60",
             hjust = 0, size = 3, fontface = "italic") +
    labs(
      title = "Forest Plot of Effect Sizes (Cohen's d / Hedges' g)",
      subtitle = "Horizontal lines represent 95% confidence intervals",
      x     = "Effect Size",
      y     = NULL
    ) +
    theme(
      axis.text.y  = element_text(size = 10),
      plot.title   = element_text(size = 13),
      panel.grid.major.y = element_line(color = "grey95")
    )

  ggsave(file.path(OUTPUT_DIR, "figures", "forest_plot.png"),
         p_forest, width = 10, height = 5, dpi = 300)

  ggsave(file.path(OUTPUT_DIR, "figures", "forest_plot.pdf"),
         p_forest, width = 10, height = 5)
} else {
  cat("  Effect sizes table not found. Run 06_effect_sizes.R first.\n")
}

# --------------------------------------------------------------------------
# 4. Paired difference plot (Bland-Altman style)
# --------------------------------------------------------------------------

cat("  Generating paired difference plot...\n")

df_wide <- df_wide %>%
  mutate(
    mean_score = (score_AI + score_noAI) / 2,
    diff_score = score_AI - score_noAI
  )

mean_diff <- mean(df_wide$diff_score, na.rm = TRUE)
sd_diff   <- sd(df_wide$diff_score, na.rm = TRUE)

p_bland_altman <- ggplot(df_wide, aes(x = mean_score, y = diff_score)) +
  geom_point(aes(color = sequence), alpha = 0.6, size = 2) +
  geom_hline(yintercept = mean_diff, color = "blue", linewidth = 0.8) +
  geom_hline(yintercept = mean_diff + 1.96 * sd_diff,
             linetype = "dashed", color = "red", linewidth = 0.6) +
  geom_hline(yintercept = mean_diff - 1.96 * sd_diff,
             linetype = "dashed", color = "red", linewidth = 0.6) +
  annotate("text", x = max(df_wide$mean_score, na.rm = TRUE),
           y = mean_diff, label = paste0("Mean = ", round(mean_diff, 2)),
           hjust = 1.1, vjust = -0.5, color = "blue", size = 3.5) +
  scale_color_manual(
    values = c("AB" = "#0072B2", "BA" = "#D55E00"),
    name   = "Sequence"
  ) +
  labs(
    title    = "Bland-Altman Plot: Agreement Between Conditions",
    subtitle = "Blue line = mean difference; red dashed = limits of agreement",
    x        = "Mean of AI and noAI Scores",
    y        = "Difference (AI - noAI)"
  )

ggsave(file.path(OUTPUT_DIR, "figures", "bland_altman_plot.png"),
       p_bland_altman, width = 8, height = 6, dpi = 300)

# --------------------------------------------------------------------------
# 5. Score distribution by condition (violin + boxplot)
# --------------------------------------------------------------------------

cat("  Generating violin plots...\n")

p_violin <- ggplot(df_clean, aes(x = condition, y = score, fill = condition)) +
  geom_violin(alpha = 0.4, trim = FALSE) +
  geom_boxplot(width = 0.2, alpha = 0.8, outlier.shape = NA) +
  geom_jitter(width = 0.05, alpha = 0.2, size = 1) +
  scale_fill_manual(values = c("noAI" = "#E69F00", "AI" = "#009E73")) +
  labs(
    title = "Score Distribution by Condition",
    x     = "Condition",
    y     = "Score (0-100)"
  ) +
  theme(legend.position = "none")

ggsave(file.path(OUTPUT_DIR, "figures", "violin_score_condition.png"),
       p_violin, width = 6, height = 6, dpi = 300)

# --------------------------------------------------------------------------
# 6. Composite figure (for publication)
# --------------------------------------------------------------------------

cat("  Generating composite figure...\n")

p_composite <- (p_interaction | p_spaghetti) /
               (p_violin | p_bland_altman) +
  plot_annotation(
    title   = "Crossover Study Results: AI vs No-AI in Educational Assessment",
    tag_levels = "A",
    theme   = theme(
      plot.title = element_text(face = "bold", size = 16, hjust = 0.5)
    )
  )

ggsave(file.path(OUTPUT_DIR, "figures", "composite_figure.png"),
       p_composite, width = 16, height = 12, dpi = 300)

ggsave(file.path(OUTPUT_DIR, "figures", "composite_figure.pdf"),
       p_composite, width = 16, height = 12)

cat("  All visualizations saved to output/figures/\n")
cat("=== 09_visualizations.R: Complete ===\n\n")
