# Formal rating and analysis data dictionary

This schema is for the approved prospective study. It does not import or change
the historical five-case trial. All report IDs are opaque and per report; model
keys are restricted analysis metadata.

| Field or object | Meaning |
| --- | --- |
| `case_id` | Cohort-qualified participant and side, such as `stroke_Sub01_P` or `control_Sub01_avg`; never join on Sub01 alone |
| `slot_id` | Private frozen case/model generation slot, retained even for no report |
| `report_id` | Opaque ID shown to both raters; no reusable model code |
| `model_key` | Restricted mapping field; absent from rater metadata |
| `material_status` | Available captured text or explicit Unavailable no-report slot |
| `required_ids` | Included frozen record IDs, not omitted candidates or individual AND/OR components |
| `decision` in Coverage | Covered, Partially covered, Not covered, or Cannot assess |
| `adjudication_status` in Coverage | Final or Pending, separate from a provisional coverage category |
| Unknown analysis item | Pending, Cannot assess, or missing label; never Not covered by default |
| `G03` | Separate common comparability-and-inference item, once per report |
| `issue_id` | One unique issue group within a report; multiple locations/tags do not multiply it |
| Issue `decision` | Error, Acceptable, Pending adjudication, or Outside case-error scope |
| `categories` | Applicable E01–E09 tags, separated by semicolons in the workbook |
| `exact_quote` | A verbatim substring of the retained response; locations may identify repeated occurrences |
| `pathology_flag` / `normality_flag` | Yes/No on qualifying confirmed or pending control issues; stroke rows may leave these inapplicable fields blank |
| `issue_review_complete` | Explicit completion of issue review; blank issues alone do not prove an error-free review |
| `four_section_format` | Separate format judgment; not an error group or primary score deduction |
| `incidental_unblinding` | Reviewer reports recognition or self-identifying prose; text remains unchanged |
| `coverage` | Finally Covered count divided by fixed K; unavailable if any case item is unknown |
| `coverage_bounds` | Known Covered/K to (known Covered + unknown)/K |
| `any_error` | Positive after any confirmed error; negative only with complete review and no confirmed/pending issue; otherwise unknown |
| `joint` | Success only when all case items/G03 are Covered and issue review is complete without confirmed/pending error; known failure can coexist with other unknown components |
| `joint_complete_review` | Eligibility for the main descriptive joint proportion; all components final and issue review complete without pending issues |
| Control semantic state | Each flag is positive after a confirmed qualifying issue, negative after complete review without qualifying confirmed/pending issues, otherwise unknown |
| `complete triad` | Same stroke case has complete final case-coverage labels for all three models; G03 and errors are not primary-score eligibility filters |
| `resample_indices` | 20,000 shared participant-resampling rows, columns in sorted complete-case order, seed 20260918; retain the matrix with final analysis artifacts |

Every planned slot must appear in the analysis input. A wholly unavailable report
has no invented coverage or issue ratings; its coverage bounds are [0,1]. The
primary contrast units and matched binary differences are percentage points;
per-report coverage and binomial proportions are on a 0–1 scale. Unknown values
are JSON null, never NaN or numeric zero.

Keep original independent workbook bytes, normalized labels and lock hashes
separate from subsequent discussion and human adjudication records. Agreement
uses only the original independent records. A final consensus importer remains
to be implemented and must require a traceable human decision; choosing one
rater programmatically is not adjudication.
