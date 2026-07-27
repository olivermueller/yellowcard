"""Insensitivity checks for the machinery-evaluation appendix.

Three panels, all on the primary [45,60] Spec-B sample:

  (1) Learner swap: re-estimate all four ATEs with the nuisance learners
      replaced -- baseline HGB; a deeper HGB; random forests; regularised
      linear models (logistic / ridge with standardised inputs). Estimates
      should be stable across learners.
  (2) Seed spread: repeat the baseline over 20 replications, varying both
      the HGB random state and the (match-level) fold assignment; report
      the spread of the ATE per outcome.
  (3) Residual balance: cluster-robust joint F-test of T_res on all W
      columns -- after residualisation no confounder should predict the
      treatment residual.

Outputs: data/insensitivity_learners.csv, data/insensitivity_seeds.csv,
         data/insensitivity_balance.csv.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, HGB, ate, build_W, load

RF = dict(n_estimators=400, min_samples_leaf=50, n_jobs=-1, random_state=0)

LEARNERS = {
    "HGB (baseline)": (
        lambda: HistGradientBoostingClassifier(**HGB),
        lambda: HistGradientBoostingRegressor(**HGB)),
    "HGB (deeper)": (
        lambda: HistGradientBoostingClassifier(max_iter=800, learning_rate=0.05,
                                               min_samples_leaf=50, random_state=0),
        lambda: HistGradientBoostingRegressor(max_iter=800, learning_rate=0.05,
                                              min_samples_leaf=50, random_state=0)),
    "Random forest": (
        lambda: RandomForestClassifier(**RF),
        lambda: RandomForestRegressor(**RF)),
    "Linear (logit / ridge)": (
        lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0))),
}


def match_folds(groups, seed, k=5):
    """(train, test) index pairs from a seeded permutation of match ids."""
    rng = np.random.default_rng(seed)
    uniq = rng.permutation(pd.unique(groups))
    fold_of = {m: i for i, part in enumerate(np.array_split(uniq, k)) for m in part}
    f = np.array([fold_of[g] for g in groups])
    idx = np.arange(len(groups))
    return [(idx[f != i], idx[f == i]) for i in range(k)]


def fit_ates(df, W, clf, reg, cv, groups):
    t = df.treat_yellow_card.astype(int).values
    e = cross_val_predict(clf, W, t, cv=cv, method="predict_proba")[:, 1]
    T_res = t - e
    out = {}
    for dv, lab in DVS.items():
        y = df[dv].values.astype(float)
        m = cross_val_predict(reg, W, y, cv=cv)
        out[lab] = ate(T_res, y - m, groups)
    return out


def main():
    df = load()
    W = build_W(df).astype(float)
    groups = df.match_id.values
    cv0 = match_folds(groups, seed=0)

    # ---- (1) learner swap ----
    rows = []
    for name, (mk_clf, mk_reg) in LEARNERS.items():
        res = fit_ates(df, W, mk_clf(), mk_reg(), cv0, groups)
        for lab, (est, se, p) in res.items():
            rows.append(dict(learner=name, dv=lab, ate=round(est, 4),
                             se=round(se, 4), p=round(p, 4)))
        print(pd.DataFrame(rows)[pd.DataFrame(rows).learner == name]
              .to_string(index=False), flush=True)
    pd.DataFrame(rows).to_csv("data/insensitivity_learners.csv", index=False)

    # ---- (2) seed spread (HGB random state + fold assignment) ----
    seed_rows = []
    for s in range(20):
        hp = dict(HGB); hp["random_state"] = s
        res = fit_ates(df, W, HistGradientBoostingClassifier(**hp),
                       HistGradientBoostingRegressor(**hp),
                       match_folds(groups, seed=s), groups)
        for lab, (est, _, _) in res.items():
            seed_rows.append(dict(seed=s, dv=lab, ate=est))
        print(f"seed {s}: " + ", ".join(f"{lab} {est:+.4f}" for lab, (est, _, _) in res.items()),
              flush=True)
    sd = pd.DataFrame(seed_rows)
    summ = sd.groupby("dv").ate.agg(["mean", "std", "min", "max"]).round(4)
    print("\nseed spread:\n", summ.to_string())
    sd.to_csv("data/insensitivity_seeds.csv", index=False)

    # ---- (3) residual balance: T_res ~ W joint F ----
    t = df.treat_yellow_card.astype(int).values
    clf, _ = LEARNERS["HGB (baseline)"][0], None
    e = cross_val_predict(LEARNERS["HGB (baseline)"][0](), W, t, cv=cv0,
                          method="predict_proba")[:, 1]
    T_res = t - e
    X = sm.add_constant(W.values)
    fit = sm.OLS(T_res, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    R = np.zeros((W.shape[1], W.shape[1] + 1))
    R[:, 1:] = np.eye(W.shape[1])
    ft = fit.f_test(R)
    bal = pd.DataFrame([dict(k=W.shape[1], F=float(ft.fvalue), p=float(ft.pvalue))])
    bal.to_csv("data/insensitivity_balance.csv", index=False)
    print(f"\nresidual balance: F({W.shape[1]}) = {float(ft.fvalue):.3f}, "
          f"p = {float(ft.pvalue):.4f}")
    print("\nwrote data/insensitivity_{learners,seeds,balance}.csv")


if __name__ == "__main__":
    main()
