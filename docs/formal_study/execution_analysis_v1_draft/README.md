# Execution and analysis review package

The next-step plan is prepared for confirmation. The finalized case requirements remain unchanged. The user's known-external-use check is complete for all 35 selected participants, with no additional use reported and no sample changes.

Read [PROTOCOL.md](PROTOCOL.md), then complete the relevant fields in [Study_plan_review.xlsx](Study_plan_review.xlsx). The workbook contains 11 proposed decisions, explicit responsibility assignments, reviewer capacity and blank approval fields. It does not contain model reports or authorize generation.

## Proposed decisions in plain language

- Primary outcome: how many case-specific required findings each stroke report fully conveys. Give participants equal weight and retain partial coverage as a separate category without assigning half points.
- Correctness: separately report whether a report has any confirmed case error and how many distinct error groups it contains. Do not subtract errors from coverage or invent a combined score.
- Comparison: compare the three models within the same participant; analyze the 25 stroke cases and 10 controls separately. Prespecify interval estimates, three-pair multiplicity and handling of missing outputs.
- Generation: retain the first usable response; allow only capped, logged retries for specified transient technical failures. Poor, cautious or truncated content does not trigger regeneration.
- Review: two independent blinded assessments, followed by documented human reconciliation, with original opinions preserved.

The 105 planned reports require up to 105 report reviews and 552 coverage judgments from **each** rater, plus issue review and reconciliation. Confirm capacity explicitly. The primary denominator excludes common G03, which is assessed separately.

## Who reviews what

The study lead owns D01, D03, D05, D06, D08, D09 and D11 and may request statistical/technical review. Both experts focus on D02 (G03 application), D04 (two control semantic flags), D07 (review/adjudication process) and D10 (capacity). These are new operational choices, not another review of the 200 finalized case rows.

Reviewers should save separate copies, such as `Study_plan_review_rater1.xlsx`, `Study_plan_review_rater2.xlsx` and `Study_plan_review_study_lead.xlsx`. Fill only the decisions within the reviewer's scope; mark other items Outside my review scope if useful. Record actual names and dates. A reviewer must not sign for another person. Unanswered choices remain pending.

## Message to experts

> The prospective case requirements are now finalized, including the R099 correction. Please review the remaining operational items in docs/formal_study/execution_analysis_v1_draft/PROTOCOL.md and record your decisions in Study_plan_review.xlsx. Please focus on D02 (G03 once per report, separate from the primary case-coverage denominator), D04 (the two exact supplementary control flags), D07 (independent review and human adjudication), and D10 (capacity). Each rater would review up to 105 reports and 552 coverage rows, plus issue review and reconciliation. Please confirm a feasible schedule in Capacity, enter your review scope and overall decision, and save a separate English copy as Study_plan_review_rater1.xlsx or Study_plan_review_rater2.xlsx. The finalized case requirements need not be reviewed again. Statistical and generation decisions are owned by the study lead; you may comment without endorsing matters outside your scope. This review does not itself authorize model generation.

## Technical and release status

The input registry binds the 35 selected cases and 149 included requirements to the previously reviewed prompt hashes. Its verification columns distinguish current-byte checks from prior-manifest-only records. Model strings in `plan.json` are historical local candidates, with live availability and exact effective settings explicitly unverified. The current runner requires changes for attempt logging, selective retries, pre-call manifests, first-response retention and complete text-block extraction before formal use.

This stage prepared the plan and review materials only. It did not implement a formal runner, call any model API, create a private blinding key, generate new reports or analyze historical model outcomes. After the remaining decisions are confirmed, implement and test the formal workflow offline, freeze the concrete configuration and obtain the separate batch authorization.

## Records

- [EXPOSURE_ATTESTATION.md](EXPOSURE_ATTESTATION.md) and `exposure_confirmation.json`: the user's known-history attestation, scope and selected-case binding.
- `plan.json`: proposed endpoints, analysis and generation parameters, with approval flags false.
- `input_registry.csv`: 35 cases and source input hashes; not a model answer key.
- `validation.json` and `manifest.json`: package checks, source hashes and output hashes.

Scientific method references are linked in the protocol. They support the cited calculations and implementation conventions, not the unapproved study-design choices themselves.
