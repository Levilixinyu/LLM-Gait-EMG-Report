"""Failure-mode tests for the prospective policy; all responses are synthetic."""
import copy
import json
import time

import pytest

from src.llm.formal_generation import (
    IntegrityError, SyntheticTransport, append, batch_lock, digest,
    read_journal, run_offline, visible_text, write_once,
)


def manifest():
    return {"mode": "offline_test", "network_allowed": False, "tasks": [{
        "slot_id": "synthetic_openai", "case_id": "synthetic", "provider": "openai",
        "model": "fake-model", "system_prompt": "Synthetic system", "user_prompt": "Synthetic input",
        "parameters": {"max_tokens": 8000}, "source_hashes": {"synthetic": digest("fixture")},
    }]}


def execute(path, attempts, spec=None, **kwargs):
    spec = spec or manifest()
    return run_offline(path, spec, {t["slot_id"]: SyntheticTransport(tuple(attempts)) for t in spec["tasks"]},
                       sleep=kwargs.pop("sleep", lambda _: None), **kwargs)


def text(value):
    return {"type": "text", "text": value, "raw": {"synthetic_delta": value}}


def complete(reason="stop"):
    return {"type": "completed", "finish_reason": reason, "raw": {"synthetic_finish": reason}}


def error(code, **kwargs):
    return {"type": "error", "code": code, **kwargs}


def records(path, kind):
    return [r for r in read_journal(path)[0] if r["kind"] == kind]


@pytest.mark.parametrize("value,reason", [("Partial report", "length"), ("I cannot provide that.", "refusal"), ("Malformed", "stop")])
def test_captured_outputs_survive_resume_without_regeneration(tmp_path, value, reason):
    first = execute(tmp_path, [[text(value), complete(reason)]])
    second = execute(tmp_path, [])
    assert first == second
    assert second["outcomes"]["synthetic_openai"]["text"] == value
    assert len(records(tmp_path, "start")) == 1
    assert (tmp_path / "task_manifest.json").exists()


def test_completed_empty_is_terminal(tmp_path):
    execute(tmp_path, [[text("  "), complete("content_filter")]])
    result = execute(tmp_path, [])
    assert result["outcomes"]["synthetic_openai"]["status"] == "empty"
    assert len(records(tmp_path, "start")) == 1


def test_transient_attempt_budget_and_backoffs_survive_resume(tmp_path):
    delays = []
    clock = [100.0]
    def sleep(seconds):
        delays.append(seconds)
        clock[0] += seconds
    execute(tmp_path, [[error("timeout")]] * 3, now=lambda: clock[0], sleep=sleep)
    assert delays == [5, 30]
    result = execute(tmp_path, [])
    assert result["outcomes"]["synthetic_openai"]["status"] == "exhausted"
    assert len(records(tmp_path, "start")) == 3


@pytest.mark.parametrize("event,status", [
    (error("permanent_quota", http_status=429), "stop"),
    (error("unsupported_model", http_status=503), "stop"),
    (error("resource_exhausted", http_status=429), "pause"),
    (error("transient_rate_limit", http_status=429, retry_after_seconds=301), "pause"),
])
def test_nonretryable_halts_entire_batch_persistently(tmp_path, event, status):
    spec = manifest()
    other = copy.deepcopy(spec["tasks"][0]); other["slot_id"] = "second_slot"
    spec["tasks"].append(other)
    assert execute(tmp_path, [[event]], spec)["status"] == status
    assert execute(tmp_path, [], spec)["status"] == status
    assert len(records(tmp_path, "start")) == 1


def test_partial_text_before_timeout_is_retained(tmp_path):
    result = execute(tmp_path, [[text("Keep this"), error("timeout")]])
    assert result["outcomes"]["synthetic_openai"]["text"] == "Keep this"
    assert len(records(tmp_path, "start")) == 1


def test_retry_after_longer_than_backoff_is_respected(tmp_path):
    delays = []
    execute(tmp_path, [[error("transient_rate_limit", http_status=429, retry_after_seconds=60)],
                       [text("Recovered"), complete()]], now=lambda: 100, sleep=delays.append)
    assert delays == [60]


def test_manifest_and_start_are_saved_before_dispatch(tmp_path, monkeypatch):
    def stream(events, deadline):
        frozen = json.loads((tmp_path / "task_manifest.json").read_text())
        assert frozen["manifest"] == manifest()
        assert len(records(tmp_path, "start")) == 1
        yield text("Recorded after manifest")
        yield complete()
    monkeypatch.setattr("src.llm.formal_generation.stream_fixture", stream)
    execute(tmp_path, [[]])


def test_invalid_text_evidence_cannot_be_recovered_as_valid_output(tmp_path):
    with pytest.raises(IntegrityError, match="raw evidence"):
        execute(tmp_path, [[{"type": "text", "text": "No raw evidence"}]])
    assert execute(tmp_path, [])["status"] == "paused"
    assert not records(tmp_path, "outcome")


def prepare_interruption(path, captured=None, end=None):
    spec = manifest()
    write_once(path / "task_manifest.json", {"manifest": spec, "sha256": digest(spec), "deadline_seconds": 600})
    append(path, {"kind": "start", "slot_id": "synthetic_openai", "attempt": 1})
    if captured:
        append(path, {"kind": "capture", "slot_id": "synthetic_openai", "event": text(captured)})
    if end:
        append(path, {"kind": "attempt_end", "slot_id": "synthetic_openai", "attempt": 1, **end})


def test_interrupted_attempt_is_not_reissued(tmp_path):
    prepare_interruption(tmp_path)
    assert execute(tmp_path, [])["status"] == "paused"
    assert len(records(tmp_path, "start")) == 1


def test_interrupted_captured_text_is_recovered(tmp_path):
    prepare_interruption(tmp_path, captured="Saved before crash")
    result = execute(tmp_path, [])
    assert result["outcomes"]["synthetic_openai"]["text"] == "Saved before crash"
    assert len(records(tmp_path, "start")) == 1


@pytest.mark.parametrize("action", ["empty", "exhausted", "stop", "pause"])
def test_crash_between_attempt_end_and_final_record(tmp_path, action):
    prepare_interruption(tmp_path, end={"action": action})
    result = execute(tmp_path, [])
    if action in {"empty", "exhausted"}:
        assert result["outcomes"]["synthetic_openai"]["status"] == action
    else:
        assert result["status"] == action
    assert len(records(tmp_path, "start")) == 1


def test_resume_preserves_remaining_delay_and_attempt_number(tmp_path):
    prepare_interruption(tmp_path, end={"action": "retry", "retry_not_before": 120})
    delays = []
    execute(tmp_path, [[], [text("Second attempt"), complete()]], now=lambda: 110, sleep=delays.append)
    assert delays == [10]
    assert [r["attempt"] for r in records(tmp_path, "start")] == [1, 2]


def test_changed_configuration_cannot_replace_existing_outputs(tmp_path):
    execute(tmp_path, [[text("Original"), complete()]])
    spec = manifest(); spec["tasks"][0]["parameters"]["max_tokens"] = 16000
    with pytest.raises(IntegrityError, match="Frozen manifest changed"):
        execute(tmp_path, [], spec)


def test_journal_corruption_prevents_any_more_attempts(tmp_path):
    execute(tmp_path, [[text("Original"), complete()]])
    path = tmp_path / "event-000001.json"
    record = json.loads(path.read_text()); record["payload"]["event"]["text"] = "Replacement"
    path.write_text(json.dumps(record))
    with pytest.raises(IntegrityError, match="hash mismatch"):
        execute(tmp_path, [])


def test_batch_lock_prevents_concurrent_execution(tmp_path):
    with batch_lock(tmp_path):
        with pytest.raises(IntegrityError, match="lock"):
            execute(tmp_path, [])


def test_live_execution_is_unavailable(tmp_path):
    spec = manifest(); spec["mode"] = "formal"
    with pytest.raises(IntegrityError, match="offline"):
        execute(tmp_path, [], spec)
    assert not (tmp_path / "task_manifest.json").exists()


def test_hard_deadline_retains_streamed_text(tmp_path):
    started = time.monotonic()
    result = execute(tmp_path, [[text("Before timeout"), {"type": "delay", "seconds": 20}]], deadline_seconds=1.5)
    assert time.monotonic() - started < 6
    out = result["outcomes"]["synthetic_openai"]
    assert out["text"] == "Before timeout"
    assert out["terminal"]["code"] == "timeout"


def test_all_visible_blocks_and_refusals_are_preserved():
    assert visible_text("anthropic", {"content": [{"type": "text", "text": "One"},
        {"type": "thinking", "thinking": "Private"}, {"type": "text", "text": "Two"}]}) == "OneTwo"
    assert visible_text("gemini", {"candidates": [{"content": {"parts": [
        {"text": "Private", "thought": True}, {"text": "One"}, {"text": "Two"}]}}]}) == "OneTwo"
    assert visible_text("openai", {"choices": [{"message": {"content": None, "refusal": "No"}}]}) == "No"


@pytest.mark.parametrize("provider,key", [("openai", "choices"), ("gemini", "candidates")])
def test_multiple_candidates_are_not_selected_by_quality(provider, key):
    with pytest.raises(IntegrityError):
        visible_text(provider, {key: [{}, {}]})
