# Three-rater review: current status

For full current scores, use [the consolidated working dataset](../consolidated_ratings_v1/Consolidated_ratings_working.xlsx) and [the latest scoring audit](../consolidated_ratings_v1/SCORING_AUDIT_2026-09-21.md). [Three_rater_current_positions.xlsx](Three_rater_current_positions.xlsx) retains this earlier 38-item discussion scope. The five targeted final dispositions are accepted as **Pending adjudication**, with no confirmed error counted for them:

- D002 and D004: E03. Rater3's agreed fallback applies because no common interpretation rule was adopted.
- D024: E02; E04 remains withdrawn.
- RA857737CABCC0FB8/I001 and RDB18B7C593D48194/I002: E01, one issue group per report; repeated Sub15 statements count once.

The accepted outcomes are registered in the four rightmost discussion columns and in Final disposition record, with registration date 2026-09-20 and source-linked acceptance attribution. This administrative transcription creates no new signatures. Individual preferred interpretations remain separate: four preferred-label differences remain, but these five disposition discussions do not require another rating round.

Across the 38 discussion items, 22 have matching substantive decisions. Twelve have matching individual Pending positions; four additional claims now have an agreed final Pending disposition despite different preferred readings. Thus 16 discussion items remain substantively uncertain. Pending is neither a confirmed error nor a confirmed correct claim. This file does not define statistical denominators or sensitivity analyses, and is not the complete final study dataset.

## Retained sources

- Rater1 and rater2 latest workbook returns in this directory.
- [Rater3 final closing return](../../../outputs/rater3_independent/Three_rater_discussion_merged_rater3_completed.xlsx), SHA-256 prefix `caa2c7f327c9fd80`.
- [DISCUSSION_FEEDBACK.json](DISCUSSION_FEEDBACK.json): forwarded final replies, English-summary attribution, source hashes, conditional-fallback basis and accepted dispositions.
- [Latest full scoring audit](../consolidated_ratings_v1/SCORING_AUDIT_2026-09-21.md): current findings; the superseded accumulated narrative was removed with a cleanup-log entry.
- [Three_rater_discussion.xlsx](Three_rater_discussion.xlsx): full earlier inventory of 552 coverage comparisons and 298 issue records, before the latest discussion outcomes. Do not use its discussion labels as final scores.
- Original independent submissions under `../three_rater_review_v1/private/`, and required completed rechecks and rules, remain retained.

These outcomes have been merged into the complete working scoring dataset, including the subsequent residual replies. Follow the latest scoring audit for remaining work. Original independent ratings remain separate for reliability analysis. Do not silently treat Pending as correct or pool repeated records as independent errors.

The builder `scripts/build_latest_discussion_positions.py` refuses to overwrite registered outcomes. The earlier full-inventory builder reconstructs only the historical inventory. Cleanup details are in [CLEANUP_LOG.json](CLEANUP_LOG.json); obsolete templates and intermediate copies are not active dependencies.
