---
title: "Step 1: Understanding the Crossover Design"
parent: Tutorial
nav_order: 1
---

# Step 1: Understanding the Crossover Design
{: .no_toc }

Learn what a crossover experiment is, why it is well-suited to educational research, and how the statistical model separates treatment effects from nuisance factors.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## What is a crossover design?

A **crossover design** (also called an AB/BA design) is an experimental plan in which every participant receives *both* treatments, but in a different order. Half the participants start with Treatment A and then switch to Treatment B; the other half do the reverse.

In our context the two treatments are:

- **AI** -- the student completes a challenge task with access to a generative AI tool.
- **noAI** -- the student completes a comparable challenge task without AI assistance.

Because each student experiences both conditions, individual differences in ability, motivation, and prior knowledge are naturally controlled. This makes the crossover design one of the most efficient experimental plans available for educational research.

## The 2 x 2 crossover table

The design can be summarized in a compact table:

| | **Period 1** | **Period 2** |
|:--|:------------|:------------|
| **Sequence AB** (50 % of students) | Challenge **without** AI | Challenge **with** AI |
| **Sequence BA** (50 % of students) | Challenge **with** AI | Challenge **without** AI |

Students are randomly assigned to one of the two sequences before the study begins. Each period involves a different challenge topic of equivalent difficulty, and a **washout interval** (e.g., a different lecture, a time gap of one or more weeks) separates the two periods to minimize carryover.

### Visual schematic

```
Sequence AB                Sequence BA

  Period 1    Period 2       Period 1    Period 2
 ┌────────┐  ┌────────┐    ┌────────┐  ┌────────┐
 │  noAI  │──│   AI   │    │   AI   │──│  noAI  │
 └────────┘  └────────┘    └────────┘  └────────┘
       ▲                          ▲
       └── washout ──┘            └── washout ──┘
```

## A practical example

Imagine you teach a Civil Engineering course and you want to know whether students learn better with or without AI assistance on structural-analysis exercises.

1. You design two challenge tasks of comparable difficulty -- say, one on beam deflection and another on truss analysis.
2. You randomly split your class of 60 students into two groups of 30.
3. In **Week 4**, Group AB solves the beam-deflection task *without* AI, while Group BA solves it *with* AI.
4. In **Week 8** (after the washout), Group AB tackles the truss task *with* AI, and Group BA tackles it *without* AI.
5. You collect scores on both tasks, along with pre/post questionnaires on self-efficacy and attitudes toward AI.

At the end, every student has one AI score and one noAI score, and you can compare them within each individual. This is exactly the kind of study the crossover-edtech-toolkit is built to support.

## The statistical model

The outcome for participant *i* in period *j* receiving treatment *k* in sequence *l* is modeled as:

```
Y_ijk = mu + pi_j + tau_k + lambda_l + S_i + epsilon_ijk
```

Each term captures a different source of variation:

| Symbol | Name | Meaning |
|:-------|:-----|:--------|
| `mu` | Grand mean | Overall average score across all observations |
| `pi_j` | Period effect | Systematic difference between Period 1 and Period 2 (e.g., practice, fatigue, or familiarity with the task format). *j* = 1, 2 |
| `tau_k` | Treatment effect | The effect of interest -- the difference between AI and noAI conditions. *k* = AI, noAI |
| `lambda_l` | Carryover (sequence) effect | Whether the order in which treatments are received matters -- e.g., does using AI first change how you perform without it later? *l* = AB, BA |
| `S_i` | Subject effect | Random effect capturing stable individual differences (S_i ~ N(0, sigma_S^2)). This is what makes the crossover design powerful: by modeling each student as a random effect, within-subject comparisons automatically remove this variability |
| `epsilon_ijk` | Residual error | Everything else (epsilon ~ N(0, sigma^2)) |

The **primary hypothesis** concerns `tau_k`: is there a statistically significant difference between the AI and noAI conditions?

The model is fit as a **linear mixed-effects model** (LMM), with `S_i` as a random intercept and the remaining terms as fixed effects. The toolkit implements this using `lme4::lmer()` in R and `statsmodels.MixedLM` in Python.
{: .note }

## Why is this better than parallel groups?

In a traditional parallel-group (between-subjects) design, one group uses AI and another does not. The two groups are then compared. This approach has several limitations that the crossover design addresses:

| Criterion | Parallel groups | Crossover |
|:----------|:---------------|:----------|
| **Between-subject variability** | Confounds the treatment comparison -- Group A may simply have better students | Eliminated; each student is their own control |
| **Statistical power** | Low: large samples needed because between-subject variance inflates the error term | High: within-subject variance is much smaller, so the same effect is easier to detect |
| **Sample size** | Typically requires 2--4 times more participants for the same power | Efficient; all participants contribute data under both conditions |
| **Ethical fairness** | One group never receives the potentially beneficial treatment | Every student gets access to AI at some point |
| **Data efficiency** | Half the data is "wasted" on the control-only group | No waste; every observation informs the treatment comparison |

As a rule of thumb, a crossover design can achieve the same statistical power as a parallel-group design with roughly **half the participants** (or fewer), because the within-subject error variance is substantially smaller than the between-subject error variance.
{: .tip }

## Key assumptions

The crossover design is powerful, but it relies on several assumptions that you must consider during planning:

### 1. No (or negligible) carryover

The effect of the first treatment should not persist into the second period. In educational settings, this means that knowledge or skills gained with AI in Period 1 should not give an unfair advantage (or disadvantage) when the student works without AI in Period 2.

**How the toolkit handles this:** Script `07_carryover_analysis` implements Grizzle's test for carryover. If carryover is detected (at alpha = 0.10), the analysis flags this and optionally restricts inference to Period 1 data only.

### 2. Equivalent task difficulty

The two challenge tasks used in Period 1 and Period 2 must be of comparable difficulty. If one task is substantially harder, the period effect will be confounded with task difficulty.

**Mitigation strategies:**
- Pilot-test both tasks on a separate group of students.
- Use rubrics with clear, objective criteria.
- Compare raw score distributions across tasks.

### 3. Proper washout

There must be sufficient time or change of context between the two periods so that the effects of the first condition dissipate. In educational studies, changing the topic (e.g., beam deflection in Period 1, truss analysis in Period 2) usually provides an adequate washout.

### 4. No differential dropout

Students should not systematically drop out based on which treatment they received first. If students who found the noAI condition frustrating are more likely to skip Period 2, this introduces bias.

If any assumption is violated, the toolkit's analysis scripts will help you detect it. Carryover is tested explicitly, period effects are estimated in the ANOVA, and the data import script checks for missing data and dropout patterns.
{: .note }

## Summary

The 2 x 2 crossover design offers a rigorous, efficient, and ethically sound framework for studying the impact of AI (or any intervention) on student learning. By ensuring that every student experiences both conditions, it eliminates between-subject confounds and dramatically increases the statistical power of your study.

In the next step, you will set up your computing environment so you can run the analysis pipeline on sample data.

---

**Next:** [Step 2: Setting Up Your Environment](02-setup)
