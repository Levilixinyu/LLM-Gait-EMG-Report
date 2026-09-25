"""Real provider SDKs, fake credentials and mocked HTTP only."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import socket

import httpx
import pytest

from src.llm.formal_generation import IntegrityError, SyntheticTransport, classify_error, digest, run_offline
from src.llm.formal_providers import MockSDKAttempt, OneTransmission, normalize_error, retry_after, stream_attempt


CONFIG = json.loads((Path(__file__).resolve().parents[1] /
    "docs/formal_study/generation_preflight_v1/provider_candidates.json").read_text())
PROVIDERS = [p["provider"] for p in CONFIG["providers"]]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network connections are prohibited by this test suite")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)


def task(provider):
    c = next(p for p in CONFIG["providers"] if p["provider"] == provider)
    return {"slot_id": "synthetic_" + provider, "case_id": "synthetic", "provider": provider,
            "model": c["model"], "parameters": copy.deepcopy(c["parameters"]),
            "system_prompt": "Synthetic system only.", "user_prompt": "Synthetic input only.",
            "source_hashes": {"synthetic": digest("synthetic input")}}


def sse(event, named=False):
    prefix = f"event: {event['type']}\n" if named else ""
    return (prefix + "data: " + json.dumps(event) + "\n\n").encode()


def fixture_events(provider, finish=True, empty=False, refusal=False):
    content = "" if empty else ("I cannot do that." if refusal else "First. Second.")
    if provider == "openai":
        base = {"id": "response-synthetic", "object": "chat.completion.chunk", "created": 1, "model": "mock-response-model"}
        delta = {"refusal" if refusal else "content": content}
        result = [sse({**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]})]
        if finish:
            result += [sse({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "length"}]}),
                       sse({**base, "choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}),
                       b"data: [DONE]\n\n"]
        return result
    if provider == "anthropic":
        result = [sse({"type": "message_start", "message": {"id": "response-synthetic", "type": "message", "role": "assistant",
            "content": [], "model": "mock-response-model", "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 0}}}, True)]
        result += [sse({"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}}, True),
                   sse({"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "Private thinking"}}, True),
                   sse({"type": "content_block_stop", "index": 0}, True)]
        for index, value in enumerate([content[:7], content[7:]], 1):
            result += [sse({"type": "content_block_start", "index": index, "content_block": {"type": "text", "text": ""}}, True),
                       sse({"type": "content_block_delta", "index": index, "delta": {"type": "text_delta", "text": value}}, True),
                       sse({"type": "content_block_stop", "index": index}, True)]
        if finish:
            result += [sse({"type": "message_delta", "delta": {"stop_reason": "max_tokens", "stop_sequence": None},
                           "usage": {"output_tokens": 20}}, True), sse({"type": "message_stop"}, True)]
        return result
    result = [sse({"responseId": "response-synthetic", "modelVersion": "mock-response-model",
                   "candidates": [{"index": 0, "content": {"role": "model", "parts": [
                       {"text": "Private thinking", "thought": True}, {"text": content[:7]}, {"text": content[7:]}]}}]})]
    if finish:
        result += [sse({"responseId": "response-synthetic", "modelVersion": "mock-response-model",
                        "candidates": [{"index": 0, "finishReason": "MAX_TOKENS"}],
                        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20, "totalTokenCount": 30}})]
    return result


class ByteStream(httpx.SyncByteStream):
    def __init__(self, parts, failure=None):
        self.parts = parts
        self.failure = failure
        self.closed = False

    def __iter__(self):
        yield from self.parts
        if self.failure:
            raise self.failure

    def close(self):
        self.closed = True


def invoke(provider, response=None, failure=None, **kwargs):
    requests = []
    byte_stream = ByteStream(fixture_events(provider, **kwargs), failure)
    def handler(request):
        requests.append(request)
        if response is not None:
            return response
        return httpx.Response(200, headers={"content-type": "text/event-stream", "x-request-id": "request-synthetic"}, stream=byte_stream)
    events = list(stream_attempt(task(provider), api_key="fake-offline-key", transport=httpx.MockTransport(handler)))
    return events, requests, byte_stream


@pytest.mark.parametrize("provider", PROVIDERS)
def test_sdk_stream_capture_metadata_and_wire_parameters(provider):
    events, requests, stream = invoke(provider)
    assert len(requests) == 1
    assert stream.closed
    assert events[-1]["type"] == "completed", events[-1]
    assert "".join(e.get("text", "") for e in events) == "First. Second."
    assert events[-1]["metadata"]["response_id"] == "response-synthetic"
    assert events[-1]["metadata"]["response_model"] == "mock-response-model"
    assert events[-1]["metadata"]["usage"]
    assert events[-1]["response_headers"]["x-request-id"] == "request-synthetic"
    assert all(e["task_sha256"] == digest(task(provider)) for e in events)
    payload = json.loads(requests[0].content)
    if provider == "openai":
        assert requests[0].url.path == "/v1/chat/completions"
        assert payload["stream"] is True and payload["stream_options"]["include_usage"] is True
        assert payload["messages"][0]["content"] == task(provider)["system_prompt"]
        assert payload["messages"][1]["content"] == task(provider)["user_prompt"]
        assert payload["reasoning_effort"] == "high" and payload["max_completion_tokens"] == 8000
    elif provider == "anthropic":
        assert requests[0].url.path == "/v1/messages"
        assert payload["stream"] is True and payload["system"] == task(provider)["system_prompt"]
        assert payload["messages"][0]["content"] == task(provider)["user_prompt"]
        assert payload["thinking"]["type"] == "adaptive" and payload["output_config"]["effort"] == "high"
    else:
        assert requests[0].url.path.endswith(":streamGenerateContent")
        assert payload["systemInstruction"]["parts"][0]["text"] == task(provider)["system_prompt"]
        assert payload["contents"][0]["parts"][0]["text"] == task(provider)["user_prompt"]
        assert payload["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "HIGH"
        assert payload["generationConfig"]["maxOutputTokens"] == 8000


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("status", [429, 503])
def test_sdk_makes_one_http_transmission_on_retryable_status(provider, status):
    body = {"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded", "status": "RESOURCE_EXHAUSTED", "message": "Synthetic failure"}}
    events, requests, _ = invoke(provider, response=httpx.Response(status, json=body, headers={"retry-after": "60"}))
    assert len(requests) == 1
    assert events[-1]["type"] == "error"
    assert events[-1]["retry_after_seconds"] == 60
    assert events[-1]["transmissions"] == 1


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("empty", [True, False])
def test_real_sdk_events_flow_through_persistent_policy(tmp_path, provider, empty):
    events, requests, _ = invoke(provider, empty=empty)
    t = task(provider)
    manifest = {"mode": "offline_test", "network_allowed": False, "tasks": [t]}
    result = run_offline(tmp_path, manifest, {t["slot_id"]: SyntheticTransport((events,))})
    out = result["outcomes"][t["slot_id"]]
    assert out["status"] == ("empty" if empty else "captured")
    resumed = run_offline(tmp_path, manifest, {t["slot_id"]: SyntheticTransport(())})
    assert result == resumed
    assert len(requests) == 1


@pytest.mark.parametrize("provider", PROVIDERS)
def test_disconnect_preserves_text_and_no_hidden_retry(provider):
    events, requests, stream = invoke(provider, finish=False, failure=httpx.ReadError("Synthetic disconnect"))
    assert len(requests) == 1
    assert stream.closed
    assert events[-1]["type"] == "error"
    assert "".join(e.get("text", "") for e in events) == "First. Second."
    assert events[-1]["code"] == "transport", events[-1]


@pytest.mark.parametrize("provider", PROVIDERS)
def test_eof_without_finish_is_not_completed_empty(provider):
    events, requests, _ = invoke(provider, finish=False, empty=True)
    assert events[-1]["code"] == "unexpected_eof"
    assert classify_error(events[-1]) == "pause"
    assert len(requests) == 1


def test_openai_refusal_is_report_text():
    events, _, _ = invoke("openai", refusal=True)
    assert "".join(e.get("text", "") for e in events) == "I cannot do that."


@pytest.mark.parametrize("provider,status,body,action", [
    ("openai", 429, {"error": {"code": "insufficient_quota"}}, "stop"),
    ("openai", 429, {"error": {"code": "rate_limit_exceeded"}}, "retry"),
    ("anthropic", 429, {"error": {"type": "rate_limit_error"}}, "retry"),
    ("anthropic", 400, {"error": {"type": "invalid_request_error", "message": "Your credit balance is too low"}}, "stop"),
    ("gemini", 429, {"error": {"status": "RESOURCE_EXHAUSTED"}}, "pause"),
    ("gemini", 429, {"error": {"details": [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}]}}, "stop"),
    ("gemini", 429, {"error": {"details": [{"violations": [{"quotaId": "GenerateRequestsPerMinutePerProjectPerModel"}]}]}}, "retry"),
    ("gemini", 429, {"error": {"details": [{"violations": [{"quotaId": "GenerateRequestsPerMinutePerProjectPerModel", "quotaValue": "0"}]}]}}, "stop"),
    ("openai", 503, {"error": {"code": "billing_hard_limit_reached"}}, "stop"),
])
def test_permanent_payload_precedes_generic_retry_status(provider, status, body, action):
    assert classify_error(normalize_error(provider, status, body)) == action


def test_retry_after_seconds_milliseconds_http_date_and_invalid():
    assert retry_after({"retry-after": "12"}) == 12
    assert retry_after({"retry-after-ms": "12000"}) == 12
    assert retry_after({"retry-after": "Fri, 18 Sep 2026 12:01:00 GMT"}, datetime(2026, 9, 18, 12, tzinfo=timezone.utc)) == 60
    assert retry_after({"retry-after": "garbled"}) is None
    assert retry_after({"retry-after": "nan"}) is None


def test_transmission_guard_blocks_second_dispatch():
    sent = []
    transport = OneTransmission(httpx.MockTransport(lambda r: sent.append(r) or httpx.Response(200)))
    request = httpx.Request("POST", "https://example.invalid")
    transport.handle_request(request)
    with pytest.raises(IntegrityError):
        transport.handle_request(request)
    assert len(sent) == 1


@pytest.mark.parametrize("provider", PROVIDERS)
def test_sdk_worker_to_durable_ledger_under_hard_deadline(tmp_path, provider):
    t = task(provider)
    fixture = MockSDKAttempt(t, tuple(fixture_events(provider, finish=False)), stall_after_chunks_seconds=20)
    manifest = {"mode": "offline_test", "network_allowed": False, "tasks": [t]}
    result = run_offline(tmp_path, manifest, {t["slot_id"]: SyntheticTransport((fixture,))}, deadline_seconds=2.5)
    outcome = result["outcomes"][t["slot_id"]]
    assert outcome["text"] == "First. Second."
    assert outcome["terminal"]["code"] == "timeout"
    resumed = run_offline(tmp_path, manifest, {t["slot_id"]: SyntheticTransport(())}, deadline_seconds=2.5)
    assert result == resumed


@pytest.mark.parametrize("provider", PROVIDERS)
def test_sdk_transport_timeout_has_one_dispatch(provider):
    requests = []
    def handler(request):
        requests.append(request)
        raise httpx.ReadTimeout("Synthetic timeout")
    events = list(stream_attempt(task(provider), api_key="fake-offline-key", transport=httpx.MockTransport(handler)))
    assert len(requests) == 1
    assert events[-1]["code"] == "timeout"


@pytest.mark.parametrize("provider,body", [
    ("openai", {"error": {"code": "insufficient_quota", "message": "Synthetic permanent quota"}}),
    ("anthropic", {"error": {"type": "billing_error", "message": "Synthetic billing failure"}}),
    ("gemini", {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": [
        {"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}], "message": "Synthetic daily quota"}}),
])
def test_sdk_permanent_quota_errors_are_not_retried(provider, body):
    events, requests, _ = invoke(provider, response=httpx.Response(429, json=body))
    assert len(requests) == 1
    assert classify_error(events[-1]) == "stop", events[-1]


def test_anthropic_error_inside_successful_http_stream():
    chunks = fixture_events("anthropic", finish=False)
    chunks.append(sse({"type": "error", "error": {"type": "overloaded_error", "message": "Synthetic overload"}}, True))
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=ByteStream(chunks))
    events = list(stream_attempt(task("anthropic"), api_key="fake-offline-key", transport=httpx.MockTransport(handler)))
    assert "".join(e.get("text", "") for e in events) == "First. Second."
    assert events[-1]["code"] == "transient_server", events[-1]


def test_wrong_task_stream_cannot_be_saved_as_the_requested_report(tmp_path):
    t = task("openai")
    other = copy.deepcopy(t); other["user_prompt"] = "A different input."
    fixture = MockSDKAttempt(other, tuple(fixture_events("openai")))
    manifest = {"mode": "offline_test", "network_allowed": False, "tasks": [t]}
    with pytest.raises(IntegrityError, match="different frozen task"):
        run_offline(tmp_path, manifest, {t["slot_id"]: SyntheticTransport((fixture,))})


@pytest.mark.parametrize("provider", PROVIDERS)
def test_redirect_is_not_followed(provider):
    events, requests, _ = invoke(provider, response=httpx.Response(307, headers={"location": "https://example.invalid/redirect"}))
    assert len(requests) == 1
    assert events[-1]["type"] == "error"
    assert classify_error(events[-1]) == "pause"
