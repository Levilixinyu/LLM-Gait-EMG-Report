"""Focused verification of the user's one-request-per-provider amendment."""
import json
import pytest
from scripts import run_full_length_once as runner
from src.llm.compatibility_check import HTTPFixture
from src.llm.formal_generation import digest, IntegrityError


@pytest.fixture(autouse=True)
def current_offline_parent(tmp_path, monkeypatch):
    """Exercise execution behavior without rewriting the historical live plan."""
    parent = tmp_path / "synthetic_parent.json"
    parent.write_text(json.dumps(runner.original_plan()), encoding="utf-8")
    monkeypatch.setattr(runner, "PARENT", parent)


def inputs():
    plan = runner.build_plan()
    auth = {"approved": True, "scope": plan["scope"], "plan_sha256": digest(plan),
            "max_total_attempts": 3, "budget_limit_usd": 4.0,
            "confirmation_source": "SYNTHETIC fixture", "confirmed_at": "2026-09-18", "recorded_by": "Software test"}
    return plan, auth, {t["slot_id"]: HTTPFixture() for t in plan["tasks"]}


@pytest.mark.parametrize("failure", [False, True])
def test_only_one_call_per_provider_even_after_failure_and_resume(tmp_path, monkeypatch, failure):
    calls = []
    def stream(task, key, fixture, deadline, persist):
        calls.append(task["provider"])
        persist({"type": "dispatch_requested", "task_sha256": digest(task)})
        if failure:
            persist({"type": "error", "code": "timeout", "remote_completion_possible": True})
        else:
            persist({"type": "text", "text": "Synthetic " * 1000})
            persist({"type": "completed", "metadata": {"usage": {"output_tokens": 1200},
                     "response_model": task["model"], "finish_reason": "stop"}})
    monkeypatch.setattr(runner, "_process_events", stream)
    plan, auth, fixtures = inputs()
    result = runner.execute(plan, auth, root=tmp_path, fixtures=fixtures)
    assert len(calls) == len(set(calls)) == 3
    assert result["all_three_support_length"] is (not failure)
    assert result["automatic_retries"] == 0
    assert runner.execute(plan, auth, root=tmp_path, fixtures={}) == result
    assert len(calls) == 3


def test_unsigned_run_never_loads_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "load_keys", lambda: pytest.fail("Premature credential access"))
    with pytest.raises(IntegrityError, match="authorization"):
        runner.execute(runner.build_plan(), {}, root=tmp_path)


def test_changed_parent_identity_rejected_before_credentials(tmp_path, monkeypatch):
    plan, auth, _ = inputs()
    parent = json.loads(runner.PARENT.read_text())
    parent["source_sha256"]["src/llm/formal_release.py"] = "0" * 64
    runner.PARENT.write_text(json.dumps(parent), encoding="utf-8")
    monkeypatch.setattr(runner, "load_keys", lambda: pytest.fail("Premature credential access"))
    monkeypatch.setattr(runner, "_process_events", lambda *a, **k: pytest.fail("Premature dispatch"))
    with pytest.raises(IntegrityError, match="source identity changed"):
        runner.execute(plan, auth, root=tmp_path / "rejected")
    assert not (tmp_path / "rejected").exists()
