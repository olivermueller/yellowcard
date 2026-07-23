"""Attrition / eligibility table for the JQAS paper (T2).

Reproduces the sample construction step by step on the Spec-B match
universe (male, five European leagues, complete odds-era seasons) and
prints the surviving player-match count after each criterion:

  1. players listed in the match lineups
  2. started the match (Starting XI)
  3. outfield position (GK dropped)
  4. on the pitch through minute 60 (no substitution, temporary exit or
     sending-off before 60')
  5. no yellow card in the pre-window [0,15)
  6. at most one yellow card in the treatment window [15,45]
  7. age and betting odds available (complete case)

The final row must equal the analysis sample of build_male_dml.load().
Output: data/attrition_table.csv
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import CARD, EU_LEAGUES, load


def main():
    frame = pd.read_csv("data/analysis_frame.csv",
                        usecols=["match_id", "player_id", "gender", "competition", "season",
                                 "position", "position_group", "treat_yellow_card"],
                        low_memory=False)
    fr = frame[(frame.gender == "male") & frame.competition.isin(EU_LEAGUES)
               & ~frame.season.isin(["1973/1974", "1986/1987"])]
    mids = fr.match_id.unique().tolist()

    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "period", "minute", "type", "position"] + CARD,
        filters=[("match_id", "in", mids)])
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    posmap = frame.drop_duplicates("position").set_index("position").position_group.to_dict()
    posmap["Goalkeeper"] = "Goalkeeper"
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first().map(posmap).rename("grp"))

    lu = pd.read_parquet("data/lineups_male.parquet")
    d = lu[lu.match_id.isin(mids)][["match_id", "player_id", "started"]].copy()
    rows = [("Players listed in match lineups", len(d))]

    d = d[d.started]
    rows.append(("Started the match", len(d)))

    d = d.merge(pos, on=["match_id", "player_id"], how="left")
    d = d[d.grp.isin(["Defender", "Midfielder", "Forward"])]
    rows.append(("Outfield position", len(d)))

    exits = ev[((ev.type.isin(["Substitution", "Player Off"])) |
                card.isin(["Red Card", "Second Yellow"])) & (ev.minute < 60)]
    xk = set(zip(exits.match_id, exits.player_id))
    d = d[[k not in xk for k in zip(d.match_id, d.player_id)]]
    rows.append(("On the pitch through minute 60", len(d)))

    pre_y = ev[card.eq("Yellow Card") & (ev.period == 1) & (ev.minute < 15)]
    pk = set(zip(pre_y.match_id, pre_y.player_id))
    d = d[[k not in pk for k in zip(d.match_id, d.player_id)]]
    rows.append(("No yellow card in [0,15)", len(d)))

    ty = ev[card.eq("Yellow Card") & (ev.period == 1) & ev.minute.between(15, 45)]
    multi = ty.groupby(["match_id", "player_id"]).size()
    mk = set(multi[multi >= 2].index)
    d = d[[k not in mk for k in zip(d.match_id, d.player_id)]]
    rows.append(("At most one yellow in [15,45]", len(d)))

    spec = load()
    rows.append(("Age and betting odds available", len(spec)))

    out = pd.DataFrame(rows, columns=["criterion", "player_matches"])
    out["dropped"] = -out.player_matches.diff().fillna(0).astype(int)
    print(out.to_string(index=False))
    print(f"\nmatches: {len(mids):,} | treated in final sample: "
          f"{int(spec.treat_yellow_card.sum()):,} "
          f"({100*spec.treat_yellow_card.mean():.2f}%)")
    consistent = abs(rows[-2][1] - len(spec) - (rows[-2][1] - rows[-1][1])) == 0
    print("reconciles with build_male_dml.load():", rows[-1][1] == len(spec))
    out.to_csv("data/attrition_table.csv", index=False)
    print("wrote data/attrition_table.csv")


if __name__ == "__main__":
    main()
