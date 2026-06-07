"""
run_monte_carlo.py
==================

Vectorised Monte Carlo runner for Paper 2.

For each cell of a scenario grid (sample size, treatment effect, period
effect, carryover, between- and within-subject variance, task inequality,
attrition) it simulates k cohorts and compares three designs:

  - Crossover 2x2  (paired t-test on within-subject differences)
  - Parallel       (Welch two-sample t-test, no baseline)
  - Parallel+ANCOVA(two-sample comparison with baseline covariate)

For each (cell, design) tuple it reports power, type-I error, bias,
coverage of the nominal 95% CI, and root mean squared error of the
treatment estimator. The crossover branch additionally reports the
operating characteristics of the Grizzle carryover test.

Usage
-----

    python sample_data/run_monte_carlo.py                # full grid, k=1000
    python sample_data/run_monte_carlo.py --reps 200     # pilot
    python sample_data/run_monte_carlo.py --quick        # one-axis sweep

Outputs
-------

    sample_data/scenario_validation/mc_long.csv     - one row per metric
    sample_data/scenario_validation/mc_summary.csv  - pivoted, paper-ready
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent / "scenario_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Scenario grid (matches Paper 2 Section "Scenario Grid")
# ---------------------------------------------------------------------------

GRID = {
    "n":          [30, 50, 75, 100, 150],
    "d":          [0.0, 0.20, 0.30, 0.50],
    "pi":         [0.0, 3.0, 7.0],          # period effect (raw units, sd=10)
    "lam":        [0.0, 2.0, 4.0],          # carryover (raw units)
    "sigma_s":    [6.0, 10.0, 14.0],        # between-subject SD
    "sigma_e":    [4.0, 7.0, 10.0],         # within-subject SD
    "task_ineq":  [0.0, 4.0],               # mean shift period 2 vs 1
    "attrition":  [0.0, 0.05, 0.10],
}

# Quick mode: only varies n and d, holds everything else at the middle.
QUICK_GRID = {
    "n":          [30, 50, 75, 100, 150],
    "d":          [0.0, 0.20, 0.30, 0.50],
    "pi":         [3.0],
    "lam":        [0.0],
    "sigma_s":    [10.0],
    "sigma_e":    [7.0],
    "task_ineq":  [0.0],
    "attrition":  [0.0],
}


# ---------------------------------------------------------------------------
# Data-generating process
# ---------------------------------------------------------------------------

def simulate_cell(*, n, d, pi, lam, sigma_s, sigma_e, task_ineq, attrition,
                  reps, rng):
    """Generate `reps` synthetic cohorts of `n` participants under the
    crossover model. Returns:

        Y         (reps, n, 2)  per-subject responses, periods 1 and 2
        seq       (reps, n)     0 = AB sequence, 1 = BA sequence
        cond      (reps, n, 2)  0 = noAI, 1 = AI
        obs       (reps, n, 2)  1 = observed, 0 = dropped by attrition

    The treatment effect is expressed in standardized units (d) and rescaled
    by the total SD of the responses, sqrt(sigma_s^2 + sigma_e^2), so that
    the Cohen's d parameter is interpretable across noise settings.
    """
    sd_total = float(np.sqrt(sigma_s ** 2 + sigma_e ** 2))
    tau = d * sd_total  # treatment effect in raw points

    # Subject random intercepts
    s = rng.normal(loc=0.0, scale=sigma_s, size=(reps, n))

    # Sequence assignment: balanced, alternating
    seq = np.tile(np.array([0, 1]), reps=(reps, (n + 1) // 2))[:, :n]
    # Shuffle within-replicate to avoid order bias
    perm = rng.permuted(np.arange(n)[None, :].repeat(reps, axis=0), axis=1)
    seq = np.take_along_axis(seq, perm, axis=1)

    # Conditions per period: AB -> (noAI, AI), BA -> (AI, noAI)
    cond_p1 = seq                       # 0 if AB, 1 if BA
    cond_p2 = 1 - seq                   # opposite
    cond = np.stack([cond_p1, cond_p2], axis=-1)

    # Period effect: 0 in P1, pi in P2 (linear period shift)
    period_eff = np.array([0.0, pi])    # shape (2,)

    # Carryover: present only in period 2 for sequences that received AI in P1
    # i.e. seq=BA (had AI first). Apply lam to AI->noAI transition (P2 of BA).
    carryover_p2 = lam * seq            # active in P2 if BA (=1), else 0

    # Task inequality: shift on period 2 only (a "harder" or "easier" period 2)
    task_eff_p2 = task_ineq

    # Compose response means by period
    mu_p1 = s + period_eff[0] + tau * cond_p1
    mu_p2 = s + period_eff[1] + tau * cond_p2 + carryover_p2 + task_eff_p2

    # Within-subject noise
    eps = rng.normal(loc=0.0, scale=sigma_e, size=(reps, n, 2))
    Y = np.stack([mu_p1, mu_p2], axis=-1) + eps

    # Attrition: random drop-outs by observation
    if attrition > 0:
        obs = (rng.random(size=Y.shape) >= attrition).astype(np.int8)
    else:
        obs = np.ones_like(Y, dtype=np.int8)

    # For ANCOVA we also need a "pre-test" score uncorrelated with treatment.
    # Generate one per subject, correlated with the subject effect.
    pre = s + rng.normal(loc=0.0, scale=sigma_e, size=(reps, n))

    return Y, seq, cond, obs, pre, tau


# ---------------------------------------------------------------------------
# Estimators (vectorised over replicates)
# ---------------------------------------------------------------------------

def paired_ttest(Y, cond, obs):
    """Crossover paired contrast: for each subject, AI minus noAI score.
    Uses both periods. Skips subjects with any missing observation."""
    # Pull AI and noAI scores per subject
    ai_score = np.where(cond == 1, Y, np.nan)
    no_score = np.where(cond == 0, Y, np.nan)
    # Reduce across the 2 periods (each subject has exactly one of each)
    ai = np.nanmean(np.where(obs == 1, ai_score, np.nan), axis=2)   # (reps, n)
    no = np.nanmean(np.where(obs == 1, no_score, np.nan), axis=2)
    diff = ai - no
    valid = np.isfinite(diff)  # subjects with both observed

    # Per-replicate paired t on the surviving subjects
    n_sub = valid.sum(axis=1)
    mean = np.where(n_sub > 0, np.nansum(np.where(valid, diff, 0.0), axis=1) / np.maximum(n_sub, 1), np.nan)
    # variance
    diff_c = np.where(valid, diff - mean[:, None], 0.0)
    var = np.where(n_sub > 1, (diff_c ** 2).sum(axis=1) / np.maximum(n_sub - 1, 1), np.nan)
    se = np.sqrt(var / np.maximum(n_sub, 1))
    t = mean / se
    df = n_sub - 1
    # two-sided p-value
    p = 2.0 * stats.t.sf(np.abs(t), df=df)
    # 95% CI
    crit = stats.t.ppf(0.975, df=df)
    lo = mean - crit * se
    hi = mean + crit * se
    return mean, lo, hi, p


def parallel_ttest(Y, cond, obs):
    """Parallel design: take period-1 observations only.
       Two groups: those with cond_p1==0 (noAI) vs cond_p1==1 (AI).
       Welch two-sample t-test, per replicate."""
    y_p1 = Y[..., 0]                # (reps, n)
    obs_p1 = obs[..., 0].astype(bool)
    c_p1 = cond[..., 0]
    g_no = obs_p1 & (c_p1 == 0)
    g_ai = obs_p1 & (c_p1 == 1)

    n_no = g_no.sum(axis=1).astype(float)
    n_ai = g_ai.sum(axis=1).astype(float)
    sum_no = np.where(g_no, y_p1, 0.0).sum(axis=1)
    sum_ai = np.where(g_ai, y_p1, 0.0).sum(axis=1)
    m_no = sum_no / np.maximum(n_no, 1)
    m_ai = sum_ai / np.maximum(n_ai, 1)
    sq_no = (np.where(g_no, y_p1 - m_no[:, None], 0.0) ** 2).sum(axis=1)
    sq_ai = (np.where(g_ai, y_p1 - m_ai[:, None], 0.0) ** 2).sum(axis=1)
    var_no = sq_no / np.maximum(n_no - 1, 1)
    var_ai = sq_ai / np.maximum(n_ai - 1, 1)

    mean = m_ai - m_no
    se = np.sqrt(var_no / np.maximum(n_no, 1) + var_ai / np.maximum(n_ai, 1))
    # Welch df
    df = (var_no / n_no + var_ai / n_ai) ** 2 / (
        (var_no / n_no) ** 2 / np.maximum(n_no - 1, 1) +
        (var_ai / n_ai) ** 2 / np.maximum(n_ai - 1, 1)
    )
    t = np.where(se > 0, mean / se, 0.0)
    p = 2.0 * stats.t.sf(np.abs(t), df=np.maximum(df, 1.0))
    crit = stats.t.ppf(0.975, df=np.maximum(df, 1.0))
    lo = mean - crit * se
    hi = mean + crit * se
    return mean, lo, hi, p


def parallel_ancova(Y, cond, obs, pre):
    """Parallel + baseline covariate (ANCOVA). Per replicate, fit
       y_p1 = b0 + b1 * group + b2 * pre. Use the b1 estimate."""
    y_p1 = Y[..., 0]                # (reps, n)
    obs_p1 = obs[..., 0].astype(bool)
    g = cond[..., 0]                # group indicator

    reps, n = y_p1.shape
    # Vectorised OLS per replicate
    out_est = np.empty(reps)
    out_lo = np.empty(reps)
    out_hi = np.empty(reps)
    out_p = np.empty(reps)
    for r in range(reps):
        m = obs_p1[r]
        if m.sum() < 5:
            out_est[r] = out_lo[r] = out_hi[r] = np.nan
            out_p[r] = 1.0
            continue
        X = np.column_stack([np.ones(m.sum()), g[r, m], pre[r, m]])
        y = y_p1[r, m]
        try:
            beta, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
            yhat = X @ beta
            resid = y - yhat
            dof = len(y) - X.shape[1]
            if dof < 1:
                out_est[r] = out_lo[r] = out_hi[r] = np.nan
                out_p[r] = 1.0
                continue
            mse = float(np.sum(resid ** 2) / dof)
            cov = mse * np.linalg.inv(X.T @ X)
            se = float(np.sqrt(cov[1, 1]))
            est = float(beta[1])
            crit = stats.t.ppf(0.975, df=dof)
            out_est[r] = est
            out_lo[r] = est - crit * se
            out_hi[r] = est + crit * se
            t_stat = est / se if se > 0 else 0.0
            out_p[r] = 2.0 * stats.t.sf(abs(t_stat), df=dof)
        except np.linalg.LinAlgError:
            out_est[r] = out_lo[r] = out_hi[r] = np.nan
            out_p[r] = 1.0
    return out_est, out_lo, out_hi, out_p


def grizzle_test(Y, seq, obs):
    """Carryover test as a two-sample t-test on the sum of period-1+period-2
    scores, grouped by sequence (AB vs BA)."""
    both = (obs[..., 0] & obs[..., 1]).astype(bool)
    total = Y[..., 0] + Y[..., 1]
    g_ab = both & (seq == 0)
    g_ba = both & (seq == 1)
    n_ab = g_ab.sum(axis=1).astype(float)
    n_ba = g_ba.sum(axis=1).astype(float)
    m_ab = np.where(g_ab, total, 0.0).sum(axis=1) / np.maximum(n_ab, 1)
    m_ba = np.where(g_ba, total, 0.0).sum(axis=1) / np.maximum(n_ba, 1)
    sq_ab = (np.where(g_ab, total - m_ab[:, None], 0.0) ** 2).sum(axis=1)
    sq_ba = (np.where(g_ba, total - m_ba[:, None], 0.0) ** 2).sum(axis=1)
    var_ab = sq_ab / np.maximum(n_ab - 1, 1)
    var_ba = sq_ba / np.maximum(n_ba - 1, 1)
    diff = m_ba - m_ab
    se = np.sqrt(var_ab / np.maximum(n_ab, 1) + var_ba / np.maximum(n_ba, 1))
    df = (var_ab / n_ab + var_ba / n_ba) ** 2 / (
        (var_ab / n_ab) ** 2 / np.maximum(n_ab - 1, 1) +
        (var_ba / n_ba) ** 2 / np.maximum(n_ba - 1, 1)
    )
    t = np.where(se > 0, diff / se, 0.0)
    p = 2.0 * stats.t.sf(np.abs(t), df=np.maximum(df, 1.0))
    return diff, p


# ---------------------------------------------------------------------------
# Metric aggregation
# ---------------------------------------------------------------------------

def cell_metrics(true_tau, est, lo, hi, p, alpha=0.05):
    rej = (p < alpha).astype(float)
    cov = ((lo <= true_tau) & (true_tau <= hi)).astype(float)
    bias = est - true_tau
    rmse = np.sqrt(np.nanmean(bias ** 2))
    mc_se_power = float(np.sqrt(rej.mean() * (1 - rej.mean()) / len(rej)))
    return {
        "power":      float(rej.mean()),
        "type1":      float(rej.mean()),   # same arithmetic; interpreted under d=0
        "bias":       float(np.nanmean(bias)),
        "coverage":   float(np.nanmean(cov)),
        "rmse":       float(rmse),
        "mc_se":      mc_se_power,
        "n_valid":    int(np.isfinite(est).sum()),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_cell(params, reps, rng):
    Y, seq, cond, obs, pre, tau = simulate_cell(reps=reps, rng=rng, **params)

    metrics = {}

    est, lo, hi, p = paired_ttest(Y, cond, obs)
    m = cell_metrics(tau, est, lo, hi, p)
    metrics["crossover_paired"] = m

    est, lo, hi, p = parallel_ttest(Y, cond, obs)
    m = cell_metrics(tau, est, lo, hi, p)
    metrics["parallel_welch"] = m

    est, lo, hi, p = parallel_ancova(Y, cond, obs, pre)
    m = cell_metrics(tau, est, lo, hi, p)
    metrics["parallel_ancova"] = m

    # Grizzle carryover test (under H0 lam=0 it should reject ~5%)
    _, p_car = grizzle_test(Y, seq, obs)
    p_car_clean = p_car[np.isfinite(p_car)]
    metrics["carryover_test"] = {
        "power": float((p_car_clean < 0.05).mean()),
        "n_valid": int(len(p_car_clean)),
    }
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reps", type=int, default=1000,
                        help="Monte Carlo replications per cell")
    parser.add_argument("--quick", action="store_true",
                        help="Use the reduced grid (varies n and d only)")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    grid = QUICK_GRID if args.quick else GRID
    cells = list(itertools.product(*grid.values()))
    keys = list(grid.keys())
    print(f"Grid cells: {len(cells)}  reps per cell: {args.reps}")
    print(f"Total fits per design: {len(cells) * args.reps:,}")

    rng = np.random.default_rng(args.seed)

    rows = []
    t_start = time.time()
    last = t_start

    for i, values in enumerate(cells):
        params = dict(zip(keys, values))
        m = run_cell(params, args.reps, rng)
        for design, met in m.items():
            row = {**params, "design": design, **met}
            rows.append(row)

        # Progress every ~30s
        now = time.time()
        if now - last >= 30 or i == len(cells) - 1:
            done = i + 1
            elapsed = now - t_start
            eta = elapsed / done * (len(cells) - done)
            print(f"  cell {done}/{len(cells)}  "
                  f"elapsed {elapsed:.1f}s  ETA {eta:.0f}s",
                  flush=True)
            last = now

    df = pd.DataFrame(rows)
    out_long = OUT_DIR / ("mc_long_quick.csv" if args.quick else "mc_long.csv")
    df.to_csv(out_long, index=False)
    print(f"\nWrote {out_long} ({len(df)} rows)")

    # Compact summary: pivot the main metrics
    summary_metrics = ["power", "coverage", "bias", "rmse", "mc_se"]
    summary_keys = keys + ["design"]
    summary = df[summary_keys + summary_metrics].copy()
    summary.rename(columns={"power": "rej_rate"}, inplace=True)
    out_summary = OUT_DIR / ("mc_summary_quick.csv" if args.quick
                             else "mc_summary.csv")
    summary.to_csv(out_summary, index=False)
    print(f"Wrote {out_summary}")

    total_min = (time.time() - t_start) / 60.0
    print(f"\nTotal runtime: {total_min:.1f} min")


if __name__ == "__main__":
    main()
