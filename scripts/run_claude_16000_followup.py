#!/usr/bin/env python3
"""One explicitly authorized Claude-only synthetic follow-up at 16,000 tokens."""
from datetime import datetime, timezone
import argparse
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

PACKAGE = ROOT / "docs/formal_study/claude_16000_followup_v1"
LIVE_ROOT = ROOT / "data/compatibility_checks/claude_16000_followup_v1"
PARENT = ROOT / "docs/formal_study/full_length_once_v1/plan.json"


def build_plan():
    parent = json.loads(PARENT.read_text())
    if digest(parent) != "4f8f6f8078155add396ba480486299e2814cc14de66eb72fb85aa26a4ff1fbf0":
        raise IntegrityError("Historical synthetic plan changed")
    task = next(t for t in parent["tasks"] if t["provider"] == "anthropic")
    task["parameters"]["max_tokens"] = 16000
    if task["parameters"] != {"max_tokens": 16000, "thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}}:
        raise IntegrityError("Unexpected Claude parameters")
    if digest([task["system_prompt"], task["user_prompt"]]) != task["input_pair_sha256"]:
        raise IntegrityError("Historical input mismatch")
    sources = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        "src/llm/compatibility_check.py", "src/llm/formal_generation.py",
        "src/llm/formal_batch.py", "src/llm/formal_providers.py")}
    return {"scope": "Claude-only single-attempt synthetic follow-up at 16000 tokens",
            "version": "claude-16000-followup-v1", "tasks": [task],
            "parent_plan_sha256": digest(json.loads(PARENT.read_text())),
            "source_sha256": sources, "sdk_versions": {p: version(p) for p in PACKAGES},
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "max_attempts_per_slot": 1, "max_total_attempts": 1, "budget_limit_usd": 0.48,
            "reservation_usd_per_attempt": {"anthropic": 0.48},
            "maximum_reservation_usd": 0.48, "attempt_deadline_seconds": 600,
            "cost_scope": "Reservation at registered rates for 16000 input and 16000 output tokens; not an invoice or guaranteed provider billing ceiling",
            "minimum_words_for_length_evidence": 900,
            "amendment": "User explicitly requested one more test and clarified Claude only; original synthetic input, approved 16000 cap, unchanged high effort. No automatic retry or fallback.",
            "formal_generation_authorized": False}


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
            supported = bool(outcome["state"] == "captured" and complete and not limit and metadata.get("finish_reason") != "refusal" and words >= 900
                             and metadata.get("usage") and metadata.get("response_model") and metadata.get("finish_reason"))
            rows.append({"provider": task["provider"], "requested_model": task["model"], "state": outcome["state"],
                         "words": words, "normal_completion": complete, "token_limit_reached": limit,
                         "technical_length_support": supported, "metadata": metadata,
                         "dispatches": sum(e["type"] == "dispatch_requested" for e in events)})
        result = {"scope": plan["scope"], "results": rows, "journal_head": ledger.head,
                  "plan_sha256": digest(plan), "formal_generation_authorized": False,
                  "automatic_retries": 0, "claude_supports_length": all(r["technical_length_support"] for r in rows)}
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
