"""Propensity-overlap figure (manuscript Appendix C).

fig_overlap.png      Distribution of the cross-fitted booking propensity
                     e(W) by treatment status (log-count histograms).

The Cinelli-Hazlett contour figure was removed from the manuscript
(2026-07-28); Section 6.2 reports the robustness values in text only.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import HGB, build_W, load

BLU, YEL, GRID = "#2a78d6", "#eda100", "#e3e8ee"


def main():
    df = load()
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    groups = df.match_id.values
    cv = GroupKFold(5)
    e = cross_val_predict(HistGradientBoostingClassifier(**HGB), W, t, groups=groups,
                          cv=cv, n_jobs=-1, method="predict_proba")[:, 1]

    fig, ax = plt.subplots(figsize=(8.5, 4))
    bins = np.linspace(0, e.max() * 1.02, 45)
    ax.hist(e[t == 0], bins=bins, color=BLU, alpha=.55, label="unbooked", zorder=2)
    ax.hist(e[t == 1], bins=bins, color=YEL, alpha=.75, label="booked", zorder=3)
    ax.set_yscale("log")
    ax.set_xlabel("cross-fitted booking propensity $\\hat{e}(W)$")
    ax.set_ylabel("player-matches (log scale)")
    ax.legend(frameon=False)
    ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig("fig_overlap.png", dpi=300, facecolor="white")
    print("wrote fig_overlap.png")


if __name__ == "__main__":
    main()
