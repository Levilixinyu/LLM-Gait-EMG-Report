"""Shared task-identity, artifact-validity and safe-placement logic for ALL report
generation entry points (audit round 2, R1/R2).

Why this exists: v2's first cache attempt hashed only (prompt_version, system prompt,
model, a partial source-file list) and skipped on bare parse-success -- the audit
demonstrated wrong-subject inputs, whitespace-only texts and edits to unhashed source
files all slipping through. The rules here:

- A task's identity covers WHO (subject/side), WHAT (full system + user prompt),
  HOW (provider, model, generation params), AGAINST WHAT (reference id, data
  manifest) and WITH WHICH CODE (source manifest). Any change => new hash.
- An existing artifact is reusable only if it parses, its task hash matches, its
  subject/side match both the spec and the filename, its text is non-blank, its
  stop reason is an explicit per-provider success value, and it is not truncated.
- Placement never overwrites: a stale/invalid file is renamed to
  `<name>.superseded-<UTC timestamp>.json` before the new record is written.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

SUCCESS_STOP_REASONS = {
    "anthropic": {"end_turn"},
    "openai": {"stop"},
    "gemini": {"STOP"},
}


@dataclass
class TaskSpec:
    subject_id: str
    side: str | None
    provider: str
    model: str
    prompt_version: str
    system_prompt: str
    user_prompt: str
    generation_params: dict = field(default_factory=dict)
    reference_id: str = ""  # e.g. "main_cohort_excel/all" or "main_cohort_excel/loo:Sub49"
    data_manifest: dict = field(default_factory=dict)  # file name -> sha256
    code_manifest: dict = field(default_factory=dict)  # file name -> sha256


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_code_manifest(paths: list[Path]) -> dict:
    return {p.name: sha256_file(p) for p in sorted(paths)}


def build_data_manifest(paths: list[Path]) -> dict:
    return {p.name: sha256_file(p) for p in sorted(paths)}


def task_hash(spec: TaskSpec) -> str:
    canonical = json.dumps(asdict(spec), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:24]


def artifact_name(spec: TaskSpec) -> str:
    side = f"_{spec.side}" if spec.side else ""
    return f"{spec.subject_id}{side}__{spec.provider}__{spec.model}__{spec.prompt_version}.json"


def record_from_result(spec: TaskSpec, result) -> dict:
    """result: providers.GenerationResult (or anything with the same attributes)."""
    return {
        "subject_id": spec.subject_id,
        "side": spec.side,
        "provider": spec.provider,
        "model": spec.model,
        "prompt_version": spec.prompt_version,
        "task_hash": task_hash(spec),
        "reference_id": spec.reference_id,
        "generation_params": spec.generation_params,
        "data_manifest": spec.data_manifest,
        "code_manifest": spec.code_manifest,
        "system_prompt": spec.system_prompt,
        "user_prompt": spec.user_prompt,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "report_text": result.text,
        "stop_reason": result.stop_reason,
        "truncated": result.truncated,
        "response_model": getattr(result, "response_model", None),
        "request_id": getattr(result, "request_id", None),
        "response_id": getattr(result, "response_id", None),
        "usage": getattr(result, "usage", None),
    }


def existing_record_valid(path: Path, spec: TaskSpec) -> tuple[bool, str]:
    """Reuse-eligibility check for an existing artifact. Returns (ok, reason).
    Malformed content of ANY shape must yield (False, reason), never an exception --
    a corrupt file aborting the whole batch is worse than regenerating one task
    (audit round 3, T4: a JSON list crashed this with AttributeError)."""
    if not path.exists():
        return False, "missing"
    try:
        record = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False, "unparseable"
    if not isinstance(record, dict):
        return False, "not a JSON object"
    if record.get("task_hash") != task_hash(spec):
        return False, "task hash mismatch (input/reference/params/code changed)"
    if record.get("subject_id") != spec.subject_id or record.get("side") != spec.side:
        return False, "subject/side mismatch vs spec"
    if artifact_name(spec) != path.name:
        return False, "filename does not match spec"
    text = record.get("report_text")
    if not isinstance(text, str) or not text.strip():
        return False, "blank or non-string report text"
    allowed = SUCCESS_STOP_REASONS.get(spec.provider)
    stop = record.get("stop_reason")
    if allowed is not None:
        if stop not in allowed:
            return False, f"stop_reason {stop!r} not an explicit success value"
    elif not stop:
        return False, "missing stop_reason"
    if record.get("truncated"):
        return False, "truncated"
    return True, "valid"


def place_record(path: Path, record: dict, timestamp: str | None = None) -> Path | None:
    """Write the record; if a file already exists at path, preserve it first as
    `<stem>.superseded-<ts>[-N].json` (audit R2: config changes must not silently
    overwrite same-named records). The archive name is made UNIQUE with a counter
    suffix -- second-resolution timestamps alone lose history when supersedes happen
    within the same second (audit round 3, T3). Returns the superseded path if one
    was made. `timestamp` is injectable for tests."""
    superseded = None
    if path.exists():
        ts = timestamp or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        candidate = path.with_name(f"{path.stem}.superseded-{ts}.json")
        n = 2
        while candidate.exists():
            candidate = path.with_name(f"{path.stem}.superseded-{ts}-{n}.json")
            n += 1
        superseded = candidate
        path.rename(superseded)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
    return superseded
