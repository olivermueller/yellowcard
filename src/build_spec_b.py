"""Spec B: male European domestic leagues, age + betting odds in W (backlog B/E).

Comparison spec to the canonical A (male, all competitions, age in W):
restrict to the five European leagues in the frame (all season blocks),
extend the football-data.co.uk odds join to every league-season present
(23 usable; the archival La Liga 1973/74 and Serie A 1986/87 singles have
no odds source and are dropped), and estimate the four DV ATEs twice on
the identical sample: W + age (isolates the sample effect vs A) and
W + age + odds (isolates the odds contribution).

Odds: first available of B365 -> Pinnacle -> BetWin -> Interwetten ->
William Hill; de-vigged team-perspective win/draw probabilities.

Outputs: data/odds/odds_european_male.csv, data/spec_b_results.csv.
"""
import warnings; warnings.filterwarnings("ignore")
import sys, time, urllib.request
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm as _norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_config import build_W_Z
from build_male_dml import HGB, crossfit, ate
from build_odds import norm as norm_name, MANUAL

EU = {"La Liga": "SP1", "Ligue 1": "F1", "Premier League": "E0",
      "Serie A": "I1", "1. Bundesliga": "D1"}
BOOKS = [("B365H", "B365D", "B365A"), ("PSH", "PSD", "PSA"), ("BWH", "BWD", "BWA"),
         ("IWH", "IWD", "IWA"), ("WHH", "WHD", "WHA")]
MANUAL2 = dict(MANUAL)
MANUAL2.update({"Wolverhampton Wanderers": "Wolves", "Deportivo Alavés": "Alaves",
                "Atlético Madrid": "Ath Madrid", "Athletic Club": "Ath Bilbao"})


def season_code(season):
    a, b = season.split("/")
    return a[-2:] + b[-2:]


def download(pairs):
    Path("data/odds").mkdir(parents=True, exist_ok=True)
    for code, sc in pairs:
        dest = Path(f"data/odds/{code}_{sc}.csv")
        if not dest.exists():
            url = f"https://www.football-data.co.uk/mmz4281/{sc}/{code}.csv"
            urllib.request.urlretrieve(url, dest)
            time.sleep(0.2)


def load_odds(pairs):
    frames = []
    for code, sc in pairs:
        o = pd.read_csv(f"data/odds/{code}_{sc}.csv", encoding="latin-1",
                        on_bad_lines="skip").dropna(subset=["HomeTeam"])
        keep = ["Date", "HomeTeam", "AwayTeam"] + [c for trio in BOOKS for c in trio if c in o.columns]
        frames.append(o[keep])
    odds = pd.concat(frames, ignore_index=True)
    odds["date"] = pd.to_datetime(odds.Date, format="mixed", dayfirst=True).dt.date.astype(str)
    H = pd.Series(np.nan, index=odds.index); D = H.copy(); A = H.copy()
    for h, d, a in BOOKS:
        if h in odds.columns:
            m = H.isna() & odds[h].notna()
            H[m], D[m], A[m] = odds.loc[m, h], odds.loc[m, d], odds.loc[m, a]
    odds["oH"], odds["oD"], odds["oA"] = H, D, A
    return odds.dropna(subset=["oH"])


def build_mapping(sb, fd):
    import difflib
    fdn = {norm_name(t): t for t in fd}
    mapping = {}
    for t in sb:
        if t in MANUAL2:
            mapping[t] = MANUAL2[t]; continue
        n = norm_name(t)
        if n in fdn:
            mapping[t] = fdn[n]; continue
        hit = difflib.get_close_matches(n, list(fdn), n=1, cutoff=0.6)
        mapping[t] = fdn[hit[0]] if hit else None
    return mapping


def main():
    df = pd.read_csv("data/analysis_frame.csv", low_memory=False)
    df = df[(df.gender == "male") & df.competition.isin(EU)].copy()
    df = df[~df.season.isin(["1973/1974", "1986/1987"])]
    dob = pd.read_parquet("data/player_dob.parquet")[["player_id", "dob"]]
    df = df.merge(dob, on="player_id", how="left")
    df["age"] = (pd.to_datetime(df.match_date) - pd.to_datetime(df.dob)).dt.days / 365.25
    df = df.dropna(subset=["age"]).reset_index(drop=True)

    pairs = sorted({(EU[c], season_code(s)) for c, s in
                    df[["competition", "season"]].drop_duplicates().values})
    print(f"sample: {len(df):,} rows, treated {int(df.treat_yellow_card.sum()):,} | "
          f"{len(pairs)} league-season odds files")
    download(pairs)
    odds = load_odds(pairs)

    m = df.drop_duplicates("match_id")[["match_id", "match_date", "team_name",
                                        "opponent_name", "home_away"]].copy()
    m["home"] = np.where(m.home_away == "home", m.team_name, m.opponent_name)
    m["away"] = np.where(m.home_away == "home", m.opponent_name, m.team_name)
    mapping = build_mapping(sorted(set(m.home) | set(m.away)),
                            sorted(set(odds.HomeTeam) | set(odds.AwayTeam)))
    unmapped = [k for k, v in mapping.items() if v is None]
    if unmapped:
        print("UNMAPPED TEAMS:", unmapped)
    m["h"] = m.home.map(mapping); m["a"] = m.away.map(mapping)
    j = m.merge(odds, left_on=["match_date", "h", "a"],
                right_on=["date", "HomeTeam", "AwayTeam"], how="left")
    print(f"odds joined: {j.oH.notna().sum()}/{len(m)} matches")
    miss = j[j.oH.isna()]
    if len(miss):
        print("missing matches:\n", miss[["match_date", "home", "away"]].head(15).to_string(index=False))
    inv = pd.DataFrame({"h": 1 / j.oH, "d": 1 / j.oD, "a": 1 / j.oA})
    tot = inv.sum(axis=1)
    j["odds_p_home"] = inv.h / tot; j["odds_p_draw"] = inv.d / tot
    j[["match_id", "odds_p_home", "odds_p_draw"]].to_csv(
        "data/odds/odds_european_male.csv", index=False)

    df = df.merge(j[["match_id", "odds_p_home", "odds_p_draw"]], on="match_id", how="left")
    df = df.dropna(subset=["odds_p_home"]).reset_index(drop=True)
    df["odds_p_win"] = np.where(df.home_away == "home", df.odds_p_home,
                                1 - df.odds_p_home - df.odds_p_draw)
    print(f"final spec-B sample: {len(df):,} rows, treated {int(df.treat_yellow_card.sum()):,}")

    W0, _, _, _, _, _ = build_W_Z(df)
    W_age = pd.concat([W0, df[["age"]].astype(float)], axis=1)
    W_age = W_age.loc[:, W_age.nunique() > 1]
    W_odds = pd.concat([W_age, df[["odds_p_win", "odds_p_draw"]].astype(float)], axis=1)

    rows = []
    for label, W in [("B_age", W_age), ("B_age_odds", W_odds)]:
        T_res, Y_res, e = crossfit(df, W)
        for dv, lab in [("post_n_def_events", "def_engagement"), ("post_n_pressure", "pressures"),
                        ("post_n_tackle", "tackles"), ("post_n_foul_committed", "fouls")]:
            est, se, p = ate(T_res, Y_res[dv], df.match_id.values)
            cm = df.loc[df.treat_yellow_card == 0, dv].mean()
            rows.append(dict(spec=label, dv=lab, control_mean=round(cm, 3), ate=round(est, 4),
                             se=round(se, 4), p=round(p, 4), rel=f"{100*est/cm:+.1f}%"))
        print(pd.DataFrame(rows)[pd.DataFrame(rows).spec == label].to_string(index=False), flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("data/spec_b_results.csv", index=False)
    print("\nwrote data/spec_b_results.csv")


if __name__ == "__main__":
    main()
