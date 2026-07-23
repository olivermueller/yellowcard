"""Section-6 bounds figure: DML estimates with conditional Lee
identification bounds across all outcome windows (count outcomes).

Input: data/multiwindow_results.csv, data/lee_bounds_windows.csv.
Output: fig_bounds.png (300 dpi).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLU, INK, GRID = "#2a78d6", "#1b2733", "#e3e8ee"


def rel(v):
    return float(str(v).replace("%", ""))


def main():
    mw = pd.read_csv("data/multiwindow_results.csv")
    bd = pd.read_csv("data/lee_bounds_windows.csv")
    wins = ["45-50", "45-60", "45-70", "45-80", "45-90"]
    xs = np.arange(len(wins))
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.6), sharex=True)
    axes = axes.ravel()
    for ax, dv, ttl in [(axes[0], "fouls", "Fouls"),
                        (axes[1], "def_engagement", "Defensive engagement"),
                        (axes[2], "pressures", "Pressures"),
                        (axes[3], "tackles", "Tackles")]:
        m = mw[mw.dv == dv].set_index("window")
        b = bd[bd.dv == dv].set_index("window")
        est = [100 * m.loc[w, "ate"] / m.loc[w, "control_mean"] for w in wins]
        ci = [196 * m.loc[w, "se"] / m.loc[w, "control_mean"] for w in wins]
        lo = [rel(b.loc[w, "lee_lo_rel"]) for w in wins]
        hi = [rel(b.loc[w, "lee_hi_rel"]) for w in wins]
        ax.fill_between(xs, lo, hi, color=BLU, alpha=.13, lw=0, zorder=1,
                        label="identification bounds")
        ax.errorbar(xs, est, yerr=ci, fmt="o", color=BLU, ms=6, capsize=4,
                    elinewidth=1.6, zorder=3, label="DML estimate (95% CI)")
        ax.axhline(0, color="#444", lw=1, zorder=2)
        ax.set_xticks(xs)
        ax.set_xticklabels([w.replace("-", "–") + "′" for w in wins], fontsize=9)
        ax.set_title(ttl, loc="left", fontsize=11, fontweight="bold", color=INK)
        ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    for i in (0, 2):
        axes[i].set_ylabel("effect relative to control mean (%)")
    axes[0].legend(fontsize=8.5, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig("fig_bounds.png", dpi=300, facecolor="white")
    print("wrote fig_bounds.png")


if __name__ == "__main__":
    main()
