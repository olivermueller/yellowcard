"""Section-6 figure: binarized-outcome Lee bounds with Imbens-Manski CIs.

Per outcome and window: DML point estimate (percentage points), the
conditional Lee identification bounds (shaded band), and the 95%
Imbens-Manski interval for the partially identified effect (whiskers).

Input:  data/lee_bounds_binary_im.csv
Output: fig_bounds_binary.png (300 dpi).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLU, INK, GRID = "#2a78d6", "#1b2733", "#e3e8ee"
# restricted to the outcomes with significant Section-5 effects (Oliver, 2026-07-29);
# bounds for the null outcomes remain in data/lee_bounds_binary_im.csv
PANELS = [("any_def_action", "Defensive actions"), ("any_pressure", "Pressures"),
          ("any_foul", "Fouls")]


def main():
    b = pd.read_csv("data/lee_bounds_binary_im.csv")
    wins = ["45-50", "45-60", "45-70", "45-80", "45-90"]
    xs = np.arange(len(wins))
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), sharex=True)
    axes = axes.ravel()
    for ax, (dv, ttl) in zip(axes, PANELS):
        d = b[b.dv == dv].set_index("window").loc[wins]
        ax.fill_between(xs, d.lee_lo_pp, d.lee_hi_pp, color=BLU, alpha=.18, lw=0,
                        zorder=1, label="identification bounds")
        ax.errorbar(xs, (d.lee_lo_pp + d.lee_hi_pp) / 2,
                    yerr=[(d.lee_lo_pp + d.lee_hi_pp) / 2 - d.ci_lo_pp,
                          d.ci_hi_pp - (d.lee_lo_pp + d.lee_hi_pp) / 2],
                    fmt="none", ecolor=BLU, elinewidth=1.1, capsize=3, zorder=2,
                    label="Imbens–Manski 95% CI")
        ax.plot(xs, d.ate_pp, "o", color=INK, ms=5, zorder=3, label="DML estimate")
        ax.axhline(0, color="#444", lw=1, zorder=2)
        ax.set_xticks(xs)
        ax.set_xticklabels([w.replace("-", "–") + "′" for w in wins], fontsize=9)
        ax.set_title(ttl, loc="left", fontsize=11, fontweight="bold", color=INK)
        ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("effect on probability (pp)")
    axes[0].legend(fontsize=8.5, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig("fig_bounds_binary.png", dpi=300, facecolor="white")
    print("wrote fig_bounds_binary.png")


if __name__ == "__main__":
    main()
