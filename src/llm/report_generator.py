"""DEPRECATED v1-era generation library -- kept only so historical code paths remain
readable. Do NOT use for new generation (audit round 2, R1): it predates the
generation_cache task-identity/validity system, defaults to prompt_version v1, and
its original version silently overwrote same-named outputs. New entry points are
scripts/generate_pilot_reports.py and scripts/generate_control_spotcheck.py, both
built on src/llm/generation_cache.py.

The only behavioral change made here post-audit: it now REFUSES to overwrite an
existing file instead of clobbering it.
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
    import warnings

    warnings.warn(
        "report_generator.generate_reports is deprecated; use the v2 scripts built on "
        "generation_cache (audit R1)",
        DeprecationWarning,
        stacklevel=2,
    )
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    system = COT_SYSTEM_PROMPT if use_cot else SYSTEM_PROMPT

    for summary in summaries:
        user_prompt = build_user_prompt(summary)
        for provider in providers:
            fname = out_path / f"{summary.subject_id}__{provider.name}__{provider.model}__{prompt_version}.json"
            if fname.exists():
                print(f"REFUSING to overwrite existing {fname.name} (deprecated path has no "
                      f"validity checking; use the v2 scripts)")
                continue
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
            fname.write_text(json.dumps(record, indent=2, ensure_ascii=False))
