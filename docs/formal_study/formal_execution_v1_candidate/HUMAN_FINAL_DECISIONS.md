# Human final-decision import contract

The future final submission is an English JSON record prepared from the actual
discussion/adjudication returns. An agent may format an authorized human decision,
but cannot create the decision, identity attestation or signature itself. Do not
fill a final submission now: no formal reports have been independently rated.

Top-level fields:

- `independent_submission_sha256`: the locked original workbook hashes for
  `rater1` and `rater2`.
- `final_review`: `review`, `coverage` and `issues` rows using the same field names
  as the validated independent JSON. Retain every report and frozen requirement.
  The text of required wording/components is unchanged. Unknown/Pending coverage
  needs a reason. Issues need applicable categories, exact retained-report quotes,
  locations, reasons and properly scoped control flags.
- `authorities`: one or more entries whose `report_ids` together cover each report
  exactly once. Each entry binds `final_review_sha256` to the canonical digest of
  the entire final-review object. A scoped confirmation therefore identifies both
  its report subset and the exact full dataset it accompanies.

An authority with `kind = two_rater_consensus` contains two `confirmations`, one
for each original rater. Their names must match the submitted independent review
records. An authority with `kind = third_human_adjudication` contains one named
`third_reviewer` confirmation and a `prior_discussion` evidence record. The third
reviewer must differ from both independent raters. Third-reviewer authority does
not require the original raters to agree with that adjudicator's decision.

Every confirmation records `role`, `name`, `confirmed_at` in ISO 8601 format,
`human_confirmation = true`, `confirmation_source`, `evidence_file` and
`evidence_sha256`. The true flag describes an existing documented human action;
it is not permission for an agent to invent one. The prior-discussion record
contains `evidence_file` and `evidence_sha256`. Named evidence files must be inside
the submitted evidence directory; retain exact original bytes.

The importer validates structure, scope, quotes and recorded hashes. It cannot
independently authenticate a signature or decide whether a clinical interpretation
is correct. A human confirmation of a dataset with Pending items acknowledges
those unresolved states; it does not silently resolve them.

Both independent snapshots remain unchanged. Final analysis and separate
independent sensitivity/consistency outputs are placed in the private final
consensus directory. Existing imports cannot be overwritten. The final artifacts
include the resample matrices themselves, their hashes, human evidence copies
and an explicit count of zero automatically created adjudications.
