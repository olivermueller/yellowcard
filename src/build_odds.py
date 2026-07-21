"""Betting-odds covariate for the big-5 2015/16 frame (backlog item E).

Downloads the five football-data.co.uk season files (Premier League E0,
La Liga SP1, Bundesliga D1, Serie A I1, Ligue 1 F1; season 2015/16), maps
StatsBomb team names to football-data names (normalised + fuzzy, with a
handful of manual fixes — note Inter/AC Milan collide under fuzzy matching),
and joins Bet365 match odds to every match in ``data/analysis_frame_big5.csv``
on (date, home, away).

One match (Marseille–Nantes, 2016-04-24) has no B365 odds in the source and
is patched with Pinnacle odds from the same row.

Output: data/odds/odds_big5_1516.csv with raw B365H/D/A plus de-vigged
implied probabilities ``odds_p_home`` / ``odds_p_draw`` (use
1 - p_home - p_draw for the away-win probability).
"""
import difflib, re, unicodedata, urllib.request
from pathlib import Path
import pandas as pd

ODDS_DIR = Path("data/odds")
LEAGUES = ["E0", "SP1", "D1", "I1", "F1"]
URL = "https://www.football-data.co.uk/mmz4281/1516/{}.csv"

# Manual fixes where normalisation/fuzzy matching fails or silently errs.
MANUAL = {
    "Inter Milan": "Inter",                    # fuzzy collides with AC Milan -> "Milan"
    "Athletic Club": "Ath Bilbao",
    "Borussia Mönchengladbach": "M'gladbach",
    "Gazélec Ajaccio": "Ajaccio GFCO",
    "Paris Saint-Germain": "Paris SG",
}


def norm(s):
    """Lowercase ASCII team-name key with club-form tokens stripped."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(fc|cf|ac|as|afc|ssc|us|ss|sc|rc|cd|ca|sd|ud|de|il|calcio|club)\b", " ", s.lower())
    return re.sub(r"[^a-z]", "", s)


def download():
    ODDS_DIR.mkdir(parents=True, exist_ok=True)
    for code in LEAGUES:
        dest = ODDS_DIR / f"{code}_1516.csv"
        if not dest.exists():
            urllib.request.urlretrieve(URL.format(code), dest)
            print(f"downloaded {dest}")


def load_odds():
    frames = []
    for code in LEAGUES:
        o = pd.read_csv(ODDS_DIR / f"{code}_1516.csv", encoding="latin-1").dropna(subset=["HomeTeam"])
        frames.append(o[["Date", "HomeTeam", "AwayTeam", "B365H", "B365D", "B365A", "PSH", "PSD", "PSA"]])
    odds = pd.concat(frames, ignore_index=True)
    odds["date"] = pd.to_datetime(odds.Date, format="mixed", dayfirst=True).dt.date.astype(str)
    return odds


def build_mapping(sb_teams, fd_teams):
    fdn = {norm(t): t for t in fd_teams}
    mapping = {}
    for t in sb_teams:
        n = norm(t)
        if n in fdn:
            mapping[t] = fdn[n]
            continue
        hit = difflib.get_close_matches(n, list(fdn), n=1, cutoff=0.6)
        mapping[t] = fdn[hit[0]] if hit else None
    mapping.update(MANUAL)
    assert None not in mapping.values(), f"unmapped: {[k for k, v in mapping.items() if v is None]}"
    assert len(set(mapping.values())) == len(mapping), "mapping not 1:1"
    return mapping


def main():
    download()
    frame = pd.read_csv("data/analysis_frame_big5.csv", usecols=["match_id"], low_memory=False).drop_duplicates()
    m = pd.read_csv("data/matches.csv", usecols=["match_id", "match_date", "home_team", "away_team"],
                    low_memory=False)
    m = m[m.match_id.isin(frame.match_id)].copy()
    odds = load_odds()

    mapping = build_mapping(sorted(set(m.home_team) | set(m.away_team)),
                            sorted(set(odds.HomeTeam) | set(odds.AwayTeam)))
    m["h"] = m.home_team.map(mapping)
    m["a"] = m.away_team.map(mapping)

    j = m.merge(odds, left_on=["match_date", "h", "a"],
                right_on=["date", "HomeTeam", "AwayTeam"], how="left")

    # Rows that joined but lack B365 odds: fall back to Pinnacle (sharpest book).
    fb = j.B365H.isna() & j.PSH.notna()
    if fb.any():
        print(f"patching {int(fb.sum())} match(es) with Pinnacle odds:",
              j.loc[fb, ["match_date", "home_team", "away_team"]].to_records(index=False))
        j.loc[fb, ["B365H", "B365D", "B365A"]] = j.loc[fb, ["PSH", "PSD", "PSA"]].values

    assert j.B365H.notna().all(), \
        f"missing odds: {j.loc[j.B365H.isna(), ['match_date', 'home_team', 'away_team']]}"

    inv = 1 / j[["B365H", "B365D", "B365A"]]
    tot = inv.sum(axis=1)
    j["odds_p_home"] = (inv.B365H / tot).round(4)
    j["odds_p_draw"] = (inv.B365D / tot).round(4)

    out = j[["match_id", "B365H", "B365D", "B365A", "odds_p_home", "odds_p_draw"]]
    out.to_csv(ODDS_DIR / "odds_big5_1516.csv", index=False)
    print(f"wrote {ODDS_DIR / 'odds_big5_1516.csv'} ({len(out)} matches, "
          f"p_home mean {j.odds_p_home.mean():.3f})")


if __name__ == "__main__":
    main()
