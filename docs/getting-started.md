---
title: Getting Started
layout: default
nav_order: 2
---

# Getting Started
{: .no_toc }

Run the full analysis pipeline on sample data in under 5 minutes.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

You need **one** of the following:

| Language | Version | Check command |
|:---------|:--------|:-------------|
| **R** | 4.2.0 or higher | `R --version` |
| **Python** | 3.9 or higher | `python --version` |

Both pipelines produce identical results. Choose whichever you're more comfortable with.

## 1. Clone the repository

```bash
git clone https://github.com/jtorreci/crossover-edtech-toolkit.git
cd crossover-edtech-toolkit
```

## 2. Generate sample data

The repo includes a data generator that creates a realistic synthetic dataset (100 participants, 2 periods, crossover design):

**R:**
```r
source("sample_data/generate_sample_data.R")
```

**Python:**
```bash
python sample_data/generate_sample_data.py
```

This creates `sample_data/crossover_sample_data.csv` with 200 rows (100 participants x 2 periods).

If you want a stronger workflow check, the repo also includes a **scenario-based validation suite** that generates several synthetic classroom populations and runs the full pipeline on each one:

```bash
python sample_data/generate_scenario_validation.py
```

That workflow is intended to test whether the toolkit correctly distinguishes treatment effects, period effects, carryover, and high heterogeneity under known conditions. It is documented in [Synthetic Validation](reference/synthetic-validation).

## 3. Run the full pipeline

**R** (from the project root):
```r
source("analysis/R/run_all.R")
```

**Python** (from the project root):
```bash
pip install -r analysis/python/requirements.txt
python analysis/python/run_all.py
```

Both will execute 10 analysis steps and report results:

```
  Pipeline Summary
  Total scripts:   10
  Successful:      10
  Errors:          0
  Total duration:  ~15-45 seconds
```

## 4. Check the output

Results are organized in `output/`:

```
output/
├── tables/          # 14+ CSV summary tables
│   ├── summary_by_condition.csv
│   ├── paired_comparisons.csv
│   ├── mixed_anova.csv
│   ├── effect_sizes.csv
│   └── ...
├── figures/         # 17+ publication-quality plots (PNG + PDF)
│   ├── interaction_plot.png
│   ├── forest_plot.png
│   ├── spaghetti_plot.png
│   └── ...
├── models/          # Fitted model objects (R only: .rds)
└── pipeline_log.csv # Execution log with timing
```

## 5. Explore interactively (Python)

For an interactive walkthrough with explanations and inline plots:

```bash
jupyter notebook analysis/python/full_analysis.ipynb
```

## What's next?

- Follow the [full tutorial](tutorial/) for a detailed explanation of each step
- Read the [study design guide](reference/study-design) to understand the crossover methodology
- Check the [instrument adaptation guide](reference/instruments) to customize for your discipline
