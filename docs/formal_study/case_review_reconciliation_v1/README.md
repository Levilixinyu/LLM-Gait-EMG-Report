# New-case requirements reconciliation

Status: both independent review workbooks have been received and checked. Final case requirements await documented expert consensus. This package covers 25 stroke participants and 10 healthy controls; it contains no generated model reports.

Open [Case_requirements_reconciliation.xlsx](Case_requirements_reconciliation.xlsx). Repeated questions appear first in **Shared questions**. Both original opinions and comments are preserved. Agent discussion advice is explicitly labeled and is not an expert decision.

## What was received

| Return | Retain | Modify | Omit | Complete decisions |
| --- | ---: | ---: | ---: | ---: |
| rater1 | 49 | 91 | 60 | 200 |
| rater2 | 110 | 27 | 63 | 200 |

Both returns preserve the template's case records and the six original requirement fields. Every modification has replacement wording; reviewer and date fields are populated. No Chinese text or formulas were found in either workbook. The 178 source hashes supplied by rater1 match current files. Rater2 did not supply an equivalent provenance sheet; no such verification is attributed to rater2. Evidence for all 13 rater1 additions and 10 rater2 additions matches the corresponding model input text.

Original returns remain in `../case_review_v1/Expert_case_requirements_review_rater1.xlsx` and `../case_review_v1/Expert_case_requirements_review_rater2.xlsx`. Their full SHA-256 hashes are in [summary.json](summary.json). Independence is stated by the reviewers, not independently witnessed by this administrative check.

## What needs discussion

| Comparison | Original items |
| --- | ---: |
| Both retain the original | 47 |
| Both omit the original | 52 |
| Both include a requirement, but wording/components need alignment | 82 |
| Disagree whether a requirement should be included | 19 |

These are mechanical comparison counts, not inter-rater reliability or signed consensus. Retain comments can qualify a requirement. Both Modify can mean different muscle identities, required directions, or AND/OR routes. Even the 99 matching retain/omit decisions require confirmation of their comments and final scope.

There are also 13 case-level addition rows: ten control-provenance proposals raised by both reviewers, and three CCI proposals raised only by rater1. Entries saying None or None proposed are not additions.

The eight shared topics are:

1. EMG priority: under rater2's choices, seven complete-EMG controls have no required EMG item. Agree whether that is intended. The pooled p95 endpoint 4.61 should not silently become a universal content-priority or matched-control cutoff.
2. Joint findings: agree which joints are essential, which are alternatives, and when a GVS-versus-excursion contrast is required.
3. EMG components: agree muscle identities, directions, locations and one-versus-two finding routes. For example, stroke Sub34 N04 differs substantively despite both reviewers including an item.
4. Threshold coverage: decide the three specific N05 proposals for stroke Sub10, Sub13 and Sub24.
5. CCI additions: decide TA-GAS in stroke Sub25/Sub33 and RF-BF in stroke Sub40. Input support does not automatically make a finding mandatory.
6. Control GPS-like: resolve four inclusion disputes and avoid duplicate mandatory content under N01 and N02.
7. Control provenance: confirm shared wording for all ten controls, including separate conditional branches for speed, cadence and the task-specific step index.
8. Component precision: distinguish mandatory findings from optional numerical anchors and contextual caveats. Do not turn review heuristics into new clinical thresholds.

These are discussion proposals within the already approved input and rubric framework. They do not revise historical ratings or authorize a new global scoring rule.

## How experts complete the workbook

1. Read **Read first**, then discuss **Shared questions**. Record an agreed rule, confirmer names and date. If unresolved, say so explicitly rather than implying agreement.
2. Use **Priority items** to navigate the 19 inclusion disputes. Click the comparison-row link to edit the authoritative row in **Full comparison**.
3. Use **Wording alignment** for the 82 items needing alignment. Read both comments as well as replacement wording. Then confirm the scope of the remaining 99 rows.
4. Resolve the 13 rows in **Additions**. If one common rule applies to all ten controls, record its topic identifier and explicitly confirm its application in each affected row.
5. In **Full comparison** and **Additions**, fill the blue final-decision fields. For an included requirement, write the complete final core and its mandatory components, AND/OR routes and optional anchors. For an omitted requirement, record the reason. Record supporting consensus evidence, the actual confirmer names and confirmation date. Use Pending discussion where agreement has not been reached.
6. Save a new copy as `Case_requirements_reconciliation_consensus.xlsx`. Preserve both independent returns and this blank discussion master. Do not sign for another reviewer. If decisions are confirmed asynchronously, cite the actual confirmation record.

The navigation tabs are not additional places to enter decisions. A shared-topic decision guides case decisions but does not silently finalize them. All consensus fields are intentionally blank in this package.

## Message to send to both experts

> Thank you for completing the independent review of the 35 new cases. Both returns have been checked and preserved. Please use `docs/formal_study/case_review_reconciliation_v1/Case_requirements_reconciliation.xlsx` for the consensus discussion. Start with Shared questions, where repeated issues have been grouped into eight topics. Then resolve the 19 inclusion differences, align the 82 included requirements with differing wording/components, confirm the remaining original items, and decide the 13 addition rows. Enter final case decisions only in Full comparison and Additions. Please distinguish required components from optional anchors and state any AND/OR alternatives explicitly. Record actual confirmer names, dates and consensus evidence, and save a new copy as Case_requirements_reconciliation_consensus.xlsx. Agent advice is a discussion aid; it is not an adjudication. This review concerns prospective case requirements only and does not approve historical changes, study outcomes, analysis, sample exposure status or model generation.

## Audit and next gate

`source_returns.json` is a faithful cell-value transcription of every returned worksheet, not a new expert assessment. The comparison CSVs are machine-readable views of this discussion master. The original XLSX files remain the primary evidence.

`manifest.json` records the source and output hashes. Available non-visual package files and the review-provenance sources were checked. HTML/PNG/PDF assets were not rehashed for this administrative comparison, and additional iCloud placeholder files were skipped in the package sweep; their prior manifest hashes are recorded separately, not presented as fresh verification. Source workbooks and the actual input text used for addition checks were read and verified. No images were regenerated or historical reports changed.

After documented consensus is returned, validate it and freeze the new-case requirements. External case-exposure confirmation, outcome/analysis decisions and generation/retry/failure rules remain separate outstanding work. The planned 35 participants x 3 models = 105 reports have not been generated by this step.
