# Blinded working consolidation

The subsequent [blinded analysis-input freeze](../analysis_freeze_v1/README.md) is complete and has been validated. It preserves this working layer and the separate personal category proposals as source-linked records; it is not a new expert signature or a model-unblinding result.

Latest review: [Scoring audit, 2026-09-21](SCORING_AUDIT_2026-09-21.md) and [targeted audit workbook](SCORING_AUDIT_2026-09-21.xlsx). The targeted returns and rater3 clarifications are complete. The new issue decisions and 24 control-flag annotations have been incorporated from explicit human responses. All 18 category proposals are preserved separately, with four groups retaining different proposed tags. See [return check](SCORING_AUDIT_RETURN_CHECK.md).

This is an administrative consolidation of the three human raters' records, not a signed final consensus release. It preserves independent submissions separately from post-feedback judgments. No model identity key was read by the builder, and no model comparison was run.

## Current results

- 105 reports from 35 participants.
- 552 report-requirement rows: 447 case requirements and 105 G03 rows. All three latest coverage labels match on every row. Matching labels are not a newly signed approval of the entire dataset.
- 34 discussed issue claims: 14 Acceptable, 4 Error, and 16 Pending adjudication. These are counts within the discussion subset, not study-wide error counts.
- 329 current per-rater issue records after residual and audit responses. Each rater has 52 Error and 16 Pending records; the confirmed records map to 52 report-scoped groups, not 156 independent errors.
- The five recently closed claims remain Pending: D002/D004 (E03), D024 (E02; E04 withdrawn), and the two within-median claims (E01; one group per report). Preferred interpretations are retained separately.

`Consolidated_ratings_working.xlsx` contains the current records, discussion crosswalk, original independent records, sources, and the completed residual responses. No report-level differences remain in confirmed-record counts or any-error labels. `BUILD_RECORD.json` records source and output hashes. The builder refuses to overwrite a workbook edited after generation.

## Earlier residual returns incorporated on 2026-09-21

All five requested responses have been incorporated. The latest rater3 workbook changes the Sub02 judgment from Pending adjudication to Error E03. Source reasons and source confirmation dates (2026-09-20) are retained as submitted; receipt and consolidation are dated 2026-09-21. No expert source workbook was edited during this consolidation.

| Report | rater1 | rater2 | rater3 | Result |
| --- | --- | --- | --- | --- |
| R25F5AA9361D9E14F, control Sub06; medial-head designation | Error E01 | Error E01 | Error E01 | Aligned |
| R31D0B47CA4DF36CF, stroke Sub02; below-threshold complement | Error E03 | Error E03 | Error E03 | Aligned after rater3 revision |
| RAF417EE5FDC33A78, stroke Sub13; whole-cycle continuity | Error E03 | Error E03 | Error E03 | Aligned |

See **Residual return decisions** for the five responses and source paths. The **Residual record differences** sheet now contains no outstanding rows. At this earlier residual-only stage, each rater had 51 confirmed issue records and 16 Pending records. These are per-rater counts, not 153 independent errors; no new study-wide grouping or final model comparison is inferred from matching counts.

`RESIDUAL_RETURN_CHECK.json` retains source hashes, the previous Sub02 interpretation, and the latest response. The user confirmed that rater3 is a human reviewer; the earlier identity-description correction changed no assessments or signatures. The latest rater3 rationale mentions a strict rule; this is preserved as the reviewer's submitted reasoning, not adopted as a new study-wide rule. The previously closed 16 Pending claims remain unchanged.

Original independent records remain separate for reliability analysis. This completed residual alignment is not a newly signed final dataset release. The later audit return supplies the missing control flags explicitly; see Audit flag updates in the current workbook.

A source-span comparison of current confirmed records was also checked. The additional apparent mismatch in RDBE98A8F7EC455C5 is a grouped repetition: raters quote either line 17 or line 46, and their explanations explicitly connect both to the same ERS continuity issue. It needs no additional response. This alignment check is not a fresh clinical assessment of all 105 reports.

## Pending and analysis

Follow the approved execution protocol, section 9, in `../execution_analysis_v3_draft/PROTOCOL.md`. Pending is neither confirmed Error nor confirmed Acceptable. Any-error is positive when a confirmed error exists, negative only after complete review without confirmed or pending issues, and otherwise unknown. Report unknown-outcome bounds as specified in the protocol; do not silently recode unknown outcomes. Pending issue judgments alone do not remove an otherwise complete coverage score. Keep fixed coverage denominators and the separate G03 result; do not assign partial coverage a value of 0.5.

Submitted control flags remain preserved, including the 24 explicit audit updates. No current control Error/Pending record is missing either flag. A Pending record remains Pending regardless of its flags. Report summaries are per-rater working summaries, not final model-level outcomes.

Before final analysis, align the final import and analysis specification with the actual three-independent-rater workflow. The [blinded analysis preparation](../three_rater_analysis_v1/README.md) now provides a tested additive interface and a concrete draft addendum; it does not authorize final analysis or replace the existing importer. The existing importer assumes two independent raters plus a third adjudicator and must not be used unchanged. Preserve original independent ratings for reliability analysis; post-discussion agreement is not independent reliability. Any change to the prespecified analysis must be documented explicitly before model comparisons. Freeze the completed common data and supporting confirmations before unblinding.

## Verification

All quoted claim anchors match the blinded report text. Source hashes remained unchanged; original independent records are retained. The workbook contains no Chinese text, formula cells, or spreadsheet error cells. The existing formal rating, consensus, and analysis tests passed (35 tests). Additional source-to-output checks verified all 24 imported flag records, exact independent-sheet preservation, and the 52-group crosswalk. These checks do not establish expert consensus or validate a future three-rater final analysis.

## Audit responses incorporated; verification completed on 2026-09-22

All three targeted returns are complete. See [return check](SCORING_AUDIT_RETURN_CHECK.md) and [source-linked receipt record](SCORING_AUDIT_RETURN_CHECK.json). Source confirmation dates remain September 21; the final verification date is recorded separately.

- `Audit issue decisions`: three explicit Error E01 responses for the one Sub15 medial-head claim, now in Issues current.
- `Audit flag updates`: 24 explicit per-rater annotations, now in Issues current. No automatic No values were introduced.
- `Audit category proposals`: 18 personal proposals, including rater3's withdrawal of E05 for Sub01. Four of six groups retain different proposals. The Categories field in Issues current still contains the earlier registered sets; this separate proposal sheet must be consulted before category-level analysis. No common-category update or first-tag policy was inferred.

All original independent workbook rows and all 16 closed Pending groups remain unchanged. The 51 existing audit crosswalk groups plus the new Sub15 group account exactly for all 156 confirmed per-rater records (52 groups). This administrative crosswalk is not a newly signed consensus release. No further rater response is requested for this audit round.

The dated audit workbook is the pre-return snapshot; its Sources sheet intentionally records the earlier hashes. Current output and source hashes are in BUILD_RECORD.json. The receipt JSON retains previous return hashes, dates, and the submitted revisions rather than overwriting their provenance.
