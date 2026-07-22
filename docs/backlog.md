# Yellow-Card Paper — Project Backlog

**Source:** Co-author meeting 2026-07-14. **Primary target:** Journal of Quantitative Analysis in Sports (JQAS).
**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · **(P1/P2/P3)** priority.

---

## A. Story & framing
- [ ] **(P1)** Reframe the paper so the **"yellow cards" research question is the headline**; causal ML is presented as *method*, not contribution.
- [ ] **(P2)** Rewrite abstract + intro to lead with the football/behaviour question; move DML machinery to the methods section.

## B. Data scope & filtering
- [x] **(P1)** Stay on **StatsBomb open data** (decided). Do *not* introduce new event sources.
- [x] **(P1)** ~~Big-5 2015/16 filter~~ **REVISED 2026-07-22: too much power lost (ATEs same sign but n.s. at half the n). Sample = FULL MALE frame** (66,582 rows / 2,942 treated after age complete-case). Big-5 frame kept as data artifact; big-5 DML run superseded and removed.
- [ ] **(P2)** Document the final sample definition + inclusion/exclusion counts for the paper.

## C. Survival bias / outcome window
- [~] **(P1)** **CANONICAL SPEC LOCKED (2026-07-22, Oliver):** male-only · age in W and tested as Z · eligibility = starters, no H1 exit, on pitch through post window; **CORRECTED (Oliver): controls MAY be carded in the post window** — no explicit card filter; a treated player's post-window yellow = second yellow -> sending-off, excluded automatically by the on-pitch rule. Consequence: notebook 02's `no_yellow_in_post` criterion DISABLED (it deleted high-fouling carded controls and attenuated the foul effect — affects the published Table 2 too) and frame rebuilt again. Conditional Lee bounds (count + binary, SEs -> Imbens-Manski CIs) for every H2 window. Canonical chain v2 running: frame rebuild -> multiwindow -> count bounds -> binary bounds -> 27-cell anchor -> IM CIs -> Table 2 -> male_dml (age-as-Z subgroups).
- [x] **(P1)** **Multi-window analysis DONE (2026-07-22, `src/build_multiwindow.py`, `data/multiwindow_results.csv`)**: fouls **−23% to −27% (p<.0001) stable across 45-50/60/70/80**; def_eng −5.6 to −7.0%; pressures −4.5 to −6.3%; tackles null. Effect at full strength already in the near-censoring-free 45-50 anchor and durable through 80'. **30-45 window (T=[15,30]) shows fouls +17.4% — adjacent-window contamination** (booking arrives during a high-foul spell that persists; no HT reset; W=[0,15) can't absorb the 15-30 spell) → empirically justifies the H2 outcome design; not a valid anchor.
- [ ] **(P1)** **FRAME BUG found & verified (2026-07-22): the paper frame's `is_starter` criterion uses StatsBomb "Player On" events, which only mark re-entry after temporary absence — substitutes coming on have NO such event.** Result: ~26% of frame rows are non-starters with empty pre-window W (mean 0.02 passes in [0,15)) and truncated outcomes; stated "on pitch from kick-off through 60" was silently unenforced. Fix = lineup-based Starting XI flag (as in multiwindow pipeline). **Notebook 02 must be corrected and all paper numbers re-derived from the fixed frame.**
- [x] **(P1)** **Booking/substitution descriptives + censoring table** (done 2026-07-21): `src/build_desc_minutes.py` (minute histograms overall + per position; 7,872 yellows 4.32/match rising through the game, Defenders most-booked/least-subbed; 10,473 subs 5.74/match, 7.2% at HT, median 71') and `src/build_censoring_table.py` (`data/censoring_by_window.csv`). **Key: booked players withdrawn at HT 3.5% vs 1.78% for comparable controls (~2x, robust to position x starter-share adjustment). Lee trims: 45-50 2.4%, 45-60 5.5%, 45-70 8.9%, 45-80 11.4%** — quantifies the window bias-signal trade-off; plan = effects per window + Lee bounds.
- [ ] **(P1)** **DECIDED 2026-07-21:** report the coach-response finding — *a first-half booking nearly doubles the probability of being withdrawn at half-time* (3.5% vs 1.78%) — as a result in its own right (extensive margin: coach substitutes; intensive margin: surviving players adapt).
- [x] **(P1)** Lee bounds v1 (blunt, unconditional trim + DML re-run) implemented in `src/build_male_dml.py` — male-sample trim 6.4% (treated 11.9% vs position-adj control 5.9% censored by 60'). Lower bounds tight (approx. -6.5% def_eng); **upper bounds cross zero — artifact of unconditional trimming on right-skewed counts**, not evidence of fragility.
- [x] **(P1)** **Conditional Lee bounds run (2026-07-22)** — `src/build_lee_conditional.py` (cell-based: position x pre-activity tercile; per-cell trims 2.0-10.9%), `data/male_dml_lee_conditional.csv`. Upper bounds tightened ~25% vs blunt (def_eng +17.7% -> +13.0%) **but still cross zero — at ~6% censoring, worst-case trimming bounds cannot certify the 45-60' effect on their own**. Cite Lee (2009) + Semenova (better Lee bounds); estimand = effect among always-on-pitch players.
- [x] **(P1)** **Conditional Lee bounds for ALL H2 windows (2026-07-22, `src/build_lee_windows.py`, `data/lee_bounds_windows.csv`; supersedes the anchor-only run)**: consistent family on the corrected sample; trims grow 0-5.4% (45-50) to 5.2-18.2% (45-80); upper bounds widen monotonically (def_eng +4.2% -> +8.5%) — the bias-signal frontier in one table. All cross zero (rare-count bluntness). Earlier anchor-only run: 45-50 conditional Lee bounds ~3x tighter than 45-60 (def_eng upper +13.0% -> **+4.2%** vs ATE -6.8%; fouls +35.2% -> +11.6% vs -25.2%) **but still cross zero. Diagnosis: worst-case trimming bounds on RARE COUNTS are inherently near-vacuous** (trimming 3% of controls with >=1 foul moves a 0.098 mean by ~1/3) — a property of the method, not the effect.
- [ ] **(P1)** **Bounds reporting plan:** (a) report anchor bounds as the formal worst case, noting the adversary must allocate essentially all top-tail control foulers to the marginal stratum; (b) **plausibility figure**: H1 observable profiles of actually-withdrawn booked players vs control survivors; (c) DONE (2026-07-22, `src/build_lee_binary.py`, `data/lee_bounds_binary.csv`): **binarized-outcome bounds EXCLUDE ZERO in key cells** — P(any def action) and P(any pressure) at the 45-50 anchor ([-4.1,-0.8]pp and [-3.9,-0.5]pp); P(any foul) at 45-70 ([-11.3,-0.6]pp) and 45-80 ([-15.1,-1.8]pp); at 45-50/60 the P(any foul) upper bound barely misses (+0.8/+0.4pp vs effects -2.3/-5.0pp). Note: extensive margin saturates for pressures/def-action at windows >=60 (control P ~0.87-0.98 → binary ATE ~0; effect is intensive-margin there) — expected ceiling, not a contradiction. TODO for paper: Imbens-Manski confidence intervals around the bounds (current bounds are point-identification bounds).
- [x] **(P1)** **Male-sample DML re-run (2026-07-22, `src/build_male_dml.py`): headline results replicate with age in W** — fouls -13.5% (p=.010), pressures -3.6% (p=.045), def_eng -3.9% (p=.031), tackles null. Game state (q=.019) and position (q=.030) survive BH; age as moderator null. Big-5 insignificance was power, not confounding. `data/male_dml_results.csv`, `data/male_dml_subgroups.csv`.
- [ ] **(P2)** Report effect estimates across all windows; discuss sensitivity of conclusions to the window choice.
- [ ] **(P3)** (Considered, deprioritised) per-minute normalisation — superseded by multi-window; revisit only if windows prove insufficient.

## D. Outcomes / targets
- [ ] **(P1)** Keep **overall defensive actions** as a headline outcome.
- [ ] **(P1)** Add **fine-grained defensive actions** (decompose the aggregate).
- [ ] **(P1)** Add **"error" events** — dispossessed, unforced errors, miscontrols, etc.
- [ ] **(P2)** Add **rate-based targets** (e.g., duel/tackle win rate) alongside raw counts.
- [ ] **(P2)** Define + document each target's exact StatsBomb event construction.

## E. Covariates
- [x] **(P1)** **Betting odds sourced & joined**: football-data.co.uk 2015/16 big-5; 1,823/1,823 matches matched (1 patched with Pinnacle). `data/odds/odds_big5_1516.csv` incl. de-vigged `odds_p_home`/`odds_p_draw`.
- [x] **(P2)** **Player age/experience covariate** (done 2026-07-21): `data/player_covariates_big5.parquet` — **age** from Wikidata DOB (label/alias/search + footballer + birth-year plausibility + club-membership validation, QID kept; 99.89% row coverage, 6 fringe players NA) and **starter_share** = cumulative starts ÷ team matchday from StatsBomb lineups (100%; treated 0.66 vs control 0.58). `data/lineups_big5.parquet` fetched for all 1,823 matches (also feeds C's substitution descriptives). REVISED 2026-07-22: **starter_share removed** (code + artifacts deleted); **betting odds dropped from the analysis** (data + build script kept in repo for possible return); **age extended to the full male sample** via era-aware Wikidata rounds — `data/player_dob.parquet` now 7,079 players, 98.6% male-row coverage (`data/lineups_male.parquet` fetched for all 2,924 male matches). Age enters **W as confounder**; tested as moderator -> null (q=.98).
- [ ] **(P3)** Elo, player market values — **not pursued** for now (explicitly out of scope).

## F. Publication strategy (two papers)
- [ ] **(P1)** **Paper 1 ("yellow cards")** → JQAS. This backlog covers Paper 1.
- [ ] **(P3)** **Paper 2 (methods-forward, Call for Causal ML)** → Journal of Sports Analytics; *different* treatment (X) and outcome (Y). Park as a separate future track — not part of Paper 1's critical path.

## G. Manuscript production (JQAS)
- [ ] **(P2)** Expand full DML exposition (orthogonality, cross-fitting, match-clustered inference).
- [ ] **(P2)** Heterogeneity θ(Z) with validation battery (BLP / GATES / calibration).
- [ ] **(P2)** Robustness: placebo/pre-window checks, treatment-definition sensitivity ([15′,45′]).
- [ ] **(P3)** Prepare reproducibility repo (code + StatsBomb data pointers) for JQAS submission.

---

### Suggested critical path (next up)
1. **E → B**: get betting odds, then settle the data filter (the two are coupled).
2. **C**: build the multi-window + booking/substitution descriptives pipeline.
3. **D**: assemble the extended outcome set.
4. **A / G**: reframe narrative and expand methods once the empirics are refreshed.
