# Targeted return receipt check

These are submitted personal positions, not a new consensus, a fresh independent rating round, or an import into frozen results. This receipt script does not modify submitted workbooks. Authorized reviewer-name corrections are recorded separately in IDENTITY_CORRECTION_RECORD.json; all judgments and exposure declarations are preserved.

| Item | rater1 | rater2 | rater3 |
|---|---|---|---|
| AG004 | Error | Error | Error |
| AG011 | Pending adjudication | Error | Error |
| AG019 | Error | Error | Error |
| AG023 | Error | Error | Error |
| AG028 | Acceptable | Pending adjudication | Error |
| AG048 | Error | Error | Acceptable |
| AG050 | Pending adjudication | Acceptable | Error |
| AG051 | Error | Error | Error |

## Receipt and attribution

- **rater1:** Read. File: `docs/formal_study/wording_boundary_confirmation_v1/rater1_review_materials/Wording_boundary_confirmation_rater1_completed.xlsx`. Form complete and static template intact: True. Counts: {'Error': 5, 'Pending adjudication': 2, 'Acceptable': 1}. AG023 flag: Yes.

  Completion reviewer field, verbatim: rater1 (human expert reviewer; reviewed and adopted). The reviewer is a human expert. Original ratings were independently made by the reviewer, as confirmed by the study lead. This targeted return records the reviewer's own subsequent judgment; it is not a new initial independent-rating round.

- **rater2:** Read. File: `docs/formal_study/wording_boundary_confirmation_v1/Wording_boundary_confirmation_rater2_completed.xlsx`. Form complete and static template intact: True. Counts: {'Error': 6, 'Pending adjudication': 1, 'Acceptable': 1}. AG023 flag: No.

  Completion reviewer field, verbatim: rater2. The reviewer is a human expert. Original ratings were independently made by the reviewer, as confirmed by the study lead. This targeted return records the reviewer's own subsequent judgment; it is not a new initial independent-rating round.

- **rater3:** Read. File: `outputs/rater3_independent/Wording_boundary_confirmation_rater3_completed.xlsx`. Form complete and static template intact: True. Counts: {'Error': 7, 'Acceptable': 1}. AG023 flag: Yes.

  Completion reviewer field, verbatim: rater3 (human expert reviewer; reviewed and adopted). The reviewer is a human expert. Original ratings were independently made by the reviewer, as confirmed by the study lead. This targeted return records the reviewer's own subsequent judgment; it is not a new initial independent-rating round.

## Remaining differences

- Matching submitted labels: AG004, AG019, AG023, AG051.
- Divergent submitted labels: AG011, AG028, AG048, AG050.
- AG023 control pathology annotation: rater1 = Yes; rater2 = No; rater3 = Yes. This is separate from the Error decision and category tags.

## Handling

Human review and adoption are recorded in HUMAN_REVIEW_CONFIRMATION.json. Do not convert disagreement into a majority decision, force alignment, or treat Pending as an error. Source-specific categories and annotations remain individual. Prior discussion exposure is preserved; these targeted follow-ups must not replace the original independent-rating baseline. No frozen dataset, existing category assignment, control endpoint or model result was changed.

See [submitted positions](Submitted_positions.xlsx) and [machine-readable receipt record](RETURN_CHECK.json).
