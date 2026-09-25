#!/usr/bin/env python3
"""One authorized Claude clinical-content probe using approved pilot-case input."""
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.compatibility_check import HTTPFixture, _process_events, attempt_resolution, load_keys
from src.llm.formal_batch import Ledger
from src.llm.formal_generation import IntegrityError, batch_lock, digest, write_once
from importlib.metadata import version
from src.llm.compatibility_check import PACKAGES

PACKAGE = ROOT / "docs/formal_study/claude_clinical_probe_v1"
LIVE_ROOT = ROOT / "data/compatibility_checks/claude_clinical_probe_v1"
APPROVAL = ROOT / "docs/formal_study/candidate_v3_1/APPROVAL_RECORD.json"
INPUT = ROOT / "docs/expert_trial/data_cards_v7_candidate/stroke_Sub09_P"


def build_plan():
    approval = json.loads(APPROVAL.read_text())
    if approval["status"] != "approved_as_written_by_both_reviewers_for_interpretation_instructions_only":
        raise IntegrityError("Clinical interpretation approval is missing")
    case_id = "stroke_Sub09_P"
    approved = next(r for r in approval["approved_inputs"] if r["case_id"] == case_id)
    content = {}
    for label in ("system", "user"):
        raw = (INPUT / f"model_{label}_prompt.txt").read_bytes()
        if hashlib.sha256(raw).hexdigest() != approved[f"{label}_sha256"]:
            raise IntegrityError("Expert-approved input bytes changed")
        content[label] = raw.decode("utf-8")
    registry = ROOT / "docs/formal_study/control_supplement_v2/selected_study_cases.csv"
    with registry.open() as handle:
        if case_id in {f"{r['participant_key']}_{r['side']}" for r in csv.DictReader(handle)}:
            raise IntegrityError("Probe case must remain outside the formal sample")
    configuration = ROOT / "docs/formal_study/formal_execution_v2_candidate/provider_configuration.json"
    provider = next(p for p in json.loads(configuration.read_text())["providers"] if p["provider"] == "anthropic")
    if provider["model"] != "claude-opus-5" or provider["parameters"] != {"max_tokens": 16000, "thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}}:
        raise IntegrityError("Expected approved Claude 16K/high configuration")
    task = {"slot_id": f"{case_id}_anthropic_clinical_probe", "case_id": case_id,
            "provider": "anthropic", "model": provider["model"], "parameters": provider["parameters"],
            "system_prompt": content["system"], "user_prompt": content["user"],
            "input_pair_sha256": digest([content["system"], content["user"]])}
    paths = [ROOT / name for name in ("src/llm/compatibility_check.py", "src/llm/formal_generation.py",
             "src/llm/formal_batch.py", "src/llm/formal_providers.py")]
    paths += [APPROVAL, registry, configuration, INPUT / "model_system_prompt.txt", INPUT / "model_user_prompt.txt"]
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    return {"scope": "Claude-only single-attempt approved clinical-content probe",
            "purpose": "Test whether real research content is affected",
            "version": "claude-clinical-probe-v1", "tasks": [task],
            "input_version": "limited-evidence-v3.1-candidate",
            "case_selection": "Previously used five-case pilot participant; not a new formal participant. Latest expert-approved input is used, not the earlier pilot prompt version.",
            "source_sha256": sources, "sdk_versions": {p: version(p) for p in PACKAGES},
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "max_attempts_per_slot": 1, "max_total_attempts": 1, "budget_limit_usd": 0.48,
            "reservation_usd_per_attempt": {"anthropic": 0.48},
            "maximum_reservation_usd": 0.48, "attempt_deadline_seconds": 600,
            "cost_scope": "Reservation at registered rates for 16000 input and 16000 output tokens; not an invoice or guaranteed provider billing ceiling",
            "acceptance": "Record refusal and visible output, finish reason, usage, model and request identifiers. Complete nonempty non-refused output supports technical completion for this input only. No clinical quality or minimum-word acceptance filter.",
            "amendment": "User authorized one real expert-approved prior test case, one Claude request at 16K. Purpose recorded externally without altering approved prompts. No automatic retry or fallback.",
            "include_in_formal_analysis": False, "formal_generation_authorized": False}


def execute(plan, authorization, *, root=LIVE_ROOT, fixtures=None):
    if plan != build_plan():
        raise IntegrityError("Amended plan changed")
    if (authorization.get("approved") is not True or authorization.get("plan_sha256") != digest(plan)
        or authorization.get("max_total_attempts") != 1 or authorization.get("budget_limit_usd") != 0.48
        or authorization.get("scope") != plan["scope"]
        or not all(authorization.get(k) for k in ("confirmation_source", "confirmed_at", "recorded_by"))):
        raise IntegrityError("Exact single-attempt authorization required")
    live = fixtures is None
    root = Path(root).resolve()
    if live != (root == LIVE_ROOT.resolve()):
        raise IntegrityError("Live and mock evidence must use separate directories")
    keys = load_keys() if live else {t["provider"]: "fake-offline-key" for t in plan["tasks"]}
    with batch_lock(root):
        envelope = {"plan": plan, "plan_sha256": digest(plan), "mode": "live" if live else "mock",
                    "authorization": authorization}
        manifest = root / "run_manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text()) != envelope:
                raise IntegrityError("Existing run identity cannot change")
        else:
            if Ledger(root).records:
                raise IntegrityError("Missing run manifest")
            write_once(manifest, envelope)
        ledger = Ledger(root)
        for task in plan["tasks"]:
            slot = task["slot_id"]
            rows = ledger.slot(slot)
            decisions = [r for r in rows if r["kind"] == "attempt_resolved"]
            if decisions:
                continue
            starts = [r for r in rows if r["kind"] == "attempt_started"]
            if starts:
                if len(starts) != 1 or starts[0]["task_sha256"] != digest(task):
                    raise IntegrityError("Attempt identity mismatch")
                events = [r["event"] for r in rows if r["kind"] == "stream_event"]
            else:
                if sum(r["kind"] == "attempt_started" for r in ledger.records) >= 1:
                    raise IntegrityError("One-request limit reached")
                fixture = None if live else fixtures[slot]
                if not live and type(fixture) is not HTTPFixture:
                    raise IntegrityError("Explicit mock transport required")
                ledger.append({"kind": "attempt_started", "slot_id": slot, "attempt": 1,
                               "task_sha256": digest(task), "provider": task["provider"],
                               "time": datetime.now(timezone.utc).isoformat()})
                events = []
                def persist(event):
                    ledger.append({"kind": "stream_event", "slot_id": slot, "attempt": 1, "event": event})
                    events.append(event)
                _process_events(task, keys[task["provider"]], fixture, 600, persist)
            outcome = attempt_resolution(events, 1, 0)
            # All non-content outcomes are final for this one-shot check. No
            # retry, retrieval-driven new request, or cap escalation is scheduled.
            if outcome["state"] not in {"captured", "empty"}:
                outcome.update(state="failed_no_retry", original_state=outcome["state"])
            ledger.append({"kind": "attempt_resolved", "slot_id": slot, "attempt": 1, **outcome})
        rows = []
        for task in plan["tasks"]:
            records = ledger.slot(task["slot_id"])
            outcome = next(r for r in reversed(records) if r["kind"] == "attempt_resolved")
            events = [r["event"] for r in records if r["kind"] == "stream_event"]
            metadata = next((e["metadata"] for e in reversed(events) if e.get("metadata")), {})
            words = len(outcome.get("text", "").split())
            complete = any(e["type"] == "completed" for e in events)
            limit = metadata.get("finish_reason") in {"length", "max_tokens", "MAX_TOKENS"}
            supported = bool(outcome["state"] == "captured" and complete and not limit and metadata.get("finish_reason") != "refusal" and words > 0
                             and metadata.get("usage") and metadata.get("response_model") and metadata.get("finish_reason"))
            rows.append({"provider": task["provider"], "requested_model": task["model"], "state": outcome["state"],
                         "words": words, "normal_completion": complete, "token_limit_reached": limit,
                         "technical_request_completed": supported, "metadata": metadata,
                         "dispatches": sum(e["type"] == "dispatch_requested" for e in events)})
        result = {"scope": plan["scope"], "results": rows, "journal_head": ledger.head,
                  "plan_sha256": digest(plan), "formal_generation_authorized": False,
                  "automatic_retries": 0, "clinical_probe_completed": all(r["technical_request_completed"] for r in rows)}
        if not (root / "results.json").exists():
            write_once(root / "results.json", result)
        elif json.loads((root / "results.json").read_text()) != result:
            raise IntegrityError("Existing result summary differs")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    plan = json.loads((PACKAGE / "plan.json").read_text())
    if not args.live:
        if plan != build_plan():
            raise IntegrityError("Plan changed")
        print(json.dumps({"status": "Single-attempt plan verified", "requests": 1, "automatic_retries": 0}))
        return
    result = execute(plan, json.loads((PACKAGE / "authorization.json").read_text()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
