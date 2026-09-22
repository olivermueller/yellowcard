"""Joint heterogeneity analysis: linear DML theta(Z) with all moderators at once.

Best linear predictor of the CATE: regress the outcome residual on
the treatment residual interacted with the FULL moderator design,

    Y_res ~ (1, Z) * T_res ,   Z = [pos5 dummies, game state,
                                    age, age^2, odds_p_win, odds_p_win^2]

so each coefficient is that moderator's contribution holding the others
fixed. Cluster-robust (match) inference; per-block F-tests with BH across
blocks; overall heterogeneity F-test (all non-constant terms = 0).

Positions use the 5-group tactical scheme: CentralDef,
WideDef (full/wing backs), DefMid (defensive + centre midfield), OffMid
(attacking + wide midfield), Forward. Age and win probability enter
continuously with quadratic terms.

Sample and nuisances as in build_dml.py (primary 45-60 outcomes).

Outputs: data/hte_joint_coefs.csv, data/hte_joint_blocks.csv,
         data/hte_joint_pos5.csv (implied per-position effects).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dml import DVS, build_W, crossfit, load

POS5 = {
 "Center Back": "CentralDef", "Left Center Back": "CentralDef", "Right Center Back": "CentralDef",
 "Left Back": "WideDef", "Right Back": "WideDef", "Left Wing Back": "WideDef", "Right Wing Back": "WideDef",
 "Left Defensive Midfield": "DefMid", "Right Defensive Midfield": "DefMid",
 "Center Defensive Midfield": "DefMid", "Left Center Midfield": "DefMid",
 "Right Center Midfield": "DefMid", "Center Midfield": "DefMid",
 "Left Attacking Midfield": "OffMid", "Right Attacking Midfield": "OffMid",
 "Center Attacking Midfield": "OffMid", "Left Midfield": "OffMid", "Right Midfield": "OffMid",
 "Left Wing": "Forward", "Right Wing": "Forward", "Left Center Forward": "Forward",
 "Right Center Forward": "Forward", "Center Forward": "Forward", "Secondary Striker": "Forward",
}
POS_ORDER = ["CentralDef", "WideDef", "DefMid", "OffMid", "Forward"]   # base: CentralDef


def z_design(df):
    """Moderator design (no constant; constant added separately)."""
    Z = pd.DataFrame(index=df.index)
    pos5 = df.position.map(POS5)
    for g in POS_ORDER[1:]:
        Z[f"pos_{g}"] = (pos5 == g).astype(float)
    gs = np.where(df.ht_score_diff < 0, "trailing", np.where(df.ht_score_diff > 0, "leading", "level"))
    Z["gs_trailing"] = (gs == "trailing").astype(float)
    Z["gs_leading"] = (gs == "leading").astype(float)
    Z = Z.loc[:, Z.nunique() > 1]          # constant moderators drop
    age_std = (df.age - df.age.mean()) / df.age.std()
    Z["age_std"] = age_std
    Z["age_std_sq"] = age_std ** 2
    odds_std = (df.odds_p_win - df.odds_p_win.mean()) / df.odds_p_win.std()
    Z["odds_std"] = odds_std
    Z["odds_std_sq"] = odds_std ** 2
    return Z, pos5


BLOCKS = {"position": ["pos_WideDef", "pos_DefMid", "pos_OffMid", "pos_Forward"],
          "game_state": ["gs_trailing", "gs_leading"],
          "age": ["age_std", "age_std_sq"],
          "odds": ["odds_std", "odds_std_sq"]}


def main():
    df = load()
    Z, pos5 = z_design(df)
    print("treated by pos5:", df[df.treat_yellow_card == 1].position.map(POS5).value_counts().to_dict())

    W = build_W(df)
    groups = df.match_id.values
    T_res, Y_res, _ = crossfit(df, W)

    X = pd.concat([pd.Series(1.0, index=df.index, name="const"), Z], axis=1)
    feats = X.values * T_res[:, None]
    names = list(X.columns)

    coef_rows, block_rows, pos_rows, gs_rows = [], [], [], []
    # opponent-directed aggregate + all three components (appendix table);
    # ball-directed results are part of the replication package
    for dv in ["post_n_opp_directed", "post_n_pressure", "post_n_tackle", "post_n_foul_committed"]:
        lab = DVS[dv]
        fit = sm.OLS(Y_res[dv], feats).fit(cov_type="cluster", cov_kwds={"groups": groups})
        b = np.asarray(fit.params); V = np.asarray(fit.cov_params())
        for nm, bi, si, pi in zip(names, b, np.asarray(fit.bse), np.asarray(fit.pvalues)):
            coef_rows.append(dict(dv=lab, term=nm, coef=round(bi, 4), se=round(si, 4), p=round(pi, 4)))
        # block F-tests + BH within DV
        pvals = {}
        blocks = {k: [c for c in v if c in names] for k, v in BLOCKS.items()}
        blocks = {k: v for k, v in blocks.items() if v}
        fstats = {}
        for bl, cols in blocks.items():
            R = np.zeros((len(cols), len(names)))
            for i, c in enumerate(cols):
                R[i, names.index(c)] = 1
            ft = fit.f_test(R)
            pvals[bl] = float(ft.pvalue)
            fstats[bl] = (float(ft.fvalue), int(ft.df_num))
        Rall = np.zeros((len(names) - 1, len(names)))
        for i in range(1, len(names)):
            Rall[i - 1, i] = 1
        ft_all = fit.f_test(Rall)
        p_overall = float(ft_all.pvalue)
        fstats["OVERALL_heterogeneity"] = (float(ft_all.fvalue), int(ft_all.df_num))
        m = len(pvals); order = sorted(pvals.items(), key=lambda kv: kv[1]); qs = {}; prev = 1.0
        for rank in range(m, 0, -1):
            nm_, pv = order[rank - 1]; prev = min(prev, pv * m / rank); qs[nm_] = prev
        for bl in blocks:
            block_rows.append(dict(dv=lab, block=bl, F=round(fstats[bl][0], 2),
                                   df=fstats[bl][1], F_p=round(pvals[bl], 4), BH_q=round(qs[bl], 4)))
        block_rows.append(dict(dv=lab, block="OVERALL_heterogeneity",
                               F=round(fstats["OVERALL_heterogeneity"][0], 2),
                               df=fstats["OVERALL_heterogeneity"][1],
                               F_p=round(p_overall, 4), BH_q=np.nan))

        # implied per-position effects, other moderators at sample means
        zbar = X.mean().values.copy()
        for g in POS_ORDER:
            z = zbar.copy()
            for gg in POS_ORDER[1:]:
                z[names.index(f"pos_{gg}")] = 1.0 if gg == g else 0.0
            th = float(z @ b); se = float(np.sqrt(z @ V @ z))
            cm = df.loc[(df.treat_yellow_card == 0) & (pos5 == g), dv].mean()
            from scipy.stats import norm
            pos_rows.append(dict(dv=lab, pos5=g, theta=round(th, 4), se=round(se, 4),
                                 p=round(2 * (1 - norm.cdf(abs(th / se))), 4),
                                 control_mean=round(cm, 3), rel=f"{100*th/cm:+.1f}%"))
        # implied game-state effects, other moderators at sample means
        gs_lv = np.where(df.ht_score_diff < 0, "trailing",
                         np.where(df.ht_score_diff > 0, "leading", "level"))
        for state, tset, lset in [("trailing", 1, 0), ("level", 0, 0), ("leading", 0, 1)]:
            z = zbar.copy()
            z[names.index("gs_trailing")] = tset
            z[names.index("gs_leading")] = lset
            th = float(z @ b); se = float(np.sqrt(z @ V @ z))
            cm = df.loc[(df.treat_yellow_card == 0) & (gs_lv == state), dv].mean()
            from scipy.stats import norm
            gs_rows.append(dict(dv=lab, state=state, theta=round(th, 4), se=round(se, 4),
                                p=round(2 * (1 - norm.cdf(abs(th / se))), 4),
                                control_mean=round(cm, 3), rel=f"{100*th/cm:+.1f}%"))
        print(f"[{lab}] overall heterogeneity p={p_overall:.4f} | blocks:",
              {k: round(v, 4) for k, v in pvals.items()}, flush=True)

    pd.DataFrame(coef_rows).to_csv("data/hte_joint_coefs.csv", index=False)
    pd.DataFrame(block_rows).to_csv("data/hte_joint_blocks.csv", index=False)
    pd.DataFrame(pos_rows).to_csv("data/hte_joint_pos5.csv", index=False)
    pd.DataFrame(gs_rows).to_csv("data/hte_joint_gs3.csv", index=False)

    print("\n=== fouls: joint-model coefficients ===")
    cr = pd.DataFrame(coef_rows)
    print(cr[cr.dv == "fouls"].to_string(index=False))
    print("\n=== implied per-position effects (other Z at means) ===")
    pr = pd.DataFrame(pos_rows)
    print(pr[pr.dv.isin(["fouls", "opp_directed"])].to_string(index=False))
    print("\nwrote data/hte_joint_{coefs,blocks,pos5,gs3}.csv")


if __name__ == "__main__":
    main()
