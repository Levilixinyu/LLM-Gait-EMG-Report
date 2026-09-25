# Comprehensive project readiness review

Date: 2026-09-16. Purpose: to determine whether the project can enter the next stage, rather than again requiring the packaging fixes that have already passed acceptance to be redone.

## Overall assessment

**The project can enter the next stage, but that stage should consist of completing the evaluation materials and conducting a small-scale developmental pilot evaluation; it is not yet appropriate to launch the full-scale formal comparison directly.** The data and core engineering foundations are in place, and the acceptance conclusions for F1/F2 and T1–T6 remain unchanged. The main unfinished work concerns the inputs, reference standards, scoring rules, and sample/analysis plan for the research evaluation, not an unusable dataset or a need to rewrite the entire codebase.

| Component | Current assessment | Work that can proceed |
|---|---|---|
| Main dataset and descriptive task | Usable within the defined research scope | Prepare case materials based on verified mean curves |
| Extraction, task caching, generation, blinded-evaluation packaging | Local validation passed | Prepare and verify pilot-evaluation materials and run simulated workflows |
| SDKs and dependencies | Successful small-example records available, environment consistent | Check complete reports for real cases after authorization |
| Expert pilot-evaluation materials | Draft, not yet complete | First prepare data cards, reference checklists, and scoring rules for 5 cases |
| Formal model comparison | Not yet ready | Freeze the primary endpoint, sample, and analysis plan after the pilot evaluation |
| Clinical diagnostic/deployment validity | Outside the objectives this study can support | Do not claim validation on this basis |

## 1. Checks actually performed in this review and their boundaries

Reviewed the README, research scope and data-review records, feature inputs, provider/runner/cache, the two generation entry points, packaging and rubric, dependency lock, SDK smoke scripts and records, and the newly added expert pilot-evaluation draft and CSV templates. Did not read the contents of .env, initiate real API calls, or modify production code.

- Snapshots of 33 Python source/script/test files; hashes were unchanged at the end.
- Current tests: 45 passed in 2.12s.
- `pip check` found no dependency conflicts; the 46 entries in requirements.lock.txt match the versions actually installed in ~/.venvs/gait-emg, and already include SDKs from all three providers.
- The newly added generation_runner.py and both entry points themselves have all been added to CODE_FILES: the non-blocking provenance recommendation from the sixth round has been implemented.
- The SHA256 hashes of curves.npz, metadata.json, and spatiotemporal_original.json match the initial archived records; using these previously verified released-data caches, 238 summaries were regenerated with the current code, including 138 healthy controls using leave-one-out references excluding themselves, and all passed strict JSON validation.
- This round did not reload the full Excel/MAT collection or review all C3D or healthy MAT files. Validation of the previous 1100 Excel/MAT curves and 100 published walking speeds remains based on earlier evidence; no claim is made that it was repeated this round.
- `audit/outputs/sdk_smoke_check.json` records OK responses from all three providers, successful termination, model/ID/usage, and all serialization checks passing. This round checked existing project records; no online requests were personally resent. This script is a single-word response test and does not demonstrate that formal long-report inputs, complete outputs, costs, and latency have all been validated.
- The formal v2 report directory contains no reports yet; the existing 54 patient reports and 12 healthy reports are historical v1 reports and must not be treated as new formal results simply because the SDK checks passed.

Files available for rechecking: readiness/check.py, checks.json, actual input text for each case, source_manifest.json, source_end_check.json, document_manifest.json, test_results.txt.

## 2. Data and sample: usable, but the candidate sample must be correctly delimited

This round's recalculation agrees with the previous round: among 138 healthy participants, 102 had all seven channels complete, 7 had partial channels, and 29 had all channels missing; for the affected side of 50 stroke participants, 43 were complete, 3 partial, and 4 entirely missing; for the unaffected side, 44 were complete, 2 partial, and 4 entirely missing.

The 18-person development set includes 16 participants with all seven affected-side channels complete. Therefore, only 27 of the 43 complete participants are outside these 18. The 27 are candidates calculated as “not included in the 18-person list”; this does not automatically mean that they were entirely uninvolved in any exploration: development exposure still needs to be defined using historical viewing/tuning records, and they cannot be claimed to inherently constitute an independent confirmatory validation set.

Continue using the single-dataset, retrospective, exploratory objective of “descriptive fidelity/uncertainty expression/expert reviewability.” Existing limitations remain, including unmatched speeds, peak normalization rather than absolute force, average curves masking step-to-step variability, and inconsistencies between clinical labels and inclusion descriptions. There is no need to immediately download the full healthy MAT collection or resolve external CSV channel mapping for the current descriptive pilot rating.

Performing technical spot checks of gait features first does not automatically disqualify all participants from evaluation; the key is not to subsequently treat cases used to select prompts, error rules, and result interpretations as unseen confirmatory evidence. The formal protocol can remain exploratory and transparently disclose the development process.

## 3. Evaluation materials that must be completed before pilot rating

### A. Turn the 5-case draft into actual, distributable case packets

docs/expert_trial/TRIAL_RATING_PLAN_DRAFT.md has proposed Sub09_P, Sub05_P, Sub50_P, Sub47_P, and healthy Sub49 with a leave-one-out reference, which is a reasonable combination for developmental pilot rating. Currently, only the draft and empty CSV headers exist; the script for generating data cards, curve plots, and case-specific checklists do not yet exist.

Each case should contain at least: the same frozen input as provided to the model; the originally published average curves and the reference curves used; activation thresholds and interval annotations; metric definitions and applicable empirical references; and lists of required descriptions/permitted interpretations/unsupported inferences. Healthy Sub49 must explicitly specify group=control to avoid confusion with the stroke case of the same name.

Experts see the curves to verify whether the numbers and interpretations are supported; completeness scores should not be reduced because the model did not describe details present only in the curves but not included in its input. Case-specific checklists must specify “information actually available to the model.” Experts involved in developing the checklists should establish the reference before viewing model outputs, to prevent reference answers from changing with the model's wording.

### B. Align the reference basis for model inputs and expert ratings

The current input provides only the overall span of healthy max|z| p95, 3.65–4.61, and states that leave-one-out values are higher; it does not fully list the applicable thresholds for each muscle. The JSON already contains more detailed data, such as TA pooled p95=4.605 and LOO p95=5.174; the expert pilot-rating draft still broadly states 3.65–4.61. Healthy LOO results cannot be rated normal/abnormal using pooled limits without explanation, and experts must not deduct points because the model does not know precise ranges that were not provided.

Before pilot rating, select and implement one consistent approach: provide muscle-specific references compatible with the method used alongside the input and data cards; or explicitly state that these statistics only describe deviations and permit an indeterminate judgment when applicable ranges are unavailable. CCI and GPS-like must also identify the sources of their empirical distributions; the existence of a percentile does not make it a clinically validated disease cutoff. The reference mean±SD curve band is a phase-specific description, not a diagnostic threshold for the entire curve.

This item concerns freezing the formal evaluation criteria and does not negate previously passed metadata fixes such as “actual reference of 137 participants/exclusion of the participant themself.”

### C. Distinguish “the model correctly judges the result indeterminate” from “the rater cannot assess”

The pilot-rating draft ends by mapping INDETERMINATE to NA-indeterminate for each Likert item, which introduces confusion. When the model correctly expresses uncertainty because of insufficient data, it can still receive regular ratings on dimensions such as accuracy/unsupported inference; this must not automatically become a missing rating. NA should be limited to cases where the dimension genuinely does not apply or the expert lacks sufficient materials, with the reason and statistical handling method recorded.

Also add intermediate anchors for scores of 1–5 and standardized examples of important omissions/error severity. Retain item-by-item evidence citations for safety items; mechanistic explanations that go beyond the data must still be evaluated as overinterpretation. “Not evaluating the truth of mechanisms” must not mean entirely omitting evaluation of mechanistic assertions in reports.

### D. Add batch and case identity to the rating form

The new packager starts anonymous numbering at R0001 for every batch. The current CSV contains only rater_id, anon_report_id, subject_case, etc., with no batch_id. Patient and healthy pilot ratings may come from different batches, and later regeneration will also produce identical anonymous IDs.

Rating data should use at least `(batch_id, anon_report_id, rater_id)` for unique identification; case identity should retain group, subject_id, side, or an equivalent nonduplicated case_id. Add the rating form/rule version. Raters must not see provider/model or the answer key; the batch ID itself can be a neutral identifier that does not reveal the model. Do not change the batch-isolation implementation that has already passed; simply make the rating form and import validation match it.

## 4. Study choices to freeze before formal comparison

These issues do not all need to be decided before plotting, but they must be locked before viewing the formal comparison results:

- One primary evaluation endpoint and its denominator, for example whether a report contains a predefined important factual error/unsupported inference; list other Likert dimensions as secondary outcomes, with the final choice determined jointly with experts.
- Sample inclusion/exclusion, development cases versus subsequent evaluation cases, and the roles of complete/missing EMG subsets and the healthy known-label task. Do not combine all outputs and call them the same type of false-positive detection.
- Number of generations per case per model, valid-output conditions, and retry and retention rules for timeouts/truncations/failures; a single report can only evaluate that output and cannot represent model output stability.
- Model version, SDK, input/prompt, default or explicit sampling/reasoning parameters, output budget, and whether budgets are directly comparable across providers. Existing records explicitly set only the output token limit; using defaults is acceptable, but this must be disclosed, and strictly matched reasoning computation cannot be claimed.
- ≥2 experts rate independently, retaining original ratings before adjudication; select agreement and comparative analyses appropriate for the endpoint and sample size. Participants are the repeated-measures/clustering units, with models and raters crossed; do not treat 18 participants×3 models as 54 independent patients.
- Handling of NA, missing reports, and dispute adjudication; effect sizes and uncertainty; and the boundaries of exploratory conclusions. The small pilot rating is for improving the process, not for declaring a winning model.

The existing draft sets out the general direction but has not frozen the operational details above. The fact that “rubric.py exists” cannot be treated as evidence that the statistical and evaluation design is complete.

## 5. Documentation and method descriptions need to be synchronized, without restarting the engineering review

README still contains old paths and operating instructions: the project tree points the generator to data/reports/; the status lists 54 reports as “verified clean”; setup still uses the old .venv; the demonstration main-cohort reference does not pass source, which produces generic text under the current code. Update these to the current environment, v2 directory, _meta manifest, and returned batch path, clearly distinguishing historical v1 from v2 that has not yet been generated. README's healthy-reference self-inclusion description should also clearly identify it as historical pooled calibration rather than the current control-generation entry point.

The normalization definition should explicitly state “a common peak across available gait cycles for each muscle of each participant, followed by averaging,” to prevent the existing wording each cycle from being read as separate normalization within each cycle. Data processing and Data Records in the original paper explicitly specify the maximum across available cycles: [Original paper](https://www.nature.com/articles/s41597-023-02767-y). This is a wording clarification; no renewed incorrect normalization in the Excel pathway was found this round.

README already states that Sub46 received hand support from a therapist, but the actual Sub46 input does not yet include assisted-walking status. If such context is included in rating requirements in the future, it should also be added to the model input and data card; if the input remains streamlined, points must not be deducted because the model did not mention context that was not provided. Individual toe-off, age, etc., have already been declared not provided and should be handled in the same way.

The mild/moderate/severe descriptions in the 5-case draft should explicitly refer to development cases selected by walking speed; without independent evidence, they must not be treated as ground truth for overall clinical severity.

## 6. Recommended execution order and completion criteria

1. **Complete pilot-rating preparation first (can be done now).** Generate data cards and curves for 5 cases; align the reference basis; complete rating anchors, NA, and batch fields; update README with the current operating workflow. Acceptance: every required rating item can be traced to the actual model input or an explicitly permitted reference.
2. **Validate a small number of real cases.** There is no need to repeatedly rerun the existing single-word SDK smoke test without reason; after the user authorizes the budget, first use 1 case×3 models to check complete reports, termination status, request-parameter archiving, costs, and packaging, then complete the planned 5-case pilot-rating reports. Do not directly use the fixed 18-person script to generate the full set as a substitute for pilot-rating sample selection.
3. **Developmental pilot rating by ≥2 experts.** Rate independently, recording time, disagreements, and insufficient materials; revise the rules and retain versions and original records.
4. **Generate formal batches only after freezing the formal protocol.** Lock the sample and primary endpoint, execute the predefined failure handling and analysis, and fully archive original reports, batch answer keys, ratings, and adjudications.

There should be no further aimless rounds of full-code review. The most valuable progress now is to enable experts to rate the same evidence consistently and to validate the complete report workflow using a small sample of real cases.
