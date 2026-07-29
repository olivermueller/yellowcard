"""Raw mean differences by treatment status (paper Table: raw outcomes).

Booked - unbooked difference for the defensive-actions aggregate and each
component in the primary window, with match-clustered standard errors
(OLS of the outcome on the treatment indicator).

Output: data/raw_differences.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import load

COLS = [("post_n_def_actions", "def_actions"), ("post_n_pressure", "pressures"),
        ("post_n_tackle", "tackles"), ("post_n_foul_committed", "fouls"),
        ("post_n_ball_recovery", "ball_recoveries"), ("post_n_clearance", "clearances"),
        ("post_n_block", "blocks"), ("post_n_interception", "interceptions")]


def main():
    df = load()
    t = df.treat_yellow_card.astype(int).values
    rows = []
    for col, lab in COLS:
        y = df[col].astype(float).values
        f = sm.OLS(y, sm.add_constant(t)).fit(cov_type="cluster",
                                              cov_kwds={"groups": df.match_id.values})
        rows.append(dict(dv=lab, mean_unbooked=round(y[t == 0].mean(), 3),
                         mean_booked=round(y[t == 1].mean(), 3),
                         diff=round(f.params[1], 4), se=round(f.bse[1], 4),
                         p=round(f.pvalues[1], 4)))
        print(pd.DataFrame(rows).tail(1).to_string(index=False, header=(len(rows) == 1)))
    pd.DataFrame(rows).to_csv("data/raw_differences.csv", index=False)
    print("\nwrote data/raw_differences.csv")


if __name__ == "__main__":
    main()
