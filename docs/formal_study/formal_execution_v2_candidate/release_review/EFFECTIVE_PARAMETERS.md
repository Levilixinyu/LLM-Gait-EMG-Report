# Effective formal request parameters

This record describes the existing v2 candidate plan exactly. It supersedes the earlier 8,000-token parameter record for prospective formal generation only. It does not change or authorize the plan.

| Provider | Requested model | Explicit settings |
| --- | --- | --- |
| Anthropic | claude-opus-5 | max_tokens=16000; thinking.type=adaptive; output_config.effort=high; streamed Messages |
| OpenAI | gpt-6-astra | max_completion_tokens=16000; reasoning_effort=high; n=1; stream=true; stream_options.include_usage=true; Chat Completions |
| Google | gemini-3.1-pro-preview | max_output_tokens=16000; thinking_level=HIGH; include_thoughts=false; candidate_count=1; streamed Generate Content |

Google field names are serialized to the corresponding camelCase wire fields. Google automatic function calling is disabled. No tools, retrieval, images, earlier dialogue, expert checklist, reference-card attachment or expert feedback is transmitted. Each request uses the exact saved system and user text for that case. Full serialized request validation occurs before dispatch.

No temperature, top-p/top-k, generation random seed, stop sequence, penalty or response-schema override is supplied. Omitted settings remain provider-managed; omission is not a claim of deterministic output. Sampling controls unsupported by a model are not assigned invented defaults. Model-specific documentation and the original review of omitted parameters are retained in `../../full_length_once_v1/EFFECTIVE_PARAMETERS.md`. No new claims about live provider defaults or pricing are made here.

OpenAI and Anthropic client retries are zero; Google SDK total attempts are one. The formal ledger permits up to three transmitted attempts only for eligible operational failures under the approved protocol, with at most 315 attempts across 105 slots. Each attempt has a 600-second local deadline. Uncertain completion requires review before another request. Captured text, including partial or refusal text, is retained; an empty completed response is terminal. No retry may be used to improve content, length or model ranking. No automatic model fallback is enabled.

The scheduling seed 20260919 controls request order, not generation randomness. The installed SDK versions and exact source hashes are in `../plan.json`. Requested identifiers are aliases, not promises of immutable model weights. Returned identifiers, usage and available request/response metadata are retained. Equal caps and high effort labels do not establish equal computation across providers.
