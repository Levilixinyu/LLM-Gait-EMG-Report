"""T1 acceptance (audit round 3): rating-packet packaging must select exactly the
current successful reports -- superseded archives, truncated/blank records,
duplicates, missing providers and wrong versions must be excluded or fail loudly.
Includes the end-to-end generation->archival->packaging flow with a fake provider
(no API calls), which is the exact path the audit measured leaking (1 current +
1 superseded truncated report packaged as 2 items)."""
from __future__ import annotations

import json

import pytest

from src.eval.blinding import PacketSelectionError, create_rating_packets
from src.llm.generation_cache import TaskSpec, artifact_name, place_record, record_from_result


# per-provider REAL success codes -- fixtures must not blanket-use "end_turn" for
# every provider, or the per-provider stop-reason validation is never exercised
# (audit round 4, T1 item 1)
SUCCESS_CODE = {"anthropic": "end_turn", "openai": "stop", "gemini": "STOP"}
MODEL_FOR = {"anthropic": "claude-opus-5", "openai": "gpt-6-astra",
             "gemini": "gemini-3.1-pro-preview"}
PROVIDERS3 = {"anthropic", "openai", "gemini"}


class FakeResult:
    def __init__(self, text="Report body.", stop_reason="end_turn", truncated=False):
        self.text = text
        self.stop_reason = stop_reason
        self.truncated = truncated
        self.response_model = "fake-model-v1"
        self.request_id = "req_1"
        self.response_id = "msg_1"
        self.usage = {"input_tokens": 1, "output_tokens": 2}


def spec_for(subject, provider="anthropic", model=None, version="v2", user="U"):
    return TaskSpec(
        subject_id=subject, side="P", provider=provider,
        model=model or MODEL_FOR[provider],
        prompt_version=version, system_prompt="S", user_prompt=user,
        generation_params={}, reference_id="ref", data_manifest={}, code_manifest={},
    )


def write_report(dir_, subject, provider="anthropic", model=None,
                 version="v2", user="U", **result_kw):
    spec = spec_for(subject, provider, model, version, user)
    result_kw.setdefault("stop_reason", SUCCESS_CODE[provider])
    path = dir_ / artifact_name(spec)
    return place_record(path, record_from_result(spec, FakeResult(**result_kw))), path


def make_full_subject(dir_, subject, user="U"):
    for prov in sorted(PROVIDERS3):
        write_report(dir_, subject, prov, user=user)


def test_superseded_archives_are_excluded(tmp_path):
    """The audit's measured leak: current + superseded-truncated => 2 packet items."""
    reports = tmp_path / "reports"
    reports.mkdir()
    make_full_subject(reports, "Sub01")
    # supersede the anthropic report once: old (truncated) goes to archive, new is current
    spec = spec_for("Sub01")
    path = reports / artifact_name(spec)
    place_record(path, record_from_result(spec, FakeResult(text="OLD", stop_reason="max_tokens", truncated=True)),
                 )  # becomes the archived one after next write
    place_record(path, record_from_result(spec, FakeResult(text="NEW current")))
    assert any(".superseded-" in f.name for f in reports.iterdir())

    batch = create_rating_packets(str(reports), str(tmp_path / "out"),
                                  prompt_version="v2", expected_providers=PROVIDERS3)
    packet = json.loads((batch / "packets" / "Sub01.json").read_text())
    assert len(packet) == 3  # exactly one per provider, not 4
    texts = [p["report_text"] for p in packet]
    assert not any("OLD" in t for t in texts)


def test_truncated_current_report_fails_loudly(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01", text="cut off mid-", stop_reason="max_tokens", truncated=True)
    with pytest.raises(PacketSelectionError, match="truncated"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2")


def test_duplicate_subject_provider_fails(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01")
    # same subject+provider under a different model id => duplicate rating item risk
    write_report(reports, "Sub01", model="claude-opus-5.1")
    with pytest.raises(PacketSelectionError, match="duplicate"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2")


# ---- round-4 T1 closure cases ----

def test_content_filter_finish_rejected(tmp_path):
    """T1 item 1: a non-success finish (OpenAI content_filter) with text present and
    truncated=False must not enter packets."""
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01", "openai", stop_reason="content_filter", truncated=False)
    with pytest.raises(PacketSelectionError, match="not a success value"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2")


def test_unknown_provider_rejected(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    spec = TaskSpec(subject_id="Sub01", side="P", provider="mystery", model="m1",
                    prompt_version="v2", system_prompt="S", user_prompt="U",
                    generation_params={}, reference_id="r", data_manifest={}, code_manifest={})
    place_record(tmp_path / "reports" / artifact_name(spec),
                 record_from_result(spec, FakeResult(stop_reason="done")))
    with pytest.raises(PacketSelectionError, match="unknown provider"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2")


def test_corrupt_archives_do_not_break_anonymization(tmp_path):
    """T1 item 2: corrupt / non-object superseded archives in the directory must not
    crash packaging of the valid current set."""
    reports = tmp_path / "reports"
    reports.mkdir()
    make_full_subject(reports, "Sub01")
    (reports / "junk.superseded-20260916T000000Z.json").write_text("{corrupt")
    (reports / "junk2.superseded-20260916T000001Z.json").write_text("[]")
    (reports / "junk3.superseded-20260916T000002Z.json").write_text("null")
    batch = create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2",
                                  expected_providers=PROVIDERS3)
    assert len(json.loads((batch / "packets" / "Sub01.json").read_text())) == 3


def test_same_version_different_experiment_input_caught(tmp_path):
    """T1 item 3: three v2 records, but one generated from a DIFFERENT user prompt
    (another experiment run) -- the frozen task manifest must reject the mix."""
    from src.llm.generation_cache import task_hash
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01", "anthropic", user="EXPERIMENT_A")
    write_report(reports, "Sub01", "openai", user="EXPERIMENT_A")
    write_report(reports, "Sub01", "gemini", user="EXPERIMENT_B")  # stray input
    expected = {
        ("Sub01", prov): task_hash(spec_for("Sub01", prov, user="EXPERIMENT_A"))
        for prov in PROVIDERS3
    }
    with pytest.raises(PacketSelectionError, match="task_hash mismatch"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2",
                              expected_providers=PROVIDERS3, expected_tasks=expected)
    # and the manifest also guards the subject set
    expected_extra = dict(expected)
    for prov in PROVIDERS3:
        expected_extra[("Sub99", prov)] = "whatever"
    reports_ok = tmp_path / "reports_ok"
    reports_ok.mkdir()
    make_full_subject(reports_ok, "Sub01", user="EXPERIMENT_A")
    with pytest.raises(PacketSelectionError, match="subject set mismatch"):
        create_rating_packets(str(reports_ok), str(tmp_path / "out2"), prompt_version="v2",
                              expected_providers=PROVIDERS3, expected_tasks=expected_extra)


def test_batches_are_self_contained_and_history_is_preserved(tmp_path):
    """T1 item 4 + F2: re-packaging into the same out dir yields a NEW self-contained
    batch (packets + its own answer key + rubric + packaging manifest); the earlier
    batch -- including its anonymous-ID answer key needed to trace old scores -- is
    left completely untouched."""
    reports_a = tmp_path / "ra"
    reports_a.mkdir()
    make_full_subject(reports_a, "Sub01")
    out = tmp_path / "out"
    batch1 = create_rating_packets(str(reports_a), str(out), prompt_version="v2",
                                   expected_providers=PROVIDERS3)
    key1_before = (batch1 / "answer_key_DO_NOT_SHARE.csv").read_text()
    assert (batch1 / "packets" / "Sub01.json").exists()
    assert (batch1 / "rubric.json").exists()
    assert (batch1 / "packaging_manifest.json").exists()
    # the answer key must sit at batch root, never inside the rater-facing packets/
    assert not (batch1 / "packets" / "answer_key_DO_NOT_SHARE.csv").exists()

    reports_b = tmp_path / "rb"
    reports_b.mkdir()
    make_full_subject(reports_b, "Sub02")
    batch2 = create_rating_packets(str(reports_b), str(out), prompt_version="v2",
                                   expected_providers=PROVIDERS3)
    assert batch2 != batch1
    # new batch: only its own subjects, own key
    assert {f.name for f in (batch2 / "packets").iterdir()} == {"Sub02.json"}
    key2 = (batch2 / "answer_key_DO_NOT_SHARE.csv").read_text()
    assert "Sub02" in key2 and "Sub01" not in key2
    # old batch untouched byte-for-byte, key still traceable
    assert (batch1 / "packets" / "Sub01.json").exists()
    assert (batch1 / "answer_key_DO_NOT_SHARE.csv").read_text() == key1_before
    assert "Sub01" in key1_before


def test_missing_provider_fails_when_expected(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01", "anthropic", "claude-opus-5")
    write_report(reports, "Sub01", "openai", "gpt-6-astra")
    with pytest.raises(PacketSelectionError, match="providers"):
        create_rating_packets(str(reports), str(tmp_path / "out"),
                              prompt_version="v2", expected_providers=PROVIDERS3)


def test_wrong_prompt_version_fails(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01", version="v1")
    with pytest.raises(PacketSelectionError, match="prompt_version"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2")


def test_blank_text_fails(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    write_report(reports, "Sub01", text="   ")
    with pytest.raises(PacketSelectionError, match="blank"):
        create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2")


def test_same_second_supersede_keeps_all_versions(tmp_path):
    """T3: three writes within one (frozen) second must preserve both archives."""
    spec = spec_for("Sub01")
    path = tmp_path / artifact_name(spec)
    place_record(path, record_from_result(spec, FakeResult(text="v_first")))
    s1 = place_record(path, record_from_result(spec, FakeResult(text="v_second")), timestamp="20260916T120000Z")
    s2 = place_record(path, record_from_result(spec, FakeResult(text="v_third")), timestamp="20260916T120000Z")
    assert s1 is not None and s2 is not None and s1 != s2
    texts = {json.loads(p.read_text())["report_text"] for p in [s1, s2, path]}
    assert texts == {"v_first", "v_second", "v_third"}


def test_non_object_json_rejected_not_crash(tmp_path):
    """T4: list/null/number content must yield invalid, not AttributeError."""
    from src.llm.generation_cache import existing_record_valid
    spec = spec_for("Sub01")
    path = tmp_path / artifact_name(spec)
    for content in ["[]", "null", "5", '"text"', '{"report_text": 123}']:
        path.write_text(content)
        ok, reason = existing_record_valid(path, spec)
        assert not ok, content


class FakeProvider:
    """Stands in for a real provider object in generate_batch: same interface
    (.name/.model/.max_tokens/.generate), per-provider real success codes."""

    def __init__(self, name):
        self.name = name
        self.model = MODEL_FOR[name]
        self.max_tokens = 8000

    def generate(self, system, user_prompt):
        return FakeResult(text=f"Report by {self.name} for input {user_prompt[:20]}",
                          stop_reason=SUCCESS_CODE[self.name])


def test_real_entry_generation_then_packaging(tmp_path):
    """F1 acceptance (audit round 5): drive the REAL shared generation entry
    (generation_runner.generate_batch, the loop both scripts' main() call) with fake
    providers, producing the full directory INCLUDING the task manifest -- then
    package straight from it. The first integration failed exactly here: the
    manifest sat in the reports root and packaging raised
    'blank/non-string report_text: task_manifest.json'."""
    from src.eval.blinding import load_task_manifest
    from src.llm.generation_runner import generate_batch, manifest_path

    reports = tmp_path / "reports"
    providers = [FakeProvider(p) for p in sorted(PROVIDERS3)]
    tasks = [
        {"subject_id": "Sub01", "side": "P", "user_prompt": "U-Sub01", "reference_id": "ref"},
        {"subject_id": "Sub02", "side": "P", "user_prompt": "U-Sub02", "reference_id": "ref"},
    ]
    counters = generate_batch(tasks, providers, reports, "v2", "SYSTEM", {}, {})
    assert counters == {"generated": 6, "skipped": 0, "failed": 0, "superseded": 0}
    assert manifest_path(reports).exists()  # manifest is in _meta/, not the root

    # idempotent rerun through the same real entry: 0 new calls
    counters2 = generate_batch(tasks, providers, reports, "v2", "SYSTEM", {}, {})
    assert counters2 == {"generated": 0, "skipped": 6, "failed": 0, "superseded": 0}

    # a config change forces one supersede -- archive appears in the root
    tasks_changed = [dict(tasks[0], user_prompt="U-Sub01-CHANGED"), tasks[1]]
    generate_batch(tasks_changed, providers, reports, "v2", "SYSTEM", {}, {})
    assert any(".superseded-" in f.name for f in reports.iterdir())

    # packaging from the real directory, validated against the runner's own manifest
    expected = load_task_manifest(manifest_path(reports))
    batch = create_rating_packets(str(reports), str(tmp_path / "out"), prompt_version="v2",
                                  expected_providers=PROVIDERS3, expected_tasks=expected)

    total_items = sum(len(json.loads(f.read_text())) for f in (batch / "packets").iterdir())
    assert total_items == 6
    key_lines = (batch / "answer_key_DO_NOT_SHARE.csv").read_text().strip().splitlines()
    assert len(key_lines) == 1 + 6
    assert not any(".superseded-" in line for line in key_lines)
    assert not any("task_manifest" in line for line in key_lines)
