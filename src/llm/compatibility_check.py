"""Authorized synthetic compatibility check, persistent capture and recovery.

This is deliberately not an entry point for formal participant reports. The
three fixed synthetic tasks are reconstructed and compared before every run.
Only the explicit live mode may load real keys or create a network transport.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import time

from .formal_generation import IntegrityError, append, batch_lock, digest, read_journal, visible_text, write_once
from .formal_providers import stream_attempt

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/formal_study/compatibility_check_v1"
LIVE_ROOT = ROOT / "data/compatibility_checks/synthetic_v1"
CONFIG = ROOT / "docs/formal_study/generation_preflight_v1/provider_candidates.json"
SYSTEM = "You are testing a text generation interface using entirely fictional, nonclinical data. Use only the supplied data."
USER = ("Fictional bench sensor A recorded values 2, 4, and 6 arbitrary units. "
        "No reference range or threshold is supplied. Write four short numbered sections: "
        "1. Repeat the observations. 2. Give their arithmetic mean. "
        "3. State what cannot be concluded without a reference. "
        "4. Ask one question about the missing reference. Keep the response under 180 words.")
KEY_NAMES = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
PACKAGES = ["openai", "anthropic", "google-genai", "httpx", "httpx2"]
CODE_FILES = ["src/llm/compatibility_check.py", "src/llm/formal_providers.py",
              "src/llm/formal_generation.py", "scripts/run_compatibility_check.py"]
PRICES = {"anthropic": {"input": 5, "output": 25}, "openai": {"input": 10, "output": 50},
          "gemini": {"input": 2, "output": 12}}
# Include the documented OpenAI cache-write rate in the conservative reservation.
RESERVED_INPUT_RATES = {"anthropic": 5, "openai": 12.5, "gemini": 2}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_plan():
    config = json.loads(CONFIG.read_text())
    expected = {"anthropic": ("claude-opus-5", "max_tokens"), "openai": ("gpt-6-astra", "max_completion_tokens"),
                "gemini": ("gemini-3.1-pro-preview", "max_output_tokens")}
    if len(config["providers"]) != 3 or {p["provider"] for p in config["providers"]} != set(expected):
        raise IntegrityError("Compatibility roster changed")
    for p in config["providers"]:
        model, cap = expected[p["provider"]]
        if p["model"] != model or p["parameters"].get(cap) != 8000:
            raise IntegrityError("This compatibility plan requires the reviewed model roster and 8000 candidate cap")
    sources = {p: sha(ROOT / p) for p in CODE_FILES}
    sources[str(CONFIG.relative_to(ROOT))] = sha(CONFIG)
    tasks = [{"slot_id": "synthetic_v1_" + p["provider"], "case_id": "synthetic_bench_sensor_v1",
              "provider": p["provider"], "model": p["model"], "parameters": p["parameters"],
              "system_prompt": SYSTEM, "user_prompt": USER, "source_hashes": sources}
             for p in config["providers"]]
    reservation = {p: round((2000 * RESERVED_INPUT_RATES[p] + 8000 * PRICES[p]["output"]) / 1e6, 6)
                   for p in PRICES}
    return {"version": "synthetic-compatibility-v1", "scope": "Synthetic API compatibility only",
            "formal_generation_authorized": False, "tasks": tasks, "source_sha256": sources,
            "sdk_versions": {p: version(p) for p in PACKAGES}, "max_attempts_per_slot": 3,
            "max_total_dispatches": 9, "attempt_deadline_seconds": 600,
            "backoff_seconds": [5, 30], "retry_after_pause_threshold_seconds": 300,
            "live_output_directory": str(LIVE_ROOT.relative_to(ROOT)),
            "budget_limit_usd": 3.0, "input_token_reservation_per_attempt": 2000,
            "reservation_usd_per_attempt": reservation,
            "estimated_maximum_usd": round(3 * sum(reservation.values()), 6),
            "price_checked_date": "2026-09-18", "standard_prices_usd_per_million": PRICES,
            "cost_scope": "Conservative token estimate, not an enforceable provider billing cap; excludes taxes and account-specific charges",
            "price_sources": ["https://developers.openai.com/api/docs/models/gpt-6-astra",
                "https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5",
                "https://ai.google.dev/gemini-api/docs/pricing"],
            "remote_recovery_policy": "Pause uncertain no-text completions for documented retrieval review before any retry",
            "content_policy": "Retain first captured text, including truncation/refusal; terminal empty responses are not regenerated"}


def validate_plan(plan):
    if plan != build_plan():
        raise IntegrityError("Plan, source files, installed versions or fixed synthetic inputs changed; prepare and review again")
    if len(plan["tasks"]) != 3 or any(t["case_id"] != "synthetic_bench_sensor_v1" for t in plan["tasks"]):
        raise IntegrityError("Only the three registered synthetic slots are allowed")


def validate_authorization(plan, authorization):
    if (authorization.get("approved") is not True or authorization.get("scope") != plan["scope"] or
        authorization.get("plan_sha256") != digest(plan) or authorization.get("max_total_dispatches") != 9 or
        authorization.get("budget_limit_usd") != 3.0 or not authorization.get("confirmation_source") or
        not authorization.get("recorded_by") or not authorization.get("confirmed_at")):
        raise IntegrityError("Specific authorization for this exact three-slot plan is required")


def load_keys():
    """Read credentials only after live authorization, without printing them."""
    values = {p: os.environ.get(name) for p, name in KEY_NAMES.items()}
    if not all(values.values()):
        from dotenv import dotenv_values
        local = dotenv_values(ROOT / ".env") if (ROOT / ".env").exists() else {}
        for p, name in KEY_NAMES.items():
            values[p] = values[p] or local.get(name)
        values["gemini"] = values["gemini"] or os.environ.get("GOOGLE_API_KEY") or local.get("GOOGLE_API_KEY")
    missing = [KEY_NAMES[p] for p, value in values.items() if not value]
    if missing:
        raise IntegrityError("Missing credential variable(s): " + ", ".join(missing))
    return values


@dataclass(frozen=True)
class HTTPFixture:
    status: int = 200
    chunks: tuple = ()
    headers: tuple = (("content-type", "text/event-stream"),)
    stall_seconds: float = 0


def _worker(connection, task, api_key, fixture):
    """Dispatch cannot proceed until the parent's durable reservation is acked."""
    import httpx

    def before_dispatch(wire_hash):
        connection.send({"type": "dispatch_requested", "task_sha256": digest(task), "wire_body_sha256": wire_hash})
        if connection.recv() != "durably_recorded":
            raise IntegrityError("Parent did not acknowledge dispatch reservation")

    try:
        if fixture is None:
            transport = httpx.HTTPTransport(retries=0)
        else:
            class Stream(httpx.SyncByteStream):
                def __iter__(self):
                    yield from fixture.chunks
                    if fixture.stall_seconds:
                        time.sleep(fixture.stall_seconds)

            transport = httpx.MockTransport(lambda _: httpx.Response(fixture.status,
                headers=dict(fixture.headers), stream=Stream()))
        for event in stream_attempt(task, api_key=api_key, transport=transport, before_dispatch=before_dispatch):
            connection.send(event)
    except BaseException as exc:
        # Never serialize credentials or arbitrary exception messages.
        try:
            connection.send({"type": "error", "code": "worker_exception", "exception_type": type(exc).__name__})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def _process_events(task, api_key, fixture, deadline, persist):
    context = mp.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=_worker, args=(child, task, api_key, fixture))
    expires = time.monotonic() + deadline
    process.start()
    child.close()
    terminal = False
    dispatches = 0

    def receive(event, allow_dispatch=True):
        nonlocal terminal, dispatches
        if "task_sha256" in event and event["task_sha256"] != digest(task):
            raise IntegrityError("Worker task attribution mismatch")
        if event.get("type") == "dispatch_requested":
            dispatches += 1
            if dispatches > 1:
                raise IntegrityError("Second dispatch reservation within one attempt")
            persist(event)
            if allow_dispatch:
                parent.send("durably_recorded")
        elif event.get("type") in {"text", "completed", "error"}:
            persist(event)
            if event["type"] in {"completed", "error"}:
                terminal = True
        else:
            raise IntegrityError("Unexpected worker event")

    try:
        while time.monotonic() < expires and not terminal:
            if parent.poll(min(0.05, max(0, expires - time.monotonic()))):
                try:
                    event = parent.recv()
                except EOFError:
                    break
                receive(event)
        if not terminal:
            if process.is_alive():
                process.terminate()
            process.join(timeout=1)
            while parent.poll():
                try:
                    event = parent.recv()
                except (EOFError, OSError):
                    break
                receive(event, allow_dispatch=False)
            if not terminal:
                persist({"type": "error", "code": "timeout" if time.monotonic() >= expires else "worker_interrupted",
                         "remote_completion_possible": dispatches > 0})
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join()
        parent.close()


def attempt_resolution(events, number, now):
    from .formal_generation import classify_error
    text = "".join(e.get("text", "") for e in events if e["type"] == "text")
    terminal = next((e for e in reversed(events) if e["type"] in {"completed", "error"}), None)
    if text.strip():
        return {"state": "captured", "text": text, "terminal": terminal}
    if terminal is None:
        return {"state": "paused", "reason": "Interrupted attempt needs technical recovery", "text": ""}
    if terminal["type"] == "completed":
        return {"state": "empty", "text": "", "terminal": terminal}
    action = classify_error(terminal)
    if action == "stop":
        return {"state": "stopped", "text": "", "terminal": terminal}
    # Even a recognized timeout may have completed remotely. Pause first;
    # retrievability is reviewed before an operator can authorize a duplicate.
    if action != "retry" or terminal.get("remote_completion_possible") or terminal.get("code") in {"timeout", "transport"}:
        return {"state": "paused", "text": "", "terminal": terminal,
                "reason": "Review raw evidence and retrieval before any retry"}
    delay = terminal.get("retry_after_seconds", 0)
    if not isinstance(delay, (float, int)) or not math.isfinite(delay) or delay < 0 or delay > 300:
        return {"state": "paused", "text": "", "terminal": terminal, "reason": "Retry-After requires review"}
    if number >= 3:
        return {"state": "exhausted", "text": "", "terminal": terminal}
    return {"state": "retry_wait", "text": "", "terminal": terminal,
            "retry_not_before": now + max([5, 30][number - 1], delay)}


def _slot_records(root, slot):
    return [r for r in read_journal(root)[0] if r.get("slot_id") == slot]


def run_check(root, plan, *, mode="mock", authorization=None, fixtures=None, deadline=None, sleep=time.sleep, now=time.time):
    validate_plan(plan)
    root = Path(root).resolve()
    if mode == "live":
        validate_authorization(plan, authorization or {})
        if root != LIVE_ROOT.resolve() or fixtures is not None or deadline is not None:
            raise IntegrityError("Live output path, transports and deadline are fixed by the plan")
        keys = load_keys()
        deadline = 600
    elif mode == "mock":
        if root == LIVE_ROOT.resolve() or not isinstance(fixtures, dict):
            raise IntegrityError("Mock runs require explicit fixtures and a separate output directory")
        keys = {p: "fake-offline-key" for p in KEY_NAMES}
        deadline = 600 if deadline is None else deadline
        if not 0 < deadline <= 600:
            raise ValueError("Invalid mock deadline")
    else:
        raise ValueError("Mode must be live or mock")
    envelope = {"plan": plan, "plan_sha256": digest(plan), "mode": mode,
                "authorization": authorization if mode == "live" else None, "deadline": deadline}
    with batch_lock(root):
        path = root / "run_manifest.json"
        if path.exists():
            if json.loads(path.read_text()) != envelope:
                raise IntegrityError("Run identity changed; existing evidence cannot be superseded")
        elif read_journal(root)[0]:
            raise IntegrityError("Journal has no run manifest")
        else:
            write_once(path, envelope)
        outcomes = {}
        for task in plan["tasks"]:
            slot = task["slot_id"]
            while True:
                records = _slot_records(root, slot)
                starts = [r for r in records if r["kind"] == "attempt_started"]
                decisions = [r for r in records if r["kind"] in {"attempt_resolved", "recovery"}]
                if starts and (not decisions or decisions[-1]["attempt"] < starts[-1]["attempt"]):
                    number = starts[-1]["attempt"]
                    events = [r["event"] for r in records if r["kind"] == "stream_event" and r["attempt"] == number]
                    resolution = attempt_resolution(events, number, now())
                    if not events or resolution["state"] == "retry_wait":
                        resolution = {"state": "paused", "text": "", "reason": "Interrupted persistence; technical recovery required"}
                    decision = {"kind": "attempt_resolved", "slot_id": slot, "attempt": number, **resolution}
                    append(root, decision)
                    decisions.append(decision)
                if decisions:
                    decision = decisions[-1]
                    state = decision["state"]
                    if state in {"captured", "empty", "exhausted", "closed_no_report"}:
                        outcomes[slot] = decision
                        break
                    if state in {"paused", "stopped"}:
                        return {"status": state, "slot_id": slot, "outcomes": outcomes, "reason": decision.get("reason")}
                    if state != "retry_wait":
                        raise IntegrityError("Unrecognized persisted decision")
                    sleep(max(0, decision["retry_not_before"] - now()))
                number = len(starts) + 1
                if number > 3:
                    raise IntegrityError("Attempt budget exhausted")
                all_starts = [r for r in read_journal(root)[0] if r["kind"] == "attempt_started"]
                cost = sum(plan["reservation_usd_per_attempt"][r["provider"]] for r in all_starts)
                if len(all_starts) >= 9 or cost + plan["reservation_usd_per_attempt"][task["provider"]] > plan["budget_limit_usd"]:
                    raise IntegrityError("Call or conservative cost reservation limit reached")
                fixture = None
                if mode == "mock":
                    fixture = fixtures[slot][number - 1]
                    if type(fixture) is not HTTPFixture:
                        raise IntegrityError("Mock fixture type required; network fallback forbidden")
                append(root, {"kind": "attempt_started", "slot_id": slot, "provider": task["provider"],
                              "attempt": number, "task_sha256": digest(task), "time": now(),
                              "possible_duplicate": number > 1})
                events = []
                def persist(event):
                    append(root, {"kind": "stream_event", "slot_id": slot, "attempt": number, "event": event, "time": now()})
                    events.append(event)
                _process_events(task, keys[task["provider"]], fixture, deadline, persist)
                resolution = attempt_resolution(events, number, now())
                append(root, {"kind": "attempt_resolved", "slot_id": slot, "attempt": number, **resolution})
        return {"status": "complete", "outcomes": outcomes}


def recovery(root, plan, decision):
    """Apply a documented local technical decision; never contacts a provider.

    All recovery decisions are bound to the current journal head and exact task.
    Retry is allowed only for paused attempts after a recorded transient-error
    determination and retrieval review. The lifetime three-attempt cap remains.
    """
    validate_plan(plan)
    root = Path(root)
    with batch_lock(root):
        envelope = json.loads((root / "run_manifest.json").read_text())
        if envelope["plan_sha256"] != digest(plan):
            raise IntegrityError("Recovery plan differs from run")
        records, head = read_journal(root)
        if decision.get("journal_head") != head:
            raise IntegrityError("Recovery decision is stale")
        task = next((t for t in plan["tasks"] if t["slot_id"] == decision.get("slot_id")), None)
        if task is None or decision.get("task_sha256") != digest(task):
            raise IntegrityError("Recovery task mismatch")
        if not all(decision.get(k) for k in ["reviewer", "reviewed_at", "evidence_note", "confirmation_source"]):
            raise IntegrityError("Recovery requires a named technical review and evidence")
        slot_records = [r for r in records if r.get("slot_id") == task["slot_id"]]
        starts = [r for r in slot_records if r["kind"] == "attempt_started"]
        if not starts:
            raise IntegrityError("No attempt to recover")
        number = starts[-1]["attempt"]
        states = [r for r in slot_records if r["kind"] in {"attempt_resolved", "recovery"}]
        if states and states[-1]["state"] in {"captured", "empty", "exhausted", "closed_no_report"}:
            raise IntegrityError("Terminal output cannot be reopened")
        events = [r["event"] for r in slot_records if r["kind"] == "stream_event" and r["attempt"] == number]
        if any(e.get("text", "").strip() for e in events) or any(e["type"] == "completed" for e in events):
            raise IntegrityError("Captured or completed evidence must be recovered by resume, not replaced")
        action = decision.get("action")
        base = {"kind": "recovery", "slot_id": task["slot_id"], "attempt": number,
                "decision": decision, "text": ""}
        if action == "close_no_report":
            base["state"] = "closed_no_report"
        elif action == "retry":
            current_states = [r for r in states if r["attempt"] == number]
            inferred = attempt_resolution(events, number, time.time())
            if number >= 3 or inferred["state"] == "stopped" or (current_states and current_states[-1]["state"] == "stopped"):
                raise IntegrityError("Stopped or exhausted attempts cannot be retried")
            if current_states and current_states[-1]["state"] != "paused":
                raise IntegrityError("Only a paused attempt can receive retry recovery")
            if decision.get("retrieval_status") not in {"not_supported_for_registered_request", "checked_no_text", "checked_unavailable"} or decision.get("confirmed_transient") is not True:
                raise IntegrityError("Retry requires a transient determination and retrieval review")
            not_before = decision.get("retry_not_before")
            event_records = [r for r in slot_records if r["kind"] == "stream_event" and r["attempt"] == number]
            last_event_time = event_records[-1]["time"] if event_records else starts[-1]["time"]
            minimum = last_event_time + [5, 30][min(number - 1, 1)]
            for record in event_records:
                event = record["event"]
                delay = event.get("retry_after_seconds")
                if isinstance(delay, (float, int)) and math.isfinite(delay):
                    minimum = max(minimum, record["time"] + delay)
            if not isinstance(not_before, (float, int)) or not math.isfinite(not_before) or not_before < minimum:
                raise IntegrityError("Recovery retry time violates the waiting period")
            base.update(state="retry_wait", retry_not_before=not_before, possible_duplicate=True)
        elif action == "attach_response":
            body = decision.get("raw_response")
            text = visible_text(task["provider"], body) if isinstance(body, dict) else ""
            if not text.strip() or not decision.get("response_attribution_verified"):
                raise IntegrityError("Recovered output requires raw response and verified task attribution")
            response_id = body.get("id") or body.get("response_id") or body.get("responseId")
            known = {e.get("metadata", {}).get("response_id") for e in events} - {None}
            if known and (response_id not in known):
                raise IntegrityError("Recovered response ID does not match captured metadata")
            base.update(state="captured", text=text, recovered_response=True)
        else:
            raise IntegrityError("Unsupported recovery action")
        append(root, base)
        return base


def status(root):
    """Read-only operational summary, without response text or credentials."""
    root = Path(root)
    if not (root / "run_manifest.json").exists():
        return {"status": "not_started", "attempts_reserved": 0, "dispatches_reserved": 0}
    records, head = read_journal(root)
    states = {}
    for record in records:
        if record["kind"] == "attempt_started":
            states[record["slot_id"]] = "incomplete_attempt"
        if record["kind"] in {"attempt_resolved", "recovery"}:
            states[record["slot_id"]] = record["state"]
    return {"status": "recorded", "journal_head": head, "slots": states,
            "attempts_reserved": sum(r["kind"] == "attempt_started" for r in records),
            "dispatches_reserved": sum(r["kind"] == "stream_event" and r["event"]["type"] == "dispatch_requested" for r in records)}


def technical_results(root):
    """Describe transport outcomes without grading content or ranking models."""
    root = Path(root)
    envelope = json.loads((root / "run_manifest.json").read_text())
    records, head = read_journal(root)
    rows = []
    for task in envelope["plan"]["tasks"]:
        selected = [r for r in records if r.get("slot_id") == task["slot_id"]]
        decisions = [r for r in selected if r["kind"] in {"attempt_resolved", "recovery"}]
        latest = decisions[-1] if decisions else {}
        events = [r["event"] for r in selected if r["kind"] == "stream_event"]
        metadata = next((e["metadata"] for e in reversed(events) if e.get("metadata")), {})
        text = latest.get("text", "")
        finish = metadata.get("finish_reason")
        completed = any(e["type"] == "completed" for e in events)
        rows.append({"slot_id": task["slot_id"], "requested_model": task["model"],
            "state": latest.get("state", "not_started"), "visible_text_characters": len(text),
            "attempts_reserved": sum(r["kind"] == "attempt_started" for r in selected),
            "dispatches_reserved": sum(e["type"] == "dispatch_requested" for e in events),
            "normal_stream_completion": completed, "finish_reason": finish,
            "token_limit_reached": finish in {"length", "max_tokens", "MAX_TOKENS"},
            "response_model": metadata.get("response_model"), "response_id": metadata.get("response_id"),
            "usage": metadata.get("usage", {}),
            "request_capture_complete": bool(text.strip()) and completed and bool(metadata.get("usage")) and bool(metadata.get("response_model")),
            "formal_generation_authorized": False})
    return {"scope": "Technical compatibility only; no clinical quality assessment", "mode": envelope["mode"],
            "journal_head": head, "results": rows,
            "adequate_for_formal_token_budget": "Not established by a short synthetic check",
            "configuration_frozen": False, "formal_generation_authorized": False}
