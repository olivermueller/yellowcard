"""Cross-check of Table 4 against the DoubleML package (Bach et al.).

Re-estimates the ATE for every outcome in the primary window with
DoubleMLPLR, the partially linear model with the partialling-out score --
the same estimator implemented in build_dml.py -- using the identical
sample, confounder matrix, and HistGradientBoosting learners. Two runs
per outcome:

  1. pinned folds: the exact GroupKFold(5) assignment of build_dml.py is
     passed via set_sample_splitting, so the estimate should agree with
     Table 4 up to the numerical differences between the two final-stage
     solvers;
  2. cluster-aware: DoubleMLClusterData with match_id as the cluster
     variable, DoubleML's own cluster-respecting fold draw and
     cluster-robust variance.

Requires the optional packages of requirements_crosscheck.txt; if they
are missing the script prints a note and exits without error, so the
driver notebook remains runnable.

Output: data/crosscheck_plr.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import doubleml as dml
except ImportError:
    print("SKIPPED: the DoubleML package is not installed "
          "(pip install -r requirements_crosscheck.txt).")
    sys.exit(0)

import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from build_dml import DVS, HGB, build_W, load


def main():
    df = load()
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    groups = df.match_id.values
    smpls = [list(GroupKFold(n_splits=5).split(W, t, groups))]

    ours = pd.read_csv("data/dml_results.csv").set_index("dv")
    xcols = list(W.columns)
    base = pd.concat([W, pd.Series(t, index=W.index, name="d"),
                      df.match_id.rename("match_id")], axis=1)

    rows = []
    for dv, lab in DVS.items():
        data = base.copy()
        data["y"] = df[dv].astype(float).values

        # 1. pinned folds: identical sample splitting, plain variance
        obj = dml.DoubleMLPLR(
            dml.DoubleMLData(data, y_col="y", d_cols="d", x_cols=xcols),
            ml_l=HistGradientBoostingRegressor(**HGB),
            ml_m=HistGradientBoostingClassifier(**HGB),
            n_folds=5, score="partialling out")
        obj.set_sample_splitting(smpls)
        obj.fit()
        theta_pin = float(obj.coef[0])

        # 2. DoubleML's own cluster-aware splitting and variance
        objc = dml.DoubleMLPLR(
            dml.DoubleMLClusterData(data, y_col="y", d_cols="d",
                                    cluster_cols="match_id", x_cols=xcols),
            ml_l=HistGradientBoostingRegressor(**HGB),
            ml_m=HistGradientBoostingClassifier(**HGB),
            n_folds=5, score="partialling out")
        objc.fit()
        theta_cl, se_cl, p_cl = float(objc.coef[0]), float(objc.se[0]), float(objc.pval[0])

        rows.append(dict(dv=lab,
                         ate_ours=ours.loc[lab, "ate"], se_ours=ours.loc[lab, "se"],
                         ate_pinned=round(theta_pin, 4),
                         diff_pinned=round(theta_pin - ours.loc[lab, "ate"], 4),
                         ate_cluster=round(theta_cl, 4), se_cluster=round(se_cl, 4),
                         p_cluster=round(p_cl, 4)))
        print(f"{lab:>15}: ours {ours.loc[lab, 'ate']:+.4f}  "
              f"pinned {theta_pin:+.4f}  cluster {theta_cl:+.4f} ({se_cl:.4f})")

    out = pd.DataFrame(rows)
    out.to_csv("data/crosscheck_plr.csv", index=False)
    print("\nmax |pinned - ours|:", out.diff_pinned.abs().max())
    print("wrote data/crosscheck_plr.csv")


if __name__ == "__main__":
    main()
