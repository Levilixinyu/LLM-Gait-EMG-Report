# Approved clinical-content probe: completed

Purpose: **Test whether real research content is affected.**

The single authorized Claude request completed on the previously tested stroke Sub09 paretic-side case using its expert-approved v3.1 system and user inputs, unchanged. This case is outside the formal 25-stroke sample and is distinct from control Sub09. The response is retained verbatim in [REPORT.md](REPORT.md).

| Item | Observed result |
| --- | --- |
| Model | claude-opus-5 (requested and returned) |
| Output cap | 16000 tokens |
| Reasoning | Adaptive thinking, high effort |
| Finish reason | end_turn |
| Visible word count | 1958 whitespace-delimited words |
| Input tokens | 4396 |
| Output tokens, including thinking | 5646 |
| Thinking tokens reported | 1116 |
| Token-limit termination | No |
| Refusal | No |
| Requests | 1 Claude request |
| Automatic retries / fallback | 0 / 0 |
| Other-provider requests | 0 |
| Registered-rate cost estimate | $0.16313; not an invoice |

Response ID: `msg_011CfBovoG5bsbyEwekLMNfW`.
Request ID: `req_011CfBovnaAAVNQNjhwDcPMQ`.

## Interpretation and scope

The earlier empty synthetic refusals do not reproduce on this one approved clinical input. This is evidence of successful technical completion for this input at the chosen configuration. It does not identify the cause of the synthetic refusals, establish success on every study case, validate clinical accuracy, or compare models. No clinical-quality acceptance filter was applied.

This output is a separate technical probe and must not replace the historical pilot report, enter formal ratings or analysis, or count toward the planned 105 formal reports. No new formal participant has been exposed. Historical refusals, reports, expert decisions and the formal configuration remain unchanged. This authorization does not approve a formal batch or any additional test.

Exact prompts, hashes and configuration: `plan.json`. User authorization: `authorization.json`. Raw stream and dispatch evidence: repository directory `data/compatibility_checks/claude_clinical_probe_v1/`. `RESULTS.json` binds the verbatim report and evidence hashes.
