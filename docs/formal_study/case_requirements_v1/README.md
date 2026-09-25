# Final case requirements v1

The prospective case-specific requirements for 25 stroke participants and 10 healthy controls are finalized from both reviewers' documented confirmations. All 200 original candidate rows, 13 addition rows and eight shared topics have decisions; no item remains unresolved.

Open [Final_case_requirements_v1.xlsx](Final_case_requirements_v1.xlsx). **Included requirements** contains the 149 included requirements. **Omitted candidates** preserves the 64 excluded candidates for traceability; they carry no omission penalty. **Shared rules** records the eight agreed interpretation rules, and **Case summary** gives the per-case counts. Apply the previously approved rubric v2 and its common requirements separately.

These are requirement counts, not reports, independent observations, or an approved weighting scheme. The 35 cases do not all have the same number of included requirements. Optional assertions remain subject to correctness review even when their omission carries no coverage penalty.

## Evidence and exact change

The source consensus workbook remains unchanged at SHA-256 `caffdccafbbb8665481dbf2899c71817e3320ff27caa8afee989134cece769ac`.

The confirmation chain consists of:

1. The two discussion replies, covering eight shared topics, 23 original rows and all 13 additions.
2. Rater1's version-specific confirmation of 176 remaining original rows as written.
3. Rater1's exact R099 replacement, explicitly accepted by rater2 in [RATER2_R099_CONFIRMATION.md](../case_review_reconciliation_v1/RATER2_R099_CONFIRMATION.md), SHA-256 `14a3512a27131d3d2f398ee7bbb5602e0772f1f1ba98b7b84514305ef450b03e`.

R099 (stroke_Sub29_P, N03) is the only substantive change from the source consensus. Its BF reference-deviation route requires muscle, direction and approximate location. Its alternative RF threshold-coverage route requires muscle, approximate coverage and boundary spanning. One complete route suffices; the latter route does not inherit the former's direction/location components. The final wording and components reproduce the accepted passages exactly.

All other 212 original/addition rows preserve the source decisions, wording and components. The presentation removes superseded discussion notes from the operational workbook; original opinions and replies remain in [the reconciliation directory](../case_review_reconciliation_v1/). The final workbook is an administrative compilation, not a new expert signature.

## Files and verification

- `case_requirements.csv`: all 213 decisions, final text, inclusion status and confirmation evidence filenames. Filter `included=Yes` for case-specific coverage requirements.
- `shared_rules.csv` and `case_summary.csv`: agreed rules and per-case counts.
- `change_log.json`: the exact before/after R099 text and administrative changes.
- `summary.json` and `validation.json`: final status and verification results.
- `manifest.json`: source and output SHA-256 hashes and the finalization script hash.

Verification checked the reviewed source version, all 176 accepted rows, the explicit discussion reply chain, the exact R099 acceptance and input evidence, preservation of every other row, saved workbook/CSV agreement, English text and unchanged source hashes. No raw dataset analysis or model generation was performed.

This version was produced by `scripts/finalize_case_requirements.py`. The script refuses to overwrite an existing finalized directory. Future substantive changes require a new version and the appropriate expert confirmation; do not edit this version in place.

## Next work

The case-requirement review is complete. Participant exposure confirmation, outcomes and scoring aggregation, statistical analysis, and generation/retry/failure rules still need to be resolved before the planned 105-report batch. This requirements approval does not itself approve those decisions or authorize generation. Approved input instructions, the general rubric and historical ratings remain unchanged.
