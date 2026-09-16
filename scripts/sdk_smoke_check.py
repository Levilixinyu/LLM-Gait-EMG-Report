"""Real-SDK small-sample compatibility check (handoff §13.2). ONE minimal paid call
per provider -- run only with the user's explicit go-ahead.

Purpose: everything so far validated response-metadata extraction against MOCK
objects; this confirms the live SDK response objects actually carry the fields the
extractors read (response_model / request_id / response_id / usage incl. nested
detail), that stop reasons land in the per-provider success sets, and that a full
record_from_result() output is strict-JSON serializable. It does NOT validate
clinical content -- a trivial prompt is used on purpose.

Writes audit/outputs/sdk_smoke_check.json. Exits nonzero if any provider's live
response fails a check (same fail-loudly rule as the other acceptance scripts).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.llm.generation_cache import SUCCESS_STOP_REASONS, TaskSpec, record_from_result
from src.llm.providers import AnthropicProvider, GeminiProvider, OpenAIProvider

OUT = Path(__file__).resolve().parents[1] / "audit" / "outputs" / "sdk_smoke_check.json"

def main() -> None:
    results = {}
    failures = []
    for ProviderCls, low_tokens in [(AnthropicProvider, 512), (OpenAIProvider, 32), (GeminiProvider, 512)]:
        # anthropic and gemini get extra headroom: BOTH models' thinking tokens count
        # against max_tokens (live-verified 2026-09-16: claude-opus-5 spent 31 thinking
        # tokens under a 32-token cap and truncated after one text character --
        # usage.output_tokens_details.thinking_tokens=31, stop_reason=max_tokens).
        # Production runs use 8000, which produced 0/54 truncations in the v1 batch.
        provider = ProviderCls(max_tokens=low_tokens)
        name = provider.name
        t0 = time.time()
        try:
            result = provider.generate("Reply with exactly one word.", "Say OK.")
        except Exception as exc:
            failures.append(f"{name}: call failed - {type(exc).__name__}: {exc}")
            results[name] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        elapsed = time.time() - t0

        checks = {
            "text_non_blank": bool(result.text.strip()),
            "stop_reason_success": result.stop_reason in SUCCESS_STOP_REASONS[name],
            "response_model_present": bool(result.response_model),
            "usage_present": isinstance(result.usage, dict) and bool(result.usage),
            # id semantics: at least one of the two ids must be present; request_id
            # may legitimately be None (gemini), response_id should exist for
            # anthropic/openai
            "some_id_present": bool(result.request_id or result.response_id),
        }
        spec = TaskSpec(subject_id="SMOKE", side=None, provider=name, model=provider.model,
                        prompt_version="smoke", system_prompt="s", user_prompt="u")
        try:
            json.dumps(record_from_result(spec, result), allow_nan=False)
            checks["record_strict_json"] = True
        except (TypeError, ValueError) as exc:
            checks["record_strict_json"] = False
            failures.append(f"{name}: record not strict-JSON serializable: {exc}")

        for key, ok in checks.items():
            if not ok:
                failures.append(f"{name}: check failed - {key}")

        results[name] = {
            "elapsed_s": round(elapsed, 1),
            "requested_model": provider.model,
            "response_model": result.response_model,
            "request_id": result.request_id,
            "response_id": result.response_id,
            "stop_reason": result.stop_reason,
            "usage": result.usage,
            "text": result.text.strip()[:50],
            "checks": checks,
        }
        print(f"{name}: {json.dumps(results[name], ensure_ascii=False)}")

    OUT.write_text(json.dumps({"results": results, "failures": failures}, indent=2, ensure_ascii=False))
    print(f"written to {OUT}")
    if failures:
        print(f"SMOKE CHECK FAILED ({len(failures)}):")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("ALL SDK SMOKE CHECKS PASSED")


if __name__ == "__main__":
    main()
