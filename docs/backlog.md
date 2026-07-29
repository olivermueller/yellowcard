# Yellow-Card Paper — Project Backlog

**Source:** Co-author meeting 2026-07-14. **Primary target:** Journal of Quantitative Analysis in Sports (JQAS).
**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · **(P1/P2/P3)** priority.
Completed items are removed from this list; the full record of decisions and results is in the git history of this file.

---

## A. Story & framing
- [ ] **(P1)** Write §2 Related work (three strands: cards→team outcomes; suspension/deterrence between matches; cards as referee decisions; gap = within-match player-level response). No causal-ML-in-sports strand; no "Foul Play" (cards are outcome there, not treatment).
- [ ] **(P2)** Write abstract (~200 words) + §1 Introduction (lead with the football/behaviour question; three margins: coach withdrawal 2.7x, player fouls −26.5%, teammates +4.5%) + keywords (3–6, not in title).
- [ ] **(P1)** Write §7 Discussion and conclusion.

## D. Outcomes / targets
- [~] **(P1)** **Extended outcome set — INTEGRATED (2026-07-29, latest manuscript commit 8c430c2):** headline aggregate = 7-component defensive actions (−4.3%*** primary; −4.4..−5.5% across windows; heterogeneity null p=.56; direct effect −4.1%***; RV 1.8/0.9%; ladder −0.219..−0.231; Appendix A/C + binary-bounds rows refreshed). **ADVERSE EVENTS FAMILY REMOVED from text and code (Oliver, 2026-07-29)** — exploration recoverable from git history. Table 3 SPLIT: raw-means table with match-clustered difference tests (`src/build_raw_diffs.py`) + DML table. **Window analysis mirrors the primary analysis**: aggregate + all 7 components × 5 windows (18/20 ball-winning cells null; blocks 45-50 −11.6% p=.029 and clearances 45-90 +5.1% p=.054 flagged as chance-compatible); 8-panel window figure. 29 pp. OPEN: Oliver reviews; then the conditional cleanup below. Family 1 = defensive family extended by ball recoveries, clearances, blocks, interceptions (added to pressures/tackles/fouls); Family 2 (new) = miscontrols, dispossessions, times dribbled past. Family names SETTLED (Oliver): **"defensive actions"** / **"adverse events"**. Rate-based targets DROPPED (post-treatment denominator selection). Literal StatsBomb "Error" event unusable (defined as mistake leading to a shot; 0.003/player-match). Estimation on the primary window done (`src/build_outcome_families.py` → `data/outcome_families.csv`); full-chain re-run on the new aggregate in progress; manuscript integration next.
- [ ] **(P2)** **Conditional on adopting the new analysis (Oliver, 2026-07-29):** drop the frame's original 3-component aggregate column `post_n_def_events` (notebook 02 + `analysis_frame.csv` rebuild; `build_male_dml.load()` then sums `post_n_def_actions` from the component columns instead of extending the old aggregate).

## G. Manuscript production (JQAS)
- [ ] **(P2)** Page budget — CHECKED (2026-07-29, local guideline PDFs + current degruyterbrill.com instructions, last update 2025-03-03): the only length statement is "Typical JQAS manuscripts are 20–30 pages long. Longer papers are discouraged" (soft guideline, in the manuscript-preparation PDF; the current Instructions for Authors state NO page/word limit; abstract max 250 words). Appendices sit inside the manuscript before the references; no counting rule stated — safest reading: they count. Supplementary material is explicitly supported: online-only, separate files ≤10 MB, not typeset, cited as "Figure S1/Table S1"; it does NOT count toward the article PDF. Decision for Oliver: manuscript is 28 pp with §1/§2/§7 still to write (~7–9 pp) → likely ~35 pp total; move Appendices A–C (or a subset) to supplementary material to land near 30.
- [ ] **(P2)** De-identification pass for blind review (acknowledgements, repo links, self-references).
- [ ] **(P3)** Prepare reproducibility repo (code + StatsBomb data pointers) for JQAS submission.
- [ ] **(P3)** Sync slide deck (`documents/slides_paper.pptx`) to the canonical Spec-B numbers.
- [ ] **(P3)** JQAS submission mechanics: figures as separate EPS/TIF/JPG ≥300 dpi, ScholarOne upload, keywords check.

---

### Suggested critical path (next up, status 2026-07-28)
1. **A**: write §2 Related work, then §1 Introduction, then §7 Discussion + abstract/keywords.
2. **D**: decide keep/drop for the extended outcome set (fine-grained actions, error events, rates).
3. **G**: page-budget check; de-identification pass; slide-deck sync; submission mechanics.
