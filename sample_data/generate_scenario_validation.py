"""
generate_scenario_validation.py
Purpose: Generate several synthetic classroom populations, run the full
         crossover analysis pipeline on each one, and collect panel-ready
         outputs for documentation and regression-style workflow checks.

Run from the project root:
    python sample_data/generate_scenario_validation.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "analysis" / "python" / "run_all.py"
SCENARIO_ROOT = Path(__file__).resolve().parent / "scenario_validation"


SCENARIOS = [
    {
        "scenario_id": "S0",
        "slug": "high_domain_mastery",
        "population_label": "High domain mastery",
        "cluster_label": "Experienced in subject matter",
        "n_total": 100,
        "mu": 72,
        "tau_ab": 0.5,
        "tau_ba": 0.5,
        "pi_effect": 0.5,
        "lam": 0.0,
        "sigma_subj": 8,
        "sigma_resid": 6,
        "time_ai": 34.0,
        "time_noai": 37.0,
        "missing_rate": 0.02,
    },
    {
        "scenario_id": "S1",
        "slug": "ai_naive_students",
        "population_label": "AI-naive students",
        "cluster_label": "Low familiarity with AI tools",
        "n_total": 100,
        "mu": 62,
        "tau_ab": 8.0,
        "tau_ba": 8.0,
        "pi_effect": 2.0,
        "lam": 0.0,
        "sigma_subj": 12,
        "sigma_resid": 8,
        "time_ai": 38.0,
        "time_noai": 48.0,
        "missing_rate": 0.03,
    },
    {
        "scenario_id": "S2",
        "slug": "transfer_prone_strategic",
        "population_label": "Transfer-prone strategic learners",
        "cluster_label": "Rapid transfer of learned strategies",
        "n_total": 100,
        "mu": 64,
        "tau_ab": 3.0,
        "tau_ba": 3.0,
        "pi_effect": 2.0,
        "lam": 4.0,
        "sigma_subj": 10,
        "sigma_resid": 7,
        "time_ai": 36.0,
        "time_noai": 42.0,
        "missing_rate": 0.03,
    },
    {
        "scenario_id": "S3",
        "slug": "steep_learning_curve",
        "population_label": "Students in steep-learning courses",
        "cluster_label": "Large period effect",
        "n_total": 100,
        "mu": 60,
        "tau_ab": 2.0,
        "tau_ba": 2.0,
        "pi_effect": 7.0,
        "lam": 0.0,
        "sigma_subj": 11,
        "sigma_resid": 8,
        "time_ai": 37.0,
        "time_noai": 43.0,
        "missing_rate": 0.03,
    },
    {
        "scenario_id": "S4",
        "slug": "digitally_expert_order_sensitive",
        "population_label": "Digitally expert students",
        "cluster_label": "High digital fluency",
        "n_total": 100,
        "mu": 66,
        "tau_ab": 6.0,
        "tau_ba": 2.0,
        "pi_effect": 1.5,
        "lam": 0.0,
        "sigma_subj": 9,
        "sigma_resid": 6,
        "time_ai": 30.0,
        "time_noai": 39.0,
        "missing_rate": 0.02,
    },
    {
        "scenario_id": "S5",
        "slug": "heterogeneous_small_effect",
        "population_label": "Highly heterogeneous cohorts",
        "cluster_label": "Mixed prior experience and attainment",
        "n_total": 100,
        "mu": 63,
        "tau_ab": 2.0,
        "tau_ba": 2.0,
        "pi_effect": 1.5,
        "lam": 0.0,
        "sigma_subj": 18,
        "sigma_resid": 12,
        "time_ai": 37.0,
        "time_noai": 43.0,
        "missing_rate": 0.04,
    },
]


def generate_dataset(spec: dict) -> pd.DataFrame:
    rng = np.random.default_rng(2026 + int(spec["scenario_id"][1:]))
    n_total = spec["n_total"]
    n_per_seq = n_total // 2

    participant_ids = [f"{spec['scenario_id']}_P{i:03d}" for i in range(1, n_total + 1)]
    groups = ["A"] * n_per_seq + ["B"] * n_per_seq
    sequences = ["AB"] * n_per_seq + ["BA"] * n_per_seq
    subject_effects = rng.normal(0, spec["sigma_subj"], n_total)

    participants = pd.DataFrame(
        {
            "participant_id": participant_ids,
            "group": groups,
            "sequence": sequences,
            "subject_effect": subject_effects,
        }
    )

    rows = []
    for _, participant in participants.iterrows():
        for period in [1, 2]:
            if participant["sequence"] == "AB":
                condition = "noAI" if period == 1 else "AI"
                tau = spec["tau_ab"]
            else:
                condition = "AI" if period == 1 else "noAI"
                tau = spec["tau_ba"]

            treatment_ind = 1.0 if condition == "AI" else 0.0
            period_centered = period - 1.5
            carryover_term = spec["lam"] if (period == 2 and participant["sequence"] == "BA") else 0.0
            residual = rng.normal(0, spec["sigma_resid"])

            score_raw = (
                spec["mu"]
                + spec["pi_effect"] * period_centered
                + tau * treatment_ind
                + carryover_term
                + participant["subject_effect"]
                + residual
            )
            score = round(np.clip(score_raw, 0, 100), 1)

            rows.append(
                {
                    "participant_id": participant["participant_id"],
                    "group": participant["group"],
                    "sequence": participant["sequence"],
                    "period": period,
                    "condition": condition,
                    "score": score,
                    "population_group": spec["population_label"],
                    "scenario_id": spec["scenario_id"],
                }
            )

    df = pd.DataFrame(rows)

    df["rubric_score"] = np.round(
        np.clip(df["score"].values / 10 * 0.75 + rng.normal(0, 1.0, len(df)) + 0.5, 0, 10),
        1,
    )

    common_factor = rng.normal(0, 0.6, len(df))
    ai_mask = (df["condition"] == "AI").values.astype(float)
    strong_ai_advantage = spec["tau_ab"] + spec["tau_ba"] > 6

    likert_specs = {
        "likert_usefulness": (3.1, 0.6 if strong_ai_advantage else 0.2, 0.7),
        "likert_ease": (3.3, 0.4, 0.8),
        "likert_confidence": (3.0, 0.3, 0.7),
        "likert_engagement": (3.2, 0.3, 0.8),
        "likert_satisfaction": (3.1, 0.5, 0.7),
        "likert_learning": (3.2, 0.2, 0.8),
    }

    for col_name, (base_mean, ai_bonus, item_sd) in likert_specs.items():
        raw = base_mean + ai_bonus * ai_mask + common_factor + rng.normal(0, item_sd, len(df))
        df[col_name] = pd.Series(np.clip(np.round(raw), 1, 5)).astype("Int64")

    time_mean = np.where(df["condition"] == "AI", spec["time_ai"], spec["time_noai"])
    df["time_spent"] = np.round(np.maximum(5.0, rng.normal(time_mean, 10.0)), 1)

    rng_miss = np.random.default_rng(9000 + int(spec["scenario_id"][1:]))
    n_obs = len(df)
    missing_rate = spec["missing_rate"]

    missing_rubric = rng_miss.choice(n_obs, size=max(1, round(n_obs * missing_rate)), replace=False)
    df.loc[df.index[missing_rubric], "rubric_score"] = np.nan

    for col_name in likert_specs:
        n_miss = max(1, round(n_obs * missing_rate / 2))
        missing_idx = rng_miss.choice(n_obs, size=n_miss, replace=False)
        df.loc[df.index[missing_idx], col_name] = pd.NA

    missing_time = rng_miss.choice(n_obs, size=max(1, round(n_obs * missing_rate / 3)), replace=False)
    df.loc[df.index[missing_time], "time_spent"] = np.nan

    col_order = [
        "participant_id",
        "group",
        "sequence",
        "period",
        "condition",
        "score",
        "rubric_score",
        "time_spent",
        "likert_usefulness",
        "likert_ease",
        "likert_confidence",
        "likert_engagement",
        "likert_satisfaction",
        "likert_learning",
        "population_group",
        "scenario_id",
    ]

    return df[col_order].sort_values(["participant_id", "period"]).reset_index(drop=True)


def run_pipeline_for_scenario(spec: dict) -> dict:
    scenario_dir = SCENARIO_ROOT / spec["scenario_id"]
    data_dir = scenario_dir / "sample_data"
    output_dir = scenario_dir / "output"

    if scenario_dir.exists():
        shutil.rmtree(scenario_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = generate_dataset(spec)
    df.to_csv(data_dir / "crossover_sample_data.csv", index=False)

    env = os.environ.copy()
    env["CROSSOVER_TOOLKIT_DATA_DIR"] = str(data_dir)
    env["CROSSOVER_TOOLKIT_OUTPUT_DIR"] = str(output_dir)

    print(f"=== Running pipeline for {spec['scenario_id']} - {spec['population_label']} ===")
    completed = subprocess.run(
        [sys.executable, str(PIPELINE)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )

    (scenario_dir / "pipeline_stdout.log").write_text(completed.stdout, encoding="utf-8")
    (scenario_dir / "pipeline_stderr.log").write_text(completed.stderr, encoding="utf-8")

    if completed.returncode != 0:
        raise RuntimeError(
            f"Pipeline failed for {spec['scenario_id']}: "
            f"{completed.stderr.splitlines()[-1] if completed.stderr else 'unknown error'}"
        )

    return {
        "scenario_id": spec["scenario_id"],
        "slug": spec["slug"],
        "population_label": spec["population_label"],
        "cluster_label": spec["cluster_label"],
        "tau_ab": spec["tau_ab"],
        "tau_ba": spec["tau_ba"],
        "pi_effect": spec["pi_effect"],
        "lam": spec["lam"],
        "sigma_subj": spec["sigma_subj"],
        "sigma_resid": spec["sigma_resid"],
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
    }


def main() -> None:
    SCENARIO_ROOT.mkdir(parents=True, exist_ok=True)
    scenario_info = [run_pipeline_for_scenario(spec) for spec in SCENARIOS]

    pd.DataFrame(scenario_info).to_csv(SCENARIO_ROOT / "scenario_catalog.csv", index=False)

    panel_builder = Path(__file__).resolve().parent / "build_scenario_panels.py"
    subprocess.run([sys.executable, str(panel_builder)], cwd=ROOT, check=True)

    print(f"Scenario validation outputs written to: {SCENARIO_ROOT}")


if __name__ == "__main__":
    main()
