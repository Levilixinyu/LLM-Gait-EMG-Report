# English manuscript working draft

Read [the browser version](MANUSCRIPT.html) or edit [the Markdown manuscript](MANUSCRIPT.md). The draft contains an abstract, introduction, methods, results, discussion and limitations, with a separate healthy-control analysis, six main tables and five supplementary tables. Supplementary tables include coverage across scoring stages and descriptive report length. [Excel tables](Manuscript_tables.xlsx) use the same source values.

Numerical results come from the frozen model analysis, original independent agreement/outcomes and the subsequent targeted sensitivity. Original reports, reviewer submissions, model-analysis files and the frozen dataset were not modified. The manuscript distinguishes the original two-reviewer plan, later third independent reviewer and post-unblinding follow-up. It does not claim a unanimous pathology annotation after the later disagreement.

[Author confirmations](AUTHOR_CONFIRMATION.md) record the confirmed reviewer background and identify the remaining ethics and author declarations. These fields remain explicit placeholders, so this is not yet a submission-ready manuscript. [Source map](SOURCE_MAP.md), [table data](TABLE_DATA.json) and [build record](BUILD_RECORD.json) support verification. All project documents are in English.

Rebuild numerical tables and the draft with `python scripts/build_manuscript_draft.py` from the repository root. This overwrites generated manuscript files; preserve author edits before rerunning. The author-confirmation file is not overwritten on rebuild. For a separate build, use `python scripts/build_manuscript_draft.py --output /path/to/new/manuscript`; an existing explicit output directory is refused.
