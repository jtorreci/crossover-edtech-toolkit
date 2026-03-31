---
title: "Step 4: Running the Analysis Pipeline"
parent: Tutorial
nav_order: 4
---

# Step 4: Running the Analysis Pipeline
{: .no_toc }

Learn how to execute the 10 analysis scripts, what each one does, what output it produces, and how to re-run individual steps.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The analysis pipeline consists of **10 modular scripts** numbered `00` through `09`. Each script performs one well-defined analysis step, reads its inputs from `output/`, writes its results back to `output/`, and prints a summary to the console.

You can execute all 10 scripts in sequence with a single command, or run any individual script on its own. Because each script saves its intermediate results to disk, you can re-run a single step without repeating earlier ones.

The R and Python pipelines produce identical results. Choose whichever language you prefer -- you do not need to run both.
{: .note }

## Running the full pipeline at once

The simplest way to execute all 10 steps is to use the runner script.

**R** (from the project root):
```r
source("analysis/R/run_all.R")
```

**Python** (from the project root):
```bash
python analysis/python/run_all.py
```

Both runners execute scripts `00` through `09` in order, capture timing information, handle errors gracefully, and print a summary at the end:

```
================================================================
  crossover-edtech-toolkit: Full Analysis Pipeline
  Started: 2026-03-15 10:42:07
================================================================

>>> Running: 00_setup.R
>>> 00_setup.R completed in 3.21 seconds.

>>> Running: 01_data_import_clean.R
>>> 01_data_import_clean.R completed in 0.45 seconds.

...

================================================================
  Pipeline Summary
================================================================

  Total scripts:   10
  Successful:      10
  Errors:          0
  Total duration:  28.37 seconds

  Step-by-step results:
  ----------------------------------------------------------------------
  [OK] 00_setup.R                             3.21s
  [OK] 01_data_import_clean.R                 0.45s
  [OK] 02_descriptive_stats.R                 1.83s
  [OK] 03_instrument_validation.R             0.92s
  [OK] 04_paired_comparisons.R                0.67s
  [OK] 05_mixed_anova.R                       4.15s
  [OK] 06_effect_sizes.R                      0.58s
  [OK] 07_carryover_analysis.R                0.73s
  [OK] 08_perception_analysis.R               2.41s
  [OK] 09_visualizations.R                   13.42s
  ----------------------------------------------------------------------

  Pipeline log saved to: output/pipeline_log.csv
  All scripts completed successfully.
  Output files are in: output/
================================================================
```

If any script fails, the runner marks it with `[!!]`, prints the error message, and continues with the next script. Check `output/pipeline_log.csv` for a machine-readable record of each run.
{: .tip }

## Running individual scripts

Every script can be run independently. This is useful when you want to tweak one analysis step without re-running the entire pipeline.

**R** -- source the setup script first (it loads packages and sets paths), then source the target script:
```r
source("analysis/R/00_setup.R")
source("analysis/R/04_paired_comparisons.R")
```

**Python** -- run the script directly:
```bash
python analysis/python/04_paired_comparisons.py
```

Scripts `01`--`09` depend on the output of earlier scripts (e.g., the cleaned data file `df_clean.rds` created by script `01`). As long as those intermediate files exist in `output/`, you can re-run any later script in isolation.
{: .note }

---

## Script-by-script reference

### 00 -- Setup

**What it does:** Installs any missing R packages (or verifies Python dependencies), sets global options (random seed, ggplot theme), and creates the output directory structure (`output/tables/`, `output/figures/`, `output/models/`).

**Key output files:**
- `output/tables/` (directory created)
- `output/figures/` (directory created)
- `output/models/` (directory created)

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
```
```bash
# Python
python analysis/python/00_setup.py
```

**What to look for:** Confirmation that all packages loaded successfully and that the project root was detected correctly.

```
=== 00_setup.R: Installing and loading packages ===
  Project root: /home/user/crossover-edtech-toolkit
  Data dir:     /home/user/crossover-edtech-toolkit/sample_data
  Output dir:   /home/user/crossover-edtech-toolkit/output
=== 00_setup.R: Complete ===
```

If a package fails to install, install it manually (`install.packages("lme4")` in R, or `pip install statsmodels` in Python) and re-run.
{: .warning }

---

### 01 -- Data Import and Cleaning

**What it does:** Reads the CSV file from `sample_data/`, validates the column structure, sets factor types and levels, checks for missing data and out-of-range values, creates derived variables (within-subject differences, period sums for the carryover test), flags potential outliers using the IQR method, and saves the cleaned data in several formats.

**Key output files:**
- `output/df_clean.rds` -- cleaned long-format data (R) or equivalent pickle (Python)
- `output/df_wide.rds` -- wide format with one row per participant, including `score_AI`, `score_noAI`, and `score_diff`
- `output/df_period_sums.rds` -- participant-level sum of scores across periods (used for carryover test)

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/01_data_import_clean.R")
```
```bash
# Python
python analysis/python/01_data_import_clean.py
```

**What to look for:** Row count (should be 200 for 100 participants), number of Likert columns detected (6), and the sequence balance table:

```
  Loaded 200 rows and 14 columns.
  All required columns present.
  No missing data found.
  Found 6 Likert columns.
  Created wide-format data with 100 participants.
  Flagged 3 potential outliers (IQR method).
  Sequence balance:
    sequence  n
    AB       50
    BA       50
```

Outliers are flagged but not removed. Review them before deciding whether exclusion is appropriate for your study.
{: .tip }

---

### 02 -- Descriptive Statistics

**What it does:** Computes summary statistics (mean, SD, median, min, max) for score, rubric score, and time spent, broken down by condition, by condition x period, and by sequence x period x condition. Generates basic distribution plots.

**Key output files:**
- `output/tables/summary_by_condition.csv` -- means and SDs by AI vs noAI
- `output/tables/summary_condition_period.csv` -- the 2x2 cell means
- `output/tables/summary_by_sequence.csv` -- means by sequence x period x condition
- `output/figures/boxplot_score_by_condition.png`
- `output/figures/boxplot_score_period_condition.png`
- `output/figures/histogram_score_diff.png`
- `output/figures/boxplot_time_by_condition.png`

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/02_descriptive_stats.R")
```
```bash
# Python
python analysis/python/02_descriptive_stats.py
```

**What to look for:** The condition means and the direction of the treatment effect. With the sample data you should see:

```
  Summary by condition:
    condition   n  mean_score  sd_score
    noAI      100    66.21     13.18
    AI        100    71.30     12.45
```

The AI condition should score higher than noAI. The 2x2 table of condition x period means is essential for interpreting the interaction plot later.

---

### 03 -- Instrument Validation

**What it does:** Validates the data collection instruments. Computes Cronbach's alpha for internal consistency of the 6 Likert items, item-total correlations, and alpha-if-item-dropped. Also computes V de Aiken for content validity (if expert ratings are provided) and ICC for inter-rater reliability of rubric scores (if multi-rater data is provided).

**Key output files:**
- `output/tables/cronbach_item_stats.csv` -- item-level reliability statistics
- `output/tables/cronbach_alpha_if_dropped.csv` -- what alpha would be if each item were removed
- `output/tables/v_aiken_simulated.csv` (or `v_aiken_results.csv` if expert data is available)

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/03_instrument_validation.R")
```
```bash
# Python
python analysis/python/03_instrument_validation.py
```

**What to look for:** The overall Cronbach's alpha value. For the sample data, expect alpha around 0.758, which indicates acceptable internal consistency:

```
  Raw alpha:         0.758
  Standardized alpha: 0.761
```

If alpha is below 0.70 in your data, check which item(s) have low item-total correlations and consider removing them. The alpha-if-item-dropped table will tell you whether removing a specific item would improve reliability.
{: .tip }

---

### 04 -- Paired Comparisons

**What it does:** Performs within-subject paired comparisons of AI vs noAI scores. Tests normality of the within-subject differences (Shapiro-Wilk), runs a paired t-test (parametric) and a Wilcoxon signed-rank test (non-parametric), and repeats the analysis separately for each sequence group as a sensitivity check.

**Key output files:**
- `output/tables/paired_comparisons.csv` -- test statistics, CIs, and p-values
- `output/figures/qq_score_diff.png` -- Q-Q plot of within-subject differences

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/04_paired_comparisons.R")
```
```bash
# Python
python analysis/python/04_paired_comparisons.py
```

**What to look for:** The mean difference, confidence interval, and p-value for the paired t-test:

```
--- Paired t-test: Score (AI vs noAI) ---
  Mean difference (AI - noAI): 5.19
  95% CI: [2.78, 7.60]
  t(99) = 4.27
  p-value = 0.0000
```

Both the parametric and non-parametric tests should agree on the direction and significance. If the Shapiro-Wilk test rejects normality, rely on the Wilcoxon result as the primary test.
{: .note }

---

### 05 -- Mixed ANOVA and Linear Mixed Models

**What it does:** Fits a mixed ANOVA (treatment as within-subject factor, sequence as between-subject factor) and a linear mixed-effects model (LMM) as a robustness check. Tests assumptions (normality of residuals, homogeneity of variances, extreme outliers). Computes estimated marginal means (EMMs) and pairwise contrasts. Also fits an extended model with a treatment x period interaction to assess carryover via a different approach.

**Key output files:**
- `output/tables/mixed_anova.csv` -- ANOVA table with F-statistics, p-values, and generalized eta-squared
- `output/tables/lmm_fixed_effects.csv` -- fixed-effect estimates and CIs from the LMM
- `output/tables/emm_by_condition.csv` -- estimated marginal means
- `output/tables/posthoc_comparisons.csv` -- pairwise post-hoc results by sequence
- `output/models/lmm_main.rds` -- saved LMM model object (R only)
- `output/models/lmm_interaction.rds` -- saved interaction model (R only)

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/05_mixed_anova.R")
```
```bash
# Python
python analysis/python/05_mixed_anova.py
```

**What to look for:** The condition effect should be significant. The LMM output with the sample data shows:

```
  Fixed effects with 95% CI:
    term            estimate  CI_lower  CI_upper
    (Intercept)     63.517    59.843    67.191
    conditionAI      5.190     2.780     7.600
    period_num       2.095     0.108     4.082
    sequenceBA       1.203    -3.661     6.067
```

The `conditionAI` estimate is the treatment effect (positive means AI improves scores). Check that the confidence interval does not include zero. The `sequenceBA` term tests whether the two sequence groups differ overall; a non-significant result is expected and desirable.

---

### 06 -- Effect Sizes

**What it does:** Computes Cohen's d (paired) and Hedges' g (bias-corrected) for the overall AI vs noAI comparison, plus Cohen's d broken down by sequence. Extracts generalized eta-squared from the ANOVA. Provides interpretation labels (negligible, small, medium, large) and 95% confidence intervals for every effect size.

**Key output files:**
- `output/tables/effect_sizes.csv` -- all effect size estimates with CIs and interpretation

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/06_effect_sizes.R")
```
```bash
# Python
python analysis/python/06_effect_sizes.py
```

**What to look for:** The overall Cohen's d and the sequence-specific values:

```
  Score (AI vs noAI):
    Cohen's d = 0.43  [95% CI: 0.15, 0.71]

  Sequence AB:
    Cohen's d = 0.58  [95% CI: 0.17, 0.99]

  Sequence BA:
    Cohen's d = 0.26  [95% CI: -0.14, 0.66]
```

A Cohen's d of 0.43 falls in the small-to-medium range. Note that sequence AB (noAI first, then AI) typically shows a stronger effect than sequence BA; this is normal and does not necessarily indicate carryover.
{: .tip }

---

### 07 -- Carryover Analysis

**What it does:** Tests for carryover effects using Grizzle's test: it compares the sum of each participant's scores across both periods between the AB and BA sequence groups. If the sums differ significantly (at alpha = 0.10), carryover is present and the analysis should be restricted to Period 1 data only. Also runs a non-parametric alternative (Wilcoxon rank-sum) and a period effect test.

**Key output files:**
- `output/tables/carryover_test.csv` -- Grizzle and Wilcoxon test statistics
- `output/figures/carryover_test.png` -- boxplot of score sums by sequence

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/07_carryover_analysis.R")
```
```bash
# Python
python analysis/python/07_carryover_analysis.py
```

**What to look for:** The Grizzle test p-value. For the sample data:

```
--- Grizzle's carryover test ---
  Sequence AB: mean sum = 135.22 (SD = 23.41, n = 50)
  Sequence BA: mean sum = 139.58 (SD = 24.87, n = 50)
  Difference: -4.36
  t(97.2) = -0.94
  p-value = 0.14

  No significant carryover effect (p >= 0.10).
  The standard crossover analysis is valid.
```

A p-value above 0.10 means no significant carryover was detected. This is the result you want. If you see p < 0.10, the script will automatically run a Period 1 only analysis as a fallback.
{: .warning }

---

### 08 -- Perception Analysis

**What it does:** Analyzes the 6 Likert-scale perception items. Computes frequency tables and means by condition, runs paired Wilcoxon signed-rank tests for each item (with Holm correction for multiple comparisons), and generates diverging stacked bar charts and a side-by-side comparison plot.

**Key output files:**
- `output/tables/likert_means_by_condition.csv` -- mean Likert score per item by condition
- `output/tables/likert_wilcoxon_tests.csv` -- Wilcoxon test results with adjusted p-values
- `output/figures/likert_comparison.png` -- stacked bar chart comparing AI vs noAI perceptions
- `output/figures/likert_diverging_ai.png` -- diverging bar chart for the AI condition
- `output/figures/likert_diverging_noai.png` -- diverging bar chart for the noAI condition

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/08_perception_analysis.R")
```
```bash
# Python
python analysis/python/08_perception_analysis.py
```

**What to look for:** Which Likert items show significant differences between conditions. In the sample data, `likert_satisfaction` is the most differentiated item:

```
  item                 median_AI  median_noAI  V       p_value   p_adjusted  r_effect
  likert_usefulness    4          3            3012    0.023     0.115       0.228
  likert_ease          3          3            2845    0.089     0.267       0.170
  likert_confidence    4          3            2901    0.054     0.216       0.193
  likert_engagement    3          3            2756    0.182     0.364       0.134
  likert_satisfaction  4          3            3198    0.001     0.006       0.325
  likert_learning      3          3            2812    0.112     0.267       0.159
```

After Holm correction for 6 comparisons, only `likert_satisfaction` remains significant (p = 0.006). The others are marginal at best.

---

### 09 -- Visualizations

**What it does:** Generates publication-quality figures: the crossover interaction plot, individual trajectory (spaghetti) plots, a forest plot of effect sizes, a Bland-Altman agreement plot, violin plots of score distributions, and a four-panel composite figure suitable for inclusion in a journal article.

**Key output files:**
- `output/figures/interaction_plot.png` (and `.pdf`)
- `output/figures/spaghetti_plot.png` (and `.pdf`)
- `output/figures/forest_plot.png` (and `.pdf`)
- `output/figures/bland_altman_plot.png`
- `output/figures/violin_score_condition.png`
- `output/figures/composite_figure.png` (and `.pdf`)

**Run individually:**
```r
# R
source("analysis/R/00_setup.R")
source("analysis/R/09_visualizations.R")
```
```bash
# Python
python analysis/python/09_visualizations.py
```

**What to look for:** Open the PNG files in `output/figures/` and verify that the plots look correct. The interaction plot should show two crossing or converging lines representing the two sequences, the forest plot should show effect sizes with CIs, and the composite figure should combine four panels labeled A through D.

All figures are saved in both PNG (for web and presentations) and PDF (for journal submission) formats. The composite figure is designed at 16 x 12 inches / 300 DPI, which meets the requirements of most journals.
{: .tip }

---

## Output directory structure

After a successful pipeline run, the `output/` directory will contain:

```
output/
├── tables/
│   ├── summary_by_condition.csv
│   ├── summary_condition_period.csv
│   ├── summary_by_sequence.csv
│   ├── cronbach_item_stats.csv
│   ├── cronbach_alpha_if_dropped.csv
│   ├── v_aiken_simulated.csv
│   ├── paired_comparisons.csv
│   ├── mixed_anova.csv
│   ├── lmm_fixed_effects.csv
│   ├── emm_by_condition.csv
│   ├── posthoc_comparisons.csv
│   ├── effect_sizes.csv
│   ├── carryover_test.csv
│   ├── likert_means_by_condition.csv
│   └── likert_wilcoxon_tests.csv
├── figures/
│   ├── boxplot_score_by_condition.png
│   ├── boxplot_score_period_condition.png
│   ├── boxplot_time_by_condition.png
│   ├── histogram_score_diff.png
│   ├── qq_score_diff.png
│   ├── interaction_plot.png / .pdf
│   ├── spaghetti_plot.png / .pdf
│   ├── forest_plot.png / .pdf
│   ├── bland_altman_plot.png
│   ├── violin_score_condition.png
│   ├── carryover_test.png
│   ├── likert_comparison.png
│   ├── likert_diverging_ai.png
│   ├── likert_diverging_noai.png
│   └── composite_figure.png / .pdf
├── models/
│   ├── lmm_main.rds
│   └── lmm_interaction.rds
├── df_clean.rds
├── df_wide.rds
├── df_period_sums.rds
└── pipeline_log.csv
```

## Troubleshooting

| Problem | Solution |
|:--------|:---------|
| `Data file not found` | Run `source("sample_data/generate_sample_data.R")` or `python sample_data/generate_sample_data.py` first |
| `Missing required columns` | Your CSV does not match the expected format. See the [data dictionary](../../sample_data/data_dictionary.md) |
| A single script fails | Check the error message. You can fix the issue and re-run just that script without restarting the full pipeline |
| R package fails to install | Try `install.packages("package_name")` manually in an R console, then re-run `00_setup.R` |
| Python import error | Run `pip install -r analysis/python/requirements.txt` to install all dependencies |
| Plots look blank or malformed | Ensure you have a working graphics device. On headless servers, the pipeline saves to files without requiring a display |

## Next step

Now that you have run the pipeline and generated all the output, proceed to **Step 5** to learn how to interpret every result.

---

**Next:** [Step 5: Interpreting Your Results](05-results)
