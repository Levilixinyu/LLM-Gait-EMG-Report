# Wording-boundary sensitivity analysis

This is an exploratory supplement created after the analysis team was unblinded. It preserves the original frozen outcomes and all human reviewers' individual decisions. No new consensus, ranking or confirmatory test is introduced.

## What changes

The coverage scores and their previously computed paired intervals are identical in every scenario: the targeted returns change no coverage judgment. Stroke mean full coverage remains Claude 98.2%, GPT 97.0%, Gemini 81.8%. The Claude-GPT contrast still includes zero. This invariance follows from the scope of the review, not an independent validation of coverage scoring.

## Stroke error reports

Claude remains 11/22 evaluable (3 unknown; all-planned bounds 44%-56%). GPT remains 2/25 (0 unknown; bounds 8%-8%). Gemini varies as follows:

| Scenario | Error / evaluable | Unknown | All-planned bounds | Confirmed groups | Pending groups |
| --- | --- | --- | --- | --- | --- |
| Frozen baseline | 12/23 | 2 | 48%-56% | 13 | 9 |
| rater1 targeted overlay | 11/22 | 3 | 44%-56% | 11 | 10 |
| rater2 targeted overlay | 12/23 | 2 | 48%-56% | 12 | 10 |
| rater3 targeted overlay | 11/22 | 3 | 44%-56% | 12 | 9 |
| Disagreements kept unknown | 10/21 | 4 | 40%-56% | 10 | 12 |
| Disputed claims cleared | 10/22 | 3 | 40%-52% | 10 | 9 |
| Disputed claims counted | 12/23 | 2 | 48%-56% | 13 | 9 |

Across these scenarios, Gemini has 10-12 confirmed-error stroke reports out of 25 planned slots; counting unknown states as 0/1 gives an overall envelope of 40%-56%. The lowest corresponding Claude bound is 44%, while GPT remains 8%. Thus the descriptive finding of fewer flagged stroke reports for GPT persists within this targeted sensitivity. This is not a confidence-interval comparison, a significance test, or proof of general superiority. Claude versus Gemini does not have a stable error ordering across these choices.

Two report-level any-error statuses can change under these scenarios. Other changed issue labels leave an existing confirmed error in their report. A report with no remaining confirmed error but another Pending issue stays unknown, not error-free. Detailed report attribution is retained only in the protected analysis directory.

## Controls and pathology annotation

Control any-error results do not change: Claude 6/9 evaluable (1 unknown; bounds 60%-70%), Gemini 8/10 (80%), GPT 0/10. Other confirmed groups remain in each affected control report.

For the single disputed Gemini pathology annotation, rater1 and rater3 give Yes while rater2 gives No. The corresponding targeted overlays are 1/10, 0/10 and 1/10. A scenario retaining that disagreement as unknown gives 0/9 evaluable, one unknown, and all-planned bounds 0%-10%. Do not report it as a newly unanimous confirmed pathology event or as evidence of no event. Normality annotations remain zero for every model, and the other models' pathology annotations remain zero. These semantic annotations are not diagnostic false-positive rates.

## How to use this supplement

- **Hybrid overlays:** A named-rater scenario substitutes only that reviewer's eight latest labels and one flag. It does not represent a full independent re-rating by that reviewer.
- **Disagreement scenarios:** No voting or forced consensus. Pending/cleared/counted scenarios are analyst-defined alternatives. Previously frozen Pending groups remain Pending in every scenario.
- **Bounds:** All-planned bounds count unknown report status as 0/1. They are not confidence intervals. A report is positive if any confirmed error remains; negative requires a complete review without confirmed or pending errors.
- **Joint outcome:** The point estimate uses complete nonpending reviews, as in the existing protocol. Known failure with an unresolved issue can be outside that denominator but still constrains all-planned bounds.
- **Categories and flags:** No shared E-code set is imposed. The AG023 pathology annotation varies independently of its matching Error decision; E02 is not required. Category-tag differences do not multiply issue counts.
- **Interpretation:** Selected internal sample; one response per model and case. These scenarios do not assess all possible wording disputes or establish general model superiority. The original-independent sensitivity must still accompany these results.

The original independent-review sensitivity remains necessary: rater3's original error pattern did not reproduce the later Claude-GPT ordering. These targeted scenarios do not resolve that between-stage difference.

Files: [aggregate workbook](Wording_sensitivity.xlsx), [manuscript wording](MANUSCRIPT_ADDENDUM.md), [provenance record](BUILD_RECORD.json). Per-report scenarios and the identity join remain in `data/rating_packets_formal_v1/private/wording_sensitivity_v1/ANALYSIS.json`, outside reviewer packets.
