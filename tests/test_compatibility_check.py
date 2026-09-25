"""Authorization, durable dispatch and recovery tests; no live model requests."""
import copy
import json
from pathlib import Path
import socket
import time

import pytest

from src.llm.compatibility_check import (
    HTTPFixture, LIVE_ROOT, build_plan, recovery, run_check, status, technical_results, validate_authorization,
)
from src.llm.formal_generation import IntegrityError, digest, read_journal
from tests.test_formal_providers import fixture_events


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("This test must not open a network connection")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)


def fixtures(plan, **kwargs):
    return {t["slot_id"]: (HTTPFixture(chunks=tuple(fixture_events(t["provider"], **kwargs))),) for t in plan["tasks"]}


def error_fixture(code="rate_limit_error", status_code=429, retry_after="5"):
    return HTTPFixture(status_code, (json.dumps({"error": {"type": code, "message": "Synthetic error"}}).encode(),),
                       (("content-type", "application/json"), ("retry-after", retry_after)))


def review(root, plan, action, **extra):
    slot = plan["tasks"][0]["slot_id"]
    return {"journal_head": read_journal(root)[1], "slot_id": slot, "task_sha256": digest(plan["tasks"][0]),
            "action": action, "reviewer": "Synthetic test operator", "reviewed_at": "2026-09-18",
            "evidence_note": "Mock evidence only", "confirmation_source": "Automated test fixture; not a human signature",
            **extra}


def test_unsigned_live_run_stops_before_credentials_or_files(tmp_path, monkeypatch):
    def forbidden():
        pytest.fail("Credentials must not be accessed before authorization")
    monkeypatch.setattr("src.llm.compatibility_check.load_keys", forbidden)
    with pytest.raises(IntegrityError, match="authorization"):
        run_check(tmp_path, build_plan(), mode="live", authorization={"approved": False})
    assert not (tmp_path / "run_manifest.json").exists()


def test_wrong_scope_hash_budget_and_request_limit_cannot_authorize():
    plan = build_plan()
    auth = {"approved": True, "scope": plan["scope"], "plan_sha256": digest(plan),
            "max_total_dispatches": 9, "budget_limit_usd": 3.0, "confirmation_source": "Test only",
            "recorded_by": "Test", "confirmed_at": "2026-09-18"}
    validate_authorization(plan, auth)
    for key, value in [("scope", "Formal batch"), ("plan_sha256", "other"), ("budget_limit_usd", 4), ("max_total_dispatches", 10)]:
        changed = {**auth, key: value}
        with pytest.raises(IntegrityError):
            validate_authorization(plan, changed)


def test_formal_participant_input_cannot_enter_compatibility_runner(tmp_path):
    plan = build_plan()
    plan["tasks"][0]["user_prompt"] = "Sub01 actual participant input"
    with pytest.raises(IntegrityError, match="changed"):
        run_check(tmp_path, plan, fixtures={})


@pytest.mark.parametrize("empty", [False, True])
def test_three_sdks_dispatch_after_durable_reservation_and_resume_without_calls(tmp_path, empty):
    plan = build_plan()
    result = run_check(tmp_path, plan, fixtures=fixtures(plan, empty=empty))
    assert result["status"] == "complete"
    assert len(result["outcomes"]) == 3
    assert {r["state"] for r in result["outcomes"].values()} == ({"empty"} if empty else {"captured"})
    log = read_journal(tmp_path)[0]
    for task in plan["tasks"]:
        rows = [r for r in log if r.get("slot_id") == task["slot_id"]]
        assert rows[0]["kind"] == "attempt_started"
        assert rows[1]["event"]["type"] == "dispatch_requested"
        assert rows[1]["event"]["wire_body_sha256"]
    assert status(tmp_path)["dispatches_reserved"] == 3
    assert run_check(tmp_path, plan, fixtures={}) == result
    assert status(tmp_path)["dispatches_reserved"] == 3


def test_transient_exhaustion_and_longer_backoff_persist(tmp_path):
    plan = build_plan(); fs = fixtures(plan)
    first = plan["tasks"][0]["slot_id"]
    fs[first] = (error_fixture(retry_after="60"),) * 3
    waits = []
    result = run_check(tmp_path, plan, fixtures=fs, now=lambda: 100, sleep=waits.append)
    assert result["outcomes"][first]["state"] == "exhausted"
    assert waits == [60, 60]
    assert status(tmp_path)["attempts_reserved"] == 5
    assert run_check(tmp_path, plan, fixtures={}) == result


def test_permanent_failure_stops_batch_and_cannot_be_retried(tmp_path):
    plan = build_plan(); fs = fixtures(plan)
    fs[plan["tasks"][0]["slot_id"]] = (error_fixture("billing_error"),)
    assert run_check(tmp_path, plan, fixtures=fs)["status"] == "stopped"
    assert status(tmp_path)["dispatches_reserved"] == 1
    with pytest.raises(IntegrityError, match="Stopped"):
        recovery(tmp_path, plan, review(tmp_path, plan, "retry", confirmed_transient=True,
            retrieval_status="checked_no_text", retry_not_before=time.time() + 300))


def test_unknown_remote_completion_pauses_and_requires_retrieval_review(tmp_path):
    plan = build_plan(); fs = fixtures(plan)
    slot = plan["tasks"][0]["slot_id"]
    fs[slot] = (HTTPFixture(chunks=(), stall_seconds=20),)
    result = run_check(tmp_path, plan, fixtures=fs, deadline=1.5)
    assert result["status"] == "paused"
    assert status(tmp_path)["dispatches_reserved"] == 1
    assert run_check(tmp_path, plan, fixtures={}, deadline=1.5)["status"] == "paused"
    with pytest.raises(IntegrityError, match="retrieval review"):
        recovery(tmp_path, plan, review(tmp_path, plan, "retry"))
    recovery(tmp_path, plan, review(tmp_path, plan, "retry", confirmed_transient=True,
        retrieval_status="not_supported_for_registered_request", retry_not_before=time.time() + 30))
    fs = fixtures(plan); fs[slot] = (HTTPFixture(), fs[slot][0])
    result = run_check(tmp_path, plan, fixtures=fs, deadline=1.5, sleep=lambda _: None)
    assert result["status"] == "complete"
    assert status(tmp_path)["attempts_reserved"] == 4


def test_partial_text_survives_worker_deadline_without_regeneration(tmp_path):
    plan = build_plan(); fs = fixtures(plan)
    task = plan["tasks"][0]
    fs[task["slot_id"]] = (HTTPFixture(chunks=tuple(fixture_events(task["provider"], finish=False)), stall_seconds=20),)
    result = run_check(tmp_path, plan, fixtures=fs, deadline=1.5)
    assert result["outcomes"][task["slot_id"]]["text"] == "First. Second."
    assert status(tmp_path)["attempts_reserved"] == 3


def test_completed_empty_cannot_be_reopened_by_recovery(tmp_path):
    plan = build_plan()
    run_check(tmp_path, plan, fixtures=fixtures(plan, empty=True))
    with pytest.raises(IntegrityError, match="Terminal"):
        recovery(tmp_path, plan, review(tmp_path, plan, "retry"))


def test_retrieved_output_is_kept_and_stale_recovery_rejected(tmp_path):
    plan = build_plan(); fs = fixtures(plan)
    fs[plan["tasks"][0]["slot_id"]] = (HTTPFixture(chunks=()),)
    assert run_check(tmp_path, plan, fixtures=fs)["status"] == "paused"
    decision = review(tmp_path, plan, "attach_response", response_attribution_verified=True,
        raw_response={"id": "retrieved-synthetic", "content": [{"type": "text", "text": "Recovered output"}]})
    recovery(tmp_path, plan, decision)
    with pytest.raises(IntegrityError, match="stale"):
        recovery(tmp_path, plan, decision)
    result = run_check(tmp_path, plan, fixtures=fixtures(plan))
    assert result["outcomes"][plan["tasks"][0]["slot_id"]]["text"] == "Recovered output"
    assert status(tmp_path)["attempts_reserved"] == 3


def test_close_no_report_preserves_gap_without_new_request(tmp_path):
    plan = build_plan(); fs = fixtures(plan)
    fs[plan["tasks"][0]["slot_id"]] = (HTTPFixture(chunks=()),)
    run_check(tmp_path, plan, fixtures=fs)
    recovery(tmp_path, plan, review(tmp_path, plan, "close_no_report"))
    result = run_check(tmp_path, plan, fixtures=fixtures(plan))
    assert result["outcomes"][plan["tasks"][0]["slot_id"]]["state"] == "closed_no_report"
    assert status(tmp_path)["dispatches_reserved"] == 3


def test_live_root_cannot_be_populated_by_mock_run():
    with pytest.raises(IntegrityError, match="separate output"):
        run_check(LIVE_ROOT, build_plan(), fixtures={})


def test_cost_reservation_counts_full_output_for_every_attempt():
    plan = build_plan()
    assert plan["estimated_maximum_usd"] == 2.205
    assert plan["estimated_maximum_usd"] < plan["budget_limit_usd"]
    assert len(plan["tasks"]) * plan["max_attempts_per_slot"] == plan["max_total_dispatches"] == 9


@pytest.mark.parametrize("empty", [False, True])
def test_crash_after_capture_before_resolution_does_not_generate_replacement(tmp_path, monkeypatch, empty):
    import src.llm.compatibility_check as module
    original = module.append
    def interrupted(root, record):
        if record["kind"] == "attempt_resolved":
            raise RuntimeError("Synthetic persistence interruption")
        original(root, record)
    plan = build_plan()
    monkeypatch.setattr(module, "append", interrupted)
    with pytest.raises(RuntimeError, match="persistence interruption"):
        run_check(tmp_path, plan, fixtures=fixtures(plan, empty=empty))
    monkeypatch.setattr(module, "append", original)
    result = run_check(tmp_path, plan, fixtures=fixtures(plan))
    assert result["outcomes"][plan["tasks"][0]["slot_id"]]["state"] == ("empty" if empty else "captured")
    assert status(tmp_path)["attempts_reserved"] == 3


def test_nine_request_budget_cannot_be_reset_by_resume(tmp_path):
    plan = build_plan()
    fs = {t["slot_id"]: (error_fixture("api_error", 503),) * 3 for t in plan["tasks"]}
    result = run_check(tmp_path, plan, fixtures=fs, sleep=lambda _: None)
    assert {r["state"] for r in result["outcomes"].values()} == {"exhausted"}
    assert status(tmp_path)["dispatches_reserved"] == 9
    assert run_check(tmp_path, plan, fixtures={}) == result
    assert status(tmp_path)["dispatches_reserved"] == 9


def test_technical_summary_does_not_infer_clinical_quality_or_freeze(tmp_path):
    plan = build_plan()
    run_check(tmp_path, plan, fixtures=fixtures(plan))
    result = technical_results(tmp_path)
    assert len(result["results"]) == 3
    assert all(r["token_limit_reached"] for r in result["results"])
    assert result["configuration_frozen"] is False
    assert result["formal_generation_authorized"] is False


def test_persist_failure_before_dispatch_does_not_acknowledge_worker(tmp_path, monkeypatch):
    import src.llm.compatibility_check as module
    original = module.append
    def fail_reservation(root, record):
        if record["kind"] == "stream_event" and record["event"]["type"] == "dispatch_requested":
            raise OSError("Synthetic disk failure")
        original(root, record)
    plan = build_plan()
    monkeypatch.setattr(module, "append", fail_reservation)
    with pytest.raises(OSError, match="disk failure"):
        run_check(tmp_path, plan, fixtures=fixtures(plan))
    monkeypatch.setattr(module, "append", original)
    assert status(tmp_path)["dispatches_reserved"] == 0
    assert run_check(tmp_path, plan, fixtures={})["status"] == "paused"


def test_cli_without_live_flag_is_blocked(tmp_path, monkeypatch):
    import scripts.run_compatibility_check as cli
    package = tmp_path / "package"; package.mkdir()
    (package / "plan.json").write_text(json.dumps(build_plan()))
    monkeypatch.setattr(cli, "PACKAGE", package)
    monkeypatch.setattr("sys.argv", ["run_compatibility_check.py", "run"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


def test_prepare_cannot_replace_a_started_live_plan(tmp_path, monkeypatch):
    import scripts.run_compatibility_check as cli
    live = tmp_path / "live"; live.mkdir()
    (live / "run_manifest.json").write_text('{}')
    monkeypatch.setattr(cli, "PACKAGE", tmp_path / "package")
    monkeypatch.setattr(cli, "LIVE_ROOT", live)
    monkeypatch.setattr("sys.argv", ["run_compatibility_check.py", "prepare"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert not (tmp_path / "package/plan.json").exists()
