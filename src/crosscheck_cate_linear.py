"""Cross-check of the foul-CATE drivers against EconML's LinearDML.

Re-estimates the best linear predictor of the foul CATE on the moderator
design of build_hte_joint.py with LinearDML (Battocchi et al.), whose
final stage solves the same moment -- the outcome residual regressed on
the treatment residual interacted with (1, Z). The identical GroupKFold(5)
assignment is passed as cv. One deliberate difference remains: LinearDML
residualizes on (W, Z) jointly, whereas build_hte_joint.py residualizes
on W alone, so coefficients are expected to agree in pattern and
magnitude, not digit for digit.

Requires the optional packages of requirements_crosscheck.txt; if they
are missing the script prints a note and exits without error.

Output: data/crosscheck_cate.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from econml.dml import LinearDML
except ImportError:
    print("SKIPPED: the econml package is not installed "
          "(pip install -r requirements_crosscheck.txt).")
    sys.exit(0)

import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from build_dml import HGB, build_W, load
from build_hte_joint import z_design


def main():
    df = load()
    Z, _ = z_design(df)
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    y = df.post_n_foul_committed.astype(float).values
    groups = df.match_id.values
    folds = list(GroupKFold(n_splits=5).split(W, t, groups))

    est = LinearDML(model_y=HistGradientBoostingRegressor(**HGB),
                    model_t=HistGradientBoostingClassifier(**HGB),
                    discrete_treatment=True, cv=folds, random_state=0)
    est.fit(y, t, X=Z.values, W=W.values, inference="statsmodels")

    inf = est.coef__inference()
    ours = pd.read_csv("data/hte_joint_coefs.csv").query("dv == 'fouls'").set_index("term")

    rows = [dict(term="const", coef_ours=ours.loc["const", "coef"],
                 coef_econml=round(float(est.intercept_), 4),
                 se_econml=round(float(est.intercept__inference().stderr), 4))]
    for i, name in enumerate(Z.columns):
        rows.append(dict(term=name, coef_ours=ours.loc[name, "coef"],
                         coef_econml=round(float(est.coef_[i]), 4),
                         se_econml=round(float(np.asarray(inf.stderr).ravel()[i]), 4)))

    out = pd.DataFrame(rows)
    out["diff"] = (out.coef_econml - out.coef_ours).round(4)
    out.to_csv("data/crosscheck_cate.csv", index=False)
    print(out.to_string(index=False))
    print("\nmax |diff|:", out["diff"].abs().max())
    print("wrote data/crosscheck_cate.csv")


if __name__ == "__main__":
    main()
