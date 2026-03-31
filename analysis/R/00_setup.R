# ==============================================================================
# 00_setup.R
# Purpose: Install (if needed) and load all required packages for the
#          crossover-edtech-toolkit analysis pipeline.
# ==============================================================================

cat("=== 00_setup.R: Installing and loading packages ===\n")

# List of required packages
required_packages <- c(

  "tidyverse",    # Data wrangling, ggplot2, dplyr, tidyr, readr, purrr, etc.
  "lme4",         # Linear mixed-effects models
  "lmerTest",     # p-values for lmer models (Satterthwaite approximation)
  "emmeans",      # Estimated marginal means and pairwise comparisons
  "effectsize",   # Cohen's d, eta-squared, and other effect sizes
  "psych",        # Cronbach's alpha, descriptive statistics
  "irr",          # Inter-rater reliability (ICC, kappa)
  "likert",       # Likert scale analysis and visualization
  "ggplot2",      # Grammar of graphics (also loaded via tidyverse)
  "car",          # Levene's test, Type III SS ANOVA
  "rstatix",      # Pipe-friendly statistical tests
  "knitr",        # Table formatting
  "kableExtra",   # Enhanced table formatting
  "scales",       # Axis formatting for plots
  "patchwork",    # Combine multiple ggplots
  "RColorBrewer"  # Color palettes for visualizations
)

# Install missing packages
install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(paste0("  Installing: ", pkg, "\n"))
    install.packages(pkg, repos = "https://cran.r-project.org", quiet = TRUE)
  }
}

invisible(lapply(required_packages, install_if_missing))

# Load all packages
invisible(lapply(required_packages, function(pkg) {
  suppressPackageStartupMessages(library(pkg, character.only = TRUE))
}))

# --------------------------------------------------------------------------
# Global options
# --------------------------------------------------------------------------

# Reproducibility
set.seed(2026)

# Suppress scientific notation for readability
options(scipen = 999)

# ggplot2 global theme: clean academic style
theme_crossover <- theme_minimal(base_size = 12) +
  theme(
    plot.title       = element_text(face = "bold", hjust = 0.5),
    plot.subtitle    = element_text(hjust = 0.5, color = "grey40"),
    panel.grid.minor = element_blank(),
    legend.position  = "bottom",
    strip.text       = element_text(face = "bold")
  )
theme_set(theme_crossover)

# --------------------------------------------------------------------------
# Directory setup
# --------------------------------------------------------------------------

# Determine project root (assumes scripts are run from the project root
# or via source() from the project root)
if (!exists("PROJECT_ROOT")) {
  # Try to detect project root from script location
  PROJECT_ROOT <- tryCatch({
    script_dir <- dirname(sys.frame(1)$ofile)
    normalizePath(file.path(script_dir, "..", ".."), winslash = "/")
  }, error = function(e) {
    normalizePath(".", winslash = "/")
  })
}

DATA_DIR   <- file.path(PROJECT_ROOT, "sample_data")
OUTPUT_DIR <- file.path(PROJECT_ROOT, "output")

# Create output directories if they don't exist
dir.create(file.path(OUTPUT_DIR, "tables"),  recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(OUTPUT_DIR, "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(OUTPUT_DIR, "models"),  recursive = TRUE, showWarnings = FALSE)

cat(paste0("  Project root: ", PROJECT_ROOT, "\n"))
cat(paste0("  Data dir:     ", DATA_DIR, "\n"))
cat(paste0("  Output dir:   ", OUTPUT_DIR, "\n"))

cat("=== 00_setup.R: Complete ===\n\n")
