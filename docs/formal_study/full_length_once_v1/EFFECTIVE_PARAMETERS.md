# Exact request parameters and omitted settings

Documentation and installed request builder reviewed on 2026-09-18. No request
parameter was changed after viewing the long-check outcomes. This completes the
parameter record; it does not override the failed release check or approve a cap.

| Provider | API route | Explicit generation settings |
| --- | --- | --- |
| OpenAI | Streamed Chat Completions | gpt-6-astra; max_completion_tokens=8000; reasoning_effort=high; n=1; stream=true; stream_options.include_usage=true |
| Anthropic | Streamed Messages | claude-opus-5; max_tokens=8000; thinking.type=adaptive; output_config.effort=high; stream=true |
| Google | Streamed Generate Content | gemini-3.1-pro-preview; maxOutputTokens=8000; thinkingLevel=HIGH; includeThoughts=false; candidateCount=1 |

Each request contains exactly one saved system instruction and one saved user
input. There are no tools, retrieval, images, previous conversations, expert
answers or feedback. The adapter compares the entire serialized request body
against its expected fields before dispatch. Google automatic function calling
is disabled. OpenAI/Anthropic SDK retries are zero and Google total SDK attempts
are one; the one-shot wrapper permits one request per provider. The local
wall-clock deadline is 600 seconds.

No temperature, top-p/top-k override, random seed, stop sequence, frequency or
presence penalty, or response schema is transmitted. These omissions do not imply
temperature zero or deterministic output. Unsupported settings are not assigned
invented numerical defaults.

- OpenAI's GPT-6 guidance identifies temperature and top_p as unsupported; they
  are omitted rather than assigned generic Chat Completions defaults. See the
  [official model guidance](https://developers.openai.com/api/docs/guides/latest-model).
- Claude documents temperature 1 or omission when thinking is enabled and
  restricts nondefault sampling settings on Opus 5. The request omits those
  controls and uses provider-managed sampling. See the
  [API primer](https://platform.claude.com/docs/en/claude_api_primer) and
  [thinking guide](https://platform.claude.com/docs/en/build-with-claude/thinking).
- Google documents temperature 1.0 as the Gemini 3 default. It is omitted in the
  registered request. Other omitted model-specific sampling internals are not
  measured or pinned by this study. See the
  [Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3).

The model strings are the exact tested aliases, not promises of immutable dated
weights. Returned model identifiers and request/response metadata are retained.
Installed versions are bound by the original plan: openai 3.14.1, anthropic 1.6.0,
google-genai 2.23.0, httpx 0.28.1 and httpx2 2.13.0. Provider effort labels and equal
token ceilings do not establish equal computation.
