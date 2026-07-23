"""Figure for the joint heterogeneity analysis (paper F4).

Three panels from the joint theta(Z) model for FOULS (the only DV with
significant heterogeneity, overall p=.0007):
  A: implied effect per tactical position (5 groups), other moderators at
     sample means, 95% cluster-robust CIs;
  B: implied effect per half-time game state;
  C: implied effect as a continuous function of age (the null, visibly),
     with a pointwise 95% band.

Output: fig_hte_joint.png (300 dpi; also usable as a separate-file figure
for JQAS after EPS/TIF conversion).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import build_W, crossfit, load
from build_hte_joint import z_design, POS_ORDER

BLU, INK, GRID, MUT = "#2a78d6", "#1b2733", "#e3e8ee", "#9aa3ad"
DV = "post_n_foul_committed"


def implied(zrow, b, V):
    th = float(zrow @ b)
    se = float(np.sqrt(zrow @ V @ zrow))
    return th, se


def main():
    df = load()
    if "competition_format" not in df.columns:
        df["competition_format"] = (df["competition_type"] == "Domestic League").map(
            {True: "league", False: "cup"})
    Z, pos5 = z_design(df)
    W = build_W(df)
    T_res, Y_res, _ = crossfit(df, W)
    X = pd.concat([pd.Series(1.0, index=df.index, name="const"), Z], axis=1)
    names = list(X.columns)
    fit = sm.OLS(Y_res[DV], X.values * T_res[:, None]).fit(
        cov_type="cluster", cov_kwds={"groups": df.match_id.values})
    b, V = np.asarray(fit.params), np.asarray(fit.cov_params())
    zbar = X.mean().values

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), sharey=True)

    def style(ax):
        ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
        ax.axhline(0, color="#444", lw=1, zorder=1)

    # --- A: positions ---
    ax = axes[0]
    labels = {"CentralDef": "Central\ndefender", "WideDef": "Wide\ndefender",
              "DefMid": "Defensive\nmidfield", "OffMid": "Offensive\nmidfield",
              "Forward": "Forward"}
    ths, ses = [], []
    for g in POS_ORDER:
        z = zbar.copy()
        for gg in POS_ORDER[1:]:
            z[names.index(f"pos_{gg}")] = 1.0 if gg == g else 0.0
        th, se = implied(z, b, V); ths.append(th); ses.append(se)
    xs = np.arange(len(POS_ORDER))
    sig = [abs(t) > 1.96 * s for t, s in zip(ths, ses)]
    ax.bar(xs, ths, .62, color=BLU, alpha=[.9 if s_ else .35 for s_ in sig][0], zorder=2)
    for x, t, s_ in zip(xs, ths, sig):
        ax.patches[x].set_alpha(.9 if s_ else .35)
    ax.errorbar(xs, ths, yerr=[1.96 * s for s in ses], fmt="none",
                ecolor=INK, elinewidth=1.4, capsize=4, zorder=3)
    ax.set_xticks(xs); ax.set_xticklabels([labels[g] for g in POS_ORDER], fontsize=9)
    ax.set_ylabel("effect on fouls, 45–60′ (events)")
    ax.set_title("A  Tactical position", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.text(.98, .04, "block p = .002", transform=ax.transAxes, ha="right", fontsize=9, color=MUT)
    style(ax)

    # --- B: game state ---
    ax = axes[1]
    gs_levels = [("trailing", {"gs_trailing": 1, "gs_leading": 0}),
                 ("level", {"gs_trailing": 0, "gs_leading": 0}),
                 ("leading", {"gs_trailing": 0, "gs_leading": 1})]
    ths, ses = [], []
    for _, setting in gs_levels:
        z = zbar.copy()
        for k, v in setting.items():
            z[names.index(k)] = v
        th, se = implied(z, b, V); ths.append(th); ses.append(se)
    xs = np.arange(3)
    sig = [abs(t) > 1.96 * s for t, s in zip(ths, ses)]
    ax.bar(xs, ths, .55, color=BLU, zorder=2)
    for x, s_ in zip(xs, sig):
        ax.patches[x].set_alpha(.9 if s_ else .35)
    ax.errorbar(xs, ths, yerr=[1.96 * s for s in ses], fmt="none",
                ecolor=INK, elinewidth=1.4, capsize=4, zorder=3)
    ax.set_xticks(xs); ax.set_xticklabels(["trailing", "level", "leading"], fontsize=9.5)
    ax.set_title("B  Half-time game state", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.text(.98, .04, "block p = .005", transform=ax.transAxes, ha="right", fontsize=9, color=MUT)
    style(ax)

    # --- C: age (continuous) ---
    ax = axes[2]
    ages = np.linspace(df.age.quantile(.02), df.age.quantile(.98), 60)
    mu, sd = df.age.mean(), df.age.std()
    ths, los, his = [], [], []
    for a in ages:
        z = zbar.copy()
        z[names.index("age_std")] = (a - mu) / sd
        z[names.index("age_std_sq")] = ((a - mu) / sd) ** 2
        th, se = implied(z, b, V)
        ths.append(th); los.append(th - 1.96 * se); his.append(th + 1.96 * se)
    ax.fill_between(ages, los, his, color=BLU, alpha=.18, lw=0, zorder=1)
    ax.plot(ages, ths, color=BLU, lw=2, zorder=2)
    ax.set_xlabel("age at match (years)")
    ax.set_title("C  Age", loc="left", fontsize=11, fontweight="bold", color=INK)
    ax.text(.98, .04, "block p = .51 (n.s.)", transform=ax.transAxes, ha="right", fontsize=9, color=MUT)
    style(ax)

    fig.suptitle("")
    fig.tight_layout()
    fig.savefig("fig_hte_joint.png", dpi=300, facecolor="white")
    print("wrote fig_hte_joint.png")


if __name__ == "__main__":
    main()
