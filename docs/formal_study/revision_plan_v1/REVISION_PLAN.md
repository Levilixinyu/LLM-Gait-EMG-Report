# Journal submission revision plan (v1)

Drafted 2026-09-25 from a full read of `manuscript_v1/MANUSCRIPT.md`, the frozen analysis records and the maturity follow-up. This is a planning document. It changes no score, report, frozen outcome or authorization. Items marked **author** need a decision or information that project files cannot supply.

## Already done (do not duplicate)

| Reviewer concern | Existing answer | Location |
| --- | --- | --- |
| Low kappa for error judgments despite high raw agreement | Post-hoc nominal AC1 with participant-cluster bootstrap, all 18 original cross-tabulations reproduced | `agreement_sensitivity_v1/` |
| No reporting checklist | TRIPOD-LLM main and abstract checklist with item-level status | `reporting_checklist_v1/` |
| Provenance detail crowds the main text | Supplementary methods started | `manuscript_v1/SUPPLEMENTARY_METHODS.md` |
| Offline reproducibility | Researcher-only bundle and clean-environment replay | `reproducibility_v1/` |

Both remain post-hoc and are labeled as such. Do not present AC1 as the pre-specified reliability measure.

## Phase 0. Stabilize the working tree (same day)

1. Reconcile concurrent edits. More than one agent session has written to this tree today. Finish or stop the other session, run the full suite, then commit the current manuscript revision, AC1 analysis, checklist and supplementary methods as one or two commits.
2. Rebuild the manuscript and the checklist once after committing so their build records reference the same source hashes.
3. Freeze the scope of automated additions. Every further analysis needs a one-line justification in this file before it is built.

## Phase 1. Decide the two design-level questions (author, this week)

**Q1. Repeat generation.** Single output per case and model is the most predictable reviewer objection. Options:

| Option | New reports | Generation reservation at recorded rates | Human rating load | Effect on claims |
| --- | --- | --- | --- | --- |
| A. None | 0 | 0 | 0 | Keep as stated limitation; target a methods-friendly journal |
| B. Stroke only, 2 extra outputs per case and model | 150 | about 85 USD | 150 reports; coverage plus error tags | Within-model consistency estimate for the primary endpoint |
| C. Full replicate, 2 extra outputs everywhere | 210 | about 120 USD | 210 reports | Also covers the control supplement |

The reservation figures scale the recorded 59.64 USD per 105-slot pass and are not invoices. Human rating is the real cost: one original stage was 315 assignments and 1,656 coverage judgments across three raters. Option B rated by two raters, with the third resolving disagreements only, is the smallest design that still answers the objection. Any new generation must be a new authorized stage with its own plan and freeze; the completed 105 reports and their ratings are not regenerated or re-rated.

**Q2. Framing.** Choose between (a) a model comparison with a transparent scoring framework, or (b) a methodological evaluation study whose main contribution is scoring completeness and evidence fidelity separately while preserving unresolved judgments. Option (b) matches the sample size, the post-hoc stages and the model-version instability better. The title can stay; the abstract objective, the first Discussion paragraph and the Conclusion move.

Both answers gate Phase 3. Phases 2 and 4 can proceed regardless.

## Phase 2. Author-owned declarations (author, parallel)

Every item in `manuscript_v1/AUTHOR_CONFIRMATION.md` is still open except reviewer background:

- Institutional determination for this secondary analysis of public de-identified data, with a reference number or an explicit written exemption. Do not infer exemption.
- Author list, affiliations, contributions, corresponding author.
- Funding statement and competing interests for each author.
- AI-assistance disclosure in the target journal's required form. The project record shows assistant-supported coding, source audit, material preparation and manuscript drafting; human raters made all scoring judgments.
- Public release scope: which code, which data exports, which expert records. The current bundle contains model identities and rating data and is not a public artifact as-is.

## Phase 3. Rewrite the manuscript for readers (2 to 3 weeks)

Target 4,000 to 4,500 words for the main text before references, down from 8,011. Word counts are the current Markdown build.

1. **Move to supplement**: generation staging, freeze and unblinding chronology, hash and stream verification, the D01-D03 wording, the semantic-flag clarification, the joint-success denominator discussion, report-length counting rules, and every sentence that only restates what a number is not. Supplementary methods already exist; extend them rather than the main text.
2. **Rename internal terms once and use plain names after**: frozen post-feedback layer becomes "final ratings"; original independent layer becomes "original ratings"; G03 becomes "reference-comparability requirement"; D01-D03 becomes "the post-rating clarification"; all-planned bounds become "bounds counting unknown reports as 0 or 1". Define each once in Methods.
3. **Limit caveats to one per claim.** Keep the strongest caveat in the sentence where the claim appears and remove repetitions elsewhere. Limitations already collects them.
4. **Cut Table 5 to the planned pair** (rater1-rater2) in the main text and move all three pairs plus AC1 to a supplementary table. Add AC1 to that supplementary table rather than creating a new one.
5. **Results order**: sample; primary coverage; errors; controls; agreement; sensitivity. Drop the report-length subsection from Results into one Discussion paragraph with the supplementary table reference.
6. **Discussion**: lead with the coverage-versus-fidelity finding, one paragraph on rating-stage dependence, one on length, one on controls, one on what the next study needs. Five paragraphs.
7. **Introduction**: keep at four paragraphs; the current version is close.
8. Synchronize every edit in `scripts/build_manuscript_draft.py` so a rebuild preserves the prose, per `AGENTS.md`.

If Phase 1 chooses repeat generation, Phase 3 waits for those results and adds one Results subsection and one supplementary table; nothing else in the structure changes.

## Phase 4. Journal formatting and preprint (1 week)

Recommended order of targets, chosen for fit rather than impact factor:

1. JMIR AI or JMIR Medical Informatics: receptive to LLM evaluation designs, CLEVER precedent, structured abstract.
2. Journal of NeuroEngineering and Rehabilitation: gait and EMG readership, no strict length limit, accepts pilot-scale evaluations.
3. PLOS Digital Health as the fallback.

Steps: confirm the journal's article type and word limit; convert references to the journal style; attach TRIPOD-LLM as a supplement; post a medRxiv preprint before submission so the preserved analyses have a citable date; complete the submission-system declarations from Phase 2.

## Out of scope for this revision

- Re-rating the completed 105 reports, forcing agreement on the 16 Pending groups or the disputed control annotation.
- Adding models, prompt variants or a second dataset.
- Any claim of diagnostic accuracy, clinical benefit or equivalence between models.
