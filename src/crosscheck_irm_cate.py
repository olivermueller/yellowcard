"""Foul-CATE drivers under the interactive model, via DoubleML.

The moderator analysis of build_hte_joint.py projects the partially
linear residual product on the moderator design, which weights the
conditional effects by e(W){1 - e(W)}. This script re-estimates the
projection from the interactive (AIPW) model's orthogonal signal, an
unweighted best linear predictor of the CATE (Semenova and Chernozhukov,
2021), using DoubleML's cate() on the same moderator design, plus group
average treatment effects for position and half-time score state.
Sample, confounders, and learners as in the main analysis.

Requires the optional packages of requirements_crosscheck.txt; if they
are missing the script prints a note and exits without error.

Output: data/crosscheck_irm_cate.csv
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
from build_dml import HGB, build_W, load
from build_hte_joint import POS5, z_design


def main():
    df = load()
    Z, pos5 = z_design(df)
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    xcols = list(W.columns)
    data = pd.concat([W, pd.Series(t, index=W.index, name="d"),
                      df.match_id.rename("match_id")], axis=1)
    data["y"] = df.post_n_foul_committed.astype(float).values

    obj = dml.DoubleMLIRM(
        dml.DoubleMLClusterData(data, y_col="y", d_cols="d",
                                cluster_cols="match_id", x_cols=xcols),
        ml_g=HistGradientBoostingRegressor(**HGB),
        ml_m=HistGradientBoostingClassifier(**HGB),
        n_folds=5, score="ATE",
        trimming_rule="truncate", trimming_threshold=0.01)
    obj.fit()
    print(f"IRM ATE (fouls): {float(obj.coef[0]):+.4f} ({float(obj.se[0]):.4f})")

    ours = pd.read_csv("data/hte_joint_coefs.csv").query("dv == 'fouls'").set_index("term")
    rows = []

    basis = pd.concat([pd.Series(1.0, index=Z.index, name="const"), Z], axis=1)
    blp = obj.cate(basis)
    est = np.asarray(blp.blp_model.params, dtype=float)
    se = np.asarray(blp.blp_model.bse, dtype=float)
    for name, b, s in zip(basis.columns, est, se):
        rows.append(dict(kind="blp", term=name,
                         coef_ours=ours.loc[name, "coef"] if name in ours.index else np.nan,
                         coef_irm=round(float(b), 4), se_irm=round(float(s), 4)))

    gs = np.where(df.ht_score_diff < 0, "trailing",
                  np.where(df.ht_score_diff > 0, "leading", "level"))
    for gname, series in [("position", pos5), ("game_state", pd.Series(gs, index=df.index))]:
        groups = pd.get_dummies(pd.Series(series, index=df.index), dtype=bool)
        g = obj.gate(groups=groups)
        gest = np.asarray(g.blp_model.params, dtype=float)
        gse = np.asarray(g.blp_model.bse, dtype=float)
        for name, b, s in zip(groups.columns, gest, gse):
            rows.append(dict(kind=f"gate_{gname}", term=str(name), coef_ours=np.nan,
                             coef_irm=round(float(b), 4), se_irm=round(float(s), 4)))

    out = pd.DataFrame(rows)
    out.to_csv("data/crosscheck_irm_cate.csv", index=False)
    print(out.to_string(index=False))
    print("\nwrote data/crosscheck_irm_cate.csv")


if __name__ == "__main__":
    main()
