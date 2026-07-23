"""DML on the full male sample with age as an added confounder + Lee bounds.

Sample:  data/analysis_frame.csv, gender == male (complete-case on age).
W:       paper W (pre_* counts/diffs + categoricals; gender dummy drops as
         constant) + age (Wikidata DOB, data/player_dob.parquet).
Z:       one-moderator-at-a-time subgroup ATEs (paper style): position,
         venue, half-time game state, competition format, age tercile.
Bounds:  Lee (2009) trimming bounds for the [45,60] window. The trimming
         fraction is computed on THIS sample (male matches): population =
         starters on the pitch at the end of H1; treated = first yellow in
         [15,45]; control censoring standardized to the treated position
         mix. Upper/lower bound = full DML re-run after deleting the
         top/bottom p% of the control-arm outcome distribution (nuisances
         refit; seeded tie-break). Unconditional trim — the covariate-
         conditional version is a noted refinement.

Nuisances as in the paper: HistGradientBoosting (max_iter=400, lr=.05,
min_samples_leaf=200, seed 0), 5-fold GroupKFold by match, cluster-robust
SEs by match.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_config import build_W_Z

DVS = {"post_n_def_events": "def_engagement", "post_n_pressure": "pressures",
       "post_n_tackle": "tackles", "post_n_foul_committed": "fouls"}
HGB = dict(max_iter=400, learning_rate=0.05, min_samples_leaf=200, random_state=0)
CARD = ["foul_committed_card", "bad_behaviour_card"]


EU_LEAGUES = ["La Liga", "Ligue 1", "Premier League", "Serie A", "1. Bundesliga"]


def load():
    """SPEC B (canonical since 2026-07-23): male, five European domestic
    leagues (archival 1973/74 + 1986/87 singles dropped), age + betting
    odds merged, complete-case on both."""
    df = pd.read_csv("data/analysis_frame.csv", low_memory=False)
    df = df[(df.gender == "male") & df.competition.isin(EU_LEAGUES)]
    df = df[~df.season.isin(["1973/1974", "1986/1987"])]
    dob = pd.read_parquet("data/player_dob.parquet")[["player_id", "dob"]]
    df = df.merge(dob, on="player_id", how="left")
    df["age"] = (pd.to_datetime(df.match_date) - pd.to_datetime(df.dob)).dt.days / 365.25
    odds = pd.read_csv("data/odds/odds_european_male.csv")
    df = df.merge(odds, on="match_id", how="left")
    n0 = len(df)
    df = df.dropna(subset=["age", "odds_p_home"]).reset_index(drop=True)
    df["odds_p_win"] = np.where(df.home_away == "home", df.odds_p_home,
                                1 - df.odds_p_home - df.odds_p_draw)
    print(f"SPEC-B sample: {len(df):,} rows ({n0-len(df):,} dropped: missing age/odds) | "
          f"treated {int(df.treat_yellow_card.sum()):,}")
    return df


def build_W(df):
    W, _, _, _, _, _ = build_W_Z(df)
    extra = [c for c in ["age", "odds_p_win", "odds_p_draw"] if c in df.columns]
    W = pd.concat([W, df[extra].astype(float)], axis=1)
    return W.loc[:, W.nunique() > 1]


def crossfit(df, W):
    t = df.treat_yellow_card.astype(int).values
    groups = df.match_id.values
    cv = GroupKFold(n_splits=5)
    e = cross_val_predict(HistGradientBoostingClassifier(**HGB), W, t,
                          cv=cv, groups=groups, method="predict_proba")[:, 1]
    T_res = t - e
    res = {}
    for dv in DVS:
        y = df[dv].values.astype(float)
        m = cross_val_predict(HistGradientBoostingRegressor(**HGB), W, y,
                              cv=cv, groups=groups)
        res[dv] = y - m
    return T_res, res, e


def ate(T_res, Y_res, groups):
    X = sm.add_constant(T_res)
    f = sm.OLS(Y_res, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    return f.params[1], f.bse[1], f.pvalues[1]


def subgroup(df, T_res, Y_res, levels, groups):
    d = pd.get_dummies(pd.Series(levels, name="g"), dtype=float)
    X = np.column_stack([d.values * T_res[:, None], np.ones(len(T_res))])
    f = sm.OLS(Y_res, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    k = d.shape[1]
    out = {lev: (f.params[i], f.bse[i], f.pvalues[i]) for i, lev in enumerate(d.columns)}
    R = np.zeros((k - 1, k + 1))
    for i in range(k - 1):
        R[i, i], R[i, i + 1] = 1, -1
    return out, float(f.f_test(R).pvalue)


def lee_trim_fraction(df):
    """Trimming fraction for [45,60] computed on this sample's matches."""
    mids = df.match_id.unique().tolist()
    posmap = df.drop_duplicates("position").set_index("position").position_group.to_dict()
    posmap["Goalkeeper"] = "Goalkeeper"
    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "period", "minute", "type", "position"] + CARD,
        filters=[("match_id", "in", mids)])
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first().map(posmap).rename("grp"))
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
    E = E.merge(exit2, on=["match_id", "player_id"], how="left")
    E["exit2"] = E.exit2.fillna(999)
    E = E.merge(pos, on=["match_id", "player_id"], how="left")
    E["key"] = list(zip(E.match_id, E.player_id))
    T = E[E.key.isin(tk)]
    C = E[~E.key.isin(bk)]
    t_c = (T.exit2 <= 60).mean()
    w = T.grp.value_counts(normalize=True)
    cr = C.groupby("grp").exit2.apply(lambda s: (s <= 60).mean())
    c_adj = sum(w.get(k, 0) * cr.get(k, np.nan) for k in w.index)
    p = max(0.0, ((1 - c_adj) - (1 - t_c)) / (1 - c_adj))
    print(f"censoring by 60': treated {100*t_c:.1f}% vs control (position-adj) {100*c_adj:.1f}% "
          f"-> Lee trim {100*p:.1f}%  (T={len(T):,}, C={len(C):,})")
    return p


def main():
    df = load()
    W = build_W(df)
    print(f"W: {W.shape[1]} columns (paper W + age)")
    groups = df.match_id.values
    t = df.treat_yellow_card.astype(int).values

    T_res, Y_res, e = crossfit(df, W)
    print(f"propensity range: ({e.min():.4f}, {e.max():.4f})")
    p_trim = lee_trim_fraction(df)

    print("\n=== ATE + Lee bounds (per DV) ===")
    rng = np.random.default_rng(0)
    rows = []
    for dv, lab in DVS.items():
        est, se, p = ate(T_res, Y_res[dv], groups)
        cm = df.loc[t == 0, dv].mean()
        y = df[dv].values.astype(float)
        ctrl_idx = np.where(t == 0)[0]
        n_trim = int(round(p_trim * len(ctrl_idx)))
        jitter = rng.random(len(ctrl_idx))
        order = ctrl_idx[np.lexsort((jitter, y[ctrl_idx]))]
        bounds = {}
        for side, drop in [("upper", order[-n_trim:]), ("lower", order[:n_trim])]:
            keep = np.setdiff1d(np.arange(len(df)), drop)
            d2 = df.iloc[keep].reset_index(drop=True)
            Tr2, Yr2, _ = crossfit(d2, build_W(d2))
            b, _, _ = ate(Tr2, Yr2[dv], d2.match_id.values)
            bounds[side] = b
        rows.append(dict(dv=lab, control_mean=round(cm, 3), ate=round(est, 4),
                         se=round(se, 4), p=round(p, 4), rel=f"{100*est/cm:+.1f}%",
                         lee_lo=round(bounds["lower"], 4), lee_hi=round(bounds["upper"], 4),
                         lee_lo_rel=f"{100*bounds['lower']/cm:+.1f}%",
                         lee_hi_rel=f"{100*bounds['upper']/cm:+.1f}%"))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)), flush=True)
    pd.DataFrame(rows).to_csv("data/male_dml_results.csv", index=False)

    print("\n=== Subgroup ATEs ===")
    gs = np.where(df.ht_score_diff < 0, "trailing", np.where(df.ht_score_diff > 0, "leading", "level"))
    age_t = pd.qcut(df.age, 3, labels=["young", "mid", "old"]).astype(str)
    mods = {"position": df.position_group.values, "venue": df.home_away.values,
            "game_state": gs, "format": df.competition_format.values, "age": age_t.values}
    mods = {k: v for k, v in mods.items() if pd.Series(v).nunique() > 1}   # constant in Spec B -> skip
    sub_rows = []
    for dv in ["post_n_foul_committed", "post_n_def_events"]:
        joint_ps = {}
        for mname, lv in mods.items():
            res, jp = subgroup(df, T_res, Y_res[dv], lv, groups)
            joint_ps[mname] = jp
            for lev, (b, se_, p_) in res.items():
                sub_rows.append(dict(dv=DVS[dv], moderator=mname, level=lev,
                                     ate=round(b, 4), se=round(se_, 4), p=round(p_, 4)))
        m = len(joint_ps)
        order = sorted(joint_ps.items(), key=lambda kv: kv[1])
        qs, prev = {}, 1.0
        for rank in range(m, 0, -1):
            name, pv = order[rank - 1]
            prev = min(prev, pv * m / rank)
            qs[name] = prev
        print(f"\n{DVS[dv]}: joint-test BH q per moderator:",
              {k: round(v, 4) for k, v in sorted(qs.items(), key=lambda kv: kv[1])})
    sub = pd.DataFrame(sub_rows)
    sub.to_csv("data/male_dml_subgroups.csv", index=False)
    print("\nfouls subgroup ATEs:")
    print(sub[sub.dv == "fouls"].to_string(index=False))
    print("\nwrote data/male_dml_results.csv, data/male_dml_subgroups.csv")


if __name__ == "__main__":
    main()
