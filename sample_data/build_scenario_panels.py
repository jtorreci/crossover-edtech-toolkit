"""
build_scenario_panels.py
Purpose: Build comparison panels from scenario-validation outputs.

Expected inputs:
  - sample_data/scenario_validation/scenario_catalog.csv
  - per-scenario figures under sample_data/scenario_validation/S*/output/figures/
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
SCENARIO_ROOT = ROOT / "scenario_validation"
PANEL_DIR = SCENARIO_ROOT / "panels"
PANEL_DIR.mkdir(parents=True, exist_ok=True)

catalog = pd.read_csv(SCENARIO_ROOT / "scenario_catalog.csv")


def build_panel(panel_name: str, figure_name: str) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    for ax, (_, row) in zip(axes, catalog.iterrows()):
        image_path = Path(row["output_dir"]) / "figures" / figure_name
        img = mpimg.imread(image_path)
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(
            f"{row['scenario_id']} | {row['population_label']}",
            fontsize=10,
            fontweight="bold",
        )

    for ax in axes[len(catalog):]:
        ax.axis("off")

    fig.suptitle(panel_name, fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    slug = panel_name.lower().replace(" ", "_")
    fig.savefig(PANEL_DIR / f"{slug}.png", dpi=300)
    fig.savefig(PANEL_DIR / f"{slug}.pdf")
    plt.close(fig)


def main() -> None:
    build_panel("Interaction plots by synthetic population", "interaction_plot.png")
    build_panel("Carryover diagnostics by synthetic population", "carryover_test.png")
    build_panel("Forest plots by synthetic population", "forest_plot.png")
    build_panel("Composite toolkit outputs by synthetic population", "composite_figure.png")
    print(f"Panels written to: {PANEL_DIR}")


if __name__ == "__main__":
    main()
