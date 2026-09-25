# Third independent review: after the second batch of fixes

Date: 2026-09-16. Source snapshot under review: `review3/source_manifest.json`.

## Conclusion

**Most issues from the previous round have been fixed; there is no need to start over. Two major integration issues affecting formal generation/evaluation remain: historical archives can enter blinded rating packets, and the descriptions of leave-one-out/custom references are inconsistent with the calculations.** There are also smaller closeout issues involving archive naming, cache type checks, reasons for missingness, and response identifiers.

No paid APIs were called in this round, and no production source code was modified. Tests were run after copying the code to a temporary directory, and a fake provider was additionally used to exercise two actual generation entry points; 238 summaries were recomputed from the previously verified snapshot of the released curves. Passing locally in this round cannot be interpreted as verification of the actual SDK interfaces or clinical validity.

## Independently confirmed passes

- **All 28 existing tests passed.**
- Both the patient and healthy-control actual entry points invoke the unified caching logic and output v2. In the fake-provider end-to-end test, each entry point generated 3 reports on the first run, with 0 additional calls on an identical second run.
- The healthy-control entry point did exclude the subject being evaluated. For test subject C1, the reference members were only C0/C2; this was not merely a change to reference_id without changing the calculation.
- The main cache checks for blank text, lack of a successful termination status, and changes to input/parameter/data/code hashes have been added.
- The raw prompt no longer incorrectly appends 138 subjects, 1001 points, and main-dataset quantiles.
- The six missing channels for Sub46 are now explicitly listed; the known reason for non-acquisition is used for Sub47.
- The optional step-length definition is now passed along records→lookup→summary→text.
- The circular-intersection counterexample 95%→5% does not cover 74%–87% and is now correctly evaluated as False; the script can exit with a nonzero status for interval/text and raw-scale failures.
- Partial NaN values in the normalized path produce a quality warning, CCI is omitted, and strict JSON validation passes. This verification does not extend to a claim that all missing-data situations in raw continuous signals are supported.
- All 238 real-curve summaries still pass strict JSON validation, and the Sub50/Sub05 multi-interval/boundary-crossing results remain correct.
- README no longer instructs distribution of the v1 rating packets, and the expert reference standard and evaluation sequence have been rewritten; the wording on handrail assistance for Sub46 has been corrected.
- The response model, identifiers, and usage are now being saved with reports; complete API SDK dependency locking remains a to-do before actual calls.

## T1: Archiving and blinded rating packet creation are not integrated—high priority, must be fixed before formal rating

Location: `src/llm/generation_cache.py:127–136`, `src/eval/blinding.py:74`.

`place_record()` saves old results as `*.superseded-time.json` in the same directory. `create_rating_packets()` still iterates over all `*.json` in that directory, neither excluding historical archives nor checking successful termination/truncation status or uniqueness for the same task.

**Independent reproduction**: First write a truncated old report, then write a normal new report, and then call the actual packet-creation function. There should be only 1 current report, but 2 rating items were actually produced, with the text `OLD_INVALID_TRUNCATED` and `NEW_VALID`. This could include the same model more than once, mix different input versions, and deliver failed reports to raters.

This is a failure mode of the actual code constructed in a temporary directory, not a claim that the formal v2 rating packets have already been contaminated, because the formal reports have not yet been generated.

Recommendation: Move historical records into an explicit archive subdirectory; base rating packets on the list of successful tasks for the current experiment, not on all JSON files in the directory. Validate subject/side, provider, prompt/input version, successful termination, absence of truncation, and the expected number of models. Historical, failed, and duplicate tasks should be excluded or trigger explicit errors.

Acceptance criteria: Local integration tests cover five types of situations: coexisting new and old records, failure/truncation, missing models, duplicate models, and different input versions; normally, one subject with three models must produce only three rating items for the current round.

## T2: Leave-one-out calculations are implemented, but the reference description still refers to the full cohort—high priority, fix before healthy-control v2 generation

Location: `_DEFS_MAIN_COHORT` and the end of `extract_summary_from_normalized()` in `src/features/pipeline.py`; the interface between reference_id in the healthy-control script and the summary.

Currently, whenever normative is supplied, normalized extraction labels it `reference_source="main_cohort_excel"`, without carrying the reference subject count, members, or method. The leave-one-out information in the healthy-control script is written only to the generation record and does not enter the definitions seen by the model.

**Sub10 test result**: The actual reference comprises the other 137 subjects, GPS-like=7.2417, but the input still states 138 subjects and does not explain that a leave-one-out reference was actually used in this instance. The ordinary full-sample quantiles in the text and the background description that “leave-one-out is higher” do not amount to calibration for the statistical basis currently used.

**General counterexample**: NormalizedTrialData with 3 controls and 101 points is also automatically described as the main dataset with 138 subjects and 1001 points. This shows that R5 fixed only the raw entry point; normalized custom references remain incorrect.

Recommendation: Have the reference constructor return structured metadata: source, method, members/excluded subjects, kinematic subject count, valid subject count for each muscle, number of phase points, and calibration source; generate the summary and prompt from this object. Leave-one-out for controls should explicitly state that the subject has been excluded, distinguish the current reference from the full-cohort background distribution, and not substitute one for the other by default. When a custom reference is unknown, use a generic description; do not infer the data source from the called function's name.

Acceptance criteria: The full main reference, Sub10 leave-one-out reference, and 3-subject custom reference each output the correct subject count/method/point count; every calibration quantile is labeled with its scope of applicability.

## T3: Second-resolution timestamps on archive files may overwrite earlier history—medium priority

Location: `generation_cache.py:133–135`.

With the time fixed to the same second, writing three versions FIRST, SECOND, THIRD consecutively leaves only SECOND and THIRD, with FIRST lost: the second rename uses the same archive destination, overwriting the first archive. Production API calls usually take longer than one second, so this does not happen on every run, but the promise of “not overwriting any history” does not hold.

Recommendation: Use unique task/run identifiers and a creation method that cannot overwrite existing files, and finish writing a temporary file before replacing the current file. Higher-resolution timestamps can only reduce collisions; alone, they cannot guarantee no overwriting.

Acceptance criteria: With the clock frozen, write three times consecutively; all three versions are retained, and the old contents remain unchanged.

## T4: The cache crashes on valid non-object JSON—medium priority

Location: `generation_cache.py:103–113`.

Existing tests cover only malformed JSON text. If the file contains `[]`, parsing succeeds, but `.get()` raises AttributeError. The validity check occurs before the try block in the generation loop and may terminate the entire batch. An explicit check for an incorrect report_text field type is also missing.

Recommendation: First validate that the top level is a dict and that required fields have the correct types, returning an explainable reason for invalidity on failure; do not let bad historical artifacts bring down the entire batch.

Acceptance criteria: Lists, null, numbers, strings, and non-string report_text are all deemed invalid without raising exceptions.

## T5: Missing-data reasons have still been fixed for only one case—medium priority, complete before expanding the cases

Currently, `DOCUMENTED_NO_ANALOG_SUBJECTS` contains only Sub47. The original study also lists TVC11, TVC55, TVC57 as having no analog signal acquisition, corresponding to Sub08, Sub47, Sub48 respectively; the Sub08/Sub48 outputs still state that the reason was not disclosed, and the comments make the same assertion.

Recommendation: Correct all three subjects according to the verified mapping of original identifiers; do not assign the same reason to Sub43 without evidence. The reason mapping should include the data source and group to avoid misuse for identical Sub identifiers across different cohorts or generic inputs. For specific sources, see the main-dataset review and the data records in the original paper.

Acceptance criteria: The three known cases have correct explanations, while unknown reasons remain explicitly unknown; stroke reasons must not be applied to identical IDs in healthy-control/custom data.

## T6: Response metadata field semantics still need organizing—lower priority, complete before actual collection

`extract_openai_metadata()` still writes `id="chatcmpl-RESPONSE"` into request_id even when the response object has `_request_id="req-REQUEST"`. Request identifiers, message identifiers, and response identifiers from different vendors are currently mixed in the same field. Traceability is better than before, but the field meaning is inconsistent.

Recommendation: Save request_id and response/message_id separately, leaving missing values empty rather than substituting one under another name; retain JSON-serializable nested details in usage, as the current `_usage_dict()` filters out nested dictionaries. The complete SDK dependency lock and small actual-interface examples remain unverified and should be completed before formal collection.

This round checked only local extraction functions and mock objects; no claim was made on that basis that actual server-side fields are necessarily complete.

## Known unfinished items, no longer conflated with “failed fixes”

- Individual toe-off, age, and other information are still intentionally excluded from the input. This can serve as a predefined simplified-input condition, but phase interpretation should be limited; incorporate them later if the scope of clinical interpretation is expanded.
- Formal rating forms/case reference checklists and expert pilot rating still need to be organized. Correcting the plan in README does not mean the materials have already been produced.
- A threshold change remains a methodological change, and the existing sensitivity explanation should be retained; there is no need to repeatedly roll back the already-fixed multi-interval algorithm.
- The acceptance script can now exit on some key failures, but the threshold-table/calibration sections still mainly calculate and save results, without failure conditions tied to explicit expected values. The final ALL CHECKS PASSED should not be interpreted as meaning that every number has been automatically checked against a reference.

## Recommended next steps

Prioritize fixing T1 and T2, then add narrowly scoped regression tests for T3–T5. Complete T6 and the full SDK lock before actual collection. Do not repeatedly modify the core signal-extraction logic that has already passed.

Then prepare development materials for 3–5 cases and a small number of v2 examples to check the final input and rating feasibility. Whether to call paid APIs remains subject to user authorization.

Evidence: `review3/probe.py` / `probes.json`, `entrypoints.py` / `entrypoint_checks.json`, `Sub10_LOO_input.txt`, `source_manifest.json` and `source_end_check.json`.
