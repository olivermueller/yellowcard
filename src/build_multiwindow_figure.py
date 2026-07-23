"""Multi-window effect profile (paper F3, 'money figure').

Relative DML effects on fouls and defensive engagement across the H2
outcome windows 45-50/60/70/80 (points, 95% cluster-robust CIs) with the
conditional Lee identification bounds as a shaded band, plus the 30-45
within-half placebo (treatment 15-30) as a separated open marker.

Inputs: data/multiwindow_results.csv, data/lee_bounds_windows_im.csv.
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
    bd = pd.read_csv("data/lee_bounds_windows_im.csv")
    wins = ["45-50", "45-60", "45-70", "45-80"]
    xs = np.arange(len(wins))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for ax, dv, ttl in [(axes[0], "fouls", "Fouls"),
                        (axes[1], "def_engagement", "Defensive engagement")]:
        m = mw[mw.dv == dv].set_index("window")
        b = bd[bd.dv == dv].set_index("window")
        est = [100 * m.loc[w, "ate"] / m.loc[w, "control_mean"] for w in wins]
        ci = [196 * m.loc[w, "se"] / m.loc[w, "control_mean"] for w in wins]
        lo = [rel(b.loc[w, "lee_lo_rel"]) for w in wins]
        hi = [rel(b.loc[w, "lee_hi_rel"]) for w in wins]
        ax.fill_between(xs, lo, hi, color=BLU, alpha=.13, lw=0, zorder=1,
                        label="Lee identification bounds")
        ax.errorbar(xs, est, yerr=ci, fmt="o", color=BLU, ms=6, capsize=4,
                    elinewidth=1.6, zorder=3, label="DML estimate (95% CI)")
        # within-half placebo (30-45, treatment 15-30)
        pl = mw[(mw.dv == dv) & (mw.window == "30-45")].iloc[0]
        pe = 100 * pl.ate / pl.control_mean
        pc = 196 * pl.se / pl.control_mean
        ax.errorbar([-1.1], [pe], yerr=[pc], fmt="o", mfc="white", color=RED,
                    ms=6, capsize=4, elinewidth=1.6, zorder=3,
                    label="within-half placebo (30–45′)")
        ax.axvline(-0.55, color=MUT, lw=1, ls=":")
        ax.axhline(0, color="#444", lw=1, zorder=2)
        ax.set_xticks(np.concatenate([[-1.1], xs]))
        ax.set_xticklabels(["30–45′\n(T: 15–30′)"] + [w.replace("-", "–") + "′" for w in wins],
                           fontsize=9)
        ax.set_title(ttl, loc="left", fontsize=11, fontweight="bold", color=INK)
        ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("effect relative to control mean (%)")
    axes[0].legend(fontsize=8.5, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig("fig_multiwindow.png", dpi=300, facecolor="white")
    print("wrote fig_multiwindow.png")


if __name__ == "__main__":
    main()
