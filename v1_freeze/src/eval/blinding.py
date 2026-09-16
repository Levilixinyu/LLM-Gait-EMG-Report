"""De-identifies and randomizes generated reports into per-subject rater packets,
keeping a separate answer key that must NOT be shared with raters until scoring
is complete (needed to unblind results for statistical analysis afterward)."""
from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path

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


def _build_strip_patterns(reports_dir: Path) -> list[re.Pattern]:
    """Adds exact-match patterns for every provider/model id actually present in the
    reports being processed, on top of the generic vendor-stem backstop -- guarantees
    coverage of whatever models were actually used, not a hardcoded guess that goes
    stale every time the model roster changes."""
    exact_terms = set()
    for f in reports_dir.glob("*.json"):
        record = json.loads(f.read_text())
        for field in ("provider", "model"):
            value = record.get(field)
            if value:
                exact_terms.add(value)
    exact_patterns = [re.compile(re.escape(term), re.IGNORECASE) for term in exact_terms]
    return VENDOR_STEM_PATTERNS + exact_patterns


def _strip_identifying_tokens(text: str, patterns: list[re.Pattern]) -> str:
    for pattern in patterns:
        text = pattern.sub("[model]", text)
    return text


def create_rating_packets(reports_dir: str, out_dir: str, seed: int = 42) -> None:
    reports_path = Path(reports_dir)
    out_path = Path(out_dir)
    packets_dir = out_path / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    key_rows = []
    strip_patterns = _build_strip_patterns(reports_path)

    by_subject: dict[str, list[Path]] = {}
    for f in reports_path.glob("*.json"):
        record = json.loads(f.read_text())
        by_subject.setdefault(record["subject_id"], []).append(f)

    anon_counter = 0
    for subject_id, files in sorted(by_subject.items()):
        rng.shuffle(files)
        subject_packet = []
        for f in files:
            record = json.loads(f.read_text())
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
                    "source_file": str(f),
                }
            )
        (packets_dir / f"{subject_id}.json").write_text(json.dumps(subject_packet, indent=2, ensure_ascii=False))

    key_path = out_path / "answer_key_DO_NOT_SHARE.csv"
    with open(key_path, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["anon_id", "subject_id", "provider", "model", "prompt_version", "source_file"]
        )
        writer.writeheader()
        writer.writerows(key_rows)

    # shared rubric doc, referenced once by raters while going through per-subject
    # packets -- not duplicated into every packet file
    rubric_path = out_path / "rubric.json"
    rubric_path.write_text(
        json.dumps({"likert_dimensions": rubric_as_dict(), "safety_critical_checks": safety_checks_as_dict()}, indent=2)
    )
