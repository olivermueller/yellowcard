"""ATE and ATT under the interactive (AIPW) model, via DoubleML.

The partially linear estimator of build_dml.py identifies, under effect
heterogeneity, an overlap-weighted average of conditional effects with
weights e(W){1 - e(W)} rather than the unweighted ATE. This script
re-estimates every primary-window outcome in DoubleML's interactive
regression model (IRM), whose AIPW score targets the ATE directly, and
in its ATTE variant, which targets the effect on the treated. Sample,
confounder matrix, and HistGradientBoosting learners are identical to
the main analysis; folds are cluster-aware by match and inference is
cluster-robust by match.

Requires the optional packages of requirements_crosscheck.txt; if they
are missing the script prints a note and exits without error.

Output: data/crosscheck_irm.csv
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
from build_dml import DVS, HGB, build_W, load


def main():
    df = load()
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    xcols = list(W.columns)
    base = pd.concat([W, pd.Series(t, index=W.index, name="d"),
                      df.match_id.rename("match_id")], axis=1)
    ours = pd.read_csv("data/dml_results.csv").set_index("dv")

    rows = []
    for dv, lab in DVS.items():
        data = base.copy()
        data["y"] = df[dv].astype(float).values
        ctrl_mean = data.loc[data.d == 0, "y"].mean()
        row = dict(dv=lab, control_mean=round(ctrl_mean, 4),
                   plr_ate=ours.loc[lab, "ate"], plr_se=ours.loc[lab, "se"])
        for score, tag in [("ATE", "ate"), ("ATTE", "att")]:
            obj = dml.DoubleMLIRM(
                dml.DoubleMLClusterData(data, y_col="y", d_cols="d",
                                        cluster_cols="match_id", x_cols=xcols),
                ml_g=HistGradientBoostingRegressor(**HGB),
                ml_m=HistGradientBoostingClassifier(**HGB),
                n_folds=5, score=score,
                trimming_rule="truncate", trimming_threshold=0.01)
            obj.fit()
            est, se, p = float(obj.coef[0]), float(obj.se[0]), float(obj.pval[0])
            row[f"irm_{tag}"] = round(est, 4)
            row[f"irm_{tag}_se"] = round(se, 4)
            row[f"irm_{tag}_p"] = round(p, 4)
            row[f"irm_{tag}_rel"] = f"{100 * est / ctrl_mean:+.1f}%"
            print(f"{lab:>15} {score:>4}: {est:+.4f} ({se:.4f}) p={p:.4f} "
                  f"rel {100 * est / ctrl_mean:+.1f}%  [PLR {ours.loc[lab, 'ate']:+.4f}]")
        rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv("data/crosscheck_irm.csv", index=False)
    print("\nwrote data/crosscheck_irm.csv")


if __name__ == "__main__":
    main()
