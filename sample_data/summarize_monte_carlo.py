"""
summarize_monte_carlo.py
========================

Reads the long-form Monte Carlo output produced by run_monte_carlo.py and
emits the paper-ready tables and figures for Paper 2.

Usage:
    python sample_data/summarize_monte_carlo.py
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = Path(__file__).resolve().parent / "scenario_validation"
OUT_DIR = IN_DIR / "summaries"
FIG_DIR = IN_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

DESIGNS = ["crossover_paired", "parallel_welch", "parallel_ancova"]
DESIGN_LABELS = {
    "crossover_paired": "Crossover 2x2",
    "parallel_welch":   "Parallel (Welch)",
    "parallel_ancova":  "Parallel + baseline",
}

sns.set_theme(style="whitegrid", font_scale=1.0)
plt.rcParams.update({
    "font.family": "serif",
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


def load():
    df = pd.read_csv(IN_DIR / "mc_long.csv")
    df = df[df["design"].isin(DESIGNS)].copy()
    return df


def type1_table(df):
    """Empirical type-I error at d=0, by design and key conditions."""
    null = df[df["d"] == 0].copy()
    # Default cell (everything at mid-noise, no extras) for clean type-I
    base = null[(null["pi"] == 3.0) & (null["lam"] == 0.0)
                & (null["sigma_s"] == 10.0) & (null["sigma_e"] == 7.0)
                & (null["task_ineq"] == 0.0) & (null["attrition"] == 0.0)]
    tbl = base.pivot_table(index="n", columns="design", values="rej_rate"
                           if "rej_rate" in base.columns else "power")
    tbl = tbl.rename(columns=DESIGN_LABELS)
    tbl.to_csv(OUT_DIR / "table_type1.csv")
    return tbl


def power_curves(df):
    """Power curves by N, one panel per d, lines per design.
    Holds noise/period/carryover at their middle defaults."""
    base = df[(df["pi"] == 3.0) & (df["lam"] == 0.0)
              & (df["sigma_s"] == 10.0) & (df["sigma_e"] == 7.0)
              & (df["task_ineq"] == 0.0) & (df["attrition"] == 0.0)
              & (df["d"] > 0)]

    ds = sorted(base["d"].unique())
    fig, axes = plt.subplots(1, len(ds), figsize=(4 * len(ds), 3.6),
                             sharey=True)
    if len(ds) == 1:
        axes = [axes]
    for ax, d in zip(axes, ds):
        sub = base[base["d"] == d]
        for design in DESIGNS:
            piece = sub[sub["design"] == design].sort_values("n")
            metric = "rej_rate" if "rej_rate" in piece.columns else "power"
            ax.plot(piece["n"], piece[metric], marker="o",
                    label=DESIGN_LABELS[design])
        ax.axhline(0.80, color="grey", lw=0.7, ls="--")
        ax.set_xlabel("Sample size (N)")
        ax.set_title(f"Cohen's d = {d}")
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("Statistical power")
    axes[-1].legend(loc="lower right", fontsize=8)
    fig.suptitle("Power as a function of N, by design", y=1.02)
    fig.savefig(FIG_DIR / "power_curves.pdf")
    fig.savefig(FIG_DIR / "power_curves.png")
    plt.close(fig)

    # Also save the underlying table
    metric = "rej_rate" if "rej_rate" in base.columns else "power"
    tbl = base.pivot_table(index=["d", "n"], columns="design", values=metric)
    tbl = tbl.rename(columns=DESIGN_LABELS).reset_index()
    tbl.to_csv(OUT_DIR / "table_power_main.csv", index=False)
    return tbl


def min_n_for_power_80(df):
    """Smallest N achieving >=0.80 power by design at d in {0.3, 0.5}."""
    base = df[(df["pi"] == 3.0) & (df["lam"] == 0.0)
              & (df["sigma_s"] == 10.0) & (df["sigma_e"] == 7.0)
              & (df["task_ineq"] == 0.0) & (df["attrition"] == 0.0)]
    metric = "rej_rate" if "rej_rate" in base.columns else "power"
    rows = []
    for d in (0.2, 0.3, 0.5):
        for design in DESIGNS:
            piece = base[(base["d"] == d) & (base["design"] == design)]
            piece = piece.sort_values("n")
            ok = piece[piece[metric] >= 0.80]
            row = {"d": d, "design": DESIGN_LABELS[design]}
            row["min_n"] = int(ok.iloc[0]["n"]) if not ok.empty else None
            row["max_power_in_grid"] = float(piece[metric].max())
            rows.append(row)
    tbl = pd.DataFrame(rows)
    tbl.to_csv(OUT_DIR / "table_min_n_power80.csv", index=False)
    return tbl


def bias_and_coverage(df):
    """Bias and coverage by design and condition. Includes a stress test
    under non-zero carryover for the crossover."""
    nonzero = df[df["d"] > 0].copy()
    # Aggregate over the full grid
    g = (nonzero
         .groupby(["design", "d"])
         .agg(bias_mean=("bias", "mean"),
              bias_abs=("bias", lambda x: float(np.abs(x).mean())),
              coverage=("coverage", "mean"),
              rmse=("rmse", "mean"))
         .reset_index())
    g["design"] = g["design"].map(DESIGN_LABELS)
    g.to_csv(OUT_DIR / "table_bias_coverage.csv", index=False)
    return g


def carryover_operating(df):
    """Power of Grizzle test as carryover increases, at N in {30, 50, 100}."""
    car = df[(df["design"] == "carryover_test") if "carryover_test" in df["design"].unique() else df["design"] == DESIGNS[0]]
    # We have to read carryover power from the raw long file (carryover_test design)
    raw = pd.read_csv(IN_DIR / "mc_long.csv")
    car = raw[raw["design"] == "carryover_test"]
    base = car[(car["sigma_s"] == 10.0) & (car["sigma_e"] == 7.0)
               & (car["task_ineq"] == 0.0) & (car["attrition"] == 0.0)
               & (car["d"] == 0.3) & (car["pi"] == 3.0)]
    tbl = base.pivot_table(index="lam", columns="n", values="power")
    tbl.to_csv(OUT_DIR / "table_carryover_power.csv")
    return tbl


def attrition_degradation(df):
    """How power degrades with attrition, for each design, at d=0.3, N=50."""
    base = df[(df["d"] == 0.3) & (df["n"] == 50)
              & (df["pi"] == 3.0) & (df["lam"] == 0.0)
              & (df["sigma_s"] == 10.0) & (df["sigma_e"] == 7.0)
              & (df["task_ineq"] == 0.0)]
    metric = "rej_rate" if "rej_rate" in base.columns else "power"
    tbl = base.pivot_table(index="attrition", columns="design",
                            values=metric)
    tbl = tbl.rename(columns=DESIGN_LABELS)
    tbl.to_csv(OUT_DIR / "table_attrition.csv")

    fig, ax = plt.subplots(figsize=(5, 3.5))
    for c in tbl.columns:
        ax.plot(tbl.index, tbl[c], marker="o", label=c)
    ax.set_xlabel("Attrition rate")
    ax.set_ylabel("Power")
    ax.set_title("Power degradation with attrition\n(N=50, d=0.3)")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.02)
    fig.savefig(FIG_DIR / "attrition.pdf")
    fig.savefig(FIG_DIR / "attrition.png")
    plt.close(fig)
    return tbl


def crossover_under_carryover(df):
    """Crossover bias and coverage as carryover increases. Stress test."""
    base = df[(df["design"] == "crossover_paired") & (df["d"] == 0.3)
              & (df["n"] == 50) & (df["pi"] == 3.0)
              & (df["sigma_s"] == 10.0) & (df["sigma_e"] == 7.0)
              & (df["task_ineq"] == 0.0) & (df["attrition"] == 0.0)]
    tbl = base[["lam", "bias", "coverage", "rmse"]].sort_values("lam")
    tbl.to_csv(OUT_DIR / "table_crossover_carryover.csv", index=False)
    return tbl


def main():
    df = load()
    print(f"Loaded {len(df)} rows.")

    print("\n=== Type-I error (d=0, mid defaults) ===")
    print(type1_table(df).round(3).to_string())

    print("\n=== Power curves ===")
    print(power_curves(df).round(3).to_string(index=False))

    print("\n=== Minimum N for power >= 0.80 ===")
    print(min_n_for_power_80(df).to_string(index=False))

    print("\n=== Bias / coverage / RMSE ===")
    print(bias_and_coverage(df).round(3).to_string(index=False))

    print("\n=== Carryover-test power vs lambda (d=0.3) ===")
    print(carryover_operating(df).round(3).to_string())

    print("\n=== Attrition degradation (N=50, d=0.3) ===")
    print(attrition_degradation(df).round(3).to_string())

    print("\n=== Crossover under increasing carryover (stress test) ===")
    print(crossover_under_carryover(df).round(3).to_string(index=False))

    print(f"\nAll outputs in: {OUT_DIR}")
    print(f"Figures in:      {FIG_DIR}")


if __name__ == "__main__":
    main()
