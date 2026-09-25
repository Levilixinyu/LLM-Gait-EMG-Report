# OpenAI follow-up after restored credits

The user reported that credits were available and the OpenAI-only synthetic
follow-up succeeded on 2026-09-18. All three requested models now have a successful
synthetic API compatibility response.

The registered amendment authorized one additional OpenAI request within the
original lifetime attempt and USD 3 budget limits. The model, prompt and generation
parameters were identical to the initial check. The original three-slot journal,
its credit failure and its closed slot remain unchanged. Claude and Gemini were
not called again.

| Check | Result |
|---|---|
| Requested / returned model | `gpt-6-astra` / `gpt-6-astra` |
| Stream completion | Complete; finish reason `stop` |
| Visible text | 404 characters |
| Input tokens | 111 |
| Output tokens | 219, including 111 reasoning tokens |
| Token cap reached | No |
| Additional requests | 1 |
| Combined requests across both checks | 4: three successful responses and one original credit failure |

At the prices registered in the plan, this successful OpenAI response costs an
estimated USD 0.012060. All three successful responses total an estimated USD
0.030221. These are token-based estimates, not invoices; the initial rejected
OpenAI request returned no usage and its billed amount remains unverified.

Evidence and provenance are recorded in
[OPENAI_CREDIT_FOLLOWUP_RESULTS.json](OPENAI_CREDIT_FOLLOWUP_RESULTS.json) and
[the amendment authorization](OPENAI_CREDIT_FOLLOWUP_AUTHORIZATION.json). Raw
events are retained in `data/compatibility_checks/openai_credit_followup_v1/`.
Three offline tests verified that the follow-up cannot silently redispatch after
success, completed empty output or interruption.

This is a connectivity and capture check, not a clinical quality comparison.
The 105-report formal experiment has not started. Final configuration and token
allowance, formal execution readiness, blinded rating delivery and analysis
validation remain separate work. A short synthetic response does not establish
that an 8000-token cap is adequate for the full gait inputs.
