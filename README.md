# crossover-edtech-toolkit

**Open-Source Platform for Replicable Crossover Experimental Studies in Education**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://img.shields.io/badge/DOI-10.xxxx%2Fxxxxx-blue.svg)](https://doi.org/10.xxxx/xxxxx)

---

## Overview

`crossover-edtech-toolkit` provides a complete, reproducible framework for conducting **crossover (AB/BA) experimental studies** in higher education, with a particular focus on evaluating the impact of **generative AI tools on student learning outcomes**.

### What is a crossover 2x2 design?

In a crossover study, every participant experiences **both experimental conditions** (e.g., with AI assistance and without AI assistance) across two time periods. Participants are randomly assigned to one of two **sequences**:

- **Sequence AB**: Period 1 without AI, Period 2 with AI
- **Sequence BA**: Period 1 with AI, Period 2 without AI

Because each student serves as their own control, this design dramatically **reduces between-subject variability**, increasing statistical power with smaller sample sizes. The design also allows explicit testing for **carryover effects** and **period effects**, both of which are critical when studying learning interventions.

The statistical model underlying the analysis is:

```
Y_ijk = mu + pi_j + tau_k + lambda_l + S_i + epsilon_ijk
```

where `mu` is the grand mean, `pi_j` is the period effect, `tau_k` is the treatment effect (AI vs. no-AI), `lambda_l` is the carryover effect, `S_i` is the random subject effect, and `epsilon_ijk` is the residual error.

## Features

| Component | Description |
|---|---|
| **Web application** | Firebase-based data collection platform with pre-test, challenge, post-challenge, and post-test phases |
| **Validated instruments** | Rubrics, Likert-scale questionnaires, and knowledge tests adaptable to any discipline |
| **R analysis pipeline** | 10 modular scripts covering descriptive statistics, instrument validation, mixed ANOVA, carryover tests, effect sizes, and publication-quality visualizations |
| **Python analysis pipeline** | Parallel set of 10 scripts plus a Jupyter notebook, using pandas, scipy, pingouin, statsmodels, and matplotlib/seaborn to replicate every R analysis |
| **Sample data generator** | Synthetic dataset simulating 100 students in a 2x2 crossover, with configurable effect sizes (available in both R and Python) |
| **Comprehensive documentation** | Study design guide, deployment instructions, instrument adaptation manual, ethical considerations template |

## Quick Start

The toolkit provides **two equivalent analysis pipelines**. Choose whichever language you are more comfortable with -- both produce the same statistical results, tables, and publication-quality figures.

### Prerequisites

| Language | Requirement |
|---|---|
| **R** | R >= 4.2.0 (RStudio recommended) |
| **Python** | Python >= 3.9 |
| Both | **Git** for cloning the repository |

### Option A: R Pipeline

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/crossover-edtech-toolkit.git
   cd crossover-edtech-toolkit
   ```

2. **Install R dependencies**:
   ```r
   source("analysis/R/00_setup.R")
   ```

3. **Generate sample data** (optional, for testing):
   ```r
   source("sample_data/generate_sample_data.R")
   ```

4. **Run the full analysis pipeline**:
   ```r
   source("analysis/R/run_all.R")
   ```

5. **Explore outputs** in the `output/` directory (created automatically).

### Option B: Python Pipeline

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/crossover-edtech-toolkit.git
   cd crossover-edtech-toolkit
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r analysis/python/requirements.txt
   ```

3. **Generate sample data** (optional, for testing):
   ```bash
   python sample_data/generate_sample_data.py
   ```

4. **Run the full analysis pipeline**:
   ```bash
   python analysis/python/run_all.py
   ```

5. **Explore outputs** in the `output/` directory (created automatically).

#### Interactive notebook

For an interactive workflow, open the Jupyter notebook that combines all analysis steps in a single narrative document:

```bash
jupyter notebook analysis/python/full_analysis.ipynb
```

### Choosing between R and Python

Both pipelines mirror each other script-by-script:

| Step | R script | Python script | Purpose |
|---|---|---|---|
| 00 | `00_setup.R` | `00_setup.py` | Environment setup |
| 01 | `01_data_import_clean.R` | `01_data_import_clean.py` | Data import and cleaning |
| 02 | `02_descriptive_stats.R` | `02_descriptive_stats.py` | Descriptive statistics |
| 03 | `03_instrument_validation.R` | `03_instrument_validation.py` | Cronbach's alpha, V de Aiken, ICC |
| 04 | `04_paired_comparisons.R` | `04_paired_comparisons.py` | Paired t-test, Wilcoxon |
| 05 | `05_mixed_anova.R` | `05_mixed_anova.py` | Mixed ANOVA, linear mixed model |
| 06 | `06_effect_sizes.R` | `06_effect_sizes.py` | Cohen's d, Hedges' g, eta-squared |
| 07 | `07_carryover_analysis.R` | `07_carryover_analysis.py` | Grizzle's carryover test |
| 08 | `08_perception_analysis.R` | `08_perception_analysis.py` | Likert analysis, Wilcoxon + Holm |
| 09 | `09_visualizations.R` | `09_visualizations.py` | Publication-quality figures |
| -- | `run_all.R` | `run_all.py` | Pipeline orchestrator |

The Python pipeline additionally includes `full_analysis.ipynb`, a Jupyter notebook that combines all steps in an interactive, narrative format.

For detailed instructions, see [docs/analysis_guide.md](docs/analysis_guide.md).

## Directory Structure

```
crossover-edtech-toolkit/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── CITATION.cff                 # Citation metadata
├── CONTRIBUTING.md              # Contribution guidelines
├── .gitignore                   # Git ignore rules
├── paper/                       # SoftwareX manuscript
│   ├── paper.tex
│   └── references.bib
├── docs/                        # Documentation
│   ├── deployment_guide.md      # Firebase webapp deployment
│   ├── instrument_adaptation.md # Adapting instruments to other disciplines
│   ├── analysis_guide.md        # Step-by-step analysis instructions
│   ├── study_design.md          # Crossover 2x2 design explanation
│   └── ethical_considerations.md# Ethics committee submission template
├── instruments/                 # Validated data collection instruments
│   └── README.md
├── analysis/                    # Statistical analysis code
│   ├── R/
│   │   ├── 00_setup.R           # Package installation and loading
│   │   ├── 01_data_import_clean.R
│   │   ├── 02_descriptive_stats.R
│   │   ├── 03_instrument_validation.R
│   │   ├── 04_paired_comparisons.R
│   │   ├── 05_mixed_anova.R
│   │   ├── 06_effect_sizes.R
│   │   ├── 07_carryover_analysis.R
│   │   ├── 08_perception_analysis.R
│   │   ├── 09_visualizations.R
│   │   └── run_all.R
│   └── python/
│       ├── requirements.txt     # Python package dependencies
│       ├── 00_setup.py          # Environment check and configuration
│       ├── 01_data_import_clean.py
│       ├── 02_descriptive_stats.py
│       ├── 03_instrument_validation.py
│       ├── 04_paired_comparisons.py
│       ├── 05_mixed_anova.py
│       ├── 06_effect_sizes.py
│       ├── 07_carryover_analysis.py
│       ├── 08_perception_analysis.py
│       ├── 09_visualizations.py
│       ├── run_all.py
│       └── full_analysis.ipynb  # Interactive Jupyter notebook
├── sample_data/                 # Synthetic data for testing
│   ├── generate_sample_data.R
│   ├── generate_sample_data.py
│   └── data_dictionary.md
└── tests/                       # Automated tests
    └── test_analysis_pipeline.R
```

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@article{torrecilla2026crossover,
  title   = {crossover-edtech-toolkit: An Open-Source Platform for Replicable
             Crossover Experimental Studies Evaluating Generative {AI} in Education},
  author  = {Torrecilla Pinero, Juan Antonio and others},
  journal = {SoftwareX},
  year    = {2026},
  doi     = {10.xxxx/xxxxx}
}
```

See also [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

## Related Publications

- **Methodological paper**: Torrecilla Pinero, J.A. et al. (2025). *Crossover experimental design for evaluating generative AI in higher education engineering courses*. (In preparation)
- **SoftwareX paper**: Torrecilla Pinero, J.A. et al. (2026). *crossover-edtech-toolkit: An open-source platform for replicable crossover experimental studies evaluating generative AI in education*. (In preparation)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

Developed at the **Universidad de Extremadura** as part of a Teaching Innovation Project focused on evaluating the impact of generative artificial intelligence on learning outcomes in higher education.

---

*For questions or collaboration inquiries, please open an issue on GitHub or contact the project maintainers.*
