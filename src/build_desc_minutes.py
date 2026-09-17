"""Booking/substitution descriptives over the 90 minutes (backlog item C).

Canonical male sample (all male matches in the corrected frame). Computes headline stats (cards & subs per match, half
splits, half-time subs, censoring of booked players) and renders minute
histograms — overall and per position group.

Stoppage time is folded into the 45' and 90' bins (period-1 minutes clipped
to 45, period-2 to 90); half-time subs are recorded by StatsBomb at period 2,
minute 45.

Outputs: fig_timing_cards.png, fig_timing_subs.png (each a 2x2 grid:
overall + Defender/Midfielder/Forward panels).
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
    # outfield players only, consistent with the analysis sample
    yel = yel[yel.grp.isin(["Defender", "Midfielder", "Forward"])]
    sub = sub[sub.grp.isin(["Defender", "Midfielder", "Forward"])]
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
    grps = ["Defender", "Midfielder", "Forward"]

    # --- yellow cards: overall, single panel ---
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.hist(yel.m, bins=bins, color=YEL, edgecolor="white", lw=.8, zorder=2)
    style(ax)
    ax.set_ylabel("events"); ax.set_xlabel("minute")
    ax.text(46, ax.get_ylim()[1]*.93, "HT", fontsize=8, color="#9aa3ad")
    fig.tight_layout()
    fig.savefig("fig_timing_cards.png", dpi=300, facecolor="white")

    # --- substitutions: overall + per position group (2x2) ---
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), sharex=True)
    panels = [("All outfield players", sub)] + [(g, sub[sub.grp == g]) for g in grps]
    for k, (ax, (ttl, d)) in enumerate(zip(axes.ravel(), panels)):
        _, _, hp = ax.hist(d[~d.interval].m, bins=bins, color=BLU, edgecolor="white",
                           lw=.8, zorder=2)
        hb = ax.bar(45, d.interval.sum(), width=2.2, color="#9fc2ea", edgecolor=BLU,
                    hatch="///", lw=.8, zorder=3)
        style(ax)
        ax.set_title(ttl, fontsize=11, color=INK, loc="left", fontweight="bold")
        if k == 0:
            ax.legend(handles=[hp[0], hb[0]], labels=["during play", "half-time interval"],
                      fontsize=8.5, frameon=False, loc="upper left")
    for i in (0, 2): axes.ravel()[i].set_ylabel("events")
    for i in (2, 3): axes.ravel()[i].set_xlabel("minute")
    fig.tight_layout()
    fig.savefig("fig_timing_subs.png", dpi=300, facecolor="white")
    print("\nwrote fig_timing_cards.png, fig_timing_subs.png")


if __name__ == "__main__":
    main()
