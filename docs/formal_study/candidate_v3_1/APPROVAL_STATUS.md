# Interpretation instructions approved as written

Recorded: 2026-09-18
Version: `limited-evidence-v3.1-candidate`

Both rater1 and rater2 approved this revised version as written. All seven required confirmation points were agreed, and neither submission lists a required outstanding revision. This is an administrative status record based on the original submissions and the user's confirmation, not a new expert assessment or signature.

- [Rater1 confirmation](reviews/rater1/rater1_limited-evidence-v3.1-candidate_confirmation.md) and [companion record](reviews/rater1/rater1_limited-evidence-v3.1-candidate_confirmation_record.json).
- [Rater2 confirmation](reviews/rater2_confirmation_limited-evidence-v3.1-candidate.md).
- [Machine-readable approval record](APPROVAL_RECORD.json), including full submission hashes, approved input hashes and verification scope.

The 43 material hashes in rater1's submission match the current files. The five-case package hashes also match. Rater2's SHA-256 is `39806d34015fc3e08287545b43192382fa42f64d34b11dd1f3217a40480d5cd5`, matching the prefix supplied by the user. Original submissions, prompts, cards and numerical summaries were not edited to record approval.

## Scope and historical status records

Approval applies only to the prospective interpretation instructions and their reviewed five-case inputs. It does not approve the final scoring rubric, formal sample, analysis specification or a generation batch, and does not alter historical scores or adjudications.

The README, response-to-reviewers document, candidate validation record and generated card manifest retain their pre-confirmation status as historical reviewed artifacts. Their original hashes are preserved. This later status record supersedes their pending-status statements only for the interpretation-instruction scope; draft checklist items remain unapproved as scoring criteria.

## Non-blocking notes retained for subsequent work

1. Audit counts remain in the approved stroke input. Rater2 suggested moving them to reference notes in a future input version; the as-written approval is not used to silently edit the confirmed inputs.
2. The scoring rubric should credit appropriately supported indeterminate conclusions when the visible references are insufficient. Providing all seven muscle-specific percentiles would change the information available to models and requires a separate version decision.
3. The Sub43 paretic zero-duration event record remains a future eligibility-review issue outside these five cases.

## Technical clarification of the R08 explanation

Rater2's conclusion about rounded 100% coverage is compatible with the approved prompt. However, the explanation that the 3% rule discards short below-threshold dips does not describe the implementation.

In `src/features/emg_signal.py`, coverage is calculated directly from the threshold mask before retained-interval filtering. The duration criterion removes short **above-threshold runs**; it does not fill below-threshold gaps. A synthetic 1001-sample curve with four below-threshold samples has coverage 99.6004%, displayed as 100%. The same gap and retained circular interval persist under 1% and 3% duration rules. This is a rounding example, not a patient finding.

The original expert submission remains intact. Carry this clarification into later rubric discussions rather than attributing a corrected statement to the expert. No change to the approved prompt is needed: its existing wording already requires sufficient evidence before claiming that no below-threshold segment exists.

## Next work

Prepare a prospective scoring rubric for the confirmed instructions: required versus optional findings, coverage categories, treatment of indeterminate conclusions, error definitions, examples and duplicate handling. Submit that rubric for expert confirmation separately. Formal generation remains unauthorized.
