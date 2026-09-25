"""A funded-account follow-up must not reopen or replace captured outputs."""
from scripts.run_openai_credit_followup import capture_once
from src.llm.compatibility_check import HTTPFixture, build_plan
from src.llm.formal_generation import append, read_journal
from tests.test_formal_providers import fixture_events


def task():
    return next(t for t in build_plan()['tasks'] if t['provider'] == 'openai')


def test_success_is_kept_without_redispatch(tmp_path):
    fixture = HTTPFixture(chunks=tuple(fixture_events('openai')))
    result = capture_once(tmp_path, task(), api_key='fake-offline-key', fixture=fixture)
    assert result['state'] == 'captured'
    # This resume has no mock transport; a mistaken dispatch would be a defect.
    assert capture_once(tmp_path, task(), api_key='fake-offline-key', fixture=HTTPFixture()) == result
    assert sum(r['kind'] == 'attempt_started' for r in read_journal(tmp_path)[0]) == 1


def test_interrupted_followup_cannot_silently_reset_count(tmp_path):
    append(tmp_path, {'kind': 'attempt_started', 'attempt': 2})
    result = capture_once(tmp_path, task(), api_key='fake-offline-key', fixture=HTTPFixture())
    assert result['state'] == 'paused'
    assert len(read_journal(tmp_path)[0]) == 2


def test_empty_completed_output_is_terminal(tmp_path):
    fixture = HTTPFixture(chunks=tuple(fixture_events('openai', empty=True)))
    result = capture_once(tmp_path, task(), api_key='fake-offline-key', fixture=fixture)
    assert result['state'] == 'empty'
    assert capture_once(tmp_path, task(), api_key='fake-offline-key', fixture=HTTPFixture()) == result
