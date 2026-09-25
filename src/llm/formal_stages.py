"""Bounded formal execution stages over one unchanged study ledger.

The attempt loop preserves the existing formal policy. Stage authorization restricts
which slots can be transmitted and cannot authorize the other stages.
"""
import hashlib
import json
from pathlib import Path
import time

from .formal_batch import (ROOT, LIVE_ROOT, RELEASE_CHECKS, TERMINAL, Ledger,
                           validate_plan, _verify_envelope)
from .compatibility_check import HTTPFixture, _process_events, attempt_resolution, load_keys
from .formal_generation import IntegrityError, batch_lock, digest, write_once

PACKAGE = ROOT / "docs/formal_study/formal_stages_v1"
FULL_PLAN = ROOT / "docs/formal_study/formal_execution_v2_candidate/plan.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stage_layout(plan):
    stroke = list(dict.fromkeys(t["case_id"] for t in plan["tasks"] if t["group"] == "stroke"))
    first, second = set(stroke[:10]), set(stroke[10:20])
    groups = [first, second, {t["case_id"] for t in plan["tasks"]} - first - second]
    return [[t["slot_id"] for t in plan["tasks"] if t["case_id"] in cases] for cases in groups]


def build_stage(plan, number):
    if type(number) is not int or number not in (1, 2, 3):
        raise IntegrityError("Stage number must be 1, 2 or 3")
    layout = stage_layout(plan)
    schedule = json.loads((PACKAGE / "stage_schedule.json").read_text())
    if schedule["full_plan_sha256"] != digest(plan) or schedule["slot_ids_by_stage"] != layout:
        raise IntegrityError("Stage schedule differs from the recorded content-independent partition")
    slots = layout[number - 1]
    tasks = [t for t in plan["tasks"] if t["slot_id"] in slots]
    once = sum(plan["reservation_usd_per_attempt"][t["provider"]] for t in tasks)
    return {"scope": "Formal study stage " + str(number), "stage_number": number,
            "full_plan_sha256": digest(plan), "slot_ids": slots,
            "case_ids": list(dict.fromkeys(t["case_id"] for t in tasks)),
            "required_prior_slots": [s for block in layout[:number - 1] for s in block],
            "max_total_attempts": len(tasks) * 3,
            "budget_limit_usd": round(once * 3, 6), "one_attempt_reservation_usd": round(once, 6),
            "full_study_reservation_limit_usd": plan["budget_limit_usd"],
            "schedule_sha256": sha(PACKAGE / "stage_schedule.json"),
            "runner_sha256": sha(Path(__file__)),
            "cli_sha256": sha(ROOT / "scripts/run_formal_stage.py"),
            "unchanged_full_plan": True}


def validate_stage_authorization(plan, stage, authorization):
    if stage != build_stage(plan, stage.get("stage_number")):
        raise IntegrityError("Stage identity changed")
    if (authorization.get("approved") is not True
        or authorization.get("stage_sha256") != digest(stage)
        or authorization.get("full_plan_sha256") != digest(plan)
        or authorization.get("slot_ids") != stage["slot_ids"]
        or authorization.get("max_total_attempts") != stage["max_total_attempts"]
        or authorization.get("budget_limit_usd") != stage["budget_limit_usd"]
        or authorization.get("full_batch_authorized") is not False
        or not all(authorization.get(k) for k in ("confirmation_source", "confirmed_at", "recorded_by"))):
        raise IntegrityError("Exact bounded stage authorization is required")
    checks = authorization.get("release_checks", {})
    if set(checks) != RELEASE_CHECKS | {"stage_boundary_checks_passed"}:
        raise IntegrityError("Stage release evidence is incomplete")
    for item in checks.values():
        path = (ROOT / item.get("evidence_path", "")).resolve()
        if (item.get("passed") is not True or not path.is_relative_to(ROOT / "docs/formal_study")
            or not path.is_file() or sha(path) != item.get("evidence_sha256")):
            raise IntegrityError("Stage release evidence mismatch")


def run_stage(root, plan, stage, authorization, *, mode="live", fixtures=None,
              sleep=time.sleep, now=time.time, progress=None):
    # Both live and offline runs require bounded authorization before credentials.
    validate_stage_authorization(plan, stage, authorization)
    validate_plan(plan, live=True)
    root = Path(root).resolve()
    if mode == "live":
        if root != LIVE_ROOT.resolve() or fixtures is not None:
            raise IntegrityError("Live stage path and transport are fixed")
        keys = load_keys()
    elif mode == "mock":
        if root == LIVE_ROOT.resolve() or not isinstance(fixtures, dict):
            raise IntegrityError("Mock stage requires separate output and explicit fixtures")
        keys = {p: "fake-offline-key" for p in ("anthropic", "openai", "gemini")}
    else:
        raise IntegrityError("Unknown stage mode")
    deadline = plan["attempt_deadline_seconds"]
    tasks = [t for t in plan["tasks"] if t["slot_id"] in stage["slot_ids"]]
    with batch_lock(root):
        _verify_envelope(root, plan, mode, {"authorization_mode": "separate_per_stage", "schedule_sha256": stage["schedule_sha256"], "full_batch_authorized": False}, deadline)
        evidence = root / f"stage-{stage['stage_number']:02d}-authorization.json"
        envelope = {"stage": stage, "authorization": authorization, "mode": mode}
        if evidence.exists():
            if json.loads(evidence.read_text()) != envelope:
                raise IntegrityError("Stage authorization identity changed")
        else:
            write_once(evidence, envelope)
        ledger = Ledger(root)
        outcomes = {}
        for previous in stage["required_prior_slots"]:
            prior_decisions = [r for r in ledger.slot(previous) if r["kind"] in {"attempt_resolved", "recovery"}]
            if not prior_decisions or prior_decisions[-1]["state"] not in TERMINAL:
                raise IntegrityError("Previous stage is not terminal")
        for task in tasks:
            slot = task["slot_id"]
            while True:
                rows = ledger.slot(slot)
                starts = [r for r in rows if r["kind"] == "attempt_started"]
                decisions = [r for r in rows if r["kind"] in {"attempt_resolved", "recovery"}]
                if [s["attempt"] for s in starts] != list(range(1, len(starts) + 1)) or any(s["task_sha256"] != digest(task) for s in starts):
                    raise IntegrityError("Attempt identity or sequence mismatch")
                if starts and (not decisions or decisions[-1]["attempt"] < starts[-1]["attempt"]):
                    number = starts[-1]["attempt"]
                    events = [r["event"] for r in rows if r["kind"] == "stream_event" and r["attempt"] == number]
                    resolution = attempt_resolution(events, number, now())
                    if not events or resolution["state"] == "retry_wait":
                        resolution = {"state": "paused", "text": "", "reason": "Interrupted persistence; recovery review required"}
                    decision = {"kind": "attempt_resolved", "slot_id": slot, "attempt": number, **resolution}
                    ledger.append(decision)
                    decisions.append(decision)
                if decisions:
                    decision = decisions[-1]
                    if decision["state"] in TERMINAL:
                        outcomes[slot] = decision
                        if progress:
                            progress({"completed_slots": len(outcomes), "stage_slots": len(tasks), "slot_id": slot, "state": decision["state"]})
                        break
                    if decision["state"] in {"paused", "stopped"}:
                        return {"status": decision["state"], "slot_id": slot, "completed_slots": len(outcomes)}
                    if decision["state"] != "retry_wait":
                        raise IntegrityError("Unknown persisted decision")
                    # Sleep in short increments so the CLI remains interruptible.
                    remaining = max(0, decision["retry_not_before"] - now())
                    while remaining > 0:
                        duration = min(remaining, 30)
                        sleep(duration)
                        remaining -= duration
                number = len(starts) + 1
                if number > 3:
                    raise IntegrityError("Persistent attempt limit exceeded")
                all_starts = [r for r in ledger.records if r["kind"] == "attempt_started"]
                cost = sum(plan["reservation_usd_per_attempt"][r["provider"]] for r in all_starts)
                if len(all_starts) >= plan["max_total_attempts"] or cost + plan["reservation_usd_per_attempt"][task["provider"]] > plan["budget_limit_usd"]:
                    return {"status": "budget_paused", "slot_id": slot, "completed_slots": len(outcomes)}
                stage_starts = [r for r in all_starts if r["slot_id"] in stage["slot_ids"]]
                stage_cost = sum(plan["reservation_usd_per_attempt"][r["provider"]] for r in stage_starts)
                if len(stage_starts) >= stage["max_total_attempts"] or stage_cost + plan["reservation_usd_per_attempt"][task["provider"]] > stage["budget_limit_usd"] + 1e-9:
                    return {"status": "stage_budget_paused", "slot_id": slot, "completed_slots": len(outcomes)}
                fixture = None
                if mode == "mock":
                    fixture = fixtures[slot][number - 1]
                    if type(fixture) is not HTTPFixture:
                        raise IntegrityError("Mock HTTP fixture required; no network fallback")
                ledger.append({"kind": "attempt_started", "slot_id": slot, "provider": task["provider"],
                               "attempt": number, "task_sha256": digest(task), "time": now(), "possible_duplicate": number > 1, "stage_number": stage["stage_number"]})
                events = []
                def persist(event):
                    ledger.append({"kind": "stream_event", "slot_id": slot, "attempt": number, "event": event, "time": now()})
                    events.append(event)
                _process_events(task, keys[task["provider"]], fixture, deadline, persist)
                ledger.append({"kind": "attempt_resolved", "slot_id": slot, "attempt": number,
                               **attempt_resolution(events, number, now())})
        return {"status": "stage_complete", "stage_number": stage["stage_number"], "completed_slots": len(outcomes), "journal_head": ledger.head}
