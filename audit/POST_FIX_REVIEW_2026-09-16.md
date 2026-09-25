# Second-round independent review after Claude's fixes

Date: 2026-09-16. Scope: current src, scripts, tests, README, fix records, v1 frozen artifacts, and new calibration/input artifacts.

## Conclusion

**The core feature errors have been substantially fixed, but the entire project still cannot be marked as having completed acceptance or proceed directly to formal batch generation/expert scoring.** The main Excel extraction pipeline has clearly improved; the remaining issues mainly concern inconsistent generation entry points, incomplete caching and archiving, study/scoring documentation that has not been synchronized, and still-incomplete individual information and missing-data explanations in the input.

This review added only review files, did not modify the production implementation or old reports, and did not run any paid APIs. The source code was copied to a temporary directory for isolated testing; source-code hashes were recorded to avoid mixing concurrent changes into the review.

## 1. Items that passed independent validation

- Existing project tests: **10 passed** (run on an isolated source-code snapshot).
- v1 archive: all 113 files in the manifest passed SHA256 verification. See `review2/freeze_checks.json` for a file-by-file comparison of the production directories and the archive.
- Independently recalculated all 238 summaries (138 healthy+100 stroke sides) from the snapshot of the original released curves validated in the previous round; all can be serialized as strict JSON. This work was not misrepresented as a re-review of all C3D files.
- Sub50 TA now outputs a boundary-crossing interval of 56.6%→7.4%, and activity in the second half of the cycle is no longer omitted; the input includes the direction and phase of the maximum deviation.
- The later segment of Sub05 GAS remains within the output coverage, with max|z|=13.33, occurring at 80.3%, in the direction above the reference.
- All six rows of the dual-threshold table were reproduced; the ordinary/leave-one-out healthy p95 for each muscle also matched the previous recalculation.
- All 10-fold amplitude-scaling checks for the four muscles in the raw pathway passed, with relative changes in z of approximately 4.3e-12 to 2.0e-11; the previous scale-mismatch error has been fixed.
- The changes to prioritize replacement of full model IDs during anonymization and to fix file ordering are correct, and the related tests passed.
- The two operational definitions of step length have been clarified, and internal consistency is no longer described as independent ground-truth validation; clinical adjudication remains unresolved.
- The README has withdrawn the unsupported model rankings and added the speed support range and dataset limitations.

Recalculation scripts and outputs are located in `audit/review2/`. No v2 model reports were generated in this round, and no production output directory `data/reports_v2/` has currently been found.

## 2. Work still to be completed before formal generation

### R1 / High priority: versions and safeguards are inconsistent across the three generation entry points

Location: `scripts/generate_control_spotcheck.py:38–39,56,69`; `src/llm/report_generator.py`.

The main patient script has been changed to reports_v2/v2, but the healthy-participant script still uses the old directory, `PROMPT_VERSION="v1"`, skips whenever a file exists, and builds the reference from all controls, including the participant being tested. Yet it imports feature and prompt code that has already become v2.

Consequence: when all 12 current old files are present, all will be skipped; if files are missing or new models are added, reports generated from new inputs may be labeled v1 and mixed with old results. This is a potential contamination pathway; this review found no evidence that it had already occurred.

The general-purpose `generate_reports()` still defaults to v1, lacks complete input archiving, and writes directly using fixed filenames; selecting the same directory may overwrite old results. Fixing only one script does not justify claiming that all generation workflows have been unified.

Recommendation: freeze old entry points as read-only/explicit historical paths, or unify the generation infrastructure and version naming; use a separate directory for control v2 and a predefined leave-one-out/held-out reference. All active entry points should share request-archiving, validity-checking, and version-isolation rules.

Acceptance: validate with a local mock provider without network calls, while demonstrating that none of the entry points mix v1/v2 writes; the presence of old files should not conceal input changes; test controls should not contribute to their own reference, or the work should be explicitly limited to a historical exploratory experiment.

### R2 / High priority: the configuration hash does not cover actual inputs, and the cache still incorrectly accepts old results

Location: `scripts/generate_pilot_reports.py:41–68`.

The current hash covers some source code, the system prompt, and the model name, but does not cover the user prompt, data/reference membership, or actual generation parameters, and also omits dependencies such as providers.py, kinematic.py, and spatiotemporal.py.

Independent probes have reproduced the following:

- Even with clearly mismatched subject_id and user_prompt, the result is still judged valid as long as config_hash matches.
- A report_text containing only spaces and lacking termination/truncation status can also be judged valid.
- Modifying the above source files that are not included in the hash leaves the hash unchanged. The model's maximum-output parameter is currently located in the omitted provider implementation.

Recommend constructing the task identifier around the actual request content: model/provider, system/user prompt, actual parameters, input and reference data versions, and code version. Check the subject, side, `report_text.strip()`, and an explicit successful termination status. Retain historical versions in different paths to avoid directly overwriting same-named v2 files after configuration changes.

Acceptance criteria: after changing the input, reference, parameters, or relevant algorithms, old results must not be skipped; invalid statuses and blank text must be rejected. All of the above can be tested locally.

### R3 / High priority: README next steps contradict the new research plan

Location: approximately lines 303–319 of README; `src/eval/rubric.py:75–83`.

The preceding text already states that v1 is exploratory only, but Next steps still marks the old reports and old rating packets as complete and instructs distribution of the old `data/rating_packets/`. It still calls for “gold-standard reference reports” for the same development subset, without incorporating the distinction between expert reference standards, pilot rating, and formal evaluation.

The rating form still uses examples such as “4+ SD termed markedly deviant” for a normal/abnormal dichotomy, lacking metric-specific references and handling of “insufficient evidence/indeterminate,” which can easily reintroduce the aforementioned uncalibrated interpretations into rating.

There is also a specific factual error: README states that Sub46 used an “assistive device,” whereas the original record describes hand support provided by a physiotherapist; this cannot be described as use of an assistive device.

Recommend completely rewriting Next steps and the rating instructions; add factual accuracy, unsupported inference, uncertainty handling, and rules for indeterminate cases. Establish data cards, a list of permitted/prohibited inferences, and a pilot rating form before generating the final evaluation packets.

The framework for expert materials and the organization of reference data do not depend on paying to generate v2 reports first, and cannot all be postponed on the grounds of “waiting for v2 reports”; only final packaging requires the report text.

### R4 / Must be completed before generation: response metadata and dependency locking remain incomplete

`GenerationResult` still contains only the requested model name, text, and termination status, without the actual response model version, request ID, usage, etc. requirements.lock.txt explicitly covers only the local validation environment and does not lock the API SDK.

Claude has truthfully marked this as partially complete, so this is not concealment; however, “add it during the next real call” is not a necessary technical dependency. Field passthrough can be implemented first and verified with mock response objects, with interface compatibility checked when running a small real example. The full runtime dependencies and actual generation configuration should be locked before formal collection.

## 3. Input specification: significant improvement, but still only partially complete

### R5 / Medium priority: healthy reference and metric descriptions are hard-coded and cannot be used for the general raw pathway

Location: `METRIC_DEFINITIONS` and `to_prompt_text()` in `pipeline.py`.

An independent test used 5 synthetic controls, 101 phase points, and 3 joints; the output still claimed a reference of 138 people, statistics across 1001 points, and a GPS-like measure composed of 4 components, and included reference quantiles from the main dataset. These descriptions do not hold for the general raw pathway.

The corresponding numbers are largely correct when the current main Excel pathway uses the original reference, so the issue must not be described as all patient v2 inputs being incorrect. However, changing the reference or data will also make them inaccurate.

Recommend passing the reference source, number of people, processing method, number of phase points, and quantiles as structured metadata; do not automatically populate values from the main cohort when applicable calibration is unavailable. The entry point may temporarily be explicitly restricted to the main dataset, but do not simultaneously claim that general raw reports have also been standardized.

### R6 / Medium priority: individual events and missingness statuses are still insufficiently incorporated into the input

- Age, individual toe-off, clinical background, etc. are now explicitly described as “available but not provided,” which improves honesty but does not complete the incorporation of this information into the input.
- Sub46 actually has valid data only for ERS. The current text lists only ERS without individually declaring the other six muscles missing. The model still has to guess whether unlisted muscles are missing or were not selected for analysis.
- The explanation for Sub47's entirely missing data still makes the blanket statement that individual reasons are not in the public materials, but it corresponds to TVC55, which the original paper explicitly lists as one of the subjects without analog acquisition. Unknown reasons cannot be applied to all cases.
- After adding `step_length_definition="instantaneous"`, this definition is not passed into the summary with the results; the prompt still hard-codes successive-footfall. The default main pathway is unaffected, but using the new option creates a mismatch between the method description and the numerical values.

Recommend adding at least per-channel availability status, known reasons for missingness, individual toe-off, and operational definitions. If simplified input is deliberately being studied, document it as a prespecified experimental condition, restrict interpretations of stance/swing phases, and mark this item's status as “intentionally not implemented,” rather than “all input information has been completed.”

## 4. Verification scripts and boundary behavior need strengthening

### R7 / Medium priority: fix acceptance has a false-pass pathway

The late-burst expression in `scripts/audit_fix_verification.py` ultimately returns True whenever it finds any wrapped interval.

Independent counterexample: the detected result is 95%→5% and the target interval is 74%–87%; the two do not overlap, but the current logic still passes. The script prints and saves Boolean values but has no final assertion to exit with a nonzero status on failure; saving prompt_line also does not constitute verification that the text semantics are consistent with the structured intervals.

Note: this does not invalidate the actual Sub50/Sub05 fixes. Separate recalculation in this review confirmed that these two cases are correct. It shows that future regression testing cannot rely solely on “the acceptance script ran successfully.”

Recommend implementing a general circular-interval intersection check; making all acceptance assertions explicit and exiting with a nonzero status on failure; and performing actual checks of consistency between structured data and text.

### R8 / Lower priority: partial missingness is treated as inactivity, and CCI can produce NaN

The new test treats partial NaN values as inactive and checks only that interval endpoints are finite. An independently constructed curve with 20 missing points: missingness breaks the interval, but there is no quality warning; CCI is NaN, and strict JSON serialization fails.

The original main dataset curves have been checked and contain no partial NaN values, so this counterexample does not affect the current 238 main-data summaries. It is a quality-handling defect in the general pathway/future data. Unknown values should be distinguished from below-threshold values, a rejection, masking, or explicit interpolation policy should be specified, and validity rules for CCI and z should be unified.

The minimum-duration convention also needs to be unified: when 30 points out of 1001 are retained, the output endpoints are 10.0–12.9%, a span of 2.9%, although the configuration specifies 3%. This is a discrete-sampling/endpoint-convention issue and should be clearly defined and supplemented with boundary tests; do not exaggerate it into a major error in the current clinical conclusions.

## 5. The threshold change is a methodological change, not just a bug fix

v2 changes the primary definition to 20% of the mean curve's own peak, explicitly states this, and retains a fixed 0.2 sensitivity analysis; this part is much more consistent than v1.

However, this does not justify claiming that the new definition has been physiologically/clinically validated. Sub05 GAS changes from two main intervals under the fixed threshold to approximately 97% of the cycle above threshold under the relative threshold, with a boundary-crossing interval of 91.6%→88.4%. The change directly affects the report narrative.

The fixed 0.2 originally also had a clear operational meaning relative to the original cross-cycle normalization peak; the problem was that implementation, comments, and statistics used different conventions, not that an absolute threshold is necessarily mathematically wrong.

Recommend explicitly stating in the methods that “v2 changes the threshold definition” and retaining feature comparisons under both conventions. When comparing v1/v2, distinguish the fix for omitted intervals, the threshold change, and the increase in prompt information; not all changes can be attributed to improved model capabilities.

## 6. Reasonable scope for the next acceptance review

Prioritize fixing R1–R4: unify entry points, improve caching and archiving, and synchronize README/the rating workflow. Then address items in R5–R7 that affect actual main-data input; R8 can be listed separately as a limitation of the general pathway and need not invalidate the main-data recalculations that have passed.

After completion, prepare input/rating materials for a small number of development cases and healthy cases, confirm the research conditions, and then conduct small-scale v2 generation as authorized by the user. At this stage, directly rerunning all reports in a batch or distributing the old rating packets is not recommended.

## Evidence files

- `review2/source_manifest.json`: hashes of the source code under review; `changed_files.json`: changes relative to v1.
- `review2/freeze_checks.json`: comparison of archived and current historical artifacts.
- `review2/probe.py` / `probes.json`: counterexamples for raw scaling, caching, incorrect reference descriptions, partial NaN values, and false acceptance passes.
- `review2/check_real_curves.py` / `real_curve_checks.json`: 238 summaries, actual cases, threshold statistics, and ordinary/leave-one-out reference distributions.
- `review2/Sub05_input.txt`, `Sub46_input.txt`, `Sub47_input.txt`, `Sub50_input.txt`: verification of current feature-input excerpts; these independently recalculated examples do not include spatiotemporal parameters and are not presented as actual complete API requests.
- `review2/review_end_source_check.json`: whether source-code changes occurred during the review.

The review evaluates the implementation solely on code and local execution evidence, without substituting Claude's self-reported fixes for verification; it does not evaluate capabilities based on new model outputs because v2 model reports have not yet been generated.
