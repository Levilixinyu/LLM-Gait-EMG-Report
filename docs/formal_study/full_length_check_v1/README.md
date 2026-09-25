# Representative-length synthetic technical check

Date: 2026-09-18. **Prepared; not authorized and not run.** The earlier short
connectivity check and its authorization are historical, separate records.

Purpose: obtain technical evidence about the proposed 8,000-token allowance
before any formal participant report. Three intended responses use identical,
wholly invented industrial bench-sensor data. No clinical participant, selected
case, expert requirement or previous model output is supplied.

The exact synthetic system/user pair is saved alongside `plan.json`. Its combined
UTF-8 size exceeds 14,000 bytes, compared with 12,126–12,444 bytes for the reviewed
formal inputs. Byte length is not token equivalence, clinical complexity or proof
of equal computational demand. The prompt requests a four-section, 900–1,100-word
English engineering report with numerical findings and explicit interpretation
limits, without copying its audit log.

| Item | Registered proposal |
| --- | --- |
| Intended responses | Three, one per model |
| Models | claude-opus-5, gpt-6-astra, gemini-3.1-pro-preview |
| Inference settings | Same explicit high/adaptive settings as the short check |
| Output allowances | 8,000 each, including reasoning/thinking as registered |
| Attempts | At most three per model, nine total; eligible transient no-text failures only |
| Deadline | 600 seconds per attempt |
| Proposed local reservation budget | USD 4 |
| Reservation estimate | USD 1.008 for one attempt each; USD 3.024 for three attempts each |
| Price/input assumptions | Previously registered rates and 16,000 reserved input tokens per attempt; not invoices or a hard provider billing cap |

## Predeclared interpretation

Check exact task attribution, retained full visible text, normal stream completion,
finish reason, response-model metadata and usage. A token-limit finish does not
pass. Record word count using whitespace-delimited words. Fewer than 900 words
makes representative-length adequacy **inconclusive**, even after normal completion.
A longer complete response can support the technical check. Do not choose settings
by clinical quality, rank models or retry a completed response because it is short,
poor or cautious.

Keep the first captured text, including truncation or refusal. Completed empty
responses are terminal no-report outcomes. Unknown completion pauses for technical
retrieval review. No automatic cap increase, continuation or content-based
regeneration is authorized by this plan. Any changed configuration needs its own
prospective record before further calls. Passing this finite check cannot guarantee
that every formal report will finish within its cap.

## Execution and approval

`authorization_TEMPLATE.json` remains unsigned with `approved = false`. The
existing short-check authorization cannot authorize this different prompt and
budget. No credential is loaded or request sent without an exact-plan authorization.

Read-only verification:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_full_length_check.py check
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_full_length_check.py status
```

After separate user authorization, the concrete entry point is
`scripts/run_full_length_check.py run --live --authorization <approved-record.json>`.
Its raw events go only to `data/compatibility_checks/full_length_v1/`, outside
formal report directories. This check does not authorize the 105-report study.
