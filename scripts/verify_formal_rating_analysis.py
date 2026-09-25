#!/usr/bin/env python3
"""Offline 105-slot rehearsal; all responses and ratings are synthetic fixtures.

Read reviewed input hashes and approved requirement membership. Never read model
outputs, old private keys, archives, API keys, or external services. Temporary
synthetic packets are removed after the checks; retain only the audit summary.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.formal_analysis import analyze, assessments_from_review, independent_agreement
from src.eval.formal_rating import build_package, lock_independent_review, require_both_independent_locks
from src.llm.formal_generation import canonical

BASE = ROOT / "docs/formal_study"
OUT = BASE / "workflow_readiness_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources():
    verified = {}
    for name in ("case_requirements_v1", "execution_analysis_v3_draft"):
        manifest = json.loads((BASE / name / "manifest.json").read_text())
        for filename, expected in manifest["output_sha256"].items():
            path = BASE / name / filename
            if sha(path) != expected:
                raise ValueError(f"Reviewed evidence changed: {path.relative_to(ROOT)}")
            verified[str(path.relative_to(ROOT))] = expected
    registry = BASE / "control_supplement_v2/selected_study_cases.csv"
    manifest_path = BASE / "case_review_v1/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if sha(registry) != manifest["selection_source_sha256"]:
        raise ValueError("Selected registry changed")
    selected = list(csv.DictReader(registry.open()))
    case_ids = {f"{r['participant_key']}_{r['side']}": r["group"] for r in selected}
    if len(case_ids) != 35 or set(case_ids) != {c["case_id"] for c in manifest["cases"]}:
        raise ValueError("Reviewed roster mismatch")
    input_bytes = []
    for case in manifest["cases"]:
        size = 0
        for filename in ("model_system_prompt.txt", "model_user_prompt.txt"):
            path = BASE / "case_review_v1" / case["case_id"] / filename
            if sha(path) != case["files_sha256"][filename]:
                raise ValueError("Reviewed model input changed")
            size += len(path.read_bytes())
            verified[str(path.relative_to(ROOT))] = sha(path)
        input_bytes.append(size)
    requirements = {case: [] for case in case_ids}
    for row in csv.DictReader((BASE / "case_requirements_v1/case_requirements.csv").open()):
        if row["included"] == "Yes":
            requirements[row["case_id"]].append({"requirement_id": row["record_id"],
                "required_wording": row["required_wording"], "components": row["required_components_and_optional_content"]})
    roster = {case: {"group": group, "required_ids": [r["requirement_id"] for r in requirements[case]]}
              for case, group in case_ids.items()}
    return roster, requirements, verified, {"minimum": min(input_bytes), "maximum": max(input_bytes), "total_one_model": sum(input_bytes)}


def fill_synthetic_return(template, destination, rater):
    """Never use this fixture helper on a real expert workbook."""
    book = load_workbook(template)
    book["Instructions"].cell(15, 2, "SYNTHETIC FIXTURE - NOT AN EXPERT")
    book["Instructions"].cell(16, 2, "2026-09-18")
    book["Instructions"].cell(17, 2, "Yes")
    missing = set()
    for row in book["Review"].iter_rows(min_row=2):
        if row[2].value == "Unavailable":
            missing.add(row[0].value)
            row[3].value, row[4].value, row[7].value = "Unavailable", "No", "SYNTHETIC missing-output fixture."
        else:
            row[3].value, row[4].value, row[5].value, row[6].value = "Completed", "Yes", "No", "No"
    for index, row in enumerate(book["Coverage"].iter_rows(min_row=2)):
        row[5].value = "Cannot assess" if row[0].value in missing else (
            "Partially covered" if rater == "rater2" and index % 7 == 0 else "Covered")
        row[6].value = "Final"
        row[7].value = "SYNTHETIC software fixture only; not an expert assessment."
    book.save(destination)


def main():
    roster, requirements, verified, input_bytes = verify_sources()
    models = ("SYNTHETIC_A", "SYNTHETIC_B", "SYNTHETIC_C")
    missing_case = sorted(c for c in roster if roster[c]["group"] == "stroke")[0]
    slots = []
    for case in sorted(roster):
        for model in models:
            text = None if (case, model) == (missing_case, models[0]) else (
                "SYNTHETIC OFFLINE FIXTURE. This is not a generated clinical report.\n")
            slots.append({"slot_id": f"{case}_{model}", "case_id": case, "model_key": model,
                          "report_text": text, "terminal_status": "captured" if text else "empty",
                          "source_sha256": hashlib.sha256(canonical([case, model, text])).hexdigest()})
    case_assets = {case: {"model_system_prompt.txt": b"SYNTHETIC REHEARSAL ONLY",
                         "model_user_prompt.txt": b"SYNTHETIC REHEARSAL ONLY"} for case in roster}
    with tempfile.TemporaryDirectory(prefix="gait-formal-workflow-") as temporary:
        root = Path(temporary)
        package = root / "synthetic_packet"
        counts = build_package(package, slots, requirements, case_assets, {"RUBRIC.md": b"SYNTHETIC TEST ONLY"})
        if counts != {"report_slots": 105, "available_reports": 104, "coverage_rows_per_rater": 552}:
            raise AssertionError("Incorrect workload")
        for rater in ("rater1", "rater2"):
            returned = root / f"{rater}_SYNTHETIC.xlsx"
            fill_synthetic_return(package / "raters" / rater / "Independent_ratings.xlsx", returned, rater)
            lock_independent_review(package, rater, returned)
        locked = require_both_independent_locks(package)
        # This mapping belongs solely to the temporary SYNTHETIC fixture above.
        mapping = json.loads((package / "private/answer_key_DO_NOT_SHARE.json").read_text())["mapping"]
        rows = {r: assessments_from_review(locked[r], mapping, roster) for r in locked}
        results, indices = analyze(roster, models, rows["rater1"])
        agreement = independent_agreement(roster, models, rows["rater1"], rows["rater2"])
        if results["primary_stroke"]["n"] != 24:
            raise AssertionError("One missing output did not exclude its complete triad")
        if any(x != 1 for x in results["primary_stroke"]["paired_model_means"].values()):
            raise AssertionError("Unexpected synthetic coverage result")
        if agreement["stroke"]["case_requirements"]["jointly_assessable"] != 119 * 3 - len(roster[missing_case]["required_ids"]):
            raise AssertionError("Wrong independent agreement denominator")
        second, repeated = analyze(dict(reversed(list(roster.items()))), models[::-1], rows["rater1"][::-1])
        if canonical(results) != canonical(second) or not np.array_equal(indices, repeated):
            raise AssertionError("Analysis depends on input order")
        np.save(root / "resample_indices.npy", indices, allow_pickle=False)
        matrix_hash = sha(root / "resample_indices.npy")
        public_metadata_safe = all(
            "SYNTHETIC_A" not in (package / "raters" / r / "reports.json").read_text()
            for r in locked)
        if not public_metadata_safe:
            raise AssertionError("Model metadata leaked")
    sources = ["src/eval/formal_analysis.py", "src/eval/formal_rating.py", "scripts/verify_formal_rating_analysis.py",
               "tests/test_formal_analysis.py", "tests/test_formal_rating.py",
               "docs/formal_study/execution_analysis_v3_draft/PROTOCOL.md",
               "docs/formal_study/rubric_v2_draft/APPROVAL_RECORD.json",
               "docs/formal_study/case_requirements_v1/case_requirements.csv"]
    record = {"status": "Offline synthetic workflow checks passed; not a formal batch release",
              "checked_utc": datetime.now(timezone.utc).isoformat(), "model_calls": 0, "human_ratings_created": 0,
              "formal_reports_created": 0, "historical_reports_or_private_mappings_read": 0,
              "reviewed_prompt_files_verified": 70, "planned_cases": 35, "planned_report_slots": 105,
              "coverage_rows_per_rater": 552, "synthetic_available_reports": 104,
              "synthetic_complete_stroke_triads": 24, "analysis_seed": 20260918,
              "bootstrap_resamples": 20000, "synthetic_resample_matrix_sha256": matrix_hash,
              "verified_checks": ["Unchanged approved membership and exact input hashes",
                "105-slot packing includes one explicit no-report fixture",
                "Two independent spaced orders and 552-row dropdown workbooks",
                "Verbatim report text; private metadata excluded from rater manifest",
                "Both independent return snapshots validated before comparison",
                "Workbook-to-analysis conversion preserves human-label schema",
                "One missing output excludes its entire stroke triad",
                "Independent agreement excludes unassessable rows",
                "20,000 shared paired resamples and deterministic case-order invariance"],
              "model_input_utf8_bytes": input_bytes,
              "source_sha256": {p: sha(ROOT / p) for p in sources}, "verified_evidence_sha256": verified,
              "remaining_release_gates": ["Final output allowance and effective provider configuration",
                "Formally authorized frozen 105-slot runner, schedule and cost limits",
                "Terminal generation-ledger importer and full real-asset packet validation",
                "Final human-consensus importer with adjudication provenance",
                "Separate concrete formal-generation authorization"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "offline_rehearsal.json").write_text(json.dumps(record, indent=2, ensure_ascii=True) + "\n")
    print(json.dumps({k: record[k] for k in ("status", "model_calls", "planned_report_slots", "coverage_rows_per_rater", "synthetic_complete_stroke_triads")}))


if __name__ == "__main__":
    main()
