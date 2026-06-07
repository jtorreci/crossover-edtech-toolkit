"""
10_post_survey.py
Purpose: Analyse the closing (post) survey that captures the dissociation
         between *result/output quality* and *learning*:
           - mejor_resultado: which condition produced the better deliverable
           - mas_aprendizaje: with which condition the student learned more
           - preferencia, utilidad
         Forced-choice items (con_ia / sin_ia / igual). We report frequencies
         and a two-sided exact binomial test on the decided responses
         (con_ia vs sin_ia, ignoring 'igual').
Input:   post_survey.csv in DATA_DIR (written by exportar_y_analizar.py).
         If absent (e.g. the synthetic sample), the script exits cleanly.
Output:  post_survey_summary.csv, post_survey_tests.csv (tables) and
         post_survey.png (figure).
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

print("=== 10_post_survey.py: Post survey (result vs learning) ===")

post_file = DATA_DIR / "post_survey.csv"
if not post_file.exists():
    print(f"  No post_survey.csv in {DATA_DIR}. Skipping (expected for sample data).")
    print("=== 10_post_survey.py: Skipped ===\n")
else:
    df = pd.read_csv(post_file)
    print(f"  Loaded {len(df)} student post-surveys.")

    ITEMS = {
        "mejor_resultado": "Mejor resultado / entregable",
        "mas_aprendizaje": "Mayor aprendizaje",
    }
    CHOICES = ["con_ia", "sin_ia", "igual"]

    # ----- Frequency table --------------------------------------------------
    rows = []
    for col in ITEMS:
        if col not in df.columns:
            continue
        counts = df[col].value_counts(dropna=True)
        for choice in CHOICES:
            rows.append({
                "item": col,
                "respuesta": choice,
                "n": int(counts.get(choice, 0)),
            })
    summary = pd.DataFrame(rows)
    if not summary.empty:
        totals = summary.groupby("item")["n"].transform("sum")
        summary["pct"] = (summary["n"] / totals * 100).round(1)
    summary.to_csv(TABLES_DIR / "post_survey_summary.csv", index=False)
    print("\n  Frequencies:")
    print(summary.to_string(index=False))

    # ----- Exact binomial test on decided responses -------------------------
    test_rows = []
    for col in ITEMS:
        if col not in df.columns:
            continue
        n_con = int((df[col] == "con_ia").sum())
        n_sin = int((df[col] == "sin_ia").sum())
        n_dec = n_con + n_sin
        if n_dec > 0:
            res = stats.binomtest(n_con, n_dec, 0.5, alternative="two-sided")
            p = res.pvalue
            prop_con = n_con / n_dec
        else:
            p, prop_con = np.nan, np.nan
        favor = "con_ia" if n_con > n_sin else ("sin_ia" if n_sin > n_con else "tie")
        test_rows.append({
            "item": col,
            "n_con_ia": n_con,
            "n_sin_ia": n_sin,
            "n_decided": n_dec,
            "prop_con_ia": round(prop_con, 3) if n_dec else np.nan,
            "favors": favor,
            "binomial_p": round(p, 5) if n_dec else np.nan,
        })
    tests = pd.DataFrame(test_rows)
    tests.to_csv(TABLES_DIR / "post_survey_tests.csv", index=False)
    print("\n  Binomial tests (con_ia vs sin_ia, 'igual' excluded):")
    print(tests.to_string(index=False))

    # ----- Preferencia (informational) --------------------------------------
    if "preferencia" in df.columns:
        print("\n  Preferencia de orden:")
        print(df["preferencia"].value_counts(dropna=True).to_string())

    # ----- Figure: grouped bars --------------------------------------------
    if not summary.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        items = list(ITEMS.keys())
        x = np.arange(len(items))
        width = 0.27
        colors = {"con_ia": PALETTE["AI"], "sin_ia": PALETTE["noAI"], "igual": "#999999"}
        labels = {"con_ia": "Con IA", "sin_ia": "Sin IA", "igual": "Igual"}
        for k, choice in enumerate(CHOICES):
            vals = [int(summary[(summary["item"] == it) & (summary["respuesta"] == choice)]["n"].sum())
                    for it in items]
            ax.bar(x + (k - 1) * width, vals, width, label=labels[choice], color=colors[choice])
            for xi, v in zip(x + (k - 1) * width, vals):
                if v > 0:
                    ax.text(xi, v + 0.5, str(v), ha="center", va="bottom", fontsize=9)
        ax.set_xticks(x)
        ax.set_xticklabels([ITEMS[it] for it in items])
        ax.set_ylabel("Nº de estudiantes")
        ax.set_title("Disociación resultado vs aprendizaje (encuesta post)")
        ax.legend(title="Condición", loc="upper right")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "post_survey.png", dpi=300)
        fig.savefig(FIGURES_DIR / "post_survey.pdf")
        plt.close(fig)
        print(f"\n  Saved figure: {FIGURES_DIR / 'post_survey.png'}")

    print("=== 10_post_survey.py: Complete ===\n")
