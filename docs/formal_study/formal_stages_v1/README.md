# Formal generation in three bounded stages

The user accepted proceeding with the presented 16K/high configuration and instructed generation of ten stroke cases first. Only stage 1 is authorized. This is the start of formal generation, not another expendable pilot. All first outcomes count under the approved protocol, regardless of quality.

| Stage | Cases | Report slots | Current authorization |
| --- | --- | --- | --- |
| 1 | First 10 stroke cases in the frozen case order | 30 | Authorized |
| 2 | Next 10 stroke cases | 30 | Not authorized |
| 3 | Remaining 5 stroke cases and 10 controls | 45 | Not authorized |

Stage 1: stroke_Sub27_P, stroke_Sub02_P, stroke_Sub34_P, stroke_Sub15_P, stroke_Sub40_P, stroke_Sub49_P, stroke_Sub16_P, stroke_Sub30_P, stroke_Sub13_P, stroke_Sub22_P. Cohort-qualified identifiers avoid confusion with identically numbered controls.

The partition was recorded before any formal output. At the user's request, the originally interleaved control case blocks are deferred to stage 3. Within each stage and each case, the predeclared order is retained. No case was selected based on an output. All 105 frozen tasks, prompts, model identities, parameters, requirements and analysis rules remain unchanged.

## Scientific interpretation

Splitting delivery or execution into three operational stages does not by itself change the participant sample size or make the three stages independent studies. Each participant receives all three models in the same stage, preserving paired comparisons. Keep configurations fixed and minimize elapsed time between stages because aliases, provider behavior or service conditions may change. Save timestamps, requested/returned model identifiers, usage and technical outcomes. Controls are an exploratory supplement; their later generation is a batch/cohort limitation and should not be interpreted as a causal group difference.

Inspect stage 1 operationally for completion, refusal, truncation, attribution and file integrity. Do not tune prompts or parameters, redraw cases, regenerate weak reports, or stop the study based on apparent model rankings. Any necessary scientific change must be versioned and its consequences for combining batches reviewed explicitly. Do not silently pool differently configured reports. Final analysis uses participants as units under the existing protocol, not batch means, and accounts for incomplete outcomes as already specified.

## Execution boundary and budget

The stage-specific runner uses one formal ledger in `data/reports_formal_v1/`. It preserves the frozen full plan and the existing attempt/resume/import behavior. Each stage requires its own exact authorization and is checked before credentials. The first stage stops at its 30 slots; later stages do not start automatically. The generic whole-batch runner cannot reuse the stage authorization.

Stage 1 reserves $17.04 for one attempt per slot and at most $51.12 for all eligible three-attempt operational retries. The global $120 reservation limit is retained. Reservations use previously registered rates and assumed input allowance; they are not an invoice or an enforceable provider billing cap. Captured text, including truncation or refusal, is retained without quality-based retry. Empty completed responses are terminal. Uncertain remote completion pauses for review; permanent billing/authentication failures stop. No automatic fallback is enabled.

Run the authorized stage only:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_formal_stage.py --stage 1 --live
```

Stage-boundary protections passed eight offline tests, including a complete mock three-stage ledger import. No new live technical test was performed. Stage 1 authorization is recorded in `stage_01/authorization.json`. Historical inputs, results, signed evidence and the full candidate remain unchanged. The latest status entry in the project README supersedes earlier not-started notices without rewriting historical records.

## Stage 1 completed

All 30 formal reports from the first ten stroke cases were retained after exactly 30 requests, with no refusals, token-limit finishes or retry attempts. The runner stopped at the authorized boundary. See [technical results](stage_01/RESULTS.md) and the [researcher-only report index](stage_01/REPORT_INDEX.md). Stages 2 and 3 remain unstarted and require separate authorization. Clinical quality has not been scored by this technical review.

## Stage 2 authorized and completed

The user subsequently instructed starting stage 2. Its separate authorization and completion records are retained under `stage_02/`; the original schedule file records the earlier stage-one-only authorization and has not been rewritten. The second ten stroke cases produced all 30 reports with 30 calls, no refusals, no token-limit finishes and no retries. Across stages 1 and 2, 20 stroke cases and 60 formal reports are now complete. Stage 1 evidence is unchanged. See [stage 2 results](stage_02/RESULTS.md) and the [researcher-only report index](stage_02/REPORT_INDEX.md). Stage 3 remains unstarted and unapproved.

## All formal generation completed

The user subsequently authorized stage 3, which produced its 45 reports. All three stages are complete: 25 stroke participants and 10 controls, 105 reports, 105 requests, no refusals, no token-limit finishes and no retries. See [overall completion](GENERATION_COMPLETION.md) and the [researcher-only full report index](ALL_REPORTS_INDEX.md). Earlier status entries retain their historical context. No further generation is scheduled; independent clinical scoring remains pending.
