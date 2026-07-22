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
- [ ] **(P1)** Replace the "played first 60'" restriction with a **multi-window analysis**: 30–45, 45–50, 45–60, 45–70, 45–80.
- [x] **(P1)** **Booking/substitution descriptives + censoring table** (done 2026-07-21): `src/build_desc_minutes.py` (minute histograms overall + per position; 7,872 yellows 4.32/match rising through the game, Defenders most-booked/least-subbed; 10,473 subs 5.74/match, 7.2% at HT, median 71') and `src/build_censoring_table.py` (`data/censoring_by_window.csv`). **Key: booked players withdrawn at HT 3.5% vs 1.78% for comparable controls (~2x, robust to position x starter-share adjustment). Lee trims: 45-50 2.4%, 45-60 5.5%, 45-70 8.9%, 45-80 11.4%** — quantifies the window bias-signal trade-off; plan = effects per window + Lee bounds.
- [ ] **(P1)** **DECIDED 2026-07-21:** report the coach-response finding — *a first-half booking nearly doubles the probability of being withdrawn at half-time* (3.5% vs 1.78%) — as a result in its own right (extensive margin: coach substitutes; intensive margin: surviving players adapt).
- [x] **(P1)** Lee bounds v1 (blunt, unconditional trim + DML re-run) implemented in `src/build_male_dml.py` — male-sample trim 6.4% (treated 11.9% vs position-adj control 5.9% censored by 60'). Lower bounds tight (approx. -6.5% def_eng); **upper bounds cross zero — artifact of unconditional trimming on right-skewed counts**, not evidence of fragility.
- [x] **(P1)** **Conditional Lee bounds run (2026-07-22)** — `src/build_lee_conditional.py` (cell-based: position x pre-activity tercile; per-cell trims 2.0-10.9%), `data/male_dml_lee_conditional.csv`. Upper bounds tightened ~25% vs blunt (def_eng +17.7% -> +13.0%) **but still cross zero — at ~6% censoring, worst-case trimming bounds cannot certify the 45-60' effect on their own**. Cite Lee (2009) + Semenova (better Lee bounds); estimand = effect among always-on-pitch players.
- [ ] **(P1)** **Bounds strategy for the paper (NEW):** (a) use the **multi-window design as the bound-tightening device** — 45-50' trim is only ~2.4%, so bounds there should be informative; anchor the effect at 45-50', then wider windows add signal under weaker worst-case guarantees; (b) add a **plausibility figure**: compare H1 profiles of actually-withdrawn booked players vs control survivors — if the withdrawn are not extreme-tail types in observables, the worst-case allocation loses bite.
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
