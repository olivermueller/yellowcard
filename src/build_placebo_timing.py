"""Timing placebos for the machinery-evaluation appendix (backlog G).

Two placebo designs; in both, the outcome precedes the placebo treatment,
so any estimated "effect" of a FUTURE booking reflects selection into
booking that the confounder set does not absorb.

  within_half: placebo treatment = first yellow in H2 minutes (60, 75];
      outcome = behaviour in [45, 60]; sample = on pitch through 75, no
      yellow through 60 in either half. Booking and outcome sit in the
      same half with no interruption -- the configuration the 30-45
      analysis showed to be contaminated by persistent activity spells,
      and the configuration the paper's design deliberately avoids.
  cross_break: placebo treatment = first yellow in H2 minutes (45, 60];
      outcome = behaviour in H1 from minute 30 (incl. stoppage); sample =
      on pitch through 60, no yellow in H1. Outcome and placebo booking
      are separated by the half-time interval -- the mirror image of the
      paper's design (H1 booking, interval, H2 outcome). If the interval
      breaks activity spells, this placebo should be near zero.

Sample and estimation mirror the main pipeline exactly: Spec-B frame rows
plus event-reconstructed extras, paper W + age + odds, HGB nuisances,
GroupKFold(5) by match, cluster-robust SEs by match.

Output: data/placebo_timing.csv (both designs x all four outcomes).
"""
import warnings; warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_male_dml import DVS, CARD, build_W, crossfit, ate
from build_multiwindow import (DEF_TYPES, OUT_TYPES, load_all, exits, bookings, build_extras,
                               window_counts)


def p2_first_yellow(ev):
    card = ev[CARD[0]].where(ev[CARD[0]].notna(), ev[CARD[1]])
    y = ev[card.eq("Yellow Card") & (ev.period == 2)]
    return (y.sort_values("minute").groupby(["match_id", "player_id"]).minute.first()
              .rename("p2_yellow_min"))


def p2_first_yellow_typed(ev):
    """First H2 yellow per player with its source: 'foul' (foul_committed_card)
    or 'dissent' (bad_behaviour_card: dissent, time-wasting, etc.)."""
    rows = []
    for col, src in [(CARD[0], "foul"), (CARD[1], "dissent")]:
        y = ev[ev[col].eq("Yellow Card") & (ev.period == 2)]
        rows.append(y[["match_id", "player_id", "minute"]].assign(src=src))
    y = pd.concat(rows).sort_values("minute")
    first = y.groupby(["match_id", "player_id"]).first().reset_index()
    return first.rename(columns={"minute": "p2y_min", "src": "p2y_src"})


def assemble_base(frame, ev, lu, book, exit_after, h1x, e2):
    """Frame + extras for starters without H1 exit, on pitch beyond exit_after."""
    starters = lu[lu.started][["match_id", "team_id", "player_id"]]
    starters = starters[[k not in h1x for k in zip(starters.match_id, starters.player_id)]]
    starters = starters.merge(e2, on=["match_id", "player_id"], how="left")
    starters["exit2"] = starters.exit2.fillna(999)
    elig = starters[starters.exit2 > exit_after]

    fkeys = set(zip(frame.match_id, frame.player_id))
    inf = [k in fkeys for k in zip(elig.match_id, elig.player_id)]
    f = frame.merge(elig[["match_id", "player_id"]], on=["match_id", "player_id"])
    cand = elig[~np.array(inf)][["match_id", "team_id", "player_id"]]
    extras = build_extras(cand, frame, ev, book)
    rows = [f.copy()]
    if len(extras):
        rows.append(extras)
    d = pd.concat(rows, ignore_index=True, sort=False)
    d = d.drop(columns=["book_min"], errors="ignore")
    bm = d.merge(book, on=["match_id", "player_id"], how="left").book_min
    d["h1_yellow"] = bm.notna().values
    return d


def attach_outcomes(d, counts):
    d = d.merge(counts, on=["match_id", "player_id"], how="left")
    for t in OUT_TYPES.values():
        d[t] = d[t].fillna(0) if t in d.columns else 0.0
    for col, t in OUT_TYPES.items():
        d[col] = d[t]
    d["post_n_opp_directed"] = d.pressure + d.tackle + d.foul_committed
    d["post_n_ball_directed"] = d.ball_recovery + d.clearance + d.block + d.interception
    return d.dropna(subset=["age"]).reset_index(drop=True)


def run_design(name, d):
    t = d.treat_yellow_card.values
    print(f"[{name}] n={len(d):,}, placebo-treated={int(t.sum()):,} "
          f"({100*t.mean():.2f}%)", flush=True)
    W = build_W(d)
    T_res, Y_res, e = crossfit(d, W)
    print(f"[{name}] propensity range: ({e.min():.4f}, {e.max():.4f})", flush=True)
    out = []
    for dv, lab in DVS.items():
        est, se, p = ate(T_res, Y_res[dv], d.match_id.values)
        cm = d.loc[t == 0, dv].mean()
        out.append(dict(design=name, dv=lab, n=len(d), treated=int(t.sum()),
                        control_mean=round(cm, 3), ate=round(est, 4), se=round(se, 4),
                        p=round(p, 4), rel=f"{100*est/cm:+.1f}%"))
        print(pd.DataFrame(out).tail(1).to_string(index=False, header=(len(out) == 1)),
              flush=True)
    return out


def main():
    frame, ev, lu = load_all()
    h1x, e2 = exits(ev)
    book = bookings(ev)                       # first H1 yellow
    p2y = p2_first_yellow(ev)
    results = []

    # ---- within_half: booking (60,75] on [45,60] outcomes ----
    d = assemble_base(frame, ev, lu, book, exit_after=75, h1x=h1x, e2=e2)
    d = d.merge(p2y, on=["match_id", "player_id"], how="left")
    d = d[~d.h1_yellow]
    d = d[~(d.p2_yellow_min <= 60)]
    d["treat_yellow_card"] = d.p2_yellow_min.between(61, 75).astype(int)
    d = attach_outcomes(d, window_counts(ev, 2, 45, 60))
    results += run_design("within_half", d)

    # ---- cross_break: booking (45,60] on H1 30+ outcomes ----
    d = assemble_base(frame, ev, lu, book, exit_after=60, h1x=h1x, e2=e2)
    d = d.merge(p2y, on=["match_id", "player_id"], how="left")
    d = d[~d.h1_yellow]
    d["treat_yellow_card"] = d.p2_yellow_min.le(60).fillna(False).astype(int)
    d = attach_outcomes(d, window_counts(ev, 1, 30, None))
    results += run_design("cross_break", d)

    # ---- cross_break by card source: dissent-type vs foul-type bookings ----
    # A future bad-behaviour booking (dissent, time-wasting) is not generated
    # by defensive-activity volume, so this variant shuts off the mechanical
    # behaviour->booking channel and isolates persistent-disposition selection.
    # The foul-card variant on the identical sample carries both channels.
    # Placebo window extended to minute 75 for power (dissent cards are rare).
    typed = p2_first_yellow_typed(ev)
    base = assemble_base(frame, ev, lu, book, exit_after=75, h1x=h1x, e2=e2)
    base = base.merge(typed, on=["match_id", "player_id"], how="left")
    base = base[~base.h1_yellow]
    booked75 = base.p2y_min.le(75).fillna(False)
    for src in ["dissent", "foul"]:
        d = base[~booked75 | (base.p2y_src == src)].copy()
        d["treat_yellow_card"] = (d.p2y_min.le(75).fillna(False)
                                  & (d.p2y_src == src)).astype(int)
        d = attach_outcomes(d, window_counts(ev, 1, 30, None))
        results += run_design(f"cross_break_{src}", d)

    pd.DataFrame(results).to_csv("data/placebo_timing.csv", index=False)
    print("\nwrote data/placebo_timing.csv")


if __name__ == "__main__":
    main()
