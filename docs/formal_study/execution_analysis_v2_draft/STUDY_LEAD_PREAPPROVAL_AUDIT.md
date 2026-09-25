# Audit of the seven study-lead decisions

Audit date: 2026-09-18. Scope: the current v2 protocol, its seven Study lead rows, relevant local generation code and official API/statistical documentation. This is agent advice, not an expert signature, a statistical certification or a generation authorization.

The user stated that they had read and agreed with the seven decisions, then explicitly requested a critical review of whether all should be accepted. That expressed agreement is preserved in the conversation. No approval cells were changed during this audit, and the proposed clarifications below are not silently represented as user-approved revisions.

## Recommendation

The overall design is suitable for the stated resource-limited, exploratory comparison. Do not interpret blanket agreement with its principles as evidence that provider configuration or operational readiness has been verified. Four decisions can be accepted as written within their stated scope; two benefit from explicit implementation definitions; the concrete D09 configuration should remain open until it is actually specified and checked.

| Decision | Audit recommendation | Reason |
| --- | --- | --- |
| D01: primary outcome | Accept as written | Full case-coverage proportion with equal participant weights and a fixed case denominator is explicit. It measures completeness, not overall clinical quality. Preserve separate partial/not-covered descriptions. |
| D03: correctness and secondary outcomes | Accept the outcome choices; clarify joint-outcome missingness | Separate error groups from coverage. Define the AND-based joint outcome explicitly rather than relying on an analogy to the OR-based any-error flag. |
| D05: paired analysis | Accept as an exploratory prespecified analysis | Preserve case pairing, three-comparison adjustment, small-sample limitations and the existing no-interval rule for degenerate BCa calculations. More resamples do not create more participants or validated power. |
| D06: missingness | Accept as written with the required reporting | Complete-triad estimates are conditional on evaluability. The all-planned-case bounds and explicit failure accounting are essential, not optional. Do not call the complete-triad subset the whole 25-case result when data are missing. |
| D08: generation/retries | Accept the principles; clarify response eligibility and error precedence | Usable must mean administratively captured text, not good content. Permanent quota/billing failures must override generic HTTP retry rules. Implement the existing no-regeneration policy consistently. |
| D09: provider settings | Accept the model-comparison objective; do not freeze the concrete settings yet | Official model identifiers exist, but account access, effective reasoning settings, operational token allowance and runtime behavior have not been verified. An 8,000-token cap is not an 8,000-token report allowance. |
| D11: readiness/release | Accept as a release requirement | This approves checks that must be performed; it does not state that those checks passed or that the existing runner is ready. |

## D03: make the joint outcome explicit

The protocol's secondary joint measure requires every case requirement Covered, G03 Covered and no confirmed case error. Section 9 correctly defines an any-error flag, then asks for analogous treatment of the joint measure. An OR-based error indicator and an AND-based success indicator have different truth conditions. The complete-review point estimate can remain as specified; all-planned-case bounds should use this explicit classification.

Proposed addition:

> For the secondary joint-success indicator, classify success only when all included case requirements and G03 are finally Covered and the completed issue review contains no confirmed or pending in-scope error. Classify failure when at least one requirement or G03 is finally Partially covered or Not covered, or when a confirmed in-scope error exists, even if another component remains unresolved. Otherwise classify the joint indicator as unknown. An unavailable report is unknown, not a confirmed failure. Preserve the complete-review denominator for its main descriptive point estimate and use these known/unknown states for all-planned-case bounds.

Examples: an unequivocal confirmed error makes joint success false even if another coverage item is pending. In contrast, an apparently complete report cannot be called jointly successful while a potentially qualifying error remains unresolved. This clarification changes no expert error definition or required report content.

## D08: define capture, not quality

Proposed addition:

> A usable captured response means non-whitespace report text attributable to the correct frozen task and retained with its raw response or stream evidence. It does not require all four sections, successful clinical interpretation or a normal finish reason. Preserve any recoverable partial text and do not discard it to obtain a replacement. A completed response with no report text is a terminal no-report outcome. Where no report text was captured, classify provider error codes and payloads before applying the HTTP retry list: authentication, unsupported parameters/models and permanent quota/billing errors stop the batch even if a response also has a generally retryable status code. Uncertain transient classification pauses for documented technical review rather than triggering an automatic content-selection opportunity.

The current local runner still catches every exception for retry. It writes its task manifest after processing, and the Anthropic adapter selects only the first text block. Those already documented gaps remain implementation work, not evidence that a formal batch failed. A hard per-attempt deadline must also stop/record an attempt; merely setting a socket read timeout is not necessarily the same thing. No code was changed or API test run in this audit.

## D09: budget and effective model configuration

The requested model names were found in official documentation: [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), [Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5) and [Gemini 3.1 Pro Preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview). This documents model identifiers; it does not verify this user's account entitlement, quota or exact server behavior.

The OpenAI Chat Completions `max_completion_tokens` allowance includes reasoning and visible output, as documented in the [official API reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create). The locally installed OpenAI SDK parameter description states the same distinction. Thus the current 8,000 value is not a guaranteed visible report length.

Claude Opus 5 has adaptive thinking enabled by default, with thinking consumption included in its `max_tokens` allowance. Its effort setting affects reasoning behavior. These facts are documented on the [official Opus 5 page](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5).

Gemini's `max_output_tokens` allowance also includes thought tokens, and reaching that hard limit can leave truncated or empty visible output. The [official thinking documentation](https://ai.google.dev/gemini-api/docs/generate-content/thinking) distinguishes the allowance from the thinking setting.

Inference for this study: equal numerical limits do not establish equal computational effort, equal visible output opportunity, or freedom from budget-induced truncation. This is a reason to verify the configuration before freezing it, not proof that 8,000 is inadequate or that a particular higher number will solve the problem. The v2 text already acknowledges unequal budgets; the missing part is an operationally verified configuration.

Recommended replacement for the budget-selection paragraph:

> Before formal generation, register each provider's exact model identifier or available snapshot, API route, reasoning/thinking configuration, output-token allowance and its documented semantics, timeout, SDK version and effective retry settings. Set reproducible request parameters explicitly where supported; where a setting is omitted, document the provider default and its verification date. Provider effort labels are not assumed to represent equal compute. Treat the existing 8,000 value as a historical candidate until a predeclared configuration check supports the intended evaluation. Use only synthetic material outside the selected 35 cases for any separately authorized live compatibility check; assess successful response capture, token-limit/finish behavior and parameter compatibility, not clinical answer quality or model ranking. Freeze all settings before formal case outputs, and do not change settings or regenerate reports in response to formal result quality.

No particular new cap, effort level or model substitution is selected by this audit. A configuration check needs a defined task set and acceptance rule before calls. Passing a small synthetic check reduces obvious implementation risk; it cannot prove that no formal report will truncate. Once the batch is frozen, faithfully captured truncation remains an outcome under D08.

## Statistical interpretation limits that are already handled

The paired case-level bootstrap and explicit multiplicity family are reasonable design choices for this exploratory comparison, not a guarantee of exact coverage with 25 cases. [SciPy's documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) explicitly describes paired index resampling and undefined BCa intervals for degenerate data. The protocol already retains these limitations and avoids changing interval methods after inspecting favorable results; no new fallback test is recommended here.

The primary coverage outcome can be high in a report with an unsupported assertion. That is why D03 must remain visible beside D01 in every model comparison. A model should not be called generally better at clinical interpretation solely because it has the largest coverage estimate. The sample does not establish clinical validity, equivalence or population-wide superiority; no approval of these seven rows should expand the stated research scope.

## What this review does and does not close

The sample, confirmed requirements and expert-approved D02/D07 process are not reopened. The proposed D03/D08 wording is an administrative analysis/execution clarification, and D09 requires a concrete configuration rather than a new 200-row expert review. Existing expert D04 and capacity follow-ups remain separate; this audit does not substitute for their replies.

No original protocol, confirmation workbook, source report, expert return or approval status was edited. The study lead's expressed agreement remains recorded in the conversation; the present review recommends limiting any formal approval to its actual scope and recording material amendments separately before release.
