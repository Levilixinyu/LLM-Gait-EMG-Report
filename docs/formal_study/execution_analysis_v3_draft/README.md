# Execution and analysis plan v3

The study-lead audit changes have been applied and the user's authorization recorded. Both new expert returns were also checked: D04 and the rater2 delivery-order clarification are now closed. Use [APPROVAL_STATUS.md](APPROVAL_STATUS.md) for the current decision state; earlier v1/v2 files remain historical evidence.

- [PROTOCOL.md](PROTOCOL.md): current full plan with the exact D03 and D08 additions and D09 policy replacement.
- [Study_lead_decisions.xlsx](Study_lead_decisions.xlsx): the seven decisions, their actual scope and the conversation-based confirmation source.
- `STUDY_LEAD_CONFIRMATION.json`: explicit user authorization and its limits, translated into English with the original retained in conversation.
- `expert_return_records.json`: cell-value transcription of both original v2 expert returns; original workbooks remain the primary evidence.
- `plan.json`: machine-readable current status, accepted policies and unresolved release conditions.
- `change_log.json`, `validation.json`, `manifest.json`: exact changes, checks and source/output hashes.

The joint-success rule now distinguishes known failure from unknown status even when other components are pending. The response-capture rule accepts attributable saved text independently of clinical quality and prioritizes permanent quota/configuration failures over generic retryable HTTP status codes. The D09 budget paragraph now requires an explicitly verified configuration; no new numerical token allowance or effort setting has been chosen by implication.

No further expert content review is needed for D02, D04 or D07. Rater1 availability has since been confirmed by the study lead as flexible with 24/7 scheduling; no fixed completion deadline is implied. See `RATER1_AVAILABILITY_UPDATE.json`. Concrete provider configuration and implementation readiness remain open. The next technical work is configuration preflight and offline preparation, not re-reviewing the finalized case checklist. Live compatibility checks and formal report generation have not been performed or authorized by this step.

All project artifacts are English. No earlier protocol, expert return, original confirmation workbook, historical report or finalized case requirement was edited. No private model mapping was opened or created.
