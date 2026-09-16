"""Shared batch-generation runner used by BOTH real entry points
(scripts/generate_pilot_reports.py and scripts/generate_control_spotcheck.py).

File conventions this runner owns (audit round 5, F1): the report directory's ROOT
contains ONLY report artifacts (`<subject>[_side]__<provider>__<model>__<version>.json`
plus their `*.superseded-*` archives). Batch metadata -- the frozen task manifest --
lives in `<out_dir>/_meta/task_manifest.json`, OUT of the packet selector's glob, so
the manifest can never be mistaken for a report. (The first integration wrote the
manifest into the root and every real generation->packaging run failed on
"blank/non-string report_text: task_manifest.json".)

Extracting this loop also makes the F1 acceptance honest: tests drive the SAME code
path the real mains use, with a fake provider -- not hand-written report JSONs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .generation_cache import (
    TaskSpec,
    artifact_name,
    existing_record_valid,
    place_record,
    record_from_result,
    task_hash,
)

META_DIR_NAME = "_meta"
MANIFEST_NAME = "task_manifest.json"


def manifest_path(out_dir: Path) -> Path:
    return Path(out_dir) / META_DIR_NAME / MANIFEST_NAME


def generate_batch(
    tasks: list[dict],
    providers: list,
    out_dir: Path,
    prompt_version: str,
    system_prompt: str,
    data_manifest: dict,
    code_manifest: dict,
    call_fn=None,
) -> dict:
    """tasks: [{subject_id, side, user_prompt, reference_id, extra_fields?}].
    providers: objects with .name/.model/.max_tokens and .generate(system, user).
    call_fn(provider, system, user) -> GenerationResult; defaults to
    providers.call_with_retry (injectable so tests use fake providers directly).
    Writes reports into out_dir and the frozen task manifest into out_dir/_meta/.
    Returns counters {generated, skipped, failed, superseded}."""
    from .providers import call_with_retry

    call = call_fn or call_with_retry
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    counters = {"generated": 0, "skipped": 0, "failed": 0, "superseded": 0}
    manifest_tasks = []
    total = len(tasks) * len(providers)
    done = 0

    for task in tasks:
        for provider in providers:
            spec = TaskSpec(
                subject_id=task["subject_id"],
                side=task.get("side"),
                provider=provider.name,
                model=provider.model,
                prompt_version=prompt_version,
                system_prompt=system_prompt,
                user_prompt=task["user_prompt"],
                generation_params={"max_tokens": provider.max_tokens},
                reference_id=task.get("reference_id", ""),
                data_manifest=data_manifest,
                code_manifest=code_manifest,
            )
            manifest_tasks.append({
                "subject_id": spec.subject_id, "side": spec.side,
                "provider": spec.provider, "model": spec.model,
                "prompt_version": prompt_version, "task_hash": task_hash(spec),
            })
            fname = out_dir / artifact_name(spec)
            label = f"{spec.subject_id}{'_' + spec.side if spec.side else ''} x {provider.name}"
            ok, reason = existing_record_valid(fname, spec)
            if ok:
                done += 1
                counters["skipped"] += 1
                print(f"[{done}/{total}] {label}: SKIP (valid, same task hash)")
                continue
            if fname.exists():
                print(f"    {fname.name}: existing artifact not reusable ({reason}) -- will supersede")

            t0 = time.time()
            try:
                result = call(provider, system_prompt, task["user_prompt"])
                record = record_from_result(spec, result)
                for k, v in (task.get("extra_fields") or {}).items():
                    record[k] = v
                superseded = place_record(fname, record)
                if superseded:
                    counters["superseded"] += 1
                counters["generated"] += 1
                done += 1
                flag = " *** TRUNCATED ***" if result.truncated else ""
                sup = f" (old kept as {superseded.name})" if superseded else ""
                print(f"[{done}/{total}] {label}: OK ({time.time() - t0:.1f}s, "
                      f"{len(result.text)} chars, stop={result.stop_reason}, "
                      f"resp_model={result.response_model}){flag}{sup}")
            except Exception as exc:
                counters["failed"] += 1
                done += 1
                print(f"[{done}/{total}] {label}: FAILED - {type(exc).__name__}: {exc}")

    mp = manifest_path(out_dir)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps({"prompt_version": prompt_version, "tasks": manifest_tasks}, indent=2))
    print(f"task manifest written to {META_DIR_NAME}/{MANIFEST_NAME} ({len(manifest_tasks)} tasks).")
    return counters
