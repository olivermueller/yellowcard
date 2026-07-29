"""Section-6 robustness numbers for the defensive-actions aggregate.

(1) Overlap/trimming ladder: primary def_actions ATE re-estimated after
    discarding observations with e(W) outside successively tighter bands.
(2) Cinelli-Hazlett sensitivity: robustness value (estimate to zero) and
    RV for significance at the 5% level; benchmark = partial R2 of the
    tactical-position dummies with the outcome residual and with the
    treatment residual.

Outputs: printed numbers + data/robustness_numbers.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import ate, build_W, crossfit, load

DV = "post_n_def_actions"


def main():
    df = load()
    W = build_W(df)
    groups = df.match_id.values
    T_res, Y_res, e = crossfit(df, W)
    print(f"e(W) range: [{e.min():.4f}, {e.max():.4f}] | "
          f"medians booked {np.median(e[df.treat_yellow_card==1]):.3f} / "
          f"unbooked {np.median(e[df.treat_yellow_card==0]):.3f} | "
          f"99th pct booked {np.quantile(e[df.treat_yellow_card==1],.99):.3f} / "
          f"unbooked {np.quantile(e[df.treat_yellow_card==0],.99):.3f}")

    rows = []
    est0, se0, p0 = ate(T_res, Y_res[DV], groups)
    print(f"\nfull sample: ATE {est0:.4f} (se {se0:.4f}, p {p0:.4f})")
    rows.append(dict(check="trim", band="none", n=len(df), ate=round(est0, 4)))
    for lo, hi in [(0.001, 0.999), (0.01, 0.99), (0.02, 0.98), (0.05, 0.95)]:
        keep = (e >= lo) & (e <= hi)
        d2 = df[keep].reset_index(drop=True)
        Tr, Yr, _ = crossfit(d2, build_W(d2))
        b, s, p = ate(Tr, Yr[DV], d2.match_id.values)
        print(f"trim [{lo},{hi}]: n={keep.sum():,} ({100*(1-keep.mean()):.1f}% removed) "
              f"ATE {b:.4f} (p {p:.4f})")
        rows.append(dict(check="trim", band=f"[{lo},{hi}]", n=int(keep.sum()), ate=round(b, 4)))

    # ---- Cinelli-Hazlett on the partial-linear final stage ----
    X = sm.add_constant(T_res)
    fit = sm.OLS(Y_res[DV], X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    est, se = fit.params[1], fit.bse[1]
    dof = len(df) - W.shape[1] - 1
    f2 = (est / se / np.sqrt(dof)) ** 2
    rv = 0.5 * (np.sqrt(f2 ** 2 + 4 * f2) - f2)
    t05 = 1.96
    fq = abs(est / se) - t05
    f2q = (fq / np.sqrt(dof)) ** 2
    rv05 = 0.5 * (np.sqrt(f2q ** 2 + 4 * f2q) - f2q) if fq > 0 else 0.0
    print(f"\nCinelli-Hazlett: RV(estimate=0) {100*rv:.2f}% | RV(p=.05) {100*rv05:.2f}%")

    # benchmark: position dummies' partial R2 with outcome and treatment residuals
    pos = pd.get_dummies(df.position_group, drop_first=True, dtype=float).values
    r2y = sm.OLS(Y_res[DV], sm.add_constant(pos)).fit().rsquared
    r2t = sm.OLS(T_res, sm.add_constant(pos)).fit().rsquared
    print(f"benchmark (position): partial R2 outcome {100*r2y:.2f}% | treatment {100*r2t:.3f}%")
    rows.append(dict(check="CH", band="RV_zero", n=len(df), ate=round(100*rv, 2)))
    rows.append(dict(check="CH", band="RV_p05", n=len(df), ate=round(100*rv05, 2)))
    rows.append(dict(check="CH", band="bench_pos_r2y_pct", n=len(df), ate=round(100*r2y, 2)))
    rows.append(dict(check="CH", band="bench_pos_r2t_pct", n=len(df), ate=round(100*r2t, 3)))
    pd.DataFrame(rows).to_csv("data/robustness_numbers.csv", index=False)
    print("\nwrote data/robustness_numbers.csv")


if __name__ == "__main__":
    main()
