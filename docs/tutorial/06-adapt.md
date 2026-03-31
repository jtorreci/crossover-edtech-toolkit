---
title: "Step 6: Adapting to Your Study"
parent: Tutorial
nav_order: 6
---

# Step 6: Adapting to Your Study
{: .no_toc }

Learn how to replace the sample data with your own, customize instruments for your discipline, plan your sample size, and prepare your results for publication.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 1. Replacing sample data with your own

Once you have collected data from your crossover experiment, replacing the sample data is straightforward.

### Required CSV format

Prepare a CSV file with the following columns. Column names must match exactly (case-sensitive):

| Column | Type | Required? | Valid values |
|:-------|:-----|:----------|:-------------|
| `participant_id` | String | Yes | Unique identifier per participant (e.g., P001, S042) |
| `group` | String | Yes | `A` or `B` |
| `sequence` | String | Yes | `AB` or `BA` |
| `period` | Integer | Yes | `1` or `2` |
| `condition` | String | Yes | `AI` or `noAI` |
| `score` | Numeric | Yes | 0--100 (primary outcome) |
| `rubric_score` | Numeric | No | 0--10 |
| `time_spent` | Numeric | No | Minutes (> 0) |
| `likert_usefulness` | Integer | No | 1--5 |
| `likert_ease` | Integer | No | 1--5 |
| `likert_confidence` | Integer | No | 1--5 |
| `likert_engagement` | Integer | No | 1--5 |
| `likert_satisfaction` | Integer | No | 1--5 |
| `likert_learning` | Integer | No | 1--5 |

Each participant must have **exactly 2 rows** (one per period). The file must be UTF-8 encoded with a header row.

For the full column specification with descriptions and edge cases, see the [data dictionary](../../sample_data/data_dictionary.md).
{: .note }

### Steps to replace the data

1. Save your data as a CSV following the format above.
2. Copy it to `sample_data/crossover_sample_data.csv`, replacing the existing file.
3. Run the pipeline as described in [Step 4](04-run-pipeline).

Alternatively, if you want to keep the sample data intact, place your file elsewhere and update the `DATA_DIR` path in `analysis/R/00_setup.R` or set the corresponding environment variable in the Python pipeline.

### Adding or removing Likert items

If your perception survey has more or fewer items than the default six, the pipeline adapts automatically. The scripts detect Likert columns by their `likert_` prefix: any column whose name starts with `likert_` will be included in the perception analysis (script `08`) and instrument validation (script `03`).

To add a custom item, simply include a column named `likert_youritem` in your CSV. To remove an item, omit the column. No code changes are needed.

If you rename your outcome variable (e.g., `grade` instead of `score`), you will need to update the `required_cols` list in `01_data_import_clean.R` or the corresponding Python file. Keep the standard names if possible.
{: .warning }

---

## 2. Adapting instruments to your discipline

The toolkit ships with instruments designed for engineering education, but they can be adapted to any field. The [instrument adaptation guide](../instrument_adaptation) provides detailed instructions, including:

- How to modify the challenge tasks for your discipline (e.g., clinical case analysis for medicine, essay writing for humanities, financial modeling for business)
- How to adapt the Likert perception items while preserving the underlying constructs
- How to validate adapted instruments using V de Aiken (content validity), pilot testing, and Cronbach's alpha
- How to adapt the evaluation rubric and verify inter-rater reliability (ICC)

The key principle is to change the surface content (terminology, examples, task format) while preserving the measurement constructs (usefulness, ease, confidence, engagement, satisfaction, learning).
{: .tip }

### Quick adaptation checklist

- [ ] Replace challenge task topics with content from your discipline
- [ ] Review and adapt Likert item wording with 2--3 domain experts
- [ ] Compute V de Aiken from expert ratings (target V >= 0.70 per item)
- [ ] Pilot the adapted instruments with 10--20 students
- [ ] Compute Cronbach's alpha on pilot data (target alpha >= 0.70)
- [ ] If using a rubric, train raters and compute ICC (target ICC >= 0.70)
- [ ] Document all changes for reproducibility

---

## 3. Sample size considerations

The crossover design is more efficient than parallel-group designs because within-subject comparisons reduce error variance. However, you still need enough participants to detect your expected effect size with adequate power.

### Rule of thumb

For a 2x2 crossover design with paired t-test as the primary analysis:

| Expected effect size (Cohen's d) | Minimum n per sequence | Total N |
|:----------------------------------|:-----------------------|:--------|
| Large (d = 0.80) | 15--20 | 30--40 |
| Medium (d = 0.50) | 30--40 | 60--80 |
| Small (d = 0.30) | 80--100 | 160--200 |

These estimates assume power = 0.80 and alpha = 0.05 (two-sided). In practice, target **30--50 participants per sequence** (60--100 total) for medium effects, which covers most educational AI studies.

These numbers are approximations. For a formal power analysis, use G*Power (free software) or the `pwr` package in R. Specify: paired t-test, two-tailed, alpha = 0.05, power = 0.80, and your anticipated Cohen's d.
{: .tip }

### Accounting for attrition

Plan for 10--15% dropout between Period 1 and Period 2. If you need 80 complete cases, recruit at least 90--95 participants.

### Multi-class designs

If your class has only 30 students, consider running the study across multiple sections of the same course, or across semesters. The pipeline handles any sample size, but statistical power depends on the number of complete participant pairs.

---

## 4. Multi-site studies

If you are coordinating a study across multiple institutions, campuses, or countries, additional considerations apply.

### Adding institutional fields

Add columns to your CSV to identify the site:

| Column | Example values |
|:-------|:---------------|
| `institution` | `UEx`, `MIT`, `TU_Delft` |
| `country` | `ES`, `US`, `NL` |
| `instructor` | `Instructor_A`, `Instructor_B` |

These columns will be ignored by the default pipeline (which only requires the core columns), but you can use them for subgroup analyses.

### Pooling data from multiple sites

1. Ensure all sites use the **same column names and value coding** (especially `condition`, `sequence`, and `period`).
2. Concatenate the CSV files into a single file.
3. Add an `institution` column to identify the source of each row.
4. Run the standard pipeline on the pooled data.

For a more rigorous multi-site analysis, extend the LMM in script `05_mixed_anova.R` to include `institution` as a random effect:

```r
# Multi-site model
lmm_multisite <- lmer(
  score ~ condition + period_num + sequence + (1 | institution/participant_id),
  data = df_clean
)
```

This accounts for systematic differences between institutions while still estimating a common treatment effect. If the treatment effect might differ across sites, add a random slope:

```r
# Multi-site model with random treatment effect
lmm_multisite_rs <- lmer(
  score ~ condition + period_num + sequence + (condition | institution) + (1 | participant_id),
  data = df_clean
)
```

Multi-site analyses increase statistical power and generalizability, but they require careful coordination to ensure procedural consistency across sites.
{: .note }

---

## 5. Reporting checklist

When writing up your results for publication, ensure you include all of the following elements. This checklist follows the CONSORT extension for crossover trials (Dwan et al., 2019) adapted for educational research.

### Study design and methods

- [ ] State the design: 2x2 crossover (AB/BA)
- [ ] Report the number of participants and how they were randomized to sequences
- [ ] Describe both treatment conditions (AI tool used, task instructions, time limits)
- [ ] Describe the washout period (duration, what happened between periods)
- [ ] Report the challenge tasks used in each period and how equivalence was established
- [ ] Describe all outcome measures (score, rubric, Likert items) and their psychometric properties
- [ ] State the statistical model: paired t-test and/or linear mixed model
- [ ] Report the alpha level and any corrections for multiple comparisons

### Results

- [ ] Report the carryover test result (Grizzle's test statistic and p-value)
- [ ] Report descriptive statistics by condition: means, SDs, and sample sizes
- [ ] Report the 2x2 cell means (condition x period)
- [ ] Report the paired t-test or Wilcoxon result: test statistic, df, p-value, 95% CI
- [ ] Report effect sizes with confidence intervals (Cohen's d or Hedges' g)
- [ ] Report the mixed ANOVA or LMM: treatment, period, and sequence effects
- [ ] Report perception results: medians by condition, Wilcoxon tests, correction method
- [ ] Include at least one figure (the interaction plot or composite figure)

### Transparency

- [ ] State whether the analysis was pre-registered (and provide the registration link)
- [ ] Report any deviations from the pre-registered analysis plan
- [ ] Make data and analysis code available (link to the GitHub repository)
- [ ] Report any excluded participants and the reasons for exclusion

The CONSORT crossover extension (Dwan et al., 2019) is designed for clinical trials but adapts well to educational research. Reviewers familiar with CONSORT will appreciate this level of reporting rigor.
{: .tip }

### Example results paragraph

See the narrative example at the end of [Step 5](05-results#putting-it-all-together-a-results-narrative) for a model paragraph that covers all essential elements in about 100 words.

---

## 6. Where to publish

Crossover studies on AI in education are relevant to a growing number of journals and conferences. Consider the following venues, listed by scope:

### Journals focused on educational technology

| Journal | Impact factor (approx.) | Notes |
|:--------|:------------------------|:------|
| *Computers & Education* | 12.0 | Flagship journal; strong empirical focus |
| *British Journal of Educational Technology (BJET)* | 6.7 | Open to experimental designs |
| *International Journal of Educational Technology in Higher Education (IJETHE)* | 8.6 | Open access; higher education focus |
| *Education and Information Technologies* | 5.5 | Broad scope within ed-tech |
| *Interactive Learning Environments* | 4.8 | Focus on learning environments and tools |
| *The Internet and Higher Education* | 8.6 | Specifically higher education and online/blended contexts |

### Journals focused on discipline-specific education

| Journal | Discipline |
|:--------|:-----------|
| *Journal of Engineering Education* | Engineering |
| *Medical Education* | Medicine |
| *Journal of Chemical Education* | Chemistry |
| *Teaching in Higher Education* | General HE pedagogy |

### Journals for methodology and software

| Journal | Focus |
|:--------|:------|
| *SoftwareX* | Research software with clear impact |
| *Journal of Open Source Software (JOSS)* | Open-source research tools |
| *Journal of Statistical Software* | Statistical methods and implementations |

### Conferences

- **EDUCON** (IEEE Global Engineering Education Conference)
- **FIE** (Frontiers in Education)
- **LAK** (Learning Analytics and Knowledge)
- **AIED** (Artificial Intelligence in Education)
- **ICALT** (International Conference on Advanced Learning Technologies)

Match your manuscript to the audience. If your primary contribution is the educational finding (AI helps or does not help), target an education journal. If your contribution is the methodology or the reusable toolkit, consider a methods or software journal.
{: .note }

---

## 7. Contributing back

The crossover-edtech-toolkit is an open-source community project. If you use it in your research, consider contributing back to help others:

### Share your adapted instruments

If you adapted the instruments for a new discipline (e.g., nursing, architecture, law), share them by:

1. Placing the adapted instruments in the `instruments/` directory.
2. Including a brief README describing the discipline, language, and validation evidence.
3. Submitting a pull request to the [GitHub repository](https://github.com/jtorreci/crossover-edtech-toolkit).

### Share validation data

Psychometric validation data (Cronbach's alpha, V de Aiken, ICC) from real studies strengthens the evidence base for the instruments. Consider sharing:

- Your sample size and population characteristics
- Reliability coefficients for each instrument
- Factor analysis results (if available)

### Translations

If you translated the instruments into another language, your translation is valuable. Follow the translate-back-translate protocol described in the [instrument adaptation guide](../instrument_adaptation#language-adaptation) and include both the forward and back translations.

### Report bugs and suggest features

Open an issue on GitHub if you find a bug in the pipeline, encounter unclear documentation, or have ideas for new analysis features (e.g., Bayesian estimation, ordinal mixed models, mediation analysis).

### Cite the toolkit

If you use this toolkit in published work, please cite it so that others can find it:

```bibtex
@article{torrecilla2026crossover,
  title   = {crossover-edtech-toolkit: An Open-Source Platform for Replicable
             Crossover Experimental Studies Evaluating Generative AI in Education},
  author  = {Torrecilla-Pinero, Jes{\'u}s {\'A}ngel and others},
  journal = {SoftwareX},
  year    = {2026}
}
```

---

## Summary

You have completed the full tutorial. You now know how to:

1. Understand the crossover design and its statistical model
2. Set up the computing environment
3. Explore and validate the sample data
4. Run the full analysis pipeline
5. Interpret every output: descriptive statistics, carryover tests, paired comparisons, mixed models, effect sizes, perception analyses, and visualizations
6. Adapt the toolkit to your own study, discipline, and publication goals

The crossover design, combined with open and replicable analysis code, provides a strong foundation for evidence-based research on the impact of generative AI in education. We look forward to seeing what you discover.
