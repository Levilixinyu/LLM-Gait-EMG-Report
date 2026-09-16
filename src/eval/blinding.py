"""De-identifies and randomizes generated reports into per-subject rater packets,
keeping a separate answer key that must NOT be shared with raters until scoring
is complete (needed to unblind results for statistical analysis afterward)."""
from __future__ import annotations

import csv
import json
import random
import re
import time
from pathlib import Path

from ..llm.generation_cache import SUCCESS_STOP_REASONS
from .rubric import rubric_as_dict, safety_checks_as_dict

# Backstop vendor/family stems -- kept broad and generic (not tied to one model
# generation) since exact model ids change frequently (this file has already needed
# fixing once this session when the roster moved from gpt-4o/claude-opus-4-6 to
# gpt-6-astra/claude-opus-5/gemini-3.1-pro-preview). The real defense is
# _build_strip_patterns() below, which derives exact-id patterns from whatever models
# actually appear in the reports being processed -- this list only catches a vendor
# name mentioned without the specific model id.
VENDOR_STEM_PATTERNS = [
    re.compile(r"\b(claude|opus|sonnet|haiku|fable|anthropic)\b", re.IGNORECASE),
    re.compile(r"\b(gpt|chatgpt|openai|astra)\b", re.IGNORECASE),
    re.compile(r"\b(gemini|google)\b", re.IGNORECASE),
    re.compile(r"\b(qwen|llama|deepseek|mistral)\b", re.IGNORECASE),
]


def _build_strip_patterns_from_records(records: list[dict]) -> list[re.Pattern]:
    """Adds exact-match patterns for every provider/model id present in the SELECTED
    records, on top of the generic vendor-stem backstop.

    Consumes the already-selected records rather than re-globbing the directory --
    the earlier directory-scan version parsed every *.json again, so a corrupt or
    non-object superseded archive that the selector had correctly excluded still
    crashed anonymization (audit round 4, T1 item 2).

    ORDER MATTERS (audit P1-4): exact/full model ids are replaced BEFORE vendor
    stems, longest id first, or a stem replacement inside a longer id breaks the
    exact match and leaks the version suffix ("[model]-3.1-pro-preview")."""
    exact_terms = set()
    for record in records:
        for field in ("provider", "model"):
            value = record.get(field)
            if value:
                exact_terms.add(value)
    exact_patterns = [
        re.compile(re.escape(term), re.IGNORECASE)
        for term in sorted(exact_terms, key=len, reverse=True)
    ]
    return exact_patterns + VENDOR_STEM_PATTERNS


def _build_strip_patterns(reports_dir: Path) -> list[re.Pattern]:
    """Legacy directory-scan variant kept for the blinding unit tests' API; skips
    superseded archives and unparseable/non-object files instead of crashing."""
    records = []
    for f in sorted(reports_dir.glob("*.json")):
        if ".superseded-" in f.name:
            continue
        try:
            record = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(record, dict):
            records.append(record)
    return _build_strip_patterns_from_records(records)


def _strip_identifying_tokens(text: str, patterns: list[re.Pattern]) -> str:
    for pattern in patterns:
        text = pattern.sub("[model]", text)
    return text


class PacketSelectionError(ValueError):
    """Raised when the report set for packaging is not exactly what was expected --
    packaging must fail loudly rather than silently ship the wrong reports."""


def load_task_manifest(path) -> dict:
    """Loads a generation script's task_manifest.json into the
    (subject_id, provider) -> task_hash dict that create_rating_packets expects."""
    data = json.loads(Path(path).read_text())
    return {(t["subject_id"], t["provider"]): t["task_hash"] for t in data["tasks"]}


def _select_current_reports(
    reports_path: Path,
    prompt_version: str | None,
    expected_providers: set | None,
    expected_tasks: dict | None = None,
) -> dict:
    """Selects exactly the CURRENT, successful report per (subject, provider) --
    audit round 3, T1: superseded archives share the directory and previously
    entered the packets via the bare `*.json` glob (measured: 1 current + 1 old
    truncated report packaged as 2 rating items). Rules:

    - `*.superseded-*.json` archives are never candidates;
    - a candidate must be a JSON object with non-blank string report_text,
      truncated == False, a present stop_reason, and (when prompt_version is given)
      the matching prompt_version;
    - exactly ONE record per (subject, provider) -- duplicates raise;
    - when expected_providers is given, every subject must have exactly that
      provider set -- anything missing or extra raises.
    Invalid files are reported in the returned dict for the caller to surface."""
    selected: dict[str, dict] = {}
    skipped: list[str] = []
    for f in sorted(reports_path.glob("*.json")):
        if ".superseded-" in f.name:
            skipped.append(f"{f.name}: superseded archive")
            continue
        try:
            record = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            raise PacketSelectionError(f"unreadable report file: {f.name}")
        if not isinstance(record, dict):
            raise PacketSelectionError(f"report file is not a JSON object: {f.name}")
        text = record.get("report_text")
        if not isinstance(text, str) or not text.strip():
            raise PacketSelectionError(f"blank/non-string report_text: {f.name}")
        if record.get("truncated"):
            raise PacketSelectionError(f"truncated report present: {f.name}")
        subject_id, provider = record.get("subject_id"), record.get("provider")
        if not subject_id or not provider:
            raise PacketSelectionError(f"missing subject_id/provider: {f.name}")
        # per-provider explicit success codes -- "has some stop_reason" is not
        # success: e.g. an OpenAI content_filter finish with text and truncated=False
        # previously slipped into packets (audit round 4, T1 item 1)
        allowed = SUCCESS_STOP_REASONS.get(provider)
        if allowed is None:
            raise PacketSelectionError(
                f"unknown provider {provider!r} -- no success stop-reason set defined, "
                f"cannot verify completion status: {f.name}"
            )
        if record.get("stop_reason") not in allowed:
            raise PacketSelectionError(
                f"stop_reason {record.get('stop_reason')!r} is not a success value for "
                f"{provider} (allowed: {sorted(allowed)}): {f.name}"
            )
        if prompt_version is not None and record.get("prompt_version") != prompt_version:
            raise PacketSelectionError(
                f"prompt_version {record.get('prompt_version')!r} != expected {prompt_version!r}: {f.name}"
            )
        key = (subject_id, provider)
        # frozen task-manifest check: same version but a different experiment's input
        # (different user_prompt => different task hash) must not mix into one packet
        # run (audit round 4, T1 item 3). Each task matches ITS OWN expected hash --
        # hashes are not required to be equal across providers.
        if expected_tasks is not None:
            expected_hash = expected_tasks.get(key)
            if expected_hash is None:
                raise PacketSelectionError(f"task {key} not in the frozen expected-task manifest: {f.name}")
            if record.get("task_hash") != expected_hash:
                raise PacketSelectionError(
                    f"task_hash mismatch for {key} (record from a different input/reference/"
                    f"config than the frozen manifest): {f.name}"
                )
        bucket = selected.setdefault(subject_id, {})
        if provider in bucket:
            raise PacketSelectionError(
                f"duplicate report for {key}: {bucket[provider]['file'].name} and {f.name}"
            )
        bucket[provider] = {"file": f, "record": record}

    if expected_providers is not None:
        for subject_id, bucket in sorted(selected.items()):
            got = set(bucket)
            if got != set(expected_providers):
                raise PacketSelectionError(
                    f"{subject_id}: providers {sorted(got)} != expected {sorted(expected_providers)}"
                )
    if expected_tasks is not None:
        expected_subjects = {s for s, _ in expected_tasks}
        got_subjects = set(selected)
        if got_subjects != expected_subjects:
            raise PacketSelectionError(
                f"subject set mismatch vs manifest: got {sorted(got_subjects)}, "
                f"expected {sorted(expected_subjects)}"
            )
    return {"selected": selected, "skipped": skipped}


def create_rating_packets(
    reports_dir: str,
    out_dir: str,
    seed: int = 42,
    prompt_version: str | None = None,
    expected_providers: set | None = None,
    expected_tasks: dict | None = None,
) -> Path:
    """Package blinded rating packets from CURRENT reports only. Pass prompt_version,
    expected_providers and (for real runs) expected_tasks -- the frozen
    (subject, provider) -> task_hash manifest emitted by the generation scripts --
    which turn silent mis-selection into hard errors (audit rounds 3-4, T1).

    Publishing (audit round 5, F2): every run produces its own SELF-CONTAINED,
    never-reused batch directory `out_dir/batch-<UTC ts>[-N]/` holding packets/,
    answer_key_DO_NOT_SHARE.csv, rubric.json and packaging_manifest.json together.
    The whole batch is built in a staging directory and renamed into place as one
    unit; prior batches -- including their anonymous-ID answer keys, needed to trace
    old scores -- are never touched or overwritten. The answer key lives at the batch
    ROOT, beside (never inside) the packets/ subdirectory that goes to raters.
    Returns the published batch path."""
    reports_path = Path(reports_dir)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    selection = _select_current_reports(reports_path, prompt_version, expected_providers, expected_tasks)
    for note in selection["skipped"]:
        print(f"packaging: skipped {note}")

    selected_records = [e["record"] for bucket in selection["selected"].values() for e in bucket.values()]
    strip_patterns = _build_strip_patterns_from_records(selected_records)

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    batch_dir = out_path / f"batch-{ts}"
    n = 2
    while batch_dir.exists() or batch_dir.with_name(batch_dir.name + ".building").exists():
        batch_dir = out_path / f"batch-{ts}-{n}"
        n += 1
    staging = batch_dir.with_name(batch_dir.name + ".building")
    packets_staging = staging / "packets"
    packets_staging.mkdir(parents=True)

    rng = random.Random(seed)
    key_rows = []
    anon_counter = 0
    for subject_id, bucket in sorted(selection["selected"].items()):
        entries = [bucket[p] for p in sorted(bucket)]  # deterministic pre-shuffle order
        rng.shuffle(entries)
        subject_packet = []
        for entry in entries:
            record = entry["record"]
            anon_counter += 1
            anon_id = f"R{anon_counter:04d}"
            subject_packet.append(
                {"anon_id": anon_id, "report_text": _strip_identifying_tokens(record["report_text"], strip_patterns)}
            )
            key_rows.append(
                {
                    "anon_id": anon_id,
                    "subject_id": subject_id,
                    "provider": record["provider"],
                    "model": record["model"],
                    "prompt_version": record.get("prompt_version"),
                    "source_file": str(entry["file"]),
                }
            )
        (packets_staging / f"{subject_id}.json").write_text(json.dumps(subject_packet, indent=2, ensure_ascii=False))

    with open(staging / "answer_key_DO_NOT_SHARE.csv", "w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["anon_id", "subject_id", "provider", "model", "prompt_version", "source_file"]
        )
        writer.writeheader()
        writer.writerows(key_rows)

    # shared rubric doc, referenced once by raters while going through per-subject
    # packets -- not duplicated into every packet file
    (staging / "rubric.json").write_text(
        json.dumps({"likert_dimensions": rubric_as_dict(), "safety_critical_checks": safety_checks_as_dict()}, indent=2)
    )

    # provenance of this batch: what was expected and what was selected
    (staging / "packaging_manifest.json").write_text(json.dumps({
        "reports_dir": str(reports_path),
        "prompt_version": prompt_version,
        "expected_providers": sorted(expected_providers) if expected_providers else None,
        "expected_tasks": (
            [{"subject_id": s, "provider": p, "task_hash": h} for (s, p), h in sorted(expected_tasks.items())]
            if expected_tasks else None
        ),
        "n_subjects": len(selection["selected"]),
        "n_reports": len(key_rows),
        "seed": seed,
        "created_at": ts,
    }, indent=2))

    # unified publish: the complete batch appears atomically under its final name
    staging.rename(batch_dir)
    print(f"packaging: published batch {batch_dir.name}/ "
          f"({len(selection['selected'])} subjects, {len(key_rows)} reports)")
    return batch_dir
