# Project working rules

- Use English for newly written or translated project filenames, prose, table headings, UI text, and code comments. Conversation with the user may be bilingual.
- Original-language evidence is archived outside this repository under `/Users/lixinyu/ProjectArchives/LLM-Gait-EMG-Report/`. That directory is archive-only, not a runnable project or an input dataset.
- Never search, import, generate reports from, rate, or analyze archived files as part of routine work. Access an archived original only for an explicitly requested provenance check or restoration.
- Never create a symlink from the active project into the archive. Default discovery roots must remain inside this repository and exclude archive/staging directories.
- Distinguish original evidence from English translations. Translation does not constitute a new model response, new expert assessment, or new signature.
- Preserve original source hashes in provenance records. Do not silently replace them with hashes of translated files. Record translation hashes separately.
- Completed trial inputs and results are historical. Do not regenerate a completed batch merely because a translation changed document bytes or paths.
- Keep model identity mappings outside rater materials. Do not unblind during translation or administrative processing.
- The study lead confirms that rater1, rater2 and rater3 are human experts who made their original scoring judgments independently. Do not attribute administrative preparation, software checks, source audits or manuscript drafting to the raters as automated scoring. Keep original independent judgments separate from later human discussion and personal rechecks.

## Manuscript prose

- Write concise scientific prose with a clear argument and concrete subjects and verbs. Begin paragraphs with the question, finding or interpretation they develop.
- Avoid promotional language, stock transitions, repeated caveats and internal administrative terminology where a plain description is sufficient. Keep technical terms consistent rather than varying them for style.
- Describe material protocol changes and uncertainty accurately, but keep routine editing history out of the manuscript. Preserve the distinction between original independent ratings and later review.
- During stylistic revisions, preserve numerical results, denominators, endpoint definitions, citations and the strength of each claim. Natural prose must not imply clinical validation or stronger evidence.
- Apply the installed `manuscript-writing-review` skill when reviewing manuscript prose. Synchronize revisions in `scripts/build_manuscript_draft.py` with the Markdown and HTML outputs so rebuilding preserves author edits.
