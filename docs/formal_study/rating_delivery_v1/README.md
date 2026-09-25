# Formal independent-rating delivery

Status: Original blank delivery packets are retained. Both human experts have submitted their independent ratings; completed workbooks are stored separately in the rater folders.

## Files to send

| Recipient | Send only this archive | Reports | Coverage rows |
| --- | --- | --- | --- |
| Rater 1 | [Formal_review_rater1.zip](Formal_review_rater1.zip) | 105 | 552 |
| Rater 2 | [Formal_review_rater2.zip](Formal_review_rater2.zip) | 105 | 552 |

Each reviewer extracts the entire archive, opens `START_HERE.html`, reads `HOW_TO_REVIEW.html`, and fills a separately saved copy of `Independent_ratings.xlsx`. The offline browser pages show one report at a time with its exact model inputs, final case requirements, reference context and curves. They do not store ratings. All project and packet text is in English.

The workbook contains Instructions, Review, Coverage and Issues sheets with dropdowns. Review contains 105 report rows. Coverage contains 447 case-specific rows plus 105 G03 rows. All human-judgment and completion fields are blank; Review starts at Not started. Expert requirements are fixed text, not scores.

Each rater has a separately randomized fixed order. Same-case reports are separated by at least two other reports. Opaque report IDs are shared between raters to support later reconciliation, but there is no shared visible model code. Do not give an expert the other expert's packet or the researcher-only report index.

## Returning the review

Rater 1 returns `Independent_ratings_rater1_completed.xlsx`; rater 2 returns `Independent_ratings_rater2_completed.xlsx`. The name/date/completion fields are completed by the actual reviewer after independent review. Pending adjudication can remain documented. Preserve original submissions and lock both independent records before sharing judgments or starting discussion. A material problem must be documented and repaired without changing the report content.

The completed-review invitation was removed during documentation cleanup. Packet instructions and original submissions remain unchanged. See the [current project index](../../CURRENT_PROJECT_INDEX.md).

## Administrative provenance

The canonical package remains at repository path `data/rating_packets_formal_v1/`. Its private key and integrity records were not copied into either archive. No private model key was read for delivery preparation or verification. The canonical workbook, report and material bytes remain unchanged in the shareable copies.

Only the dictionary-key ordering in the public `reports.json` was normalized to opaque report IDs; its values and the separately fixed rater order are unchanged. This avoids carrying source insertion order into public metadata. Added HTML pages and filling guidance do not alter report text, required components, rubric rules or workbook schema. ZIP entries have a common timestamp and sorted paths; request timing and generation order are not included.

`BUILD_RECORD.json` and `VALIDATION.json` retain preparation and verification evidence. Checks include archive CRC and entry-byte matching, source hashes, original report and embedded text equality, all local navigation targets, PNG decoding, model-identity metadata exclusion, workbook dropdowns and blank judgments, case spacing and English text. The static pages were not tested in a browser during this preparation. A lack of explicit identity words cannot prevent a reviewer from guessing identity from style; incidental unblinding must still be recorded.

No model calls, expert scores, cross-review or final adjudication were performed during packaging. Technical generation completion is not a clinical-quality judgment. The original approved rubric is copied verbatim, including its historical draft/five-case wording; the supplied approval status and current review scope explain which documents govern this 35-case study.
