# Contributing to crossover-edtech-toolkit

Thank you for your interest in contributing to this project. This toolkit is designed to support open and replicable research in education, and contributions from the community are valuable.

## How to Contribute

### Reporting Issues

If you find a bug, have a question, or want to suggest an improvement:

1. Check the [existing issues](https://github.com/your-org/crossover-edtech-toolkit/issues) to avoid duplicates.
2. Open a new issue with a clear title and description.
3. For bugs, include: R version, operating system, error messages, and a minimal reproducible example.

### Submitting Changes

1. **Fork** the repository and create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**. Follow the coding style described below.
3. **Test** your changes by running the test suite:
   ```r
   source("tests/test_analysis_pipeline.R")
   ```
4. **Commit** with a clear message describing what you changed and why:
   ```bash
   git commit -m "Add support for Latin square designs in carryover analysis"
   ```
5. **Push** to your fork and open a **Pull Request** against `main`.

### Types of Contributions We Welcome

- **Bug fixes** in the R analysis scripts
- **New analysis modules** (e.g., Bayesian alternatives, additional effect size measures)
- **Instrument adaptations** for new disciplines or languages
- **Documentation improvements** (clarifications, translations, additional examples)
- **Validation studies** that replicate the pipeline with new datasets
- **Webapp enhancements** (accessibility, new question types, localization)

### What We Ask

- Please do not submit large reformatting changes without prior discussion.
- If you are adding a new R dependency, justify it in the pull request.
- Academic software benefits from stability: prefer well-established packages over bleeding-edge ones.

## Coding Style

### R Scripts

- Use the **tidyverse** style guide: https://style.tidyverse.org/
- Every script file should start with a header comment block explaining its purpose.
- Use `<-` for assignment, not `=`.
- Keep lines under 100 characters where practical.
- Comment non-obvious statistical choices (e.g., why a particular test or correction was selected).

### Documentation

- Write in clear, accessible English.
- Define technical terms on first use.
- When describing statistical procedures, reference the relevant literature.

## Academic Credit

If your contribution is substantial (e.g., a new analysis module, a validated instrument adaptation), we will acknowledge you as a contributor in the repository and, where appropriate, discuss co-authorship on related publications. Please indicate in your pull request if you wish to be acknowledged.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold a respectful and inclusive environment for all contributors.

## Questions

For questions about contributing, open an issue or contact the maintainers directly.
