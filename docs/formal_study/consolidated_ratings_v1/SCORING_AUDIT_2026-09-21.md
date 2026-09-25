# Scoring-material audit — 2026-09-21

The review found **one high-confidence missed-issue proposal**, incomplete control-flag annotations, and unresolved category-tag alignment. It did not establish a new coverage-label error or justify reopening the 16 closed Pending groups. The working scores were not silently changed into new human judgments.

Use [the audit workbook](SCORING_AUDIT_2026-09-21.xlsx) for exact records and response fields. The current full scoring data remain [Consolidated_ratings_working.xlsx](Consolidated_ratings_working.xlsx).

## 1. Missed anatomical-specificity issue

**RDB18B7C593D48194, stroke Sub15, line 6:** `medial gastrocnemius (GAS)`.

Neither saved model prompt supplies a medial-head designation; the reference card also lacks it. All three current issue lists omit this claim. The same unsupported addition in control Sub06, R25F5AA9361D9E14F, was explicitly accepted as E01 by all three raters. Applying the existing source-fidelity rule consistently supports a separate E01 here. It is distinct from the functional-ambulation-band Error and the within-median Pending already recorded for Sub15.

This is an **audit proposal awaiting human recording**, not an additional signed expert decision. The Targeted issue sheet provides one row per reviewer. If confirmed, this adds one group within a report already known to contain an error; its any-error status would stay positive. Do not add three groups because three raters assess it.

## 2. Control flags are incomplete

There are **24 per-rater control issue records with unsupplied pathology and/or normality flags**, covering 20 Error records and 4 Pending records. By reviewer: rater1 2, rater2 1, rater3 21. The 20 confirmed-error records span 13 control reports.

The conspicuous example is the constrained-pelvic-ROM claim in R25F5AA9361D9E14F: rater1 and rater2 record pathology Yes, while rater3's corresponding flag is blank. Agreement on Error does not automatically fill the flag. The Control flags sheet identifies every incomplete record. These blanks must remain unknown or receive explicit supported annotation before the supplementary control outcomes are finalized. They are **not 24 new errors or proof of 24 misjudgments**. A Pending claim does not become a confirmed pathological inference merely because a flag is later supplied.

## 3. Six confirmed groups have different category tags

All three raters agree Error for these claims, but their E-tag sets differ:

| Report | Difference |
| --- | --- |
| R3077041C029681A9 | E07 versus E07;E02 |
| R25F5AA9361D9E14F | E07 versus E07;E02 |
| RE68C712B44209423 | E01 versus E01;E03 |
| R18C0D9D4DF5C8281 | E01 versus E01;E03 |
| REB162D9F656B2188 | E01 versus E01;E05 |
| R0C44EC0AE866FB58 | E01 versus E01;E05 |

This is category annotation, not disagreement about whether the claim is erroneous. Additional E tags never multiply the issue count. Preserve per-rater categories; a final common category-frequency table requires an explicit choice rather than an automatic union, intersection, or majority rule. The Category alignment sheet records these six groups.

## 4. Administrative correction completed

Some preserved discussion reasons contain earlier conditional acceptance or outdated descriptions of peers. The final labels were already correct, but a reader could mistake those old reasons for the latest disposition. The builder and current workbook now add **Final disposition evidence** for all 15 per-rater records belonging to the five explicitly closed Pending claims. This cites the final acceptance register and distinguishes it from historical interpretations. No score, original reason, or signature was changed.

Rater3's latest Sub02 rationale mentions a strict rule. The explicit local Error E03 is retained. That wording alone is not evidence of a new global rule adopted by all raters and is not used to recode D002, D004, D008, or other completed claims.

## 5. Scope, checks and limits

- Reviewed all 552 current coverage rows against the frozen wording/components and recorded explanations, and all 326 current per-rater issue records (193 distinct report-scoped exact quotations).
- Verified 149 included case requirements expand exactly to 447 case rows, with 105 separate G03 rows. Current coverage remains 511 Covered and 41 Partially covered.
- Aligned the existing 153 per-rater confirmed records into 51 claim groups, each with one record from each rater. The repeated ERS assertions in RDBE98A8F7EC455C5 are explicitly linked by source reasons despite different quoted locations. This crosswalk is a technical audit, not a new signed adjudication.
- Checked all 105 saved report files for source identity, registered quotations, numerical tokens and targeted omission patterns. Read the relevant passages and selected complete reports in context. All quoted issue anchors match; the two delivered rater report sets and all 35 system/user/reference-card sets agree byte-for-byte. All 105 reports in the independent template ZIP match these reports.
- Checked original independent records remain preserved. The approved rubric, requirement approvals, D01–D03 clarification, completed rechecks, latest discussion returns, final disposition register and residual replies remain available for tracing decisions.
- Context comparisons did not establish an additional error solely from the words “100%” or boundary continuity. Likewise, the similar-magnitude component of Sub30 R104 exists in the frozen requirements; it was not invented during recheck.
- Existing formal-rating, consensus and analysis tests passed: **35 tests**. These tests do not establish clinical correctness or validate a new three-rater analysis design.

This was an audit of scoring records and model-visible evidence, not a new independent expert rating, a recalculation of raw curves, or proof that every possible report assertion is error-free. Automated whole-corpus screens are not an exhaustive clinical rereading. No answer key was read or model comparison generated during this audit.

The previously identified analysis limitation remains: the old final importer assumes two independent raters plus a third adjudicator, while the actual study used three independent human raters. Document and implement the actual workflow before final import and unblinding; do not present post-discussion agreement as independent reliability.

## 6. Cleanup

Two superseded narrative files were selected for deletion: the accumulated merged-return review narrative and the repeated personal-recheck status note. Their final states are superseded by this audit, the current README and the source-linked disposition records. Exact paths, hashes and reasons are retained in the dated entry of [CLEANUP_LOG.json](../three_rater_discussion_v2/CLEANUP_LOG.json).

Original independent submissions, latest expert replies, necessary intermediate rechecks, approved frozen materials and builder inputs remain retained. Some historical invitation messages are included in frozen manifests or used by the independent-template builder; they were **not** deleted merely because their invitation stage is complete. No report, input, curve, reviewer submission, approval or model mapping was deleted.
