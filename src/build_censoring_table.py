"""Censoring-by-window table for the survival-selection analysis (backlog item C).

Population (canonical male sample): starters still on the pitch at the end of H1 (no sub-off or
sending-off during period 1). Treated = first yellow in [15', 45'] of H1;
control = starters with no H1 booking. For each candidate outcome window
45'-c we report the share censored by c (substituted — incl. half-time subs,
recorded by StatsBomb at period 2 minute 45 — or sent off), the control rate
standardized to the treated position x pre-activity-tercile mix (the canonical
bounds cell scheme), and the
implied Lee (2009) trimming fraction p = (q_c - q_t) / q_c with q = share
still observed.

The trimming fraction is the size of the control-survivor slice ("marginal"
players who would have been withdrawn had they been booked) that Lee bounds
delete from the top/bottom of the control outcome distribution.

Output: data/censoring_by_window.csv + printed table.
"""
import numpy as np, pandas as pd

CARD = ["foul_committed_card", "bad_behaviour_card"]
WINDOWS = [50, 60, 70, 80]


def main():
    af = pd.read_csv("data/analysis_frame.csv",
                     usecols=["match_id", "gender", "competition", "season",
                              "position", "position_group"], low_memory=False)
    af = af[(af.gender == "male")
            & af.competition.isin(["La Liga", "Ligue 1", "Premier League", "Serie A", "1. Bundesliga"])
            & ~af.season.isin(["1973/1974", "1986/1987"])]      # SPEC B match universe
    mids = af.match_id.unique().tolist()
    posmap = af.drop_duplicates("position").set_index("position").position_group.to_dict()
    posmap["Goalkeeper"] = "Goalkeeper"

    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "period", "minute", "type", "position"] + CARD,
        filters=[("match_id", "in", mids)])
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    pos = (ev.dropna(subset=["position", "player_id"]).sort_values(["period", "minute"])
             .groupby(["match_id", "player_id"]).position.first().map(posmap).rename("grp"))

    sub = ev[(ev.type == "Substitution") & ev.period.le(2)]
    red = ev[card.isin(["Second Yellow", "Red Card"]) & ev.period.le(2)]
    ex = pd.concat([sub, red])[["match_id", "player_id", "period", "minute"]]
    h1_exit = set(zip(*ex[ex.period == 1][["match_id", "player_id"]].values.T))
    exit2 = (ex[ex.period == 2].assign(m=lambda d: d.minute.clip(upper=90))
               .groupby(["match_id", "player_id"]).m.min().rename("exit2"))

    y1 = ev[card.eq("Yellow Card") & (ev.period == 1) & ev.minute.between(15, 45)]
    treated_keys = set(zip(*y1.drop_duplicates(["match_id", "player_id"])[["match_id", "player_id"]].values.T))
    booked_keys = set(zip(*ev[card.eq("Yellow Card") & (ev.period == 1)]
                          [["match_id", "player_id"]].drop_duplicates().values.T))

    lu = pd.read_parquet("data/lineups_male.parquet")
    E = lu[lu.started][["match_id", "player_id"]]
    E = E[[k not in h1_exit for k in zip(E.match_id, E.player_id)]].copy()
    E = E.merge(exit2, on=["match_id", "player_id"], how="left")
    E["exit2"] = E.exit2.fillna(999)
    E["key"] = list(zip(E.match_id, E.player_id))
    T = E[E.key.isin(treated_keys)].copy()
    C = E[~E.key.isin(booked_keys)].copy()
    print(f"population: starters on pitch at end of H1 | treated {len(T):,} | control {len(C):,}")

    pre = (ev[(ev.period == 1) & (ev.minute < 15)].groupby(["match_id", "player_id"])
             .size().rename("pre_n"))
    for D in (T, C):
        D2 = (D.merge(pos, on=["match_id", "player_id"], how="left")
                .merge(pre, on=["match_id", "player_id"], how="left"))
        D2["pre_n"] = D2.pre_n.fillna(0)
        act = pd.qcut(D2.pre_n.rank(method="first"), 3, labels=["low", "mid", "high"]).astype(str)
        D["cell"] = D2.grp.values + "|" + act.values

    print(f"HT withdrawal: treated {100*(T.exit2==45).mean():.1f}% vs control {100*(C.exit2==45).mean():.2f}%")

    rows = []
    w = T.cell.value_counts(normalize=True)
    for c in WINDOWS:
        t_c = (T.exit2 <= c).mean()
        cell_rates = C.groupby("cell").exit2.apply(lambda s, cc=c: (s <= cc).mean())
        c_adj = sum(w.get(k, 0) * cell_rates.get(k, np.nan) for k in w.index)
        lee = max(0.0, ((1 - c_adj) - (1 - t_c)) / (1 - c_adj))
        rows.append(dict(window=f"45-{c}", treated=f"{100*t_c:.1f}%",
                         control_adj=f"{100*c_adj:.1f}%", raw=f"{100*(C.exit2<=c).mean():.1f}%",
                         diff_pp=round(100 * (t_c - c_adj), 1), lee_trim=f"{100*lee:.1f}%"))
    out = pd.DataFrame(rows)
    print(); print(out.to_string(index=False))
    out.to_csv("data/censoring_by_window.csv", index=False)
    print("\nwrote data/censoring_by_window.csv")


if __name__ == "__main__":
    main()
