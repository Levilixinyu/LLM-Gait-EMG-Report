# Expert preparation package for 35 provisional cases

Prepared: 2026-09-18. Version: `formal-case-requirements-v1-draft`.

**Status: agent-prepared case requirements, pending independent expert review. External exposure history and final case eligibility remain unconfirmed. No new model reports have been generated.**

The user confirmed a plan for 25 stroke participants and 10 healthy controls, with three model reports per participant: 105 planned reports. This package prepares their prospective inputs and candidate requirements. It is not a report-scoring packet, final expert reference standard or generation authorization.

Start with [index.html](index.html), which contains all 35 cases and editable review controls. Read the common guidance once, then navigate to each case. Each case has a standalone `card.html`, exact model input files, extracted summary, EMG/kinematic plots, reference context and candidate items. The master page loads plots from the case subdirectories; keep the package folder structure intact.

For reviewers who prefer Excel, use [Expert_case_requirements_review.xlsx](Expert_case_requirements_review.xlsx). Read [REVIEW_GUIDE.md](REVIEW_GUIDE.md) before returning comments. Choose one authoritative return format per reviewer: browser JSON or Excel. No comments are sent automatically.

## What experts are being asked to decide

Decide which input-supported findings are essential for a report on each new case, how to phrase them, and what components or alternative routes constitute coverage. Shared interpretation rules and rubric v2 have already been approved; they are referenced here rather than submitted for another blanket approval.

The 200 initial candidates comprise six per stroke case and five per control. They are a starting point, not a requirement to retain 200 scoring items. The agent selected review candidates using displayed speed/step-length findings, leading displayed GVS and max-|z| values, and an optional threshold-coverage example. Numerical ranking does not establish clinical importance. Experts may omit redundant items, replace the numerical priorities, or add other model-visible findings.

Candidate N05 is explicitly optional for inclusion in the required core. Do not retain a threshold-coverage requirement merely because its displayed value is 100%. CCI, cadence and other input findings remain available for optional reporting or expert addition; their absence from the initial candidate list does not mean they are missing from the data or exempt from factual-error review.

Existing common G03 applies once to each reference-bearing report. Its meaning is not duplicated as another mandatory row for every case. Do not require hidden muscle-specific percentile limits, plot-only morphology, administrative age/speed, or intermediate gait events. Describing a supported difference and stating that its clinical meaning is indeterminate is allowed.

## Inputs and references

The system prompt is exactly the approved `limited-evidence-v3.1-candidate` system prompt. New user inputs use the same unchanged builder and numerical pipeline. Before constructing these materials, all five earlier approved user-input snapshots were reproduced exactly, as were their system prompts. No historical report was regenerated.

Each stroke case uses the pooled reference of 138 controls. Each control uses 137 other controls, excluding itself from its own mean/SD reference. Per-muscle effective counts are shown on plots and in `reference_card.md`. Mean/SD arrays were independently checked against the finite contributing curves for every new case; reference membership was checked explicitly.

Pooled calibration context remains the approved context and has previous control-cohort contributions. Leave-one-out reference construction does not create an independent validation cohort or matched diagnostic cutoffs. Expert figures and reference notes are not model inputs. Controls retain their documented pooled-side provenance and unavailable individual speed/cadence fields; no administrative metadata was silently added.

Each `model_messages.json` contains only two messages, system and user, with the exact content in the accompanying prompt text files. It contains no checklist, expert decision, plot, rater information or generated answer. These files are input snapshots for review; subsequent generation must still compare the frozen inputs against the actual saved requests.

## Exposure status and scope

The 35 cases match the [current provisional selection](../control_supplement_v2/README.md). The registered draw was not changed. Current local pilot/spot-check paths and hashes match the earlier 66-file inventory, and none of these 35 group-qualified participants occurs in it. This check does not certify external terminal or conversation history.

The user's instruction to continue is not treated as an attestation that no other use occurred. Complete the separate [exposure review workbook](../control_supplement_v2/Study_sample_and_exposure_review.xlsx) before final eligibility is asserted. Preparing these prospective expert materials does not authorize changing the already approved shared prompt based on future model output. Any objective eligibility exclusion must follow the recorded selection rules and retain this original package as provenance.

## Verification and files

- [Case index](case_index.csv): all case identifiers, paths and reference participant counts.
- [Candidate requirements](candidate_requirements.csv): all 200 machine-drafted proposals; expert columns are blank.
- [Manifest](manifest.json): data/code hashes, protected prior-file hashes, five-case regression checks, reference membership and per-case file hashes.
- [Validation](validation.json): numerical, source-preservation, English-text, workbook and browser checks.

The package uses the SHA-256-verified audit cache previously checked against released Excel/MAT data. This task does not claim a new raw-acquisition audit. Production feature/prompt code, approved expert evidence, historical reports, sample selection and archive separation remain unchanged. No identity key or model mapping was opened.

Reproduction creates a new preparation version and must not overwrite returned expert work:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/build_formal_case_review.py --out /private/tmp/gait-formal-case-review-recheck
```

The script generates the case materials and workbook; this README, review guide and final validation are maintained as package documentation. The existing destination is refused. The clinical decision is still made by experts, not by running the builder.

After both independent returns, reconcile new-case requirements while preserving original opinions. Finalize endpoints, paired analysis, failure/retry rules and rating forms before a generation freeze. Expert acceptance of case requirements alone does not approve the model batch.
