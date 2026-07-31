# Yellow-Card Paper — Project Backlog

**Source:** Co-author meeting 2026-07-14. **Primary target:** Journal of Quantitative Analysis in Sports (JQAS).
**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · **(P1/P2/P3)** priority.
Completed items are removed from this list; the full record of decisions and results is in the git history of this file.

---

## A. Story & framing
- [ ] **(P1)** Write §2 Related work (three strands: cards→team outcomes; suspension/deterrence between matches; cards as referee decisions; gap = within-match player-level response). No causal-ML-in-sports strand; no "Foul Play" (cards are outcome there, not treatment).
- [ ] **(P2)** Write abstract (~200 words) + §1 Introduction (lead with the football/behaviour question; three margins: booked players withdrawn 2.7x more often [non-causal phrasing], player fouls −26.5%, teammates +4.5% fouls / +3.6% recoveries) + keywords (3–6, not in title).
- [ ] **(P1)** Write §6 Discussion and conclusion (was §7 before the §6→5.4 fold).
- [ ] **(P2)** At submission: attach the cut full-outcome tables (HTE coefficients, null-outcome bounds) as online supplementary material (Table S1 etc.) to reconcile the significant-findings focus with the completeness rule.

## D. Outcomes / targets
- [~] **(P1)** **TAXONOMY (Oliver, 2026-07-30): opponent-directed (pressures, tackles, fouls; sanction risk) vs ball-directed (recoveries, clearances, blocks, interceptions; no sanction path) — category aggregates replace the 7-component grand total (NOT shown).** Chain + manuscript DONE (2026-07-30 evening, manuscript 6ca1251, 29 pp, clean): headline contrast opponent-directed −6.1%*** (windows −6.4..−8.1%) vs ball-directed −0.6% p=.73 (windows null); §3.3 taxonomy + ex-ante prediction; two-panel tables (DML, spillover, learner); 5x2 window figure; §5.4 numbers re-based (ladder −0.212..−0.237; RV 2.1/1.1; benchmark 2.7/<0.1; binary opp bounds excl. zero at 45-50). OPEN: Oliver reviews the taxonomy version.
- [x] (superseded by the taxonomy) **Extended outcome set — DONE except final sign-off:** defensive-actions aggregate (7 components) is the headline throughout; adverse events removed; full 8-outcome sweep ran through every analysis; exhibits since focused on the 3 significant outcomes with salience bolding (full record in this file's git history and docs/paper_plan_jqas.md). OPEN: Oliver's final sign-off on the integrated version, then the conditional cleanup below.
- [ ] **(P2)** **Conditional on adopting the new analysis (Oliver, 2026-07-29):** drop the frame's original 3-component aggregate column `post_n_def_events` (notebook 02 + `analysis_frame.csv` rebuild; `build_male_dml.load()` then sums `post_n_def_actions` from the component columns instead of extending the old aggregate).

## G. Manuscript production (JQAS)
- [ ] **(P2)** Page budget — CHECKED (2026-07-29, local guideline PDFs + current degruyterbrill.com instructions, last update 2025-03-03): the only length statement is "Typical JQAS manuscripts are 20–30 pages long. Longer papers are discouraged" (soft guideline, in the manuscript-preparation PDF; the current Instructions for Authors state NO page/word limit; abstract max 250 words). Appendices sit inside the manuscript before the references; no counting rule stated — safest reading: they count. Supplementary material is explicitly supported: online-only, separate files ≤10 MB, not typeset, cited as "Figure S1/Table S1"; it does NOT count toward the article PDF. Decision for Oliver: manuscript is 30 pp with §1/§2/§6 still to write (~7–9 pp) → likely ~37 pp total; move appendices (and the cut full-outcome tables, see item A) to supplementary material to land near 30.
- [ ] **(P2)** De-identification pass for blind review (acknowledgements, repo links, self-references).
- [ ] **(P3)** Prepare reproducibility repo (code + StatsBomb data pointers) for JQAS submission.
- [ ] **(P3)** Sync slide deck (`documents/slides_paper.pptx`) to the canonical Spec-B numbers.
- [ ] **(P3)** JQAS submission mechanics: figures as separate EPS/TIF/JPG ≥300 dpi, ScholarOne upload, keywords check.

---

### Suggested critical path (next up, status 2026-07-30)
1. **A**: write §2 Related work, then §1 Introduction, then §6 Discussion + abstract/keywords.
2. **D**: final sign-off on the extended-outcome integration; then drop the frame's old 3-component column.
3. **G**: supplementary-material packaging (cut tables + appendices); de-identification; slide-deck sync; submission mechanics.
