"""Compute the three-estimator comparison table (Table 2 in the paper).

For each of the four outcomes, report ATE + cluster-robust 95% CI + p + %
change vs. control mean from three estimators:

  1. Naive OLS:        Y ~ T,         no controls
  2. OLS + W:          Y ~ T + W,     linear adjustment for the full W set
  3. DML:              partial-linear DML with boosted-tree nuisances

Cluster-robust SEs at the match level for all three.

Output: prints a markdown-ready table to stdout (no file is written, so the
caller can paste straight into the LaTeX or copy the numbers).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

from analysis_config import build_W_Z

PRIMARY = "post_n_def_events"
COMPONENTS = ["post_n_pressure", "post_n_tackle", "post_n_foul_committed"]
ORDER = [PRIMARY] + COMPONENTS
DV_LABEL = {
    "post_n_def_events":      "Defensive engagement (sum)",
    "post_n_pressure":        "Pressures",
    "post_n_tackle":          "Tackles",
    "post_n_foul_committed":  "Fouls",
}

# ---- data ------------------------------------------------------------------
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(REPO_ROOT / "data" / "analysis_frame.csv", low_memory=False)
t = df["treat_yellow_card"].astype(int).values
groups = df["match_id"].values
W, *_ = build_W_Z(df)

# ---- shared DML nuisances --------------------------------------------------
MY = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, min_samples_leaf=200, random_state=0)
MT = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, min_samples_leaf=200, random_state=0)
cf = GroupKFold(5)
e_hat = cross_val_predict(clone(MT), W, t, groups=groups, cv=cf, n_jobs=-1, method="predict_proba")[:, 1]
T_res = t - e_hat

def fmt(b, se, p, ctrl):
    rel = b / ctrl if ctrl else float("nan")
    star = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
    return f"{b:+.3f} [{b-1.96*se:+.3f}, {b+1.96*se:+.3f}] ({100*rel:+.1f}%){star}"

def naive(dv):
    y = df[dv].astype(float).values
    d = pd.DataFrame({"y": y, "t": t, "m": groups})
    fit = smf.ols("y ~ t", data=d).fit(cov_type="cluster", cov_kwds={"groups": d["m"]})
    return float(fit.params["t"]), float(fit.bse["t"]), float(fit.pvalues["t"])

def ols_W(dv):
    y = df[dv].astype(float).values
    X = pd.concat([pd.Series(t, name="t"), W.reset_index(drop=True)], axis=1)
    X = sm.add_constant(X)
    fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    return float(fit.params["t"]), float(fit.bse["t"]), float(fit.pvalues["t"])

def dml(dv):
    y = df[dv].astype(float).values
    Y_res = y - cross_val_predict(clone(MY), W, y, groups=groups, cv=cf, n_jobs=-1)
    d = pd.DataFrame({"Yr": Y_res, "Tr": T_res, "m": groups})
    fit = smf.ols("Yr ~ Tr - 1", data=d).fit(cov_type="cluster", cov_kwds={"groups": d["m"]})
    return float(fit.params["Tr"]), float(fit.bse["Tr"]), float(fit.pvalues["Tr"])

# ---- build the table -------------------------------------------------------
print(f"{'Outcome':30s}  {'Ctrl mean':>10s}  {'Naive OLS':>34s}  {'OLS + W':>34s}  {'DML':>34s}")
print("-" * 150)
for dv in ORDER:
    ctrl = float(df.loc[t == 0, dv].mean())
    b1, s1, p1 = naive(dv)
    b2, s2, p2 = ols_W(dv)
    b3, s3, p3 = dml(dv)
    print(f"{DV_LABEL[dv]:30s}  {ctrl:>10.3f}  {fmt(b1, s1, p1, ctrl):>34s}  "
          f"{fmt(b2, s2, p2, ctrl):>34s}  {fmt(b3, s3, p3, ctrl):>34s}")
