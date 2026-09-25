"""Render a post-unblinding source audit; never change expert decisions.

The assessments below are authored assistant interpretations, not computed truth
labels or a fourth expert rating. Source/quote checks are mechanical only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.features.emg_signal import analyze_activation
OUT = ROOT / "docs/formal_study/confirmed_error_source_audit_v1"
FREEZE = ROOT / "docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json"
MANIFEST = ROOT / "docs/formal_study/analysis_freeze_v1/FREEZE_RECORD.json"
INTEGRITY = ROOT / "data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/package_integrity_snapshot.json"
PACKAGE = ROOT / "docs/formal_study/independent_expert_review_template_v1/Independent_expert_review_template.zip"

DIRECT = {1, 2, 3, 6, 9, 10, 20, 21, 27, 32, 33, 34, 35, 38, 41}
UNPROVIDED = {5, 8, 12, 13, 15, 17, 24, 30, 43, 44, 49, 999}
SENSITIVE = {4, 11, 19, 23, 28, 48, 50, 51}
LABELS = {
    "D": "Direct inconsistency with supplied facts or definitions",
    "F": "Unprovided participant or recording detail",
    "I": "Inference exceeds supplied evidence",
    "W": "Wording-sensitive interpretation",
}

# Each tuple contains the audit assessment and its appropriate limitation.
NOTES = {
1: ("13.7 / 4.61 = 2.97 and 13.7 / 3.65 = 3.75. The supplied comparison is not approximately tenfold. The false magnitude comparison is in a declarative sentence before a permissible clinical question.", "This is a quantitative wording error, not evidence of an incorrect diagnosis."),
2: ("The input lists seven coverages at least 73% (100, 73, 73, 100, 77, 87, 98), all with boundary continuity. The report's exact-count summary says six of seven.", "Earlier correct reporting preserves coverage credit; it does not explicitly retract this later count."),
3: ("10.56 remains below 10.7 at displayed precision. Under ordinary nearest rounding, 10.56 is below 10.565 and 10.7 is at least 10.65; the intervals do not overlap. Rounding does not make their numerical order indeterminate.", "Clinical classification remains uncertain; only the stated rounding-based inability to order the numbers is rejected."),
4: ("The question says 'reduced sagittal joint ROMs observed here'; no matched ROM comparator is supplied. Error is defensible if this asserts an observed reduction relative to normal. However, the report also says ROM alone does not confirm clinical restriction and asks about alternative explanations.", "D03 permits clinical questions. This is a presupposition/description boundary, not proof of a real contracture or a clear diagnostic assertion. A descriptive-small-ROM reading is a competing interpretation."),
6: ("The report applies the 3% retention rule to the approximately 2% GAS residual region. The model input defines retention for ABOVE-threshold runs. It does not retain or discard below-threshold gaps using that duration rule.", "This is an algorithm-description error; it does not establish muscle inactivity in the residual region."),
7: ("The three GAS/BF/ERS entries add 'no below-threshold segment detected' to rounded coverage and retained above-threshold intervals. No independent below-threshold detection result is supplied.", "The issue is unsupported certainty, not a demonstrated actual gap. Repeated channels are one frozen group."),
9: ("The ST retained interval is 52%-51% wrapping, whereas the report groups ST with full-window retained intervals. Its explicit refusal to assert no below-threshold samples is appropriate, but does not correct that interval identity.", "Keep the factual interval mismatch distinct from the appropriate rounding caveat; extra category tags are not additional errors."),
10: ("The input contains TA/GAS and RF/BF only. The overview adds RF-vs-GAS/BF, introducing GAS into the second pair. The later correct RF/BF entry is not an explicit correction of the overview.", "This is a pair-label/source-fidelity error, not evidence that the numeric CCI computation was wrong."),
11: ("The input's -6.6% index uses the mean of the two step lengths as denominator. A conventional percentage shortening relative to the non-paretic step would be 200*6.6/(200+6.6) = 6.389%. Error is defensible if '6.6% shorter' asserts that different denominator.", "The same report identifies the symmetry index correctly in Section 1, and the question calls it the 'noted asymmetry'. It may be shorthand for that index. The quote does not explicitly say 'relative to the non-paretic step'; an unequivocal denominator error should not be claimed without acknowledging this reading."),
14: ("ERS 100% and 0%-100% are supplied as displayed summaries; the report adds 'establishing no below-threshold segment'. The system prompt explicitly disallows establishing absence from rounded coverage alone.", "This is overprecision beyond model-visible evidence, not proof that the measured ERS curve contains a gap."),
16: ("The ERS entry adds a no-below-threshold conclusion to rounded 100% coverage and a displayed 0%-100% interval. That stronger negative finding is not independently supplied.", "The study rule supports Error for the added inference, not for accurately repeating the displayed coverage."),
18: ("The report explicitly says the supplied evidence 'does establish' that ERS never fell below threshold 'anywhere'. The following disclaimer concerns contraction/strides, not sample-level certainty.", "Defensible E03 under the existing prompt; not an observed biological or diagnostic error."),
19: ("The phrase 'no retained below-threshold segment' misnames the output, but can be read as an imprecise retained-list description. The following 'envelope that stays above' supports the stronger reading used by the raters; the next paragraph also warns the list is not exhaustive.", "Compare consistently with closed Pending D002/D004. The quoted retained terminology alone does not compel Error. AG020 is a separate, clear algorithm-description error in this same report."),
20: ("The report says sub-threshold segments shorter than 3% would not be retained. The duration filter retains supra-threshold runs, not sub-threshold gaps, so it applies the rule to the wrong object.", "The correct conclusion that the list is not exhaustive does not cure the incorrect explanation."),
21: ("BF 2.3 is below 3.65, not inside 3.65-4.61. Including it with RF/VL/ST in the 'within' statement is a numerical misplacement.", "The same sentence refuses muscle-specific classification. E01 is well supported; E05 should not be added merely for using the endpoint span descriptively."),
22: ("The whole-section comparability paragraph asserts that leave-one-out limits would be wider. The input supplies higher leave-one-out extreme-EMG reference values, not a universal widening of kinematic/composite limits.", "This is an unsupported extension of a supplied reference property, not proof that the actual missing limits are narrower. Its application to this case's kinematic section supports case-error scope."),
23: ("The question calls the pelvic excursion 'constrained', which supports the raters' reading of an unsupported restriction premise. But it expressly asks whether this is the participant's typical mechanics, and does not assert a diagnosis or an observed pathological examination finding.", "Under D03 a descriptive-small-excursion reading is also plausible. Error and especially the pathology flag depend on interpreting the adjective as impairment; do not describe this as unambiguous hallucinated pathology. The separate medial-head addition remains."),
25: ("The ERS sentence makes the envelope the subject and asserts continuously above threshold throughout displayed 0%-100%. The input gives rounded summaries, not a full-precision every-sample guarantee.", "This is a strict evidence/precision violation under rubric 8. It does not show the actual curve was discontinuous."),
26: ("'Remaining above threshold throughout the entire cycle' adds an unqualified whole-window signal assertion to the interval listing. The repeated Section 4 premise belongs to the same group.", "The clinical question itself is allowed. This is an evidence-boundary issue, not continuous physiological contraction."),
27: ("A wrapping 95-61 interval is the union of 95-100 and 0-61. The 68-72 and 72-81 segments are outside it. Shared displayed endpoint 72 also does not establish true overlap.", "The report denies separate physiological events; that physiological allegation should not be revived. The containment error is independently sufficient."),
28: ("'Categorized functionally' goes beyond the input's instruction that the ambulator label is a speed band only. This supports a strict instruction-compliance Error.", "The phrase still ends in 'band' and makes no separate claim about walking independence or safety. A naming imprecision rather than an actual functional conclusion is plausible. The separate medial-head detail remains."),
29: ("The report explicitly says the supplied display 'establishes no below-threshold segment' in BF/ST/ERS. A no-contraction disclaimer does not limit that stronger signal-level conclusion.", "The supplied display does not prove absence at full precision; actual gaps were not investigated here."),
31: ("The report uses an 'explicit 0-100% interval' to support absence of a below-threshold segment in ERS. The interval endpoints and coverage are displayed, not an unrounded negative gap finding.", "This is an inference beyond supplied precision, rather than a disproved raw-signal statement."),
32: ("TA coverage is 67%, but ERS coverage is 70%. Calling TA the highest-coverage channel is wrong, even though TA does have the largest max-|z| and four intervals.", "The question's technical possibilities remain permissible; only its false ranking premise is at issue."),
33: ("At displayed precision, 0.58-0.48 = 0.10 and 0.68-0.58 = 0.10. It is not closer to the lower endpoint than to the median.", "Unknown hidden precision cannot support either closer-than statement; this is a small numerical comparison error, not a clinical conclusion."),
34: ("16.8 / 4.61 = 3.64 and 16.8 / 3.65 = 4.60, not approximately tenfold. The ratio comparison remains independently assessable inside a question.", "This is a quantitative exaggeration; the proposed signal-quality assessment is permitted."),
35: ("The VL displayed wrapping interval 88-54 spans about 66%, whereas total coverage is 69%. Two endpoints rounded to integer percent plus rounded coverage and one-sample convention do not explain a three-point difference on a 1001-point grid. Short discarded supra-threshold runs are a possible additional contributor.", "The cause was not supplied and was not recomputed here. Do not replace the unsupported rounding-only explanation with a claim that discarded runs definitely occurred."),
36: ("The report asserts ERS 'did not fall below' threshold 'anywhere'. This directly exceeds what rounded coverage and displayed endpoints establish under the task rule.", "The mean-envelope disclaimer excludes physiological inference, but does not resolve the sample-precision claim."),
37: ("The report equates all regions outside retained intervals with below-threshold signal. Short supra-threshold runs can fail the duration criterion; absence from the retained list does not establish amplitude below threshold everywhere outside it.", "This is insufficient evidence for an interval-wide assertion; it is not proof that discarded short runs actually existed in this case."),
38: ("Both BF 3.3 and ERS 3.3 are below the supplied lower endpoint 3.65, not within 3.65-4.61. The later correct ERS statement does not explicitly retract the initial shared claim.", "Additional E05 tags remain individual judgments. The common direct error is numerical placement; do not use an unsupplied LOO cutoff to classify the participant."),
39: ("The ERS entry asserts that the envelope exceeds threshold continuously from 0 to 100%, rather than only reporting displayed coverage. This exceeds the supplied rounding precision under rubric 8.", "A strict task-evidence error, not an established clinical abnormality or proof of discontinuity."),
40: ("The report assigns the entire ERS region between displayed endpoints 34 and 44 to below-threshold amplitude. Retained intervals alone cannot exclude short unretained supra-threshold runs within that region, and endpoints are rounded.", "The complement of sample coverage must not itself be said to contain supra-threshold discarded runs: those runs still count in raw coverage. The remaining issue is the interval-wide location assertion."),
41: ("The overview names RF/GAS instead of the supplied RF/BF pair; Section 4 also attributes CCI to RF/VL and BF/ST. None of these extra measured pairings is supplied.", "Group the repeated pair-provenance mistake once. The correct Section 2 pair/value remains valid coverage evidence."),
42: ("The RF entry adds 'leaving no below-threshold segment' to the displayed full-cycle summary, without sample-level evidence that establishes this absence.", "This is a precision/evidence error, not proof of a clinical activation disorder."),
45: ("RF/ST/ERS entries explicitly infer no below-threshold segment. ST additionally has a 52%-51% wrapping interval despite coverage rounded to 100%, illustrating why rounded coverage does not erase the displayed gap.", "Count repeated inference once as frozen. It does not imply a physiological silent period."),
46: ("The GAS/BF parentheticals explicitly add 'continuously above threshold' to displayed 100% values without a local precision qualification. The strict rubric distinguishes that from reported interval extent.", "The claim is unsupported at full precision; the underlying signal's actual continuity is not disproved by this audit."),
47: ("The ERS sentence explicitly asserts continuous exceedance from 0 to 100%, repeated in Section 4. The rounded input does not establish an unrounded whole-cycle guarantee.", "Keep this separate from the BF wording in AG050. Multiple locations of the ERS claim remain one group."),
48: ("'Continuous 100% threshold coverage observed' plus Section 2's continuous-coverage heading supports the raters' uninterrupted-signal reading. However, both refer to supplied mean-envelope coverage, and the report does not literally add a no-gap/no-sample claim.", "The boundary between reporting 100% coverage and asserting full-precision continuity remains wording-sensitive. The clinical correlates in the question are not themselves errors. Do not call the frozen Error an unequivocal physiological falsehood."),
50: ("BF has 95% coverage split between two retained intervals, and the question calls coverage 'high continuous'. If that means a single uninterrupted BF run, it conflicts with the input.", "Section 2 correctly lists both intervals and 95%; 'high continuous envelope coverage' may be loose description of the continuous-envelope metric rather than a single-run claim. This is not automatically a 100%-coverage allegation. AG047 remains independently supported."),
51: ("The heading 'Continuous Above-Threshold Activity' and 'maintained ... for 100%' support a strict whole-cycle reading. But the sentence's explicit adverb 'continuously' modifies 'across the cycle boundary', which is supplied, and the 100% number itself is supplied.", "Do not penalize boundary continuity itself or invent physiological contraction. The inference from heading plus numeric restatement is wording-sensitive and less explicit than 'did not fall below anywhere'. The clinical question on reported coverage is allowed."),
}

SEX = {5, 8, 12, 17, 44}
ABSENT = {13, 15, 24, 30, 43}
for n in SEX:
    NOTES[n] = ("The participant-specific 'him' adds a male designation. Neither saved system nor case input supplies participant sex. Some reports also explicitly acknowledge that sex was not supplied.", "This is unsupported demographic specificity, not proof that the participant is actually female or that the gait interpretation is clinically wrong.")
for n in ABSENT:
    NOTES[n] = ("The input says gait speed (and where applicable cadence) was not provided. 'Unrecorded/not recorded' asserts a stronger fact about source data collection that the input does not establish.", "This is an information-provenance error under the explicit task boundary. It does not prove that the measurements were actually recorded, and is not a diagnostic error.")
for n in (49, 999):
    NOTES[n] = ("Both actual prompts name GAS without a medial-head designation or a channel legend establishing it. Expanding it to 'medial gastrocnemius' adds unsupplied anatomical specificity.", "This is a source-fidelity issue. It does not establish that the actual electrode targeted another head, that standard anatomy is wrong, or that a diagnosis was invented.")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def number(gid: str) -> int:
    return int(gid[2:]) if gid.startswith("AG") else 999


def kind(n: int) -> str:
    return "D" if n in DIRECT else "F" if n in UNPROVIDED else "W" if n in SENSITIVE else "I"


def main() -> None:
    if OUT.exists():
        if "--refresh-unchanged-assistant-output" not in sys.argv:
            raise SystemExit("Audit directory already exists; explicit refresh is required.")
        old = json.loads((OUT / "BUILD_RECORD.json").read_bytes())
        for name, expected in old["outputs_sha256"].items():
            assert sha((OUT / name).read_bytes()) == expected, "Modified audit output; refuse refresh"
    frozen_bytes = FREEZE.read_bytes()
    frozen = json.loads(frozen_bytes)
    manifest = json.loads(MANIFEST.read_bytes())
    assert sha(frozen_bytes) == manifest["dataset_sha256"]
    integrity_bytes = INTEGRITY.read_bytes()
    hashes = json.loads(integrity_bytes)["files_sha256"]
    groups = [g for g in frozen["issue_groups"] if g["decision"] == "Error"]
    assert len(groups) == 52 and len({g["report_id"] for g in groups}) == 39
    assert {number(g["group_id"]) for g in groups} == set(NOTES)
    package_bytes = PACKAGE.read_bytes()
    import io
    z = ZipFile(io.BytesIO(package_bytes))
    prefix = "independent_expert_review/"
    sources = []
    reports, inputs, systems = {}, {}, {}

    def material(case: str, name: str) -> str:
        member = f"{prefix}materials/{case}/{name}"
        b = z.read(member)
        expected = hashes[f"raters/rater2/materials/{case}/{name}"]
        assert sha(b) == expected, member
        sources.append({"Kind": "Model input", "Source": member, "SHA-256": sha(b), "Verified against": "Frozen delivery integrity snapshot"})
        return b.decode("utf-8")

    for g in groups:
        rid, cid = g["report_id"], g["case_id"]
        if rid not in reports:
            member = f"{prefix}reports/{rid}.txt"
            b = z.read(member)
            p = f"docs/formal_study/rating_delivery_v1/rater2/reports/{rid}.txt"
            assert sha(b) == manifest["source_sha256"][p], member
            assert sha(b) == hashes[f"raters/rater2/reports/{rid}.txt"], member
            reports[rid] = b.decode("utf-8")
            sources.append({"Kind": "Original report", "Source": p, "SHA-256": sha(b), "Verified against": "Freeze manifest and delivery integrity snapshot"})
        if cid not in inputs:
            inputs[cid] = material(cid, "model_user_prompt.txt")
            systems[cid] = material(cid, "model_system_prompt.txt")
    assert len(inputs) == 26
    assert len(set(systems.values())) == 1
    for name in ("RUBRIC.md", "CURRENT_REVIEW_SCOPE.md", "EXAMPLES.md"):
        member = f"{prefix}materials/{name}"
        b = z.read(member)
        assert sha(b) == hashes[f"raters/rater2/materials/{name}"]
        sources.append({"Kind": "Delivered scoring material", "Source": member, "SHA-256": sha(b), "Verified against": "Frozen delivery integrity snapshot"})

    # Test the inference, not the participant: even all three displayed fields
    # together are compatible with a pair of below-threshold samples.
    probe = []
    for label, indices in (("All samples above", []), ("One internal dip", [500]),
                           ("One endpoint dip", [0]), ("Two near-boundary dips", [1, 999])):
        curve = np.ones(1001)
        curve[indices] = 0
        result = analyze_activation(curve, threshold_frac=0.2, min_duration_pct=3.0)
        assert result is not None
        probe.append({"scenario": label, "below_threshold_indices": indices,
                      "sample_count": 1001, "exact_coverage": result.above_threshold_pct,
                      "exact_intervals": result.intervals, "boundary_continuity": result.crosses_cycle_boundary,
                      "displayed_coverage": f"{result.above_threshold_pct:.0f}%",
                      "displayed_intervals": [[f"{a:.0f}%", f"{b:.0f}%"] for a, b in result.intervals]})
    assert probe[0]["displayed_coverage"] == probe[3]["displayed_coverage"] == "100%"
    assert probe[0]["displayed_intervals"] == probe[3]["displayed_intervals"] == [["0%", "100%"]]
    assert probe[0]["boundary_continuity"] and probe[3]["boundary_continuity"]
    assert probe[3]["exact_coverage"] < 100

    rows = []
    for g in groups:
        n = number(g["group_id"])
        rid, cid, quote = g["report_id"], g["case_id"], g["exact_anchor"]
        text = reports[rid]
        assert quote in text, (g["group_id"], quote)
        start = text[:text.index(quote)].count("\n") + 1
        lines = text.splitlines()
        context = "\n".join(f"{i+1}: {lines[i]}" for i in range(max(0, start-3), min(len(lines), start+2)))
        if n in SEX or n in (49, 999):
            assert "medial" not in (inputs[cid] + systems[cid]).lower()
        input_evidence = "\n".join(l for l in inputs[cid].splitlines() if l.startswith(("Subject:", "Gait speed:", "Cadence:", "Step length symmetry index:", "Composite kinematic", "Deviation reference", "- GAS:", "- RF:", "- VL:", "- BF:", "- ST:", "- TA:", "- ERS:", "- TA_vs", "- RF_vs", "- AnkleAngles:", "- KneeAngles:", "- HipAngles:", "- PelvisAngles:", "- Above-threshold intervals", "- Step length symmetry index", "- Healthy-cohort CCI", "- Additional source fields", "Model-visible information boundary:")))
        r = {
            "Group ID": g["group_id"], "Report ID": rid, "Case ID": cid,
            "Frozen expert decision": "Error", "Audit evidence class": LABELS[kind(n)],
            "Assistant assessment": NOTES[n][0], "Limits and competing reading": NOTES[n][1],
            "Report line": start, "Exact registered quote": quote,
            "Original report context": context, "Supplied input evidence": input_evidence,
            "Rule basis": "D03; rubric 8-9" if n in SENSITIVE else "Rubric 8-9; actual system/user evidence boundary",
            "Report source": f"docs/formal_study/rating_delivery_v1/rater2/reports/{rid}.txt",
            "Input source": f"docs/formal_study/rating_delivery_v1/rater2/materials/{cid}/model_user_prompt.txt",
            "Score change": "None; assistant audit only",
        }
        for who in ("rater1", "rater2", "rater3"):
            rec = g["individual_records"][who]
            assert rec["Current decision"] == "Error"
            r[f"{who} frozen reason"] = rec["Reason"]
        rows.append(r)

    summary = []
    for rid, text in reports.items():
        gg = [g for g in groups if g["report_id"] == rid]
        supported = [g["group_id"] for g in gg if number(g["group_id"]) not in SENSITIVE]
        sensitive = [g["group_id"] for g in gg if number(g["group_id"]) in SENSITIVE]
        f = next(r for r in frozen["reports"] if r["report_id"] == rid)
        summary.append({"Report ID": rid, "Case ID": f["case_id"], "Frozen any-error": "Yes",
                        "Frozen confirmed groups": len(gg), "Frozen Pending groups": f["pending_issue_count"],
                        "Groups supported without highlighted wording dispute": "; ".join(supported),
                        "Wording-sensitive groups": "; ".join(sensitive),
                        "Interpretation": "At least one other supported issue remains" if supported else "Error-positive status depends on the highlighted wording judgment; not automatically error-free",
                        "Official outcome changed": "No"})
    counts = Counter(kind(number(g["group_id"])) for g in groups)
    dependent = [r for r in summary if not r["Groups supported without highlighted wording dispute"]]
    assert len(dependent) == 4
    OUT.mkdir(parents=True, exist_ok=True)
    probe_path = OUT / "THRESHOLD_DISPLAY_COUNTEREXAMPLE.json"
    probe_path.write_text(json.dumps({
        "purpose": "Synthetic logical counterexample; not participant data or a discovered patient gap",
        "implementation": "src/features/emg_signal.py:analyze_activation",
        "implementation_sha256": sha((ROOT / "src/features/emg_signal.py").read_bytes()),
        "threshold_fraction": 0.2, "minimum_run_percent": 3.0,
        "scenarios": probe,
        "explanation": "Two below-threshold samples at indices 1 and 999 leave a retained run from 0.2% to 99.8%, displayed 0%-100%. The two above-threshold boundary samples form a short circular run discarded by the ABOVE-threshold duration filter. Coverage 99.8001998% rounds to 100%; both endpoints remain above threshold. No below-threshold gap filling is performed."
    }, indent=2) + "\n")
    wb = Workbook()
    ws = wb.active
    ws.title = "Read first"
    intro = [
        ("Scope", "52 frozen confirmed issue groups in 39 error-positive reports; 26 distinct case inputs."),
        ("Audit operator", "Assistant source audit after model comparison/unblinding; separate from the human expert ratings."),
        ("What was checked", "Original quotation and surrounding context, relevant full sections, model-visible inputs, delivered rubric and D03. Selected complete reports reread for disputed scope."),
        ("Source identity", "Original package report bytes match frozen hashes; prompts match delivery hashes. No translated reconstruction or regenerated report used."),
        ("Meaning of confirmed", "Final recorded expert Error under study rules, not guaranteed clinical falsehood, severity or a wholly unusable report."),
        ("Evidence classes", "; ".join(f"{LABELS[k]}: {counts[k]}" for k in ("D", "F", "I", "W"))),
        ("Wording-sensitive", "Eight groups have defensible competing readings. This is not eight proven rater mistakes or eight proposed Acceptable decisions."),
        ("Report-level dependency", "Four reports have only a highlighted wording-sensitive confirmed group. A change would require explicit expert disposition; existing Pending issues do not disappear."),
        ("Unchanged", "Original ratings, frozen outcomes, model comparisons, category choices, control flags and all 16 closed Pending groups."),
        ("Limitations", "No raw-waveform recomputation, clinical examination, severity grading or complete search for missed issues in all 105 reports."),
        ("Algorithm counterexample", "A synthetic 1001-sample curve with two below-threshold samples still displays 100% coverage, a single 0%-100% retained interval and boundary continuity. See THRESHOLD_DISPLAY_COUNTEREXAMPLE.json. This is not a claim about any participant."),
        ("Next use", "Use balanced evidence to explain the endpoint. If revisiting a boundary, preserve each expert's view and record any change transparently as post-unblinding; do not force consensus or silently replace primary results."),
    ]
    for row in intro:
        ws.append(row)
    for name, data in (("Claim audit", rows), ("Report implications", summary), ("Source verification", sources)):
        sh = wb.create_sheet(name)
        sh.append(list(data[0]))
        for r in data:
            sh.append([r[k] for k in data[0]])
        sh.freeze_panes = "A2"
        sh.auto_filter.ref = sh.dimensions
    for sh in wb:
        for cell in sh[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="24435A")
        for col in range(1, sh.max_column+1):
            sh.column_dimensions[get_column_letter(col)].width = 24 if col < 6 else 65
        for row in sh:
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if isinstance(cell.value, str):
                    cell.data_type = "s"
        for row in range(2, sh.max_row+1):
            sh.row_dimensions[row].height = 95 if sh.title == "Claim audit" else 48
    ws.column_dimensions["B"].width = 110
    xp = OUT / "Confirmed_error_source_audit.xlsx"
    wb.save(xp)
    check = load_workbook(xp)
    assert check["Claim audit"].max_row == 53
    assert check["Report implications"].max_row == 40
    for sh in check:
        for row in sh:
            for cell in row:
                assert cell.data_type not in ("f", "e")
                if isinstance(cell.value, str):
                    assert not any("\u4e00" <= ch <= "\u9fff" for ch in cell.value)

    text = """# Source audit of confirmed-error reports

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

"""
    for r in rows:
        if number(r["Group ID"]) in SENSITIVE:
            text += f"- **{r['Group ID']} / {r['Report ID']} / {r['Case ID']} / line {r['Report line']}**: {r['Assistant assessment']} {r['Limits and competing reading']}\n\n"
    text += "## Report-level implications\n\nFour reports have no other frozen confirmed issue outside the highlighted wording-sensitive set:\n\n"
    for r in dependent:
        text += f"- {r['Report ID']} ({r['Case ID']}): {r['Wording-sensitive groups']}; existing frozen Pending groups: {r['Frozen Pending groups']}.\n"
    text += """
The other 35 error-positive reports retain at least one supported issue outside this highlighted set. This is a dependency check, not a revised error count. Even those supported issues may be minor source-fidelity or precision violations rather than clinical mistakes. If a sensitive claim were later changed, reports with existing Pending claims would not automatically become error-free.

The control Sub06 pathology flag depends on the constrained-ROM reading (AG023). The report also has a separate source-fidelity error (AG049), so its any-error status and its pathology flag are different questions. This audit changes neither.

## Scope and next use

Read the result as an **expert-confirmed task-error endpoint**, and present representative error types alongside rates. Do not call these clinical misdiagnosis rates or imply that all three original independent raters initially reached the same result. Do not discard weak-looking issues selectively after knowing model identities.

No full rereview is mandated by this audit. If the study lead decides the highlighted wording boundaries require expert reconsideration, send both readings without a requested outcome, preserve each individual response, and record any resulting revision as post-unblinding. The frozen primary analysis stays versioned; a later sensitivity analysis is not a silent replacement.

This review inspected all registered confirmed anchors and their relevant original context and inputs, with complete-report rereading for selected scope disputes. It did not recompute raw curves, independently diagnose participants, grade clinical harm, or perform an exhaustive new search for missed issues in all 105 reports. The 16 closed Pending groups remain unchanged.

Files: [claim-by-claim workbook](Confirmed_error_source_audit.xlsx) and [verification/provenance record](BUILD_RECORD.json).
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")
    assert FREEZE.read_bytes() == frozen_bytes
    record = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "author": "Assistant; post-unblinding source audit, not human expert adjudication",
        "frozen_dataset_sha256": sha(frozen_bytes),
        "package_sha256": sha(package_bytes),
        "delivery_integrity_snapshot_sha256": sha(integrity_bytes),
        "script_sha256": sha(Path(__file__).read_bytes()),
        "all_report_hashes_verified": True, "all_input_hashes_verified": True,
        "confirmed_groups": 52, "reports": 39, "cases": 26,
        "evidence_class_counts": {LABELS[k]: v for k, v in counts.items()},
        "wording_sensitive_groups": [r["Group ID"] for r in rows if number(r["Group ID"]) in SENSITIVE],
        "reports_dependent_on_wording_sensitive_groups": [r["Report ID"] for r in dependent],
        "source_workbooks_modified": False, "frozen_dataset_modified": False,
        "model_comparison_modified": False, "new_human_decisions": 0,
        "raw_signals_recomputed": False, "new_model_calls": 0,
        "synthetic_algorithm_scenarios": 4,
        "algorithm_sha256": sha((ROOT / "src/features/emg_signal.py").read_bytes()),
        "sources": sources,
        "outputs_sha256": {p.name: sha(p.read_bytes()) for p in (xp, OUT / "README.md", probe_path)},
    }
    (OUT / "BUILD_RECORD.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "groups": 52, "reports": 39, "classes": dict(counts), "wording_dependent_reports": len(dependent)}))


if __name__ == "__main__":
    main()
