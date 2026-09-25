# Fourth independent review: Core fixes passed; blinded-rating packaging awaits closeout

Date: 2026-09-16. Addresses T1–T6 from the previous round; this round's status takes precedence over historical conclusions from the third round.

## Conclusion and scope

T2–T6 passed within the scope of this round's checks; T1 has resolved the issue of normal superseded archives being directly mixed into rating entries, but the packaging workflow is not yet complete end to end. The remaining work is grouped into one task: ensure that the report packets delivered to experts come from the expected tasks for this round, all successful and using the same experimental input, and that the output directory is consistent with the answer key. This does not call for discarding the already-fixed feature extraction or generation workflows.

This round added only review records and reproduction scripts; it did not modify production source code, call real model APIs, or regenerate formal reports. Code was executed from an isolated snapshot in /private/tmp/gait-review4; 31 source/script/test files were rechecked at the end of the review, and all hashes were unchanged. Summaries for the main dataset were recomputed using curves.npz verified in the previous round; this round did not reread the full MAT collection or conduct expert clinical validity validation.

## Accepted items

- Project tests: 40 passed (1.56 seconds). This demonstrates that existing tests pass, not that the additional edge cases below are covered.
- T2: Reference source, subject count, point count, method, and excluded subjects enter the input with the metadata. The actual text for Sub10 is “137 healthy subjects (leave-one-out, excluding Sub10), 1001 phase points, source: main_cohort_excel”. The 138-subject background is explicitly labeled COHORT BACKGROUND and is no longer misrepresented as the actual reference for this case. A custom reference with 3 subjects and 101 points no longer inappropriately uses the main-cohort description.
- T3: With time frozen to the same second, three consecutive writes retained all three versions: FIRST/SECOND/THIRD.
- T4: Non-object JSON returns an invalid record and no longer crashes by calling .get.
- T5: Stroke subjects Sub08/Sub47/Sub48, documented as having no analog data, use the corresponding explanation; unspecified missingness retains an unknown reason, and grouping prevents healthy controls with the same names from being misclassified.
- T6: request_id and response_id are stored separately, and nested usage information now has regression coverage; a mock OpenAI response correctly retained req-REQUEST and chatcmpl-RESPONSE.
- Both actual generation entry points were connected to mock providers: each made 3 calls on the first run and 0 additional calls on the second; patients used the full-control reference, controls used a leave-one-out reference excluding themselves, and all recorded v2.
- 238 real-curve summaries passed strict JSON serialization; previous fixes for multiple activation segments, cross-cycle intervals, missing-value explanations, and other issues remain effective.

## Sole remaining work item: T1 end-to-end completion of blinded-rating packaging

### 1. Incomplete success-status validation (high priority)

Location: src/eval/blinding.py:95–104. Currently, stop_reason is only required to be nonempty. Independent reproduction: OpenAI with stop_reason=content_filter, truncated=False, and text present was still packaged with the other two providers into 3 rating records.

Recommendation: Reuse the provider-specific successful termination-reason validation defined in generation_cache. Reject failure codes, unknown codes, and success codes belonging to other providers. Mock results in tests/test_packet_selection.py default to end_turn for all providers; these also need to be changed to each provider's actual corresponding success code to avoid embedding incorrect conditions in the tests.

Acceptance criteria: A normal three-model set succeeds; any non-success code must raise an explicit error, and a seemingly complete new set of rating packets must not be published.

### 2. Skipped corrupt archives still cause anonymization to crash (medium priority)

Locations: src/eval/blinding.py:29–46, 148. After the selector skips superseded, _build_strip_patterns scans the entire directory again and parses all JSON. Independent reproduction: A corrupt current JSON was normally archived via place_record and a valid new report was written; the selector skipped that archive, but anonymization still raised JSONDecodeError.

Recommendation: Build model anonymization rules from the already selected records, without traversing unselected files a second time.

Acceptance criteria: With superseded archives in the form of corrupt JSON, arrays, or null alongside valid current reports, only current valid records are packaged and anonymization completes; corrupt current candidates should still raise errors.

### 3. This round's tasks and shared experimental input are not checked (high priority)

Location: src/eval/blinding.py:102–124. prompt_version=v2 plus the expected provider set cannot prove that reports come from the same input. Independent reproduction: All three providers used v2, with one report each and successful termination, but Gemini used DIFFERENT INPUT; 3 entries were still packaged.

Recommendation: Use a frozen task manifest to specify expected subjects, sides, provider/model, and corresponding task hashes, then check the shared experimental input and reference. Full task hashes inherently differ across providers, so the three providers' task hashes cannot be directly required to be equal; each should match its own expected task, while ensuring that inputs/references that should be consistent are consistent. Preserve model-specific parameter differences allowed by the design.

Acceptance criteria: The same v2 label but different inputs/references, outdated tasks, or omission of an entire subject are all blocked; the normal expected task set passes.

### 4. Reusing the output directory leaves old rating packets behind (medium priority)

Locations: src/eval/blinding.py:139–140, 172–179. Output permits an existing directory, writes only current subject files, and rewrites the answer key without handling old subject files. The independent reproduction inserted a mock old subject packet after successful output; after repackaging, the old packet was still present. The current answer key therefore cannot represent all rating files in the directory; this round does not assert that formal output has already been contaminated.

Recommendation: Prefer requiring a fresh or empty output directory, or use an approach that builds everything in a temporary location before publishing it together. Do not directly delete old directories that may already contain ratings. Before publication, verify the expected file set and one-to-one correspondence between anonymized IDs and the answer key.

Acceptance criteria: Explicitly reject reuse of a directory containing old packets, or generate a complete, consistent new directory; no old packets absent from this round's answer key may be left behind.

## Evidence and reproduction boundaries

- review4/source_manifest.json, source_end_check.json: Source code tested and final consistency verification.
- review4/packaging_probes.json, probe.py: Independent reproductions of the four items above; operations confined to temporary directories.
- review4/entrypoint_checks.json, entrypoints.py: Actual generation entry points connected to mock providers.
- review4/probes.json, regression_probes.py: Regression checks for archiving, caching, references, and 238 real summaries.
- review4/Sub10_LOO_input.txt: Actual complete model input; see line 16.

Note: claims_138=true, carried over from the old probe, only means that the background text contains 138; mentions_LOO_method_as_actual_reference=false uses an old fixed-phrase match. Neither constitutes a failure judgment in this round; the actual line 16 already correctly distinguishes the reference. The complete input and this report's conclusions take precedence.

After T1 is fixed and the meaningful integration tests above are added, work can proceed to the preplanned SDK/real small-example compatibility checks and formal v2 generation. Freezing the statistical plan, expert reference standards, and rating design remain research-stage work; this round's code acceptance does not replace that work or support premature comparison of the models' clinical capabilities.
