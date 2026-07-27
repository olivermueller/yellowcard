"""Out-of-fold nuisance diagnostics for the machinery-evaluation appendix.

On the primary [45,60] Spec-B sample: cross-fitted (GroupKFold by match)
predictions from the same HGB learners as the main analysis.

  e(W): AUC, Brier score (vs. the base-rate Brier of a constant predictor),
        and a decile calibration plot (mean predicted vs. observed booking
        rate per predicted-propensity decile).
  m(W): out-of-fold R^2 per outcome.

Outputs: data/nuisance_metrics.csv, fig_calibration.png (300 dpi).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, brier_score_loss

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, build_W, crossfit, load

BLU, YEL, INK, GRID = "#2a78d6", "#eda100", "#1b2733", "#e3e8ee"


def main():
    df = load()
    W = build_W(df)
    t = df.treat_yellow_card.astype(int).values
    T_res, Y_res, e = crossfit(df, W)

    rows = []
    auc = roc_auc_score(t, e)
    brier = brier_score_loss(t, e)
    base = brier_score_loss(t, np.full_like(e, t.mean()))
    rows.append(dict(model="e(W) propensity", metric="AUC", value=round(auc, 4)))
    rows.append(dict(model="e(W) propensity", metric="Brier", value=round(brier, 5)))
    rows.append(dict(model="e(W) propensity", metric="Brier (base rate)", value=round(base, 5)))
    print(f"e(W): AUC {auc:.4f} | Brier {brier:.5f} vs base-rate {base:.5f}")
    for dv, lab in DVS.items():
        y = df[dv].values.astype(float)
        r2 = 1 - np.var(Y_res[dv]) / np.var(y)
        rows.append(dict(model=f"m(W) {lab}", metric="R2 (out-of-fold)", value=round(r2, 4)))
        print(f"m(W) {lab}: OOF R2 {r2:.4f}")
    pd.DataFrame(rows).to_csv("data/nuisance_metrics.csv", index=False)

    # ---- calibration plot: predicted-propensity deciles ----
    q = pd.qcut(e, 10, labels=False, duplicates="drop")
    cal = pd.DataFrame({"q": q, "e": e, "t": t}).groupby("q").agg(
        pred=("e", "mean"), obs=("t", "mean"), n=("t", "size"))
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    lim = max(cal.pred.max(), cal.obs.max()) * 1.12
    ax.plot([0, lim], [0, lim], color=GRID, lw=1.4, zorder=1)
    ax.plot(cal.pred, cal.obs, marker="o", color=BLU, ms=6, lw=1.4, zorder=3)
    ax.set_xlabel("mean predicted booking propensity (decile)")
    ax.set_ylabel("observed booking rate")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.grid(color=GRID, lw=.6); ax.set_axisbelow(True)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig("fig_calibration.png", dpi=300, facecolor="white")
    print("\ncalibration by decile:")
    print(cal.round(4).to_string())
    print("\nwrote data/nuisance_metrics.csv, fig_calibration.png")


if __name__ == "__main__":
    main()
