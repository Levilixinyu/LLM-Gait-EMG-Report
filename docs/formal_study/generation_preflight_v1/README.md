# Formal generation: offline preparation

Status on 2026-09-18: input verification, synthetic execution-policy tests and
three-provider SDK integration against mocked HTTP completed. No model API
calls were made during that offline checkpoint. The later authorized live check
initially returned two responses and one OpenAI credit failure. The registered
OpenAI follow-up subsequently succeeded after restored credits; see
[the current results](../compatibility_check_v1/OPENAI_CREDIT_FOLLOWUP_RESULTS.md). This package does not freeze provider
settings or authorize a compatibility check or the 105-report formal batch.

The approved scientific and operational decisions remain in
[execution plan v3](../execution_analysis_v3_draft/APPROVAL_STATUS.md).
Both experts' clinical decisions and rater availability remain recorded there;
this engineering work does not require a new clinical review.

## Files and scope

- `provider_candidates.json`: explicit proposed request parameters, official
  documentation links and outstanding configuration checks.
- `task_inventory_DRAFT.json`: 105 planning slots (35 participants times three
  models), bound to the 70 exact reviewed system/user prompt hashes. The roster
  preserves group and side; `stroke_Sub01_P` and `control_Sub01_avg` are different
  cases. This inventory cannot be executed by the offline runner and is not the
  final frozen execution manifest.
- `offline_validation.json`: roster, requirement counts, SDK versions and
  verified evidence hashes. There are 149 case requirements, yielding 447
  case-specific coverage rows plus 105 G03 rows per rater.
- `test_results.xml`: automated failure-mode and historical regression results.
- `validation_record.json`: test counts, file hashes and outstanding release gates.
- `change_log.json`: successive engineering checkpoints and earlier validation
  hashes; these are technical records, not new expert approvals.

Reproduce input verification from the project root:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/prepare_formal_generation.py
```

Reproduce the focused tests:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python -m pytest -q tests/test_formal_providers.py tests/test_formal_generation.py tests/test_generation_cache.py tests/test_provider_metadata.py
```

## Configuration findings

| Provider | Candidate identifier | Proposed explicit reasoning setting | Historical cap to check |
|---|---|---|---|
| Anthropic | `claude-opus-5` | Adaptive thinking; high effort | `max_tokens=8000` |
| OpenAI | `gpt-6-astra` | `reasoning_effort=high` | `max_completion_tokens=8000` |
| Google | `gemini-3.1-pro-preview` | `thinking_level=HIGH` | `max_output_tokens=8000` |

High effort across providers is a proposed configuration choice, not a measure
of equal computation. GPT-6-astra documents support for high reasoning effort;
this package does not infer its default effort. See the
[OpenAI model page](https://developers.openai.com/api/docs/models/gpt-6-astra).

Claude Opus 5 enables adaptive thinking by default and supports an explicit
adaptive setting. Its token cap includes thinking and visible text. See
[Opus 5 behavior changes](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5)
and [effort settings](https://platform.claude.com/docs/en/build-with-claude/effort).
OpenAI's completion cap also includes reasoning tokens. See the
[Chat Completions reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).
Gemini 3.1 Pro defaults to high thinking and its cap includes thought tokens;
exhaustion during thinking can leave an empty response. See
[Generate Content thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking).

Consequently, 8000 is not a guaranteed visible-report allowance and has not been
approved for the formal batch. Account access and sufficient budget have not
been checked. Candidate aliases do not guarantee an immutable model snapshot.
Sampling defaults and exact effective request parameters still need a complete
record before configuration freeze.

The local SDK inspection found `openai 3.14.1`, `anthropic 1.6.0`, and
`google-genai 2.23.0`, with `httpx 0.28.1` and `httpx2 2.13.0`. The Google SDK's `HttpRetryOptions.attempts` describes a
total-attempt count, defaulting to five; setting it to one disables its retries.
The OpenAI/Anthropic client setting is `max_retries=0`. Real SDK calls against
mocked HTTP verified a single dispatch on 429, 503 and transport timeout, for
each provider. A transport guard also blocks an unexpected second dispatch.
Redirects are not followed.

## Implemented and tested

`src/llm/formal_generation.py` is an isolated, offline reference implementation.
It accepts only built-in synthetic transports and rejects live/formal execution.
Fixtures can replay normalized events or exercise actual SDKs against mocked
HTTP inside the deadline worker. Neither path loads real credentials.

The tests exercise pre-attempt manifest persistence, an exclusive batch lock,
append-only records with hash chaining, a persistent three-attempt ceiling,
5/30-second backoffs, Retry-After pauses, permanent-error precedence, preserved
partial/refusal/truncated text, terminal empty responses, interrupted-attempt
recovery, and refusal to supersede a changed manifest or corrupted journal.
All visible text blocks are retained by provider response extractors; thinking
blocks are excluded from the report. A separate process implements the local
wall-clock deadline, tested using stalled HTTP streams through each actual SDK.

`src/llm/formal_providers.py` implements streamed Messages, Chat Completions and
Generate Content requests. It requires an explicitly supplied credential and
HTTP transport; it does not load `.env` or create a batch. Every normalized event
records the task hash, response metadata, safe response headers and effective
wire-body hash. The final usage chunk is consumed before declaring completion.
Empty completed responses are distinguished from an unexpected end of stream.
Unknown quota payloads pause; recognized billing/daily/zero-limit failures stop.
Local termination is not proof of remote cancellation or remote non-completion.

Mock integration revealed two local SDK compatibility issues, now handled:

- Anthropic 1.6.0 requires an `httpx2.Client`; an `httpx.Client` fails before
  dispatch. A small bridge preserves the common counted HTTP transport and
  closes the underlying response on completion or error.
- Google 2.23.0 emitted nested `thinking_level`/`include_thoughts` keys in this
  path. The adapter normalizes those two aliases to the documented JSON spellings
  `thinkingLevel`/`includeThoughts`, rejects conflicts and verifies the complete
  effective request before dispatch. This observation does not establish whether
  the live API accepts the original aliases. Automatic function calling is
  explicitly disabled.

These findings came from installed SDK source/signatures and actual mock HTTP
requests. Stream parsing also follows the official
[OpenAI request reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create),
[Anthropic streaming guide](https://platform.claude.com/docs/en/build-with-claude/streaming),
and [Gemini error guide](https://ai.google.dev/gemini-api/docs/troubleshooting).
The tests prohibit real socket connections and use fixed fake keys. Process
fixtures hardcode a mocked transport and a fake key.

Captured text has no clinical-quality acceptance filter. Empty completed
responses do not trigger retries. Uncertain interrupted attempts pause for
technical recovery; the attempt budget is not reset. Attempts are conservatively
reserved before transmission, so a crash before dispatch may leave an ambiguous
reservation requiring review. Hash chaining detects altered records and interior
gaps, but is not an externally anchored tamper-proof audit system.

Historical runners and completed outputs are unchanged. In particular, their
old truncation/cache rules are not imported into this formal reference logic.

## Remaining work before a live check or formal release

1. The [synthetic compatibility package](../compatibility_check_v1/README.md)
   now supplies a concrete live entry point, exact-plan authorization check,
   acknowledged durable dispatch reservation, fixed call/cost limits and local
   recovery workflow. These passed offline tests and the user subsequently authorized the synthetic
   check. Its current outcomes are linked above. Formal 105-slot execution remains
   a separate release.
2. After that separate authorization, run the three fixed synthetic requests.
   Evaluate parameter acceptance, finish/usage metadata and capture only; do not
   select settings by clinical report quality or model ranking. Retain every
   check and document any configuration change before formal generation. A short
   connectivity check does not establish token-budget adequacy for formal cases.
3. Freeze the complete configuration and execution manifest, including effective
   defaults, SDK/code/input/reference hashes and snapshot or alias limitations.
4. Complete blinded delivery, independent-rating lock and analysis tests, then
   record the separate authorization for formal generation.

This package establishes input identity and offline behavior through the
provider SDK/HTTP boundary. It does not establish live account access, adequate
token allowances or completed validation of clinical scoring, blinding or
statistical analysis.
