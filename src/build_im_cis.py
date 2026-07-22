"""Imbens-Manski (2004) confidence intervals for the Lee bounds.

Reads the SE-augmented bounds CSVs (count: data/lee_bounds_windows.csv,
binary: data/lee_bounds_binary.csv) and attaches the IM 95% CI for the
partially identified ATE: [L - c*se_L, U + c*se_U], where c solves
    Phi(c + (U - L) / max(se_L, se_U)) - Phi(-c) = 0.95.
The IM critical value interpolates between 1.645 (wide identified set:
one-sided error at each end) and 1.96 (point identification).

Output: data/lee_bounds_windows_im.csv, data/lee_bounds_binary_im.csv
"""
import numpy as np, pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq


def im_c(L, U, sL, sU, alpha=0.05):
    s = max(sL, sU)
    if s <= 0:
        return norm.ppf(1 - alpha / 2)
    delta = max(0.0, U - L) / s
    f = lambda c: norm.cdf(c + delta) - norm.cdf(-c) - (1 - alpha)
    return brentq(f, 1e-6, 10)


def main():
    # ---- count bounds ----
    w = pd.read_csv("data/lee_bounds_windows.csv")
    cs = [im_c(r.lee_lo, r.lee_hi, r.lee_lo_se, r.lee_hi_se) for r in w.itertuples()]
    w["im_c"] = np.round(cs, 3)
    w["ci_lo"] = (w.lee_lo - w.im_c * w.lee_lo_se).round(4)
    w["ci_hi"] = (w.lee_hi + w.im_c * w.lee_hi_se).round(4)
    w["ci_lo_rel"] = (100 * w.ci_lo / w.control_mean).round(1)
    w["ci_hi_rel"] = (100 * w.ci_hi / w.control_mean).round(1)
    w.to_csv("data/lee_bounds_windows_im.csv", index=False)
    print("=== count outcomes: bounds + IM 95% CI (relative %) ===")
    print(w[["window", "dv", "rel", "lee_lo_rel", "lee_hi_rel", "ci_lo_rel", "ci_hi_rel"]].to_string(index=False))

    # ---- binary bounds ----
    b = pd.read_csv("data/lee_bounds_binary.csv")
    cs = [im_c(r.lee_lo_pp, r.lee_hi_pp, r.lee_lo_se_pp, r.lee_hi_se_pp) for r in b.itertuples()]
    b["im_c"] = np.round(cs, 3)
    b["ci_lo_pp"] = (b.lee_lo_pp - b.im_c * b.lee_lo_se_pp).round(2)
    b["ci_hi_pp"] = (b.lee_hi_pp + b.im_c * b.lee_hi_se_pp).round(2)
    b["zero_excluded_ci"] = (b.ci_hi_pp < 0) | (b.ci_lo_pp > 0)
    b.to_csv("data/lee_bounds_binary_im.csv", index=False)
    print("\n=== binary outcomes: bounds + IM 95% CI (pp) ===")
    print(b[["window", "dv", "ate_pp", "lee_lo_pp", "lee_hi_pp", "ci_lo_pp", "ci_hi_pp",
             "zero_excluded", "zero_excluded_ci"]].to_string(index=False))
    print("\nwrote data/lee_bounds_windows_im.csv, data/lee_bounds_binary_im.csv")


if __name__ == "__main__":
    main()
