"""Teammate spillover (paper Table 4, left panel): effect of a teammate's
booking in [15,45] on UNBOOKED players' outcomes, all four DVs.

Mirrors the assumption-check estimation: sample = unbooked player-matches;
treatment = at least one teammate booked in the treatment window; paper W;
HGB nuisances, GroupKFold(5) by match; match-clustered SEs.

Output: data/spillover_effect.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, HGB, ate, build_W, load


def main():
    df = load()
    tc = df.groupby(["match_id", "team_id"]).treat_yellow_card.sum()
    df = df.join(tc.rename("team_n"), on=["match_id", "team_id"])
    df["mate_carded"] = ((df.team_n - df.treat_yellow_card) > 0).astype(int)
    d = df[df.treat_yellow_card == 0].reset_index(drop=True)
    t = d.mate_carded.values
    print(f"unbooked sample: {len(d):,} | teammate-exposed {int(t.sum()):,} "
          f"({100*t.mean():.1f}%)")

    W = build_W(d)
    groups = d.match_id.values
    cv = GroupKFold(5)
    e = cross_val_predict(HistGradientBoostingClassifier(**HGB), W, t, groups=groups,
                          cv=cv, n_jobs=-1, method="predict_proba")[:, 1]
    Tr = t - e
    rows = []
    for dv, lab in DVS.items():
        y = d[dv].astype(float).values
        Yr = y - cross_val_predict(HistGradientBoostingRegressor(**HGB), W, y,
                                   groups=groups, cv=cv, n_jobs=-1)
        est, se, p = ate(Tr, Yr, groups)
        cm = y[t == 0].mean()
        rows.append(dict(dv=lab, control_mean=round(cm, 3), ate=round(est, 4),
                         se=round(se, 4), p=round(p, 4), rel=f"{100*est/cm:+.1f}%"))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)),
              flush=True)
    pd.DataFrame(rows).to_csv("data/spillover_effect.csv", index=False)
    print("\nwrote data/spillover_effect.csv")


if __name__ == "__main__":
    main()
