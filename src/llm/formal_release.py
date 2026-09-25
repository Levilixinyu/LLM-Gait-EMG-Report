"""Construct and verify the formal candidate and explicit reviewer asset set."""
from __future__ import annotations

import csv
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

from .compatibility_check import PACKAGES
from .formal_generation import IntegrityError, digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/formal_study"
PACKAGE = BASE / "formal_execution_v2_candidate"
ASSET_NAMES = ("model_system_prompt.txt", "model_user_prompt.txt", "reference_card.md",
               "curves_emg.png", "curves_kinematics.png")
CODE_FILES = ("src/llm/formal_batch.py", "src/llm/formal_release.py", "src/llm/formal_generation.py",
              "src/llm/formal_providers.py", "src/llm/compatibility_check.py",
              "src/eval/formal_rating.py", "src/eval/formal_analysis.py", "src/eval/formal_consensus.py",
              "src/llm/full_length_check.py", "scripts/run_full_length_check.py", "scripts/run_formal_batch.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def reviewed_materials():
    """Read only named current evidence; no historical output or mapping scans."""
    manifest = read(BASE / "case_review_v1/manifest.json")
    registry = BASE / "control_supplement_v2/selected_study_cases.csv"
    if sha(registry) != manifest["selection_source_sha256"]:
        raise IntegrityError("Selected roster changed")
    selected = list(csv.DictReader(registry.open()))
    roster = {f"{r['participant_key']}_{r['side']}": r["group"] for r in selected}
    if len(roster) != 35 or list(roster.values()).count("stroke") != 25 or list(roster.values()).count("control") != 10:
        raise IntegrityError("Expected 25 stroke and 10 control cases")
    if set(roster) != {c["case_id"] for c in manifest["cases"]}:
        raise IntegrityError("Reviewed case membership changed")
    source_hashes = {str(registry.relative_to(ROOT)): sha(registry)}
    for folder in ("case_requirements_v1", "execution_analysis_v3_draft"):
        directory = BASE / folder
        for filename, expected in read(directory / "manifest.json")["output_sha256"].items():
            path = directory / filename
            if sha(path) != expected:
                raise IntegrityError(f"Reviewed evidence changed: {path.relative_to(ROOT)}")
            source_hashes[str(path.relative_to(ROOT))] = expected
    policy = read(BASE / "execution_analysis_v3_draft/plan.json")
    if policy["study_lead_policy_approved"] is not True or policy["clinical_operational_items_approved"] is not True:
        raise IntegrityError("Study policy approval missing")
    requirements = {case: [] for case in roster}
    for row in csv.DictReader((BASE / "case_requirements_v1/case_requirements.csv").open()):
        if row["included"] == "Yes":
            requirements[row["case_id"]].append({"requirement_id": row["record_id"],
                "required_wording": row["required_wording"], "components": row["required_components_and_optional_content"]})
    if sum(map(len, requirements.values())) != 149:
        raise IntegrityError("Final requirement count changed")
    assets, cases = {}, {}
    for case in manifest["cases"]:
        cid = case["case_id"]
        cases[cid] = case
        assets[cid] = {}
        for filename in ASSET_NAMES:
            path = BASE / "case_review_v1" / cid / filename
            content = path.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            if actual != case["files_sha256"][filename]:
                raise IntegrityError(f"Review asset changed: {cid}/{filename}")
            assets[cid][filename] = content
            source_hashes[str(path.relative_to(ROOT))] = actual
    rubric = BASE / "rubric_v2_draft"
    approval = read(rubric / "APPROVAL_RECORD.json")
    common = {}
    for filename in ("RUBRIC.md", "EXAMPLES.md", "rubric.json"):
        content = (rubric / filename).read_bytes()
        expected = approval["approved_output_sha256"][filename]
        if hashlib.sha256(content).hexdigest() != expected:
            raise IntegrityError("Approved rubric bytes changed")
        common[filename] = content
        source_hashes[str((rubric / filename).relative_to(ROOT))] = expected
    common["RUBRIC_APPROVAL_STATUS.md"] = (rubric / "APPROVAL_STATUS.md").read_bytes()
    common["shared_rules.csv"] = (BASE / "case_requirements_v1/shared_rules.csv").read_bytes()
    common["CURRENT_REVIEW_SCOPE.md"] = (
        "# Current formal review scope\n\nThe approved rubric v2 is retained verbatim, including its historical draft wording. "
        "RUBRIC_APPROVAL_STATUS.md records the subsequent approval. Its five-case annex is developmental; "
        "the Coverage sheet contains the final requirements for these 35 cases. G03 applies once to each report. "
        "Curves and reference cards help verify evidence, but cannot create mandatory model content that was not supplied. "
        "The two control flags annotate existing confirmed or pending in-scope issue groups; they are not new error categories. "
        "Preserve original independent judgments before discussion. Report files are verbatim.\n"
    ).encode()
    for relative in ("case_review_v1/manifest.json", "rubric_v2_draft/APPROVAL_RECORD.json",
                     "rubric_v2_draft/APPROVAL_STATUS.md", "candidate_v3_1/APPROVAL_RECORD.json",
                     "execution_analysis_v1_draft/exposure_confirmation.json",
                     "generation_preflight_v1/provider_candidates.json"):
        source_hashes[str((BASE / relative).relative_to(ROOT))] = sha(BASE / relative)
    return roster, requirements, assets, common, cases, source_hashes


def build_candidate():
    from .formal_batch import schedule
    roster, requirements, assets, common, cases, source_hashes = reviewed_materials()
    for name in CODE_FILES:
        source_hashes[name] = sha(ROOT / name)
    for name in ("provider_configuration.json", "CAP_CHANGE_RECORD.json"):
        path = PACKAGE / name
        source_hashes[str(path.relative_to(ROOT))] = sha(path)
    proposals = read(PACKAGE / "provider_configuration.json")["providers"]
    providers = {p["provider"]: p for p in proposals}
    tasks = []
    for case, provider in schedule(roster):
        parameters = providers[provider]["parameters"]
        system = assets[case]["model_system_prompt.txt"].decode("utf-8")
        user = assets[case]["model_user_prompt.txt"].decode("utf-8")
        tasks.append({"slot_id": f"{case}_{provider}", "case_id": case, "group": roster[case],
                      "provider": provider, "model": providers[provider]["model"], "parameters": parameters,
                      "system_prompt": system, "user_prompt": user, "input_pair_sha256": digest([system, user]),
                      "reference_meta": cases[case]["reference_meta"],
                      "effective_reference_n": cases[case]["effective_reference_n"]})
    # Registered rate assumptions are copied from the completed check, not a new
    # price lookup or a provider invoice. Input reservation is an engineering
    # assumption, not a certified tokenizer upper bound or hard billing ceiling.
    original = read(BASE / "compatibility_check_v1/plan.json")
    rates = original["standard_prices_usd_per_million"]
    input_rates = {"anthropic": 5, "openai": 12.5, "gemini": 2}
    cap_keys = {"anthropic": "max_tokens", "openai": "max_completion_tokens", "gemini": "max_output_tokens"}
    reservations = {p: (16000 * input_rates[p] + providers[p]["parameters"][cap_keys[p]] * rates[p]["output"]) / 1e6 for p in providers}
    return {
        "version": "formal-execution-v2-candidate", "scope": "Formal 25 stroke plus 10 control reports",
        "configuration_status": "Candidate; 16000-token output allowance approved, formal generation not authorized; Claude refusal unresolved",
        "tasks": tasks, "schedule_seed": 20260919, "source_sha256": source_hashes,
        "sdk_versions": {p: version(p) for p in PACKAGES},
        "max_attempts_per_slot": 3, "max_total_attempts": 315, "attempt_deadline_seconds": 600,
        "budget_limit_usd": 120.0, "reservation_usd_per_attempt": reservations,
        "input_token_reservation_per_attempt": 16000,
        "one_attempt_all_slots_reservation_usd": round(35 * sum(reservations.values()), 6),
        "three_attempt_all_slots_reservation_usd": round(105 * sum(reservations.values()), 6),
        "cost_scope": "Registered 2026-09-18 rates and assumed input allowance; not an invoice or hard provider billing limit",
        "price_source_plan_sha256": sha(BASE / "compatibility_check_v1/plan.json"),
        "review_assets_per_case": list(ASSET_NAMES), "common_asset_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in common.items()},
        "case_requirements_sha256": digest(requirements),
        "live_output_directory": str(Path("data/reports_formal_v1")),
        "omitted_parameters": "Sampling settings omitted by the current adapter remain provider-managed; their final documentation is a release gate",
    }


def package_terminal_run(run_root, plan, output, *, allow_mock=False):
    from .formal_batch import terminal_slots
    from src.eval.formal_rating import build_package
    roster, requirements, assets, common, _, _ = reviewed_materials()
    if digest(requirements) != plan["case_requirements_sha256"]:
        raise IntegrityError("Frozen requirement identity changed")
    if {n: hashlib.sha256(b).hexdigest() for n, b in common.items()} != plan["common_asset_sha256"]:
        raise IntegrityError("Common review assets changed")
    slots = terminal_slots(run_root, plan, allow_mock=allow_mock)
    if {s["case_id"] for s in slots} != set(roster):
        raise IntegrityError("Terminal output roster differs from reviewed materials")
    return build_package(output, slots, requirements, assets, common)
