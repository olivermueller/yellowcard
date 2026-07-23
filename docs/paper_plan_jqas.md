# JQAS Paper Plan — "Yellow Cards" (Paper 1)

**Created:** 2026-07-23 · **Target:** Journal of Quantitative Analysis in Sports (De Gruyter)
**Source manuscript:** `olivermueller/mlsa26-yellowcard-paper` (MLSA26 submission backed up:
`backup/` + git tag `mlsa26-submission`).

## Journal requirements (from JQAS manuscript-preparation guidelines + instructions)

- **Submission:** ScholarOne — http://mc.manuscriptcentral.com/dgjqas. Word or PDF; if LaTeX,
  submit the LaTeX source too.
- **Length: 20–30 pages typical, longer discouraged** — double-spaced (~26 lines/page),
  8.5×11", 1" margins, single column, 11–12 pt ⇒ roughly 6,500–9,000 words incl. tables.
- **Blind review: manuscript must be de-identified** (strip authors, affiliations, repo URL —
  the GitHub footnote in the MLSA version must go or be anonymized).
- Abstract ≈ 200 words; 3–6 keywords *not appearing in the title*.
- **Chicago author-date** citations (MLSA used Springer numeric — full bibliography conversion).
- Figures in **separate files** (EPS/TIF/JPG, ≥300 dpi), not embedded; color free of charge.
  Tables as text (never images), placed near first reference. Footnotes sparingly.
- **Template:** the old De Gruyter template link in the guidelines is dead; the current
  incarnation is the Overleaf "Manuscript Template for Walter de Gruyter Books and Journals"
  (`dgruyter.sty`). NOTE: the template is *optional* for submission — double-spaced plain
  `article` class satisfies every stated requirement (the guidelines even say the DG template's
  spacing must be changed). **Decision: write in plain `article` (12 pt, `setspace` double,
  `natbib` + Chicago author-date), convert to DG layout only if requested at production.**

## Framing (per backlog A + co-author meeting)

Title direction: lead with the question, not the method — e.g.
*"Does a yellow card change how a player defends? Causal evidence from 3,000 bookings"*.
Causal ML appears as the method that answers the football question. The MLSA methods-showcase
framing ("we invite the community to adopt causal ML") moves to a short discussion paragraph.

## Structure and page budget (≈28 double-spaced pages)

1. **Introduction (≈4 pp).** The half-time dilemma; deterrence hypothesis; preview of the
   three-margin answer: coaches withdraw booked players ~2.4× more often, surviving players cut
   fouls ~25% (tackling untouched), teammates partially compensate (+5%). One paragraph on why
   observational causal inference is required.
2. **Related work (≈3 pp).** Three strands, all *between-match or team-level* — none
   estimates the in-game, player-level effect of a booking:
   - **Cards and team outcomes:** Ridder, Cramer & Hopstaken (1994, JASA) and the red-card
     literature (Cerveny, van Ours & van Tuijl 2018, Empirical Economics; Bar-Eli et al.;
     Lago-Penas et al. 2016) on dismissals and team performance; Anders & Rotthoff (2011,
     JQAS — home turf) on yellow/red cards and win probability; "Influence of red and yellow
     cards on team performance in elite soccer" (Annals of OR, 2023).
   - **Suspension deterrence ACROSS matches:** VanDerwerken, Rothert & Nguelifack (2018,
     J. Sports Economics — 12-23% foul reduction when one card from suspension); strategic
     "suspension by choice" (fifth-yellow timing); fouling-incentive studies (Deutscher et
     al. 2013).
   - **Cards as referee decisions:** referee bias/consistency literature (Buraimo, Forrest &
     Simmons; "Yellow fever", JRSS-A 2025; Unkelbach & Memmert) — cards as outcomes, not
     treatments.
   **Gap statement:** existing causal work studies *between-match* deterrence (suspension
   threat) or *team-level* consequences; we estimate the **within-match, player-level causal
   effect of a booking on the booked player's own subsequent behaviour** — the margin the
   half-time substitution decision actually turns on. (Verify/complete citations while
   writing; candidates flagged above.)
3. **Data and design (≈5 pp).**
   - StatsBomb open data; **canonical sample**: male, outfield **lineup-verified starters**, no
     H1 exit, on pitch through the outcome window; ~52k player-matches, ~3.0k treated.
   - **Attrition/eligibility table** (backlog B-P2): from raw player-matches to the analysis
     sample, step by step (lineup-verified starters, no H1 exit, on pitch through the window).
   - Windows: pre [0,15) → treatment [15,45] → outcomes 45–b for b ∈ {50,60,70,80};
     Table 1 (variable families) updated with age (Wikidata DOB, 98.6% coverage).
   - Descriptives: booking/substitution timing histograms; **censoring table** (withdrawal
     4.8% vs 1.96% at HT; per-window trims 3.2–11.6%).
4. **Methods (≈4.5 pp).** Partial-linear DML (expanded per backlog G: orthogonality,
   cross-fitting, GroupKFold by match, clustered inference); subgroup CATEs + BH; **selection
   into observation and Lee bounds**: estimand = effect among always-on-pitch players;
   cell-based conditional trimming (position × pre-activity); binarized-outcome bounds;
   Imbens–Manski CIs. Cite Lee (2009), Semenova (better Lee bounds), Imbens–Manski (2004),
   Hudgens–Halloran (partial interference).
5. **Results (≈7 pp).**
   - **Main effects:** descriptive treated-vs-control differences (raw means per DV), then
     the DML estimates: fouls −25.6%***, def. engagement −5.7%***, pressures −4.3%**,
     tackles null. (No naive-OLS / OLS+W estimator ladder — DML is the single estimator.)
   - **Coach response:** booking ×2.4 HT withdrawal — the extensive margin (own result).
   - **Multi-window (durability):** fouls −23…−27% stable 45′→80′; immediate onset at 45–50′;
     30–45′ contamination check motivates the H2 design.
   - **Heterogeneity:** game state (q=.012) and position (q=.005) moderate; age tested, null.
   - **Teammate spillover (third margin):** +5.4% fouls (p=.0035) for non-carded teammates;
     direct effect vs unexposed controls −22.6%*** (robustness; mixture ATE stays primary).
6. **Robustness and identification (≈3.5 pp).** Rewritten §3.4 on canonical numbers:
   positivity ê∈[0.020, 0.159], ATE invariant to trimming; Cinelli–Hazlett RV 1.80% ≈ 6× the
   strongest observed benchmark; SUTVA discussion re-centred on the measured spillover +
   caveats (opponent-side untested; match-heat upper bound); **Lee-bounds table** (count +
   binary, IM CIs) + plausibility figure (withdrawn players are below-average activity types);
   betting-odds robustness sentence (evaluated on league subsample; estimates unchanged).
7. **Discussion & conclusion (≈2.5 pp).** Selective caution as deterrence; implications for
   the substitution decision (early substitution often unnecessary; teammate compensation as a
   hidden cost); limitations (15–35′ windows, open-data scope, always-on-pitch estimand);
   future work (fine-grained outcomes = backlog D, Paper 2 pointer).

**Figures (separate files, regenerate at ≥300 dpi):** F1 DAG · F2 timing histograms ·
F3 multi-window effect profile with bounds (new — the money figure) · F4 subgroup ATEs ·
F5 plausibility (withdrawn vs survivors). Tables: T1 variables · T2 attrition · T3 descriptives +
main DML effects · T4 multi-window + Lee/IM bounds · T5 spillover.

## Work plan

1. [ ] New repo/Overleaf project `jqas-yellowcard-paper` seeded from the MLSA backup;
       plain `article` double-spaced skeleton; Chicago author-date via natbib.
2. [ ] Port + rewrite section by section per the structure above (order: 3 → 5 → 6 → 4 → 2 → 1 → 7).
3. [ ] Regenerate all figures from canonical scripts (300 dpi, separate files, sans-serif).
4. [ ] Build T2 attrition table (small script; also closes backlog B-P2).
5. [ ] De-identify (authors, acknowledgements, repo URL → anonymized archive link).
6. [ ] Convert references to Chicago author-date; add Lee/Semenova/Imbens–Manski/Hudgens–Halloran.
7. [ ] Internal pass vs the 20–30-page budget; co-author round; ScholarOne submission.

**Open questions for co-authors:** (a) title; (b) keep 45–60′ or
45–50′ as the headline window in the abstract (recommend 45–60′ with 45–50′ as onset evidence).
