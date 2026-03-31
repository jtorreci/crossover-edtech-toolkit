"""
run_all.py
Purpose: Execute the full Python analysis pipeline in sequence, with error
         handling and timing information for each step.
Usage:   python analysis/python/run_all.py
         (from the project root directory)
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS = [
    "00_setup.py",
    "01_data_import_clean.py",
    "02_descriptive_stats.py",
    "03_instrument_validation.py",
    "04_paired_comparisons.py",
    "05_mixed_anova.py",
    "06_effect_sizes.py",
    "07_carryover_analysis.py",
    "08_perception_analysis.py",
    "09_visualizations.py",
]

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

print("=" * 64)
print("  crossover-edtech-toolkit: Full Analysis Pipeline (Python)")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 64)
print()

pipeline_start = time.time()

# ---------------------------------------------------------------------------
# Execute each script
# ---------------------------------------------------------------------------

results = []

for script in SCRIPTS:
    script_path = SCRIPT_DIR / script
    print(f">>> Running: {script}")
    step_start = time.time()

    try:
        completed = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        duration = time.time() - step_start

        if completed.returncode == 0:
            # Print stdout from the script
            if completed.stdout:
                for line in completed.stdout.splitlines():
                    print(f"    {line}")
            results.append({
                "script": script,
                "status": "SUCCESS",
                "duration": round(duration, 2),
                "message": "",
            })
            print(f">>> {script} completed in {duration:.2f} seconds.\n")
        else:
            # Print both stdout and stderr for error diagnosis
            if completed.stdout:
                for line in completed.stdout.splitlines()[-10:]:
                    print(f"    {line}")
            error_msg = completed.stderr.strip().splitlines()[-1] if completed.stderr else "Unknown error"
            results.append({
                "script": script,
                "status": "ERROR",
                "duration": round(duration, 2),
                "message": error_msg,
            })
            print(f"*** ERROR in {script}: {error_msg}\n")

    except subprocess.TimeoutExpired:
        duration = time.time() - step_start
        results.append({
            "script": script,
            "status": "TIMEOUT",
            "duration": round(duration, 2),
            "message": "Script exceeded 300s timeout",
        })
        print(f"*** TIMEOUT in {script}\n")

    except Exception as exc:
        duration = time.time() - step_start
        results.append({
            "script": script,
            "status": "ERROR",
            "duration": round(duration, 2),
            "message": str(exc),
        })
        print(f"*** ERROR in {script}: {exc}\n")

# ---------------------------------------------------------------------------
# Pipeline summary
# ---------------------------------------------------------------------------

total_duration = time.time() - pipeline_start
results_df = pd.DataFrame(results)

n_success = (results_df["status"] == "SUCCESS").sum()
n_error = (results_df["status"] != "SUCCESS").sum()

print()
print("=" * 64)
print("  Pipeline Summary")
print("=" * 64)
print()
print(f"  Total scripts:   {len(SCRIPTS)}")
print(f"  Successful:      {n_success}")
print(f"  Errors:          {n_error}")
print(f"  Total duration:  {total_duration:.2f} seconds")
print()
print("  Step-by-step results:")
print("  " + "-" * 70)

for _, row in results_df.iterrows():
    icon = "[OK]" if row["status"] == "SUCCESS" else "[!!]"
    msg = f"  {row['message']}" if row["message"] else ""
    print(f"  {icon} {row['script']:35s} {row['duration']:8.2f}s{msg}")

print("  " + "-" * 70)

# Save pipeline log
results_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_file = OUTPUT_DIR / "pipeline_log.csv"
results_df.to_csv(log_file, index=False)
print(f"\n  Pipeline log saved to: {log_file}")

if n_error > 0:
    print("\n  Some scripts failed. Check error messages above.")
else:
    print("\n  All scripts completed successfully.")
    print(f"  Output files are in: {OUTPUT_DIR}")

print(f"\n  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 64)
