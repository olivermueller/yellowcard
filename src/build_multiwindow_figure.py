"""Multi-window effect profile (paper Figure 3).

Relative DML effects on the defensive-actions aggregate and all
components across the H2 outcome windows (points, 95% cluster-robust
CIs). Marker convention mirrors the heterogeneity figure: filled =
significant at the 5% level, open = not.

Input:  data/multiwindow_results.csv
Output: fig_multiwindow.png (300 dpi).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLU, INK, GRID, MUT, RED = "#2a78d6", "#1b2733", "#e3e8ee", "#9aa3ad", "#e34948"


def rel(v):  # "+12.3%" -> 12.3
    return float(str(v).replace("%", ""))


def main():
    mw = pd.read_csv("data/multiwindow_results.csv")
    wins = ["45-50", "45-60", "45-70", "45-80", "45-90"]
    xs = np.arange(len(wins))

    # column per category: left opponent-directed, right ball-directed
    panels = [("opp_directed", "Opponent-directed (aggregate)"),
              ("ball_directed", "Ball-directed (aggregate)"),
              ("fouls", "Fouls"), ("ball_recoveries", "Ball recoveries"),
              ("pressures", "Pressures"), ("clearances", "Clearances"),
              ("tackles", "Tackles"), ("blocks", "Blocks"),
              (None, None), ("interceptions", "Interceptions")]
    fig, axes = plt.subplots(5, 2, figsize=(11, 16.5), sharex=True)
    axes = axes.ravel()
    for ax, (dv, ttl) in zip(axes, panels):
        if dv is None:
            ax.axis("off")
            continue
        m = mw[mw.dv == dv].set_index("window")
        est = np.array([100 * m.loc[w, "ate"] / m.loc[w, "control_mean"] for w in wins])
        ci = np.array([196 * m.loc[w, "se"] / m.loc[w, "control_mean"] for w in wins])
        sig = np.array([m.loc[w, "p"] < .05 for w in wins])
        ax.errorbar(xs, est, yerr=ci, fmt="none", ecolor=BLU, capsize=4,
                    elinewidth=1.6, zorder=2)
        ax.plot(xs[sig], est[sig], "o", color=BLU, ms=7, zorder=3,
                label="significant at 5%")
        ax.plot(xs[~sig], est[~sig], "o", mfc="white", mec=BLU, mew=1.6, ms=7,
                zorder=3, label="not significant")
        ax.axhline(0, color="#444", lw=1, zorder=2)
        ax.set_xticks(xs)
        ax.set_xticklabels([w.replace("-", "–") + "′" for w in wins], fontsize=9)
        ax.set_title(ttl, loc="left", fontsize=11, fontweight="bold", color=INK)
        ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    for i in (0, 2, 4, 6):
        axes[i].set_ylabel("effect relative to control mean (%)")
    axes[9].tick_params(labelbottom=True)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="none", color=BLU, ms=7,
                      label="significant at the 5% level"),
               Line2D([], [], marker="o", ls="none", mfc="white", mec=BLU, mew=1.6,
                      ms=7, label="not significant"),
               Line2D([], [], color=BLU, lw=1.6, label="95% CI")]
    fig.legend(handles=handles, fontsize=9.5, frameon=False, ncol=3,
               loc="upper center", bbox_to_anchor=(0.5, 0.995))
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig("fig_multiwindow.png", dpi=300, facecolor="white")
    print("wrote fig_multiwindow.png")


if __name__ == "__main__":
    main()
