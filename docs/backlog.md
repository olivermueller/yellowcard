# Yellow-Card Paper — Project Backlog

**Source:** Co-author meeting 2026-07-14. **Primary target:** Journal of Quantitative Analysis in Sports (JQAS).
**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · **(P1/P2/P3)** priority.
Completed items are removed from this list; the full record of decisions and results is in the git history of this file.

---

## A. Story & framing
- [ ] **(P1)** Write §2 Related work (three strands: cards→team outcomes; suspension/deterrence between matches; cards as referee decisions; gap = within-match player-level response). No causal-ML-in-sports strand; no "Foul Play" (cards are outcome there, not treatment).
- [ ] **(P2)** Write abstract (~200 words) + §1 Introduction (lead with the football/behaviour question; three margins: coach withdrawal 2.7x, player fouls −26.5%, teammates +4.5%) + keywords (3–6, not in title).
- [ ] **(P1)** Write §7 Discussion and conclusion.

## C. Survival bias / outcome window
- [ ] **(P3)** (Considered, deprioritised) per-minute normalisation — superseded by multi-window; revisit only if windows prove insufficient.

## D. Outcomes / targets
- [ ] **(P1)** Add **fine-grained defensive actions** (decompose the aggregate). *Status: manuscript currently uses the 4-outcome set; decide whether the decomposition goes into a revision round or is dropped.*
- [ ] **(P1)** Add **"error" events** — dispossessed, unforced errors, miscontrols, etc. *Status: not in the current manuscript; decide keep/drop.*
- [ ] **(P2)** Add **rate-based targets** (e.g., duel/tackle win rate) alongside raw counts. *Status: not in the current manuscript; decide keep/drop.*

## E. Covariates
- [ ] **(P3)** Elo, player market values — **not pursued** for now (explicitly out of scope).

## F. Publication strategy (two papers)
- [~] **(P1)** **Paper 1 ("yellow cards")** → JQAS. This backlog covers Paper 1. **Status 2026-07-24: manuscript repo `jqas-yellowcard-paper` (Overleaf-linked); §3–§6 + Appendices A/B written on final Spec-B numbers; compiles at 25 double-spaced pages (guideline 20–30). Open: §1, §2, §7, abstract, machinery appendix, de-identification, Chicago-format bibliography for §2 references.**
- [ ] **(P3)** **Paper 2 (methods-forward, Call for Causal ML)** → Journal of Sports Analytics; *different* treatment (X) and outcome (Y). Park as a separate future track — not part of Paper 1's critical path.

## G. Manuscript production (JQAS)
- [ ] **(P1)** **Evaluation of the DML machinery (appendix; discussed 2026-07-23):** reviewers expect nuisance-fit evidence even though it is not the real test; provide a 4-exhibit package: (a) out-of-fold nuisance metrics (AUC/Brier for e(W), R2 for m(W)) + propensity CALIBRATION plot; (b) insensitivity table — learner swap (lasso/logit, random forest, HGB variants) x 4 DVs + tau-hat spread over ~20 cross-fitting seeds + residual-balance joint F (T_res vs W); (c) timing placebo (most informative of the three; to be run first): 'effect' of a future booking (60-75) on 45-60 behaviour among players unbooked through 60 — must be ~0 under unconfoundedness; the 30-45 result shows the test is able to detect contamination; doubles as Section-6 identification evidence. Semi-synthetic recovery experiment DROPPED (Oliver 2026-07-23: not a methods paper — candidate for Paper 2/JSA instead). Framing sentence: nuisance fit is not the estimand; we evaluate by insensitivity, falsifiable implications, and recovery of known effects.
- [ ] **(P2)** Robustness: treatment-definition sensitivity ([15′,45′]) still open; the timing placebo is folded into the machinery-evaluation item above.
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
