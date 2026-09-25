# Final single-attempt length check: completed, formal release on hold

Three API requests were made on 2026-09-18, exactly one per provider. There were
no automatic retries, continuations, substitute models or additional checks.
The original unexecuted nine-attempt proposal remains unchanged; the subsequent
user-authorized one-attempt amendment governed this run.

| Model | Words | Finish reason | Output allowance consumed | Technical length result |
| --- | ---: | --- | ---: | --- |
| GPT-6 Astra | 984 | stop | 2,297, including 848 reasoning tokens | Passed |
| Gemini 3.1 Pro Preview | 554 | MAX_TOKENS | 7,996: 7,248 thought + 748 visible tokens | Failed: cap exhaustion and incomplete output |
| Claude Opus 5 | 0 | refusal | 0 output tokens | Failed: empty API classifier refusal |

The cap was 8,000 for each model. The minimum 900-word criterion and normal
non-token-limit completion requirement were registered before calls. A completed
HTTP stream does not mean that its report completed normally. Gemini's partial
text and Claude's empty refusal are preserved as received.

Claude's raw `message_delta` records `stop_reason=refusal` with
`stop_details.category=cyber`. There were no text content blocks to extract.
The fictional bench-sensor task contains no request for cyber exploitation;
this appears to be a possible classifier false positive, but that inference is
not a provider-confirmed diagnosis and does not establish how clinical inputs
would behave. It is not evidence of an adapter dropping report text. The provider
documents this response shape as an API classifier refusal in its
[refusal documentation](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback).

At the previously registered rates, expected charges are approximately USD
0.250667: Gemini 0.101912 and GPT 0.148755, including the reported GPT cache writes.
Claude returned 4,645 input tokens in usage, but the cited provider documentation
says refusals before any output are not billed. These are documented-rate
estimates, not verified invoices; a usage-only calculation before that exception
would be USD 0.273892. The USD 4 reservation was not exhausted.

The proposed 8,000-token formal configuration has **not passed** the length check.
Do not label all three models ready or start the formal batch under that claim.
No formal participant report has been generated. No clinical quality comparison
or model ranking was performed here.

[RESULTS.json](RESULTS.json) records returned metadata, refusal details, estimates,
source hashes and the terminal journal head. Raw stream evidence remains in
`data/compatibility_checks/full_length_once_v1/`. The two earlier connectivity
packages remain historical. Across those checks and this one there have now been
seven transmitted requests in total; this is not seven successful reports.

This is the historical check result. Subsequent authorized configuration changes and completed generation are recorded in the [formal generation completion](../formal_stages_v1/GENERATION_COMPLETION.md). The obsolete next-step proposal has been removed; original request evidence is retained.
