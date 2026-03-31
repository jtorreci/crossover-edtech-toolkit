---
title: "Study Design"
parent: Reference
nav_order: 1
---

# Study Design: Crossover 2x2 Experimental Design
{: .no_toc }

A complete description of the two-period, two-treatment crossover design implemented by this toolkit.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

This toolkit implements a **two-period, two-treatment crossover design** (also known as an AB/BA crossover). In this design, every participant receives both treatments in sequence, with the order of treatments randomized between two groups. This makes each participant their own control, which substantially reduces the variability caused by individual differences.

## Structure

| | Period 1 | Period 2 |
|:--|:---------|:---------|
| **Sequence AB** (Group A) | Treatment B (noAI) | Treatment A (AI) |
| **Sequence BA** (Group B) | Treatment A (AI) | Treatment B (noAI) |

- **N** participants are randomly allocated to one of the two sequences.
- Each participant completes a challenge task in each period: once with access to a generative AI tool, and once without.
- A **washout period** (e.g., different topic or sufficient time gap) separates the two periods to reduce carryover.

The washout period is critical. In educational settings, this typically means using a different topic or activity for each period, and allowing enough calendar time between sessions for any short-term effects to dissipate.
{: .warning }

## Statistical model

The outcome for participant *i* in period *j* receiving treatment *k* in sequence *l* is modeled as:

```
Y_ijkl = mu + pi_j + tau_k + lambda_l + S_i + epsilon_ijkl
```

Where:

| Symbol | Meaning |
|:-------|:--------|
| `mu` | Grand mean |
| `pi_j` | Period effect (j = 1, 2). Captures learning, fatigue, or practice effects across periods |
| `tau_k` | Treatment effect (k = AI, noAI). The primary effect of interest |
| `lambda_l` | Carryover effect. Tests whether receiving treatment A first influences the response to treatment B in the next period |
| `S_i` | Random subject effect (S_i ~ N(0, sigma_S^2)). Captures individual differences |
| `epsilon_ijkl` | Residual error (epsilon ~ N(0, sigma^2)) |

The treatment effect `tau_k` is the parameter of primary interest. A positive value indicates that the AI condition improves performance relative to the control.
{: .note }

## Why a crossover design?

### Advantages

1. **Within-subject comparisons**: Each student is compared against themselves, eliminating between-subject confounds (motivation, prior knowledge, ability).
2. **Increased statistical power**: With variance reduction, you need far fewer participants than a parallel-group design to detect the same effect.
3. **Efficiency**: All participants provide data under both conditions, so no data is "wasted" on a control-only group.
4. **Ethical fairness**: Every student gets access to the AI tool at some point, avoiding concerns about withholding a potentially beneficial resource.

### Potential concerns

1. **Carryover effects**: Skills or knowledge gained with AI may persist when the student later works without AI (or vice versa). The toolkit includes explicit tests for this (script `07_carryover_analysis.R`).
2. **Period effects**: Students may improve simply due to practice or familiarity with the task format. The design separates this from the treatment effect.
3. **Different tasks**: To avoid content overlap, each period typically uses a different challenge topic. Tasks should be validated for equivalent difficulty.

If the carryover test is significant, the crossover analysis becomes unreliable. In that case, the toolkit falls back to analyzing only Period 1 data, which is equivalent to a parallel-group design. Plan your washout strategy carefully to minimize this risk.
{: .warning }

## Analysis strategy

1. **Test for carryover** (Grizzle's test): Compare the sum of each participant's scores across periods between sequences. If significant (alpha = 0.10), analyze only Period 1 data.
2. **Test for treatment effect**: If no carryover, perform paired within-subject comparisons (paired t-test, Wilcoxon signed-rank).
3. **Mixed ANOVA / LMM**: Fit the full model to estimate treatment, period, and sequence effects simultaneously.
4. **Effect sizes**: Report Cohen's d for paired comparisons and partial eta-squared for ANOVA effects, always with confidence intervals.

The carryover test uses a relaxed significance threshold (alpha = 0.10) because missing a real carryover effect has serious consequences for the validity of the treatment effect estimate.
{: .tip }

## Randomization

Participants should be randomized to sequences using:

- **Simple randomization** (coin flip) for small studies
- **Stratified randomization** (by prior GPA, gender, etc.) for better balance
- **Block randomization** to ensure equal group sizes

The webapp supports automatic randomization at enrollment.

## References

- Senn, S. (2002). *Cross-over Trials in Clinical Research* (2nd ed.). Wiley.
- Jones, B., & Kenward, M. G. (2014). *Design and Analysis of Cross-Over Trials* (3rd ed.). CRC Press.
- Wellek, S., & Blettner, M. (2012). On the proper use of the crossover design in clinical trials. *Deutsches Arzteblatt International*, 109(15), 276--281.
