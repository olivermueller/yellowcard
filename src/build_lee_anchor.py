"""Conditional Lee bounds at the 45-50 anchor window (backlog C).

Rebuilds the 45-50 multi-window dataset (build_multiwindow logic: starters,
no H1 exit, on pitch through 50', censored-in-(50,60] players restored) and
computes cell-based conditional Lee bounds exactly as build_lee_conditional
does for 45-60, but with censoring measured at 50': per cell
(position x pre-activity tercile), p(c) from treated-vs-control survival to
50' among starters on the pitch at the end of H1; trim top/bottom p(c) of
control outcomes within cells; full DML re-run per side.

Output: data/lee_anchor_45_50.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, build_W, crossfit, ate
import build_multiwindow as mw

B = 50
N_ACT = 3


def main():
    frame, ev, lu = mw.load_all()
    h1x, e2 = mw.exits(ev)
    book = mw.bookings(ev)
    starters = lu[lu.started][["match_id", "team_id", "player_id"]]
    starters = starters[[k not in h1x for k in zip(starters.match_id, starters.player_id)]]
    starters = starters.merge(e2, on=["match_id", "player_id"], how="left")
    starters["exit2"] = starters.exit2.fillna(999)
    fkeys = set(zip(frame.match_id, frame.player_id))
    starters["in_frame"] = [k in fkeys for k in zip(starters.match_id, starters.player_id)]

    # ---- assemble the 45-50 dataset (as in build_multiwindow) ----
    elig = starters[starters.exit2 > B]
    f = frame.merge(elig[["match_id", "player_id"]], on=["match_id", "player_id"])
    cand = elig[~elig.in_frame][["match_id", "team_id", "player_id"]]
    extras = mw.build_extras(cand, frame, ev, book)
    counts = mw.window_counts(ev, 2, 45, B)
    d = mw.assemble(f, extras, counts, 15, 45, book)
    t = d.treat_yellow_card.values
    print(f"anchor 45-{B}: n={len(d):,} treated={int(t.sum()):,}")

    # ---- per-cell trimming shares from survival to 50' ----
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first()
             .map(frame.drop_duplicates("position").set_index("position").position_group.to_dict())
             .rename("grp"))
    pre = (ev[(ev.period == 1) & (ev.minute < 15)].groupby(["match_id", "player_id"])
             .size().rename("pre_n"))
    card = ev[mw.CARD[0]].where(ev[mw.CARD[0]].notna(), ev[mw.CARD[1]])
    y1 = ev[card.eq("Yellow Card") & (ev.period == 1) & ev.minute.between(15, 45)]
    tk = set(zip(*y1.drop_duplicates(["match_id", "player_id"])[["match_id", "player_id"]].values.T))
    bk = set(zip(*ev[card.eq("Yellow Card") & (ev.period == 1)]
                 [["match_id", "player_id"]].drop_duplicates().values.T))
    E = (starters.merge(pos, on=["match_id", "player_id"], how="left")
                 .merge(pre, on=["match_id", "player_id"], how="left"))
    E["pre_n"] = E.pre_n.fillna(0)
    E = E[E.grp.isin(["Defender", "Midfielder", "Forward"])]
    E["act"] = pd.qcut(E.pre_n.rank(method="first"), N_ACT, labels=range(N_ACT)).astype(int)
    E["cell"] = E.grp.astype(str) + "|" + E.act.astype(str)
    E["key"] = list(zip(E.match_id, E.player_id))
    T, C = E[E.key.isin(tk)], E[~E.key.isin(bk)]
    ps = {}
    for c in sorted(E.cell.unique()):
        qt = 1 - (T[T.cell == c].exit2 <= B).mean()
        qc = 1 - (C[C.cell == c].exit2 <= B).mean()
        ps[c] = max(0.0, (qc - qt) / qc)
    print("per-cell trim p(c):", {k: f"{100*v:.1f}%" for k, v in ps.items()})

    # frame cells for the assembled dataset
    pre_cols = [c for c in d.columns if c.startswith("pre_player_n_")]
    tot = d[pre_cols].sum(axis=1)
    act = pd.qcut(tot.rank(method="first"), N_ACT, labels=range(N_ACT)).astype(int)
    cells = (d.position_group.astype(str) + "|" + act.astype(str)).values

    # ---- ATE + conditional bounds ----
    W = build_W(d)
    T_res, Y_res, _ = crossfit(d, W)
    rng = np.random.default_rng(0)
    rows = []
    for dv, lab in DVS.items():
        est, se, p = ate(T_res, Y_res[dv], d.match_id.values)
        cm = d.loc[t == 0, dv].mean()
        y = d[dv].values.astype(float)
        bounds = {}
        for side in ["upper", "lower"]:
            drop = []
            for c, pc in ps.items():
                idx = np.where((cells == c) & (t == 0))[0]
                n_trim = int(round(pc * len(idx)))
                if n_trim == 0:
                    continue
                order = idx[np.lexsort((rng.random(len(idx)), y[idx]))]
                drop.extend(order[-n_trim:] if side == "upper" else order[:n_trim])
            keep = np.setdiff1d(np.arange(len(d)), np.array(drop, dtype=int))
            d2 = d.iloc[keep].reset_index(drop=True)
            Tr2, Yr2, _ = crossfit(d2, build_W(d2))
            b, _, _ = ate(Tr2, Yr2[dv], d2.match_id.values)
            bounds[side] = b
        rows.append(dict(window=f"45-{B}", dv=lab, control_mean=round(cm, 3),
                         ate=round(est, 4), se=round(se, 4), p=round(p, 4),
                         rel=f"{100*est/cm:+.1f}%",
                         lee_lo=round(bounds["lower"], 4), lee_hi=round(bounds["upper"], 4),
                         lee_lo_rel=f"{100*bounds['lower']/cm:+.1f}%",
                         lee_hi_rel=f"{100*bounds['upper']/cm:+.1f}%"))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)), flush=True)
    pd.DataFrame(rows).to_csv("data/lee_anchor_45_50.csv", index=False)
    print("\nwrote data/lee_anchor_45_50.csv")


if __name__ == "__main__":
    main()
