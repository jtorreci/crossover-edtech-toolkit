---
title: "Ethical Considerations"
parent: Reference
nav_order: 5
layout: default
---

# Ethical Considerations and Ethics Committee Submission
{: .no_toc }

Key ethical principles, an IRB/CEIC application template, and an informed consent form template for crossover studies evaluating AI tools in higher education.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

Research involving human participants in educational settings requires ethical review and approval. This document provides a template for ethics committee (IRB/CEIC) submissions and outlines key considerations for crossover studies evaluating AI tools in higher education.

Ethics approval must be obtained before any data collection begins. Retroactive approval is not possible, and data collected without prior approval cannot be used in publications.
{: .warning }

## Key Ethical Principles

### 1. Informed Consent

All participants must provide informed consent before enrollment. The consent form should explain:

- The purpose of the study (evaluating the impact of AI tools on learning)
- The crossover design: participants will complete two challenges, one with AI access and one without
- The random assignment to sequence (AB or BA)
- What data will be collected and how it will be stored
- That participation is voluntary and withdrawal is possible at any time without penalty
- That the study will not affect their course grade (or how it will, if applicable)
- Contact information for the research team and the ethics committee

Consent must be freely given. When the researcher is also the course instructor, take extra care to ensure students do not feel coerced. Consider having a third party collect consent forms so the instructor does not know who participated until after final grades are posted.
{: .tip }

### 2. Anonymization and Data Protection

- Participant data must be **pseudonymized**: replace names with anonymous codes (P001, P002, ...).
- The mapping between real identities and codes must be stored separately and securely (encrypted, restricted access).
- Data collected through the webapp should be stored in a GDPR-compliant manner (if applicable in the EU).
- Raw data should never be shared publicly. Only anonymized, aggregated results should be published.
- Set a data retention period (e.g., 5 years after publication) and destroy identifiable data afterward.

For studies conducted within the European Union, GDPR compliance is a legal obligation, not merely a best practice. This includes appointing a data controller, maintaining a processing record, and providing participants with a mechanism to request data deletion.
{: .warning }

### 3. Equity and Fairness

The crossover design is inherently equitable: **every participant receives both conditions**. No student is permanently denied access to the AI tool. However, consider:

- The order effect: students in one sequence get AI first, the other sequence gets it second. Ensure that this does not create an unfair advantage for assessments that count toward the final grade.
- If the study is embedded in a graded course, ensure that the study conditions do not disadvantage any student in terms of their final evaluation.
- Provide equivalent support to all students regardless of sequence assignment.

The crossover design addresses the most common ethical objection to educational experiments -- that a control group is permanently denied a potentially beneficial intervention. Here, every student experiences both conditions.
{: .note }

### 4. Minimal Risk

The study should present no more than minimal risk to participants:

- The AI tool should be used in a supervised, educational context.
- Challenge tasks should be appropriate for the students' level.
- Students should be informed that they can stop at any time if they experience discomfort.
- If AI generates incorrect or misleading content, the educational context should include mechanisms to correct misconceptions (e.g., post-study debriefing, instructor feedback).

### 5. Debriefing

After the study:

- Inform participants about the study's findings (at a group level).
- Explain what the crossover design tested and why.
- Provide resources for students who want to learn more about using AI tools effectively.

Debriefing is both an ethical obligation and a pedagogical opportunity. Students benefit from understanding the research process they contributed to.
{: .tip }

---

## Template: Ethics Committee Application

The template below can be adapted for your institutional ethics review board (IRB, CEIC, or equivalent). Replace all bracketed placeholders with your study-specific details.
{: .note }

### Study Title

*Evaluating the Impact of Generative Artificial Intelligence on [Learning Outcome] in [Course/Discipline]: A Crossover Experimental Study*

### Principal Investigator

*[Name, Department, Institution, Contact]*

### Study Objectives

This study aims to evaluate whether access to a generative AI tool (e.g., ChatGPT, Copilot) during [specific educational task] improves student performance, as measured by [score, rubric evaluation, time to completion]. Secondary objectives include assessing student perceptions of usefulness, confidence, and engagement.

### Study Design

A 2x2 crossover experimental design with two periods and two conditions (AI-assisted vs. no AI). Each participant completes both conditions in a randomized order. Participants are randomly assigned to Sequence AB (noAI first, AI second) or Sequence BA (AI first, noAI second). This design ensures that each student serves as their own control.

### Participants

- **Population**: Students enrolled in [Course Name], [Department], [University]
- **Expected sample size**: N = [number] (power analysis: [details])
- **Inclusion criteria**: Enrolled in the course, willing to participate, able to provide informed consent
- **Exclusion criteria**: Students who do not consent, students who withdraw

### Procedures

1. **Information session**: Students are informed about the study and given the consent form.
2. **Randomization**: Consenting students are randomly assigned to Sequence AB or BA.
3. **Pre-test**: Baseline knowledge assessment (approximately [X] minutes).
4. **Period 1**: Challenge task under the assigned condition ([X] minutes).
5. **Post-challenge survey 1**: Perception questionnaire (approximately [X] minutes).
6. **Washout**: [Describe: different topic, time interval, etc.]
7. **Period 2**: Challenge task under the alternate condition ([X] minutes).
8. **Post-challenge survey 2**: Perception questionnaire (approximately [X] minutes).
9. **Post-test**: Knowledge retention assessment (approximately [X] minutes).

### Data Collected

| Data type | Method | Storage |
|:----------|:-------|:--------|
| Pre-test scores | Web application | Cloud Firestore (encrypted) |
| Challenge task submissions | Web application | Cloud Firestore (encrypted) |
| Rubric evaluations | Evaluator entry | Cloud Firestore (encrypted) |
| Likert perception ratings | Web application | Cloud Firestore (encrypted) |
| Time stamps | Automatic logging | Cloud Firestore (encrypted) |

### Data Protection

- All data is pseudonymized at the point of collection (anonymous participant codes).
- The identity-code mapping is stored in [secure location, access restricted to PI].
- Data is stored on [Firebase/institutional server] in compliance with [GDPR / institutional policy].
- Data will be retained for [5] years after publication, then destroyed.
- Only aggregated, anonymized results will be published.

### Risks and Benefits

**Risks**: Minimal. Participants may experience mild frustration with the task or the AI tool. No physical, psychological, or academic risk beyond normal coursework.

**Benefits**: Participants gain experience with AI tools in an educational context. They contribute to knowledge about effective pedagogical use of AI. All students experience both conditions.

### Compensation

[State whether students receive compensation, course credit, or no compensation.]

### Voluntary Participation and Withdrawal

Participation is entirely voluntary. Students who choose not to participate will complete the same activities as part of normal coursework but their data will not be included in the analysis. Students may withdraw at any time without providing a reason and without any academic penalty.

Make it explicit that non-participating students will still complete the same activities and receive the same instruction. This avoids any perception that participation is required to access course content.
{: .tip }

### Informed Consent

[Attach the informed consent form as an appendix.]

### Conflict of Interest

[Declare any conflicts of interest, funding sources, or relationships with AI tool providers.]

---

## Informed Consent Form (Template)

**Study Title**: [Title]

**Researcher**: [Name, Contact]

**Institution**: [University, Department]

You are invited to participate in a research study about the use of artificial intelligence tools in education. Please read the following information carefully.

**What is the study about?**
We are investigating whether access to a generative AI tool during [educational task] affects learning outcomes and student perceptions.

**What will I be asked to do?**
You will complete two challenge tasks over [time period]. For one task, you will have access to an AI tool; for the other, you will not. The order is randomly assigned. You will also complete brief questionnaires about your experience.

**How long will it take?**
Approximately [X] minutes per session, [Y] sessions total.

**Are there any risks?**
The risks are minimal and no greater than those experienced in normal coursework.

**Is my participation voluntary?**
Yes. You may withdraw at any time without any academic penalty. If you withdraw, your data will be deleted.

**How will my data be protected?**
Your responses will be stored with an anonymous code, not your name. Only the research team will have access to the data. Results will be published in aggregate form only.

**Questions?**
Contact [researcher name] at [email] or the ethics committee at [contact].

[ ] I have read and understood the above information. I voluntarily agree to participate.

Name: _________________ Signature: _________________ Date: _________________

This template is a starting point. Your institution's ethics committee may require additional sections (e.g., data sharing agreements, specific GDPR clauses, minor consent procedures). Always check your local requirements before submission.
{: .note }
