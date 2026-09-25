"""Single-transmission SDK stream adapters for the prospective study.

An explicit API key and HTTP transport are required. This module never loads
environment credentials or starts a batch. Tests use real SDKs and MockTransport.
The release runner must persist events as they arrive and enforce its process
deadline; the socket timeout here is not a substitute for that deadline.
"""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
import json
import math
import time

import httpx

from .formal_generation import IntegrityError, digest


SAFE_HEADERS = {"x-request-id", "request-id", "x-goog-request-id", "retry-after", "retry-after-ms"}


@dataclass(frozen=True)
class MockSDKAttempt:
    """Serializable mock HTTP response for the isolated deadline worker.

    This always uses MockTransport and a fixed fake key. There is no option to
    choose a network transport or supply a real credential through this class.
    """
    task: dict
    chunks: tuple
    status: int = 200
    stall_after_chunks_seconds: float = 0

    def events(self):
        attempt = self

        class MockStream(httpx.SyncByteStream):
            def __iter__(self):
                yield from attempt.chunks
                if attempt.stall_after_chunks_seconds:
                    time.sleep(attempt.stall_after_chunks_seconds)

        def handler(request):
            return httpx.Response(attempt.status, headers={"content-type": "text/event-stream",
                "x-request-id": "mock-worker-request"}, stream=MockStream())

        yield from stream_attempt(self.task, api_key="fake-offline-key", transport=httpx.MockTransport(handler))


def retry_after(headers, now=None):
    value = headers.get("retry-after")
    try:
        if value is not None:
            try:
                result = float(value)
            except ValueError:
                date = parsedate_to_datetime(value)
                result = max(0, (date - (now or datetime.now(timezone.utc))).total_seconds())
        elif "retry-after-ms" in headers:
            result = float(headers["retry-after-ms"]) / 1000
        else:
            return 0
        return result if math.isfinite(result) and result >= 0 else None
    except (ValueError, TypeError, OverflowError):
        return None  # Invalid retry instructions pause instead of guessing.


def normalize_error(provider, status, body, headers=None):
    """Conservatively distinguish rate limiting from permanent quota failures."""
    headers = headers or {}
    inner = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(inner, dict):
        inner = {}
    code = str(inner.get("code") or inner.get("type") or inner.get("status") or "").lower()
    kind = str(inner.get("type", "")).lower()
    details = inner.get("details") or []
    details = details if isinstance(details, list) else []
    reasons = {str(d.get("reason", "")).lower() for d in details if isinstance(d, dict)}
    violations = [v for d in details if isinstance(d, dict)
                  for v in d.get("violations", []) if isinstance(v, dict)]
    quota_ids = [str(v.get("quotaId", "")).lower() for v in violations]
    permanent = {"insufficient_quota", "billing_error", "billing_not_active", "billing_hard_limit_reached",
                 "credit_balance_too_low", "daily_limit_exceeded"}
    billing_message = str(inner.get("message", "")).lower()
    if (code in permanent or kind in permanent or reasons & permanent or
        any("perday" in q for q in quota_ids) or any(v.get("quotaValue") in {0, "0"} for v in violations)):
        normalized = "permanent_quota"
    elif provider == "anthropic" and "credit balance is too low" in billing_message:
        normalized = "billing"
    elif status == 401 or code in {"invalid_api_key", "authentication_error", "unauthenticated"}:
        normalized = "authentication"
    elif status == 403 or code in {"permission_denied", "permission_error"}:
        normalized = "permission"
    elif status == 404 or code in {"model_not_found", "not_found_error"}:
        normalized = "unsupported_model"
    elif status in {400, 422}:
        normalized = "unsupported_parameter"
    elif status == 408:
        normalized = "timeout"
    elif status == 429 and (
        (provider == "openai" and code == "rate_limit_exceeded") or
        (provider == "anthropic" and code == "rate_limit_error") or
        (provider == "gemini" and quota_ids and all("perminute" in q for q in quota_ids))
    ):
        normalized = "transient_rate_limit"
    elif provider == "anthropic" and kind == "overloaded_error" and status in {None, 200, 529}:
        normalized = "transient_server"
    elif isinstance(status, int) and 500 <= status <= 599:
        normalized = "transient_server"
    else:
        normalized = "unknown"
    return {"type": "error", "code": normalized, "http_status": None if status == 200 else status,
            "retry_after_seconds": retry_after(headers), "raw": body}


class OneTransmission(httpx.BaseTransport):
    """Count HTTP dispatches and block hidden retries or redirects."""
    def __init__(self, inner, provider=None, task=None, before_dispatch=None):
        self.inner = inner
        self.provider = provider
        self.task = task
        self.before_dispatch = before_dispatch
        self.count = 0
        self.status = None
        self.headers = {}
        self.response = None
        self.wire_body_sha256 = None

    def handle_request(self, request):
        if self.count:
            raise IntegrityError("An SDK attempted a second transmission within one attempt")
        body = json.loads(request.content) if request.content else {}
        if self.provider == "gemini":
            # google-genai 2.23.0 leaves these nested field names in Python
            # form. Normalize only the registered aliases to the documented
            # JSON wire spelling. Conflicting aliases are an integrity error.
            thinking = body.get("generationConfig", {}).get("thinkingConfig", {})
            for snake, camel in [("thinking_level", "thinkingLevel"), ("include_thoughts", "includeThoughts")]:
                if snake in thinking:
                    value = thinking.pop(snake)
                    if camel in thinking and thinking[camel] != value:
                        raise IntegrityError("Conflicting Gemini thinking aliases")
                    thinking[camel] = value
            headers = dict(request.headers)
            headers.pop("content-length", None)
            request = httpx.Request(request.method, request.url, headers=headers,
                                    content=json.dumps(body).encode(), extensions=request.extensions)
        if self.task is not None:
            routes = {"openai": ("api.openai.com", "/v1/chat/completions"),
                      "anthropic": ("api.anthropic.com", "/v1/messages"),
                      "gemini": ("generativelanguage.googleapis.com",
                                 f"/v1beta/models/{self.task['model']}:streamGenerateContent")}
            if request.method != "POST" or (request.url.host, request.url.path) != routes[self.provider]:
                raise IntegrityError("Unexpected API endpoint")
            validate_wire_request(self.task, body)
        self.wire_body_sha256 = digest(body)
        if self.before_dispatch is not None:
            self.before_dispatch(self.wire_body_sha256)
        self.count += 1
        response = self.inner.handle_request(request)
        self.response = response
        self.status = response.status_code
        self.headers = {k: v for k, v in response.headers.items() if k in SAFE_HEADERS}
        return response

    def close(self):
        if self.response is not None:
            self.response.close()
        self.inner.close()


def anthropic_http_client(trace):
    """Bridge the Anthropic SDK's httpx2 interface to the shared transport.

    The bridge makes no network request itself. The explicitly supplied inner
    transport is the only dispatch point and is counted by OneTransmission.
    """
    import httpx2

    class StreamBridge(httpx2.SyncByteStream):
        def __init__(self, response):
            self.response = response

        def __iter__(self):
            yield from self.response.stream

        def close(self):
            self.response.close()

    class TransportBridge(httpx2.BaseTransport):
        def handle_request(self, request):
            translated = httpx.Request(request.method, str(request.url), headers=list(request.headers.multi_items()),
                                       content=request.read(), extensions=request.extensions)
            response = trace.handle_request(translated)
            return httpx2.Response(response.status_code, headers=list(response.headers.multi_items()),
                                   stream=StreamBridge(response), extensions=response.extensions)

        def close(self):
            trace.close()

    return httpx2.Client(transport=TransportBridge(), trust_env=False, follow_redirects=False, timeout=600)


def validate_wire_request(task, body):
    """Check effective clinical inputs and registered settings before dispatch."""
    provider = task["provider"]
    params = task["parameters"]
    if provider in {"openai", "anthropic"}:
        expected = {**params, "model": task["model"], "stream": True}
        expected["messages"] = [{"role": "user", "content": task["user_prompt"]}]
        if provider == "openai":
            expected["messages"].insert(0, {"role": "system", "content": task["system_prompt"]})
        else:
            expected["system"] = task["system_prompt"]
        if body != expected:
            raise IntegrityError("SDK wire request differs from registered request")
    else:
        expected_config = {"candidateCount": params.get("candidate_count", 1),
                           "maxOutputTokens": params["max_output_tokens"],
                           "thinkingConfig": {"thinkingLevel": params["thinking_config"]["thinking_level"],
                                              "includeThoughts": params["thinking_config"]["include_thoughts"]}}
        expected = {"contents": [{"role": "user", "parts": [{"text": task["user_prompt"]}]}],
                    "systemInstruction": {"role": "user", "parts": [{"text": task["system_prompt"]}]},
                    "generationConfig": expected_config}
        if body != expected:
            raise IntegrityError("Gemini wire request differs from registered request")


def _body(exc):
    for attribute in ("body", "response_json"):
        value = getattr(exc, attribute, None)
        if value is not None:
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            return response.json()
        except (ValueError, httpx.ResponseNotRead):
            pass
    return {"exception_type": type(exc).__name__}


def _exception_event(provider, exc, trace):
    body = _body(exc)
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if not isinstance(status, int):
        status = trace.status
    event = normalize_error(provider, status, body, trace.headers)
    names = {type(exc).__name__, type(getattr(exc, "__cause__", None)).__name__}
    if isinstance(exc, httpx.TimeoutException) or names & {"APITimeoutError", "ReadTimeout", "ConnectTimeout"}:
        event.update(code="timeout", remote_completion_possible=True)
    elif isinstance(exc, httpx.TransportError) or "APIConnectionError" in names:
        event.update(code="transport", remote_completion_possible=True)
    if isinstance(exc, IntegrityError) or isinstance(getattr(exc, "__cause__", None), IntegrityError):
        event.update(code="adapter_integrity_error")
    # HTTP 200 belongs to the interrupted response, not to a transport failure.
    if event["code"] in {"timeout", "transport"} and status == 200:
        event["response_http_status"] = status
        event["http_status"] = None
    return event


def stream_attempt(task, *, api_key, transport, before_dispatch=None):
    """Yield evidence-bearing normalized events from one actual SDK invocation.

    `transport` must be explicitly supplied; production dispatch remains the
    responsibility of a separately authorized runner. Empty text events retain
    metadata/raw stream objects without adding content to the report.
    """
    if not api_key or not isinstance(transport, httpx.BaseTransport):
        raise ValueError("An explicit API key and HTTP transport are required")
    provider = task["provider"]
    params = dict(task["parameters"])
    allowed = {
        "openai": {"max_completion_tokens", "reasoning_effort", "n", "stream", "stream_options"},
        "anthropic": {"max_tokens", "thinking", "output_config"},
        "gemini": {"max_output_tokens", "thinking_config", "candidate_count"},
    }
    if provider not in allowed or set(params) - allowed[provider]:
        raise IntegrityError("Unsupported provider or unregistered parameters")
    if params.get("n", 1) != 1 or params.get("candidate_count", 1) != 1 or params.get("stream", True) is not True:
        raise IntegrityError("Exactly one streamed response is required")
    attribution = {"slot_id": task["slot_id"], "task_sha256": digest(task), "provider": provider}
    if provider == "openai" and params.get("stream_options") != {"include_usage": True}:
        raise IntegrityError("OpenAI usage streaming must be explicitly registered")
    trace = OneTransmission(transport, provider, task, before_dispatch)
    http = anthropic_http_client(trace) if provider == "anthropic" else httpx.Client(
        transport=trace, trust_env=False, follow_redirects=False, timeout=600)
    client = stream = None
    metadata = {"requested_model": task["model"], "response_model": None, "response_id": None,
                "usage": {}, "finish_reason": None}
    ended = False
    block_types = {}

    def wrap(event):
        return {**event, **attribution, "transmissions": trace.count,
                "wire_body_sha256": trace.wire_body_sha256,
                "response_headers": dict(trace.headers), "metadata": json.loads(json.dumps(metadata))}

    try:
        if provider == "openai":
            import openai
            client = openai.OpenAI(api_key=api_key, base_url="https://api.openai.com/v1",
                                   max_retries=0, timeout=600, http_client=http)
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}
            stream = client.chat.completions.create(model=task["model"], messages=[
                {"role": "system", "content": task["system_prompt"]},
                {"role": "user", "content": task["user_prompt"]}], **params)
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key, base_url="https://api.anthropic.com",
                                         max_retries=0, timeout=600, http_client=http)
            stream = client.messages.create(model=task["model"], system=task["system_prompt"],
                messages=[{"role": "user", "content": task["user_prompt"]}], stream=True, **params)
        else:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key, vertexai=False, http_options=types.HttpOptions(
                base_url="https://generativelanguage.googleapis.com", api_version="v1beta",
                httpx_client=http, timeout=600000, retry_options=types.HttpRetryOptions(attempts=1)))
            stream = client.models.generate_content_stream(model=task["model"], contents=task["user_prompt"],
                config=types.GenerateContentConfig(system_instruction=task["system_prompt"],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True), **params))
        for chunk in stream:
            raw = chunk.model_dump(mode="json", exclude_none=True)
            text = ""
            if provider == "openai":
                metadata["response_id"] = raw.get("id") or metadata["response_id"]
                metadata["response_model"] = raw.get("model") or metadata["response_model"]
                if raw.get("usage"):
                    metadata["usage"].update(raw["usage"])
                choices = raw.get("choices", [])
                if len(choices) > 1 or any(c.get("index", 0) != 0 for c in choices):
                    raise IntegrityError("Unexpected completion candidate")
                if choices:
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    text = (delta.get("content") or "") + (delta.get("refusal") or "")
                    if choice.get("finish_reason"):
                        metadata["finish_reason"] = choice["finish_reason"]
                        ended = True
            elif provider == "anthropic":
                kind = raw.get("type")
                if kind == "message_start":
                    message = raw["message"]
                    metadata.update(response_id=message.get("id"), response_model=message.get("model"))
                    metadata["usage"].update(message.get("usage", {}))
                elif kind == "content_block_start":
                    block = raw["content_block"]
                    block_types[raw["index"]] = block["type"]
                    if block["type"] == "text":
                        text = block.get("text", "")
                elif kind == "content_block_delta":
                    delta = raw["delta"]
                    if delta.get("type") == "text_delta":
                        if block_types.get(raw["index"]) != "text":
                            raise IntegrityError("Text delta has no matching text block")
                        text = delta.get("text", "")
                elif kind == "message_delta":
                    metadata["finish_reason"] = raw.get("delta", {}).get("stop_reason")
                    metadata["usage"].update(raw.get("usage", {}))
                elif kind == "message_stop":
                    ended = True
            else:
                metadata["response_id"] = raw.get("response_id") or metadata["response_id"]
                metadata["response_model"] = raw.get("model_version") or metadata["response_model"]
                if raw.get("usage_metadata"):
                    metadata["usage"].update(raw["usage_metadata"])
                candidates = raw.get("candidates", [])
                if len(candidates) > 1 or any(c.get("index", 0) != 0 for c in candidates):
                    raise IntegrityError("Unexpected generation candidate")
                if candidates:
                    candidate = candidates[0]
                    parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if not p.get("thought", False))
                    if candidate.get("finish_reason"):
                        metadata["finish_reason"] = candidate["finish_reason"]
                        ended = True
                elif raw.get("prompt_feedback", {}).get("block_reason"):
                    metadata["finish_reason"] = raw["prompt_feedback"]["block_reason"]
                    ended = True
            yield wrap({"type": "text", "text": text, "raw": raw})
        if ended:
            yield wrap({"type": "completed", "finish_reason": metadata["finish_reason"],
                        "raw": {"stream_exhausted": True}})
        else:
            yield wrap({"type": "error", "code": "unexpected_eof", "raw": {"stream_exhausted": True}})
    except Exception as exc:
        yield wrap(_exception_event(provider, exc, trace))
    finally:
        try:
            if stream is not None and hasattr(stream, "close"):
                stream.close()
        finally:
            try:
                if client is not None:
                    client.close()
            finally:
                http.close()
