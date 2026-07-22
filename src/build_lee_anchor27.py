"""27-cell binarized Lee bounds at the 45-50 anchor (backlog C).

Refines the 9-cell scheme with half-time game state (trailing/level/leading):
cells = position x pre-activity tercile x game state. Game state predicts
both withdrawal decisions and second-half fouling, so conditioning on it
should tighten the P(any foul) upper bound that missed zero by +0.8pp in
the 9-cell run. Binary outcomes only; anchor window only.

Output: data/lee_anchor27_binary.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import HGB, build_W, ate
from build_lee_binary import crossfit_bin, BDVS
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

    # half-time score diff per (match, team): period-1 goals from events
    ev_g = pd.read_parquet("data/events.parquet",
        columns=["match_id", "team_id", "period", "minute", "type", "shot_outcome"],
        filters=[("match_id", "in", frame.match_id.unique().tolist())])
    g1 = ev_g[(ev_g.period == 1) & (
        ((ev_g.type == "Shot") & (ev_g.shot_outcome == "Goal")) | (ev_g.type == "Own Goal For"))]
    gt = g1.groupby(["match_id", "team_id"]).size().rename("g").reset_index()
    teams = starters[["match_id", "team_id"]].drop_duplicates()
    teams = teams.merge(gt, on=["match_id", "team_id"], how="left").fillna({"g": 0})
    opp = teams.merge(teams, on="match_id", suffixes=("", "_o"))
    opp = opp[opp.team_id != opp.team_id_o][["match_id", "team_id", "g", "g_o"]]
    opp["gs"] = np.select([opp.g < opp.g_o, opp.g > opp.g_o], ["trail", "lead"], "level")
    gsmap = opp.set_index(["match_id", "team_id"]).gs

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
    E["gs"] = [gsmap.get((m, t), "level") for m, t in zip(E.match_id, E.team_id)]
    E["act"] = pd.qcut(E.pre_n.rank(method="first"), N_ACT, labels=range(N_ACT)).astype(int)
    E["cell"] = E.grp.astype(str) + "|" + E.act.astype(str) + "|" + E.gs
    E["key"] = list(zip(E.match_id, E.player_id))
    T_pop, C_pop = E[E.key.isin(tk)], E[~E.key.isin(bk)]

    elig = starters[starters.exit2 > B]
    f = frame.merge(elig[["match_id", "player_id"]], on=["match_id", "player_id"])
    cand = elig[~elig.in_frame][["match_id", "team_id", "player_id"]]
    extras = mw.build_extras(cand, frame, ev, book)
    counts = mw.window_counts(ev, 2, 45, B)
    d = mw.assemble(f, extras, counts, 15, 45, book)
    for blab, src_col in BDVS.items():
        d[blab] = (d[src_col] > 0).astype(float)
    t = d.treat_yellow_card.values

    ps = {}
    for c in sorted(E.cell.unique()):
        Tc, Cc = T_pop[T_pop.cell == c], C_pop[C_pop.cell == c]
        if len(Tc) < 20:                     # tiny treated cells: fall back to no trim info
            ps[c] = 0.0
            continue
        qt = 1 - (Tc.exit2 <= B).mean()
        qc = 1 - (Cc.exit2 <= B).mean()
        ps[c] = max(0.0, (qc - qt) / qc)
    nz = {k: v for k, v in ps.items() if v > 0}
    print(f"27-cell trims: {len(nz)}/{len(ps)} cells nonzero, range "
          f"{100*min(nz.values()):.1f}-{100*max(nz.values()):.1f}%" if nz else "all zero")

    pre_cols = [c for c in d.columns if c.startswith("pre_player_n_")]
    act = pd.qcut(d[pre_cols].sum(axis=1).rank(method="first"), N_ACT, labels=range(N_ACT)).astype(int)
    gs_frame = np.select([d.ht_score_diff < 0, d.ht_score_diff > 0], ["trail", "lead"], "level")
    cells = (d.position_group.astype(str) + "|" + act.astype(str) + "|" + gs_frame).values

    W = build_W(d)
    T_res, Y_res = crossfit_bin(d, W, list(BDVS))
    rng = np.random.default_rng(0)
    rows = []
    for blab in BDVS:
        est, se, p = ate(T_res, Y_res[blab], d.match_id.values)
        cm = d.loc[t == 0, blab].mean()
        y = d[blab].values
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
            Tr2, Yr2 = crossfit_bin(d2, build_W(d2), [blab])
            bnd, se_b, _ = ate(Tr2, Yr2[blab], d2.match_id.values)
            bounds[side] = (bnd, se_b)
        rows.append(dict(window=f"45-{B}", cells=27, dv=blab, control_p=round(cm, 4),
                         ate_pp=round(100*est, 2), p=round(p, 4),
                         lee_lo_pp=round(100*bounds["lower"][0], 2),
                         lee_hi_pp=round(100*bounds["upper"][0], 2),
                         lee_lo_se_pp=round(100*bounds["lower"][1], 2),
                         lee_hi_se_pp=round(100*bounds["upper"][1], 2),
                         zero_excluded=bool(bounds["upper"][0] < 0 or bounds["lower"][0] > 0)))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)), flush=True)
    pd.DataFrame(rows).to_csv("data/lee_anchor27_binary.csv", index=False)
    print("\nwrote data/lee_anchor27_binary.csv")


if __name__ == "__main__":
    main()
