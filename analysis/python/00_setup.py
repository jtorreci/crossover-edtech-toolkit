"""
00_setup.py
Purpose: Check Python version, import all required packages with version checks,
         set matplotlib defaults (academic style, serif fonts), create output
         directories, and define common constants and paths.
"""

import sys
import os
import importlib
from pathlib import Path

print("=== 00_setup.py: Checking environment and loading packages ===")

# --------------------------------------------------------------------------
# 1. Python version check
# --------------------------------------------------------------------------

MINIMUM_PYTHON = (3, 9)
if sys.version_info < MINIMUM_PYTHON:
    sys.exit(
        f"  Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+ is required. "
        f"You have {sys.version}."
    )

print(f"  Python version: {sys.version}")

# --------------------------------------------------------------------------
# 2. Import required packages with version checks
# --------------------------------------------------------------------------

REQUIRED_PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "statsmodels": "statsmodels",
    "pingouin": "pingouin",
    "sklearn": "scikit-learn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "factor_analyzer": "factor_analyzer",
    "krippendorff": "krippendorff",
    "openpyxl": "openpyxl",
}

missing = []
for import_name, pip_name in REQUIRED_PACKAGES.items():
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "unknown")
        print(f"  {pip_name:25s} {version}")
    except ImportError:
        missing.append(pip_name)
        print(f"  {pip_name:25s} *** NOT INSTALLED ***")

if missing:
    print(
        f"\n  Missing packages: {', '.join(missing)}\n"
        f"  Install with: pip install -r requirements.txt"
    )
    sys.exit(1)

# Now do the actual imports used throughout the pipeline
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------------------------------------------------------
# 3. Reproducibility
# --------------------------------------------------------------------------

RANDOM_SEED = 2026
np.random.seed(RANDOM_SEED)

# Suppress scientific notation in pandas
pd.set_option("display.float_format", lambda x: f"{x:.4f}")
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 120)

# --------------------------------------------------------------------------
# 4. Matplotlib defaults: clean academic style
# --------------------------------------------------------------------------

sns.set_theme(style="whitegrid", font_scale=1.1)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "figure.titlesize": 15,
    "figure.titleweight": "bold",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "legend.loc": "lower center",
    "legend.frameon": True,
    "legend.edgecolor": "0.8",
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
})

# Colour palette (colour-blind friendly, matches the R pipeline)
PALETTE = {"noAI": "#E69F00", "AI": "#009E73"}
SEQ_PALETTE = {"AB": "#0072B2", "BA": "#D55E00"}
LIKERT_COLORS = {
    "Strongly Disagree": "#d73027",
    "Disagree": "#fc8d59",
    "Neutral": "#ffffbf",
    "Agree": "#91bfdb",
    "Strongly Agree": "#4575b4",
}

# --------------------------------------------------------------------------
# 5. Directory setup
# --------------------------------------------------------------------------

# Determine project root: walk up from this script's location
_this_dir = Path(__file__).resolve().parent  # analysis/python/
PROJECT_ROOT = _this_dir.parent.parent       # crossover-edtech-toolkit/

DATA_DIR = PROJECT_ROOT / "sample_data"
OUTPUT_DIR = PROJECT_ROOT / "output"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"
MODELS_DIR = OUTPUT_DIR / "models"

# Create output directories
for d in (TABLES_DIR, FIGURES_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)

print(f"  Project root: {PROJECT_ROOT}")
print(f"  Data dir:     {DATA_DIR}")
print(f"  Output dir:   {OUTPUT_DIR}")

print("=== 00_setup.py: Complete ===\n")
