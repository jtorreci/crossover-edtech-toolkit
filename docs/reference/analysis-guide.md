---
title: "Analysis Guide"
parent: Reference
nav_order: 2
---

# Analysis Guide: Running the R Pipeline
{: .no_toc }

Complete instructions for executing the 10-script analysis pipeline, from setup through publication-quality visualizations.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

- **R** version 4.2.0 or higher
- **RStudio** (recommended but not required)
- The sample data CSV (or your own data in the same format)

If you have not yet generated the sample data, see [Step 3: Understanding the Sample Data](../tutorial/03-sample-data).
{: .tip }

## Quick start

From the project root directory in R or RStudio:

```r
# Run the entire pipeline
source("analysis/R/run_all.R")
```

This will execute all 10 scripts in sequence and produce outputs in the `output/` directory.

## Step-by-step execution

If you prefer to run scripts individually (recommended for the first time):

### Step 0: Setup

```r
source("analysis/R/00_setup.R")
```

Installs and loads all required packages. Creates the `output/` directory structure. Run this once per R session.

### Step 1: Generate sample data (if needed)

```r
source("sample_data/generate_sample_data.R")
```

Creates `sample_data/crossover_sample_data.csv` with 100 simulated participants. Skip this step if you are using your own data.

### Step 2: Import and clean data

```r
source("analysis/R/01_data_import_clean.R")
```

- Reads the CSV file
- Validates column names and data types
- Checks for missing values and reports them
- Creates derived variables (within-subject differences)
- Flags potential outliers (does not remove them)
- Saves cleaned data as RDS files in `output/`

Check the console output for any warnings about missing data or out-of-range values before proceeding to the next step.
{: .warning }

### Step 3: Descriptive statistics

```r
source("analysis/R/02_descriptive_stats.R")
```

Produces:
- `output/tables/summary_by_condition.csv` -- means, SDs by AI vs noAI
- `output/tables/summary_condition_period.csv` -- the 2x2 cell means
- `output/tables/summary_by_sequence.csv` -- breakdown by AB vs BA
- `output/figures/boxplot_score_by_condition.png`
- `output/figures/boxplot_score_period_condition.png`
- `output/figures/histogram_score_diff.png`

### Step 4: Instrument validation

```r
source("analysis/R/03_instrument_validation.R")
```

Computes:
- Cronbach's alpha for the Likert perception scale
- V de Aiken for content validity (requires `expert_ratings.csv`)
- ICC for inter-rater reliability (requires `rater_scores.csv`)

If expert ratings or rater scores files are not present, the script demonstrates with simulated data. This is expected behavior when running on sample data only.
{: .note }

### Step 5: Paired comparisons

```r
source("analysis/R/04_paired_comparisons.R")
```

The core within-subject analysis:
- Tests normality of score differences (Shapiro-Wilk)
- Paired t-test: AI vs noAI scores
- Wilcoxon signed-rank test (non-parametric alternative)
- Reports confidence intervals and p-values

### Step 6: Mixed ANOVA and linear mixed models

```r
source("analysis/R/05_mixed_anova.R")
```

Fits the full crossover model:
- Mixed ANOVA: condition (within) x sequence (between)
- LMM: `score ~ condition + period + sequence + (1|participant_id)`
- Extended model with interaction term
- Estimated marginal means (emmeans)
- Model comparison via likelihood ratio test

### Step 7: Effect sizes

```r
source("analysis/R/06_effect_sizes.R")
```

Computes:
- Cohen's d (paired) for score and rubric outcomes
- Hedges' g (bias-corrected)
- Partial eta-squared from ANOVA
- Effect sizes broken down by sequence
- All with 95% confidence intervals

### Step 8: Carryover analysis

```r
source("analysis/R/07_carryover_analysis.R")
```

Tests whether receiving the AI tool first affects performance without it later:
- Grizzle's test (compare sum of scores between sequences)
- Uses alpha = 0.10 for the carryover test (standard practice)
- If carryover detected, performs a Period 1 only analysis

A significant carryover result (p < 0.10) means the crossover design assumptions are violated. The script will automatically fall back to a between-groups analysis using only Period 1 data. Review your washout procedure if this occurs.
{: .warning }

### Step 9: Perception analysis

```r
source("analysis/R/08_perception_analysis.R")
```

Analyzes the Likert-scale perception data:
- Frequency tables by condition
- Wilcoxon signed-rank tests per item (with Holm correction)
- Diverging stacked bar charts

### Step 10: Publication visualizations

```r
source("analysis/R/09_visualizations.R")
```

Generates publication-quality figures:
- Interaction plot (classic crossover visualization)
- Spaghetti plot (individual trajectories)
- Forest plot of effect sizes
- Bland-Altman plot
- Violin plots
- Composite multi-panel figure

All figures are saved in both PNG (300 DPI) and PDF formats.

## Using your own data

1. Format your data as a CSV matching the structure in [`sample_data/data_dictionary.md`](../../sample_data/data_dictionary.md).
2. Place it at `sample_data/crossover_sample_data.csv` (or modify `DATA_DIR` in `00_setup.R`).
3. Run the pipeline as described above.
4. If your column names differ, update the `required_cols` vector in `01_data_import_clean.R`.

For detailed column requirements and valid value ranges, see [Step 3: Understanding the Sample Data](../tutorial/03-sample-data#using-your-own-data).
{: .tip }

## Output structure

After running the full pipeline:

```
output/
├── df_clean.rds              # Cleaned long-format data
├── df_wide.rds               # Wide-format data (one row per participant)
├── df_period_sums.rds        # Period sums for carryover test
├── pipeline_log.csv          # Log of all pipeline steps with status
├── tables/
│   ├── summary_by_condition.csv
│   ├── summary_condition_period.csv
│   ├── summary_by_sequence.csv
│   ├── cronbach_item_stats.csv
│   ├── paired_comparisons.csv
│   ├── mixed_anova.csv
│   ├── lmm_fixed_effects.csv
│   ├── emm_by_condition.csv
│   ├── effect_sizes.csv
│   ├── carryover_test.csv
│   ├── likert_means_by_condition.csv
│   └── likert_wilcoxon_tests.csv
├── figures/
│   ├── boxplot_score_by_condition.png
│   ├── interaction_plot.png / .pdf
│   ├── spaghetti_plot.png / .pdf
│   ├── forest_plot.png / .pdf
│   ├── composite_figure.png / .pdf
│   └── ...
└── models/
    ├── lmm_main.rds
    └── lmm_interaction.rds
```

## Running tests

```r
source("tests/test_analysis_pipeline.R")
```

This runs the full pipeline on sample data and checks that outputs are correct. Use it to verify your installation before working with real data.
