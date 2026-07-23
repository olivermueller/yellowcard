"""Figures for Section 6: propensity overlap and sensitivity contour.

fig_overlap.png      Distribution of the cross-fitted booking propensity
                     e(W) by treatment status (log-count histograms).
fig_sensitivity.png  Cinelli-Hazlett style contour plot for the primary
                     outcome: adjusted estimate as a function of the
                     partial R2 of an unobserved confounder with the
                     treatment and with the outcome; the zero contour,
                     the robustness value, and the observed-benchmark
                     region are marked.
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import HGB, build_W, load

BLU, YEL, INK, GRID, MUT, RED = "#2a78d6", "#eda100", "#1b2733", "#e3e8ee", "#9aa3ad", "#e34948"


def main():
    df = load()
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    groups = df.match_id.values
    cv = GroupKFold(5)
    e = cross_val_predict(HistGradientBoostingClassifier(**HGB), W, t, groups=groups,
                          cv=cv, n_jobs=-1, method="predict_proba")[:, 1]
    y = df.post_n_def_events.astype(float).values
    m = cross_val_predict(HistGradientBoostingRegressor(**HGB), W, y, groups=groups,
                          cv=cv, n_jobs=-1)
    T_res, Y_res = t - e, y - m

    # ---- overlap figure ----
    fig, ax = plt.subplots(figsize=(8.5, 4))
    bins = np.linspace(0, e.max() * 1.02, 45)
    ax.hist(e[t == 0], bins=bins, color=BLU, alpha=.55, label="unbooked", zorder=2)
    ax.hist(e[t == 1], bins=bins, color=YEL, alpha=.75, label="booked", zorder=3)
    ax.set_yscale("log")
    ax.set_xlabel("cross-fitted booking propensity $\\hat{e}(W)$")
    ax.set_ylabel("player-matches (log scale)")
    ax.legend(frameon=False)
    ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig("fig_overlap.png", dpi=300, facecolor="white")

    # ---- sensitivity contour (partial-linear final stage) ----
    X = sm.add_constant(T_res)
    fit = sm.OLS(Y_res, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    est, se = fit.params[1], fit.bse[1]
    dof = len(df) - W.shape[1] - 1
    tstat = est / se
    f2 = (tstat / np.sqrt(dof)) ** 2
    rv = 0.5 * (np.sqrt(f2 ** 2 + 4 * f2) - f2)

    r2t = np.linspace(0.0001, 0.05, 220)
    r2y = np.linspace(0.0001, 0.05, 220)
    RT, RY = np.meshgrid(r2t, r2y)
    bias = np.sqrt(RY * RT / (1 - RT)) * se * np.sqrt(dof)
    adj = est + bias if est < 0 else est - bias   # adverse direction: toward zero

    fig, ax = plt.subplots(figsize=(6.8, 5.4))
    cs = ax.contour(100 * RT, 100 * RY, adj, levels=10, colors=MUT, linewidths=.9)
    ax.clabel(cs, fmt="%.2f", fontsize=7)
    zero = ax.contour(100 * RT, 100 * RY, adj, levels=[0], colors=RED, linewidths=2)
    ax.clabel(zero, fmt={0: "estimate = 0"}, fontsize=8)
    ax.plot([100 * rv], [100 * rv], marker="D", color=RED, ms=7, zorder=5)
    ax.annotate(f"robustness value ({100*rv:.1f}%, {100*rv:.1f}%)",
                (100 * rv, 100 * rv), textcoords="offset points", xytext=(8, 6), fontsize=9)
    # observed benchmark: position family (strongest outcome predictor)
    ax.plot([0.02], [3.23], marker="o", color=BLU, ms=7, zorder=5)
    ax.annotate("position (observed)", (0.02, 3.23), textcoords="offset points",
                xytext=(8, -3), fontsize=9, color=BLU)
    ax.set_xlabel("partial $R^2$ of confounder with treatment (%)")
    ax.set_ylabel("partial $R^2$ of confounder with outcome (%)")
    ax.grid(color=GRID, lw=.6); ax.set_axisbelow(True)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig("fig_sensitivity.png", dpi=300, facecolor="white")
    print(f"wrote fig_overlap.png, fig_sensitivity.png (est {est:.4f}, RV {100*rv:.2f}%)")


if __name__ == "__main__":
    main()
