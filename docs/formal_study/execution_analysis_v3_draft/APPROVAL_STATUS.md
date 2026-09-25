# Current execution-plan approval status

Recorded: 2026-09-18. The user expressly authorized proceeding with the study-lead audit recommendations. The assistant has recorded that authorization; it has not fabricated an expert signature or a readiness certification.

| Decision | Current authority and scope |
| --- | --- |
| D01 | Study lead accepted as written: primary case-coverage proportion and equal participant weighting |
| D02 | Both experts accepted in v1; common G03 application stands |
| D03 | Study lead accepted with the exact joint-success missingness clarification in the audit, now in section 9 |
| D04 | Both experts explicitly accepted v2 section 6 and F01–F06; no further D04 confirmation required |
| D05 | Study lead accepted the exploratory paired analysis as written, with its stated limitations |
| D06 | Study lead accepted missingness handling, including complete-triad reporting and all-planned-case bounds |
| D07 | Both experts accepted independent review and documented human adjudication in v1 |
| D08 | Study lead accepted with the exact captured-text and permanent-error-precedence clarification, now in section 10 |
| D09 | Study lead accepted the verification policy; specific provider settings, token budgets and account/runtime checks remain pending |
| D10 | Study lead confirms rater1 flexible dates and 24/7 availability. Rater2 accepted conditionally and explicitly confirmed interleaved delivery batches. No rater1 completion deadline is invented |
| D11 | Study lead accepted the readiness requirements; this does not certify completed implementation/testing |

The seven study-lead decisions are recorded in [Study_lead_decisions.xlsx](Study_lead_decisions.xlsx). D09 deliberately records the distinction between approval of a verification policy and approval of a concrete configuration. Do not convert that row to a finalized 8,000-token configuration.

## Evidence

- The user first expressed agreement, requested a critical audit, then replied with the instruction translated as **"Okay, proceed as you recommended."** [STUDY_LEAD_CONFIRMATION.json](STUDY_LEAD_CONFIRMATION.json) records the context, scope and audit hash. Original-language messages remain in the conversation.
- Rater1's v2 return: `../execution_analysis_v2_draft/Targeted_confirmation_rater1.xlsx`, SHA-256 `ac0c00ea71db42d376a4c349b02d249fcebacad35e9f336169c036b413f73d78`.
- Rater2's v2 return: `../execution_analysis_v2_draft/Targeted_confirmation_rater2.xlsx`, SHA-256 `e1d731eab392d5ed5caeeecad43476ca849eb2b4d2422d3a722228cd8e427591`.

Both returns preserve the template's proposal fields, flag examples and Study lead fields. Neither reviewer filled another reviewer's response. Rater1 additionally supplied matching hashes for the reviewed v2 protocol and template. Both D04 responses expressly accept the v2 wording and all six examples. Rater2 expressly explains that case blocks meant delivery batches, not adjacent same-case comparisons. Rater1's original return retained Pending capacity. The later user message confirms flexible dates and 24/7 availability; see [RATER1_AVAILABILITY_UPDATE.json](RATER1_AVAILABILITY_UPDATE.json). This later study-lead information closes the availability question for planning without rewriting the original rater1 return or assigning a fixed completion deadline.

## What remains

1. Prepare and verify the concrete model configurations and a separate synthetic compatibility-check specification, including request fields, exact provider/model identifiers, token limits, SDK retries, timeouts, expected metadata, workload and cost estimate. The historical 8,000 value remains a candidate, not an approved final allowance. No live check has occurred.
2. Implement and verify the formal runner, rating forms and analysis behavior offline under the approved rules. The current historical runner is not certified for this batch.
3. Arrange packet delivery using the recorded availability: rater1 is flexible with 24/7 scheduling, and rater2 retains the existing delivery-relative schedule. Independent records must still be completed and locked before cross-review; neither availability record promises immediate completion.
4. Freeze the resulting ready-to-run package and obtain the separate concrete generation authorization. No formal model call or clinical output generation is authorized by this record.

The finalized case requirements, rubric and model-visible inputs remain unchanged. The filename and retained historical proposal language within the protocol do not supersede this specific approval record. In particular, section 6 is kept byte-identical to the expert-reviewed version; its earlier pending sentence is superseded by the explicit approvals above.
