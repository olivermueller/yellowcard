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

## F. Publication strategy
- [~] **(P1)** **Paper 1 ("yellow cards")** → JQAS. This backlog covers Paper 1. **Status 2026-07-24: manuscript repo `jqas-yellowcard-paper` (Overleaf-linked); §3–§6 + Appendices A/B written on final Spec-B numbers; compiles at 25 double-spaced pages (guideline 20–30). Open: §1, §2, §7, abstract, machinery appendix, de-identification, Chicago-format bibliography for §2 references.**
## G. Manuscript production (JQAS)
- [ ] **(P1)** **Placebo interpretation — REVIEW BY OLIVER (2026-07-27):** the machinery appendix (Appendix C, done) contains a substantive result: BOTH timing placebos reject zero on all four outcomes with positive sign (within-half: booking 60-75 on 45-60 outcomes, fouls +21.9%***; cross-interval: booking 45-60 on H1 30+ outcomes, fouls +26.6%*** — the half-time interval does not remove the selection signal). Current framing in Appendix C and §6.2: the placebos sign the residual selection (positive → main negative estimates are understatements; consistent with raw −21% vs DML −26.5% and with the Cinelli–Hazlett direction argument). Oliver to confirm this framing and decide whether the §6.2 unconfoundedness language ("as good as random") needs softening in §4.1.
- [ ] **(P2)** Robustness: treatment-definition sensitivity ([15′,45′]) still open.
- [ ] **(P2)** Page budget: manuscript now compiles at 30 double-spaced pages with §1/§2/§7 still to write — check whether JQAS counts appendices toward the 20–30 guideline; if so, appendices may need to move to supplementary material.
- [ ] **(P2)** De-identification pass for blind review (acknowledgements, repo links, self-references).
- [ ] **(P3)** Prepare reproducibility repo (code + StatsBomb data pointers) for JQAS submission.
- [ ] **(P3)** Sync slide deck (`documents/slides_paper.pptx`) to the canonical Spec-B numbers.
- [ ] **(P3)** JQAS submission mechanics: figures as separate EPS/TIF/JPG ≥300 dpi, ScholarOne upload, keywords check.

---

### Suggested critical path (next up, status 2026-07-27)
1. **A**: write §2 Related work, then §1 Introduction, then §7 Discussion + abstract/keywords.
2. **G**: machinery-evaluation appendix (timing placebo first, then nuisance metrics/calibration, then insensitivity table).
3. **D**: decide keep/drop for the extended outcome set (fine-grained actions, error events, rates).
4. **G**: de-identification pass; slide-deck sync; submission mechanics.
