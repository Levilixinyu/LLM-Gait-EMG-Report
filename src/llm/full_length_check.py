"""Predeclared nonclinical, representative-length technical check only."""
from importlib.metadata import version
import json
from pathlib import Path

from .compatibility_check import PACKAGES
from .formal_generation import digest
from .formal_release import ROOT, BASE, read, sha

SCOPE = "Synthetic full-length output check"
PACKAGE = BASE / "full_length_check_v1"
LIVE_ROOT = ROOT / "data/compatibility_checks/full_length_v1"


def synthetic_input():
    system = (
        "You are preparing an engineering report from wholly fictional bench-sensor data. "
        "There are no human participants, clinical cases or real machine measurements. "
        "Use only the values supplied. Separate numeric description, reference comparisons, "
        "interpretation limits and follow-up measurements. Do not infer failure, safety, "
        "causality, statistical significance or a severity class. Return four numbered sections "
        "in English, aiming for 900 to 1100 words in total. Do not reproduce the audit log."
    )
    parts = [
        "SYNTHETIC FULL-LENGTH TECHNICAL CHECK. Every value and identifier below is invented.",
        "The index is a normalized acquisition window from 0 to 100, not a mechanical phase sequence.",
        "Seven optical bench channels A-G have unitless, within-run normalized envelopes. Magnitudes cannot establish physical force or comparisons of absolute sensor output across channels.",
        "The empirical reference came from 120 invented runs at speeds 1.0-2.0 units/s. This target run is at 0.4 units/s; no speed-matched reference is supplied. There is no experimental causal comparison or significance test.",
        "A reported longest retained interval and rounded coverage summarize a thresholded envelope. Runs shorter than 3 percent were omitted; the method does not prove absence of brief below-threshold gaps. A boundary is a window boundary, not a physiological or mechanical event.",
        "The maximum absolute standardized deviation is relative to a window-position-specific reference mean and is not the envelope maximum. The sign of deviation is provided separately. Empirical per-channel upper endpoints span 3.7-4.5, but the individual endpoint assigned to each channel is intentionally not supplied.",
        "A composite displacement difference of 6.2 lies between the empirical median 5.0 and upper endpoint 10.0. It uses four angular sensors only, not speed or a timing symmetry index. Displacement summaries are reference-relative differences, not restriction diagnoses.",
        "Four displacement sensors H-K have differences 2.0, 3.1, 4.0, 2.6 units; excursions 8, 10, 12, 9 units. A within-run two-step spacing index is -0.8 percent. Do not infer complete system symmetry from that single index.",
        "Pairwise envelope-overlap values A-B=31, C-D=44, E-F=27 are compared with invented empirical bands 20-40, 25-50, 10-35. An in-band value does not establish normal function, useful stabilization or absence of other defects.",
    ]
    for i, channel in enumerate("ABCDEFG"):
        parts.append(f"Channel {channel}: max absolute standardized deviation {2.8 + i * 0.6:.1f}; "
                     f"envelope {'above' if i % 2 == 0 else 'below'} reference mean at index {11 + i * 12} percent; "
                     f"rounded above-threshold coverage {70 + i * 5} percent; retained interval {i * 2}-{100 - i} percent. "
                     "Describe observed direction and numeric scope; avoid assigning a named process phase or failure mechanism.")
    parts.append("Synthetic acquisition audit log follows. Entries describe data handling, not additional reference evidence.")
    index = 0
    while len((system + "\n" + "\n".join(parts)).encode()) < 14000:
        index += 1
        parts.append(f"Invented audit entry {index:03d}: channel {'ABCDEFG'[index % 7]} retained acquisition window {index:03d}; "
                     "time normalization and within-run scaling were checked by the fictional logger. "
                     "This entry supplies no new phase event, matched reference, calibration guarantee, physical mechanism, significance test or severity threshold.")
    parts.append(
        "Write exactly four numbered sections: 1. Main descriptive findings, covering the seven channels and angular summaries. "
        "2. Threshold extent and overlap observations, distinguishing them from function and event timing. "
        "3. Reference applicability and limitations, including the speed mismatch and unavailable channel-specific upper endpoints. "
        "4. Follow-up data questions that do not presuppose an unsupported fault. Aim for 900-1100 words, avoid a verbatim table/log dump, "
        "and do not mention vendors or compare models. This is a text-interface exercise, not a clinical judgment."
    )
    return system, "\n\n".join(parts)


def build_plan():
    from .formal_batch import schedule
    proposals = {p["provider"]: p for p in read(BASE / "generation_preflight_v1/provider_candidates.json")["providers"]}
    system, user = synthetic_input()
    sources = {name: sha(ROOT / name) for name in (
        "src/llm/full_length_check.py", "src/llm/formal_batch.py", "src/llm/formal_release.py",
        "src/llm/formal_generation.py", "src/llm/formal_providers.py", "src/llm/compatibility_check.py",
        "scripts/run_full_length_check.py", "docs/formal_study/generation_preflight_v1/provider_candidates.json")}
    tasks = [{"slot_id": f"{case}_{p}", "case_id": case, "provider": p,
              "model": proposals[p]["model"], "parameters": proposals[p]["parameters"],
              "system_prompt": system, "user_prompt": user, "input_pair_sha256": digest([system, user])}
             for case, p in schedule(["synthetic_full_length_v1"])]
    return {"version": "synthetic-full-length-v1", "scope": SCOPE, "tasks": tasks,
            "schedule_seed": 20260919, "sdk_versions": {p: version(p) for p in PACKAGES},
            "source_sha256": sources, "max_attempts_per_slot": 3, "max_total_attempts": 9,
            "attempt_deadline_seconds": 600, "budget_limit_usd": 4.0,
            "reservation_usd_per_attempt": {"anthropic": .28, "openai": .6, "gemini": .128},
            "input_token_reservation_per_attempt": 16000,
            "three_attempt_reservation_usd": 3.024,
            "rates_source_sha256": sha(BASE / "compatibility_check_v1/plan.json"),
            "cost_scope": "Registered rate assumptions, not a hard provider billing cap; taxes/account fees excluded",
            "input_utf8_bytes": len(system.encode()) + len(user.encode()),
            "response_length_instruction": "Aim for 900-1100 English words; engineering stress target, not a clinical quality score",
            "acceptance": ["Correct task attribution and retained full visible stream", "Normal stream completion",
                "No token-limit finish", "Nonempty report text", "Response model, finish reason and usage recorded"],
            "minimum_words_for_length_evidence": 900,
            "word_count_policy": "Count whitespace-delimited words. Fewer than 900 makes length adequacy inconclusive even after normal completion. A longer complete response may support the technical check. Never retry for length or quality.",
            "formal_generation_authorized": False,
            "configuration_change_policy": "No automatic cap escalation or quality-based retry. Document any new proposal before further calls."}
