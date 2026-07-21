# Yellow-Card Paper — Project Backlog

**Source:** Co-author meeting 2026-07-14. **Primary target:** Journal of Quantitative Analysis in Sports (JQAS).
**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · **(P1/P2/P3)** priority.

---

## A. Story & framing
- [ ] **(P1)** Reframe the paper so the **"yellow cards" research question is the headline**; causal ML is presented as *method*, not contribution.
- [ ] **(P2)** Rewrite abstract + intro to lead with the football/behaviour question; move DML machinery to the methods section.

## B. Data scope & filtering
- [x] **(P1)** Stay on **StatsBomb open data** (decided). Do *not* introduce new event sources.
- [x] **(P1)** Evaluate a **narrower filter** — **built: men + domestic league + complete seasons = big-5 2015/16** (`data/analysis_frame_big5.csv`, 41,176 player-matches / 1,823 matches / 1,948 treated, 4.73%). Drops single-club partial seasons (Barça, Invincibles, Leverkusen…). ISL 2021/22 excluded (no odds coverage) — confirm with co-authors.
- [ ] **(P2)** Document the final sample definition + inclusion/exclusion counts for the paper.

## C. Survival bias / outcome window
- [ ] **(P1)** Replace the "played first 60'" restriction with a **multi-window analysis**: 30–45, 45–50, 45–60, 45–70, 45–80.
- [ ] **(P1)** Compute **descriptive statistics on bookings and substitutions** (timing, rates, how many booked players are censored per window) to characterise the censoring transparently.
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
