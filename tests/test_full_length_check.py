"""Separate paid-check authorization, input scope and immutable preparation."""
import copy
import json

import pytest

from src.llm.formal_batch import run, validate_authorization, validate_plan
from src.llm.formal_generation import IntegrityError, digest
from src.llm.full_length_check import LIVE_ROOT, build_plan, synthetic_input


def test_check_is_long_and_wholly_synthetic_without_participant_input():
    system, user = synthetic_input()
    assert len(system.encode()) + len(user.encode()) >= 14000
    assert "SYNTHETIC" in user and "fictional" in system
    assert "Sub01" not in user and "stroke_Sub" not in user and "control_Sub" not in user
    plan = build_plan()
    assert len(plan["tasks"]) == 3
    assert len({(t["system_prompt"], t["user_prompt"]) for t in plan["tasks"]}) == 1
    assert plan["minimum_words_for_length_evidence"] == 900
    assert plan["max_total_attempts"] == 9 and plan["budget_limit_usd"] == 4
    assert 3 * sum(plan["reservation_usd_per_attempt"].values()) == pytest.approx(3.024)
    validate_plan(plan, live=True)


def test_formal_case_injected_into_check_rejected():
    plan = build_plan()
    plan["tasks"][0]["user_prompt"] = "A real participant report input"
    plan["tasks"][0]["input_pair_sha256"] = digest([plan["tasks"][0]["system_prompt"], plan["tasks"][0]["user_prompt"]])
    with pytest.raises(IntegrityError, match="changed"):
        validate_plan(plan, live=True)


def test_original_short_check_authorization_cannot_authorize_this_check():
    plan = build_plan()
    with pytest.raises(IntegrityError, match="authorization"):
        validate_authorization(plan, {"approved": True, "budget_limit_usd": 3.0})


def test_unsigned_check_does_not_load_keys_or_create_run(tmp_path, monkeypatch):
    monkeypatch.setattr("src.llm.formal_batch.load_keys", lambda: pytest.fail("Credentials accessed without approval"))
    with pytest.raises(IntegrityError, match="authorization"):
        run(tmp_path / "live", build_plan(), mode="live")
    assert not (tmp_path / "live").exists()
    with pytest.raises(IntegrityError, match="separate"):
        run(LIVE_ROOT, build_plan(), fixtures={})


def test_long_input_passes_actual_three_sdks_with_mocked_http(tmp_path):
    from src.llm.compatibility_check import HTTPFixture
    from tests.test_formal_providers import fixture_events
    plan = build_plan()
    fixtures = {t["slot_id"]: (HTTPFixture(chunks=tuple(fixture_events(t["provider"]))),)
                for t in plan["tasks"]}
    assert run(tmp_path, plan, fixtures=fixtures)["completed_slots"] == 3


def test_cli_cannot_prepare_over_an_existing_plan(tmp_path, monkeypatch):
    import scripts.run_full_length_check as cli
    folder = tmp_path / "prepared"; folder.mkdir()
    (folder / "plan.json").write_text("existing")
    monkeypatch.setattr(cli, "PACKAGE", folder)
    monkeypatch.setattr(cli, "LIVE_ROOT", tmp_path / "live")
    monkeypatch.setattr("sys.argv", ["run_full_length_check.py", "prepare"])
    with pytest.raises(SystemExit):
        cli.main()
    assert (folder / "plan.json").read_text() == "existing"
