# Five-case data cards: Use and return

Currently use the [concise clinical data cards](data_cards_v5/index.html). These are review materials confirmed as usable by the user; their clinical content still awaits expert approval.

## How to complete

1. Open the overview in a browser, enter the expert's name or identifier, and click “Start／Load review”.
2. Confirm the first 4 common requirements only once.
3. Review each case's curves, answer 3—6 targeted questions, and select “Retain／Revise wording／No need to include”. If revision is needed, provide the suggested report wording and rationale; you may also add important findings.
4. For open-ended questions such as “which joints or activity periods are worth describing”, enter specific findings before freezing the checklist; retaining only the question itself does not count as a completed reference answer.
5. After completion, export the review JSON and return it to the researcher. You may also export a CSV for viewing in Excel; import the JSON to resume completion or switch devices.

| Case | Individual case entry |
|---|---|
| Stroke Sub09, affected side | [Data card](data_cards_v5/stroke_Sub09_P/card.html) |
| Stroke Sub05, affected side | [Data card](data_cards_v5/stroke_Sub05_P/card.html) |
| Stroke Sub50, affected side | [Data card](data_cards_v5/stroke_Sub50_P/card.html) |
| Stroke Sub47, missing EMG | [Data card](data_cards_v5/stroke_Sub47_P/card.html) |
| Healthy control Sub49 | [Data card](data_cards_v5/control_Sub49_avg/card.html) |

Individual case pages include the same general section; previously entered general comments can be reused with the same browser, reviewer, and version. The exported `common_rules` is the general review section, not a sixth subject. Import review files containing multiple cases through the overview.

Browser storage does not automatically return your review or rewrite the original files on disk, so be sure to export. The first and second experts should use different identifiers; an individual's completed review does not constitute joint finalization. Comments are not automatically migrated between material versions.

## Points to note during review

- Focus on judging findings that are clinically worth describing; there is no need to restate every number or check the algorithm interval by interval.
- 0% is the window boundary and does not automatically equal physiological muscle activation onset. Cross-cycle intervals are not split at 0% into new activations; exceeding the threshold throughout also does not establish sustained abnormal contraction. Failure to repeat this explanation alone does not incur a score deduction.
- The complete model input, reference description, and calculation methods can be expanded as needed. Curves and precise reference tables are supplementary materials for experts; the model must not be penalized for failing to mention information it did not receive.
- The reference band only describes the distribution of the healthy reference population; it is not a diagnostic boundary. Reports may state that evidence is insufficient and should not make a diagnosis or propose a treatment plan based on these materials alone.
- Missing EMG does not mean no muscle activity. Use the display precision in the model input when checking numerical values.

## Files and maintenance

Retain `data_cards_v5/` as the only data-card package in use. The old `data_cards/` and v1—v4 have been removed; historical verification records and cleanup manifests remain in audit for traceability and are no longer review entry points.

Generation script: `scripts/build_expert_trial_package.py`. When a new version is needed, use a new output directory to avoid overwriting expert materials:

```sh
python scripts/build_expert_trial_package.py --verified-cache --out docs/expert_trial/data_cards_vNEXT
```

Omit `--verified-cache` to read the released Excel/MAT files directly; see `requirements-cards.txt` for plotting dependencies. The generator does not call model APIs. The package manifest records data sources, code hashes, and deliverable hashes.

All five cases are development cases, used only to prepare expert checklists and refine the process. The concise clinical version has passed 4 related tests and 19 browser checks; see `audit/card_review_ui/v5/` for evidence.
