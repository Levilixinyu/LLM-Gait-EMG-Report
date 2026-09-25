#!/usr/bin/env python3
"""Verify approved inputs and produce a non-executable 105-slot inventory.

Offline only: no credentials, provider clients, model calls, report generation,
archive discovery or private model mappings. Existing reviewed files are read
only. Generated planning files in generation_preflight_v1 may be refreshed.
"""
from __future__ import annotations

import csv
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.formal_generation import digest

BASE = ROOT / "docs/formal_study"
OUT = BASE / "generation_preflight_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def main():
    plan = read(BASE / "execution_analysis_v3_draft/plan.json")
    config = read(OUT / "provider_candidates.json")
    require(plan["study_lead_policy_approved"], "Study-lead policy not approved")
    require(plan["clinical_operational_items_approved"], "Expert content not approved")
    require(not config["configuration_approved"], "This script only prepares an unfrozen candidate")
    verified = {}
    # Check current administrative outputs and finalized requirements against
    # their own manifests. Do not reinterpret historical pending labels.
    for folder in ["execution_analysis_v3_draft", "case_requirements_v1"]:
        file = BASE / folder / "manifest.json"
        for relative, expected in read(file)["output_sha256"].items():
            path = file.parent / relative
            actual = sha(path)
            require(actual == expected, f"Evidence hash mismatch: {path.relative_to(ROOT)}")
            verified[str(path.relative_to(ROOT))] = actual
    registry = BASE / "control_supplement_v2/selected_study_cases.csv"
    selected = list(csv.DictReader(registry.open()))
    case_manifest_path = BASE / "case_review_v1/manifest.json"
    case_manifest = read(case_manifest_path)
    require(sha(registry) == case_manifest["selection_source_sha256"], "Selection changed")
    cases = {row["case_id"]: row for row in case_manifest["cases"]}
    keys = [f"{r['participant_key']}_{r['side']}" for r in selected]
    require(len(keys) == len(set(keys)) == 35, "Expected 35 unique participants")
    require(set(keys) == set(cases), "Selection and reviewed case roster differ")
    require(sum(r["group"] == "stroke" for r in selected) == 25, "Expected 25 stroke cases")
    require(sum(r["group"] == "control" for r in selected) == 10, "Expected 10 controls")
    requirements = list(csv.DictReader((BASE / "case_requirements_v1/case_requirements.csv").open()))
    included = [r for r in requirements if r["included"].lower() in {"true", "yes", "1"}]
    require(len(included) == 149, "Expected 149 included requirements")
    require(set(r["case_id"] for r in included) == set(keys), "Requirement roster differs")
    require(len(config["providers"]) == 3, "Expected three providers")
    require({(p["provider"], p["model"]) for p in config["providers"]} ==
            {(p["provider"], p["model"]) for p in plan["generation"]["candidate_models"]}, "Model roster changed")
    sources = [registry, case_manifest_path, BASE / "candidate_v3_1/APPROVAL_RECORD.json",
               BASE / "rubric_v2_draft/APPROVAL_RECORD.json", BASE / "execution_analysis_v1_draft/exposure_confirmation.json",
               BASE / "execution_analysis_v3_draft/plan.json", BASE / "case_requirements_v1/case_requirements.csv",
               BASE / "case_requirements_v1/shared_rules.csv", OUT / "provider_candidates.json",
               ROOT / "src/llm/formal_generation.py", ROOT / "src/llm/formal_providers.py", Path(__file__),
               ROOT / "tests/test_formal_generation.py", ROOT / "tests/test_formal_providers.py"]
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    slots = []
    for row in selected:
        key = f"{row['participant_key']}_{row['side']}"
        case = cases[key]
        input_hashes = {}
        for filename in ["model_system_prompt.txt", "model_user_prompt.txt"]:
            path = BASE / "case_review_v1" / key / filename
            actual = sha(path)
            require(actual == case["files_sha256"][filename], f"Reviewed input changed: {key}/{filename}")
            require(path.read_text().strip(), f"Empty model input: {key}/{filename}")
            input_hashes[str(path.relative_to(ROOT))] = actual
        for provider in config["providers"]:
            slot = {"slot_id": f"{key}_{provider['provider']}", "case_id": key,
                    "group": row["group"], "provider": provider["provider"], "model": provider["model"],
                    "proposed_parameters": provider["parameters"], "api_route": provider["api_route"],
                    "input_sha256": input_hashes, "reference_meta": case["reference_meta"],
                    "effective_reference_n": case["effective_reference_n"],
                    "source_hashes": source_hashes}
            slot["planning_sha256"] = digest(slot)
            slots.append(slot)
    require(len(slots) == len({s["slot_id"] for s in slots}) == 105, "Expected 105 unique slots")
    inventory = {"status": "Planning inventory only; not the frozen execution manifest",
                 "network_allowed": False, "formal_generation_authorized": False,
                 "source_sha256": source_hashes, "slots": slots}
    write("task_inventory_DRAFT.json", inventory)
    validation = {"status": "Offline input and planning checks passed; live readiness pending",
                  "participants": 35, "stroke": 25, "controls": 10, "report_slots": 105,
                  "verified_exact_prompt_files": 70, "included_case_requirements": 149,
                  "case_coverage_rows_per_rater": 447, "G03_rows_per_rater": 105,
                  "total_coverage_rows_per_rater": 552, "model_calls": 0,
                  "configuration_frozen": False, "generation_authorized": False,
                  "sdk_versions": {p["sdk_package"]: version(p["sdk_package"]) for p in config["providers"]},
                  "http_library_versions": {name: version(name) for name in ["httpx", "httpx2"]},
                  "verified_evidence_sha256": verified,
                  "inventory_sha256": sha(OUT / "task_inventory_DRAFT.json"),
                  "source_sha256": source_hashes}
    write("offline_validation.json", validation)
    print(json.dumps({k: validation[k] for k in ["status", "participants", "report_slots", "verified_exact_prompt_files", "model_calls"]}))


if __name__ == "__main__":
    main()
