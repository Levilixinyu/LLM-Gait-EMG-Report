# Frozen blinded three-rater outcome data

This is an administrative analysis-input freeze from recorded human judgments, not a new expert signature or model-comparison result. Original independent reviews remain separately referenced for reliability and sensitivity analyses.

- 105 reports from 35 participants (25 stroke, 10 controls).
- 552 coverage rows, including 105 separate G03 judgments.
- 52 confirmed report-scoped issue groups and 16 closed Pending groups.
- Registered categories and all 18 personal category proposals remain separately visible; four claim groups have different proposed sets.
- Pathology annotations do not require a simultaneous E02 tag, under the study-lead confirmation dated 2026-09-23. Explicit expert annotations and confirmed issue status remain required. No new flags or diagnoses were inferred.

`BLINDED_OUTCOMES.json` contains the cohort-qualified roster, report outcomes, coverage rows, claim-group crosswalk, per-rater source records, and separate category proposals. `FREEZE_RECORD.json` binds the exact dataset and input hashes. The builder refuses to overwrite this directory. Future corrections require an explicit new version.

All original independent scores, reviewer workbooks and the historical protocol remain unchanged. Pending is not converted to Error or Acceptable; missing annotations are not No. Disagreement in a control-flag outcome would remain unknown in the shared view, with individual outcomes preserved. No majority vote or pooled category decision is introduced.

Source hashes and references preserve provenance but do not authenticate human identities or create full-dataset signatures. No protected model mapping has been read. A model-identity join and model-level analysis remain a separate step; the old two-rater adjudicator importer must not be used unchanged.
