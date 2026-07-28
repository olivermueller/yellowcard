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
- [ ] **(P1)** Add **fine-grained defensive actions** (decompose the aggregate). *Status: manuscript currently uses the 4-outcome set; decide whether the decomposition goes into a revision round or is dropped.*
- [ ] **(P1)** Add **"error" events** — dispossessed, unforced errors, miscontrols, etc. *Status: not in the current manuscript; decide keep/drop.*
- [ ] **(P2)** Add **rate-based targets** (e.g., duel/tackle win rate) alongside raw counts. *Status: not in the current manuscript; decide keep/drop.*

## G. Manuscript production (JQAS)
- [ ] **(P1)** **Placebo decomposition — REVIEW BY OLIVER (2026-07-28):** Oliver's objection (defensive activity also CAUSES bookings, so a future-booking placebo cannot be expected to be zero) led to a decomposition by booking reason (`src/build_placebo_timing.py`, cross-interval design, window extended to 75'): the bad-behaviour-card placebo (dissent/time-wasting; mechanical activity→booking channel OFF; 477 treated) is NULL for engagement/pressures/tackles (−1.3/−2.4/−9.8%, all p≥.19) but POSITIVE for fouls (+23.9%, p=.017); the foul-card placebo on the identical sample (2,513 treated) is positive throughout. Framing now in Appendix C + §6.2: activity-outcome identification supported (raw placebo signal = mechanical channel); foul effect carries positive disposition selection → −26.5% is conservative. §4.1 "as good as random" left unchanged. Oliver to review the rewritten Appendix C placebo subsection and §6.2 paragraph.
- [ ] **(P2)** Page budget: manuscript now compiles at 31 double-spaced pages with §1/§2/§7 still to write — check whether JQAS counts appendices toward the 20–30 guideline; if so, appendices may need to move to supplementary material.
- [ ] **(P2)** De-identification pass for blind review (acknowledgements, repo links, self-references).
- [ ] **(P3)** Prepare reproducibility repo (code + StatsBomb data pointers) for JQAS submission.
- [ ] **(P3)** Sync slide deck (`documents/slides_paper.pptx`) to the canonical Spec-B numbers.
- [ ] **(P3)** JQAS submission mechanics: figures as separate EPS/TIF/JPG ≥300 dpi, ScholarOne upload, keywords check.

---

### Suggested critical path (next up, status 2026-07-28)
1. **G**: Oliver reviews the placebo-decomposition framing (Appendix C + §6.2).
2. **A**: write §2 Related work, then §1 Introduction, then §7 Discussion + abstract/keywords.
3. **D**: decide keep/drop for the extended outcome set (fine-grained actions, error events, rates).
4. **G**: page-budget check; de-identification pass; slide-deck sync; submission mechanics.
