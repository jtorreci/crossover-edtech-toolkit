"""
calibrate_empirical.py
======================

A-posteriori calibration of the Paper 2 Monte Carlo against the empirical
pilot (UEx crossover study, companion empirical paper).

The scenario grid in run_monte_carlo.py is generic (standardized effect
sizes on a raw-point scale with sigma_s in 6..14 and sigma_e in 4..10).
This script does the opposite move: it reads the *observed* variance
structure and effect magnitude from the real dataset, plugs them into the
exact same data-generating process and estimators, and reports the
operating characteristics the design actually had on the pilot.

It answers two questions a reviewer (and the investigator) will ask:

  1. Are the empirical estimates an artefact of an underpowered design or
     an inflated test?  -> power, type-I, coverage at the observed params.
  2. Does the simulation "capture the data"?  -> the design at the observed
     parameters reproduces near-certain detection of an effect this large,
     and the Grizzle test's detection rate at the observed carryover
     magnitude is consistent with the significant Grizzle we report.

The empirical parameters are ESTIMATED here from the real data via the same
linear mixed model used in analysis/python/05_mixed_anova.py, so nothing is
hand-entered. Run:

    python sample_data/calibrate_empirical.py
    python sample_data/calibrate_empirical.py --reps 5000

Outputs:
    sample_data/scenario_validation/calibration_empirical.csv
    sample_data/scenario_validation/calibration_params.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the EXACT DGP, estimators and metric aggregation from the main runner
from run_monte_carlo import (
    simulate_cell,
    paired_ttest,
    parallel_ttest,
    parallel_ancova,
    grizzle_test,
    cell_metrics,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent / "scenario_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Real cleaned dataset produced by the empirical pipeline.
REAL_DATA = ROOT / "real_output" / "df_clean.csv"


# ---------------------------------------------------------------------------
# Step 1 - estimate empirical parameters from the real data
# ---------------------------------------------------------------------------

def estimate_empirical_params():
    """Fit the same LMM as 05_mixed_anova.py and read off the parameters the
    Monte Carlo DGP needs: between-subject SD, within-subject SD, treatment
    effect, period effect, and carryover magnitude.

    Returns a dict of raw-scale parameters (0-100 rubric-derived score).
    """
    import statsmodels.formula.api as smf

    df = pd.read_csv(REAL_DATA)
    df = df.dropna(subset=["score"]).copy()

    df["cond_num"] = (df["condition"] == "AI").astype(int)
    df["period_num"] = df["period"].map({"Period 1": 1, "Period 2": 2}).astype(float)
    df["seq_num"] = (df["sequence"] == "BA").astype(int)

    fit = smf.mixedlm(
        "score ~ cond_num + period_num + seq_num",
        data=df,
        groups=df["participant_id"],
    ).fit(reml=True)

    # Variance components
    sigma_s = float(np.sqrt(fit.cov_re.iloc[0, 0]))   # random intercept SD
    sigma_e = float(np.sqrt(fit.scale))               # residual SD

    # Fixed effects (raw score points)
    tau = float(fit.fe_params["cond_num"])            # AI - noAI (negative)
    pi = float(fit.fe_params["period_num"])           # per-period shift
    seq_eff = float(fit.fe_params["seq_num"])         # BA - AB main effect

    # Carryover magnitude for the DGP. In a balanced 2x2 the sequence main
    # effect on subject means equals lam/2, so the raw P2 carryover shift is
    # ~ 2 * sequence effect. We also cross-check against the Grizzle sum
    # contrast reported in the empirical pipeline (BA - AB on period sums).
    lam = 2.0 * abs(seq_eff)

    sd_total = float(np.sqrt(sigma_s ** 2 + sigma_e ** 2))
    d_implied = abs(tau) / sd_total

    return {
        "sigma_s": sigma_s,
        "sigma_e": sigma_e,
        "sd_total": sd_total,
        "tau_raw": tau,
        "d_implied": d_implied,
        "pi": pi,
        "seq_eff": seq_eff,
        "lam": lam,
        "n_obs": int(len(df)),
        "n_subjects": int(df["participant_id"].nunique()),
    }


# ---------------------------------------------------------------------------
# Step 2 - run the calibrated Monte Carlo
# ---------------------------------------------------------------------------

def run_calibrated(params, *, n, d, lam, reps, rng):
    """Run one calibrated cell with the empirical noise structure. Tests are
    two-sided, so the sign of the effect is irrelevant to power/coverage; we
    pass |d| (d_implied)."""
    cell = dict(
        n=n,
        d=d,
        pi=params["pi"],
        lam=lam,
        sigma_s=params["sigma_s"],
        sigma_e=params["sigma_e"],
        task_ineq=0.0,
        attrition=0.0,
    )
    Y, seq, cond, obs, pre, tau = simulate_cell(reps=reps, rng=rng, **cell)

    est, lo, hi, p = paired_ttest(Y, cond, obs)
    m_cross = cell_metrics(tau, est, lo, hi, p)

    est, lo, hi, p = parallel_ttest(Y, cond, obs)
    m_par = cell_metrics(tau, est, lo, hi, p)

    est, lo, hi, p = parallel_ancova(Y, cond, obs, pre)
    m_anc = cell_metrics(tau, est, lo, hi, p)

    _, p_car = grizzle_test(Y, seq, obs)
    p_car = p_car[np.isfinite(p_car)]
    grizzle_power = float((p_car < 0.05).mean())

    return m_cross, m_par, m_anc, grizzle_power


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reps", type=int, default=3000,
                        help="Monte Carlo replications per calibrated cell")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    print("=== Empirical calibration of the Paper 2 Monte Carlo ===\n")

    p = estimate_empirical_params()
    print("Estimated empirical parameters (raw 0-100 score scale):")
    print(f"  between-subject SD  sigma_s = {p['sigma_s']:.2f}")
    print(f"  within-subject SD   sigma_e = {p['sigma_e']:.2f}")
    print(f"  total SD                     = {p['sd_total']:.2f}")
    print(f"  treatment effect    tau      = {p['tau_raw']:.2f} (AI - noAI, raw points)")
    print(f"  implied Cohen's d            = {p['d_implied']:.3f}")
    print(f"  period effect       pi       = {p['pi']:.2f}")
    print(f"  sequence effect              = {p['seq_eff']:.2f}")
    print(f"  carryover (DGP)     lam      = {p['lam']:.2f}")
    print(f"  observed n subjects          = {p['n_subjects']}  ({p['n_obs']} obs)\n")

    pd.DataFrame([p]).to_csv(OUT_DIR / "calibration_params.csv", index=False)

    rng = np.random.default_rng(args.seed)

    # The observed carryover is enormous (lam ~ 1.1 sigma), far beyond the
    # 0.4-sigma ceiling the grid study flags as the point where the paired
    # estimator stops being trustworthy. We therefore report TWO regimes,
    # never conflating them:
    #   "clean"    (lam = 0): the operating characteristics the design would
    #              have if carryover were bounded -- genuine power, type-I,
    #              coverage at the observed noise and effect.
    #   "observed" (lam = lam_hat): what the realised carryover does to the
    #              paired estimator -- the bias and coverage collapse the
    #              empirical Period-1 sensitivity analysis was designed to
    #              dodge.
    lam_sigma = p["lam"] / p["sd_total"]
    print(f"Observed carryover as fraction of total SD: lam/sigma = {lam_sigma:.2f}\n")

    rows = []
    for n in (30, 59):
        # CLEAN regime (lam = 0)
        clean_eff, clean_par, clean_anc, griz_fp = run_calibrated(
            p, n=n, d=p["d_implied"], lam=0.0, reps=args.reps, rng=rng)
        clean_null, _, _, _ = run_calibrated(
            p, n=n, d=0.0, lam=0.0, reps=args.reps, rng=rng)
        # OBSERVED-carryover regime (lam = lam_hat)
        obs_eff, _, _, griz_obs = run_calibrated(
            p, n=n, d=p["d_implied"], lam=p["lam"], reps=args.reps, rng=rng)

        rows.append({
            "n": n,
            "d_implied": round(p["d_implied"], 3),
            # Clean design -> detection is near-certain, test is well-behaved
            "power_crossover_clean": round(clean_eff["power"], 3),
            "power_parallel_welch_clean": round(clean_par["power"], 3),
            "power_parallel_ancova_clean": round(clean_anc["power"], 3),
            "type1_crossover_clean": round(clean_null["power"], 3),
            "coverage_crossover_clean": round(clean_eff["coverage"], 3),
            "bias_crossover_clean": round(clean_eff["bias"], 3),
            # Observed carryover -> paired estimator inflation
            "bias_crossover_obs_carryover": round(obs_eff["bias"], 3),
            "coverage_crossover_obs_carryover": round(obs_eff["coverage"], 3),
            # Grizzle test: detection at the observed carryover vs false-pos baseline
            "grizzle_power_at_obs_carryover": round(griz_obs, 3),
            "grizzle_falsepos_no_carryover": round(griz_fp, 3),
        })

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 50)
    print("Calibrated operating characteristics:")
    print(out.to_string(index=False))
    out.to_csv(OUT_DIR / "calibration_empirical.csv", index=False)
    print(f"\nWrote {OUT_DIR / 'calibration_empirical.csv'}")
    print(f"Wrote {OUT_DIR / 'calibration_params.csv'}")

    # Reconciliation: the carryover-induced bias should bridge the full
    # crossover estimate and the carryover-immune Period-1-only estimate.
    print("\n--- Reconciliation with the empirical Period-1 sensitivity analysis ---")
    bias59 = [r for r in rows if r["n"] == 59][0]["bias_crossover_obs_carryover"]
    print(f"  Full crossover paired estimate (empirical)        : tau = {p['tau_raw']:.2f}")
    print(f"  Simulated carryover bias at n=59                  : {bias59:+.2f}")
    print(f"  Carryover-corrected estimate (tau - bias)         : {p['tau_raw'] - bias59:+.2f}")
    print(f"  Empirical Period-1-only difference (carryover-free): approx -20.84 (d=-0.95)")


if __name__ == "__main__":
    main()
