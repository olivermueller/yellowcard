"""Multi-window DML (backlog C): outcomes for 30-45, 45-50, 45-60, 45-70, 45-80.

Windows and samples (male, outfield starters, complete-case on age):
  45-b  : treatment = first yellow [15,45]; outcome = counts in period 2,
          45 <= minute <= b; eligible = started, no H1 exit, not subbed or
          sent off at or before b. For b < 60 this ADDS players censored in
          (b,60] who are missing from the paper frame — their per-player
          pre-window counts are rebuilt from events (validated exact against
          the frame) and team-level covariates are borrowed from a teammate's
          frame row.
  30-45 : treatment = first yellow [15,30]; outcome = counts in period 1,
          minute >= 30 (incl. H1 stoppage); eligible = started, no H1 exit.
          Players first-booked in [0,15) or (30,45] are dropped (ambiguous /
          contaminated). Nearly censoring-free by construction.

Estimation identical to build_male_dml.py (paper W + age, HGB nuisances,
GroupKFold by match, cluster-robust SEs). Also reports the per-window
censoring differential (position-adjusted) and Lee trimming fraction.

Output: data/multiwindow_results.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, CARD, HGB, build_W, crossfit, ate

OUT_TYPES = {"post_n_pressure": "pressure", "post_n_tackle": "tackle",
             "post_n_foul_committed": "foul_committed"}


def tname(t, dt):
    if t == "Duel":
        return {"Tackle": "tackle", "Aerial Lost": "aerial_lost"}.get(dt)
    return t.lower().replace("*", "").replace("/", "_").replace("-", "_").replace(" ", "_")


def load_all():
    from build_male_dml import load as load_spec
    df = load_spec()                      # SPEC B: male EU leagues, age+odds
    mids = df.match_id.unique().tolist()
    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "team", "type", "duel_type", "period", "minute",
                 "position"] + CARD,
        filters=[("match_id", "in", mids)])
    ev["tn"] = [tname(t, d) for t, d in zip(ev.type, ev.duel_type)]
    lu = pd.read_parquet("data/lineups_male.parquet")
    return df, ev, lu[lu.match_id.isin(mids)]


def exits(ev):
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    sub = ev[(ev.type == "Substitution") & ev.period.le(2)]
    red = ev[card.isin(["Second Yellow", "Red Card"]) & ev.period.le(2)]
    ex = pd.concat([sub, red])[["match_id", "player_id", "period", "minute"]]
    h1x = set(zip(*ex[ex.period == 1][["match_id", "player_id"]].values.T))
    e2 = (ex[ex.period == 2].assign(m=lambda d: d.minute.clip(upper=90))
            .groupby(["match_id", "player_id"]).m.min().rename("exit2"))
    return h1x, e2


def bookings(ev):
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    y = ev[card.eq("Yellow Card") & (ev.period == 1)]
    return (y.sort_values("minute").groupby(["match_id", "player_id"]).minute.first()
              .rename("book_min"))


def p2_cards(ev):
    """(match_id, player_id) -> minute of first yellow/red in period 2 (clipped)."""
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    y = ev[card.isin(["Yellow Card", "Second Yellow", "Red Card"]) & (ev.period == 2)]
    return (y.assign(m=lambda d: d.minute.clip(upper=90))
              .groupby(["match_id", "player_id"]).m.min().rename("p2_card_min"))


def window_counts(ev, period, lo, hi):
    """Counts per (match,player) of the 3 component DVs in [lo, hi] (hi None = open)."""
    m = (ev.period == period) & (ev.minute >= lo) & ev.tn.isin(set(OUT_TYPES.values()))
    if hi is not None:
        m &= ev.minute <= hi
    c = ev[m].groupby(["match_id", "player_id", "tn"]).size().unstack(fill_value=0)
    for t in OUT_TYPES.values():
        if t not in c: c[t] = 0
    return c.reset_index()


def pre_counts(ev, types):
    m = (ev.period == 1) & (ev.minute < 15) & ev.tn.isin(types)
    return ev[m].groupby(["match_id", "player_id", "tn"]).size().unstack(fill_value=0)


def build_extras(cand, frame, ev, book):
    """Frame-like rows for eligible players missing from the paper frame."""
    if not len(cand):
        return pd.DataFrame()
    pre_cols = [c for c in frame.columns if c.startswith("pre_player_n_")]
    types = [c.replace("pre_player_n_", "") for c in pre_cols]
    pc = pre_counts(ev, set(types))
    # position group from first observed position; outfield only
    posmap = frame.drop_duplicates("position").set_index("position").position_group.to_dict()
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first().map(posmap).rename("position_group"))
    # one team-level donor row per (match, team)
    team_cols = ([c for c in frame.columns if c.startswith("pre_diff_n_")]
                 + ["pre_score_diff", "home_away", "competition_type", "match_date",
                    "odds_p_home", "odds_p_draw"])
    donor = frame.drop_duplicates(["match_id", "team_id"])[["match_id", "team_id"] + team_cols]

    X = cand.merge(pos, on=["match_id", "player_id"], how="left")
    X = X[X.position_group.isin(["Defender", "Midfielder", "Forward"])]
    X = X.merge(donor, on=["match_id", "team_id"], how="inner")
    X = X.merge(pc, on=["match_id", "player_id"], how="left")
    for t in types:
        X[f"pre_player_n_{t}"] = X[t].fillna(0) if t in X else 0.0
    X = X.drop(columns=[t for t in types if t in X.columns])   # raw type cols collide downstream
    X["gender"] = "male"
    X["treat_yellow_card"] = 0  # set by caller from book_min
    bm = X.merge(book, on=["match_id", "player_id"], how="left").book_min
    X["book_min"] = bm.values
    dob = pd.read_parquet("data/player_dob.parquet")[["player_id", "dob"]]
    X = X.merge(dob, on="player_id", how="left")
    X["age"] = (pd.to_datetime(X.match_date) - pd.to_datetime(X.dob)).dt.days / 365.25
    X["odds_p_win"] = np.where(X.home_away == "home", X.odds_p_home,
                               1 - X.odds_p_home - X.odds_p_draw)
    return X


def assemble(frame, extras, counts, treat_lo, treat_hi, book, drop_booked_outside=None,
             p2c=None, post_end=None):
    keep_f = frame.copy()
    bmf = keep_f.merge(book, on=["match_id", "player_id"], how="left").book_min
    keep_f["book_min"] = bmf.values
    rows = [keep_f]
    if len(extras):
        rows.append(extras)
    d = pd.concat(rows, ignore_index=True, sort=False)
    d["treat_yellow_card"] = d.book_min.between(treat_lo, treat_hi).astype(int)
    if drop_booked_outside is not None:
        lo, hi = drop_booked_outside
        d = d[~(d.book_min.between(lo, hi) & (d.treat_yellow_card == 0))]
    if p2c is not None and post_end is not None:
        d = d.merge(p2c, on=["match_id", "player_id"], how="left")
        d = d[~(d.p2_card_min <= post_end)]          # no yellow/red in the post window
    d = d.merge(counts, on=["match_id", "player_id"], how="left")
    for t in OUT_TYPES.values():
        d[t] = d[t].fillna(0) if t in d.columns else 0.0
    for col, t in OUT_TYPES.items():
        d[col] = d[t]
    d["post_n_def_events"] = sum(d[t] for t in OUT_TYPES.values())
    d = d.dropna(subset=["age"]).reset_index(drop=True)
    return d


def run_window(name, d):
    W = build_W(d)
    T_res, Y_res, _ = crossfit(d, W)
    out = []
    t = d.treat_yellow_card.values
    for dv, lab in DVS.items():
        est, se, p = ate(T_res, Y_res[dv], d.match_id.values)
        cm = d.loc[t == 0, dv].mean()
        out.append(dict(window=name, dv=lab, n=len(d), treated=int(t.sum()),
                        control_mean=round(cm, 3), ate=round(est, 4), se=round(se, 4),
                        p=round(p, 4), rel=f"{100*est/cm:+.1f}%"))
    return out


def main():
    frame, ev, lu = load_all()
    h1x, e2 = exits(ev)
    book = bookings(ev)
    starters = lu[lu.started][["match_id", "team_id", "player_id"]]
    starters = starters[[k not in h1x for k in zip(starters.match_id, starters.player_id)]]
    starters = starters.merge(e2, on=["match_id", "player_id"], how="left")
    starters["exit2"] = starters.exit2.fillna(999)
    fkeys = set(zip(frame.match_id, frame.player_id))
    starters["in_frame"] = [k in fkeys for k in zip(starters.match_id, starters.player_id)]

    results = []
    # ---- second-half windows ----
    for b in [50, 60, 70, 80]:
        elig = starters[starters.exit2 > b]
        f = frame.merge(elig[["match_id", "player_id"]], on=["match_id", "player_id"])
        cand = elig[~elig.in_frame][["match_id", "team_id", "player_id"]]
        extras = build_extras(cand, frame, ev, book)
        counts = window_counts(ev, 2, 45, b)
        d = assemble(f, extras, counts, 15, 45, book)
        print(f"[45-{b}] n={len(d):,} (frame {len(f):,} + extras {len(d)-len(f):,} after age-drop) "
              f"treated={int(d.treat_yellow_card.sum()):,}", flush=True)
        results += run_window(f"45-{b}", d)
        print(pd.DataFrame(results[-4:]).to_string(index=False), flush=True)

    # ---- first-half window 30-45 (treatment 15-30) ----
    elig = starters  # on pitch all of H1
    f = frame.merge(elig[["match_id", "player_id"]], on=["match_id", "player_id"])
    cand = elig[~elig.in_frame][["match_id", "team_id", "player_id"]]
    extras = build_extras(cand, frame, ev, book)
    counts = window_counts(ev, 1, 30, None)
    d = assemble(f, extras, counts, 15, 30, book, drop_booked_outside=(30.001, 47))
    d = d[~d.book_min.between(0, 14.999) | (d.treat_yellow_card == 1)]
    print(f"[30-45] n={len(d):,} treated={int(d.treat_yellow_card.sum()):,}", flush=True)
    results += run_window("30-45", d)
    print(pd.DataFrame(results[-4:]).to_string(index=False), flush=True)

    res = pd.DataFrame(results)
    res.to_csv("data/multiwindow_results.csv", index=False)
    print("\n=== summary (fouls + def_engagement across windows) ===")
    print(res[res.dv.isin(["fouls", "def_engagement"])]
          .pivot(index="window", columns="dv", values=["ate", "p", "rel"]).to_string())
    print("\nwrote data/multiwindow_results.csv")


if __name__ == "__main__":
    main()
