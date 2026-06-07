"""
run_highorder_attrition.py
==========================

Attrition robustness of the higher-order crossover designs (companion to
run_monte_carlo_highorder.py; for the IEEE / future methodological paper).
Does NOT touch Paper 2 or the no-attrition script.

Question: a 3- or 4-period dual design recovers an unbiased treatment
estimate and detects carryover, but it asks each student for more
challenges and is therefore more exposed to drop-out. Does the extra
period still pay off once attrition rises?

Mechanism that makes this non-trivial: in a 2-period design (2x2, Balaam)
a student who misses one period contributes a single observation, which
the within-subject (fixed-effects) transform reduces to zero -- the
student is effectively lost. In a 3- or 4-period design the same student
keeps contributing the periods they did complete. So attrition should bite
the 2-period designs harder.

We re-fit the within-FE model per replicate under random attrition (the
masking pattern differs every replicate, so the fast single-projector
trick of the no-attrition script does not apply). The true carryover is
fixed at the empirically observed magnitude (~1.14 sigma).

    python sample_data/run_highorder_attrition.py --reps 2000

Output:
    sample_data/scenario_validation/highorder_attrition.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from run_monte_carlo import grizzle_test
from run_monte_carlo_highorder import (
    build_layout, DESIGNS, SIGMA_S, SIGMA_E, PI, TAU, SD_TOTAL,
)

OUT_DIR = Path(__file__).resolve().parent / "scenario_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def simulate_with_attrition(layout, lam, attrition, reps, rng):
    """Y (reps, n, p) and a boolean observed-mask under random per-cell drop-out."""
    n, p = layout["n"], layout["p"]
    subj = rng.normal(0.0, SIGMA_S, size=(reps, n, 1))
    eps = rng.normal(0.0, SIGMA_E, size=(reps, n, p))
    mean = (subj
            + PI * layout["period"][None, :, :]
            + TAU * layout["treat"][None, :, :]
            + lam * layout["carry"][None, :, :])
    Y = mean + eps
    obs = rng.random(size=Y.shape) >= attrition       # True = observed
    return Y, obs


def masked_within_fit(Yr, obs_r, layout, include_carry):
    """Within-subject FE OLS for one replicate under an arbitrary observed
    mask. Subjects with fewer than two observed periods carry no within
    information and are dropped. Returns None if the surviving design is
    rank-deficient."""
    n, p = Yr.shape
    cols = [(layout["period"] == k).astype(float) for k in range(1, p)]
    cols.append(layout["treat"])
    if include_carry:
        cols.append(layout["carry"])
    Xfull = np.stack(cols, axis=-1)                   # (n, p, k)
    k = Xfull.shape[-1]

    ys, xs, retained = [], [], 0
    for i in range(n):
        m = obs_r[i]
        if m.sum() < 2:
            continue
        yi = Yr[i][m]
        xi = Xfull[i][m]
        ys.append(yi - yi.mean())                     # subject-demean
        xs.append(xi - xi.mean(axis=0, keepdims=True))
        retained += 1
    if retained < k + 2:
        return None

    Y = np.concatenate(ys)
    X = np.concatenate(xs, axis=0)
    if np.linalg.matrix_rank(X) < k:
        return None

    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    resid = Y - X @ beta
    dof = len(Y) - retained - k                       # minus subject means + regressors
    if dof < 1:
        return None
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * XtX_inv

    ti = p - 1
    b_t = float(beta[ti])
    se_t = float(np.sqrt(cov[ti, ti]))
    crit = stats.t.ppf(0.975, df=dof)
    out = {"treat_est": b_t, "treat_lo": b_t - crit * se_t,
           "treat_hi": b_t + crit * se_t, "treat_se": se_t,
           "retained": retained}
    if include_carry:
        ci = p
        b_c = float(beta[ci])
        se_c = float(np.sqrt(cov[ci, ci]))
        tc = b_c / se_c if se_c > 0 else 0.0
        out["carry_p"] = 2.0 * stats.t.sf(abs(tc), df=dof)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    lam = 1.14 * SD_TOTAL                              # observed carryover magnitude
    attr_levels = [0.0, 0.05, 0.10]

    print("=== Attrition robustness of higher-order designs ===")
    print(f"N = {args.n}, reps = {args.reps}, true TAU = {TAU}, "
          f"carryover lam = {lam:.1f} (1.14 sigma)\n")

    rng = np.random.default_rng(args.seed)
    rows = []

    for dname, seqs in DESIGNS.items():
        layout = build_layout(seqs, args.n)
        p = layout["p"]
        is_2x2 = (dname == "2x2")
        for attrition in attr_levels:
            Y, obs = simulate_with_attrition(layout, lam, attrition, args.reps, rng)

            est, lo, hi, se, ret, carry_hits, n_ok = [], [], [], [], [], 0, 0
            for r in range(args.reps):
                fit = masked_within_fit(Y[r], obs[r], layout,
                                        include_carry=not is_2x2)
                if fit is None:
                    continue
                n_ok += 1
                est.append(fit["treat_est"])
                lo.append(fit["treat_lo"])
                hi.append(fit["treat_hi"])
                se.append(fit["treat_se"])
                ret.append(fit["retained"])
                if not is_2x2 and fit["carry_p"] < 0.05:
                    carry_hits += 1

            est = np.array(est); lo = np.array(lo); hi = np.array(hi)

            if is_2x2:
                # Carryover not identifiable within subjects -> between-subject Grizzle
                seq01 = (layout["seq_id"] == 1).astype(int)
                seq_arr = np.tile(seq01, (args.reps, 1))
                _, p_car = grizzle_test(Y, seq_arr, obs.astype(np.int8))
                p_car = p_car[np.isfinite(p_car)]
                detect_power = float((p_car < 0.05).mean())
                bias_adj = np.nan
                cov_adj = np.nan
            else:
                detect_power = carry_hits / max(n_ok, 1)
                bias_adj = float(np.mean(est) - TAU)
                cov_adj = float(np.mean((lo <= TAU) & (TAU <= hi)))

            rows.append({
                "design": dname,
                "periods": p,
                "attrition": f"{int(attrition*100)}%",
                "mean_subjects_retained": round(float(np.mean(ret)), 1),
                "carryover_detect_power": round(detect_power, 3),
                "detect_method": "Grizzle" if is_2x2 else "within-model",
                "treat_bias_adjusted": (round(bias_adj, 2)
                                        if np.isfinite(bias_adj) else np.nan),
                "treat_coverage_adjusted": (round(cov_adj, 3)
                                            if np.isfinite(cov_adj) else np.nan),
                "treat_se_adjusted": round(float(np.mean(se)), 2),
            })

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)
    print(out.to_string(index=False))
    out.to_csv(OUT_DIR / "highorder_attrition.csv", index=False)
    print(f"\nWrote {OUT_DIR / 'highorder_attrition.csv'}")
    print("\nReading: the 2-period designs (2x2, Balaam) lose a whole subject "
          "for each dropped period, so retained N and precision fall fastest; "
          "the 3-4 period duals keep partial subjects and degrade gracefully.")


if __name__ == "__main__":
    main()
