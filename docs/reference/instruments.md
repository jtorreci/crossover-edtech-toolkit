---
title: "Instrument Adaptation"
parent: Reference
nav_order: 3
layout: default
---

# Instrument Adaptation Guide
{: .no_toc }

How to adapt the toolkit's data-collection instruments to other disciplines while preserving psychometric validity.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The instruments provided in this toolkit were originally developed for engineering education courses. However, the crossover design and the data collection instruments can be adapted to virtually any discipline. This guide explains how to adapt the instruments while maintaining their psychometric validity.

## Instruments in the Toolkit

| Instrument | Purpose | When administered |
|:-----------|:--------|:------------------|
| **Pre-test** | Assess baseline knowledge before the study | Before Period 1 |
| **Challenge task** | The main activity performed under each condition (AI / noAI) | During each period |
| **Post-challenge survey** | Measure perceptions and experience after each challenge | After each period |
| **Post-test** | Assess knowledge retention after the study | After Period 2 |
| **Evaluation rubric** | Standardized scoring of challenge task outputs | Applied by evaluators |

All five instruments should be adapted as a coherent set. Changing one instrument (e.g., the challenge task) usually requires adjustments to the others (e.g., the rubric and the knowledge tests).
{: .note }

## Adaptation Process

### Step 1: Define Learning Objectives

Before modifying any instrument, clearly articulate the learning objectives for your course. The challenge tasks should align with these objectives. For example:

- **Engineering**: Design a structural element, debug a circuit, write a technical report
- **Medicine**: Interpret a clinical case, create a treatment plan, analyze lab results
- **Humanities**: Write a critical essay, analyze a historical source, translate a passage
- **Business**: Develop a marketing strategy, analyze a financial statement, draft a business plan

### Step 2: Adapt the Pre-Test and Post-Test

The knowledge tests should:

1. Cover content relevant to **both** challenge tasks (Period 1 and Period 2).
2. Have equivalent difficulty across the two periods (if using different versions).
3. Include a mix of question types: multiple choice, short answer, applied problems.
4. Be piloted with a small group to check difficulty and discrimination indices.

**Validation checklist:**
- [ ] Content reviewed by at least 2 subject-matter experts
- [ ] Pilot tested with 10--20 students from the target population
- [ ] Difficulty index (p) between 0.20 and 0.80 for most items
- [ ] Discrimination index (D) above 0.20 for most items
- [ ] Internal consistency (Cronbach's alpha) above 0.70

Skipping the pilot phase is the most common cause of poor instrument quality. Even a small pilot (n = 10--20) can reveal ambiguous wording, ceiling effects, and items that fail to discriminate.
{: .warning }

### Step 3: Adapt the Challenge Tasks

The two challenge tasks (one per period) must be:

1. **Equivalent in difficulty** to avoid confounding period with task difficulty.
2. **Different in content** to minimize direct knowledge transfer between periods.
3. **Representative** of the learning objectives.
4. **Suitable for AI assistance**: the task should be one where AI can plausibly help (e.g., writing, problem-solving, analysis) rather than purely mechanical tasks.

**Equivalence strategies:**
- Have experts rate task difficulty on a standardized scale (use V de Aiken).
- Pilot both tasks with a separate group and compare mean scores.
- Counterbalance tasks across sequences (i.e., some AB students get Task 1 first, others get Task 2 first).

Counterbalancing tasks across sequences is strongly recommended. If Task 1 is always paired with Period 1, any difficulty difference between tasks is confounded with the period effect and cannot be disentangled.
{: .tip }

### Step 4: Adapt the Post-Challenge Survey

The Likert-scale items in the perception survey can be adapted by:

1. **Keeping the constructs**: Usefulness, ease of use, confidence, engagement, satisfaction, and perceived learning are broadly applicable.
2. **Modifying the wording**: Replace discipline-specific terminology.
3. **Adding discipline-specific items**: For example, in medical education you might add "I felt the diagnosis was more accurate with the available resources."

**Example adaptations:**

| Original (Engineering) | Adapted (Medicine) |
|:-----------------------|:-------------------|
| "The tools helped me complete the design task" | "The tools helped me complete the clinical analysis" |
| "I am confident in my technical solution" | "I am confident in my diagnostic reasoning" |

After adaptation:
- [ ] Review wording with domain experts (V de Aiken >= 0.70 per item)
- [ ] Pilot with target population
- [ ] Compute Cronbach's alpha (target >= 0.70)
- [ ] Check item-total correlations (drop items with r < 0.30)

### Step 5: Adapt the Evaluation Rubric

The rubric for scoring challenge outputs should:

1. Reflect the specific competencies assessed in your discipline.
2. Use clear, observable criteria (not subjective impressions).
3. Have 3--5 performance levels with explicit descriptions for each.
4. Be tested for inter-rater reliability (ICC >= 0.70).

**Rubric development process:**
1. Draft criteria based on learning objectives.
2. Have 2--3 experts review and refine.
3. Score 10--15 sample outputs independently.
4. Compute ICC; if below 0.70, refine descriptors and retrain raters.
5. Finalize and document.

An ICC below 0.70 does not necessarily mean the rubric is flawed -- it may indicate that raters need calibration training. Have raters discuss their scoring of 3--5 anchor examples before scoring the full sample.
{: .tip }

## Language Adaptation

If adapting instruments to another language:

1. Use the **translate-back-translate** method: translate to the target language, then have an independent translator translate back to the original language. Compare and resolve discrepancies.
2. Pilot in the target language.
3. Re-validate psychometric properties (alpha, factor structure).

Translation must go beyond literal word-for-word rendering. Cultural adaptation of examples, response anchors, and idiomatic expressions is essential to preserve construct validity.
{: .warning }

## Reporting Adaptations

When publishing results with adapted instruments, report:

- The original instrument source
- What was changed and why
- Validation evidence for the adapted version (expert review, pilot data, reliability)
- The full adapted instrument (as supplementary material or in the `instruments/` directory)

Transparent reporting of adaptations strengthens the credibility of your findings and enables other researchers to replicate or extend your work.
{: .note }
