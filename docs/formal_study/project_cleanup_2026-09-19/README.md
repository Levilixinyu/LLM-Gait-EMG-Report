# Project review-file cleanup

Completed locally on 2026-09-19. No model identity mapping was opened and no remote history was rewritten.

## Human reviewer status

The study lead explicitly confirmed that rater1, rater2 and rater3 are human expert raters. The [current human rater register](../HUMAN_RATER_REGISTER.md) records that confirmation and links the submitted formal workbooks. Detailed credentials and conflicts are retained only to the extent actually supplied.

All three formal raters are human experts. The study lead confirmed their original independent scoring. Technical processing records are separate from human reviewer judgments; the historical pilot Q055 has a human-reviewed final disposition.

## Scan scope

The file inventory covered 89,596 project files, including raw-data and generation-log metadata. Identity-related content checks covered 1,169 text/source records, 56 workbooks and six ZIP archives, including the workbooks inside the archives. The scan also identified exact duplicates among review and documentation materials.

Git history, credentials, environments and external archives were excluded. Raw dataset contents, model identity mappings and unblinded generation streams were not opened for this administrative task. Their presence was inventoried without interpreting model-linked outcomes. Original model text was not rewritten.

## Removed material

| Category | Files removed |
|---|---:|
| Superseded extracted rater3 blank packet, retained byte-exact in its source ZIP | 403 |
| Duplicate pilot distribution files, with identical canonical copies retained | 58 |
| Superseded pilot discussion workbooks, fully transcribed into the existing process record | 4 |
| Regenerable caches and operating-system metadata | 88 |
| Total | 553 |

Removed size: 39,898,703 bytes (approximately 38.1 MiB). The [cleanup record](CLEANUP_RECORD.json) lists every removed path, hash and retained source.

The four discussion submissions are recoverable as content records by filename in `docs/expert_trial/expert_rate/trial_2026-09-17_v1/rating_reconciliation/process_records.json`. Cell values, formulas, comments and hyperlinks were compared after serialization; visual layout was not preserved.

## Material retained intentionally

All three completed formal rating workbooks, the final pilot consensus workbook and the active independent expert review template have unchanged hashes across this cleanup. Raw datasets, model reports, generation-stream events, frozen approval evidence and original independent pilot ratings were retained.

Copies necessary for standalone rater packets are intentional. Earlier formal case-reconciliation replies remain because the finalized case-requirements manifest references their exact bytes. Other frozen versions and approval files are evidence dependencies, not disposable duplicates.

The old rater3 ZIP and small creation records remain as the source for the renamed template. Its redundant extracted directory was removed. The legacy verifier now validates through a temporary ZIP extraction, so no duplicate working tree is required. Use the [neutral independent expert review template](../independent_expert_review_template_v1/README.md) for new distribution.

This cleanup does not validate clinical judgments, resolve pending issues, approve a three-rater analysis plan, or change any human score.
