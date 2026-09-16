"""Mock-response tests for response-side provenance extraction (audit rounds 2 R4 +
3 T6): request_id (transport-level) and response_id (API object id) are SEPARATE
fields with distinct semantics -- never substituted for each other; absent values
stay None without raising; nested usage detail is preserved. No SDK or network."""
from __future__ import annotations

from types import SimpleNamespace

from src.llm.providers import (
    extract_anthropic_metadata,
    extract_gemini_metadata,
    extract_openai_metadata,
)


class UsageObj:
    def model_dump(self):
        return {
            "input_tokens": 123,
            "output_tokens": 456,
            # nested detail must survive (T6: don't flatten usage)
            "output_tokens_details": {"reasoning_tokens": 400},
        }


def test_anthropic_extraction_separates_ids():
    resp = SimpleNamespace(model="claude-opus-5-20260101", id="msg_abc", usage=UsageObj())
    resp._request_id = "req_123"
    meta = extract_anthropic_metadata(resp)
    assert meta["response_model"] == "claude-opus-5-20260101"
    assert meta["request_id"] == "req_123"
    assert meta["response_id"] == "msg_abc"
    assert meta["usage"]["output_tokens_details"] == {"reasoning_tokens": 400}


def test_anthropic_no_id_borrowing():
    # message id must NOT be substituted for a missing transport request id (T6)
    meta = extract_anthropic_metadata(SimpleNamespace(model="m", id="msg_abc", usage=None))
    assert meta["request_id"] is None
    assert meta["response_id"] == "msg_abc"
    assert meta["usage"] is None


def test_openai_extraction_uses_transport_request_id():
    resp = SimpleNamespace(model="gpt-6-astra-2026-09", id="chatcmpl-xyz", usage=UsageObj())
    resp._request_id = "req_oai_1"
    meta = extract_openai_metadata(resp)
    assert meta["response_model"] == "gpt-6-astra-2026-09"
    assert meta["request_id"] == "req_oai_1"  # NOT the completion id (T6)
    assert meta["response_id"] == "chatcmpl-xyz"
    assert meta["usage"]["output_tokens"] == 456


def test_gemini_extraction_keeps_request_id_none():
    usage = SimpleNamespace(prompt_token_count=10, candidates_token_count=20)
    resp = SimpleNamespace(model_version="gemini-3.1-pro-preview-0916",
                           response_id="resp-1", usage_metadata=usage)
    meta = extract_gemini_metadata(resp)
    assert meta["response_model"] == "gemini-3.1-pro-preview-0916"
    assert meta["request_id"] is None  # SDK exposes no transport id; don't borrow (T6)
    assert meta["response_id"] == "resp-1"
    assert meta["usage"]["prompt_token_count"] == 10


def test_all_absent_fields_become_none_without_raising():
    empty = SimpleNamespace()
    for fn in (extract_anthropic_metadata, extract_openai_metadata, extract_gemini_metadata):
        meta = fn(empty)
        assert meta["response_model"] is None
        assert meta["request_id"] is None
        assert meta["response_id"] is None
        assert meta["usage"] is None
