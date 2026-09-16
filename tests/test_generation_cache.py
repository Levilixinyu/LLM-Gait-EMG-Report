"""Acceptance tests for the generation task-identity / validity / placement system
(audit round 2, R1/R2) -- every case here is a failure mode the audit demonstrated
slipping through the first v2 cache (or a mixing risk of the old entry points).
All local; a fake result object stands in for paid API calls."""
from __future__ import annotations

import json
from dataclasses import replace

from src.llm.generation_cache import (
    TaskSpec,
    artifact_name,
    existing_record_valid,
    place_record,
    record_from_result,
    task_hash,
)


class FakeResult:
    def __init__(self, text="A plausible report.", stop_reason="end_turn", truncated=False):
        self.text = text
        self.stop_reason = stop_reason
        self.truncated = truncated
        self.response_model = "claude-opus-5-20260101"
        self.request_id = "req_fake123"
        self.usage = {"input_tokens": 100, "output_tokens": 500}


def make_spec(**overrides) -> TaskSpec:
    base = TaskSpec(
        subject_id="Sub01",
        side="P",
        provider="anthropic",
        model="claude-opus-5",
        prompt_version="v2",
        system_prompt="SYSTEM",
        user_prompt="USER Sub01 data",
        generation_params={"max_tokens": 8000},
        reference_id="main_cohort_excel/all-controls",
        data_manifest={"data.xlsx": "abc123"},
        code_manifest={"pipeline.py": "def456"},
    )
    return replace(base, **overrides)


def write_valid(tmp_path, spec):
    path = tmp_path / artifact_name(spec)
    place_record(path, record_from_result(spec, FakeResult()))
    return path


# ---- task-hash sensitivity: every identity dimension must change the hash ----

def test_hash_changes_on_user_prompt():
    assert task_hash(make_spec()) != task_hash(make_spec(user_prompt="USER different data"))


def test_hash_changes_on_reference():
    assert task_hash(make_spec()) != task_hash(make_spec(reference_id="main_cohort_excel/loo:Sub01"))


def test_hash_changes_on_generation_params():
    assert task_hash(make_spec()) != task_hash(make_spec(generation_params={"max_tokens": 4000}))


def test_hash_changes_on_code_manifest():
    assert task_hash(make_spec()) != task_hash(make_spec(code_manifest={"pipeline.py": "CHANGED"}))


def test_hash_changes_on_data_manifest():
    assert task_hash(make_spec()) != task_hash(make_spec(data_manifest={"data.xlsx": "CHANGED"}))


# ---- validity: audit-demonstrated slip-throughs must now be rejected ----

def test_valid_record_is_reusable(tmp_path):
    spec = make_spec()
    path = write_valid(tmp_path, spec)
    ok, reason = existing_record_valid(path, spec)
    assert ok, reason


def test_blank_text_rejected(tmp_path):
    spec = make_spec()
    path = tmp_path / artifact_name(spec)
    place_record(path, record_from_result(spec, FakeResult(text="   \n  ")))
    ok, reason = existing_record_valid(path, spec)
    assert not ok and "blank" in reason


def test_missing_stop_reason_rejected(tmp_path):
    spec = make_spec()
    path = tmp_path / artifact_name(spec)
    place_record(path, record_from_result(spec, FakeResult(stop_reason=None)))
    ok, reason = existing_record_valid(path, spec)
    assert not ok


def test_non_success_stop_reason_rejected(tmp_path):
    spec = make_spec()
    path = tmp_path / artifact_name(spec)
    place_record(path, record_from_result(spec, FakeResult(stop_reason="max_tokens", truncated=True)))
    ok, _ = existing_record_valid(path, spec)
    assert not ok


def test_subject_mismatch_rejected(tmp_path):
    # record written for Sub01 must not satisfy a Sub02 task even if renamed
    spec01, spec02 = make_spec(), make_spec(subject_id="Sub02", user_prompt="USER Sub02 data")
    path01 = write_valid(tmp_path, spec01)
    masquerade = tmp_path / artifact_name(spec02)
    masquerade.write_text(path01.read_text())
    ok, _ = existing_record_valid(masquerade, spec02)
    assert not ok


def test_config_change_invalidates_and_supersede_preserves_old(tmp_path):
    spec_old = make_spec()
    path = write_valid(tmp_path, spec_old)
    spec_new = make_spec(code_manifest={"pipeline.py": "NEWCODE"})
    ok, reason = existing_record_valid(path, spec_new)
    assert not ok and "hash" in reason
    superseded = place_record(path, record_from_result(spec_new, FakeResult(text="new report")))
    assert superseded is not None and superseded.exists()
    old = json.loads(superseded.read_text())
    new = json.loads(path.read_text())
    assert old["task_hash"] == task_hash(spec_old)
    assert new["task_hash"] == task_hash(spec_new)


def test_unparseable_rejected(tmp_path):
    spec = make_spec()
    path = tmp_path / artifact_name(spec)
    path.write_text("{corrupt json")
    ok, reason = existing_record_valid(path, spec)
    assert not ok and reason == "unparseable"


# ---- full record carries prompts + provenance (R4/R2 archival requirements) ----

def test_record_embeds_prompts_and_response_metadata():
    record = record_from_result(make_spec(), FakeResult())
    assert record["system_prompt"] == "SYSTEM"
    assert record["user_prompt"] == "USER Sub01 data"
    assert record["response_model"] == "claude-opus-5-20260101"
    assert record["request_id"] == "req_fake123"
    assert record["usage"]["output_tokens"] == 500
    json.dumps(record)  # strict-JSON serializable
