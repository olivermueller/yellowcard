"""Z-driven heterogeneity bar-chart figures.

Driven by the W/Z definition in ``analysis_config.py`` — whenever Z changes
there, both figures rebuild automatically. Categorical dummies are
reconstructed back to their multi-level originals (one panel per categorical,
with as many bars as levels); continuous half-time moderators are shown as
3-bar sign-cut subgroup ATEs to mirror the categorical layout.

Outputs (one per variable-family of Z):
  fig_subgroup_categoricals.png  — categoricals + half-time game state.
  fig_subgroup_ht_team.png       — ht_diff_n_* moderators (signed event-diffs).

Reuses the same cross-fit residuals as the notebook (Y_res = Y - m̂(W),
T_res = T - ê(W)). Degenerate splits (any subgroup < MIN_GROUP_N) are skipped.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

from analysis_config import build_W_Z, CATS

plt.rcParams["font.family"] = "Helvetica"
MIN_GROUP_N = 50

# Resolve paths relative to the repo root so the script can be invoked from
# either the project root (`python src/build_subgroup_figure.py`) or from
# inside src/. Outputs go to documents/ (kept out of the public repo).
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR  = REPO_ROOT / "data"
OUT_DIR   = REPO_ROOT / "documents"
OUT_DIR.mkdir(exist_ok=True)

# ---- data + nuisances ------------------------------------------------------
df = pd.read_csv(DATA_DIR / "analysis_frame.csv", low_memory=False)
DVS = ["post_n_pressure", "post_n_tackle", "post_n_foul_committed", "post_n_def_events"]
DV_LABEL = {"post_n_pressure": "Pressures", "post_n_tackle": "Tackles",
            "post_n_foul_committed": "Fouls", "post_n_def_events": "Def. engagement (sum)"}
# Single one-row "fouls" variant used as the paper's heterogeneity figure,
# where the subgroup effects are largest and most interpretable.
DV_VARIANTS = {
    "fouls": ["post_n_foul_committed"],
}
t = df["treat_yellow_card"].astype(int).values
groups = df["match_id"].values
W, Z, _W_NUM, _Z_NUM, _CATS, _catdum = build_W_Z(df)
assert not any(c.startswith("ht_")  for c in W.columns)
assert not any(c.startswith("str_") for c in Z.columns)

MY = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, min_samples_leaf=200, random_state=0)
MT = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, min_samples_leaf=200, random_state=0)
cf = GroupKFold(5)
e_hat = cross_val_predict(clone(MT), W, t, groups=groups, cv=cf, n_jobs=-1, method="predict_proba")[:, 1]
T_res = t - e_hat
YRES = {dv: df[dv].astype(float).values
             - cross_val_predict(clone(MY), W, df[dv].astype(float).values,
                                 groups=groups, cv=cf, n_jobs=-1) for dv in DVS}

# ---- moderator classification ---------------------------------------------
CAT_LEVELS = {c: sorted(df[c].astype(str).unique().tolist()) for c in CATS}
BLUE, ORANGE, GREY, RED = "#4f82c2", "#c98a3b", "#7f7f7f", "#c0504d"

def family_of(name, kind):
    if kind == "categorical":           return "categoricals"
    if name == "ht_score_diff":         return "categoricals"   # share the bar figure
    if name.startswith("ht_diff_n_"):   return "ht_team"
    if name.startswith("ht_player_n_"): return "ht_player"
    return "other"

def derive_moderators(Z_cols):
    out, seen = [], set()
    for col in Z_cols:
        cat = next((c for c in sorted(CATS, key=len, reverse=True)
                    if col.startswith(c + "_")), None)
        if cat:
            if cat not in seen:
                seen.add(cat); out.append({"name": cat, "kind": "categorical"})
        else:
            out.append({"name": col, "kind": "continuous"})
    return out

def group_for(mod):
    """Return (g_array, ordered_levels) — auto rule based on column shape."""
    if mod["kind"] == "categorical":
        return df[mod["name"]].astype(str).values, CAT_LEVELS[mod["name"]]
    col = mod["name"]; x = Z[col]
    if col == "ht_score_diff":
        v = x.values
        return (np.where(v < 0, "trailing", np.where(v > 0, "leading", "level")),
                ["trailing", "level", "leading"])
    if col.startswith("ht_diff_n_"):
        # signed team-vs-opponent event diff: binary split at the median (~0)
        # 3-level sign cut would produce a thin, noisy "parity" group for high-volume events.
        m = float(np.median(x.values))
        return (np.where(x.values > m, "team ahead", "team behind / equal"),
                ["team behind / equal", "team ahead"])
    if x.nunique() <= 2:
        return x.astype(int).astype(str).values, [str(v) for v in sorted(x.unique())]
    m = x.median()
    if m == 0:
        return np.where(x.values > 0, "high", "zero"), ["zero", "high"]
    return np.where(x.values > m, "high", "low"), ["low", "high"]

def colors_for(mod, levels):
    if mod["kind"] == "categorical" and len(levels) > 3:
        cmap = plt.get_cmap("tab10")
        return [cmap(i % 10) for i in range(len(levels))]
    if mod.get("name") == "ht_score_diff":
        return [RED, GREY, BLUE]
    if mod["kind"] == "continuous" and mod["name"].startswith("ht_diff_n_"):
        return [RED, BLUE]   # below/equal, ahead
    if len(levels) == 2:
        return [BLUE, ORANGE]
    return [BLUE, GREY, ORANGE][:len(levels)]

def short_label(col):
    return (col.replace("ht_diff_n_", "")
              .replace("ht_player_n_", "")
              .replace("competition_", "")
              .replace("_", " "))

PANEL_TITLES = {
    "ht_score_diff":      "Score",
    "position_group":     "Position",
    "home_away":          "Venue",
    "gender":             "Gender",
    "competition_format": "Competition Format",
}

def panel_title(mod):
    if mod["name"] in PANEL_TITLES:           return PANEL_TITLES[mod["name"]]
    if mod["name"].startswith("ht_diff_n_"):
        return f"team−opp diff: {short_label(mod['name'])}"
    return mod["name"].replace("_", " ")

# ---- estimator -------------------------------------------------------------
def subgroup(dv, mod):
    g, levels = group_for(mod)
    counts = pd.Series(g).value_counts()
    if any(counts.get(l, 0) < MIN_GROUP_N for l in levels) or len(set(g)) < 2:
        return None
    d = pd.DataFrame({"Yr": YRES[dv], "Tr": T_res, "m": groups,
                      "g": pd.Categorical(g, categories=levels, ordered=False)})
    fit  = smf.ols("Yr ~ Tr:C(g) - 1", data=d).fit(cov_type="cluster", cov_kwds={"groups": d["m"]})
    fit2 = smf.ols("Yr ~ Tr + Tr:C(g)", data=d).fit(cov_type="cluster", cov_kwds={"groups": d["m"]})
    inter = [p for p in fit2.params.index if p.startswith("Tr:C(g)")]
    R = np.zeros((len(inter), len(fit2.params)))
    for i, nm in enumerate(inter):
        R[i, list(fit2.params.index).index(nm)] = 1
    pint = float(fit2.f_test(R).pvalue)
    vals = []
    for lvl in levels:
        coef = f"Tr:C(g)[{lvl}]"
        if coef in fit.params.index:
            vals.append((fit.params[coef], 1.96 * fit.bse[coef], fit.pvalues[coef]))
        else:
            vals.append((np.nan, np.nan, np.nan))
    return vals, levels, colors_for(mod, levels), pint

# ---- group Z columns by family --------------------------------------------
MODERATORS = derive_moderators(Z.columns)
fam_mods = {"categoricals": [], "ht_team": [], "ht_player": []}
for m in MODERATORS:
    fam = family_of(m["name"], m["kind"])
    if fam in fam_mods:
        fam_mods[fam].append(m)

# ---- shared bar-grid renderer ---------------------------------------------
HOW_TO_READ = (
    "How to read.  Each panel = one moderator. Bars = within-subgroup DML "
    "treatment effect (effect of an early yellow card on the post-window event "
    "count); whiskers = 95% cluster-robust CI; stars = within-group significance "
    "(* p<.05, ** p<.01, *** p<.001). Header q = Benjamini–Hochberg-adjusted "
    "joint interaction test across the moderator's levels (FDR-controlled within "
    "each row of moderators). Negative bars = the card reduces the action.")

def bar_grid(mods, outfile, extra_note="", dvs=None):
    if not mods:
        print(f"skip {outfile}: no moderators"); return
    if dvs is None: dvs = DVS
    ncol = len(mods); nrow = len(dvs)
    widths = [max(2.0, 0.85 * len(group_for(m)[1])) for m in mods]
    row_h = 2.2 if nrow == 1 else 1.8
    fig, axes = plt.subplots(nrow, ncol, figsize=(sum(widths) + 1.6, row_h * nrow + 1.4),
                             gridspec_kw={"width_ratios": widths},
                             sharey="row", squeeze=False)
    # ---- first pass: collect subgroup results so we can BH-adjust per row ----
    cells = {}  # (r, c) -> subgroup() result or None
    for r, dv in enumerate(dvs):
        for c, mod in enumerate(mods):
            cells[(r, c)] = subgroup(dv, mod)
    # BH per row over the joint interaction p-values
    q_by_cell = {}
    for r in range(nrow):
        row_keys = [(r, c) for c in range(ncol) if cells[(r, c)] is not None]
        pints = [cells[k][3] for k in row_keys]
        if pints:
            _, qvals, _, _ = multipletests(pints, alpha=0.05, method="fdr_bh")
            for k, q in zip(row_keys, qvals):
                q_by_cell[k] = float(q)
    # ---- second pass: render ----
    for r, dv in enumerate(dvs):
        for c, mod in enumerate(mods):
            ax = axes[r][c]
            res = cells[(r, c)]
            if res is None:
                ax.set_axis_off(); continue
            vals, levels, colors, pint = res
            qint = q_by_cell[(r, c)]
            ates = np.array([v[0] for v in vals]); cis = np.array([v[1] for v in vals])
            x_pos = np.arange(len(levels))
            ax.bar(x_pos, ates, width=0.66, color=colors, edgecolor="#222", linewidth=0.7,
                   yerr=cis, capsize=4, error_kw=dict(elinewidth=1.1, ecolor="#222"))
            ax.axhline(0, color="#444", lw=0.9)
            span = (np.abs(ates) + cis).max() + 1e-9
            for xi, (a, ci, p) in zip(x_pos, vals):
                if np.isnan(p): continue
                star = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
                if star:
                    ax.text(xi, a + (ci + .04 * span if a >= 0 else -(ci + .04 * span)),
                            star, ha="center", va="bottom" if a >= 0 else "top",
                            fontsize=10, fontweight="bold")
            ax.set_xticks(x_pos)
            ax.set_xticklabels([str(l) for l in levels],
                               fontsize=8.5, rotation=25, ha="right")
            ax.tick_params(axis="y", labelsize=8.5)
            ax.spines[["top", "right"]].set_visible(False)
            if r == 0:
                ax.set_title(panel_title(mod), fontsize=11, fontweight="bold", pad=18)
            qstar = "***" if qint < .001 else "**" if qint < .01 else "*" if qint < .05 else ""
            ax.text(0.5, 1.005, f"q = {qint:.3f}{('  ' + qstar) if qstar else ''}",
                    transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5,
                    color="#c0392b" if qint < .05 else "#888")
            if c == 0:
                ax.set_ylabel(f"{DV_LABEL[dv]}\nATE", fontsize=10, fontweight="bold")
    # The "how to read" caption is no longer rendered into the figure itself;
    # it lives in the LaTeX figure caption instead. HOW_TO_READ and extra_note
    # are kept above for use as ready-to-paste caption copy.
    _ = HOW_TO_READ, extra_note  # silence unused warnings
    fig.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig); print("wrote", outfile)

TEAM_NOTE = ("For team event-diff moderators, bars split players by the team-vs-opponent "
             "count at half-time (median cut, ≈ zero by symmetry): "
             "'team behind / equal' = team had ≤ opponent in this event over [0, 45); "
             "'team ahead' = team had more.")

# Two variants per family: engagement (1 DV) and detail (3 DVs)
for variant, dvs in DV_VARIANTS.items():
    bar_grid(fam_mods["categoricals"],
             OUT_DIR / f"fig_subgroup_categoricals_{variant}.png", dvs=dvs)
    bar_grid(fam_mods["ht_team"],
             OUT_DIR / f"fig_subgroup_ht_team_{variant}.png", dvs=dvs,
             extra_note=TEAM_NOTE)
