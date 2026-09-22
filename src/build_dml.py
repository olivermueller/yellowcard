"""Main DML estimates for the primary outcome window (manuscript Table 4).

Sample: the analysis frame of 02_build_analysis_frame.ipynb — the five
European men's leagues, complete-case on age (Wikidata DOB) and betting
odds; the merge and the complete-case restriction happen in the notebook.
W: pre-window player counts, team-vs-opponent count differences, score
difference at minute 15, position and venue dummies, age, win and draw
probability.
Estimator: partial-linear DML with HistGradientBoosting nuisances
(max_iter=400, lr=.05, min_samples_leaf=200, seed 0), 5-fold GroupKFold
by match, cluster-robust SEs by match.

Output: data/dml_results.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Taxonomy of defensive actions: opponent-directed
# (pressures, tackles, fouls -- actions contesting an opponent, sanction
# risk) vs ball-directed (recoveries, clearances, blocks, interceptions --
# no opponent contest, no sanction path). No grand total.
DVS = {"post_n_opp_directed": "opp_directed", "post_n_pressure": "pressures",
       "post_n_tackle": "tackles", "post_n_foul_committed": "fouls",
       "post_n_ball_directed": "ball_directed",
       "post_n_ball_recovery": "ball_recoveries", "post_n_clearance": "clearances",
       "post_n_block": "blocks", "post_n_interception": "interceptions"}
HGB = dict(max_iter=400, learning_rate=0.05, min_samples_leaf=200, random_state=0)
CARD = ["foul_committed_card", "bad_behaviour_card"]

# Canonical StatsBomb position -> 3-group mapping (as in 02_build_analysis_frame)
POSITION_GROUP = {
    "Goalkeeper": "Goalkeeper",
    "Left Back": "Defender", "Right Back": "Defender", "Center Back": "Defender",
    "Left Center Back": "Defender", "Right Center Back": "Defender",
    "Left Wing Back": "Defender", "Right Wing Back": "Defender",
    "Left Defensive Midfield": "Midfielder", "Right Defensive Midfield": "Midfielder",
    "Center Defensive Midfield": "Midfielder", "Left Center Midfield": "Midfielder",
    "Right Center Midfield": "Midfielder", "Center Midfield": "Midfielder",
    "Left Midfield": "Midfielder", "Right Midfield": "Midfielder",
    "Left Attacking Midfield": "Midfielder", "Right Attacking Midfield": "Midfielder",
    "Center Attacking Midfield": "Midfielder",
    "Left Wing": "Forward", "Right Wing": "Forward", "Left Center Forward": "Forward",
    "Right Center Forward": "Forward", "Center Forward": "Forward",
    "Secondary Striker": "Forward",
}


LEAGUES = ["Premier League", "La Liga", "1. Bundesliga", "Serie A", "Ligue 1"]


def load():
    """Analysis sample as written by 02_build_analysis_frame.ipynb: the
    eligible frame with age (Wikidata DOB) and de-vigged betting odds
    already merged, complete-case on both."""
    df = pd.read_csv("data/analysis_frame.csv", low_memory=False)
    print(f"analysis sample: {len(df):,} rows | "
          f"treated {int(df.treat_yellow_card.sum()):,}")
    return df


def sample_match_ids():
    """match_ids of the full sample (men's matches of the five major European
    leagues, archival single-match seasons excluded) — the match universe of
    02_build_analysis_frame.ipynb, before the complete-case restriction on
    age and odds narrows the frame."""
    m = pd.read_parquet("data/matches.parquet")
    m = m[(m["competition_gender"] == "male")
          & m["competition_name"].isin(LEAGUES)
          & ~m["season_name"].isin(["1973/1974", "1986/1987"])]
    return m["match_id"].tolist()


def build_W(df):
    """Confounder matrix: the player's per-type pre-window counts, the
    team-vs-opponent per-type pre-window count differences, the score
    difference at minute 15, position and venue dummies, age, and the
    win/draw probabilities. Constant columns drop."""
    num = (sorted(c for c in df.columns if c.startswith("pre_player_n_"))
           + sorted(c for c in df.columns if c.startswith("pre_diff_n_"))
           + ["pre_score_diff"]
           + [c for c in ["age", "odds_p_win", "odds_p_draw"] if c in df.columns])
    catdum = pd.get_dummies(df[["position_group", "home_away"]], drop_first=True, dtype=float)
    W = pd.concat([df[num].astype(float), catdum], axis=1)
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


def main():
    df = load()
    W = build_W(df)
    print(f"W: {W.shape[1]} columns")
    groups = df.match_id.values

    T_res, Y_res, e = crossfit(df, W)
    print(f"propensity range: ({e.min():.4f}, {e.max():.4f})")

    print("\n=== ATE per outcome ===")
    t = df.treat_yellow_card.astype(int).values
    rows = []
    for dv, lab in DVS.items():
        est, se, p = ate(T_res, Y_res[dv], groups)
        cm = df.loc[t == 0, dv].mean()
        rows.append(dict(dv=lab, control_mean=round(cm, 3), ate=round(est, 4),
                         se=round(se, 4), p=round(p, 4), rel=f"{100*est/cm:+.1f}%"))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)), flush=True)
    pd.DataFrame(rows).to_csv("data/dml_results.csv", index=False)
    print("\nwrote data/dml_results.csv")


if __name__ == "__main__":
    main()
