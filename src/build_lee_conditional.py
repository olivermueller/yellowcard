"""Conditional (cell-based) Lee bounds for the male-sample DML.

Refines the blunt unconditional trim in build_male_dml.py: the trimming
share p(c) and the trim itself are computed WITHIN covariate cells
(position group x pre-window-activity tercile), in the spirit of Lee's
discrete-X extension / Semenova's better Lee bounds. The fat upper tail
of the control outcome distribution is concentrated in high-activity
cells, so cell-wise trimming removes comparable players rather than the
global tail — typically tightening the upper bound substantially.

Per cell c:  p(c) = max(0, (q_C(c) - q_T(c)) / q_C(c)),  q = share still
on the pitch at 60' among starters on the pitch at the end of H1
(computed from events + lineups on this sample's matches).
Bounds: within each cell drop the top / bottom p(c) share of CONTROL
outcomes (seeded tie-break), then re-run the full DML (nuisances refit).

Outputs: data/male_dml_lee_conditional.csv + printed comparison against
the unconditional bounds in data/male_dml_results.csv.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, CARD, load, build_W, crossfit, ate

N_ACT = 3   # activity terciles


def censor_cells(df):
    """Per-cell survival-based trimming shares p(c)."""
    mids = df.match_id.unique().tolist()
    posmap = df.drop_duplicates("position").set_index("position").position_group.to_dict()
    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "period", "minute", "type", "position"] + CARD,
        filters=[("match_id", "in", mids)])
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first().map(posmap).rename("grp"))
    pre = (ev[(ev.period == 1) & (ev.minute < 15)].groupby(["match_id", "player_id"])
             .size().rename("pre_n"))
    sub = ev[(ev.type == "Substitution") & ev.period.le(2)]
    red = ev[card.isin(["Second Yellow", "Red Card"]) & ev.period.le(2)]
    ex = pd.concat([sub, red])[["match_id", "player_id", "period", "minute"]]
    h1_exit = set(zip(*ex[ex.period == 1][["match_id", "player_id"]].values.T))
    exit2 = (ex[ex.period == 2].assign(m=lambda d: d.minute.clip(upper=90))
               .groupby(["match_id", "player_id"]).m.min().rename("exit2"))
    y1 = ev[card.eq("Yellow Card") & (ev.period == 1) & ev.minute.between(15, 45)]
    tk = set(zip(*y1.drop_duplicates(["match_id", "player_id"])[["match_id", "player_id"]].values.T))
    bk = set(zip(*ev[card.eq("Yellow Card") & (ev.period == 1)]
                 [["match_id", "player_id"]].drop_duplicates().values.T))
    lu = pd.read_parquet("data/lineups_male.parquet")
    E = lu[lu.started & lu.match_id.isin(mids)][["match_id", "player_id"]]
    E = E[[k not in h1_exit for k in zip(E.match_id, E.player_id)]].copy()
    E = (E.merge(exit2, on=["match_id", "player_id"], how="left")
           .merge(pos, on=["match_id", "player_id"], how="left")
           .merge(pre, on=["match_id", "player_id"], how="left"))
    E["exit2"] = E.exit2.fillna(999)
    E["pre_n"] = E.pre_n.fillna(0)
    E = E[E.grp.isin(["Defender", "Midfielder", "Forward"])]
    E["act"] = pd.qcut(E.pre_n.rank(method="first"), N_ACT, labels=range(N_ACT)).astype(int)
    E["cell"] = E.grp.astype(str) + "|" + E.act.astype(str)
    E["key"] = list(zip(E.match_id, E.player_id))
    T, C = E[E.key.isin(tk)], E[~E.key.isin(bk)]
    ps = {}
    for c in sorted(E.cell.unique()):
        qt = 1 - (T[T.cell == c].exit2 <= 60).mean()
        qc = 1 - (C[C.cell == c].exit2 <= 60).mean()
        ps[c] = max(0.0, (qc - qt) / qc)
    return ps


def frame_cells(df):
    pre_cols = [c for c in df.columns if c.startswith("pre_player_n_")]
    tot = df[pre_cols].sum(axis=1)
    act = pd.qcut(tot.rank(method="first"), N_ACT, labels=range(N_ACT)).astype(int)
    return (df.position_group.astype(str) + "|" + act.astype(str)).values


def main():
    df = load()
    cells = frame_cells(df)
    ps = censor_cells(df)
    print("per-cell Lee trim p(c):")
    for c, p in sorted(ps.items()):
        print(f"  {c:14s} {100*p:5.1f}%   (frame n={int((cells==c).sum()):,})")

    W = build_W(df)
    groups = df.match_id.values
    t = df.treat_yellow_card.astype(int).values
    T_res, Y_res, _ = crossfit(df, W)

    uncond = pd.read_csv("data/male_dml_results.csv").set_index("dv")
    rng = np.random.default_rng(0)
    rows = []
    print("\n=== conditional Lee bounds ===")
    for dv, lab in DVS.items():
        est, se, p = ate(T_res, Y_res[dv], groups)
        cm = df.loc[t == 0, dv].mean()
        y = df[dv].values.astype(float)
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
            keep = np.setdiff1d(np.arange(len(df)), np.array(drop, dtype=int))
            d2 = df.iloc[keep].reset_index(drop=True)
            Tr2, Yr2, _ = crossfit(d2, build_W(d2))
            b, _, _ = ate(Tr2, Yr2[dv], d2.match_id.values)
            bounds[side] = b
        rows.append(dict(dv=lab, control_mean=round(cm, 3), ate=round(est, 4), p=round(p, 4),
                         cond_lo=round(bounds["lower"], 4), cond_hi=round(bounds["upper"], 4),
                         cond_lo_rel=f"{100*bounds['lower']/cm:+.1f}%",
                         cond_hi_rel=f"{100*bounds['upper']/cm:+.1f}%",
                         uncond_lo_rel=uncond.loc[lab, "lee_lo_rel"],
                         uncond_hi_rel=uncond.loc[lab, "lee_hi_rel"]))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)), flush=True)
    out = pd.DataFrame(rows)
    out.to_csv("data/male_dml_lee_conditional.csv", index=False)
    print("\nwrote data/male_dml_lee_conditional.csv")


if __name__ == "__main__":
    main()
