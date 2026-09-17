"""Plausibility check for the Lee worst case: is early withdrawal of
booked players predictable from observables?

The worst-case (upper) Lee bound assumes the marginal players — booked
players who were withdrawn early and their would-be-withdrawn control
counterparts — are the TOP-TAIL outcome types within each cell. This
script confronts that with data. Among booked players (first yellow in
[15,45], starters, on pitch at the end of H1), it

  (a) prints descriptive diagnostics: H1 fouls and the percentile of
      pre-window [0,15) activity within position-matched control
      survivors, and standardized mean differences (withdrawn minus
      kept on) over pre-window characteristics;
  (b) fits classifiers predicting withdrawal by 60' (incl. half-time)
      from the pre-window characteristics plus the booking minute:
      the paper's HGB learner and a logistic benchmark, 5-fold
      stratified CV, held-out AUC/Brier, and CV-averaged permutation
      importances (held-out AUC drop).

Withdrawn players are absent from the analysis frame (it conditions on
observability), so their covariates are rebuilt from the raw events and
merged from the frame at the player level (age) and team-match level
(win probability, score margin, home).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_multiwindow as mw

COMPS = ["foul_committed", "pressure", "tackle", "ball_recovery",
         "clearance", "block", "interception"]


def smd(a, b):
    """SMD (b minus a) with pooled SD and 95% CI (Hedges & Olkin SE)."""
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    n1, n2 = len(a), len(b)
    sp = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    d = (b.mean() - a.mean()) / sp if sp > 0 else 0.0
    se = np.sqrt(1 / n1 + 1 / n2 + d ** 2 / (2 * (n1 + n2)))
    return d, 1.96 * se


def build_population():
    frame, ev, lu = mw.load_all()
    h1x, e2 = mw.exits(ev)
    card = ev[mw.CARD[0]].where(ev[mw.CARD[0]].notna(), ev[mw.CARD[1]])
    y1 = ev[card.eq("Yellow Card") & (ev.period == 1) & ev.minute.between(15, 45)]
    tk = set(zip(*y1.drop_duplicates(["match_id", "player_id"])[["match_id", "player_id"]].values.T))
    bk = set(zip(*ev[card.eq("Yellow Card") & (ev.period == 1)]
                 [["match_id", "player_id"]].drop_duplicates().values.T))

    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first()
             .map(frame.drop_duplicates("position").set_index("position").position_group.to_dict())
             .rename("grp"))
    pre_ev = ev[(ev.period == 1) & (ev.minute < 15)]
    pre = pre_ev.groupby(["match_id", "player_id"]).size().rename("pre_n")
    pre_c = (pre_ev[pre_ev.tn.isin(COMPS)]
             .groupby(["match_id", "player_id", "tn"]).size()
             .unstack(fill_value=0).reindex(columns=COMPS, fill_value=0))
    h1f = (ev[(ev.period == 1) & ev.tn.eq("foul_committed")]
             .groupby(["match_id", "player_id"]).size().rename("h1_fouls"))
    E = lu[lu.started][["match_id", "player_id", "team_id"]]
    E = E[[k not in h1x for k in zip(E.match_id, E.player_id)]].copy()
    E = (E.merge(e2, on=["match_id", "player_id"], how="left")
           .merge(pos, on=["match_id", "player_id"], how="left")
           .merge(pre, on=["match_id", "player_id"], how="left")
           .merge(pre_c, on=["match_id", "player_id"], how="left")
           .merge(h1f, on=["match_id", "player_id"], how="left"))
    E["exit2"] = E.exit2.fillna(999)
    for c in ["pre_n", "h1_fouls"] + COMPS:
        E[c] = E[c].fillna(0)
    E = E[E.grp.isin(["Defender", "Midfielder", "Forward"])]
    E["key"] = list(zip(E.match_id, E.player_id))

    dob = (frame.dropna(subset=["dob"]).drop_duplicates("player_id")
                .set_index("player_id").dob)
    mdate = frame.drop_duplicates("match_id").set_index("match_id").match_date
    tm = (frame.drop_duplicates(["match_id", "team_id"])
               [["match_id", "team_id", "odds_p_win", "pre_score_diff", "home_away"]])
    E = E.merge(tm, on=["match_id", "team_id"], how="left")
    E["age"] = ((pd.to_datetime(E.match_id.map(mdate))
                 - pd.to_datetime(E.player_id.map(dob))).dt.days / 365.25)
    E["home"] = (E.home_away == "home").astype(float)
    bmin = (y1.sort_values("minute").drop_duplicates(["match_id", "player_id"])
              .set_index(["match_id", "player_id"]).minute)
    E["book_minute"] = [bmin.get(k, np.nan) for k in E.key]
    for g in ["Defender", "Midfielder", "Forward"]:
        E[g] = (E.grp == g).astype(float)
    return E, tk, bk


def main():
    E, tk, bk = build_population()
    ctrl = E[~E.key.isin(bk)]
    booked = E[E.key.isin(tk)].copy()
    booked["withdrawn"] = (booked.exit2 <= 60).astype(int)
    ctrl_surv = ctrl[ctrl.exit2 > 60]
    kept = booked[booked.withdrawn == 0]
    wdr = booked[booked.withdrawn == 1]

    groups = {"Control survivors": ctrl_surv,
              "Booked, kept on": kept,
              "Booked, withdrawn by 60'": wdr}
    print("n per group:", {k: len(v) for k, v in groups.items()})

    tab = {}
    for name, g in groups.items():
        f = g.h1_fouls
        tab[name] = [100 * (f == 0).mean(), 100 * (f == 1).mean(), 100 * (f >= 2).mean()]
    print("\nH1 fouls committed (%):")
    print(pd.DataFrame(tab, index=["0 fouls", "1 foul", "2+ fouls"]).round(1).to_string())

    pct = {}
    for name, g in groups.items():
        vals = []
        for grp_name, gg in g.groupby("grp"):
            ref = np.sort(ctrl_surv[ctrl_surv.grp == grp_name].pre_n.values)
            vals.append(100 * np.searchsorted(ref, gg.pre_n.values, side="left") / len(ref))
        pct[name] = np.concatenate(vals)
    print("\npre-window activity percentile (vs control survivors, same position):")
    for k, v in pct.items():
        print(f"  {k:26s} mean {v.mean():5.1f} | median {np.median(v):5.1f} | share in top decile {100*(v>=90).mean():4.1f}%")

    FEATS = (["pre_n"] + COMPS + ["pre_score_diff", "odds_p_win", "home", "age",
                                  "book_minute", "Defender", "Midfielder", "Forward"])
    print("\nSMD (withdrawn - kept on):")
    for col in FEATS:
        if col == "book_minute":
            continue
        d, ci = smd(kept[col].astype(float).values, wdr[col].astype(float).values)
        print(f"  {col:16s} {d:+.3f} +- {ci:.3f}")

    # classifier: predict withdrawal among booked players
    d = booked.dropna(subset=["odds_p_win", "pre_score_diff", "age"])
    X, y = d[FEATS].values, d.withdrawn.values
    print(f"\nclassifier sample: n={len(d)}, withdrawn={y.sum()} ({100*y.mean():.1f}%)")

    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    hgb = lambda: HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05,
                                                 min_samples_leaf=200, random_state=0)
    p_hgb = cross_val_predict(hgb(), X, y, cv=cv, method="predict_proba")[:, 1]
    logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    p_log = cross_val_predict(logit, X, y, cv=cv, method="predict_proba")[:, 1]
    base = np.full_like(p_hgb, y.mean())
    print(f"HGB   : AUC {roc_auc_score(y, p_hgb):.3f} | Brier {brier_score_loss(y, p_hgb):.4f}")
    print(f"Logit : AUC {roc_auc_score(y, p_log):.3f} | Brier {brier_score_loss(y, p_log):.4f}")
    print(f"Const : Brier {brier_score_loss(y, base):.4f}")

    imp = np.zeros(len(FEATS))
    for tr, te in cv.split(X, y):
        m = hgb().fit(X[tr], y[tr])
        r = permutation_importance(m, X[te], y[te], scoring="roc_auc",
                                   n_repeats=20, random_state=0)
        imp += r.importances_mean
    imp /= cv.get_n_splits()
    print("\npermutation importance (mean held-out AUC drop):")
    for i in np.argsort(imp)[::-1]:
        print(f"  {FEATS[i]:16s} {imp[i]:+.4f}")


if __name__ == "__main__":
    main()
