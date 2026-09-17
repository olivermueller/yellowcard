"""Plausibility check for the Lee worst case (backlog C).

The worst-case (upper) Lee bound assumes the marginal players — booked
players who were withdrawn early and their would-be-withdrawn control
counterparts — are the TOP-TAIL outcome types within each cell. This
script confronts that with data. Among booked players (first yellow in
[15,45], starters, on pitch at the end of H1), it compares those
withdrawn by 60' (incl. half-time) with those kept on:

  (a) printed diagnostics: H1 fouls and the percentile of pre-window
      [0,15) activity within position-matched control survivors;
  (b) figure: standardized mean differences (withdrawn minus kept on,
      pooled SD) over pre-window characteristics, with 95% CIs.

Withdrawn players are absent from the analysis frame (it conditions on
observability), so their covariates are rebuilt from the raw events and
merged from the frame at the player level (age) and team-match level
(win probability, score margin, home).

Output: fig_smd_withdrawn.png + printed comparison tables.
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

COMPS = ["foul_committed", "pressure", "tackle", "ball_recovery",
         "clearance", "block", "interception"]
LABELS = {"foul_committed": "Fouls committed", "pressure": "Pressures",
          "tackle": "Tackles", "ball_recovery": "Ball recoveries",
          "clearance": "Clearances", "block": "Blocks",
          "interception": "Interceptions"}


def smd(a, b):
    """SMD (b minus a) with pooled SD and 95% CI (Hedges & Olkin SE)."""
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    n1, n2 = len(a), len(b)
    sp = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    d = (b.mean() - a.mean()) / sp if sp > 0 else 0.0
    se = np.sqrt(1 / n1 + 1 / n2 + d ** 2 / (2 * (n1 + n2)))
    return d, 1.96 * se


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
    pre_ev = ev[(ev.period == 1) & (ev.minute < 15)]
    pre = pre_ev.groupby(["match_id", "player_id"]).size().rename("pre_n")
    pre_c = (pre_ev[pre_ev.tn.isin(COMPS)]
             .groupby(["match_id", "player_id", "tn"]).size()
             .unstack(fill_value=0).reindex(columns=COMPS, fill_value=0))
    h1f = (ev[(ev.period == 1) & ev.tn.eq("foul_committed")]
             .groupby(["match_id", "player_id"]).size().rename("h1_fouls"))
    E = lu[lu.started][["match_id", "player_id", "team_id"]]
    E = E[[k not in h1x for k in zip(E.match_id, E.player_id)]].copy()
    E = (E.merge(e2, on=["match_id", "player_id"], how="left")
           .merge(pos, on=["match_id", "player_id"], how="left")
           .merge(pre, on=["match_id", "player_id"], how="left")
           .merge(pre_c, on=["match_id", "player_id"], how="left")
           .merge(h1f, on=["match_id", "player_id"], how="left"))
    E["exit2"] = E.exit2.fillna(999)
    for c in ["pre_n", "h1_fouls"] + COMPS:
        E[c] = E[c].fillna(0)
    E = E[E.grp.isin(["Defender", "Midfielder", "Forward"])]
    E["key"] = list(zip(E.match_id, E.player_id))

    # covariates from the frame: age at player level (dob + match date),
    # win probability / score margin / home at team-match level
    dob = (frame.dropna(subset=["dob"]).drop_duplicates("player_id")
                .set_index("player_id").dob)
    mdate = frame.drop_duplicates("match_id").set_index("match_id").match_date
    tm = (frame.drop_duplicates(["match_id", "team_id"])
               [["match_id", "team_id", "odds_p_win", "pre_score_diff", "home_away"]])
    E = E.merge(tm, on=["match_id", "team_id"], how="left")
    E["age"] = ((pd.to_datetime(E.match_id.map(mdate))
                 - pd.to_datetime(E.player_id.map(dob))).dt.days / 365.25)
    E["home"] = (E.home_away == "home").astype(float)

    ctrl = E[~E.key.isin(bk)].copy()                       # unbooked
    booked = E[E.key.isin(tk)].copy()
    booked["withdrawn"] = booked.exit2 <= 60
    ctrl_surv = ctrl[ctrl.exit2 > 60]
    kept, wdr = booked[~booked.withdrawn], booked[booked.withdrawn]

    groups = {"Control survivors": ctrl_surv,
              "Booked, kept on": kept,
              "Booked, withdrawn by 60'": wdr}
    print("n per group:", {k: len(v) for k, v in groups.items()})

    # (a) printed diagnostics (unchanged)
    tab = {}
    for name, g in groups.items():
        f = g.h1_fouls
        tab[name] = [100 * (f == 0).mean(), 100 * (f == 1).mean(), 100 * (f >= 2).mean()]
    print("\nH1 fouls committed (%):")
    print(pd.DataFrame(tab, index=["0 fouls", "1 foul", "2+ fouls"]).round(1).to_string())

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

    # (b) SMD dot plot: withdrawn minus kept on, pre-window characteristics
    chars = ([("Total events", "pre_n")]
             + [(LABELS[c], c) for c in COMPS]
             + [("Score margin at 15'", "pre_score_diff"),
                ("Pre-match win probability", "odds_p_win"),
                ("Home team", "home"), ("Age", "age")])
    for grp_name in ["Defender", "Midfielder", "Forward"]:
        kept[grp_name] = (kept.grp == grp_name).astype(float)
        wdr[grp_name] = (wdr.grp == grp_name).astype(float)
    chars += [("Defender", "Defender"), ("Midfielder", "Midfielder"),
              ("Forward", "Forward")]

    rows = [(lbl, *smd(kept[col].astype(float).values, wdr[col].astype(float).values))
            for lbl, col in chars]
    print("\nSMD (withdrawn - kept on):")
    for lbl, d, ci in rows:
        print(f"  {lbl:26s} {d:+.3f} +- {ci:.3f}")

    labels = [r[0] for r in rows]
    ds = np.array([r[1] for r in rows]); cis = np.array([r[2] for r in rows])
    y = np.arange(len(rows))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    ax.axvline(0, color=INK, lw=1.0, zorder=1)
    for v in (-0.1, 0.1):
        ax.axvline(v, color="#9aa3ad", lw=1.0, ls="--", zorder=1)
    ax.errorbar(ds, y, xerr=cis, fmt="o", color=BLU, ecolor=BLU,
                elinewidth=1.2, capsize=2.5, ms=5.5, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel("standardized mean difference (withdrawn $-$ kept on)")
    ax.grid(axis="x", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
    for sp in ["top", "right", "left"]: ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    fig.savefig("fig_smd_withdrawn.png", dpi=300, facecolor="white")
    print("\nwrote fig_smd_withdrawn.png")


if __name__ == "__main__":
    main()
