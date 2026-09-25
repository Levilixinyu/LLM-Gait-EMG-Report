# Fifth independent review: Two integration gaps remain in packaging

Date: 2026-09-16. Addresses the four T1 closeout items from the fourth round; this report takes precedence over historical conclusions from previous rounds.

## Conclusion

45 existing tests passed. Success-status validation, isolation of corrupt archives, and rejection of reports with different inputs based on frozen task hashes all passed independent re-verification; after rerunning, the current packets directory also no longer retained old subjects. However, the path from the actual generation entry points to the packager is blocked by the new task manifest, and the answer key for the old rating packets was not archived with them. T1 cannot currently be marked fully complete.

This round does not modify production source code, call paid APIs, or regenerate formal data. It only adds audit/review5 reproduction materials and this report, and updates the handoff document. Compared with the fourth round, only four production/test files changed: blinding.py, two generation scripts, and test_packet_selection.py. 31 Python files were snapshotted to /private/tmp/gait-review5, and the final hash recheck found no changes. Feature extraction and main-dataset reading are unchanged; this round does not repeat the full data review. Previous-round conclusions remain valid within their original scope.

## Passed; no further repeated modifications

- Full existing test suite: 45 passed in 1.59s.
- A valid set with normal success codes from all three providers correctly packaged 3 entries.
- OpenAI content_filter with text present and no truncation was rejected; OpenAI incorrectly using Anthropic end_turn was also rejected.
- With all three types of superseded archives—corrupt JSON, an array, and null—present simultaneously, the valid current set still completed anonymization and packaging.
- Gemini using different input was correctly rejected when it did not match the frozen expected task hash. Unexpected subjects were also rejected; existing tests additionally cover missing expected subjects.
- The two actual generation entry points were connected to mock providers: each generated 3 entries on the first run and made 0 additional calls on the second run, and both wrote task manifests containing 3 items.
- After rebuilding from an isolated report directory without the manifest file, the current rating packets matched the new answer key, and old subject packets were no longer mixed into the current packets.

## F1: The packager treats the task manifest written by the generator as a report (high priority, blocks the normal workflow)

Locations: scripts/generate_pilot_reports.py:147, scripts/generate_control_spotcheck.py:147; src/eval/blinding.py:111.

Both entry points write task_manifest.json to OUT_DIR. _select_current_reports runs glob("*.json") on that directory, excluding only superseded; it therefore treats the task manifest as an ordinary report and raises an error because it has no report_text.

The independent reproduction used both actual main() functions, replacing only the data loaders, providers, and expensive file hashing, then called load_task_manifest and create_rating_packets according to their interfaces, passing v2, the three expected providers, and the task manifest. Both entry points failed:

    PacketSelectionError: blank/non-string report_text: task_manifest.json

This is not a model request failure or a data issue; the new file conventions for generation and packaging are not aligned. Existing tests manually construct report JSON and do not include the manifest produced by the actual generation scripts, so they missed this issue.

Recommendation: Move the manifest to a separate metadata location and align all callers; or explicitly exclude the agreed manifest file in the report selector while continuing to raise strict errors for genuinely corrupt reports. Do not indiscriminately ignore all files without report_text, as this could silently swallow corrupt reports.

Acceptance criteria: Connect both actual generation entry points to mock providers → retain all files in the generated directory unchanged → load the manifest → package. Both must succeed, with exactly three entries per subject and matching answer keys. Different inputs and missing tasks must still be rejected.

## F2: Only old rating texts are archived; the old answer key is not retained (medium priority, historical review traceability)

Location: src/eval/blinding.py:244–263.

Independent reproduction: First package Sub01, then package Sub02 into the same output directory. The old Sub01.json is moved into packets.previous-<ts>/, but the old answer_key_DO_NOT_SHARE.csv is overwritten, and none of the CSVs in the output directory retain the original answer key. Both old and new packets also start numbering from R0001, so the new answer key cannot be used to interpret the old ratings.

What has been fixed is “old subject files left in the current directory”; what has not been fixed is “complete retention of old batches.” This round does not assert that formal rating data have been lost, nor does it describe an issue in a temporary test directory as an incident affecting existing research data.

In addition, the current staging area contains only report packets: packets are switched first, then the answer key and rubric are written. The documentation's claim that “packets, answer key, and rubric are fully built before being published together” does not match the implementation. A file-write exception could leave new reports paired with an old/incomplete answer key; this is a judgment based on static code paths, and no disk-failure injection testing was performed in this round.

Recommendation: Prefer a fresh, separate batch output directory and reject overwriting an existing batch; this is already sufficient to meet the previous round's requirements, without complex transactions. If directory reuse is retained, build and archive packets, the answer key, rubric, and corresponding task manifest as a complete batch, with the answer key always confidential and bound to that batch. Do not place the answer key in the packets subdirectory given to blinded expert raters.

Acceptance criteria: Package two different batches consecutively, with both retaining their own complete anonymization mappings; each batch's rating packet IDs must correspond one-to-one with its own answer key. Alternatively, reject reuse of an existing batch directory outright, leaving the old files byte-for-byte unchanged.

## Evidence and next steps

- review5/source_manifest.json, source_end_check.json: Source-code snapshot and final consistency check.
- review5/test_results.txt: Existing test results.
- review5/entrypoints.py, entrypoint_checks.json: Reproduction of failures from both actual generation entry points to the packager; mock models, no network calls.
- review5/packaging_probes.py, packaging_probes.json: Verification of success status, corrupt archives, task hashes, current packet cleanup, and loss of the old answer key.

The next round should only assess acceptance of F1 and F2 and related normal-workflow regression tests; T2–T6 and the passed T1 checks remain valid. There is no need to call paid models or recompute the main dataset to verify these two items. Once they pass, proceed to the planned small real-SDK examples, study protocol, and expert pilot evaluation preparation; passing code checks does not mean passing clinical validity assessment.
