"""
run_monte_carlo_highorder.py
============================

Higher-order crossover designs for the IEEE / future methodological paper.
This is NOT part of Paper 2: it does not touch run_monte_carlo.py and does
not change any number Paper 2 reports. It reuses the same data-generating
logic and the Grizzle test, but extends the comparison beyond the 2x2 to
designs that make first-order carryover *estimable and correctable*:

  - "2x2"      AB, BA                  (the current design; reference)
  - "Balaam"   AB, BA, AA, BB          (adds the two repeat sequences)
  - "dual_3p"  ABB, BAA, ABA, BAB      (3-period two-treatment dual design)
  - "dual_4p"  ABBA, BAAB              (4-period two-treatment dual design)

The story the table tells:

  In the 2x2, the direct treatment effect and the first-order carryover
  effect are aliased within subjects. You cannot adjust the treatment
  estimate for carryover; you can only test for carryover *between*
  subjects (Grizzle), which is badly underpowered at classroom N. The
  higher-order designs break that aliasing: carryover becomes a
  within-subject regressor, so it can be (a) detected with real power and
  (b) subtracted, yielding a treatment estimate whose bias collapses even
  when the true carryover is large (the lambda ~ 1.14 sigma we actually
  observed in the pilot).

Model: a within-subject (subject fixed-effects) linear model with period
dummies, a treatment indicator, and a first-order carryover indicator
(= 1 if the immediately preceding period used the active treatment, AI).
Because the sequence layout is fixed across replications and only the
responses change, the within design matrix is built once and every
replicate is solved by a single matrix multiply.

Usage:
    python sample_data/run_monte_carlo_highorder.py
    python sample_data/run_monte_carlo_highorder.py --reps 5000 --n 60

Output:
    sample_data/scenario_validation/highorder_designs.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from run_monte_carlo import grizzle_test  # reuse the exact 2x2 carryover test

OUT_DIR = Path(__file__).resolve().parent / "scenario_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Empirical-pilot noise structure (from calibrate_empirical.py) so that the
# bias numbers are in the same raw 0-100 points as the companion study.
SIGMA_S = 9.27     # between-subject SD
SIGMA_E = 18.56    # within-subject SD
TAU = -32.58       # direct effect of AI (B) vs noAI (A), raw points
PI = -2.70         # linear period effect per period step
SD_TOTAL = float(np.sqrt(SIGMA_S ** 2 + SIGMA_E ** 2))  # ~20.75

DESIGNS = {
    "2x2":     ["AB", "BA"],
    "Balaam":  ["AB", "BA", "AA", "BB"],
    "dual_3p": ["ABB", "BAA", "ABA", "BAB"],
    "dual_4p": ["ABBA", "BAAB"],
}


# ---------------------------------------------------------------------------
# Fixed design layout (built once per design+n)
# ---------------------------------------------------------------------------

def build_layout(sequences, n):
    """Assign n subjects round-robin to the design's sequences and return the
    fixed per-(subject, period) regressors.

    Returns dict with:
        n, p
        treat   (n, p)  1 if active treatment B (AI) in that period
        carry   (n, p)  1 if previous period used B (0 in period 1)
        period  (n, p)  0-based period index
        seq_id  (n,)    index into `sequences`
    """
    p = len(sequences[0])
    assert all(len(s) == p for s in sequences), "sequences must share length"
    seq_id = np.array([i % len(sequences) for i in range(n)])

    treat = np.zeros((n, p), dtype=float)
    carry = np.zeros((n, p), dtype=float)
    period = np.tile(np.arange(p, dtype=float), (n, 1))

    for i in range(n):
        s = sequences[seq_id[i]]
        for k, letter in enumerate(s):
            treat[i, k] = 1.0 if letter == "B" else 0.0
            if k > 0:
                carry[i, k] = 1.0 if s[k - 1] == "B" else 0.0
    return {"n": n, "p": p, "treat": treat, "carry": carry,
            "period": period, "seq_id": seq_id}


def within_design_matrix(layout, include_carry):
    """Build the subject-demeaned (fixed-effects) regressor matrix for the
    design. Columns: period dummies (p-1), treatment, [carryover].
    Returns Xd (Nobs, k), the projector P = (Xd'Xd)^-1 Xd', the rank check,
    and dof. Rows are ordered subject-major, period-minor."""
    n, p = layout["n"], layout["p"]
    cols = []

    # Period dummies for periods 1..p-1 (period 0 is the reference)
    for k in range(1, p):
        d = (layout["period"] == k).astype(float)
        cols.append(d)
    cols.append(layout["treat"])
    if include_carry:
        cols.append(layout["carry"])

    # Stack into (n, p, k) then subject-demean over the period axis
    X = np.stack(cols, axis=-1)                      # (n, p, k)
    X = X - X.mean(axis=1, keepdims=True)            # within transform
    k = X.shape[-1]
    Xd = X.reshape(n * p, k)                          # (Nobs, k)

    rank = int(np.linalg.matrix_rank(Xd))
    identifiable = rank == k
    dof = n * p - n - k                               # minus n subject means
    if not identifiable:
        return Xd, None, None, False, dof, k

    XtX_inv = np.linalg.inv(Xd.T @ Xd)
    proj = XtX_inv @ Xd.T                             # (k, Nobs)
    return Xd, proj, XtX_inv, True, dof, k


# ---------------------------------------------------------------------------
# Simulate responses for all replicates at once
# ---------------------------------------------------------------------------

def simulate_responses(layout, lam, reps, rng):
    """Y (reps, n, p) under y = subj + PI*period + TAU*treat + lam*carry + eps."""
    n, p = layout["n"], layout["p"]
    subj = rng.normal(0.0, SIGMA_S, size=(reps, n, 1))
    eps = rng.normal(0.0, SIGMA_E, size=(reps, n, p))
    mean = (subj
            + PI * layout["period"][None, :, :]
            + TAU * layout["treat"][None, :, :]
            + lam * layout["carry"][None, :, :])
    return mean + eps


def fit_all(Y, layout, proj, XtX_inv, dof, k, treat_col_idx, carry_col_idx):
    """Vectorised within-FE OLS across all replicates.
    Returns dict of arrays (one value per replicate) for the treatment
    coefficient and (if present) the carryover coefficient."""
    reps, n, p = Y.shape
    Yd = Y - Y.mean(axis=2, keepdims=True)           # subject-demean
    Yd = Yd.reshape(reps, n * p).T                   # (Nobs, reps)

    beta = proj @ Yd                                 # (k, reps)
    # SSR via the normal-equation identity (avoids rebuilding Xd):
    #   SSR = Yd'Yd - beta'(Xd'Xd)beta   (per replicate)
    XtX = np.linalg.inv(XtX_inv)
    ss_total = np.einsum("ij,ij->j", Yd, Yd)
    ss_model = np.einsum("kj,kl,lj->j", beta, XtX, beta)
    ssr = ss_total - ss_model
    sigma2 = ssr / dof                               # (reps,)

    out = {}
    se_treat = np.sqrt(sigma2 * XtX_inv[treat_col_idx, treat_col_idx])
    b_treat = beta[treat_col_idx]
    out["treat_est"] = b_treat
    out["treat_se"] = se_treat
    crit = stats.t.ppf(0.975, df=dof)
    out["treat_lo"] = b_treat - crit * se_treat
    out["treat_hi"] = b_treat + crit * se_treat

    if carry_col_idx is not None:
        se_c = np.sqrt(sigma2 * XtX_inv[carry_col_idx, carry_col_idx])
        b_c = beta[carry_col_idx]
        t_c = np.where(se_c > 0, b_c / se_c, 0.0)
        out["carry_p"] = 2.0 * stats.t.sf(np.abs(t_c), df=dof)
    return out


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3000)
    ap.add_argument("--n", type=int, default=60, help="subjects (classroom N)")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    # Carryover levels: a "moderate" one and the magnitude actually observed.
    lam_levels = {
        "moderate (0.4 sigma)": 0.40 * SD_TOTAL,
        "observed (1.14 sigma)": 1.14 * SD_TOTAL,
    }

    print("=== Higher-order crossover designs vs the 2x2 ===")
    print(f"N = {args.n} subjects, reps = {args.reps}, "
          f"true direct effect TAU = {TAU} raw points")
    print(f"noise: sigma_s = {SIGMA_S}, sigma_e = {SIGMA_E} "
          f"(total {SD_TOTAL:.2f})\n")

    rng = np.random.default_rng(args.seed)
    rows = []

    for dname, seqs in DESIGNS.items():
        layout = build_layout(seqs, args.n)
        p = layout["p"]

        # Naive model (no carryover term) and adjusted model (with it)
        _, proj_naive, inv_naive, ok_naive, dof_naive, k_naive = \
            within_design_matrix(layout, include_carry=False)
        _, proj_adj, inv_adj, ok_adj, dof_adj, k_adj = \
            within_design_matrix(layout, include_carry=True)

        # Column indices: [period dummies (p-1)] + [treat] (+ [carry])
        treat_idx = (p - 1)
        carry_idx_adj = (p - 1) + 1 if ok_adj else None

        for lam_label, lam in lam_levels.items():
            Y = simulate_responses(layout, lam, args.reps, rng)

            # --- naive treatment estimate (the "do nothing about carryover") ---
            naive = fit_all(Y, layout, proj_naive, inv_naive, dof_naive,
                            k_naive, treat_idx, None)
            bias_naive = float(np.mean(naive["treat_est"]) - TAU)

            # --- detection of carryover ---
            if dname == "2x2":
                # Aliased within-subject -> only the between-subject Grizzle
                seq01 = (layout["seq_id"] == 1).astype(int)  # AB=0, BA=1
                seq_arr = np.tile(seq01, (args.reps, 1))
                obs = np.ones_like(Y, dtype=np.int8)
                _, p_car = grizzle_test(Y, seq_arr, obs)
                p_car = p_car[np.isfinite(p_car)]
                detect_power = float((p_car < 0.05).mean())
                detect_method = "Grizzle (between-subj)"
                bias_adj = np.nan
                cov_adj = np.nan
                se_adj = np.nan
            else:
                adj = fit_all(Y, layout, proj_adj, inv_adj, dof_adj,
                              k_adj, treat_idx, carry_idx_adj)
                detect_power = float((adj["carry_p"] < 0.05).mean())
                detect_method = "within-model"
                bias_adj = float(np.mean(adj["treat_est"]) - TAU)
                cov_adj = float(np.mean(
                    (adj["treat_lo"] <= TAU) & (TAU <= adj["treat_hi"])))
                se_adj = float(np.mean(adj["treat_se"]))

            rows.append({
                "design": dname,
                "periods": p,
                "n": args.n,
                "carryover": lam_label,
                "lam_raw": round(lam, 2),
                "carryover_detect_power": round(detect_power, 3),
                "detect_method": detect_method,
                "treat_bias_naive": round(bias_naive, 2),
                "treat_bias_adjusted": (round(bias_adj, 2)
                                        if np.isfinite(bias_adj) else np.nan),
                "treat_coverage_adjusted": (round(cov_adj, 3)
                                            if np.isfinite(cov_adj) else np.nan),
                "treat_se_adjusted": (round(se_adj, 2)
                                      if np.isfinite(se_adj) else np.nan),
            })

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 50)
    print(out.to_string(index=False))
    out.to_csv(OUT_DIR / "highorder_designs.csv", index=False)
    print(f"\nWrote {OUT_DIR / 'highorder_designs.csv'}")
    print("\nReading: in the 2x2 the carryover term is not identifiable "
          "within subjects (treat_bias_adjusted = NaN); detection falls back "
          "to the underpowered Grizzle test. Balaam and the dual designs "
          "detect carryover with real power AND recover an almost unbiased "
          "treatment estimate even at the observed 1.14-sigma carryover.")


if __name__ == "__main__":
    main()
