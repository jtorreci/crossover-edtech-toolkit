# ==============================================================================
# 08_perception_analysis.R
# Purpose: Analyze Likert-scale perception data from post-challenge surveys.
#          - Frequency tables for each item
#          - Diverging stacked bar charts
#          - Comparison of perceptions between AI and noAI conditions
#          - Wilcoxon signed-rank tests for ordinal paired data
# Input:   df_clean.rds
# Output:  Perception tables and plots in output/
# ==============================================================================

cat("=== 08_perception_analysis.R: Analyzing perception data ===\n")

df_clean <- readRDS(file.path(OUTPUT_DIR, "df_clean.rds"))

# --------------------------------------------------------------------------
# 1. Identify and prepare Likert data
# --------------------------------------------------------------------------

likert_cols <- grep("^likert_", names(df_clean), value = TRUE)

if (length(likert_cols) == 0) {
  cat("  No Likert columns found. Skipping perception analysis.\n")
  cat("=== 08_perception_analysis.R: Skipped (no Likert data) ===\n\n")
} else {

  cat(paste0("  Found ", length(likert_cols), " Likert items.\n"))

  # Define Likert labels
  likert_labels <- c(
    "1" = "Strongly Disagree",
    "2" = "Disagree",
    "3" = "Neutral",
    "4" = "Agree",
    "5" = "Strongly Agree"
  )

  # --------------------------------------------------------------------------
  # 2. Frequency tables by condition
  # --------------------------------------------------------------------------

  cat("\n--- Likert frequency tables by condition ---\n")

  freq_tables <- list()
  for (col in likert_cols) {
    freq <- df_clean %>%
      filter(!is.na(.data[[col]])) %>%
      group_by(condition) %>%
      count(.data[[col]]) %>%
      rename(response = 2) %>%
      mutate(
        response = factor(response, levels = 1:5, labels = likert_labels),
        pct      = round(n / sum(n) * 100, 1)
      ) %>%
      ungroup()

    freq_tables[[col]] <- freq
  }

  # Print summary for each item
  for (col in likert_cols) {
    cat(paste0("\n  ", col, ":\n"))
    print(freq_tables[[col]] %>%
            select(condition, response, n, pct) %>%
            pivot_wider(names_from = condition, values_from = c(n, pct)))
  }

  # --------------------------------------------------------------------------
  # 3. Overall Likert summary by condition
  # --------------------------------------------------------------------------

  cat("\n--- Overall Likert means by condition ---\n")

  likert_means <- df_clean %>%
    group_by(condition) %>%
    summarise(
      across(all_of(likert_cols), ~ round(mean(., na.rm = TRUE), 2)),
      .groups = "drop"
    )

  cat("  Mean scores:\n")
  print(likert_means)

  write_csv(likert_means, file.path(OUTPUT_DIR, "tables", "likert_means_by_condition.csv"))

  # --------------------------------------------------------------------------
  # 4. Wilcoxon signed-rank tests for each Likert item
  # --------------------------------------------------------------------------

  cat("\n--- Wilcoxon signed-rank tests (paired, AI vs noAI) ---\n")

  # Reshape to wide format for paired tests
  df_likert_wide <- df_clean %>%
    select(participant_id, condition, all_of(likert_cols)) %>%
    pivot_longer(cols = all_of(likert_cols), names_to = "item", values_to = "response") %>%
    pivot_wider(names_from = condition, values_from = response, names_prefix = "cond_")

  wilcox_results <- tibble(
    item        = character(),
    median_AI   = numeric(),
    median_noAI = numeric(),
    V           = numeric(),
    p_value     = numeric(),
    p_adjusted  = numeric(),
    r_effect    = numeric()
  )

  for (col in likert_cols) {
    item_data <- df_likert_wide %>% filter(item == col) %>% drop_na()

    if (nrow(item_data) >= 10) {
      wt <- wilcox.test(item_data$cond_AI, item_data$cond_noAI, paired = TRUE)

      # Rank-biserial correlation as effect size for Wilcoxon
      n_pairs <- nrow(item_data)
      r_effect <- qnorm(wt$p.value / 2) / sqrt(n_pairs)

      wilcox_results <- wilcox_results %>%
        add_row(
          item        = col,
          median_AI   = median(item_data$cond_AI, na.rm = TRUE),
          median_noAI = median(item_data$cond_noAI, na.rm = TRUE),
          V           = as.numeric(wt$statistic),
          p_value     = wt$p.value,
          p_adjusted  = NA_real_,
          r_effect    = round(abs(r_effect), 3)
        )
    }
  }

  # Adjust p-values for multiple comparisons (Holm method)
  if (nrow(wilcox_results) > 0) {
    wilcox_results$p_adjusted <- p.adjust(wilcox_results$p_value, method = "holm")

    cat("  Results:\n")
    print(wilcox_results)

    write_csv(wilcox_results,
              file.path(OUTPUT_DIR, "tables", "likert_wilcoxon_tests.csv"))
  }

  # --------------------------------------------------------------------------
  # 5. Diverging stacked bar chart (using likert package)
  # --------------------------------------------------------------------------

  cat("\n--- Generating diverging stacked bar charts ---\n")

  # Prepare data for the likert package: separate by condition
  for (cond in levels(df_clean$condition)) {
    cond_data <- df_clean %>%
      filter(condition == cond) %>%
      select(all_of(likert_cols)) %>%
      drop_na() %>%
      mutate(across(everything(), ~ factor(., levels = 1:5, labels = likert_labels)))

    if (nrow(cond_data) >= 5) {
      lik_obj <- likert::likert(as.data.frame(cond_data))

      p_lik <- plot(lik_obj) +
        ggtitle(paste0("Perceptions: ", cond, " condition")) +
        theme(
          plot.title = element_text(face = "bold", hjust = 0.5, size = 14),
          axis.text  = element_text(size = 10)
        )

      ggsave(file.path(OUTPUT_DIR, "figures",
                        paste0("likert_diverging_", tolower(cond), ".png")),
             p_lik, width = 10, height = 6, dpi = 300)
    }
  }

  # --------------------------------------------------------------------------
  # 6. Side-by-side comparison plot (manual diverging bars with ggplot2)
  # --------------------------------------------------------------------------

  # Compute percentages for each response level by condition and item
  likert_pct <- df_clean %>%
    select(condition, all_of(likert_cols)) %>%
    pivot_longer(cols = all_of(likert_cols), names_to = "item", values_to = "response") %>%
    filter(!is.na(response)) %>%
    group_by(condition, item, response) %>%
    summarise(n = n(), .groups = "drop") %>%
    group_by(condition, item) %>%
    mutate(pct = n / sum(n) * 100) %>%
    ungroup() %>%
    mutate(
      response = factor(response, levels = 1:5, labels = likert_labels),
      item     = gsub("likert_", "", item)
    )

  # Color palette for Likert responses
  likert_colors <- c(
    "Strongly Disagree" = "#d73027",
    "Disagree"          = "#fc8d59",
    "Neutral"           = "#ffffbf",
    "Agree"             = "#91bfdb",
    "Strongly Agree"    = "#4575b4"
  )

  p_comparison <- ggplot(likert_pct, aes(x = item, y = pct, fill = response)) +
    geom_bar(stat = "identity", position = "stack") +
    coord_flip() +
    facet_wrap(~ condition) +
    scale_fill_manual(values = likert_colors, name = "Response") +
    labs(
      title = "Perception Comparison: AI vs noAI",
      x     = "Survey Item",
      y     = "Percentage (%)"
    ) +
    theme(
      legend.position = "bottom",
      strip.text      = element_text(face = "bold", size = 12)
    )

  ggsave(file.path(OUTPUT_DIR, "figures", "likert_comparison.png"),
         p_comparison, width = 12, height = 7, dpi = 300)

  cat("  Saved perception plots and tables.\n")
  cat("=== 08_perception_analysis.R: Complete ===\n\n")
}
