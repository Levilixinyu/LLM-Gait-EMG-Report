# Three independent raters: analysis addendum for study-lead confirmation

Prepared: 2026-09-22 America/Chicago (2026-09-23 UTC at validation). Status: **Draft; no approval or expert signature implied.**

Partial authorization update, 2026-09-23: the study lead explicitly authorized the three original independent agreement comparisons described in A1. These have been computed without model unblinding; see AGREEMENT_AUTHORIZATION.json and INDEPENDENT_AGREEMENT.md. This limited authorization does not approve A3's pathology-flag clarification, a final dataset release, or model-level analysis. The historical preparation statements below refer to the draft checkpoint unless superseded by this update.

Subsequent confirmation, 2026-09-23: the study lead explicitly confirmed that a pathology annotation does not require a simultaneous E02 tag. See SEMANTIC_FLAG_CONFIRMATION.json. This resolves the A3 semantic-flag question and supports the previously described blinded administrative data freeze. It does not create expert signatures, category consensus, or authorization to open model identities. Other proposed choices are not retrospectively labeled approved by this specific confirmation.

This document makes the actual three-independent-reviewer workflow explicit before model unblinding. It does not retrospectively amend the date or scope of the original protocol. It does not reopen completed Pending discussions or require raters to agree on all category tags.

## Scope and timing

The [original protocol](../execution_analysis_v3_draft/PROTOCOL.md), especially sections 3 and 7, specified two independent raters and a third human adjudicator if needed. The study lead subsequently requested a third full independent review. All three raters are human experts; rater3 joined at scoring and did not develop the criteria. The [reviewer addition record](../rating_delivery_rater3_v1/REVIEWER_ADDITION_RECORD.md) documents that this decision followed receipt and administrative inspection of the first two submissions.

By the time of this addendum, the team and processing agents have seen blinded individual judgments, disagreements, revisions, and aggregate counts. Model identities have not been used by the preparation code. Describe this as a documented amendment after blinded outcome inspection, not an original prespecification or an outcome-naive choice. Blinding does not undo exposure to other raters' views during discussion.

The sample remains 25 stroke cases and 10 separate exploratory controls, with three reports per case (105 reports). Three raters produce 315 report-rating assignments and 1,656 coverage-item judgments at a given complete stage, not additional participants. The 149 included case requirements, G03, model inputs, generated outputs, and generation settings remain fixed.

## A1. Preserve the original agreement analysis; add two descriptive pairs

Retain the planned rater1-rater2 independent agreement analysis as separately identifiable. Add rater1-rater3 and rater2-rater3 as supplementary descriptive comparisons using the same three-category cross-tabulation, raw agreement, and unweighted Cohen's kappa already specified in section 7. Do not select a preferred pair after seeing its agreement or model results. Do not average the three kappas into an alleged three-rater kappa. No new significance test, multi-rater coefficient, weighted kappa, or rater-ranking endpoint is proposed.

Use the preserved original submissions, before feedback and reconciliation. Exclude Pending and Cannot assess coverage rows from each pair's assessable denominator and disclose those exclusions. Keep stroke/control and case-requirement/G03 results separate. Report error-detection agreement at the report level for completed reviews with known any-error status; an absent issue record is not an invented Acceptable assessment of a particular claim. Do not compute issue-level kappa over an artificial union of claims.

These item-level summaries are descriptive and do not treat all items or three reports from one participant as independent participants. Use source records for any incidental unblinding or exposure disclosure. No new reliability calculation is made from the matching post-discussion labels.

## A2. Use source-linked post-feedback decisions for outcome preparation

Keep original independent records and post-feedback individual records separate. The current working table contains matching coverage labels and aligned confirmed-error groups but is not a newly signed final dataset. Matching labels alone are not a signature or permission to invent a common category set.

Assemble the final outcome layer from explicit source-linked judgments and accepted dispositions. Keep the 52 confirmed report-scoped claim groups separate from the 156 per-rater confirmed records. A multi-tag group and repeated locations within a report count once. Preserve the existing documented grouping; do not group claims by overlapping text alone or merge across reports.

The 16 Pending groups are administratively closed but substantively unresolved. They require no further full review. Pending is neither Error nor Acceptable:

- Any-error is positive when a confirmed error exists, even if another claim is Pending.
- It is negative only after a complete review with neither confirmed nor Pending issues; otherwise it is unknown.
- Report confirmed counts and Pending counts separately. The confirmed count is not a guarantee of the total underlying error count.
- Preserve the protocol's evaluable denominators and all-planned-slot unknown bounds. Do not impute unknowns as zero.
- Pending issues do not erase an otherwise complete coverage score. Preserve the fixed requirement denominator and the separate G03 result; no half-credit for Partially covered.
- Joint success requires all case requirements and G03 Covered, completed issue review, and neither confirmed nor Pending issues. Known coverage failure or confirmed error establishes joint failure even if another component is unknown. Preserve section 9's complete-review eligibility for its main point estimate.

Final assembly must record the applicable human source and scope, while acknowledging that the assembled file is an administrative derivative. Do not invent a new signature, coordinator adjudication, or fourth reviewer. If a new content disagreement appears during assembly, retain individual positions and mark the affected outcome uncertain; do not impose a majority vote.

## A3. Preserve different category proposals and semantic flags

The working workbook's `Categories` field retains prior registered sets. `Audit category proposals` contains the newer personal proposals and their exact reasons. Six claim groups were reviewed, and four now have different proposed sets. Explicitly distinguish these layers in analysis; do not silently mix old and new tags or treat the sheet's earlier common-tag wording as a joint approval.

Proposed reporting: use source-linked confirmed claim groups for any-error and issue counts; present category distributions by reviewer, applying each reviewer's explicitly recorded latest proposal to that reviewer's record in a separately traceable analysis view. For differences, show the alternatives rather than a pooled majority/union category. Multiple tags do not create multiple errors. Do not adopt the suggested first-tag-only frequency rule without a separate change; the original plan counted category membership, not tag order.

Keep the two control semantic annotations separate from category counts. Preserve explicitly supplied Yes/No values and unknowns, with an exact claim anchor. A missing annotation is not No; a Pending claim with a Yes flag remains uncertain for that flag unless a confirmed qualifying claim already makes it positive.

The earlier section 6 wording specifically tied a deficit-presupposing question's pathology flag to a confirmed E02 issue. Rater1 now proposes E07 alone for the constrained-ROM claim while retaining its pathology flag. **Confirmed by the study lead on 2026-09-23: the expert's explicit confirmed impairment interpretation and pathology annotation govern the semantic flag, rather than requiring an identical literal E02 tag across reviewers.** Merely asking a clinical question, or recording E07, is not sufficient to create the flag. This operational clarification does not automatically recode any judgment. The existing returned semantic annotations are preserved. It is a post-rating clarification, not a claim that the original protocol contained this wording.

Endpoint-span comparisons do not automatically become invalid solely because an individual muscle cutoff is unavailable. Retain differing reviewer explanations as interpretations rather than elevating any one proposal to a new common rubric rule. No new score penalties or severity weights are introduced.

## A4. Preserve the planned estimands and uncertainty

Keep the equally weighted participant mean of full case-requirement coverage as the primary stroke outcome, the same complete three-report participant sets, paired differences, 20,000 shared-index BCa resamples with seed 20260918, and the planned descriptive and family-adjusted intervals. Preserve the registered unavailable/degenerate interval behavior. G03, error outcomes, semantic flags and controls remain separate secondary/exploratory results. No extra clinical utility score, pooling of the 30 control reports as independent cases, or model winner selection from unadjusted intervals is proposed.

Show the three reviewers' original independent results as separate sensitivity descriptions. These do not replace the primary source-linked post-feedback outcome layer, and the original rater1/rater2 sensitivity results remain identifiable. One generated report per case/configuration still cannot estimate generation variability.

## Preparation and release boundary

The additive `src/eval/three_rater_blinded.py` interface operates on opaque report IDs. It refuses post-feedback input for independent agreement and preserves unknown control annotations. `scripts/prepare_three_rater_analysis.py` validates source hashes, membership, stage separation and existing per-report metrics; it does not calculate model contrasts or real-data agreement statistics. The old two-rater consensus importer remains unchanged and must not be used for this three-rater release.

Before final model analysis:

1. The study lead confirms or revises this concrete addendum, including A3's semantic-flag clarification. This is an analysis decision, not a request for experts to align their ratings.
2. Assemble and freeze the exact analysis dataset with source hashes, explicit claim grouping, retained Pending states, and individual category differences. Record approval scope without manufacturing expert signatures.
3. Only after that freeze and authorization, join the protected model mapping and run the planned comparisons. Model identities stay outside rater materials.

No study-lead confirmation, final freeze, model-mapping join, or unblinding has been performed by creating this draft.
