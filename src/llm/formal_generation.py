"""Offline reference implementation of the approved formal attempt policy.

Only SyntheticTransport is executable. Its fixtures can contain normalized
events or MockSDKAttempt responses that exercise actual SDKs against mocked HTTP.
No environment credentials or live transports are loaded. Live integration is
a separate release gate; passing these tests does not authorize generation.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import re
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass


class IntegrityError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_once(path, value):
    """Publish a complete file without replacing any existing evidence."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(name)


@contextmanager
def batch_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise IntegrityError("Another process holds the batch lock") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def read_journal(root):
    records = []
    previous = None
    for index, path in enumerate(sorted(Path(root).glob("event-*.json"))):
        if path.name != f"event-{index:06d}.json":
            raise IntegrityError("Missing or unexpected journal sequence")
        try:
            item = json.loads(path.read_text())
            payload = item["payload"]
            if item["previous"] != previous or item["sha256"] != digest([previous, payload]):
                raise IntegrityError("Journal hash mismatch")
        except (ValueError, KeyError) as exc:
            raise IntegrityError("Unreadable journal record") from exc
        records.append(payload)
        previous = item["sha256"]
    return records, previous


def append(root, payload):
    records, previous = read_journal(root)
    write_once(Path(root) / f"event-{len(records):06d}.json",
               {"previous": previous, "payload": payload, "sha256": digest([previous, payload])})


def classify_error(event):
    """Require an explicit transient classification before the HTTP retry list.

    Future adapters must inspect provider error payloads, not only status codes.
    Unknown quota/resource-exhaustion responses pause until that distinction is
    resolved. These normalized fixtures do not implement vendor classifiers.
    """
    code = event.get("code", "unknown")
    status = event.get("http_status")
    if code in {"authentication", "permission", "unsupported_parameter", "unsupported_model",
                "permanent_quota", "billing"} or status in {400, 401, 403, 404, 422}:
        return "stop"
    if code in {"timeout", "transport", "transient_rate_limit", "transient_server"}:
        if status is None or status in {408, 429} or (isinstance(status, int) and 500 <= status <= 599):
            return "retry"
    return "pause"


def visible_text(provider, response):
    """Extract one requested candidate's visible text, never thinking blocks."""
    if provider == "anthropic":
        return "".join(b.get("text", "") for b in response.get("content", []) if b.get("type") == "text")
    if provider == "openai":
        choices = response.get("choices", [])
        if len(choices) > 1:
            raise IntegrityError("Multiple response candidates were not requested")
        message = choices[0].get("message", {}) if choices else {}
        return (message.get("content") or "") + (message.get("refusal") or "")
    if provider == "gemini":
        candidates = response.get("candidates", [])
        if len(candidates) > 1:
            raise IntegrityError("Multiple response candidates were not requested")
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "".join(p.get("text", "") for p in parts if not p.get("thought", False))
    raise ValueError("Unsupported provider")


@dataclass(frozen=True)
class SyntheticTransport:
    """Each attempt has a list of normalized, synthetic stream events.

    Event types: text (text plus raw evidence), completed, error, delay. A
    provider adapter must durably attribute every event to a frozen task and
    must expose every transmission, with SDK retries disabled.
    """
    attempts: tuple


def _synthetic_worker(connection, events):
    try:
        from .formal_providers import MockSDKAttempt
        if type(events) is MockSDKAttempt:
            events = events.events()
        for event in events:
            if event["type"] == "delay":
                time.sleep(event["seconds"])
            else:
                connection.send(event)
    except BaseException:
        connection.send({"type": "error", "code": "worker_exception"})
    finally:
        connection.close()


def stream_fixture(events, deadline_seconds):
    """A wall-clock deadline terminates the isolated local worker.

    This does not claim cancellation of a remote provider request. At most one
    synthetic worker runs. An actual adapter still needs its own integration
    checks for partial stream capture, transmission counting and retrieval.
    """
    ctx = mp.get_context("spawn")
    reader, writer = ctx.Pipe(duplex=False)
    worker = ctx.Process(target=_synthetic_worker, args=(writer, events))
    deadline = time.monotonic() + deadline_seconds
    worker.start()
    writer.close()
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if reader.poll(min(remaining, 0.05)):
                try:
                    event = reader.recv()
                except EOFError:
                    yield {"type": "error", "code": "unexpected_eof"}
                    return
                yield event
                if event.get("type") in {"completed", "error"}:
                    return
        # Drain data already received before ending the local worker.
        if worker.is_alive():
            worker.terminate()
        worker.join(timeout=1)
        while reader.poll():
            try:
                event = reader.recv()
            except EOFError:
                break
            yield event
            if event.get("type") in {"completed", "error"}:
                return
        yield {"type": "error", "code": "timeout", "remote_completion_possible": True}
    finally:
        if worker.is_alive():
            worker.terminate()
        worker.join(timeout=1)
        if worker.is_alive():
            worker.kill()
            worker.join()
        reader.close()


def validate_manifest(manifest):
    if manifest.get("mode") != "offline_test" or manifest.get("network_allowed") is not False:
        raise IntegrityError("This implementation only executes offline synthetic fixtures")
    tasks = manifest.get("tasks", [])
    ids = [task["slot_id"] for task in tasks]
    if not ids or len(ids) != len(set(ids)) or any(not re.fullmatch(r"[A-Za-z0-9_-]+", x) for x in ids):
        raise IntegrityError("Task identifiers must be unique and safe")
    required = {"case_id", "provider", "model", "system_prompt", "user_prompt", "parameters", "source_hashes"}
    if any(not required.issubset(t) for t in tasks):
        raise IntegrityError("Incomplete task identity")


def run_offline(root, manifest, transports, *, deadline_seconds=600, now=time.time, sleep=time.sleep):
    """Exercise policy with synthetic transports; never contact a provider.

    Persistent starts conservatively reserve an attempt before transmission.
    A crash between reservation and transmission is ambiguous and pauses: no
    additional request is issued automatically. A technical recovery tool is
    deliberately not provided by this offline implementation.
    """
    validate_manifest(manifest)
    if not math.isfinite(deadline_seconds) or not 0 < deadline_seconds <= 600:
        raise ValueError("Deadline must be in (0, 600]")
    if set(transports) != {t["slot_id"] for t in manifest["tasks"]}:
        raise ValueError("Fixture roster mismatch")
    if any(type(t) is not SyntheticTransport for t in transports.values()):
        raise IntegrityError("Only built-in synthetic transports are allowed")
    root = Path(root)
    with batch_lock(root):
        manifest_path = root / "task_manifest.json"
        envelope = {"manifest": manifest, "sha256": digest(manifest), "deadline_seconds": deadline_seconds}
        if manifest_path.exists():
            if json.loads(manifest_path.read_text()) != envelope:
                raise IntegrityError("Frozen manifest changed; no outputs may be superseded")
        else:
            if list(root.glob("event-*.json")):
                raise IntegrityError("Journal exists without its frozen manifest")
            write_once(manifest_path, envelope)
        all_records, _ = read_journal(root)
        halted = next((r for r in all_records if r["kind"] == "batch_halt"), None)
        outcomes = {}
        for task in manifest["tasks"]:
            slot = task["slot_id"]
            records, _ = read_journal(root)
            records = [r for r in records if r.get("slot_id") == slot]
            finals = [r for r in records if r["kind"] == "outcome"]
            if finals:
                outcomes[slot] = finals[0]
                continue
            if halted:
                return {"status": halted["status"], "outcomes": outcomes}
            starts = [r for r in records if r["kind"] == "start"]
            endings = [r for r in records if r["kind"] == "attempt_end"]
            captured = "".join(r["event"]["text"] for r in records
                               if r["kind"] == "capture" and r["event"].get("type") == "text")
            if captured.strip():
                outcome = {"kind": "outcome", "slot_id": slot, "status": "captured",
                           "text": captured, "recovered_after_interruption": True}
                append(root, outcome)
                outcomes[slot] = outcome
                continue
            if len(starts) != len(endings):
                halt = {"kind": "batch_halt", "slot_id": slot, "status": "paused",
                        "reason": "Interrupted attempt requires retrieval/recovery review"}
                append(root, halt)
                return {"status": "paused", "outcomes": outcomes}
            # A crash after attempt_end but before outcome must not reopen a
            # completed empty response, permanent error or exhausted slot.
            if endings:
                last = endings[-1]
                if last["action"] != "retry":
                    if last["action"] in {"empty", "exhausted"}:
                        outcome = {"kind": "outcome", "slot_id": slot, "status": last["action"], "text": ""}
                        append(root, outcome)
                        outcomes[slot] = outcome
                        continue
                    halt = {"kind": "batch_halt", "slot_id": slot, "status": last["action"], "reason": "Recovered terminal attempt"}
                    append(root, halt)
                    return {"status": last["action"], "outcomes": outcomes}
                sleep(max(0, last["retry_not_before"] - now()))
            for number in range(len(starts) + 1, 4):
                fixture = transports[slot]
                if len(fixture.attempts) < number:
                    raise ValueError("Missing synthetic attempt fixture")
                append(root, {"kind": "start", "slot_id": slot, "attempt": number,
                              "task_sha256": digest(task), "time": now(),
                              "possible_duplicate": number > 1})
                chunks = []
                terminal = {"type": "error", "code": "unknown"}
                for event in stream_fixture(fixture.attempts[number - 1], deadline_seconds):
                    if ("task_sha256" in event and event["task_sha256"] != digest(task)) or (
                        "slot_id" in event and event["slot_id"] != slot):
                        raise IntegrityError("Stream event belongs to a different frozen task")
                    if event.get("type") == "text":
                        if not isinstance(event.get("text"), str) or "raw" not in event:
                            raise IntegrityError("Text event lacks raw evidence or valid text")
                        chunks.append(event["text"])
                    elif event.get("type") in {"completed", "error"}:
                        terminal = event
                    else:
                        raise IntegrityError("Unknown stream event")
                    append(root, {"kind": "capture", "slot_id": slot, "attempt": number, "event": event})
                captured = "".join(chunks)
                if captured.strip():
                    action = "captured"
                elif terminal["type"] == "completed":
                    action = "empty"
                else:
                    action = classify_error(terminal)
                delay = terminal.get("retry_after_seconds", 0)
                if action == "retry":
                    if (not isinstance(delay, (int, float)) or not math.isfinite(delay) or delay < 0 or delay > 300):
                        action = "pause"
                    elif number == 3:
                        action = "exhausted"
                end = {"kind": "attempt_end", "slot_id": slot, "attempt": number,
                       "action": action, "terminal": terminal, "time": now()}
                if action == "retry":
                    end["retry_not_before"] = now() + max([5, 30][number - 1], delay)
                append(root, end)
                if action in {"captured", "empty", "exhausted"}:
                    outcome = {"kind": "outcome", "slot_id": slot, "status": action,
                               "text": captured, "attempt": number, "terminal": terminal}
                    append(root, outcome)
                    outcomes[slot] = outcome
                    break
                if action in {"stop", "pause"}:
                    append(root, {"kind": "batch_halt", "slot_id": slot, "status": action,
                                  "reason": terminal})
                    return {"status": action, "outcomes": outcomes}
                sleep(max(0, end["retry_not_before"] - now()))
        return {"status": "complete", "outcomes": outcomes}
