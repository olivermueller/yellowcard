"""Extended outcome families on the primary [45,60] window (backlog D).

Family 1, defensive actions: pressures, tackles, fouls committed (paper
set) plus ball recoveries, clearances, blocks, interceptions, and the
7-component aggregate.
Family 2, adverse events: miscontrols, dispossessions,
times dribbled past, and the 3-component aggregate.

Sample and estimation identical to the main analysis (Spec-B frame,
paper W + age + odds, HGB nuisances, GroupKFold(5) by match,
cluster-robust SEs). Outcome counts for the new event types are built
from the event stream for the primary window, period 2 minutes 45-60.

Output: data/outcome_families.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import ate, build_W, crossfit, load

FAM1 = ["pressure", "tackle", "foul_committed", "ball_recovery", "clearance",
        "block", "interception"]
FAM2 = ["miscontrol", "dispossessed", "dribbled_past"]
TYPE_MAP = {"Pressure": "pressure", "Foul Committed": "foul_committed",
            "Ball Recovery": "ball_recovery", "Clearance": "clearance",
            "Block": "block", "Interception": "interception",
            "Miscontrol": "miscontrol", "Dispossessed": "dispossessed",
            "Dribbled Past": "dribbled_past"}


def main():
    df = load()
    mids = df.match_id.unique().tolist()
    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "period", "minute", "type", "duel_type"],
        filters=[("match_id", "in", mids)])
    ev["tn"] = ev.type.map(TYPE_MAP)
    ev.loc[(ev.type == "Duel") & (ev.duel_type == "Tackle"), "tn"] = "tackle"
    w = ev[(ev.period == 2) & (ev.minute >= 45) & (ev.minute <= 60) & ev.tn.notna()]
    c = (w.groupby(["match_id", "player_id", "tn"]).size().unstack(fill_value=0)
           .reindex(columns=FAM1 + FAM2, fill_value=0).reset_index())
    df = df.merge(c, on=["match_id", "player_id"], how="left")
    for t in FAM1 + FAM2:
        df[t] = df[t].fillna(0)
    df["defensive_actions"] = df[FAM1].sum(axis=1)
    df["adverse_events"] = df[FAM2].sum(axis=1)

    # validation against the paper counts
    for new, old in [("pressure", "post_n_pressure"), ("tackle", "post_n_tackle"),
                     ("foul_committed", "post_n_foul_committed")]:
        ok = (df[new] == df[old]).mean()
        print(f"validation {new} vs {old}: {100*ok:.2f}% identical")

    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    groups = df.match_id.values
    e = None
    # crossfit computes outcome residuals for DVS only; redo per new DV below
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
    from sklearn.model_selection import GroupKFold, cross_val_predict
    from build_male_dml import HGB
    cv = GroupKFold(5)
    e = cross_val_predict(HistGradientBoostingClassifier(**HGB), W, t,
                          cv=cv, groups=groups, method="predict_proba")[:, 1]
    T_res = t - e

    rows = []
    dvs = ([("defensive_actions", "1 defensive actions (aggregate, 7 components)")]
           + [(k, f"1 {k}") for k in FAM1]
           + [("adverse_events", "2 adverse events (aggregate, 3 components)")]
           + [(k, f"2 {k}") for k in FAM2])
    for dv, lab in dvs:
        y = df[dv].values.astype(float)
        m = cross_val_predict(HistGradientBoostingRegressor(**HGB), W, y,
                              cv=cv, groups=groups)
        est, se, p = ate(T_res, y - m, groups)
        cm = df.loc[t == 0, dv].mean()
        rows.append(dict(family=lab.split()[0], dv=dv, control_mean=round(cm, 3),
                         ate=round(est, 4), se=round(se, 4), p=round(p, 4),
                         rel=f"{100*est/cm:+.1f}%"))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)),
              flush=True)
    pd.DataFrame(rows).to_csv("data/outcome_families.csv", index=False)
    print("\nwrote data/outcome_families.csv")


if __name__ == "__main__":
    main()
