"""Formal batch execution with exact-plan authorization and durable dispatch.

The existing synthetic compatibility runner and its frozen source files remain
unchanged. This entry point has no default live mode and never selects responses
by quality. Source and SDK identities must match on every resume.
"""
from __future__ import annotations

import hashlib
from importlib.metadata import version
from itertools import permutations
import json
import math
from pathlib import Path
import random
import time

from .compatibility_check import HTTPFixture, PACKAGES, _process_events, attempt_resolution, load_keys
from .formal_generation import IntegrityError, batch_lock, digest, read_journal, visible_text, write_once

ROOT = Path(__file__).resolve().parents[2]
LIVE_ROOT = ROOT / "data/reports_formal_v1"
TERMINAL = {"captured", "empty", "exhausted", "closed_no_report"}
PROVIDERS = {"anthropic", "openai", "gemini"}
RELEASE_CHECKS = {
    "output_allowance_confirmed", "effective_parameters_recorded", "representative_synthetic_check_reviewed",
    "formal_runner_offline_checks_passed", "full_rating_assets_verified", "analysis_and_adjudication_import_verified",
}


def schedule(case_ids, seed=20260919):
    """Thirty-five case blocks; all six provider permutations balanced to one."""
    cases = sorted(case_ids)
    if len(set(cases)) != len(cases):
        raise IntegrityError("Duplicate schedule case")
    rng = random.Random(seed)
    rng.shuffle(cases)
    orders = list(permutations(sorted(PROVIDERS)))
    rng.shuffle(orders)
    return [(case, provider) for index, case in enumerate(cases) for provider in orders[index % 6]]


class Ledger:
    """Verify once under the batch lock; append without quadratic rereads."""
    def __init__(self, root):
        self.root = Path(root)
        self.records, self.head = read_journal(root)

    def append(self, payload):
        value = {"previous": self.head, "payload": payload, "sha256": digest([self.head, payload])}
        write_once(self.root / f"event-{len(self.records):06d}.json", value)
        self.records.append(payload)
        self.head = value["sha256"]

    def slot(self, slot_id):
        return [r for r in self.records if r.get("slot_id") == slot_id]


def validate_plan(plan, *, live=False):
    tasks = plan["tasks"]
    keys = [(t["case_id"], t["provider"]) for t in tasks]
    cases = set(c for c, _ in keys)
    if len(set(t["slot_id"] for t in tasks)) != len(tasks) or set(keys) != {(c, p) for c in cases for p in PROVIDERS} or len(keys) != len(set(keys)):
        raise IntegrityError("Missing, duplicate or unexpected batch slots")
    if keys != schedule(cases, plan["schedule_seed"]):
        raise IntegrityError("Schedule differs from the predeclared content-independent order")
    if plan["max_attempts_per_slot"] != 3 or plan["max_total_attempts"] != 3 * len(tasks) or plan["attempt_deadline_seconds"] != 600:
        raise IntegrityError("Attempt policy changed")
    if set(plan["reservation_usd_per_attempt"]) != PROVIDERS:
        raise IntegrityError("Cost reservation roster mismatch")
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0
           for x in [plan["budget_limit_usd"], *plan["reservation_usd_per_attempt"].values()]):
        raise IntegrityError("Invalid cost reservation")
    for task in tasks:
        if not task["system_prompt"].strip() or not task["user_prompt"].strip():
            raise IntegrityError("Empty frozen input")
        if digest([task["system_prompt"], task["user_prompt"]]) != task["input_pair_sha256"]:
            raise IntegrityError("Input text changed")
    if live:
        if plan.get("scope") == "Formal 25 stroke plus 10 control reports" and len(tasks) == 105:
            from .formal_release import build_candidate
            expected_plan = build_candidate()
        elif plan.get("scope") == "Synthetic full-length output check" and len(tasks) == 3:
            from .full_length_check import build_plan
            expected_plan = build_plan()
        else:
            raise IntegrityError("Live runner accepts only the exact registered study or synthetic check")
        if plan != expected_plan:
            raise IntegrityError("Candidate, sources, reviewed inputs or installed SDK versions changed")
    elif plan.get("scope") not in {"Formal 25 stroke plus 10 control reports", "Synthetic formal-runner fixture", "Synthetic full-length output check"}:
        raise IntegrityError("Unknown batch scope")
    if plan["sdk_versions"] != {p: version(p) for p in PACKAGES}:
        raise IntegrityError("SDK versions changed")


def validate_authorization(plan, authorization):
    if (authorization.get("approved") is not True or authorization.get("plan_sha256") != digest(plan)
            or authorization.get("scope") != plan["scope"]
            or authorization.get("budget_limit_usd") != plan["budget_limit_usd"]
            or authorization.get("max_total_attempts") != plan["max_total_attempts"]
            or not all(authorization.get(k) for k in ("confirmation_source", "recorded_by", "confirmed_at"))):
        raise IntegrityError("Exact-plan formal-generation authorization is required")
    if plan.get("scope") == "Synthetic full-length output check":
        return
    checks = authorization.get("release_checks", {})
    if set(checks) != RELEASE_CHECKS or any(checks[k].get("passed") is not True or not checks[k].get("evidence_sha256") for k in checks):
        raise IntegrityError("Documented release checks are incomplete")
    for record in checks.values():
        evidence = (ROOT / record.get("evidence_path", "")).resolve()
        if not evidence.is_relative_to(ROOT / "docs/formal_study") or not evidence.is_file():
            raise IntegrityError("Release evidence must be a named current formal-study file")
        if hashlib.sha256(evidence.read_bytes()).hexdigest() != record["evidence_sha256"]:
            raise IntegrityError("Release evidence hash changed")


def _verify_envelope(root, plan, mode, authorization, deadline):
    envelope = {"plan": plan, "plan_sha256": digest(plan), "mode": mode,
                "authorization": authorization if mode == "live" else None, "deadline": deadline}
    path = root / "run_manifest.json"
    if path.exists():
        if json.loads(path.read_text()) != envelope:
            raise IntegrityError("Run identity changed; previous evidence cannot be superseded")
    elif read_journal(root)[0]:
        raise IntegrityError("Journal is missing its manifest")
    else:
        write_once(path, envelope)


def run(root, plan, *, mode="mock", authorization=None, fixtures=None, deadline=None, sleep=time.sleep, now=time.time):
    # Reject unsigned live calls before credentials, filesystem mutation or providers.
    if mode == "live":
        validate_authorization(plan, authorization or {})
    validate_plan(plan, live=mode == "live")
    root = Path(root).resolve()
    if mode == "live":
        registered_root = LIVE_ROOT
        if plan["scope"] == "Synthetic full-length output check":
            from .full_length_check import LIVE_ROOT as registered_root
        if root != registered_root.resolve() or fixtures is not None or deadline is not None:
            raise IntegrityError("Live path, transport and deadline are fixed")
        keys, deadline = load_keys(), 600
    elif mode == "mock":
        from .full_length_check import LIVE_ROOT as check_root
        if root in {LIVE_ROOT.resolve(), check_root.resolve()} or not isinstance(fixtures, dict):
            raise IntegrityError("Mock runs require fixtures and a separate output directory")
        keys = {p: "fake-offline-key" for p in PROVIDERS}
        deadline = 600 if deadline is None else deadline
        if not 0 < deadline <= 600:
            raise IntegrityError("Invalid mock deadline")
    else:
        raise IntegrityError("Mode must be mock or live")
    with batch_lock(root):
        _verify_envelope(root, plan, mode, authorization, deadline)
        ledger = Ledger(root)
        outcomes = {}
        for task in plan["tasks"]:
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
                fixture = None
                if mode == "mock":
                    fixture = fixtures[slot][number - 1]
                    if type(fixture) is not HTTPFixture:
                        raise IntegrityError("Mock HTTP fixture required; no network fallback")
                ledger.append({"kind": "attempt_started", "slot_id": slot, "provider": task["provider"],
                               "attempt": number, "task_sha256": digest(task), "time": now(), "possible_duplicate": number > 1})
                events = []
                def persist(event):
                    ledger.append({"kind": "stream_event", "slot_id": slot, "attempt": number, "event": event, "time": now()})
                    events.append(event)
                _process_events(task, keys[task["provider"]], fixture, deadline, persist)
                ledger.append({"kind": "attempt_resolved", "slot_id": slot, "attempt": number,
                               **attempt_resolution(events, number, now())})
        return {"status": "complete", "completed_slots": len(outcomes), "journal_head": ledger.head}


def recover(root, plan, decision):
    """Local technical review only: no request, no clinical adjudication."""
    root = Path(root)
    with batch_lock(root):
        envelope = json.loads((root / "run_manifest.json").read_text())
        validate_plan(plan, live=envelope["mode"] == "live")
        if envelope["plan_sha256"] != digest(plan):
            raise IntegrityError("Recovery plan mismatch")
        ledger = Ledger(root)
        if decision.get("journal_head") != ledger.head:
            raise IntegrityError("Stale recovery review")
        task = next((t for t in plan["tasks"] if t["slot_id"] == decision.get("slot_id")), None)
        if task is None or decision.get("task_sha256") != digest(task):
            raise IntegrityError("Recovery task mismatch")
        if not all(decision.get(k) for k in ("reviewer", "reviewed_at", "evidence_note", "confirmation_source")):
            raise IntegrityError("Named technical review and evidence required")
        rows = ledger.slot(task["slot_id"])
        starts = [r for r in rows if r["kind"] == "attempt_started"]
        states = [r for r in rows if r["kind"] in {"attempt_resolved", "recovery"}]
        if not starts or not states or states[-1]["attempt"] != starts[-1]["attempt"]:
            raise IntegrityError("Resume must first resolve interrupted persistence")
        if states[-1]["state"] in TERMINAL:
            raise IntegrityError("Terminal output cannot be reopened")
        number = starts[-1]["attempt"]
        event_rows = [r for r in rows if r["kind"] == "stream_event" and r["attempt"] == number]
        events = [r["event"] for r in event_rows]
        if any(e.get("text", "").strip() or e["type"] == "completed" for e in events):
            raise IntegrityError("Resume must preserve existing captured or completed evidence")
        result = {"kind": "recovery", "slot_id": task["slot_id"], "attempt": number, "decision": decision, "text": ""}
        action = decision.get("action")
        if action == "close_no_report":
            result["state"] = "closed_no_report"
        elif action == "retry":
            inferred = attempt_resolution(events, number, time.time())
            if number >= 3 or states[-1]["state"] != "paused" or inferred["state"] == "stopped":
                raise IntegrityError("Stopped, nonpaused or exhausted attempts cannot be retried")
            if decision.get("confirmed_transient") is not True or decision.get("retrieval_status") not in {
                "not_supported_for_registered_request", "checked_no_text", "checked_unavailable"
            }:
                raise IntegrityError("Transient determination and retrieval review required")
            last_time = event_rows[-1]["time"] if event_rows else starts[-1]["time"]
            minimum = last_time + [5, 30][number - 1]
            for row in event_rows:
                delay = row["event"].get("retry_after_seconds")
                if isinstance(delay, (int, float)) and math.isfinite(delay):
                    minimum = max(minimum, row["time"] + delay)
            not_before = decision.get("retry_not_before")
            if not isinstance(not_before, (int, float)) or not math.isfinite(not_before) or not_before < minimum:
                raise IntegrityError("Recovery violates retry waiting period")
            result.update(state="retry_wait", retry_not_before=not_before, possible_duplicate=True)
        elif action == "attach_response":
            body = decision.get("raw_response")
            text = visible_text(task["provider"], body) if isinstance(body, dict) else ""
            if not text.strip() or decision.get("response_attribution_verified") is not True:
                raise IntegrityError("Retrieved response requires raw evidence and task attribution")
            known = {e.get("metadata", {}).get("response_id") for e in events} - {None}
            response_id = body.get("id") or body.get("response_id") or body.get("responseId")
            if known and response_id not in known:
                raise IntegrityError("Retrieved response ID mismatch")
            result.update(state="captured", text=text, recovered_response=True)
        else:
            raise IntegrityError("Unknown technical recovery action")
        ledger.append(result)
        return {"state": result["state"], "slot_id": task["slot_id"], "journal_head": ledger.head}


def terminal_slots(root, plan, *, allow_mock=False):
    """Validate the entire terminal ledger before any packet can be published."""
    root = Path(root)
    envelope = json.loads((root / "run_manifest.json").read_text())
    if envelope["plan_sha256"] != digest(plan) or envelope["plan"] != plan:
        raise IntegrityError("Terminal importer plan mismatch")
    if envelope["mode"] != "live" and not allow_mock:
        raise IntegrityError("Mock evidence is not a formal batch")
    validate_plan(plan, live=envelope["mode"] == "live")
    records, head = read_journal(root)
    if set(r["slot_id"] for r in records) - {t["slot_id"] for t in plan["tasks"]}:
        raise IntegrityError("Unregistered ledger slot")
    output = []
    for task in plan["tasks"]:
        rows = [r for r in records if r["slot_id"] == task["slot_id"]]
        starts = [r for r in rows if r["kind"] == "attempt_started"]
        decisions = [r for r in rows if r["kind"] in {"attempt_resolved", "recovery"}]
        if not starts or len(starts) > 3 or any(r["task_sha256"] != digest(task) for r in starts):
            raise IntegrityError("Missing or mismatched attempt evidence")
        if [r["attempt"] for r in starts] != list(range(1, len(starts) + 1)):
            raise IntegrityError("Attempt sequence changed")
        if not decisions or decisions[-1]["state"] not in TERMINAL or decisions[-1]["attempt"] != starts[-1]["attempt"]:
            raise IntegrityError("All planned slots must be terminal before packaging")
        final = decisions[-1]
        events = [r["event"] for r in rows if r["kind"] == "stream_event" and r["attempt"] == final["attempt"]]
        if final.get("recovered_response"):
            raw = final["decision"]["raw_response"]
            captured = visible_text(task["provider"], raw)
        else:
            captured = "".join(e.get("text", "") for e in events if e["type"] == "text")
        if final["state"] == "captured":
            if not captured.strip() or captured != final["text"]:
                raise IntegrityError("Captured report differs from retained raw evidence")
        elif captured.strip():
            raise IntegrityError("No-report outcome would discard captured text")
        # Earlier captured or completed-empty outcomes cannot be superseded.
        for start in starts[:-1]:
            prior = [r["event"] for r in rows if r["kind"] == "stream_event" and r["attempt"] == start["attempt"]]
            if any(e.get("text", "").strip() or e["type"] == "completed" for e in prior):
                raise IntegrityError("A terminal earlier response was replaced")
        metadata = next((e["metadata"] for e in reversed(events) if e.get("metadata")), {})
        output.append({"slot_id": task["slot_id"], "case_id": task["case_id"], "model_key": task["provider"],
                       "report_text": captured if final["state"] == "captured" else None,
                       "terminal_status": "technical_failure" if final["state"] == "exhausted" else final["state"],
                       "source_sha256": digest({"plan_sha256": digest(plan), "journal_head": head, "slot_records": rows}),
                       "task_sha256": digest(task), "attempts": len(starts), "metadata": metadata,
                       "truncation": metadata.get("finish_reason") in {"length", "max_tokens", "MAX_TOKENS"},
                       "normal_stream_completion": any(e["type"] == "completed" for e in events)})
    return output
