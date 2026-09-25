# Formal execution candidate v2: 16,000-token output allowance

The study lead approved a common output allowance of 16,000 tokens on 2026-09-18. The active formal runner now prepares and validates this version. All 105 slots retain their reviewed input bytes, model identifiers, schedule, high reasoning settings and other request parameters. Historical 8,000-token plans and results remain unchanged.

| Provider | Request field | Value | Reasoning setting |
| --- | --- | --- | --- |
| Anthropic | `max_tokens` | 16000 | Adaptive thinking, high effort |
| OpenAI | `max_completion_tokens` | 16000 | High effort |
| Gemini | `max_output_tokens` | 16000 | HIGH thinking |

The allowance includes reasoning/thinking and visible output. This change has been verified offline only. It does not guarantee complete output and does not resolve the prior Claude classifier refusal.

## Budget and authorization

Using the previously registered rates and a 16,000-input-token reservation per attempt, the estimated reservation is $59.64 for one attempt across all 105 slots and $178.92 if every slot uses all three permitted attempts. These are planning reservations, not measured consumption or an invoice.

The existing candidate ledger limit remains $120. It cannot fund the full $178.92 reservation; if retries exhaust available reservation, the runner must pause under its existing budget policy. No higher spending limit has been approved. The three-attempt limit permits only eligible operational retries, never retries to improve report quality.

Only the output-allowance release item is confirmed here. The authorization template remains unsigned (`approved: false`). No additional paid check, provider-support message or formal generation is authorized by this amendment. The Claude refusal remains unresolved; there is no recorded acceptance of that risk. The completed full-length check remains unsuccessful for Claude and Gemini.

## Records and verification

- `provider_configuration.json`: current formal request configuration.
- `plan.json`: all 105 tasks and current source hashes.
- `CAP_CHANGE_RECORD.json`: scope of user approval and unchanged historical file hashes.
- `validation_record.json`: offline comparison against the previous candidate.
- `provenance/formal_release_v1.py.txt`: inert snapshot of the previous builder; provenance only, never an input or runnable configuration.

The builder source changed, so reconstruction of old hash-bound synthetic plans against current code will intentionally fail. Their recorded evidence and original hashes have not been rewritten. Do not rerun completed checks or use an old authorization with this new candidate. Existing software validation remains historical evidence; this amendment checks the parameter-only task change without making API calls.
