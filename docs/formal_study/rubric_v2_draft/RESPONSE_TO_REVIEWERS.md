# Response to both rubric reviews

Original version: `rubric-v1-draft-for-limited-evidence-v3.1`
Revised version: `rubric-v2-draft-for-limited-evidence-v3.1`
Status: **revised draft; both reviewers must confirm.** This response is agent-authored, not a joint consensus or a new expert statement.

Both source workbooks record Revisions required. Their exact bytes remain unchanged. Rater1 entered 5 Accept/3 Revise policies, 18 Accept/2 Revise case rows, 9 Accept definitions and 21 Accept/3 Revise examples. Rater2 entered 8 Accept policies and 19 Accept/1 Revise case rows; definition/example feedback is in comment columns rather than formal decision columns. Those comments, including E02's requested revision, have been preserved without manufacturing decision cells.

Full source hashes and literal response fields are in [source_review_records.json](source_review_records.json). Rater2's SHA-256 is `4aefb1a1e7d76dab12b45f715b2ea5365f5b36816710ddc743624c2eadf7d99e`, matching the reported prefix.

| Change | Source | Revision and review location |
|---|---|---|
| V2-01 | Rater1 P02; rater2 P02 | Distinguish unavailable/corrupt materials from actual short/truncated captured output. Score assessable output and omissions; no automatic Cannot assess or new exclusion. RUBRIC 1–2, P02, X38. |
| V2-02 | Rater1 P02/C04; rater2 P02 | Wrong-only components earn no credit; partial requires another substantive component. Names alone are not meaningful partial coverage. P02, X07/X26/X39. |
| V2-03 | Rater1 P06 | Explicit correct-then-wrong, wrong-only and retraction rules, plus separate pending coverage adjudication for ambiguity. RUBRIC 3, P06, X25–X27/X41. |
| V2-04 | Rater2 P04 | Sub50's no-matching statement can satisfy both its C01 component and G03's comparability half. No second sentence is required; inference limitation remains necessary. P04. |
| V2-05 | Rater1 P07; rater2 P07/E01/E09 | Enumerate design scope; split mixed design/case claims; metric-identity errors remain E01. RUBRIC 9, P07, X28–X29. |
| V2-06 | Rater2 P06 | Merge the same assertion repeated as a presupposition in follow-up questions, retaining both locations. P06, X36. |
| V2-07 | Rater1 Sub09 C04 and X04 | Define each numerical route and interval route; exact numerical repetition/locations optional for C04. Separate standardized magnitude from above-mean direction in X04. Names alone Not covered. |
| V2-08 | Rater1 Sub50 C02; rater2 accepted the same intended three components | Make all three AND components explicit, including the GVS-versus-small-excursion contrast; exact numbers alone remain optional. Revised C02 and X40. |
| V2-09 | Rater2 Sub50 SL01; rater1's comment supports the same interpretation | Remove a mandatory negative disclaimer. Require index/near-zero meaning; separately assess unsupported whole-gait generalization. Revised SL01, E07, X30–X31. |
| V2-10 | Both on Sub49 C06; rater1 P03 | Conditional missingness applies per discussed domain, not as an all-fields inventory triggered by one topic. C06 and P03. |
| V2-11 | Rater1 X11/X15/X16/X18–X20 | Identify case-specific examples; X15 is Sub05 TA, X16 refers to the supplied maximum-z location, not an invented interval. Clarify optional comparisons versus full requirement coverage and ambiguous missing-activity language. |
| V2-12 | Rater2 E02/X24 | Add written degree-word, explicit severity-grade and statistical-significance rules. Anchored descriptive wording can be acceptable; unanchored/ambiguous degree words remain pending for adjudication, not automatically errors. RUBRIC 7, E02, X32–X33/X37/X42. Requires renewed expert confirmation. |
| V2-13 | Rater2 E05/X15/X24 | Add normal-phasing control error, prohibited onset companion to the allowed boundary example, and whole-gait symmetry generalization. X31/X34/X35. |
| V2-14 | Rater2 P05 optional suggestion; rater1 P05 | **Not adopted in this draft:** a fixed +/-2-percentage-point or nearest-5% tolerance. The existing no-universal-tolerance approach is retained; disputed cases go to adjudication. Rater2 labelled the suggestion optional and no joint agreement supports a numeric rule. Both reviewers can explicitly request one on return. |

## Remaining confirmation points

The important new choices are factual-contradiction handling, actual incomplete-output handling, the mixed-claim scope boundary and degree-word examples. Source acceptance of other rows does not approve these additions automatically.

X32 uses an explicitly reference-anchored descriptive meaning of moderate, not a validated severity class. Please confirm that distinction or propose narrower wording. X33 deliberately remains Pending adjudication. X42 distinguishes an explicit unsupported validated severity grade from informal emphasis. Clinical significance and statistical significance are not inferred from a word alone.

For Sub50, “small step-length difference under this definition” is a legitimate scoped description; the new error example explicitly says **overall gait symmetry**. This avoids turning every mention of step symmetry into an automatic error.

No v3.1 model input, historical score, prior review or generation setting was changed. This revision does not approve weights, sample size, analysis or a formal batch.
