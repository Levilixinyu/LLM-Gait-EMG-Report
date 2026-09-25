# Source audit of confirmed-error reports

This is an assistant audit requested after unblinding on 2026-09-23. It is not a fourth independent expert assessment and does not replace any human judgment.

The main endpoint means **a report has at least one expert-confirmed issue under the study's evidence rules**. It does not mean the whole report is wrong, that a clinical diagnosis is false, or that every issue is equally consequential. Coverage and correctness are separate.

## Findings

All 52 frozen confirmed groups were located in their original reports. The 39 report byte hashes match the freeze, and all 26 case system/user inputs match the delivery integrity record. No quote mismatch or inclusion of a frozen Pending group as a confirmed error was found in this checked set.

The source audit separates four evidence classes. These are explanatory assistant classifications, not replacement scores or validated severity categories:

| Evidence class | Groups | Meaning |
|---|---:|---|
| Direct inconsistency | 15 | Numbers, count/rank, metric/pair or interval identity, or algorithm explanation conflicts with supplied facts/definitions. |
| Unprovided detail | 12 | Five sex assignments, five unrecorded-speed/cadence claims, and two medial-head designations lack model-visible support. They are not proven false in the source population. |
| Unsupported inference | 17 | Mostly rounded-threshold/interval certainty, plus an unsupported extension of a reference property. Actual signal continuity or clinical status was not independently determined. |
| Wording-sensitive interpretation | 8 | An Error reading is defensible, but a competing permitted or less assertive reading should be acknowledged. These are not eight established misratings. |

Examples of direct problems: 13.7 versus 3.65-4.61 is approximately 3-4 times, not tenfold (AG001); BF 2.3 is below, not inside, 3.65-4.61 (AG021); 68-72/72-81 are outside a wrapping 95-61 interval (AG027); TA 67% is not the highest coverage when ERS is 70% (AG032); 0.58 is equally distant from 0.48 and 0.68 at displayed precision (AG033).

The model system prompt explicitly warns that rounded coverage alone cannot establish absence of a below-threshold segment. Thus an explicit 'did not fall below anywhere' claim can violate the task even if an eventual raw-curve inspection happens to show no gap. Conversely, merely reporting 100%, reporting retained intervals, and reporting supplied boundary continuity are allowed. No hypothetical short dip is treated as an observed dip in this audit.

### Combined interval and boundary evidence was checked

It would be insufficient to dismiss a report based on coverage rounding alone if other supplied fields established the stronger statement. The current repository's circular-run implementation was therefore tested with a concrete counterexample consistent with the supplied threshold/duration definition:

- 1001 samples; all equal to 1 except indices 1 and 999, which equal 0; threshold 0.2.
- Exact coverage is 99.8001998%, displayed as 100%.
- The retained long run is 0.2%-99.8%, displayed as 0%-100%.
- The first and last samples are above threshold, so the boundary-continuity flag is true.
- Those two boundary samples form a separate short circular supra-threshold run, which is removed by the 3% ABOVE-threshold duration filter. The two sub-threshold samples are not filled or removed by a gap filter.

The three displayed fields are therefore identical to the all-above-threshold example, despite the two dips. This validates the logical evidence limitation even when interval and boundary information are combined. It does not show that any participant had this signal. Four synthetic scenarios and the implementation hash are recorded in [the counterexample record](THRESHOLD_DISPLAY_COUNTEREXAMPLE.json).

## Wording boundaries to preserve

The workbook gives the original line/context, case input, recorded expert reasons and both interpretations for every group. The following eight are judgment-dependent:

- **AG004 / R3077041C029681A9 / stroke_Sub19_P / line 43**: The question says 'reduced sagittal joint ROMs observed here'; no matched ROM comparator is supplied. Error is defensible if this asserts an observed reduction relative to normal. However, the report also says ROM alone does not confirm clinical restriction and asks about alternative explanations. D03 permits clinical questions. This is a presupposition/description boundary, not proof of a real contracture or a clear diagnostic assertion. A descriptive-small-ROM reading is a competing interpretation.

- **AG011 / R248AD7BC90BAC7D5 / stroke_Sub02_P / line 40**: The input's -6.6% index uses the mean of the two step lengths as denominator. A conventional percentage shortening relative to the non-paretic step would be 200*6.6/(200+6.6) = 6.389%. Error is defensible if '6.6% shorter' asserts that different denominator. The same report identifies the symmetry index correctly in Section 1, and the question calls it the 'noted asymmetry'. It may be shorthand for that index. The quote does not explicitly say 'relative to the non-paretic step'; an unequivocal denominator error should not be claimed without acknowledging this reading.

- **AG019 / RA5354EEC7114E5CC / control_Sub62_avg / line 48**: The phrase 'no retained below-threshold segment' misnames the output, but can be read as an imprecise retained-list description. The following 'envelope that stays above' supports the stronger reading used by the raters; the next paragraph also warns the list is not exhaustive. Compare consistently with closed Pending D002/D004. The quoted retained terminology alone does not compel Error. AG020 is a separate, clear algorithm-description error in this same report.

- **AG023 / R25F5AA9361D9E14F / control_Sub06_avg / line 42**: The question calls the pelvic excursion 'constrained', which supports the raters' reading of an unsupported restriction premise. But it expressly asks whether this is the participant's typical mechanics, and does not assert a diagnosis or an observed pathological examination finding. Under D03 a descriptive-small-excursion reading is also plausible. Error and especially the pathology flag depend on interpreting the adjective as impairment; do not describe this as unambiguous hallucinated pathology. The separate medial-head addition remains.

- **AG028 / RDB18B7C593D48194 / stroke_Sub15_P / line 4**: 'Categorized functionally' goes beyond the input's instruction that the ambulator label is a speed band only. This supports a strict instruction-compliance Error. The phrase still ends in 'band' and makes no separate claim about walking independence or safety. A naming imprecision rather than an actual functional conclusion is plausible. The separate medial-head detail remains.

- **AG048 / RA857737CABCC0FB8 / stroke_Sub49_P / line 33**: 'Continuous 100% threshold coverage observed' plus Section 2's continuous-coverage heading supports the raters' uninterrupted-signal reading. However, both refer to supplied mean-envelope coverage, and the report does not literally add a no-gap/no-sample claim. The boundary between reporting 100% coverage and asserting full-precision continuity remains wording-sensitive. The clinical correlates in the question are not themselves errors. Do not call the frozen Error an unequivocal physiological falsehood.

- **AG050 / R1C5F93E05D9CC9EA / control_Sub62_avg / line 47**: BF has 95% coverage split between two retained intervals, and the question calls coverage 'high continuous'. If that means a single uninterrupted BF run, it conflicts with the input. Section 2 correctly lists both intervals and 95%; 'high continuous envelope coverage' may be loose description of the continuous-envelope metric rather than a single-run claim. This is not automatically a 100%-coverage allegation. AG047 remains independently supported.

- **AG051 / RAF417EE5FDC33A78 / stroke_Sub13_P / line 11**: The heading 'Continuous Above-Threshold Activity' and 'maintained ... for 100%' support a strict whole-cycle reading. But the sentence's explicit adverb 'continuously' modifies 'across the cycle boundary', which is supplied, and the 100% number itself is supplied. Do not penalize boundary continuity itself or invent physiological contraction. The inference from heading plus numeric restatement is wording-sensitive and less explicit than 'did not fall below anywhere'. The clinical question on reported coverage is allowed.

## Report-level implications

Four reports have no other frozen confirmed issue outside the highlighted wording-sensitive set:

- R3077041C029681A9 (stroke_Sub19_P): AG004; existing frozen Pending groups: 0.
- R248AD7BC90BAC7D5 (stroke_Sub02_P): AG011; existing frozen Pending groups: 0.
- RA857737CABCC0FB8 (stroke_Sub49_P): AG048; existing frozen Pending groups: 1.
- RAF417EE5FDC33A78 (stroke_Sub13_P): AG051; existing frozen Pending groups: 1.

The other 35 error-positive reports retain at least one supported issue outside this highlighted set. This is a dependency check, not a revised error count. Even those supported issues may be minor source-fidelity or precision violations rather than clinical mistakes. If a sensitive claim were later changed, reports with existing Pending claims would not automatically become error-free.

The control Sub06 pathology flag depends on the constrained-ROM reading (AG023). The report also has a separate source-fidelity error (AG049), so its any-error status and its pathology flag are different questions. This audit changes neither.

## Scope and next use

Read the result as an **expert-confirmed task-error endpoint**, and present representative error types alongside rates. Do not call these clinical misdiagnosis rates or imply that all three original independent raters initially reached the same result. Do not discard weak-looking issues selectively after knowing model identities.

No full rereview is mandated by this audit. If the study lead decides the highlighted wording boundaries require expert reconsideration, send both readings without a requested outcome, preserve each individual response, and record any resulting revision as post-unblinding. The frozen primary analysis stays versioned; a later sensitivity analysis is not a silent replacement.

This review inspected all registered confirmed anchors and their relevant original context and inputs, with complete-report rereading for selected scope disputes. It did not recompute raw curves, independently diagnose participants, grade clinical harm, or perform an exhaustive new search for missed issues in all 105 reports. The 16 closed Pending groups remain unchanged.

Files: [claim-by-claim workbook](Confirmed_error_source_audit.xlsx) and [verification/provenance record](BUILD_RECORD.json).
