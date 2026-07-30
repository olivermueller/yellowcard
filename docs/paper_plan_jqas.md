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

## Style (Oliver, 2026-07-23): write in JQAS language
Register of a sports-statistics journal, not an econometrics one: sports-analytics
terminology first (booking/caution, match, fixture, fouls conceded), statistical methods
described plainly; econometric machinery (Neyman orthogonality, estimands, partial
interference) introduced gently and defined on first use; magnitudes in football terms.
Model exemplars: recent JQAS articles (e.g., Anders & Rotthoff 2011; Wu et al. 2021).

## Framing (per backlog A + co-author meeting)

Title direction: lead with the question, not the method — e.g.
*"Does a yellow card change how a player defends? Causal evidence from 3,000 bookings"*.
Causal ML appears as the method that answers the football question. The MLSA methods-showcase
framing ("we invite the community to adopt causal ML") moves to a short discussion paragraph.

## Structure and page budget (≈28 double-spaced pages)

1. **Introduction (≈4 pp).** The half-time dilemma; deterrence hypothesis; preview of the
   three-margin answer: coaches withdraw booked players ~2.7× more often at half-time, surviving players cut
   fouls ~26% (tackling untouched), teammates partially compensate (+4.5%). One paragraph on why
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
   - StatsBomb open data; **canonical sample (Spec B)**: male, five European domestic leagues,
     outfield lineup-verified starters, no H1 exit, on pitch through the outcome window;
     age (Wikidata) + betting odds (football-data) in W — the filter is justified by
     covariate coverage; 43,527 player-matches, 2,650 treated.
   - **Attrition/eligibility table** (backlog B-P2): from raw player-matches to the analysis
     sample, step by step (lineup-verified starters, no H1 exit, on pitch through the window).
   - Windows: pre [0,15) → treatment [15,45] → outcomes 45–b for b ∈ {50,60,70,80};
     Table 1 (variable families) updated with age (Wikidata DOB, 98.6% coverage).
   - Descriptives: booking/substitution timing histograms; **censoring table** (withdrawal
     4.0% vs 1.48% at HT (~2.7x); per-window trims 2.5–10.4%).
4. **Methods (≈4.5 pp).** Partial-linear DML (expanded per backlog G: orthogonality,
   cross-fitting, GroupKFold by match, clustered inference); subgroup CATEs + BH; **selection
   into observation and Lee bounds**: estimand = effect among always-on-pitch players;
   cell-based conditional trimming (position × pre-activity); binarized-outcome bounds;
   Imbens–Manski CIs. Cite Lee (2009), Semenova (better Lee bounds), Imbens–Manski (2004),
   Hudgens–Halloran (partial interference).
5. **Results (≈7 pp).**
   - **Main effects:** descriptive treated-vs-control differences (raw means per DV), then
     the DML estimates: fouls −26.5%***, def. engagement −6.1%***, pressures −4.9%***,
     tackles null (−0.2%, p=.96). (No estimator ladder — DML is the single estimator.)
   - **Coach response:** booking ×2.4 HT withdrawal — the extensive margin (own result).
   - **Multi-window (durability):** fouls −24.8…−29.4% stable 45′→80′; onset at full strength
     45–50′ (−28.1%); 30–45′ contamination check (+13.9%) motivates the H2 design.
   - **Heterogeneity:** game state (q=.012) and position (q=.005) moderate; age tested, null.
   - **Teammate spillover (third margin):** +4.5% fouls (p=.023) for non-carded teammates;
     direct effect vs unexposed controls −23.1%*** (robustness; mixture ATE stays primary).
6. **Robustness and identification (≈3.5 pp).** Rewritten §3.4 on canonical numbers:
   positivity ê∈[0.010, 0.284], ATE invariant to trimming; Cinelli–Hazlett RV 2.06%; SUTVA
   re-centred on the measured spillover + caveats (opponent-side untested; match-heat upper
   bound); **Lee-bounds table** (count + binary, IM CIs): at the 45–50′ anchor ALL binary
   point-identification bounds exclude zero incl. P(any foul) [−2.85, −0.13]pp; P(any foul)
   zero-excluded WITH Imbens–Manski 95% CIs at 45–70′ and 45–80′; plausibility figure
   (withdrawn players are below-average activity types). Odds are IN W by design (no
   separate odds-robustness needed; note Spec-A comparison available).
7. **Discussion & conclusion (≈2.5 pp).** Selective caution as deterrence; implications for
   the substitution decision (early substitution often unnecessary; teammate compensation as a
   hidden cost); limitations (15–35′ windows, open-data scope, always-on-pitch estimand);
   future work (fine-grained outcomes = backlog D, Paper 2 pointer).

**Figures (separate files, regenerate at ≥300 dpi):** F1 DAG · F2 timing histograms ·
F3 multi-window effect profile with bounds (new — the money figure) · F4 subgroup ATEs ·
F5 plausibility (withdrawn vs survivors). Tables: T1 variables · T2 attrition · T3 descriptives +
main DML effects · T4 multi-window + Lee/IM bounds · T5 spillover.

## Status (2026-07-30)

Polish round on Oliver's read (all pushed, manuscript d704b75, 30 pp, clean compile):
- Oliver's Overleaf edits pulled (§3 restructured: selection paragraph folded into §3.2,
  old §3.5 deleted; subsection retitles; §4.3 opening reworded to "latent groups");
  3 dangling refs to sec:data:selection retargeted; one grammar slip fixed.
- **Salience:** significant estimates BOLD in Tables 3–6 (criterion noted per caption:
  5%-level for Tables 3–5; IM interval excluding zero for Table 6). Figure 3 markers now
  mirror Figure 4's convention (filled = significant at 5%, open = not; legend above the
  panels after an overlap fix).
- **Table 6 headers:** "DML estimate | Identification bounds (Lee) | 95% CI
  (Imbens–Manski)"; caption explains that each IM interval contains its bounds
  (single CI for the partially identified effect, one-sided extensions, c≈1.645);
  table in footnotesize.
- Lee-bounds intuition also delivered to Oliver in chat (two sieves / count-how-many /
  worst-case deletion / count-width arithmetic) and woven into §4.3.

## Status (2026-07-29, evening)

Major restructuring round (Oliver's decisions), manuscript at 31 pp, compiles clean:
- **Focus on significant findings:** §5.2 heterogeneity, §5.4 robustness, and the bounds
  exhibits are RESTRICTED to the three outcomes with significant effects (defensive-actions
  aggregate, pressures, fouls); each section opens with the focus statement and rationale;
  null-outcome results referenced to the replication package. Appendix A (complete HTE
  coefficient tables) CUT; §5.2 carries the three outcomes' numbers in-text; HTE code
  restricted to the three outcomes. RECOMMENDATION on file: attach the cut tables as
  online supplementary material at submission (uncounted, citable as Table S1) to square
  the restriction with the completeness rule.
- **§6 folded into §5** as subsection 5.4 "Assumption tests and robustness checks"
  (positivity/sensitivity/interference/selection now subsubsections); Discussion is §6;
  classic 6-section structure. Labels kept, refs resolve.
- **Bounds prominence swapped:** new binarized-bounds figure (estimates + identification
  bands + IM whiskers, `src/build_bounds_binary_figure.py`) is the §5.4.4 exhibit; the
  count-bounds figure moved to an appendix (wide-by-construction explanation); both now
  1x3 panels. Plain outcome labels (no P(any foul) notation) — the at-least-one-action
  reading lives in captions.
- **§4.3 carries the accessible Lee-bounds exposition** (two sieves, unseen labels,
  count-how-many trick, worst-case deletion, count-width arithmetic).
- **§5.1 rewritten around the raw foul sign reversal** (pre-window +37.4% vs post −21%;
  selection favours the opposite sign → raw diff understates the causal reduction);
  Table 3 split into raw-means-with-tests + DML tables.
- **Full 8-outcome sweep** ran through every analysis before the restriction; all CSVs in
  the repo carry the complete set (supplementary-material source). New spillover finding
  reported in §5.3: teammate ball recoveries +3.6% (p=.002).
- All tables fit page margins (zero overfull boxes).

## Status (2026-07-28, evening)

- **Timing-placebo analysis REMOVED from the manuscript (Oliver's decision)** after the
  full debate cycle (raw placebos → mechanical-channel objection → card-source
  decomposition → circularity/upper-bound caveat). §6.2 paragraph, Appendix C placebo
  subsection, and both placebo tables cut; cross-references in §4.1 and the appendix intro
  adjusted. The analysis remains in the yellowcard repo (`src/build_placebo_timing.py`,
  `data/placebo_timing.csv`) for possible reviewer responses.
- **Oliver's end-to-end read notes addressed:** pre-window selection numbers added to §5.1
  (booked players: +12.9% pre-window defensive actions, +37.4% pre-window fouls); forwards
  heterogeneity estimate explicitly non-significant (p=.057); overlap figure moved to
  Appendix C; §6.2 condensed to text-only (Cinelli–Hazlett contour figure deleted from
  manuscript AND its build code removed from `build_robustness_figures.py`); §6.3 collapsed
  to one paragraph (numbers defer to §5.3); §6.4 opening deduplicated against §5.1.
- Oliver's own edits: complete-seasons robustness sentence commented out in §3.1; §3.2
  tightened.
- **Float placement fixed:** `placeins` with section barriers; `[t]` → `[htbp]`.
- Manuscript compiles clean at 28 double-spaced pages; §1/§2/§7 + abstract still open.

## Status (2026-07-28)

- **Placebo decomposition (Oliver's objection: activity also CAUSES bookings, so zero is
  the wrong benchmark):** split by booking reason — bad-behaviour-card placebo (mechanical
  channel off, 477 treated) NULL for engagement/pressures/tackles (all p≥.19), POSITIVE for
  fouls (+23.9%, p=.017); foul-card placebo (2,513 treated, identical sample) positive
  throughout. Appendix C + §6.2 rewritten: activity-outcome identification supported; foul
  effect signed conservative. Review item for Oliver remains in the backlog.
- **Writing style rules adopted (Oliver):** topic-sentence paragraphs (one idea each),
  active first-person voice, past tense for data/analysis descriptions and literature
  review, present tense for findings/implications/intro; econometrics vocabulary allowed
  (JQAS = statistical journal). Style-conformance pass over §3–§6 + appendices DONE
  (commit 3516506); §3.1 split into three topic-sentence paragraphs; appendix headings
  dried ("Evaluation of the estimation procedure", "Out-of-sample nuisance diagnostics",
  "Sensitivity to estimation choices", "Timing placebo analysis").
- Manuscript compiles clean at 31 double-spaced pages; §1/§2/§7 + abstract still open.
- Backlog trimmed on Oliver's instruction: treatment-definition-sensitivity item and
  section F (publication strategy) removed.

## Status (2026-07-27)

Since 2026-07-24: completeness rule implemented (full 4x5 binary-bounds table, spillover
table both panels, appendix table of all joint-moderator coefficients, both window figures
2x2 with all four outcomes). Backlog trimmed to open items (completed items live in its git
history); Paper-2 track removed from the backlog (separate future project).

**Machinery-evaluation appendix DONE (2026-07-27, Appendix C, both repos pushed):**
- Exhibit a, nuisance diagnostics: e(W) AUC 0.567, Brier 0.0571 vs base-rate 0.0572,
  decile calibration figure (`fig_calibration.png`); m(W) out-of-fold R2 0.151/0.169/0.023/0.011.
- Exhibit b, insensitivity: learner swap (HGB baseline/deeper, random forest, logit+ridge)
  moves the foul ATE only within [-0.070, -0.069]; 20-replication seed+fold spread an order
  of magnitude below the sampling SEs; residual-balance joint F(62)=1.23, p=.11.
- Exhibit c, timing placebos (two designs): BOTH reject zero on all four outcomes with
  POSITIVE sign (within-half 60-75 on 45-60: fouls +21.9%***; cross-interval 45-60 on H1 30+:
  fouls +26.6%*** — the half-time interval does not remove the selection signal). Framing in
  Appendix C + section 6.2: placebos sign the residual selection; positive selection biases
  the contrast toward zero, so the reported reductions are understatements (consistent with
  raw -21% vs DML -26.5% and the Cinelli-Hazlett direction argument). OLIVER TO REVIEW this
  framing and whether section 4.1's "as good as random" needs softening.
- Covariate count corrected to 62 (was 61) in sections 4.1/6.2.
- Manuscript now 30 double-spaced pages with sections 1/2/7 still to write — check whether
  JQAS counts appendices toward the 20-30 guideline (backlog item).
- Scripts: `src/build_placebo_timing.py`, `src/build_nuisance_eval.py`,
  `src/build_insensitivity.py`; results in `data/placebo_timing.csv`,
  `data/nuisance_metrics.csv`, `data/insensitivity_{learners,seeds,balance}.csv`.
- Decided (chat, 2026-07-27): no fit statistics for the final-stage regression — it is a
  method-of-moments step whose R2 is bounded by the effect size and would be near zero even
  under randomization; quality is assessed via SEs, residual orthogonality, and placebos.

Remaining: section 2 Related work, section 1 Introduction, section 7 Discussion, abstract +
keywords; placebo-framing review; treatment-definition sensitivity ([15,45]); keep/drop
decision on extended outcomes; de-identification; Chicago bib for section-2 references;
deck sync; page-budget check.

## Status (2026-07-23, end of day)

Written and pushed: Sections 3-6 complete (compiled clean), all figures/tables placed.
- Section 3 Data and design: source + single-club caveat (with inline complete-seasons check), attrition table, windows [45,b], b in {50,60,70,80,90}, variables (Z = position5, score state, age, win probability; venue W-only), selection descriptives; timing appendix (interval subs separated, outfield only, common y-limits).
- Section 4: Identification and estimation strategy (merged) / Quantifying heterogeneous treatment effects / Accounting for selection bias. Design + DAG figures integrated (updated drawio exports).
- Section 5: Main effects across outcome windows (raw means + DML table; five-window profile figure, no bounds; substitution finding folded in; full-half tackle note) / Effect heterogeneity (2x2 figure incl. win-probability null; forwards now marginal p=.057) / Spillover effects. 30-45 placebo REMOVED (window dropped from analysis).
- Section 6 (renamed: Identification assumptions and robustness): expanded, sober register; overlap figure + trimming ladder; sensitivity contour figure (RV 2.1%/1.1%); interference; selection bounds (count-bounds figure + binary bounds table incl. 45-90; P(any foul) zero-excluded at all five windows, IM CIs at the three longest). No sample-composition subsection (folded into 3.1).
- Register rules: no narrative tone (twice corrected), no "caution", player vs player-match precision.

Remaining: Section 2 Related work, Section 1 Introduction, Section 7 Discussion, abstract + keywords; machinery-evaluation appendix (3 exhibits, timing placebo first — see backlog G); de-identification pass; Chicago bib conversion for related-work citations; deck sync.

## Work plan

1. [x] **DONE 2026-07-23:** repo `olivermueller/jqas-yellowcard-paper` (private) — double-spaced
       `article` skeleton with per-section content notes, natbib+chicago.bst, compiles clean;
       MLSA tex + this plan in `source_material/`.
2. [ ] Port + rewrite section by section per the structure above (order: 3 → 5 → 6 → 4 → 2 → 1 → 7).
3. [ ] Regenerate all figures from canonical scripts (300 dpi, separate files, sans-serif).
4. [x] **DONE 2026-07-24:** T2 attrition table (`src/build_attrition_table.py`; closed backlog B-P2).
5. [ ] De-identify (authors, acknowledgements, repo URL → anonymized archive link).
6. [ ] Convert references to Chicago author-date; add Lee/Semenova/Imbens–Manski/Hudgens–Halloran.
7. [ ] Internal pass vs the 20–30-page budget; co-author round; ScholarOne submission.

**Open questions for co-authors:** (a) title; (b) keep 45–60′ or
45–50′ as the headline window in the abstract (recommend 45–60′ with 45–50′ as onset evidence).
