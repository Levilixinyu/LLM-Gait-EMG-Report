#!/usr/bin/env python3
"""One registered OpenAI follow-up after the user reported restored credits.

The original terminal slot remains immutable. This amendment consumes one of
the original OpenAI attempt allowances; it never regenerates Claude or Gemini.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.compatibility_check import (
    LIVE_ROOT, PACKAGE, _process_events, attempt_resolution, load_keys, sha,
    validate_authorization, validate_plan,
)
from src.llm.formal_generation import IntegrityError, append, batch_lock, digest, read_journal, write_once

OUT = ROOT / "data/compatibility_checks/openai_credit_followup_v1"
AMENDMENT = PACKAGE / "OPENAI_CREDIT_FOLLOWUP_AUTHORIZATION.json"


def inspect():
    plan = json.loads((PACKAGE / "plan.json").read_text())
    validate_plan(plan)
    validate_authorization(plan, json.loads((PACKAGE / "authorization.json").read_text()))
    amendment = json.loads(AMENDMENT.read_text())
    task = next(t for t in plan["tasks"] if t["provider"] == "openai")
    prior, head = read_journal(LIVE_ROOT)
    if (amendment.get("approved") is not True or amendment.get("parent_plan_sha256") != digest(plan) or
        amendment.get("parent_journal_head") != head or amendment.get("task_sha256") != digest(task) or
        amendment.get("runner_sha256") != sha(__file__) or amendment.get("max_additional_requests") != 1 or
        not amendment.get("confirmation_source")):
        raise IntegrityError("Missing, changed or unapproved follow-up amendment")
    decisions = [r for r in prior if r.get("slot_id") == task["slot_id"] and r["kind"] in {"attempt_resolved", "recovery"}]
    failures = [r for r in prior if r.get("slot_id") == task["slot_id"] and r["kind"] == "stream_event"
                and r["event"].get("code") == "permanent_quota"]
    if not decisions or decisions[-1]["state"] != "closed_no_report" or not failures:
        raise IntegrityError("Parent is not the documented closed OpenAI credit failure")
    starts = [r for r in prior if r["kind"] == "attempt_started"]
    own = [r for r in starts if r["provider"] == "openai"]
    reserve = sum(plan["reservation_usd_per_attempt"][r["provider"]] for r in starts)
    if len(own) + 1 > 3 or len(starts) + 1 > 9 or reserve + plan["reservation_usd_per_attempt"]["openai"] > 3:
        raise IntegrityError("Original lifetime attempt or budget allowance would be exceeded")
    return plan, task, amendment, len(own) + 1, len(starts) + 1


def capture_once(root, task, *, api_key, fixture=None, deadline=600, attempt_number=2):
    """Persistent one-attempt operation; existing evidence prevents re-dispatch."""
    existing, _ = read_journal(root)
    resolved = [r for r in existing if r["kind"] == "attempt_resolved"]
    if resolved:
        return resolved[-1]
    if existing:
        events = [r["event"] for r in existing if r["kind"] == "stream_event"]
        result = attempt_resolution(events, attempt_number, time.time())
        if result["state"] not in {"captured", "empty"}:
            result.update(state="paused", reason="Interrupted follow-up requires technical review; no automatic redispatch")
    else:
        append(root, {"kind": "attempt_started", "slot_id": task["slot_id"], "provider": "openai",
                      "attempt": attempt_number, "time": time.time(), "task_sha256": digest(task),
                      "basis": "Registered follow-up after user-reported restored credits"})
        events = []
        def persist(event):
            append(root, {"kind": "stream_event", "slot_id": task["slot_id"], "attempt": attempt_number,
                          "event": event, "time": time.time()})
            events.append(event)
        _process_events(task, api_key, fixture, deadline, persist)
        result = attempt_resolution(events, attempt_number, time.time())
        if result["state"] == "retry_wait":
            result.update(state="paused", reason="This amendment permits only one additional request")
    record = {"kind": "attempt_resolved", "slot_id": task["slot_id"], "attempt": attempt_number, **result}
    append(root, record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    with batch_lock(LIVE_ROOT):
        plan, task, amendment, number, total = inspect()
        if not args.live:
            print(json.dumps({"status": "followup_valid", "additional_requests": 1,
                              "openai_lifetime_attempt": number, "combined_maximum_requests_after_followup": total}))
            return
        with batch_lock(OUT):
            envelope = {"parent_plan_sha256": digest(plan), "amendment": amendment, "task": task}
            path = OUT / "run_manifest.json"
            if path.exists():
                if json.loads(path.read_text()) != envelope:
                    raise IntegrityError("Follow-up manifest changed")
            elif read_journal(OUT)[0]:
                raise IntegrityError("Follow-up journal has no manifest")
            else:
                write_once(path, envelope)
            result = capture_once(OUT, task, api_key=load_keys()["openai"], attempt_number=number)
            rows, head = read_journal(OUT)
            events = [r["event"] for r in rows if r["kind"] == "stream_event"]
            metadata = next((e["metadata"] for e in reversed(events) if e.get("metadata")), {})
            summary = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "state": result["state"],
                       "journal_head": head, "parent_journal_head": amendment["parent_journal_head"],
                       "followup_dispatches": sum(e["type"] == "dispatch_requested" for e in events),
                       "openai_lifetime_attempts_reserved": number, "combined_attempts_reserved": total,
                       "visible_text_characters": len(result.get("text", "")), "metadata": metadata,
                       "normal_stream_completion": any(e["type"] == "completed" for e in events),
                       "formal_generation_authorized": False}
            (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary))


if __name__ == "__main__":
    main()
