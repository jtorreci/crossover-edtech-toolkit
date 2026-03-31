"""
09_visualizations.py
Purpose: Generate publication-quality plots for the crossover study:
         - Interaction plot (crossover design)
         - Individual trajectory (spaghetti) plots
         - Forest plot of effect sizes
         - Bland-Altman plot
         - Violin + box plots
         - Composite figure for publication
Input:   df_clean, df_wide, effect_sizes.csv
Output:  Publication-ready PNG (300 dpi) and PDF figures in output/figures/
"""

# ---------------------------------------------------------------------------
# Imports and setup
# ---------------------------------------------------------------------------
exec(open(str(__import__("pathlib").Path(__file__).resolve().parent / "00_setup.py")).read())

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from matplotlib.lines import Line2D

print("=== 09_visualizations.py: Generating publication-quality plots ===")

df_clean = pd.read_parquet(OUTPUT_DIR / "df_clean.parquet")
df_wide = pd.read_parquet(OUTPUT_DIR / "df_wide.parquet")

# Restore categoricals
df_clean["condition"] = pd.Categorical(df_clean["condition"], categories=["noAI", "AI"])
df_clean["period"] = pd.Categorical(df_clean["period"], categories=["Period 1", "Period 2"])
df_clean["sequence"] = pd.Categorical(df_clean["sequence"], categories=["AB", "BA"])
df_wide["sequence"] = pd.Categorical(df_wide["sequence"], categories=["AB", "BA"])

# ---------------------------------------------------------------------------
# 1. Interaction plot (classic crossover design visualization)
# ---------------------------------------------------------------------------

print("  Generating interaction plot...")

cell_stats = (
    df_clean.groupby(["sequence", "period", "condition"], observed=True)
    .agg(mean_score=("score", "mean"), se_score=("score", "sem"), n=("score", "size"))
    .reset_index()
)

fig, ax = plt.subplots(figsize=(8, 6))

for seq, color in SEQ_PALETTE.items():
    sub = cell_stats[cell_stats["sequence"] == seq].sort_values("period")
    x = [0, 1]  # period positions
    y = sub["mean_score"].values
    se = sub["se_score"].values

    label = f"Sequence {seq} ({'noAI->AI' if seq == 'AB' else 'AI->noAI'})"
    ax.errorbar(x, y, yerr=1.96 * se, marker="o", markersize=8,
                linewidth=1.5, capsize=4, color=color, label=label)

ax.set_xticks([0, 1])
ax.set_xticklabels(["Period 1", "Period 2"])
ax.set_ylabel("Mean Score")
ax.set_title("Crossover Design: Mean Scores by Sequence and Period")
ax.legend(loc="best", title="Sequence", title_fontsize=10)
ax.text(0.5, -0.12, "Error bars represent 95% confidence intervals",
        transform=ax.transAxes, ha="center", fontsize=9, color="grey")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "interaction_plot.png", dpi=300)
fig.savefig(FIGURES_DIR / "interaction_plot.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Spaghetti plot (individual trajectories)
# ---------------------------------------------------------------------------

print("  Generating spaghetti plot...")

fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
seq_labels = {"AB": "Sequence AB (noAI -> AI)", "BA": "Sequence BA (AI -> noAI)"}

for ax_idx, seq in enumerate(["AB", "BA"]):
    ax = axes[ax_idx]
    sub = df_clean[df_clean["sequence"] == seq].copy()

    # Map period to numeric for plotting
    period_map = {"Period 1": 0, "Period 2": 1}
    sub["period_x"] = sub["period"].map(period_map)

    # Individual lines
    for pid, grp in sub.groupby("participant_id"):
        grp_sorted = grp.sort_values("period_x")
        ax.plot(grp_sorted["period_x"], grp_sorted["score"],
                color="grey", alpha=0.2, linewidth=0.7)

    # Coloured dots by condition
    for cond, color in PALETTE.items():
        cond_sub = sub[sub["condition"] == cond]
        ax.scatter(cond_sub["period_x"], cond_sub["score"],
                   color=color, alpha=0.4, s=15, label=cond, zorder=3)

    # Group means
    seq_means = cell_stats[cell_stats["sequence"] == seq].sort_values("period")
    ax.plot([0, 1], seq_means["mean_score"].values,
            color="black", linewidth=2, linestyle="--", zorder=4)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Period 1", "Period 2"])
    ax.set_title(seq_labels[seq], fontweight="bold", fontsize=11)
    ax.set_ylabel("Score" if ax_idx == 0 else "")
    ax.legend(title="Condition", loc="upper left", fontsize=8)

fig.suptitle("Individual Score Trajectories Across Periods", fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(FIGURES_DIR / "spaghetti_plot.png", dpi=300)
fig.savefig(FIGURES_DIR / "spaghetti_plot.pdf")
plt.close(fig)

# ---------------------------------------------------------------------------
# 3. Forest plot of effect sizes
# ---------------------------------------------------------------------------

print("  Generating forest plot...")

es_file = TABLES_DIR / "effect_sizes.csv"
if es_file.exists():
    es_table = pd.read_csv(es_file).sort_values("Estimate")

    fig, ax = plt.subplots(figsize=(10, max(4, len(es_table) * 0.8 + 1)))

    y_pos = np.arange(len(es_table))
    ax.axvline(0, linestyle="--", color="grey", linewidth=0.8, zorder=1)
    ax.axvline(0.2, linestyle=":", color="grey", linewidth=0.5, alpha=0.6)
    ax.axvline(-0.2, linestyle=":", color="grey", linewidth=0.5, alpha=0.6)
    ax.axvline(0.5, linestyle=":", color="grey", linewidth=0.5, alpha=0.4)
    ax.axvline(-0.5, linestyle=":", color="grey", linewidth=0.5, alpha=0.4)

    ax.errorbar(
        es_table["Estimate"], y_pos,
        xerr=[
            es_table["Estimate"] - es_table["CI_lower"],
            es_table["CI_upper"] - es_table["Estimate"],
        ],
        fmt="o", color="#0072B2", markersize=7, capsize=3, linewidth=1.2,
        zorder=3,
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(es_table["Comparison"], fontsize=9)
    ax.set_xlabel("Effect Size")
    ax.set_title("Forest Plot of Effect Sizes (Cohen's d / Hedges' g)",
                 fontweight="bold")

    # Annotations
    ax.text(0.2, -0.8, "small", color="grey", fontsize=8, fontstyle="italic", ha="left")
    ax.text(0.5, -0.8, "medium", color="grey", fontsize=8, fontstyle="italic", ha="left")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "forest_plot.png", dpi=300)
    fig.savefig(FIGURES_DIR / "forest_plot.pdf")
    plt.close(fig)
else:
    print("  Effect sizes table not found. Run 06_effect_sizes.py first.")

# ---------------------------------------------------------------------------
# 4. Bland-Altman (paired difference) plot
# ---------------------------------------------------------------------------

print("  Generating paired difference plot...")

df_wide["mean_score"] = (df_wide["score_AI"] + df_wide["score_noAI"]) / 2
df_wide["diff_score"] = df_wide["score_AI"] - df_wide["score_noAI"]

mean_diff = df_wide["diff_score"].mean()
sd_diff = df_wide["diff_score"].std()

fig, ax = plt.subplots(figsize=(8, 6))

for seq, color in SEQ_PALETTE.items():
    sub = df_wide[df_wide["sequence"] == seq]
    ax.scatter(sub["mean_score"], sub["diff_score"], color=color,
               alpha=0.6, s=30, label=f"Sequence {seq}", zorder=3)

ax.axhline(mean_diff, color="blue", linewidth=0.8, label=f"Mean = {mean_diff:.2f}")
ax.axhline(mean_diff + 1.96 * sd_diff, color="red", linestyle="--", linewidth=0.6)
ax.axhline(mean_diff - 1.96 * sd_diff, color="red", linestyle="--", linewidth=0.6,
           label="Limits of agreement")
ax.set_xlabel("Mean of AI and noAI Scores")
ax.set_ylabel("Difference (AI - noAI)")
ax.set_title("Bland-Altman Plot: Agreement Between Conditions")
ax.legend(loc="upper left", fontsize=9)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "bland_altman_plot.png", dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# 5. Violin + box plots
# ---------------------------------------------------------------------------

print("  Generating violin plots...")

fig, ax = plt.subplots(figsize=(6, 6))
parts = ax.violinplot(
    [df_clean.loc[df_clean["condition"] == c, "score"].dropna().values
     for c in ["noAI", "AI"]],
    positions=[0, 1],
    showextrema=False,
)
for i, (pc, cond) in enumerate(zip(parts["bodies"], ["noAI", "AI"])):
    pc.set_facecolor(PALETTE[cond])
    pc.set_alpha(0.4)

# Overlay boxplots
bp = ax.boxplot(
    [df_clean.loc[df_clean["condition"] == c, "score"].dropna().values
     for c in ["noAI", "AI"]],
    positions=[0, 1],
    widths=0.15,
    patch_artist=True,
    showfliers=False,
    zorder=3,
)
for i, (patch, cond) in enumerate(zip(bp["boxes"], ["noAI", "AI"])):
    patch.set_facecolor(PALETTE[cond])
    patch.set_alpha(0.8)

# Jitter points
for i, cond in enumerate(["noAI", "AI"]):
    vals = df_clean.loc[df_clean["condition"] == cond, "score"].dropna().values
    jitter = np.random.default_rng(42).uniform(-0.04, 0.04, len(vals))
    ax.scatter(np.full(len(vals), i) + jitter, vals,
               color="black", alpha=0.15, s=8, zorder=2)

ax.set_xticks([0, 1])
ax.set_xticklabels(["noAI", "AI"])
ax.set_ylabel("Score (0-100)")
ax.set_title("Score Distribution by Condition")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "violin_score_condition.png", dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# 6. Composite figure (for publication)
# ---------------------------------------------------------------------------

print("  Generating composite figure...")

fig = plt.figure(figsize=(16, 12))
gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.3)

# Panel A: Interaction plot
ax_a = fig.add_subplot(gs[0, 0])
for seq, color in SEQ_PALETTE.items():
    sub = cell_stats[cell_stats["sequence"] == seq].sort_values("period")
    x = [0, 1]
    y = sub["mean_score"].values
    se = sub["se_score"].values
    label = f"{seq} ({'noAI->AI' if seq == 'AB' else 'AI->noAI'})"
    ax_a.errorbar(x, y, yerr=1.96 * se, marker="o", markersize=7,
                  linewidth=1.3, capsize=3, color=color, label=label)
ax_a.set_xticks([0, 1])
ax_a.set_xticklabels(["Period 1", "Period 2"])
ax_a.set_ylabel("Mean Score")
ax_a.set_title("A. Interaction Plot")
ax_a.legend(fontsize=8, loc="best")

# Panel B: Spaghetti plot (AB only for space)
ax_b = fig.add_subplot(gs[0, 1])
for seq in ["AB", "BA"]:
    sub = df_clean[df_clean["sequence"] == seq].copy()
    period_map_local = {"Period 1": 0, "Period 2": 1}
    sub["px"] = sub["period"].map(period_map_local)
    for pid, grp in sub.groupby("participant_id"):
        grp = grp.sort_values("px")
        ax_b.plot(grp["px"], grp["score"], color=SEQ_PALETTE[seq],
                  alpha=0.1, linewidth=0.5)
seq_means_all = cell_stats.copy()
for seq in ["AB", "BA"]:
    sm = seq_means_all[seq_means_all["sequence"] == seq].sort_values("period")
    ax_b.plot([0, 1], sm["mean_score"].values, color=SEQ_PALETTE[seq],
              linewidth=2.5, linestyle="--", label=seq, zorder=5)
ax_b.set_xticks([0, 1])
ax_b.set_xticklabels(["Period 1", "Period 2"])
ax_b.set_ylabel("Score")
ax_b.set_title("B. Individual Trajectories")
ax_b.legend(fontsize=8)

# Panel C: Violin plot
ax_c = fig.add_subplot(gs[1, 0])
parts_c = ax_c.violinplot(
    [df_clean.loc[df_clean["condition"] == c, "score"].dropna().values
     for c in ["noAI", "AI"]],
    positions=[0, 1], showextrema=False,
)
for pc, cond in zip(parts_c["bodies"], ["noAI", "AI"]):
    pc.set_facecolor(PALETTE[cond])
    pc.set_alpha(0.4)
bp_c = ax_c.boxplot(
    [df_clean.loc[df_clean["condition"] == c, "score"].dropna().values
     for c in ["noAI", "AI"]],
    positions=[0, 1], widths=0.15, patch_artist=True, showfliers=False, zorder=3,
)
for patch, cond in zip(bp_c["boxes"], ["noAI", "AI"]):
    patch.set_facecolor(PALETTE[cond])
    patch.set_alpha(0.8)
ax_c.set_xticks([0, 1])
ax_c.set_xticklabels(["noAI", "AI"])
ax_c.set_ylabel("Score (0-100)")
ax_c.set_title("C. Score Distributions")

# Panel D: Bland-Altman
ax_d = fig.add_subplot(gs[1, 1])
for seq, color in SEQ_PALETTE.items():
    sub = df_wide[df_wide["sequence"] == seq]
    ax_d.scatter(sub["mean_score"], sub["diff_score"], color=color,
                 alpha=0.5, s=20, label=f"Seq {seq}")
ax_d.axhline(mean_diff, color="blue", linewidth=0.8)
ax_d.axhline(mean_diff + 1.96 * sd_diff, color="red", linestyle="--", linewidth=0.5)
ax_d.axhline(mean_diff - 1.96 * sd_diff, color="red", linestyle="--", linewidth=0.5)
ax_d.set_xlabel("Mean Score")
ax_d.set_ylabel("Difference (AI - noAI)")
ax_d.set_title("D. Bland-Altman Plot")
ax_d.legend(fontsize=8)

fig.suptitle("Crossover Study Results: AI vs No-AI in Educational Assessment",
             fontweight="bold", fontsize=15, y=0.99)
fig.savefig(FIGURES_DIR / "composite_figure.png", dpi=300)
fig.savefig(FIGURES_DIR / "composite_figure.pdf")
plt.close(fig)

print("  All visualizations saved to output/figures/")
print("=== 09_visualizations.py: Complete ===\n")
