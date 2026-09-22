"""Appendix figure: frequency of the seven defensive-action components
over the match clock.

Per event type, mean events per match in 5-minute brackets (stoppage time
folded into the 40-45 and 85-90 brackets), with 95% confidence intervals
for the bracket mean across the 2,440 matches. Panel colour marks
the category (opponent-directed vs ball-directed).

Output: figures/fig_event_freq.png (300 dpi).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dml import load
from build_multiwindow import tname

BLU, YEL, INK, GRID = "#2a78d6", "#eda100", "#1b2733", "#e3e8ee"
PANELS = [("pressure", "Pressures", BLU), ("tackle", "Tackles", BLU),
          ("foul_committed", "Fouls", BLU), ("ball_recovery", "Ball recoveries", YEL),
          ("clearance", "Clearances", YEL), ("block", "Blocks", YEL),
          ("interception", "Interceptions", YEL)]


def main():
    Path("figures").mkdir(exist_ok=True)
    df = load()
    mids = df.match_id.unique()
    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "period", "minute", "type", "duel_type"],
        filters=[("match_id", "in", mids.tolist())])
    ev = ev[ev.period.isin([1, 2])]
    ev["tn"] = [tname(t, d) for t, d in zip(ev.type, ev.duel_type)]
    ev = ev[ev.tn.isin([p[0] for p in PANELS])]
    # 5-minute brackets; H1 stoppage folds into 40-45, H2 stoppage into 85-90
    m1 = np.minimum(ev.minute, 44)
    m2 = 45 + np.minimum(ev.minute - 45, 44)
    ev["bracket"] = np.where(ev.period == 1, (m1 // 5) * 5, ((m2 - 45) // 5) * 5 + 45)

    brackets = np.arange(0, 90, 5)
    n = len(mids)
    fig, axes = plt.subplots(4, 2, figsize=(11, 13.5), sharex=True)
    axes = axes.ravel()
    for ax, (tn, ttl, col) in zip(axes, PANELS):
        c = (ev[ev.tn == tn].groupby(["match_id", "bracket"]).size()
               .unstack(fill_value=0).reindex(index=mids, columns=brackets, fill_value=0))
        mean = c.mean(axis=0).values
        ci = 1.96 * c.std(axis=0).values / np.sqrt(n)
        ax.bar(brackets + 2.5, mean, width=4.4, color=col, zorder=2)
        ax.errorbar(brackets + 2.5, mean, yerr=ci, fmt="none", ecolor=INK,
                    elinewidth=1.0, capsize=2.5, zorder=3)
        ax.axvline(45, color="#9aa3ad", lw=1.2, ls="--", zorder=1)
        ax.set_title(ttl, loc="left", fontsize=11, fontweight="bold", color=INK)
        ax.set_xticks(np.arange(0, 91, 15))
        ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    axes[7].axis("off")
    for i in (0, 2, 4, 6):
        axes[i].set_ylabel("events per match")
    for i in (5, 6):
        axes[i].set_xlabel("minute (5-minute brackets)")
    axes[6].tick_params(labelbottom=True)
    fig.tight_layout()
    fig.savefig("figures/fig_event_freq.png", dpi=300, facecolor="white")
    print("wrote figures/fig_event_freq.png")


if __name__ == "__main__":
    main()
