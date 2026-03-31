# Data Dictionary

This document describes all variables in the crossover study dataset (`crossover_sample_data.csv`).

## Identification and Design Variables

| Variable | Type | Range / Values | Description |
|---|---|---|---|
| `participant_id` | Character | P001 - P100 | Unique anonymized participant identifier |
| `group` | Factor | A, B | Assignment group. Group A = Sequence AB, Group B = Sequence BA |
| `sequence` | Factor | AB, BA | Treatment sequence. AB = noAI in Period 1, AI in Period 2. BA = AI in Period 1, noAI in Period 2 |
| `period` | Integer | 1, 2 | Time period (1 = first challenge, 2 = second challenge) |
| `condition` | Factor | AI, noAI | Experimental condition for this observation. AI = generative AI tool available; noAI = no AI tool available |

## Outcome Variables

| Variable | Type | Range | Description |
|---|---|---|---|
| `score` | Numeric | 0 - 100 | Primary outcome. Total score on the challenge task, assessed by the instructor or automated rubric. Higher values indicate better performance |
| `rubric_score` | Numeric | 0 - 10 | Secondary outcome. Rubric-based evaluation score, typically assessed by one or more evaluators. Scale: 0 (no competency demonstrated) to 10 (full competency) |
| `time_spent` | Numeric | > 0 | Time in minutes the participant spent on the challenge task. Recorded automatically by the data collection platform |

## Perception Variables (Likert Scale)

All Likert items use a 5-point scale:

- 1 = Strongly Disagree
- 2 = Disagree
- 3 = Neutral
- 4 = Agree
- 5 = Strongly Agree

| Variable | Type | Range | Description |
|---|---|---|---|
| `likert_usefulness` | Integer | 1 - 5 | "The tools/resources available during the challenge were useful for completing the task" |
| `likert_ease` | Integer | 1 - 5 | "I found it easy to complete the challenge with the available resources" |
| `likert_confidence` | Integer | 1 - 5 | "I felt confident in the quality of my work during this challenge" |
| `likert_engagement` | Integer | 1 - 5 | "I was actively engaged and motivated throughout the challenge" |
| `likert_satisfaction` | Integer | 1 - 5 | "Overall, I am satisfied with my performance on this challenge" |
| `likert_learning` | Integer | 1 - 5 | "I feel I learned something valuable during this challenge" |

## Data Structure

- Each participant contributes **exactly 2 rows** (one per period).
- The dataset is in **long format**: each row is one participant-period observation.
- The total number of rows should be 2 x N (where N is the number of participants).

## Missing Data

A small percentage of values may be missing:

- `score`: Should have no missing values (primary outcome, always collected).
- `rubric_score`: May have missing values if an evaluator did not submit a score.
- `time_spent`: May have missing values due to technical logging issues.
- `likert_*`: May have missing values if a participant skipped a question.

Missing values are coded as `NA`.

## Notes

- **Anonymization**: Participant IDs are anonymous codes (P001, P002, ...) with no link to real identities.
- **Generated data**: The sample dataset is synthetically generated for demonstration purposes. See `generate_sample_data.R` for the data-generating process and parameter values.
- **Your own data**: Replace `crossover_sample_data.csv` with your study data, preserving the same column names and formats. The analysis pipeline will work with any dataset matching this structure.
