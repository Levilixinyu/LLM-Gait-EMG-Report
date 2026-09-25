# Live synthetic compatibility results

Historical initial-run record. The later
[OpenAI credit-restoration follow-up](OPENAI_CREDIT_FOLLOWUP_RESULTS.md) succeeded;
all three models now have successful synthetic responses. The initial results
below remain the record of the original three requests.

All three planned slots were checked on 2026-09-18 after explicit user
authorization. Two returned complete responses. OpenAI failed because the
project's API credential had no remaining credits. Three requests were
dispatched in total, with no retries. No formal participant reports were generated.

| Provider / requested model | Result | Finish reason | Reported token usage |
|---|---|---|---|
| Anthropic / `claude-opus-5` | Text and metadata captured | `end_turn` | 163 input; 336 output, including 21 thinking |
| OpenAI / `gpt-6-astra` | Permanent credit failure; no report | HTTP 429 | No usage returned |
| Google / `gemini-3.1-pro-preview` | Text and metadata captured | `STOP` | 105 input; 94 visible output; 634 thinking |

Neither successful response reached the token cap. The returned model identifiers
matched the requested identifiers. This establishes basic request compatibility
and stream capture for Claude and Gemini under these synthetic inputs; it does
not establish adequacy of the 8000-token cap for formal gait reports. OpenAI model
access and parameter compatibility remain unverified because the request was
rejected for credits.

The OpenAI error body reported `type: insufficient_quota` and
`code: credit_balance_exhausted`. The runtime stopped the batch as prescribed.
An automated technical review recorded `close_no_report` for that slot, preserving
the original stopped decision and raw error, then resumed the same run to execute
the independently planned Gemini request. No OpenAI retry, model substitution,
input change, count reset or clinical adjudication occurred. See
[technical closure](recovery_openai_credit_balance.json).

Using returned usage and the rates registered in `plan.json`, the two successful
responses cost an estimated USD 0.018161 combined (Claude: USD 0.009215; Gemini:
USD 0.008946). Gemini thinking tokens are included; Claude thinking is already
included in its output-token count. This is an estimate, not an invoice. The
rejected OpenAI request returned no usage, so its billed amount is not verified.

The next dependency is restoring OpenAI API credits for the credential actually
used by this project. A follow-up OpenAI-only compatibility check should be
registered as an explicit bounded amendment. Do not reopen the terminal failed
slot or regenerate the successful Claude/Gemini responses.

The complete operational evidence remains in the Git-ignored directory
`data/compatibility_checks/synthetic_v1/`. [LIVE_RESULTS.json](LIVE_RESULTS.json)
records the outcomes, authorization and evidence hashes. The original offline
validation record remains a pre-call checkpoint; its earlier zero-call and
pending-authorization statements do not describe the current live outcome.

Formal configuration freeze, blinded delivery and analysis readiness remain
separate. This test does not authorize the 105-report formal batch.
