"""SUTVA follow-up: main ATEs against teammate-UNEXPOSED controls (backlog G).

The canonical assumption checks (05_assumption_checks.ipynb) find a
significant positive foul spillover onto non-carded teammates (+0.0135,
p=.0035, +5.4%): when a teammate is booked, the others foul more. Since
~37% of controls are teammate-exposed, the headline foul ATE could be
overstated. This script re-estimates the main ATEs on the canonical male
sample keeping only treated players and controls WITHOUT a carded
teammate.

Result (2026-07-23): fouls -0.0566 (p<.0001, -22.6% vs -25.6% full
sample); def_engagement -0.1703 (p=.0006, -5.1% vs -5.7%) — interference
shaves ~3pp off the relative foul effect and the conclusions stand.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_config import build_W_Z
from build_male_dml import HGB

DVS = ["post_n_def_events", "post_n_pressure", "post_n_tackle", "post_n_foul_committed"]


def main():
    from build_male_dml import load as load_spec
    df = load_spec()                      # SPEC B

    tc = df.groupby(["match_id", "team_id"]).treat_yellow_card.sum()
    df = df.join(tc.rename("team_n"), on=["match_id", "team_id"])
    df["mate_carded"] = ((df.team_n - df.treat_yellow_card) > 0).astype(int)
    d = df[(df.treat_yellow_card == 1) | (df.mate_carded == 0)].reset_index(drop=True)
    print(f"sample: {len(d):,} ({len(df)-len(d):,} teammate-exposed controls dropped) | "
          f"treated {int(d.treat_yellow_card.sum()):,}")

    from build_male_dml import build_W as bw
    W = bw(d)
    t = d.treat_yellow_card.astype(int).values
    groups = d.match_id.values
    cv = GroupKFold(5)
    e = cross_val_predict(HistGradientBoostingClassifier(**HGB), W, t, groups=groups,
                          cv=cv, n_jobs=-1, method="predict_proba")[:, 1]
    Tr = t - e

    rows = []
    for dv in DVS:
        y = d[dv].astype(float).values
        Yr = y - cross_val_predict(HistGradientBoostingRegressor(**HGB), W, y,
                                   groups=groups, cv=cv, n_jobs=-1)
        th = (Yr * Tr).sum() / (Tr ** 2).sum()
        IC = (Yr - th * Tr) * Tr / (Tr ** 2).mean()
        se = np.sqrt((pd.Series(IC).groupby(groups).sum().values ** 2).sum()) / len(IC)
        cm = y[t == 0].mean()
        rows.append(dict(dv=dv, control_mean=round(cm, 3), ate=round(th, 4), se=round(se, 4),
                         p=round(2 * (1 - norm.cdf(abs(th / se))), 4),
                         rel=f"{100*th/cm:+.1f}%"))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)))
    pd.DataFrame(rows).to_csv("data/spillover_robustness.csv", index=False)
    print("\nwrote data/spillover_robustness.csv")


if __name__ == "__main__":
    main()
