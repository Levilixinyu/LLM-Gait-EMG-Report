# Execution and analysis plan v2: targeted confirmation

Both expert returns have been verified against the unchanged v1 template. Their original proposal fields and the 35-case exposure sheet match; neither reviewer filled the other reviewer's approval or capacity fields. All returned workbook text is English. Rater2's full hash is `ec8698a75a0f0e112d132e9c96a496b7734f8f24b123d459822561d75b34c2be`.

| Item | rater1 | rater2 | Current status |
| --- | --- | --- | --- |
| D02: G03 application | Accept | Accept | Expert acceptance recorded; do not reopen |
| D04: control semantic flags | Revise operational status rule | Accept v1 with contextual notes | Revised section 6 needs both confirmations |
| D07: independent review/adjudication | Accept | Accept | Expert acceptance recorded; retain implementation notes |
| D10: capacity/schedule | Workload acknowledged; availability pending | Accept subject to delivery conditions | Rater1 schedule pending; clarify rater2 delivery condition |
| D01, D03, D05, D06, D08, D09, D11 | Outside scope | Outside scope | Study-lead decisions remain pending |

Rater1's overall decision is Revisions required; capacity and schedule pending. Rater2's is Approve within scope. Observations or no-objection comments outside scope are not statistical, technical or generation approval.

## What changed

Read [PROTOCOL.md](PROTOCOL.md), section 6. It incorporates rater1's complete proposed replacement verbatim:

> Determine each semantic flag separately. A flag is positive once at least one confirmed in-scope issue satisfies its definition, even if another potentially qualifying issue remains pending. A flag is negative only after a complete issue review finds no confirmed or pending issue qualifying for that flag. Otherwise it is indeterminate. A pending issue relevant only to the other flag does not make this flag indeterminate once this flag has been fully assessed.

The previous wording could incorrectly make an already confirmed positive indeterminate. The revision fixes that inconsistency with section 9. It also incorporates rater2's contextual examples: the correct all-seven-below-3.65 displayed comparison alone is not a normality claim, and a question presupposing an unsupported deficit must first be judged under the existing error rules. No new error, penalty or mandatory case requirement is introduced.

Only section 6, the document title/status and a source-link correction changed. Sample, case requirements, primary outcome, statistics, generation parameters, retry rules and blinding paragraphs remain unchanged. The exact changes are in `change_log.json`. This is proposed revised wording, not recorded expert approval of v2.

## Capacity and packet delivery

Rater1 has not promised availability or completion dates. Workload acknowledgment is not a capacity commitment. Complete the Capacity sheet once a real delivery date or a review window relative to delivery can be agreed; Pending remains valid while that information is missing.

Rater2 recorded a proposed start of 2026-09-21 and independent-review completion of 2026-10-02, assuming complete packets arrive by 2026-09-21; later delivery shifts the schedule. Reconciliation is a separate following-week target, originally 2026-10-09. These are rater2's conditional plans, not promised project delivery dates or a commitment on behalf of rater1 or a third reviewer.

Rater2 also used the term case blocks for delivery while accepting that reports for one case are separated by at least two other reports. Please clarify that delivery batches can preserve the fixed interleaved rating order, without presenting the three same-case reports consecutively or as a side-by-side comparison. No new packet ordering has been generated.

## Targeted return

Use [Targeted_confirmation.xlsx](Targeted_confirmation.xlsx):

- **Targeted review:** both reviewers confirm D04; rater2 clarifies the delivery condition.
- **Flag examples:** six illustrative status cases make the revised logic reviewable. They are proposed examples of the same rule, not another error taxonomy.
- **Capacity:** previous responses are shown separately from blank new response fields. Rater1 completes a feasible dated or delivery-relative plan when possible. Rater2 only needs to amend dates if necessary and clarify delivery in Targeted review.
- **Study lead:** seven outstanding study-lead decisions copied from v1; experts need not approve these.

Save separate copies as `Targeted_confirmation_rater1.xlsx` and `Targeted_confirmation_rater2.xlsx`. Preserve the v1 return workbooks. Do not fill another person's fields. The finalized 200 original requirements and 13 addition decisions need no repeat review.

## Messages to send

**To rater1**

> Your D02 and D07 acceptances are recorded. I incorporated your complete D04 replacement verbatim into section 6 of docs/formal_study/execution_analysis_v2_draft/PROTOCOL.md, with the relevant contextual examples from rater2. Please confirm the revised D04 wording and its illustrative cases in Targeted_confirmation.xlsx, or identify any remaining correction. Your capacity remains pending, as requested. Please record a feasible schedule or delivery-relative review window in Capacity when known, distinguishing independent review from reconciliation; no unsupported delivery date or completion promise is requested. Save a separate English return as Targeted_confirmation_rater1.xlsx. No repeat review of finalized case requirements or D02/D07 is needed.

**To rater2**

> Your v1 acceptances and conditional schedule are recorded. Rater1 identified a D04 status inconsistency: a confirmed qualifying issue must make its own flag positive even when another issue remains pending, and the two flags must be assessed separately. The exact replacement and your contextual examples are now in section 6 of docs/formal_study/execution_analysis_v2_draft/PROTOCOL.md. Please explicitly confirm this revised wording and its illustrative cases in Targeted_confirmation.xlsx. Please also clarify that your delivery condition permits batches in the fixed interleaved rater order, with at least two other reports between same-case reports, rather than consecutive same-case comparisons. Your proposed dates remain conditional on delivery; no delivery commitment has been made. Save a separate English return as Targeted_confirmation_rater2.xlsx. D02/D07 and the finalized case requirements are not reopened.

## Accepted implementation notes and remaining scope

D02 applies once per available report for all 35 cases, up to 105 judgments per rater, not just 35 judgments across the batch. Preserve the two substantive G03 meanings and shared-evidence routes. The in-range stroke cases Sub02/Sub16/Sub38 need no duplicate comparability sentence. Control membership/self-exclusion alone does not satisfy G03.

D07 implementation should preserve and lock both complete independent records before cross-review, explicitly distinguish completed-with-issues from completed-with-no-issues, and reconcile the union of issues raised by either rater as well as coverage disagreements. A missing issue in one rater's list is not agreement. Keep originals, quote locations and reasons; record actual final decision makers and dates. Packet contents include exact model input, final case requirements/AND-OR logic and saved report text, with no other-rater or agent review comments. Do not infer that a human third reviewer has already been appointed or that any independent report ratings have occurred.

The [v1 input registry](../execution_analysis_v1_draft/input_registry.csv) and [user exposure attestation](../execution_analysis_v1_draft/EXPOSURE_ATTESTATION.md) remain authoritative source records and are not recopied or altered. `source_review_records.json` preserves the returned cell values; original XLSX files remain primary evidence. `review_audit.json`, `validation.json` and `manifest.json` document checks and hashes.

There is no full plan approval or generation authorization. Effective model settings, the seven study-lead decisions, offline implementation checks and concrete batch release remain separate work. No model API calls were made.
