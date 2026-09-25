# Rater2 confirmation of the R099 correction

Reviewer: rater2
Review date: 2026-09-18
Item: R099, stroke_Sub29_P, N03
Referenced rater1 confirmation: `RATER1_REMAINING_REQUIREMENTS_CONFIRMATION.md`, SHA-256 `d67ee16f11c9d65ffd19b4212c0eb6769ffe6c25d396cef6194e43971813dcb7`
Source consensus workbook: `Case_requirements_reconciliation_consensus.xlsx`, SHA-256 `caffdccafbbb8665481dbf2899c71817e3320ff27caa8afee989134cece769ac` (not modified by this confirmation)

## Decision

**Accepted as written.** Rater2 explicitly accepts both the proposed final requirement wording (column P) and the proposed required components (column Q) for R099 exactly as they appear in the rater1 confirmation file. No changes are proposed.

## Accepted final requirement wording (column P)

> Describe EITHER (A) the BF envelope above its phase-specific reference mean at approximately 34% of the analysis cycle OR (B) the RF mean envelope above the algorithm-defined threshold for approximately 95% of the analysis cycle AND spanning the cycle boundary. One complete route is sufficient; both routes are not required. For route A, muscle identity, mean-relative direction and approximate cycle location are jointly required; exact repetition of max |z| 5.1 is optional. For route B, muscle identity, approximate above-threshold coverage and boundary-spanning status are jointly required; exact interval endpoints are optional.

## Accepted final required components (column Q)

> OR between routes. Route A requires BF AND above its phase-specific reference mean AND approximately 34% of the analysis cycle. Route B requires RF AND the mean envelope above the algorithm-defined threshold for approximately 95% of the analysis cycle AND spanning the cycle boundary. Exact max |z| 5.1 is optional for route A; interval endpoints 80%-75% are optional for route B. Route B does not require a direction relative to the reference mean or a location of maximum deviation. Apply the approved shared interpretation limits: threshold coverage is not physiological activation duration, continuous contraction or proof of disease; neither route licenses unsupported gait-phase, normal-timing or severity claims.

## Reason

The previous final wording, which rater2 had drafted, offered the same two routes but then applied a generic component sentence requiring mean-relative direction and approximate cycle location to both. Those components belong only to the signed-deviation route A. An otherwise complete RF threshold-extent route B could have been denied full coverage for lacking components it cannot have. The correction makes the components route-specific, which is the same principle rater2 already accepted for the control EMG rows (R153, R168, R173, R178, R193) under shared topics T01 and T08.

Input support was re-checked by rater2 against `../case_review_v1/stroke_Sub29_P/model_user_prompt.txt`:

- `RF: above-threshold interval(s) 80%-75% (wraps cycle boundary), 95% of cycle above threshold, above threshold across cycle boundary`
- `BF: ... max |z| vs healthy reference: 5.1 (above reference, at 34% of cycle)`

Both routes are supported by the model-visible input; no plot, supplementary percentile or new calculation is involved.

## Scope

With this acceptance, R099 is bilaterally confirmed and, together with the rater1 confirmation of the other 176 rows and the previously recorded bilateral responses to the eight shared topics, 23 original requirements and 13 additions, all 200 original requirements and 13 addition rows have bilateral decisions. Rater2 does not reopen any other accepted requirement.

This confirmation concerns prospective case-specific scoring requirements only. It does not change historical reports, ratings or adjudications, authorize report generation, confirm participant exposure, or approve scoring weights, study outcomes, formal samples or statistical analyses. The finalized requirements version incorporating the exact agreed R099 replacement should be produced by the study administrator with the review trail retained; rater2 has not edited the consensus workbook.
