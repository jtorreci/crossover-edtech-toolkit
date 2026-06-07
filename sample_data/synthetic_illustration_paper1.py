"""
synthetic_illustration_paper1.py
================================

Generates the 3-scenario pipeline validation used in Paper 1's
"Illustration with synthetic data" section. It exercises the analytical
pipeline on three single, representative synthetic datasets with KNOWN
parameters, and checks that the pipeline recovers what was programmed:

  S0  Null            tau = 0,  lambda = 0  -> nothing should be detected
  S1  Treatment-only  tau > 0,  lambda = 0  -> full and period-1 estimates agree
  S2  Carryover       tau > 0,  lambda > 0  -> full estimate biased; the
                                               carryover-immune period-1
                                               estimate recovers tau

The conditions are labelled generically (A reference, B active). The sign
and size of the effect are arbitrary design parameters chosen to exercise
the machinery; they carry NO empirical interpretation (the real results
live in the empirical paper).

Reuses the exact DGP and Grizzle test from Paper 2's Monte Carlo engine so
the illustration is consistent with the companion simulation.

    python sample_data/synthetic_illustration_paper1.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from run_monte_carlo import simulate_cell, grizzle_test

OUT_DIR = Path(__file__).resolve().parent / "scenario_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIGMA_S, SIGMA_E, PI = 12.0, 8.0, 3.0
SD_TOTAL = float(np.sqrt(SIGMA_S ** 2 + SIGMA_E ** 2))
N = 100
TAU = 8.0          # true effect magnitude (arbitrary, neutral)
LAM = 10.0         # carryover for S2 (~0.69 sigma)
GRAND = 65.0

SCENARIOS = {
    "S0 Null":           dict(d=0.0,            lam=0.0, seed=101),
    "S1 Treatment-only": dict(d=TAU / SD_TOTAL, lam=0.0, seed=102),
    "S2 Carryover":      dict(d=TAU / SD_TOTAL, lam=LAM, seed=103),
}


def analyse(d, lam, seed):
    rng = np.random.default_rng(seed)
    Y, seq, cond, obs, pre, tau = simulate_cell(
        n=N, d=d, pi=PI, lam=lam, sigma_s=SIGMA_S, sigma_e=SIGMA_E,
        task_ineq=0.0, attrition=0.0, reps=1, rng=rng)
    Y = Y + GRAND                       # shift to a realistic mean (no effect on contrasts)
    Y0, cond0, seq0 = Y[0], cond[0], seq[0]

    # Per-subject A (reference) and B (active) scores
    b_sub = np.nanmean(np.where(cond0 == 1, Y0, np.nan), axis=1)
    a_sub = np.nanmean(np.where(cond0 == 0, Y0, np.nan), axis=1)
    diff = b_sub - a_sub

    # Full crossover paired estimate (B - A)
    t_p, p_p = stats.ttest_rel(b_sub, a_sub)
    _, w_p = stats.wilcoxon(b_sub, a_sub)
    dz = float(diff.mean() / diff.std(ddof=1))

    # Grizzle carryover test (between sequences, on period sums)
    obs1 = np.ones_like(Y0, dtype=np.int8)[None]
    _, gp = grizzle_test(Y0[None], seq0[None], obs1)
    grizzle_p = float(gp[0])

    # Carryover-immune period-1 parallel estimate
    c1, y1 = cond0[:, 0], Y0[:, 0]
    g_b, g_a = y1[c1 == 1], y1[c1 == 0]
    t1, p1 = stats.ttest_ind(g_b, g_a, equal_var=False)

    return {
        "true_tau": round(float(tau), 2),
        "mean_A": round(float(a_sub.mean()), 1),
        "mean_B": round(float(b_sub.mean()), 1),
        "full_estimate_B_minus_A": round(float(diff.mean()), 2),
        "full_t": round(float(t_p), 2),
        "full_p": round(float(p_p), 4),
        "wilcoxon_p": round(float(w_p), 4),
        "full_dz": round(dz, 2),
        "grizzle_p": round(grizzle_p, 4),
        "period1_estimate_B_minus_A": round(float(g_b.mean() - g_a.mean()), 2),
        "period1_t": round(float(t1), 2),
        "period1_p": round(float(p1), 4),
    }


def main():
    rows = []
    for name, cfg in SCENARIOS.items():
        res = analyse(cfg["d"], cfg["lam"], cfg["seed"])
        res = {"scenario": name, "programmed_lambda": cfg["lam"], **res}
        rows.append(res)

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)
    print(f"N = {N} per scenario; sigma_s = {SIGMA_S}, sigma_e = {SIGMA_E} "
          f"(total {SD_TOTAL:.2f}); period effect = {PI}; true tau = {TAU}")
    print(f"S2 carryover lambda = {LAM} ({LAM / SD_TOTAL:.2f} sigma)\n")
    print(df.to_string(index=False))
    df.to_csv(OUT_DIR / "synthetic_illustration_paper1.csv", index=False)
    print(f"\nWrote {OUT_DIR / 'synthetic_illustration_paper1.csv'}")


if __name__ == "__main__":
    main()
