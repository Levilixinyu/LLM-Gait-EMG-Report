# Technical evidence review for formal release

Status: Evidence review completed; overall formal generation authorization is pending. The word reviewed means the evidence has been assessed, not that every model passed an identical live test at 16K.

| Evidence | Observed result | Meaning for this release |
| --- | --- | --- |
| Earlier short synthetic connectivity and OpenAI credit follow-up | All three providers produced a complete response across the registered calls | Account/route compatibility was observed at those times; current balances are not certified |
| One-shot long synthetic check at 8K | GPT: 984 words and normal completion; Gemini: 554 words and MAX_TOKENS; Claude: empty cyber refusal | Preserve all results; this was not a three-model long-output pass |
| User-authorized cap change | All 105 candidate tasks now use 16K with otherwise unchanged parameters and inputs | Cap approval and offline configuration evidence only |
| Claude-only synthetic follow-up at 16K | Another empty cyber refusal | Increased allowance did not resolve that synthetic-input refusal |
| Claude-only expert-approved clinical Sub09 probe at 16K | 1958 words; end_turn; 5646 output tokens including 1116 thinking; no refusal or truncation | Demonstrates technical completion on this previously exposed pilot case, outside the formal sample; no clinical accuracy assessment |

## Proposed release decision

Proceed without another paid technical test if the study lead approves the concrete plan, budget and the following limitations. This is a proposed operational decision, not a fabricated expert approval or a claim that all checks succeeded.

- Gemini has not been live-tested at 16K. Its earlier 8K truncation remains a known observation; 16K may still truncate.
- OpenAI completed the 8K long synthetic check; no separate 16K live check was performed.
- Claude completed one approved clinical input at 16K. The cause of its two synthetic refusals remains unconfirmed; refusals on other inputs remain possible.
- Every formal outcome is retained under the approved first-response and missingness rules. Failure, empty output, refusal, partial output or truncation is not grounds for quality-based regeneration or substitution.
- No model, reviewed input, sample, rubric or analysis rule is changed. This probe is excluded from formal analysis, and clinical quality remains for independent human review.

Sources: `../../compatibility_check_v1/OPENAI_CREDIT_FOLLOWUP_RESULTS.md`, `../../full_length_once_v1/RESULTS.json`, `../../claude_16000_followup_v1/RESULTS.json`, `../../claude_clinical_probe_v1/RESULTS.json`, `../validation_record.json`.

No new paid request was made during release preparation. This evidence review does not authorize generation.
