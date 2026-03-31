# Instruments

This directory is intended to hold the validated data collection instruments used in the crossover study. Place your instrument files here in the appropriate format (PDF, DOCX, or plain text).

## Expected Instruments

| File | Description |
|---|---|
| `pre_test.*` | Knowledge assessment administered before the study begins. Establishes baseline competency. |
| `post_test.*` | Knowledge assessment administered after both periods. Measures retention and transfer. |
| `challenge_task_1.*` | Description and requirements for the challenge task in Period 1. |
| `challenge_task_2.*` | Description and requirements for the challenge task in Period 2. Should be equivalent in difficulty to Task 1 but on a different topic. |
| `post_challenge_survey.*` | Likert-scale questionnaire administered after each challenge. Measures perceptions of usefulness, confidence, engagement, and satisfaction. |
| `evaluation_rubric.*` | Standardized rubric for scoring challenge task outputs. Used by evaluators for consistent grading. |
| `informed_consent.*` | Informed consent form for participants. See `docs/ethical_considerations.md` for a template. |

## Important Notes

- **Do not commit instruments with personally identifiable information.** This directory should contain blank instrument templates, not completed responses.
- **Adapt to your context.** The instruments should be modified to match your discipline, language, and institutional requirements. See `docs/instrument_adaptation.md` for guidance.
- **Validate before use.** Any adapted instrument should be reviewed by subject-matter experts (V de Aiken >= 0.70) and pilot-tested for reliability (Cronbach's alpha >= 0.70). The analysis script `03_instrument_validation.R` can help with this.
- **Version control.** If you revise an instrument, keep previous versions (e.g., `post_challenge_survey_v1.pdf`, `post_challenge_survey_v2.pdf`) and document what changed.

## Sharing Instruments

If you develop validated instruments for a specific discipline and are willing to share them, consider contributing them back to this repository (see `CONTRIBUTING.md`). Shared instruments help other researchers replicate and extend the work.
