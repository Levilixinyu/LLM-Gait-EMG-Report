# Prospective limited-evidence interpretation candidate

Status: implemented and validated locally; pending prospective expert/study-lead approval. No model reports were generated and no formal experiment was launched.

## What to review next

Review the [five-case candidate cards](../../expert_trial/data_cards_v6_candidate/index.html), the [candidate system prompt](../../../src/llm/candidate_prompts.py), and the interpretation decisions below. These are the same development cases: Sub09, Sub05, Sub50, Sub47 and healthy control Sub49. They are not an untouched test sample.

Experts should confirm the changed interpretation boundaries rather than repeat the completed trial or re-sign its adjudications. Candidate card items remain machine-drafted preparation questions; their IDs and wording must not be substituted for the final trial's approved checklist. A full prospective scoring rubric, formal sample, analysis plan and generation scope remain separate work.

## Completed changes

- Added explicit EMG preprocessing provenance independent of the deviation reference. Released curves use a shared across-stride peak before averaging; the separate raw-signal pipeline averages envelopes before peak scaling. No feature computation was changed.
- Added opt-in prompt version `limited-evidence-v3-candidate`. Legacy v2 serialization remains for historical reproduction and is not the corrected candidate route.
- Replaced physiological activation claims with descriptions of detected threshold intervals and mean-envelope coverage. Without supplied individual toe-off and matched muscle timing, the candidate does not assign gait phases or label timing normal, delayed, early or prolonged.
- Required both limited reference comparability and limits on disease-effect/diagnostic inference, following the agreed substantive G03 approach. Age and speed need not be separate keywords. Case-specific speed content remains distinct.
- Limited CCI conclusions to empirical comparisons and separated them from normal muscle function, stiffness and phase-specific control. This prospective wording requires confirmation; Q055 and all historical adjudications are unchanged.
- Preserved the distinction between coverage and errors, model-visible information and expert-only plots, and missing input versus absence from the source dataset.
- Generated a new versioned five-case package, with actual system/user messages, curves, reference notes, editable draft review forms and checksums. Existing data cards and completed trial inputs were not overwritten.

## Evidence and checks

See [normalization evidence](NORMALIZATION_EVIDENCE.md), [array-level results](normalization_verification.json), [package verification](package_verification.json), and [browser checks](browser_checks/browser_checks.json).

- All 614 evaluable stroke subject-side-muscle combinations passed the scale and Excel averaging checks; 86 had no valid nonzero paired samples.
- All 304 evaluable bilateral muscle pairs had distinct side-specific denominators.
- All 2,618 cached curves exactly matched the released Excel arrays, including missing-value locations.
- All five candidate summaries exactly matched v5 after excluding the newly added processing-provenance field.
- Saved messages matched the system/user text shown in each card and the combined page; package/code hashes passed.
- 54 Python tests and 19 browser checks passed. The Python tests include synthetic checks; original-array evidence is recorded separately.
- 348 historical files were hashed before and after this work and remained unchanged. Checksums were used without examining the blinded model-identity mapping.

The English-conversion manifest remains a historical snapshot. It was not rewritten to conceal intentional subsequent code changes; the candidate manifest and integration record identify this revision separately. The independent folder previously created at `/Users/lixinyu/LLM-Gait-EMG-Candidate-2026-09-17` is superseded staging, not an active input or generation source.

## Reproduction

Run from the repository with the project Python environment. Use a fresh output location; existing material is protected from overwrite.

```sh
python scripts/verify_release_emg_normalization.py --out /tmp/gait-normalization-new.json
python -m pytest tests -q
python scripts/build_expert_trial_package.py --verified-cache --prompt-version limited-evidence-v3-candidate --out /tmp/gait-cards-new
python scripts/verify_card_review_ui.py --base /tmp/gait-cards-new --out /tmp/gait-browser-new
```

## Pending decisions

1. Confirm the prospective limited-input interpretation task and the timing/CCI wording. No new expert approval is claimed here.
2. Translate those decisions into a versioned scoring rubric with contextual examples, preserving C01 and the agreed G03 semantics. Do not use draft card questions as automatic omission penalties.
3. Select the held-out sample using an exposure ledger; approve analysis, repetitions, failure handling and blinding before generating a formal batch.
