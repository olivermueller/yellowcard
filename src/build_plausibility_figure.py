"""Plausibility check for the Lee worst case (backlog C).

The worst-case (upper) Lee bound assumes the marginal players — booked
players who were withdrawn early and their would-be-withdrawn control
counterparts — are the TOP-TAIL outcome types within each cell. This
script confronts that with data: among booked players (first yellow in
[15,45], starters, on pitch at the end of H1), compare those withdrawn
by 60' (incl. half-time) with those kept on, and with unbooked control
survivors, on their observable H1 profiles:

  (a) H1 fouls committed (0 / 1 / 2+ shares) — the outcome-correlated
      dimension the worst case needs to be extreme;
  (b) percentile of pre-window [0,15) total activity within the control
      survivors of the same position group.

If withdrawn booked players are NOT concentrated in the top tail, the
worst-case allocation is implausible and the bounds are conservative.

Output: fig_plausibility_withdrawn.png + printed comparison table.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_multiwindow as mw

BLU, YEL, RED, INK, GRID = "#2a78d6", "#eda100", "#e34948", "#1b2733", "#e3e8ee"


def main():
    frame, ev, lu = mw.load_all()
    h1x, e2 = mw.exits(ev)
    card = ev[mw.CARD[0]].where(ev[mw.CARD[0]].notna(), ev[mw.CARD[1]])
    y1 = ev[card.eq("Yellow Card") & (ev.period == 1) & ev.minute.between(15, 45)]
    tk = set(zip(*y1.drop_duplicates(["match_id", "player_id"])[["match_id", "player_id"]].values.T))
    bk = set(zip(*ev[card.eq("Yellow Card") & (ev.period == 1)]
                 [["match_id", "player_id"]].drop_duplicates().values.T))

    # population: starters on pitch at end of H1, outfield
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first()
             .map(frame.drop_duplicates("position").set_index("position").position_group.to_dict())
             .rename("grp"))
    pre = (ev[(ev.period == 1) & (ev.minute < 15)].groupby(["match_id", "player_id"])
             .size().rename("pre_n"))
    h1f = (ev[(ev.period == 1) & ev.tn.eq("foul_committed")]
             .groupby(["match_id", "player_id"]).size().rename("h1_fouls"))
    E = lu[lu.started][["match_id", "player_id"]]
    E = E[[k not in h1x for k in zip(E.match_id, E.player_id)]].copy()
    E = (E.merge(e2, on=["match_id", "player_id"], how="left")
           .merge(pos, on=["match_id", "player_id"], how="left")
           .merge(pre, on=["match_id", "player_id"], how="left")
           .merge(h1f, on=["match_id", "player_id"], how="left"))
    E["exit2"] = E.exit2.fillna(999)
    E["pre_n"] = E.pre_n.fillna(0)
    E["h1_fouls"] = E.h1_fouls.fillna(0)
    E = E[E.grp.isin(["Defender", "Midfielder", "Forward"])]
    E["key"] = list(zip(E.match_id, E.player_id))

    ctrl = E[~E.key.isin(bk)].copy()                       # unbooked
    booked = E[E.key.isin(tk)].copy()
    booked["withdrawn"] = booked.exit2 <= 60
    ctrl_surv = ctrl[ctrl.exit2 > 60]

    groups = {"Control survivors": ctrl_surv,
              "Booked, kept on": booked[~booked.withdrawn],
              "Booked, withdrawn by 60'": booked[booked.withdrawn]}
    print("n per group:", {k: len(v) for k, v in groups.items()})

    # (a) H1 foul distribution
    tab = {}
    for name, g in groups.items():
        f = g.h1_fouls
        tab[name] = [100 * (f == 0).mean(), 100 * (f == 1).mean(), 100 * (f >= 2).mean()]
    print("\nH1 fouls committed (%):")
    print(pd.DataFrame(tab, index=["0 fouls", "1 foul", "2+ fouls"]).round(1).to_string())

    # (b) pre-activity percentile within control survivors of same position
    pct = {}
    for name, g in groups.items():
        vals = []
        for grp_name, gg in g.groupby("grp"):
            ref = np.sort(ctrl_surv[ctrl_surv.grp == grp_name].pre_n.values)
            vals.append(100 * np.searchsorted(ref, gg.pre_n.values, side="left") / len(ref))
        pct[name] = np.concatenate(vals)
    print("\npre-window activity percentile (vs control survivors, same position):")
    for k, v in pct.items():
        print(f"  {k:26s} mean {v.mean():5.1f} | median {np.median(v):5.1f} | share in top decile {100*(v>=90).mean():4.1f}%")

    # ---- figure ----
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    colors = {"Control survivors": BLU, "Booked, kept on": YEL, "Booked, withdrawn by 60'": RED}

    ax = axes[0]
    x = np.arange(3); wdt = 0.26
    for i, (name, vals) in enumerate(tab.items()):
        ax.bar(x + (i - 1) * wdt, vals, wdt, color=colors[name], label=name, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(["0 fouls", "1 foul", "2+ fouls"])
    ax.set_ylabel("share of group (%)")
    ax.set_title("First-half fouls committed", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    ax.legend(fontsize=8.5, frameon=False)

    ax = axes[1]
    bins = np.arange(0, 105, 10)
    for name, v in pct.items():
        h, edges = np.histogram(v, bins=bins)
        ax.plot(edges[:-1] + 5, 100 * h / len(v), color=colors[name], lw=2, marker="o", ms=4, label=name, zorder=2)
    ax.axhline(10, color="#9aa3ad", lw=1, ls="--", zorder=1)
    ax.text(2, 10.6, "uniform reference", fontsize=8, color="#9aa3ad")
    ax.set_xlabel("pre-window activity percentile (within position, vs control survivors)")
    ax.set_ylabel("share of group (%)")
    ax.set_title("Where do booked players sit in the activity distribution?",
                 loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("fig_plausibility_withdrawn.png", dpi=200, facecolor="white")
    print("\nwrote fig_plausibility_withdrawn.png")


if __name__ == "__main__":
    main()
