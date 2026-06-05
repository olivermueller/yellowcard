"""Single source of truth for the W (confounders) and Z (moderators) matrices
shared by 04_dml.ipynb and build_subgroup_figure.py.

Edit Z_NUM or CATS here to change the moderator set; both the notebook and
the heterogeneity figures will rebuild from this definition automatically.
"""
import pandas as pd


# Moderator set: numeric Z columns + categorical variables (entered as dummies)
Z_NUM = [
    "ht_score_diff",
]
CATS = ["position_group", "home_away", "gender", "competition_format"]


def build_W_Z(df):
    """Return (W, Z, W_NUM, Z_NUM, CATS, catdum) for the given analysis frame.

    Adds a derived `competition_format` column on df in place if missing:
    "league" for Domestic League, "cup" for everything else (international
    tournaments, domestic cups, club competitions).

    W: pre-window event counts + pre-match score & strength (no ht_*).
    Z: half-time game state + a few key team event diffs (no player-level
       columns, no str_*). Categorical dummies are shared by W and Z.
    """
    if "competition_format" not in df.columns:
        df["competition_format"] = (df["competition_type"] == "Domestic League").map({True: "league", False: "cup"})
    def _cols(p): return sorted(c for c in df.columns if c.startswith(p))
    W_NUM = (_cols("pre_player_n_") + _cols("pre_diff_n_") + ["pre_score_diff"])  # str_* dropped: all-matches experiment
    catdum = pd.get_dummies(df[CATS], drop_first=True, dtype=float)
    W = pd.concat([df[W_NUM].astype(float), catdum], axis=1)
    Z = pd.concat([df[Z_NUM].astype(float), catdum], axis=1)
    return W, Z, W_NUM, Z_NUM, CATS, catdum
