# Current study plan: 25 stroke participants and 10 healthy controls

Recorded: 2026-09-18. **The user confirmed the sample-size plan. Participant membership is provisional pending external exposure checks. No reports have been generated for this new batch.**

This decision supersedes the 40-control recommendation in `control_supplement_v1_draft`. That earlier package and its hashes remain unchanged as planning history. Use this directory for the current sample allocation and history-review workbook; do not use the old sample-size recommendation as an active instruction.

## Confirmed counts and purpose

| Component | Participants | Models per participant | Planned reports | Role |
|---|---:|---:|---:|---|
| Stroke | 25 | 3 | 75 | Main evaluation of report interpretation quality |
| Healthy controls | 10 | 3 | 30 | Exploratory supplementary evaluation |
| Total | 35 | 3 | 105 | Cohorts reported separately |

Each of the two raters would review all 105 reports, for 210 rating assignments. Repeated model reports and rater assessments do not create additional independent participants. Each case-model contributes one planned response; this decision does not approve repeated generations, retry handling or technical-failure exclusions.

The control sample is resource-prioritized: it provides supplementary observations of unsupported pathological and normal-function claims while preserving effort for stroke case requirements and reliable independent scoring. It is not powered to establish low error rates, model equivalence or small between-model differences. The previously proposed 15-percentage-point precision target for 40 controls is no longer the design rationale.

If one model has zero target events in ten independent cases, the exact one-sided 95% binomial upper bound is `1 - 0.05^(1/10)`, approximately 25.9%. This is an illustration under independent equal-probability assumptions, not a clinical guarantee, stopping rule or finite-population analysis. See [NIST exact binomial limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm). The resource-based justification and accepted inferential limits should be stated transparently, consistent with [Sample Size Justification](https://doi.org/10.1525/collabra.33267).

The 25-case stroke count also remains a resource-defined planning decision rather than demonstrated power for model superiority. Adding controls does not resolve uncertainty in stroke model comparisons.

## Provisional healthy-control draw

One seeded pseudorandom permutation was recorded for the 98 locally eligible controls. The first ten are:

| Draw rank | Group-qualified participant |
|---:|---|
| 1 | control_Sub62 |
| 2 | control_Sub07 |
| 3 | control_Sub01 |
| 4 | control_Sub73 |
| 5 | control_Sub117 |
| 6 | control_Sub14 |
| 7 | control_Sub06 |
| 8 | control_Sub39 |
| 9 | control_Sub09 |
| 10 | control_Sub31 |

These are control participants. Their identifiers must not be confused with the same numbered stroke participants. All ten have seven finite EMG means and four finite sagittal kinematic means in the released pooled-side data. No pilot/spot-check reports for them occur in the checked local inventory, and none belongs to the five-case expert development set.

The 25 stroke participants are the previously documented conservative planning pool, retained in full rather than randomly sampled again. See [selected_study_cases.csv](selected_study_cases.csv) for all 35 group-qualified identifiers. No stroke case has been substituted or drawn from the exposed pilot cases.

## What was checked and what remains unknown

The current pilot/spot-check inventory still contains the same 66 files, including reports for control Sub10, Sub49, Sub93 and Sub98. These four controls remain excluded. File hashes match the earlier inventory, and current stroke/control Excel and audit-cache hashes match the previously verified data sources. The builder checked 1,353 mean curves across the 98 control candidates and 25 stroke candidates for the required 1,001 finite samples each.

Local evidence does not establish whether a participant was discussed, reported on or individually analyzed in an external conversation, another terminal or an unregistered file. All external-history fields remain pending. The user was asked about additional healthy-control use; no answer has been inferred from silence or from approval of the sample size.

The [sample and exposure workbook](Study_sample_and_exposure_review.xlsx) includes the proposed 35 cases and blank history-review fields. Save a separate review copy, and record the history status, evidence/details, reviewer and date. This records exposure history, not expert approval of case requirements. `No additional use known` is an attestation of known history, not a claim that every possible external record has been exhaustively searched.

All healthy candidates were previously available to reference/calibration construction. They form an internal reference-used supplementary group, not independent external validation. Age and published bilateral speed in the workbook are administrative metadata and have not been added to model inputs.

## Randomization record and replacement rules

The [registration](sampling_registration.json) records the agreed counts, sampling-frame hash, seed, algorithm and timestamp. The sampling frame and registration were written before any ranks were computed. The seed was generated once using `secrets.token_hex(32)`; there was no seed screening or reroll.

For each group-qualified key, the sorting value is SHA-256 of the UTF-8 string `seed_hex + newline + participant_key`. Sort by that value, with participant key as a tie-breaker. The resulting [full sampling order](control_sampling_order.csv) contains ten provisional selections followed by 88 ordered reserves. The procedure is a reproducible pseudorandom sample without replacement; it does not stratify or match age, speed or waveform appearance.

This deliberately changes one ordering step from the unapproved v1 proposal: the full random order is registered before external history is completely known. Final eligibility is not asserted. If a candidate is subsequently excluded using documented, objective prior-history or data-quality evidence, use the first ten eligible participants in this same registered order. Do not generate a new seed or select a preferred replacement. The rule depends on exclusions being based on objective eligibility rather than model output or favored sample characteristics.

Record any exclusion, supporting evidence and reserve promotion in a dated amendment that retains this original draw. Unknown history alone is not silently converted to eligibility or exclusion. Do not replace difficult valid cases, redraw for a preferred age/speed distribution, or enlarge the control sample in response to observed errors. Exhausted eligibility or changes to the stroke pool require a documented design amendment, not automatic relaxation of prior exclusions.

The builder refuses an existing output directory. **Do not rerun it into a new directory to obtain another sample.** Verify the stored permutation from its seed and frame instead. See [selection_record.json](selection_record.json) for provenance and [manifest.json](manifest.json) for output validation.

## Endpoints and next work

The conceptual evaluation remains faithful interpretation of the supplied data. Healthy-group membership does not prove normal physiology, and a descriptive deviation is not automatically a pathological finding. Because the model is given group membership, the control task is not an independent diagnostic classification test.

The prior package's proposed semantic flags for unsupported pathological and normal-function inferences remain proposals for expert confirmation; sample-size approval does not turn them into a finalized endpoint definition. Existing rubric v2 decisions and examples retain their approved scope. The existing five-case annex is not a set of requirements for these 35 new cases.

Next steps are:

1. Complete and record external exposure review; apply any evidence-based exclusions using the registered order. Finalize the case membership without viewing new generated reports.
2. Prepare new-case model inputs and expert requirements. Check control self-exclusion from its own mean/SD reference and keep pooled calibration dependence explicit. Do not silently change the approved input contract or copy Sub49's numerical requirements into another control.
3. Confirm the new-case requirements and finalize report-level outcomes, paired analysis, missing/unresolved assessments, technical-failure/retry rules, rater capacity and rating materials. Preserve original independent ratings and distinguish agreement from later consensus.
4. Freeze the generation package and obtain the applicable batch authorization before calling model APIs.

No existing expert signature, reviewed prompt, rubric workbook, historical report or adjudication was changed. Original-language archives and private model identity mappings were not accessed.

## Files

- [Study_sample_and_exposure_review.xlsx](Study_sample_and_exposure_review.xlsx): selected-case overview, external-history fields, control draw and ordered reserves.
- [selected_study_cases.csv](selected_study_cases.csv): 35 provisional cases and their cohort roles.
- [control_sampling_frame.csv](control_sampling_frame.csv): the frozen local 98-control candidate frame.
- [control_sampling_order.csv](control_sampling_order.csv): the full registered order and pending eligibility status.
- [sampling_registration.json](sampling_registration.json): seed and rules recorded before ranking.
- [selection_record.json](selection_record.json): source hashes, authorization scope and checks.
- [manifest.json](manifest.json): hashes and package validation.

The script `scripts/freeze_study_sample.py` created the machine-readable files. This explanatory README and final manifest document the completed package separately. The old v1 proposal is retained only as superseded planning history; this v2 package is the current decision record.
