"""Booking/substitution descriptives over the 90 minutes (backlog item C).

Canonical male sample (all male matches in the corrected frame). Computes headline stats (cards & subs per match, half
splits, half-time subs, censoring of booked players) and renders minute
histograms — overall and per position group.

Stoppage time is folded into the 45' and 90' bins (period-1 minutes clipped
to 45, period-2 to 90); half-time subs are recorded by StatsBomb at period 2,
minute 45.

Outputs: fig_desc_minutes_overall.png, fig_desc_minutes_by_position.png
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

YEL, BLU, INK, GRID = "#eda100", "#2a78d6", "#1b2733", "#e3e8ee"
CARD = ["foul_committed_card", "bad_behaviour_card"]


def load_events(mids):
    ev = pd.read_parquet("data/events.parquet",
        columns=["match_id", "player_id", "period", "minute", "type", "position"] + CARD,
        filters=[("match_id", "in", mids)])
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    return ev, card


def style(ax):
    ax.grid(axis="y", color=GRID, lw=.8, zorder=0); ax.set_axisbelow(True)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color("#c6ccd2")
    ax.axvline(45, color="#9aa3ad", lw=1, ls="--", zorder=1)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])


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

    ev, card = load_events(mids)
    yel = ev[card.eq("Yellow Card") & ev.period.le(2)].copy()
    sub = ev[(ev.type == "Substitution") & ev.period.le(2)].copy()
    for d in (yel, sub):
        d["m"] = np.where(d.period == 1, d.minute.clip(upper=45), d.minute.clip(upper=90))
        d["grp"] = d.position.map(posmap)
    # substitutions stamped at period 2, minute 45 are made DURING the
    # half-time interval (recorded at the restart) — show them separately
    sub["interval"] = (sub.period == 2) & (sub.minute == 45)
    sub_play = sub[~sub.interval]

    n = len(mids)
    ht = (sub.period == 2) & (sub.minute == 45)
    print(f"matches: {n:,}")
    print(f"yellow cards: {len(yel):,} ({len(yel)/n:.2f}/match) | "
          f"H1 {100*(yel.period==1).mean():.1f}% / H2 {100*(yel.period==2).mean():.1f}% | median {yel.m.median():.0f}'")
    print(f"substitutions: {len(sub):,} ({len(sub)/n:.2f}/match) | "
          f"at HT {ht.sum():,} ({100*ht.mean():.1f}%) | after 60' {100*(sub.m>60).mean():.1f}% | median {sub.m.median():.0f}'")
    print("\nper position (yellows | subs):")
    print(pd.DataFrame({"yellows": yel.grp.value_counts(), "subs": sub.grp.value_counts()}).to_string())

    bins = np.arange(0, 95, 5)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharex=True)
    ax = axes[0]
    ax.hist(yel.m, bins=bins, color=YEL, edgecolor="white", lw=.8, zorder=2)
    style(ax); ax.set_title("Yellow cards", fontsize=11, color=INK, loc="left", fontweight="bold")
    ax.set_xlabel("minute"); ax.set_ylabel("events")
    ax.text(46, ax.get_ylim()[1]*.93, "HT", fontsize=8, color="#9aa3ad")
    ax = axes[1]
    ax.hist(sub_play.m, bins=bins, color=BLU, edgecolor="white", lw=.8, zorder=2,
            label="during play")
    ax.bar(45, sub.interval.sum(), width=2.2, color="#9fc2ea", edgecolor=BLU,
           hatch="///", lw=.8, zorder=3, label="half-time interval")
    style(ax); ax.set_title("Substitutions", fontsize=11, color=INK, loc="left", fontweight="bold")
    ax.set_xlabel("minute")
    ax.legend(fontsize=8.5, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig("fig_desc_minutes_overall.png", dpi=300, facecolor="white")

    grps = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
    fig, axes = plt.subplots(4, 2, figsize=(10, 9), sharex=True)
    for i, g in enumerate(grps):
        ax = axes[i, 0]
        ax.hist(yel[yel.grp == g].m, bins=bins, color=YEL, edgecolor="white", lw=.8, zorder=2)
        style(ax)
        if i == 0: ax.set_title("Yellow cards", fontsize=11, color=INK, loc="left", fontweight="bold")
        ax.set_ylabel(g, fontsize=10, color=INK)
        if i == 3: ax.set_xlabel("minute")
        ax = axes[i, 1]
        gg = sub[sub.grp == g]
        ax.hist(gg[~gg.interval].m, bins=bins, color=BLU, edgecolor="white", lw=.8, zorder=2)
        ax.bar(45, gg.interval.sum(), width=2.2, color="#9fc2ea", edgecolor=BLU,
               hatch="///", lw=.8, zorder=3)
        style(ax)
        if i == 0:
            ax.set_title("Substitutions", fontsize=11, color=INK, loc="left", fontweight="bold")
            ax.legend(["during play", "half-time interval"], fontsize=8, frameon=False, loc="upper left")
        if i == 3: ax.set_xlabel("minute")
    fig.tight_layout()
    fig.savefig("fig_desc_minutes_by_position.png", dpi=300, facecolor="white")
    print("\nwrote fig_desc_minutes_overall.png, fig_desc_minutes_by_position.png")


if __name__ == "__main__":
    main()
