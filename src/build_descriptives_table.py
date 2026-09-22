"""Descriptive statistics by treatment status.

Estimation sample. Panel A: selected pre-window covariates.
Panel B: outcomes in the primary window (minutes 45-60). Means by
treatment status, raw difference, and p-value from an OLS of the
variable on the treatment indicator with match-clustered SEs.

Output: data/descriptives_by_treatment.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dml import DVS, load

OPP = ["pre_player_n_" + c for c in ["pressure", "tackle", "foul_committed"]]
BALL = ["pre_player_n_" + c for c in ["ball_recovery", "clearance", "block", "interception"]]


def main():
    df = load()
    df["pre_opp"] = df[OPP].sum(axis=1)
    df["pre_ball"] = df[BALL].sum(axis=1)
    df["pre_events"] = df[[c for c in df.columns if c.startswith("pre_player_n_")]].sum(axis=1)
    df["home"] = (df.home_away == "home").astype(float)

    covs = [("pre_opp", "Opponent-directed defensive actions, minutes [0,15)"),
            ("pre_ball", "Ball-directed defensive actions, minutes [0,15)"),
            ("pre_events", "All events, minutes [0,15)"),
            ("pre_score_diff", "Score margin at minute 15"),
            ("odds_p_win", "Pre-match win probability"),
            ("home", "Home team"),
            ("age", "Age (years)")]
    outs = [(dv, lab) for dv, lab in DVS.items()]

    t = df.treat_yellow_card.astype(int).values
    groups = df.match_id.values
    rows = []
    for panel, items in [("covariate", covs), ("outcome", outs)]:
        for col, lab in items:
            y = df[col].astype(float).values
            f = sm.OLS(y, sm.add_constant(t)).fit(cov_type="cluster",
                                                  cov_kwds={"groups": groups})
            rows.append(dict(panel=panel, var=lab,
                             mean_unbooked=y[t == 0].mean(),
                             mean_booked=y[t == 1].mean(),
                             diff=f.params[1], p=f.pvalues[1]))
    out = pd.DataFrame(rows)
    out.to_csv("data/descriptives_by_treatment.csv", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.3f}")
    print(out.to_string(index=False))

if __name__ == "__main__":
    main()
