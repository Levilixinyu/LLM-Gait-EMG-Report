"""Offline protection of the user's first-ten-stroke authorization boundary."""
import copy
import json
import socket
import pytest
from src.llm import formal_stages as runner
from src.llm.formal_generation import digest, IntegrityError, read_journal


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network permitted")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)


def inputs(number=1):
    plan = json.loads(runner.FULL_PLAN.read_text())
    stage = runner.build_stage(plan, number)
    release = json.loads((runner.ROOT / "docs/formal_study/formal_execution_v2_candidate/release_review/authorization_READY_FOR_APPROVAL.json").read_text())
    checks = release["release_checks"]
    # Mock authorization only; the actual stage uses its saved test result.
    checks["stage_boundary_checks_passed"] = copy.deepcopy(checks["formal_runner_offline_checks_passed"])
    auth = {"approved": True, "stage_sha256": digest(stage), "full_plan_sha256": digest(plan),
            "slot_ids": stage["slot_ids"], "max_total_attempts": stage["max_total_attempts"],
            "budget_limit_usd": stage["budget_limit_usd"], "full_batch_authorized": False,
            "confirmation_source": "Software test fixture only", "confirmed_at": "Synthetic", "recorded_by": "Offline test",
            "release_checks": checks}
    fixtures = {s: (runner.HTTPFixture(),) * 3 for s in stage["slot_ids"]}
    return plan, stage, auth, fixtures


def emit(task, persist, *, empty=False, partial=False):
    persist({"type": "dispatch_requested", "task_sha256": digest(task)})
    if not empty:
        persist({"type": "text", "text": "Mock formal response."})
    if partial:
        persist({"type": "error", "code": "timeout", "remote_completion_possible": True})
    else:
        persist({"type": "completed", "metadata": {"finish_reason": "refusal" if empty else "MAX_TOKENS", "response_model": task["model"], "usage": {"output_tokens": 10}}})


@pytest.mark.parametrize("kind", ["truncated", "empty", "partial"])
def test_exact_thirty_slots_and_idempotent_resume(tmp_path, monkeypatch, kind):
    plan, stage, auth, fixtures = inputs()
    calls = []
    def stream(task, key, fixture, deadline, persist):
        calls.append(task["slot_id"])
        emit(task, persist, empty=kind == "empty", partial=kind == "partial")
    monkeypatch.setattr(runner, "_process_events", stream)
    result = runner.run_stage(tmp_path, plan, stage, auth, mode="mock", fixtures=fixtures)
    assert result["status"] == "stage_complete" and result["completed_slots"] == 30
    assert calls == stage["slot_ids"] and len(set(calls)) == 30
    assert runner.run_stage(tmp_path, plan, stage, auth, mode="mock", fixtures={}) == result
    assert len(calls) == 30
    rows, _ = read_journal(tmp_path)
    assert {r["slot_id"] for r in rows} == set(stage["slot_ids"])
    assert all(t["group"] == "stroke" for t in plan["tasks"] if t["slot_id"] in calls)


def test_unsigned_or_changed_stage_cannot_load_keys(tmp_path, monkeypatch):
    plan, stage, auth, fixtures = inputs()
    monkeypatch.setattr(runner, "load_keys", lambda: pytest.fail("Premature credentials"))
    for bad in ({}, {**auth, "slot_ids": []}, {**auth, "full_batch_authorized": True}):
        with pytest.raises(IntegrityError, match="authorization"):
            runner.run_stage(tmp_path, plan, stage, bad)
    assert not (tmp_path / "run_manifest.json").exists()


def test_later_stage_cannot_use_stage_one_authorization(tmp_path):
    plan, _, auth, _ = inputs()
    later = runner.build_stage(plan, 2)
    with pytest.raises(IntegrityError, match="authorization"):
        runner.run_stage(tmp_path, plan, later, auth, mode="mock", fixtures={})
    _, later, auth2, fixtures2 = inputs(2)
    with pytest.raises(IntegrityError, match="Previous stage"):
        runner.run_stage(tmp_path, plan, later, auth2, mode="mock", fixtures=fixtures2)


def test_no_text_uncertain_timeout_pauses_without_retry(tmp_path, monkeypatch):
    plan, stage, auth, fixtures = inputs()
    calls = []
    def stream(task, key, fixture, deadline, persist):
        calls.append(task["slot_id"])
        persist({"type": "dispatch_requested", "task_sha256": digest(task)})
        persist({"type": "error", "code": "timeout", "remote_completion_possible": True})
    monkeypatch.setattr(runner, "_process_events", stream)
    for _ in range(2):
        assert runner.run_stage(tmp_path, plan, stage, auth, mode="mock", fixtures=fixtures)["status"] == "paused"
    assert len(calls) == 1


def test_eligible_transient_retry_is_bounded_and_counts_budget(tmp_path, monkeypatch):
    plan, stage, auth, fixtures = inputs()
    calls = []
    def stream(task, key, fixture, deadline, persist):
        calls.append(task["slot_id"])
        persist({"type": "dispatch_requested", "task_sha256": digest(task)})
        persist({"type": "error", "code": "transient_server", "http_status": 503, "remote_completion_possible": False})
    monkeypatch.setattr(runner, "_process_events", stream)
    waits = []
    result = runner.run_stage(tmp_path, plan, stage, auth, mode="mock", fixtures=fixtures, now=lambda: 100, sleep=waits.append)
    assert result["status"] == "stage_complete" and len(calls) == 90
    assert all(calls.count(s) == 3 for s in stage["slot_ids"])


def test_all_stages_share_ledger_and_remain_importable(tmp_path, monkeypatch):
    from src.llm.formal_batch import terminal_slots
    calls = []
    def stream(task, key, fixture, deadline, persist):
        calls.append(task['slot_id'])
        emit(task, persist)
    monkeypatch.setattr(runner, '_process_events', stream)
    for number in (1, 2, 3):
        plan, stage, auth, fixtures = inputs(number)
        assert runner.run_stage(tmp_path, plan, stage, auth, mode='mock', fixtures=fixtures)['status'] == 'stage_complete'
    assert len(calls) == len(set(calls)) == 105
    assert len(terminal_slots(tmp_path, plan, allow_mock=True)) == 105
