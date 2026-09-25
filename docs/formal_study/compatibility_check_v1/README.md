# Three-model synthetic API compatibility check

Current status: all three models now have a successful synthetic response.
The initial run returned Claude and Gemini responses plus an OpenAI credit
failure. After the user reported restored credits, a registered OpenAI-only
follow-up succeeded. Combined total: four requests, three successful responses,
one preserved credit failure and zero formal participant reports. See the
[current follow-up results](OPENAI_CREDIT_FOLLOWUP_RESULTS.md) and
[initial-run results](LIVE_RESULTS.md). This is the concrete check contemplated by execution
plan v3 [section 10](../execution_analysis_v3_draft/PROTOCOL.md#10-generation-configuration-and-retry-policy).

## Proposed scope for authorization

- Three intended responses: one each from `claude-opus-5`, `gpt-6-astra`, and
  `gemini-3.1-pro-preview`, using the same fixed fictional bench-sensor input.
- Candidate high reasoning settings and the historical 8000 total-output-token
  cap, as listed in `plan.json`; no tools, images, selected participant data,
  expert checklists, feedback or previous conversation.
- At most three attempts per slot and nine HTTP dispatches in total, including
  any documented recovery retries. One process at a time; 600 seconds per attempt.
- Proposed USD 3 token-cost budget. Conservative reservation estimate: USD
  2.205 if every allowed request is billed at its full output cap plus the
  input allowance. This is not an account-level billing cap or tax-inclusive quote.
- No model substitution, prompt revision, cap increase, continuation or
  replacement because an answer is empty, truncated, refused or undesirable.
- This authorization would cover only these synthetic requests. It would not
  authorize any of the 105 formal report slots or freeze the study configuration.

The exact synthetic system/user text, model parameters, code hashes, package
versions, call limits and cost reservations are in `plan.json`. The runtime
reconstructs this plan before execution and rejects any mismatch. The selected
35 participants are never loaded by this command.

## Cost basis checked on 2026-09-18

| Model | Standard input / million | Output / million | Reserved cost per attempt | Maximum three attempts |
|---|---:|---:|---:|---:|
| Claude Opus 5 | $5 | $25 | $0.210 | $0.630 |
| GPT-6-astra | $10 | $50 | $0.425 | $1.275 |
| Gemini 3.1 Pro Preview | $2 | $12 | $0.100 | $0.300 |

Each reservation includes 2000 input tokens and 8000 output tokens, including
reasoning/thinking. OpenAI's reservation uses its higher $12.50 input cache-write
rate as a conservative allowance. At one attempt per model the reservation is
$0.735; at three attempts per model it is $2.205. Actual usage will be recorded
when returned. Unknown usage after a failed request does not refund a reservation.
Account-specific pricing, taxes and provider billing records can differ.

Sources: [OpenAI model pricing](https://developers.openai.com/api/docs/models/gpt-6-astra),
[Claude Opus 5 pricing](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5),
[Gemini standard pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-pro-preview).

## Execution and authorization

`authorization.json` records the user's actual authorization (`approved: true`),
its source and date, the exact plan hash, nine maximum dispatches and the USD 3
budget. The assistant transcribed that decision; it is not an expert signature.
The run is now terminal. The commands below document the registered workflow;
resuming this same run does not issue replacement requests for its closed slots.

Read-only checks, from the project root:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_compatibility_check.py check
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_compatibility_check.py status
```

Only after that specific authorization is recorded:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_compatibility_check.py run --live
```

The live output directory is fixed at `data/compatibility_checks/synthetic_v1/`
and is excluded from Git. It contains the immutable run manifest and append-only
evidence journal, plus derived `last_summary.json` and `technical_results.json`.
There is no command-line option to create a fresh live output directory to reset
the attempt count. Mock runs use temporary directories and cannot populate this
live directory. Credentials are read only after authorization, from environment
variables or the project `.env`, and are never written to the plan or journal.

Before every HTTP dispatch, the isolated worker sends the parent a task-bound
reservation request. The parent writes and fsyncs it before acknowledging it;
only then may the worker send HTTP. This is a conservative reservation, not
proof that the remote provider received the request. It closes the unsafe gap
where an unrecorded request could be silently reissued after a crash. The
transaction cannot guarantee exactly-once execution across a remote service.

## Recovery procedure

1. Inspect `status` and the local journal. Preserve every file. A timeout or
   interrupted request with no text pauses the batch; it does not automatically
   issue another request. Completed empty responses and captured partial text
   are terminal and cannot be reopened for a better answer.
2. First resume to recover any already-journaled text or completion event after
   a persistence interruption. This issues no replacement for that slot.
3. For a genuinely unresolved slot, inspect the request/response IDs, captured
   metadata and provider error payload. Use a documented provider retrieval
   route if it supports this exact request. These registered synchronous calls
   do not automatically create a retrievable job; do not invent a retrieval
   endpoint, enable storage retroactively, or treat a request ID as a response.
   No retrieval API call is implemented or automatically sent by this check.
4. Record the technical review in an English JSON file inside this package.
   Required fields are `slot_id`, `task_sha256`, current `journal_head`, `reviewer`,
   `reviewed_at`, `evidence_note`, `confirmation_source`, and `action`. State
   whether retrieval was supported and what was actually checked. Technical
   operator review is separate from clinical expert adjudication.
5. Choose one action: `attach_response` preserves an attributed raw response;
   `close_no_report` records the unresolved slot without generating another;
   `retry` requires a confirmed transient cause, a recorded retrieval review,
   a valid `retry_not_before` Unix timestamp, and remaining lifetime attempts.
   An uncertain retry is explicitly marked as a possible duplicate. Permanent
   errors and an exhausted attempt budget cannot be reopened for retry.
6. Apply the local decision, then resume the same run:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_compatibility_check.py recover --decision docs/formal_study/compatibility_check_v1/recovery_decision.json
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_compatibility_check.py run --live
```

The named recovery file above is an example path, not a pre-approved decision.
`retry` also requires `confirmed_transient: true` and `retrieval_status` set to
`not_supported_for_registered_request`, `checked_no_text`, or `checked_unavailable`.
`attach_response` requires `raw_response` and `response_attribution_verified: true`;
the text is derived from that raw response, not entered separately. Known
response IDs must match. A stale journal-head reference is rejected. Recovery
does not reset the original call or budget limits, and its command makes no
network request.

## What this check can establish

`technical_results.json` records parameter acceptance or errors, actual response
model and IDs, usage, finish reason, visible-text capture, truncation and stream
completion. It does not score arithmetic accuracy, clinical quality or model
rank. An empty/truncated response is evidence to retain, not permission to retry.

Success on this short synthetic request establishes basic connectivity and
capture under the tested configuration. It does not establish that the token
cap is adequate for longer gait inputs. Any additional configuration check or
different cap needs its own recorded plan before formal generation. The formal
configuration, blinded delivery and analysis validation remain separate work.

Offline validation is recorded in `validation_record.json` and `test_results.xml`.
