"""Provider abstraction for generating LLM reports across Claude, GPT, and Gemini
(the three-commercial-flagship comparison design -- see README "Model roster" note),
so the same report-generation loop can drive a multi-model comparison without
provider-specific branching elsewhere in the pipeline. LocalOllamaProvider is kept for
a possible future open-source arm but isn't part of the current pilot (disk constraints
ruled out running a large local model)."""
from __future__ import annotations

import os
import time

from dotenv import load_dotenv

load_dotenv()  # loads .env (ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY) into os.environ
from dataclasses import dataclass


@dataclass
class GenerationResult:
    provider: str
    model: str
    text: str
    stop_reason: str | None = None  # capture so truncation (hit max_tokens) is detectable, not silent
    truncated: bool = False


class BaseProvider:
    name: str = "base"

    def generate(self, system: str, user_prompt: str) -> GenerationResult:
        raise NotImplementedError


class AnthropicProvider(BaseProvider):
    """Model name intentionally configurable -- verified current as of 2026-09-16:
    current flagship reasoning tier is "claude-opus-5" (Claude 5 family: Opus 5 / Sonnet
    5 / Fable 5, plus Haiku 4.5). An earlier version of this file defaulted to
    "claude-opus-4-6" from a stale cached skill reference (~7 months old) -- caught only
    because the user asked "why not Fable" and prompted a re-check; Fable is a separate
    named tier in the same family, not the flagship-reasoning one this comparison wants."""

    name = "anthropic"

    def __init__(self, model: str = "claude-opus-5", max_tokens: int = 8000):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, system: str, user_prompt: str) -> GenerationResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return GenerationResult(
            provider=self.name,
            model=self.model,
            text=text,
            stop_reason=response.stop_reason,
            truncated=(response.stop_reason == "max_tokens"),
        )


class OpenAIProvider(BaseProvider):
    """Model name is intentionally configurable rather than hardcoded -- verify the
    current flagship model id at run time (checked developers.openai.com/api/docs/models
    on 2026-09-16: current flagship is "gpt-6-astra"; gpt-4o is a superseded 2024 model,
    don't default to it)."""

    name = "openai"

    def __init__(self, model: str = "gpt-6-astra", max_tokens: int = 8000):
        import openai

        self.client = openai.OpenAI()
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, system: str, user_prompt: str) -> GenerationResult:
        response = self.client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,  # gpt-6-astra rejects the older max_tokens param
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
        )
        choice = response.choices[0]
        text = choice.message.content or ""
        return GenerationResult(
            provider=self.name,
            model=self.model,
            text=text,
            stop_reason=choice.finish_reason,
            truncated=(choice.finish_reason == "length"),
        )


class GeminiProvider(BaseProvider):
    """Google Gemini via the google-genai SDK (`pip install google-genai`). Reads
    GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment.

    Model name is intentionally configurable, not hardcoded to one snapshot -- verify
    the current flagship Gemini model id at run time (Google's naming/versioning has
    changed repeatedly; don't trust a remembered id without checking). Checked
    ai.google.dev/gemini-api/docs/models on 2026-09-16: current flagship reasoning
    model is "gemini-3.1-pro-preview" (released preview 2026-02-19) -- note the
    "-preview" suffix, which means Google may rename/promote it to a stable id later;
    re-check before a long-running study locks in a model id for reproducibility."""

    name = "gemini"

    def __init__(self, model: str = "gemini-3.1-pro-preview", max_tokens: int = 8000):
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, system: str, user_prompt: str) -> GenerationResult:
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=self.max_tokens,
            ),
        )
        finish_reason = None
        if response.candidates:
            fr = response.candidates[0].finish_reason
            finish_reason = fr.name if hasattr(fr, "name") else str(fr)
        return GenerationResult(
            provider=self.name,
            model=self.model,
            text=response.text or "",
            stop_reason=finish_reason,
            truncated=(finish_reason == "MAX_TOKENS"),
        )


class LocalOllamaProvider(BaseProvider):
    """Talks to a locally hosted open-source model via Ollama's HTTP API
    (https://github.com/ollama/ollama). Point base_url at any other
    OpenAI/Ollama-compatible local server (vLLM, LM Studio, ...) instead."""

    name = "local"

    def __init__(self, model: str = "qwen2.5:72b", base_url: str | None = None):
        import requests

        self._requests = requests
        self.model = model
        self.base_url = base_url or os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:11434")

    def generate(self, system: str, user_prompt: str) -> GenerationResult:
        response = self._requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("message", {}).get("content", "")
        return GenerationResult(provider=self.name, model=self.model, text=text)


def call_with_retry(provider: BaseProvider, system: str, user_prompt: str, max_retries: int = 3) -> GenerationResult:
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return provider.generate(system, user_prompt)
        except Exception as exc:  # provider SDKs raise different exception types
            last_exc = exc
            time.sleep(min(2**attempt, 30))
    raise last_exc
