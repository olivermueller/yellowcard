"""Builds the pre-match betting-odds table for the analysis sample.

Downloads football-data.co.uk odds for every league-season in the sample,
maps team names, joins fixtures (with a +-3 day rescue for postponed
matches), removes the bookmaker margin, and writes de-vigged home/draw
probabilities per match.

Output: data/odds/odds_european.csv
"""
import warnings; warnings.filterwarnings("ignore")
import time, urllib.request
from pathlib import Path
import numpy as np, pandas as pd


import re, unicodedata

MANUAL = {
    "Inter Milan": "Inter",                    # fuzzy collides with AC Milan -> "Milan"
    "Athletic Club": "Ath Bilbao",
    "Borussia M\u00f6nchengladbach": "M'gladbach",
    "Gaz\u00e9lec Ajaccio": "Ajaccio GFCO",
    "Paris Saint-Germain": "Paris SG",
}


def norm_name(s):
    """Lowercase ASCII team-name key with club-form tokens stripped."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(fc|cf|ac|as|afc|ssc|us|ss|sc|rc|cd|ca|sd|ud|de|il|calcio|club)\b", " ", s.lower())
    return re.sub(r"[^a-z]", "", s)


EU = {"La Liga": "SP1", "Ligue 1": "F1", "Premier League": "E0",
      "Serie A": "I1", "1. Bundesliga": "D1"}
BOOKS = [("B365H", "B365D", "B365A"), ("PSH", "PSD", "PSA"), ("BWH", "BWD", "BWA"),
         ("IWH", "IWD", "IWA"), ("WHH", "WHD", "WHA")]
MANUAL2 = dict(MANUAL)
MANUAL2.update({"Wolverhampton Wanderers": "Wolves", "Deportivo Alavés": "Alaves",
                "Atlético Madrid": "Ath Madrid", "Athletic Club": "Ath Bilbao",
                "Bolton Wanderers": "Bolton", "Stade Brestois": "Brest"})


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
    odds["date"] = pd.to_datetime(odds.Date, dayfirst=True).dt.date.astype(str)
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
    # rescue postponed/off-by-date fixtures within +-3 days
    miss = j[j.oH.isna()]
    if len(miss):
        o2 = odds.copy(); o2["dt"] = pd.to_datetime(o2.date)
        for i, r in miss.iterrows():
            cand = o2[(o2.HomeTeam == r.h) & (o2.AwayTeam == r.a)]
            cand = cand[(cand.dt - pd.to_datetime(r.match_date)).abs().dt.days <= 3]
            if len(cand):
                j.loc[i, ["oH", "oD", "oA"]] = cand.iloc[0][["oH", "oD", "oA"]].values
    print(f"odds joined: {j.oH.notna().sum()}/{len(m)} matches")
    miss = j[j.oH.isna()]
    if len(miss):
        print("missing matches:\n", miss[["match_date", "home", "away"]].head(15).to_string(index=False))
    inv = pd.DataFrame({"h": 1 / j.oH, "d": 1 / j.oD, "a": 1 / j.oA})
    tot = inv.sum(axis=1)
    j["odds_p_home"] = inv.h / tot; j["odds_p_draw"] = inv.d / tot
    j[["match_id", "odds_p_home", "odds_p_draw"]].to_csv(
        "data/odds/odds_european.csv", index=False)


if __name__ == "__main__":
    main()
