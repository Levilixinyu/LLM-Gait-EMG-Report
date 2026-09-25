# Blinded three-rater analysis preparation

The [analysis addendum](ANALYSIS_ADDENDUM_DRAFT.md) specifies a concrete proposed adaptation from two independent reviewers plus an adjudicator to three independent reviewers. It preserves the original two-rater comparison, treats the other two reviewer pairs as supplementary, and retains personal category differences and closed Pending decisions.

The source workbooks, historical protocol, and model identity mapping remain unchanged. This directory contains preparation and the subsequently authorized independent-agreement analysis, not a signed final dataset or model-comparison result.

## Independent agreement completed on 2026-09-23

The study lead explicitly authorized all three pairwise original independent comparisons. See [results](INDEPENDENT_AGREEMENT.md), [reviewable tables and row trace](Independent_agreement.xlsx), and [scope of authorization](AGREEMENT_AUTHORIZATION.json). The workbook contains 18 cohort/domain comparisons and 1,971 row-inclusion records. All cross-tabs were reconstructed from the trace and kappas independently checked with exact fraction arithmetic. Eight relevant three-rater tests passed.

No post-feedback labels were used, and the model mapping was not read. This authorization does not approve the entire addendum or its separate pathology-flag clarification. Raw agreement, kappa, marginals and pair-specific exclusions must be read together; agreement is not accuracy and does not rank reviewer quality.

## Semantic flag confirmation, 2026-09-23

The study lead subsequently confirmed that a pathology annotation does not require a simultaneous E02 category tag. [SEMANTIC_FLAG_CONFIRMATION.json](SEMANTIC_FLAG_CONFIRMATION.json) records that separate authorization. Explicit expert judgment and a confirmed in-scope issue remain required; a question, numerical deviation or E07 label alone creates no pathology flag. Personal categories, original independent scores and closed Pending states remain unchanged.

`scripts/freeze_blinded_three_rater_data.py` prepares the source-linked blinded freeze and refuses to overwrite an existing version. It reads no model mapping. A freeze is complete only when `../analysis_freeze_v1/FREEZE_RECORD.json` exists and its checks pass; the semantic confirmation itself is not a completed freeze or a new expert signature.

## Blinded freeze completed and validated

The [frozen dataset](../analysis_freeze_v1/README.md) was created at 2026-09-23T18:23:29.970501+00:00. Its SHA-256 is `9cf006f23d5660118f5ac4da9e631e68645fa17686a0742841e267e616ca9167`. A subsequent read verified the payload hash, 105-report/35-case roster, 552 coverage rows, 52 confirmed groups, 16 closed Pending groups, 204 linked individual records, report outcomes and control annotations. All 18 personal category proposals remain separate; no E02 tag was imposed on rater1's E07 proposal.

The freeze process verified the captured source bytes against registered hashes. Later iCloud eviction of the original XLSX files does not invalidate this already captured, hashed dataset. Original source evidence remains required provenance; it was not reconstructed. [FREEZE_STATUS.json](FREEZE_STATUS.json) retains the earlier cloud-availability history and the successful validation. No model identity mapping was read.

## Subsequent authorized model analysis

After the freeze, the study lead confirmed proceeding to model comparison. The separate [model analysis](../model_comparison_v1/README.md) is now complete and includes the protected mapping join, paired stroke estimates, separate controls, and original-review sensitivity. The earlier agreement analysis and frozen files retain their pre-unblinding scope and hashes. No model identity was inserted into the original rater packets.

Run from the repository root:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/prepare_three_rater_analysis.py
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/analyze_three_rater_agreement.py
/Users/lixinyu/.venvs/gait-emg/bin/python -m pytest -q tests/test_three_rater_blinded.py tests/test_formal_rating.py tests/test_formal_consensus.py tests/test_formal_analysis.py
```

`PREPARATION_CHECK.json` is the earlier preparation snapshot: exact input/code hashes, case/report membership, independent-row preservation, and agreement between the new per-report calculation and the existing working summaries. Its unrun-agreement status describes that earlier checkpoint. The later `AGREEMENT_BUILD_RECORD.json` identifies the completed analysis sources and output hashes. Neither contains model identities or model comparisons.

Study-lead confirmation of the addendum, source-linked final dataset assembly/freeze, and authorized unblinding are still separate steps. No additional expert rerating is requested by this preparation.
