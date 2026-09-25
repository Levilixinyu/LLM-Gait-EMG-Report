# Formal rating and analysis: offline workflow checkpoint

Date: 2026-09-18. The new formal rating and analysis components passed synthetic
checks. **This is not a formal batch release. No participant reports or expert
ratings were created in this checkpoint, and no model API was called.**

The approved scientific decisions remain in
[execution plan v3](../execution_analysis_v3_draft/APPROVAL_STATUS.md). All 70
reviewed system/user prompt hashes were verified. Case membership, 149 included
requirements, expert decisions, historical reports, and completed compatibility
check evidence are unchanged. No archived original or historical private model
mapping was opened.

## Implemented

`src/eval/formal_rating.py` creates a separate opaque ID for every planned report,
keeps captured report text byte-for-byte, and retains explicit no-report slots.
Short, truncated, malformed and refusal responses are not filtered out. Provider
metadata and independently generated order seeds stay in the private folder.
Each rater gets a separate fixed order with at least two intervening reports
between reports for the same case. Self-identifying prose is not rewritten;
reviewers record incidental unblinding.

The Excel workbook has Instructions, Review, Coverage and Issues sheets, with
dropdowns and frozen requirement text. For this roster it has 105 Review rows
and 552 Coverage rows per rater: 447 case requirements plus 105 G03 assessments.
The administrative missing-output record is separate from expert content labels.
Reviewers save a separate completed copy. The return validator checks identity,
unchanged requirement membership, completion, pending reasons, issue references,
exact report quotations, and explicit reviewer completion. It cannot verify a
reviewer's identity or clinical correctness.

Independent returns are saved as byte-exact new snapshots with hashes. Neither
can overwrite the other or replace a previous locked return. The cross-review
gate requires both intact snapshots. Pending judgments remain pending. This is
an integrity and workflow mechanism, not a cryptographic human signature or an
externally anchored tamper-proof store.

`src/eval/formal_analysis.py` implements:

- Fixed case denominators, equal participant weights, and no half-credit for
  partial coverage. G03 remains separate from the primary denominator.
- A shared complete-triad stroke sample, 20,000 paired resamples with seed
  20260918, sorted cohort-qualified case IDs, BCa 95% and 98.3333% intervals.
  The resample matrix is returned for retention by the eventual analysis runner.
  Degenerate intervals remain unavailable; there is no fallback method switch.
- All-planned-case missingness bounds, including entirely unavailable reports.
- Confirmed unique issue groups, pending issues, error flags and joint-success
  states under the exact known-positive/known-negative/unknown rules.
- Separate control semantic flags, exact binomial intervals, and zero-event
  one-sided upper bounds. Controls are not pooled across models as independent
  participants. Matched binary contrasts remain descriptive.
- Original independent agreement by cohort and by case coverage/G03, plus
  completed report-level error agreement. Consensus labels are not used to
  measure independent agreement. Independent assessment objects can also use
  the same outcome engine for the prespecified sensitivity descriptions.

## Verification

[The rehearsal record](offline_rehearsal.json) contains source/evidence hashes,
workload counts and exact remaining release gates. The 105-slot rehearsal uses
fictional placeholder reports and software-generated fixture labels, explicitly
marked as synthetic. It deliberately includes one unavailable stroke output:
the paired primary sample becomes 24 complete triads, while all 25 planned stroke
cases remain in missingness accounting. Temporary synthetic workbooks and keys
are removed after the rehearsal. No fixture is an expert opinion or study result.

[The test record](validation_record.json) and [test output](test_results.xml)
cover new components and historical blinding/packet-selection regression tests.
The BCa implementation is checked against SciPy on a nondegenerate known fixture;
the zero-event interval is checked against its closed-form value. This verifies
implementation behavior, not a new independent statistical review.

Reproduce from the project root:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/verify_formal_rating_analysis.py
/Users/lixinyu/.venvs/gait-emg/bin/python -m pytest -q tests/test_formal_analysis.py tests/test_formal_rating.py tests/test_blinding.py tests/test_packet_selection.py
```

## Remaining release work

1. Finalize the output allowance and complete effective provider parameter
   record. See [configuration review](CONFIGURATION_REVIEW.md). The short live
   checks do not establish adequacy for full reports.
2. Complete the formal live runner and freeze its 105-slot schedule, exact task
   hashes, code versions, durable attempt accounting and cost limits. The
   completed synthetic-check runner remains restricted to its original tasks.
3. Integrate terminal generation evidence with the packet builder, checking task
   attribution and supplying only verified review assets. Test full real-asset
   delivery, including curves and approved references, before releasing packets.
   The current 105-slot rehearsal uses placeholder assets; it is not that check.
4. Add the final human-consensus/adjudication importer with explicit provenance.
   The current workbook importer is for original independent reviews only.
   Record technical delivery, format, truncation/refusal and incidental unblinding
   separately in the final analysis export; the estimand engine does not infer
   these from report prose.
5. Present the resulting concrete ready-to-run package for the separate formal
   generation authorization. Do not infer it from permission for synthetic tests.

The clinical rubric and case requirements do not need another expert approval
merely because these software components were added. No final scores, model
rankings or clinical performance claims are available before generation and
human review.
