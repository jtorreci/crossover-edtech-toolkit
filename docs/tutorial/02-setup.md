---
title: "Step 2: Setting Up Your Environment"
parent: Tutorial
nav_order: 2
---

# Step 2: Setting Up Your Environment
{: .no_toc }

Install the required software, clone the repository, and verify that everything is ready to run the analysis pipeline.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

You need **one** of the following (not both):

| Language | Minimum version | Download | Check command |
|:---------|:---------------|:---------|:-------------|
| **R** | 4.2.0+ | [r-project.org](https://cran.r-project.org/) | `R --version` |
| **Python** | 3.9+ | [python.org](https://www.python.org/downloads/) | `python --version` |

Both pipelines produce **identical statistical results**. Choose whichever language you are more comfortable with. If you are new to both, Python may have a gentler setup experience; if you are already an R user, the R pipeline will feel familiar.
{: .tip }

## Clone the repository

Open a terminal and run:

```bash
git clone https://github.com/jtorreci/crossover-edtech-toolkit.git
cd crossover-edtech-toolkit
```

This will create a local copy of the entire toolkit, including analysis scripts, instruments, sample data, and documentation.

## R setup

### Install packages with `00_setup.R`

The R pipeline uses 16 packages. Rather than installing them manually, the setup script handles everything automatically:

```r
source("analysis/R/00_setup.R")
```

This script checks whether each package is already installed and only downloads what is missing. The full list of required packages:

| Package | Purpose |
|:--------|:--------|
| `tidyverse` | Data wrangling (dplyr, tidyr, readr, purrr, ggplot2, etc.) |
| `lme4` | Linear mixed-effects models |
| `lmerTest` | p-values for lmer via Satterthwaite approximation |
| `emmeans` | Estimated marginal means and pairwise comparisons |
| `effectsize` | Cohen's d, eta-squared, and other effect sizes |
| `psych` | Cronbach's alpha, descriptive statistics |
| `irr` | Inter-rater reliability (ICC, kappa) |
| `likert` | Likert-scale analysis and visualization |
| `ggplot2` | Grammar of graphics (also loaded via tidyverse) |
| `car` | Levene's test, Type III SS ANOVA |
| `rstatix` | Pipe-friendly statistical tests |
| `knitr` | Table formatting |
| `kableExtra` | Enhanced table formatting |
| `scales` | Axis formatting for plots |
| `patchwork` | Combine multiple ggplots into composite figures |
| `RColorBrewer` | Color-blind-friendly palettes |

On some Windows machines, R may not have write permission to the system library. If you see a message asking whether to create a personal library, type **yes**. The packages will be installed in your user library (typically `C:\Users\<you>\AppData\Local\R\win-library\`) and will work just the same.
{: .note }

### Verify the R setup

After running `00_setup.R`, you should see output similar to:

```
=== 00_setup.R: Installing and loading packages ===
  Project root: /path/to/crossover-edtech-toolkit
  Data dir:     /path/to/crossover-edtech-toolkit/sample_data
  Output dir:   /path/to/crossover-edtech-toolkit/output
=== 00_setup.R: Complete ===
```

If any package fails to install, the script will stop with an error message indicating which package could not be loaded. The most common fix is to update R to version 4.2 or later.

## Python setup

### Install packages with `requirements.txt`

From the project root, run:

```bash
pip install -r analysis/python/requirements.txt
```

We recommend using a virtual environment to avoid conflicts with other projects:

```bash
python -m venv .venv
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

pip install -r analysis/python/requirements.txt
```
{: .tip }

The key Python dependencies are:

| Package | Purpose |
|:--------|:--------|
| `pandas` | DataFrames and data manipulation |
| `numpy` | Numerical computing |
| `scipy` | Statistical tests (t-tests, Wilcoxon, Shapiro-Wilk) |
| `statsmodels` | Mixed-effects models, ANOVA |
| `pingouin` | Paired tests, effect sizes, mixed ANOVA |
| `scikit-learn` | Preprocessing utilities |
| `matplotlib` | Publication-quality plotting |
| `seaborn` | Statistical visualization |
| `factor_analyzer` | Exploratory factor analysis for instrument validation |
| `krippendorff` | Inter-rater reliability (Krippendorff's alpha) |
| `openpyxl` | Excel file export |
| `jupyter` | Interactive notebook environment |

### Verify the Python setup

Run the setup script to confirm all packages are importable:

```bash
python analysis/python/00_setup.py
```

You should see each package listed with its version number:

```
=== 00_setup.py: Checking environment and loading packages ===
  Python version: 3.11.5 (...)
  pandas                    2.1.0
  numpy                     1.25.2
  scipy                     1.11.2
  statsmodels               0.14.0
  pingouin                  0.5.3
  scikit-learn              1.3.0
  matplotlib                3.7.2
  seaborn                   0.12.2
  factor_analyzer           0.5.0
  krippendorff              0.6.1
  openpyxl                  3.1.2
  Project root: /path/to/crossover-edtech-toolkit
  Data dir:     /path/to/crossover-edtech-toolkit/sample_data
  Output dir:   /path/to/crossover-edtech-toolkit/output
=== 00_setup.py: Complete ===
```

If any package shows `*** NOT INSTALLED ***`, re-run `pip install -r analysis/python/requirements.txt` and check for error messages.

## Directory structure overview

After cloning, the repository has the following layout:

```
crossover-edtech-toolkit/
├── analysis/
│   ├── R/                  # 10 R scripts (00_setup through 09_visualizations)
│   │   ├── 00_setup.R
│   │   ├── 01_data_import_clean.R
│   │   ├── ...
│   │   ├── 09_visualizations.R
│   │   └── run_all.R       # Master script that runs the full pipeline
│   └── python/             # 10 Python scripts (mirrors the R pipeline)
│       ├── 00_setup.py
│       ├── 01_data_import_clean.py
│       ├── ...
│       ├── 09_visualizations.py
│       ├── run_all.py      # Master script that runs the full pipeline
│       ├── full_analysis.ipynb  # Interactive Jupyter notebook
│       └── requirements.txt
├── sample_data/            # Synthetic dataset generator and CSV output
├── instruments/            # Questionnaires, rubrics, and survey templates
├── output/                 # Generated by the pipeline
│   ├── tables/             # CSV summary tables (14+)
│   ├── figures/            # PNG and PDF plots (17+)
│   └── models/             # Fitted model objects (.rds for R)
├── docs/                   # This documentation site (Jekyll + just-the-docs)
├── paper/                  # Manuscript source files
├── tests/                  # Unit and integration tests
├── CITATION.cff            # Machine-readable citation metadata
├── CONTRIBUTING.md         # Guidelines for contributors
├── LICENSE                 # MIT License
└── README.md               # Project overview
```

The `analysis/R/` and `analysis/python/` directories are **mirror images** of each other. Each numbered script performs the same analysis step, produces the same output tables and figures, and follows the same naming conventions. You only need to use one pipeline.
{: .note }

## A note on reproducibility

Both pipelines set a random seed (`2026`) during setup. This ensures that any stochastic operations (e.g., bootstrap confidence intervals) produce the same results every time. If you need to change the seed for your own study, modify the `set.seed(2026)` line in `00_setup.R` or the `RANDOM_SEED = 2026` constant in `00_setup.py`.

## Summary

At this point you should have:

- [ ] R 4.2+ or Python 3.9+ installed and working
- [ ] The repository cloned locally
- [ ] All dependencies installed (verified by running `00_setup`)
- [ ] A basic understanding of the directory layout

In the next step, you will explore the sample dataset and understand what each variable represents.

---

**Previous:** [Step 1: Understanding the Crossover Design](01-study-design) | **Next:** Step 3: Exploring the Sample Data *(coming soon)*
