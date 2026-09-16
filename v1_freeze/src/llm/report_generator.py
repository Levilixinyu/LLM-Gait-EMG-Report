"""Batch-generates LLM reports for a set of patient feature summaries across one or
more providers, saving each output with metadata for later de-identified blinded rating.

For larger-scale runs on the Anthropic arm, swap AnthropicProvider calls for the
Message Batches API (50% cost reduction, async) once prompt/report format is finalized --
see the claude-api skill's batches.md for the pattern.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from ..features.data_types import PatientFeatureSummary
from .prompt_templates import COT_SYSTEM_PROMPT, SYSTEM_PROMPT, build_user_prompt
from .providers import BaseProvider, call_with_retry


def generate_reports(
    summaries: list[PatientFeatureSummary],
    providers: list[BaseProvider],
    out_dir: str,
    use_cot: bool = False,
    prompt_version: str = "v1",
) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    system = COT_SYSTEM_PROMPT if use_cot else SYSTEM_PROMPT

    for summary in summaries:
        user_prompt = build_user_prompt(summary)
        for provider in providers:
            result = call_with_retry(provider, system, user_prompt)
            record = {
                "subject_id": summary.subject_id,
                "provider": result.provider,
                "model": result.model,
                "prompt_version": prompt_version,
                "use_cot": use_cot,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "report_text": result.text,
                "stop_reason": result.stop_reason,
                "truncated": result.truncated,
            }
            if result.truncated:
                print(f"WARNING: {summary.subject_id} x {result.provider} was truncated (hit max_tokens)")
            fname = out_path / f"{summary.subject_id}__{result.provider}__{result.model}__{prompt_version}.json"
            fname.write_text(json.dumps(record, indent=2, ensure_ascii=False))
