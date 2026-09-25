# Formal execution candidate and integration checkpoint

Date: 2026-09-18. **Prepared and verified offline; no formal generation is
authorized or started.** This package completes the execution-ledger, real-asset
packet and human-final-decision import components that were outstanding at the
[previous workflow checkpoint](../workflow_readiness_v1/README.md).

## Concrete proposed batch

- 25 stroke cases plus 10 controls, three model configurations, 105 fixed slots.
- Exact reviewed system/user text, cohort-qualified case IDs, reference metadata,
  source hashes and installed SDK versions in `plan.json`.
- Case-block order randomized with seed 20260919. Across 35 blocks, five of the
  six provider permutations occur six times and one occurs five times. Each
  provider appears in each within-block position 11 or 12 times. Scheduling does
  not inspect output content. Rater order is a separate private randomization.
- The proposed settings remain the previously tested identifiers/high effort
  settings and 8,000-token allowances. **Output allowance and the final effective
  parameter record are not yet approved.** Do not treat this file as D09 approval.
- At most three transmitted attempts per slot, 315 total; 600 seconds per attempt.
  Hidden SDK retries remain disabled. Recognized transient no-text failures use
  the approved 5/30-second backoff and longer Retry-After rules. Uncertain remote
  completion requires retrieval review. Permanent quota/billing failures stop.
- Proposed conservative reservation: USD 35.28 for one attempt at every slot,
  USD 105.84 if every slot uses three attempts, and a proposed USD 120 local
  reservation ceiling. These calculations use rates registered on 2026-09-18 and
  an assumed 16,000 input tokens per attempt. They are not invoices, current
  account-balance checks or enforceable provider billing caps. No money was spent
  at this checkpoint, and this proposed budget has not been approved.

The unsigned `authorization_TEMPLATE.json` is a template, not permission. It
requires exact plan identity and named, hash-verified release evidence. Credentials
are not read before the appropriate live authorization checks. The new synthetic
length check has a separate scope, directory, budget and authorization.

## Execution and review behavior

`src/llm/formal_batch.py` uses the actual provider adapters and acknowledged
pre-dispatch persistence already tested in the synthetic checks. A ledger verifies
its existing hash chain once under the batch lock and appends atomically, avoiding
a full reread of every earlier stream event on every new fragment. Resuming does
not reset attempts, cost reservations or terminal outcomes.

The terminal importer requires all 105 slots, including explicit no-report
outcomes. It checks task attribution, attempt sequence, terminal state, agreement
between captured text and stream/retrieval evidence, and first-response retention.
Pauses and unstarted positions prevent premature packaging. Short, truncated,
malformed and refusal text is retained without a content-quality filter.

`src/llm/formal_release.py` verifies and supplies five named assets per case:
the two exact prompts, reference card, EMG curve PNG and kinematic curve PNG.
All 175 assets are checked against the reviewed manifest. Both rater packets also
contain the approved rubric, examples, rubric approval status and common rules.
The legacy five-case annex is explicitly distinguished from the final requirements
in the new Coverage sheet. No entire source folder, candidate case-review form or
private mapping is copied to a reviewer.

The full-roster rehearsal used 104 explicitly synthetic report texts and one
synthetic no-report outcome, with all real current review assets. It produced
105 Review rows and 552 Coverage rows for each rater and then removed the temporary
packets. None of the fixture text or labels is a clinical model output or expert
opinion.

`src/eval/formal_consensus.py` accepts submitted final decisions only after both
independent submissions are locked. It requires an exact final-dataset hash and
an authority covering each report: either both original raters' confirmations,
or a named third human adjudicator with prior discussion evidence. Evidence files
are hash-checked and retained byte-for-byte. The software does not authenticate a
human identity or create a signature or judgment. Pending final labels remain
pending and follow the approved missingness rules.

The resulting restricted analysis export retains final outcomes, original
independent agreement, both raters' sensitivity analyses, three saved resample
matrices, human evidence and source hashes. Format, incidental unblinding and
technical generation metadata remain separately available. These exports include
model mappings and must never be sent as independent rater materials.

## Commands

From the project root, these commands are read-only:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_formal_batch.py check
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/run_formal_batch.py status
```

The CLI also provides separately guarded `run --live --authorization`, `recover`,
`package`, `lock-review` and `import-consensus` commands. `prepare` cannot overwrite
a prepared or started plan. Review commands require actual submitted material;
they must not be used to manufacture completion.

For importer details, see [human final-decision schema](HUMAN_FINAL_DECISIONS.md).
Automated results and exact source hashes are in `validation_record.json` and
`test_results.xml`. Historical compatibility plans and previous checkpoint
artifacts remain unchanged.

## Remaining decisions

The [representative-length synthetic check](../full_length_check_v1/README.md) is
prepared but not authorized. After its results, document the output allowance,
provider-managed omitted settings and alias limitations, then confirm the exact
formal configuration, reservation budget and release evidence. Finally obtain
the separate 105-slot generation authorization. No new expert review of the
already approved case requirements is needed for these implementation checks.
