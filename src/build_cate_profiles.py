"""Response-quartile profiles (CLAN) for fouls.

Fits the joint moderator model of build_hte_joint.py for fouls, computes
the fitted CATE tau(Z_i) for every player-match, and writes
data/cate_clan.csv: mean moderator values in the most-responsive and
least-responsive quartile of the fitted-CATE distribution, with a
match-clustered p-value for each Q1-Q4 mean difference. Also prints a
summary of the fitted-CATE distribution.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import build_W, crossfit, load
from build_hte_joint import z_design, POS_ORDER

DV = "post_n_foul_committed"


def main():
    df = load()
    Z, pos5 = z_design(df)
    W = build_W(df)
    groups = df.match_id.values
    T_res, Y_res, _ = crossfit(df, W)

    X = pd.concat([pd.Series(1.0, index=df.index, name="const"), Z], axis=1)
    fit = sm.OLS(Y_res[DV], X.values * T_res[:, None]).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    tau = X.values @ np.asarray(fit.params)

    cm = df.loc[df.treat_yellow_card == 0, DV].mean()
    ate = float(np.mean(tau))
    q05, q95 = np.percentile(tau, [5, 95])
    print(f"fitted CATEs (fouls): n={len(tau):,} | mean {ate:+.3f} | "
          f"range [{tau.min():+.3f}, {tau.max():+.3f}] | "
          f"5th-95th [{q05:+.3f}, {q95:+.3f}] | share<0 {100*(tau<0).mean():.1f}% | "
          f"control mean {cm:.3f}")

    # CLAN: quartiles of fitted CATE; Q1 = most responsive (most negative)
    q = pd.qcut(pd.Series(tau).rank(method="first"), 4, labels=[1, 2, 3, 4]).values
    gs = np.where(df.ht_score_diff < 0, "trailing",
                  np.where(df.ht_score_diff > 0, "leading", "level"))
    prof = pd.DataFrame({
        **{f"Position: {g}": (pos5 == g).astype(float).values for g in POS_ORDER},
        "Game state: trailing": (gs == "trailing").astype(float),
        "Game state: level": (gs == "level").astype(float),
        "Game state: leading": (gs == "leading").astype(float),
        "Age (years)": df.age.values,
        "Pre-match win probability": df.odds_p_win.values})
    mask = (q == 1) | (q == 4)
    ind = (np.asarray(q)[mask] == 1).astype(float)
    g14 = groups[mask]
    rows = []
    for var in prof.columns:
        y = prof[var].values[mask]
        f = sm.OLS(y, sm.add_constant(ind)).fit(cov_type="cluster",
                                                cov_kwds={"groups": g14})
        rows.append(dict(var=var, most_responsive=round(prof.loc[q == 1, var].mean(), 3),
                         least_responsive=round(prof.loc[q == 4, var].mean(), 3),
                         p=round(float(f.pvalues[1]), 4)))
    for k, lab in [(1, "Q1 most responsive"), (4, "Q4 least responsive")]:
        m = float(np.mean(tau[q == k]))
        cmq = df.loc[(q == k) & (df.treat_yellow_card == 0), DV].mean()
        rows.append(dict(var=f"mean fitted CATE ({lab})", most_responsive=round(m, 4),
                         least_responsive=round(cmq, 4), p=np.nan))
        rows.append(dict(var=f"relative to quartile control mean ({lab})",
                         most_responsive=round(100 * m / cmq, 1),
                         least_responsive=np.nan, p=np.nan))
    out = pd.DataFrame(rows)
    out.to_csv("data/cate_clan.csv", index=False)
    print("\nquartile mean fitted CATE: ",
          {int(k): round(float(np.mean(tau[q == k])), 3) for k in [1, 2, 3, 4]})
    print(out.to_string(index=False))
    print("\nwrote data/cate_clan.csv")


if __name__ == "__main__":
    main()
