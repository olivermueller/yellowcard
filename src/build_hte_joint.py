"""Joint heterogeneity analysis: linear DML theta(Z) with all moderators at once.

Replaces the one-at-a-time subgroup CATEs (which treat every Z independently)
with the best-linear-predictor of the CATE: regress the outcome residual on
the treatment residual interacted with the FULL moderator design,

    Y_res ~ (1, Z) * T_res ,   Z = [pos5 dummies, game state, venue,
                                    format, age (continuous, std), age^2]

so each coefficient is that moderator's contribution holding the others
fixed. Cluster-robust (match) inference; per-block F-tests with BH across
blocks; overall heterogeneity F-test (all non-constant terms = 0).

Positions use the 5-group tactical scheme (2026-07-23): CentralDef,
WideDef (full/wing backs), DefMid (defensive + centre midfield), OffMid
(attacking + wide midfield), Forward. Age enters CONTINUOUSLY (terciles in
the earlier analysis were an artifact of the subgroup machinery).

Sample/nuisances: canonical (male, age in W, corrected frame, 45-60 frame
outcomes), as in build_male_dml.py.

Outputs: data/hte_joint_coefs.csv, data/hte_joint_blocks.csv,
         data/hte_joint_pos5.csv (implied per-position effects).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, build_W, crossfit, load

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
    Z["venue_home"] = (df.home_away == "home").astype(float)
    Z["format_league"] = (df.competition_format == "league").astype(float)
    Z = Z.loc[:, Z.nunique() > 1]          # constant moderators (e.g. format in Spec B) drop
    age_std = (df.age - df.age.mean()) / df.age.std()
    Z["age_std"] = age_std
    Z["age_std_sq"] = age_std ** 2
    return Z, pos5


BLOCKS = {"position": ["pos_WideDef", "pos_DefMid", "pos_OffMid", "pos_Forward"],
          "game_state": ["gs_trailing", "gs_leading"],
          "venue": ["venue_home"],
          "format": ["format_league"],
          "age": ["age_std", "age_std_sq"]}


def main():
    df = load()
    if "competition_format" not in df.columns:
        df["competition_format"] = (df["competition_type"] == "Domestic League").map(
            {True: "league", False: "cup"})
    Z, pos5 = z_design(df)
    print("treated by pos5:", df[df.treat_yellow_card == 1].position.map(POS5).value_counts().to_dict())

    W = build_W(df)
    groups = df.match_id.values
    T_res, Y_res, _ = crossfit(df, W)

    X = pd.concat([pd.Series(1.0, index=df.index, name="const"), Z], axis=1)
    feats = X.values * T_res[:, None]
    names = list(X.columns)

    coef_rows, block_rows, pos_rows = [], [], []
    for dv in ["post_n_foul_committed", "post_n_def_events", "post_n_pressure", "post_n_tackle"]:
        lab = DVS[dv]
        fit = sm.OLS(Y_res[dv], feats).fit(cov_type="cluster", cov_kwds={"groups": groups})
        b = np.asarray(fit.params); V = np.asarray(fit.cov_params())
        for nm, bi, si, pi in zip(names, b, np.asarray(fit.bse), np.asarray(fit.pvalues)):
            coef_rows.append(dict(dv=lab, term=nm, coef=round(bi, 4), se=round(si, 4), p=round(pi, 4)))
        # block F-tests + BH within DV
        pvals = {}
        blocks = {k: [c for c in v if c in names] for k, v in BLOCKS.items()}
        blocks = {k: v for k, v in blocks.items() if v}
        for bl, cols in blocks.items():
            R = np.zeros((len(cols), len(names)))
            for i, c in enumerate(cols):
                R[i, names.index(c)] = 1
            pvals[bl] = float(fit.f_test(R).pvalue)
        Rall = np.zeros((len(names) - 1, len(names)))
        for i in range(1, len(names)):
            Rall[i - 1, i] = 1
        p_overall = float(fit.f_test(Rall).pvalue)
        m = len(pvals); order = sorted(pvals.items(), key=lambda kv: kv[1]); qs = {}; prev = 1.0
        for rank in range(m, 0, -1):
            nm_, pv = order[rank - 1]; prev = min(prev, pv * m / rank); qs[nm_] = prev
        for bl in blocks:
            block_rows.append(dict(dv=lab, block=bl, F_p=round(pvals[bl], 4), BH_q=round(qs[bl], 4)))
        block_rows.append(dict(dv=lab, block="OVERALL_heterogeneity", F_p=round(p_overall, 4), BH_q=np.nan))

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
        print(f"[{lab}] overall heterogeneity p={p_overall:.4f} | blocks:",
              {k: round(v, 4) for k, v in pvals.items()}, flush=True)

    pd.DataFrame(coef_rows).to_csv("data/hte_joint_coefs.csv", index=False)
    pd.DataFrame(block_rows).to_csv("data/hte_joint_blocks.csv", index=False)
    pd.DataFrame(pos_rows).to_csv("data/hte_joint_pos5.csv", index=False)

    print("\n=== fouls: joint-model coefficients ===")
    cr = pd.DataFrame(coef_rows)
    print(cr[cr.dv == "fouls"].to_string(index=False))
    print("\n=== implied per-position effects (other Z at means) ===")
    pr = pd.DataFrame(pos_rows)
    print(pr[pr.dv.isin(["fouls", "def_engagement"])].to_string(index=False))
    print("\nwrote data/hte_joint_{coefs,blocks,pos5}.csv")


if __name__ == "__main__":
    main()
