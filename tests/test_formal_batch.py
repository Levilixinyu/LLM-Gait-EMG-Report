"""Formal runner integration and failure checks, entirely offline."""
import copy
from importlib.metadata import version
import json
import socket
import time

import pytest

from src.llm.compatibility_check import HTTPFixture, PACKAGES, status
from src.llm.formal_batch import (
    LIVE_ROOT, Ledger, recover, run, schedule, terminal_slots, validate_authorization,
)
from src.llm.formal_generation import IntegrityError, digest, read_journal
from src.llm.formal_release import BASE, build_candidate, package_terminal_run, read
from tests.test_formal_providers import fixture_events


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network in offline formal tests")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)


def plan():
    proposals = {p["provider"]: p for p in read(BASE / "generation_preflight_v1/provider_candidates.json")["providers"]}
    tasks = []
    for case, provider in schedule(["synthetic_case"]):
        task = {"slot_id": f"{case}_{provider}", "case_id": case, "provider": provider,
                "model": proposals[provider]["model"], "parameters": proposals[provider]["parameters"],
                "system_prompt": "Synthetic interface fixture.", "user_prompt": "Synthetic values 1 and 3."}
        task["input_pair_sha256"] = digest([task["system_prompt"], task["user_prompt"]])
        tasks.append(task)
    return {"scope": "Synthetic formal-runner fixture", "tasks": tasks, "schedule_seed": 20260919,
            "max_attempts_per_slot": 3, "max_total_attempts": 9, "attempt_deadline_seconds": 600,
            "sdk_versions": {p: version(p) for p in PACKAGES}, "budget_limit_usd": 9,
            "reservation_usd_per_attempt": {p: 1 for p in proposals}}


def fixtures(candidate, **kwargs):
    return {t["slot_id"]: (HTTPFixture(chunks=tuple(fixture_events(t["provider"], **kwargs))),) for t in candidate["tasks"]}


def error(code="rate_limit_error", status_code=429):
    return HTTPFixture(status=status_code, chunks=(json.dumps({"error": {"type": code, "message": "Synthetic fixture"}}).encode(),),
                       headers=(("content-type", "application/json"), ("retry-after", "5")))


def review(root, candidate, action, **fields):
    task = candidate["tasks"][0]
    return {"action": action, "slot_id": task["slot_id"], "task_sha256": digest(task),
            "journal_head": read_journal(root)[1], "reviewer": "SYNTHETIC technical fixture",
            "reviewed_at": "2026-09-18", "evidence_note": "Mock data only",
            "confirmation_source": "Software fixture, not human approval", **fields}


def test_balanced_content_independent_schedule():
    from collections import Counter
    cases = [f"case{i:02d}" for i in range(35)]
    order = schedule(cases)
    assert order == schedule(cases[::-1]) and len(order) == 105
    patterns = []
    for offset in range(0, 105, 3):
        block = order[offset:offset + 3]
        assert len({c for c, _ in block}) == 1
        patterns.append(tuple(p for _, p in block))
    assert sorted(Counter(patterns).values()) == [5, 6, 6, 6, 6, 6]
    for position in range(3):
        assert sorted(Counter(p[position] for p in patterns).values()) == [11, 12, 12]


def test_live_not_authorized_before_keys_or_files(tmp_path, monkeypatch):
    monkeypatch.setattr("src.llm.formal_batch.load_keys", lambda: pytest.fail("Premature credential access"))
    with pytest.raises(IntegrityError, match="authorization"):
        run(tmp_path / "live", plan(), mode="live", authorization={})
    assert not (tmp_path / "live").exists()
    with pytest.raises(IntegrityError, match="separate"):
        run(LIVE_ROOT, plan(), fixtures={})


@pytest.mark.parametrize("empty", [False, True])
def test_actual_three_sdk_mock_capture_and_idempotent_resume(tmp_path, empty):
    candidate = plan()
    result = run(tmp_path, candidate, fixtures=fixtures(candidate, empty=empty))
    assert result["status"] == "complete" and result["completed_slots"] == 3
    assert status(tmp_path)["dispatches_reserved"] == 3
    assert run(tmp_path, candidate, fixtures={}) == result
    slots = terminal_slots(tmp_path, candidate, allow_mock=True)
    assert all((s["report_text"] is None) == empty for s in slots)
    if not empty:
        assert all(s["truncation"] for s in slots)
    with pytest.raises(IntegrityError, match="not a formal"):
        terminal_slots(tmp_path, candidate)


def test_permanent_failure_stops_and_only_can_close_or_attach(tmp_path):
    candidate = plan(); fs = fixtures(candidate)
    fs[candidate["tasks"][0]["slot_id"]] = (error("billing_error"),)
    assert run(tmp_path, candidate, fixtures=fs)["status"] == "stopped"
    assert status(tmp_path)["dispatches_reserved"] == 1
    with pytest.raises(IntegrityError, match="Stopped"):
        recover(tmp_path, candidate, review(tmp_path, candidate, "retry"))
    recover(tmp_path, candidate, review(tmp_path, candidate, "close_no_report"))
    assert run(tmp_path, candidate, fixtures=fixtures(candidate))["status"] == "complete"
    assert status(tmp_path)["dispatches_reserved"] == 3
    assert terminal_slots(tmp_path, candidate, allow_mock=True)[0]["terminal_status"] == "closed_no_report"


def test_three_attempt_limit_and_backoff_survive_resume(tmp_path):
    candidate = plan(); fs = fixtures(candidate)
    fs[candidate["tasks"][0]["slot_id"]] = (error("api_error", 503),) * 3
    waits = []
    result = run(tmp_path, candidate, fixtures=fs, now=lambda: 100, sleep=waits.append)
    assert waits == [5, 30]
    assert result["status"] == "complete"
    assert status(tmp_path)["attempts_reserved"] == 5
    assert terminal_slots(tmp_path, candidate, allow_mock=True)[0]["terminal_status"] == "technical_failure"
    assert run(tmp_path, candidate, fixtures={}) == result


def test_partial_text_retained_under_worker_deadline(tmp_path):
    candidate = plan(); fs = fixtures(candidate); first = candidate["tasks"][0]
    fs[first["slot_id"]] = (HTTPFixture(chunks=tuple(fixture_events(first["provider"], finish=False)), stall_seconds=20),)
    assert run(tmp_path, candidate, fixtures=fs, deadline=2)["status"] == "complete"
    assert status(tmp_path)["attempts_reserved"] == 3
    row = terminal_slots(tmp_path, candidate, allow_mock=True)[0]
    assert row["report_text"] == "First. Second."
    assert row["normal_stream_completion"] is False


def test_uncertain_timeout_requires_retrieval_review(tmp_path):
    candidate = plan(); fs = fixtures(candidate)
    fs[candidate["tasks"][0]["slot_id"]] = (HTTPFixture(stall_seconds=20),)
    assert run(tmp_path, candidate, fixtures=fs, deadline=2)["status"] == "paused"
    with pytest.raises(IntegrityError, match="retrieval"):
        recover(tmp_path, candidate, review(tmp_path, candidate, "retry"))
    recover(tmp_path, candidate, review(tmp_path, candidate, "retry", confirmed_transient=True,
            retrieval_status="checked_no_text", retry_not_before=time.time() + 30))
    fs = fixtures(candidate)
    first = candidate["tasks"][0]["slot_id"]
    fs[first] = (HTTPFixture(), fs[first][0])
    assert run(tmp_path, candidate, fixtures=fs, deadline=2, sleep=lambda _: None)["status"] == "complete"
    assert status(tmp_path)["attempts_reserved"] == 4


@pytest.mark.parametrize("empty", [False, True])
def test_crash_after_capture_never_replaces_response(tmp_path, monkeypatch, empty):
    candidate = plan()
    original = Ledger.append
    def crash(self, record):
        if record["kind"] == "attempt_resolved":
            raise OSError("Synthetic disk interruption")
        original(self, record)
    monkeypatch.setattr(Ledger, "append", crash)
    with pytest.raises(OSError):
        run(tmp_path, candidate, fixtures=fixtures(candidate, empty=empty))
    monkeypatch.setattr(Ledger, "append", original)
    assert run(tmp_path, candidate, fixtures=fixtures(candidate))["status"] == "complete"
    assert status(tmp_path)["attempts_reserved"] == 3
    slots = terminal_slots(tmp_path, candidate, allow_mock=True)
    assert (slots[0]["report_text"] is None) == empty


def test_persistence_failure_cannot_acknowledge_dispatch(tmp_path, monkeypatch):
    candidate = plan(); original = Ledger.append
    def crash(self, record):
        if record["kind"] == "stream_event" and record["event"]["type"] == "dispatch_requested":
            raise OSError("Synthetic disk interruption")
        original(self, record)
    monkeypatch.setattr(Ledger, "append", crash)
    with pytest.raises(OSError):
        run(tmp_path, candidate, fixtures=fixtures(candidate))
    monkeypatch.setattr(Ledger, "append", original)
    assert status(tmp_path)["dispatches_reserved"] == 0
    assert run(tmp_path, candidate, fixtures={})["status"] == "paused"


def test_budget_and_changed_input_fail_closed(tmp_path):
    candidate = plan(); candidate["budget_limit_usd"] = 1
    assert run(tmp_path, candidate, fixtures=fixtures(candidate))["status"] == "budget_paused"
    assert status(tmp_path)["attempts_reserved"] == 1
    with pytest.raises(IntegrityError, match="attempt evidence"):
        terminal_slots(tmp_path, candidate, allow_mock=True)
    changed = copy.deepcopy(candidate); changed["tasks"][0]["user_prompt"] += " changed"
    with pytest.raises(IntegrityError, match="Input text"):
        run(tmp_path, changed, fixtures={})


def test_full_105_ledger_to_real_review_assets(tmp_path, monkeypatch):
    candidate = build_candidate()
    missing = candidate["tasks"][0]["slot_id"]
    def synthetic_stream(task, api_key, fixture, deadline, persist):
        # This stub tests orchestration at full roster size. Separate tests above
        # exercise the actual three SDKs and durable dispatch handshake.
        assert api_key == "fake-offline-key" and type(fixture) is HTTPFixture
        persist({"type": "dispatch_requested", "task_sha256": digest(task), "wire_body_sha256": "fixture"})
        if task["slot_id"] != missing:
            persist({"type": "text", "text": "SYNTHETIC SOFTWARE FIXTURE. Not a clinical model report."})
        persist({"type": "completed", "metadata": {"finish_reason": "stop", "response_model": "synthetic"}})
    monkeypatch.setattr("src.llm.formal_batch._process_events", synthetic_stream)
    output = tmp_path / "run"
    assert run(output, candidate, fixtures={t["slot_id"]: (HTTPFixture(),) for t in candidate["tasks"]})["completed_slots"] == 105
    packet = tmp_path / "packet"
    counts = package_terminal_run(output, candidate, packet, allow_mock=True)
    assert counts == {"report_slots": 105, "available_reports": 104, "coverage_rows_per_rater": 552}
    for rater in ("rater1", "rater2"):
        material = packet / "raters" / rater / "materials"
        assert len(list(material.glob("*/curves_emg.png"))) == 35
        assert len(list(material.glob("*/curves_kinematics.png"))) == 35
        assert len(list(material.glob("*/reference_card.md"))) == 35
        assert len(list(material.glob("*/model_user_prompt.txt"))) == 35
        assert not list((packet / "raters" / rater).rglob("*key*"))
    with pytest.raises(FileExistsError):
        package_terminal_run(output, candidate, packet, allow_mock=True)


def test_authorization_template_is_not_approval():
    with pytest.raises(IntegrityError, match="authorization"):
        validate_authorization(plan(), {"approved": False})
