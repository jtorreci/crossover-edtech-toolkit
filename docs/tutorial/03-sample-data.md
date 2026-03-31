---
title: "Step 3: Understanding the Sample Data"
parent: Tutorial
nav_order: 3
---

# Step 3: Understanding the Sample Data
{: .no_toc }

Learn how the synthetic dataset is generated, what each variable represents, and how to substitute your own data.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Generating the sample data

The toolkit ships with a data generator that produces a realistic synthetic dataset for a 2x2 crossover experiment. You can run it in either R or Python:

**R:**
```r
source("sample_data/generate_sample_data.R")
```

**Python:**
```bash
python sample_data/generate_sample_data.py
```

Both scripts produce the same file: `sample_data/crossover_sample_data.csv`.

The generator is deterministic (it sets a random seed), so you will get identical output each time you run it. If you want different random draws, change the seed value at the top of the script.
{: .tip }

## What gets generated

The output CSV contains **200 rows**: one row for each participant-period combination (100 participants x 2 periods). Participants are balanced across two sequences:

| Sequence | Group label | N | Period 1 | Period 2 |
|:---------|:------------|:--|:---------|:---------|
| AB | A | 50 | noAI | AI |
| BA | B | 50 | AI | noAI |

This balanced allocation ensures equal statistical power for detecting treatment, period, and carryover effects.

## Data structure

Every row in the CSV contains the following columns:

| Column | Type | Range | Description |
|:-------|:-----|:------|:------------|
| `participant_id` | String | P001--P100 | Unique anonymous identifier for each participant |
| `group` | String | A, B | Randomization group (A = sequence AB, B = sequence BA) |
| `sequence` | String | AB, BA | The order in which treatments are received |
| `period` | Integer | 1, 2 | Time period (1 = first session, 2 = second session) |
| `condition` | String | AI, noAI | Experimental condition for this observation |
| `score` | Numeric | 0--100 | Primary outcome: task performance score |
| `rubric_score` | Numeric | 0--10 | Secondary outcome: rubric-based evaluation of the deliverable |
| `time_spent` | Numeric | minutes | Time the participant spent on the challenge task |
| `likert_usefulness` | Integer | 1--5 | "The tool/approach was useful for solving the task" |
| `likert_ease` | Integer | 1--5 | "The task was easy to complete under this condition" |
| `likert_confidence` | Integer | 1--5 | "I felt confident in the quality of my solution" |
| `likert_engagement` | Integer | 1--5 | "I felt engaged while working on the task" |
| `likert_learning` | Integer | 1--5 | "I feel I learned something from this activity" |

The five Likert items form a short perception scale. The analysis pipeline computes Cronbach's alpha to verify internal consistency.
{: .note }

## Design parameters in the generator

The data generator uses the following parameters to simulate realistic crossover data. These correspond directly to the terms in the statistical model described in the [study design reference](../reference/study-design):

| Parameter | Symbol | Value | Meaning |
|:----------|:-------|:------|:--------|
| Grand mean | mu | 65 | Average score under control conditions |
| Treatment effect | tau | 5 | Expected boost from the AI condition |
| Period effect | pi | 3 | Expected improvement from Period 1 to Period 2 (practice/familiarity) |
| Carryover effect | lambda | 0 | No carryover by default (skills from AI do not persist into the noAI period) |
| Subject SD | sigma_subj | 12 | Between-subject standard deviation (individual differences) |
| Residual SD | sigma_resid | 8 | Within-subject residual standard deviation |

Setting `lambda = 0` means the generator produces data with no carryover effect, which is the ideal scenario for a crossover trial. If you want to explore what happens when carryover is present, change `lambda` to a non-zero value (e.g., 3 or 5) and re-run the generator. The carryover analysis script (`07_carryover_analysis.R`) should then detect it.
{: .tip }

## Missing data

The generator introduces approximately **3% missing values** across the dataset. This simulates real-world conditions where participants may skip a Likert item, leave a session early, or have a score that could not be recorded. Missing values are coded as `NA` in R and as empty cells in the CSV.

The analysis pipeline handles missing data gracefully:
- Descriptive statistics use pairwise complete observations.
- Paired comparisons require both periods to be present for a participant; incomplete cases are flagged and excluded with a warning.
- The linear mixed model uses all available data via maximum likelihood estimation.

## Quick sanity checks

After generating the data, verify that it looks reasonable before proceeding to the analysis:

**R:**
```r
df <- read.csv("sample_data/crossover_sample_data.csv")

# Check dimensions
nrow(df)   # Should be ~200 (minus any fully missing rows)
length(unique(df$participant_id))  # Should be 100

# Check balance
table(df$sequence, df$period)  # Should be ~50 in each cell

# Check treatment effect direction
aggregate(score ~ condition, data = df, FUN = mean, na.rm = TRUE)
# AI mean should be roughly 5 points higher than noAI
```

**Python:**
```python
import pandas as pd

df = pd.read_csv("sample_data/crossover_sample_data.csv")

print(df.shape)                          # (200, 13)
print(df["participant_id"].nunique())    # 100
print(df.groupby("sequence")["period"].value_counts())
print(df.groupby("condition")["score"].mean())
# AI mean should be roughly 5 points higher than noAI
```

Because the data is randomly generated, the observed treatment difference will not be exactly 5. With these sample sizes, expect it to fall somewhere in the range of 3--7.
{: .note }

## Using your own data

When you are ready to move beyond the sample data and use your own experimental results, follow these steps:

1. **Format your CSV** to match the column structure described above. At a minimum, you need: `participant_id`, `group`, `sequence`, `period`, `condition`, and at least one outcome variable (`score`).
2. **Save the file** as `sample_data/crossover_sample_data.csv`, or update the `DATA_DIR` variable in `analysis/R/00_setup.R` (or `analysis/python/config.py`) to point to your file.
3. **Run the pipeline** as described in [Step 4](04-run-pipeline).

If your column names differ from the expected names, update the `required_cols` vector in `01_data_import_clean.R` (or the equivalent in the Python pipeline).
{: .warning }

### Column requirements for custom data

| Requirement | Details |
|:------------|:--------|
| File format | CSV with headers in the first row |
| Encoding | UTF-8 recommended |
| Required columns | `participant_id`, `group`, `sequence`, `period`, `condition`, `score` |
| Optional columns | `rubric_score`, `time_spent`, `likert_usefulness`, `likert_ease`, `likert_confidence`, `likert_engagement`, `likert_learning` |
| Missing values | Use `NA` or leave cells empty; do not use sentinel values like -1 or 999 |
| Rows per participant | Exactly 2 (one per period) for a standard 2x2 crossover |

For the full column specification, including valid value ranges and data types, see the [data dictionary](../../sample_data/data_dictionary.md).

## Next step

Proceed to **[Step 4: Running the Analysis Pipeline](04-run-pipeline)** to execute the full statistical analysis on this dataset.
