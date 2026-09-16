"""Lightweight robustness spot-check (NOT the main pilot): generates LLM reports for a
handful of HEALTHY control subjects, to check whether each provider correctly avoids
inventing pathological findings when the underlying gait is normal -- a false-positive /
hallucination check, not part of the blinded rater evaluation.

Uses complete-EMG-data controls only. No spatiotemporal data (gait speed/cadence/step
length) is included -- that requires the able-bodied .mat file (~6GB), which was never
downloaded since it wasn't needed for the main pilot's normative reference (built
straight from the Excel EMG/kinematic data). extract_summary_from_normalized() and
to_prompt_text() already handle gait_speed_m_s=None etc. gracefully by omitting those
lines, so this is a deliberate, harmless scope limit for this spot-check, not a bug.

Normative reference is built from all 138 controls, including the ones being tested --
a very mild circularity (each tested subject is ~0.7% of their own baseline), acceptable
for a spot-check but worth a caveat if this ever gets used for anything more rigorous
than "does the model hallucinate pathology."

Run from project root with the venv active: `python3 scripts/generate_control_spotcheck.py`
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.figshare_loader import load_control_excel
from src.features.pipeline import build_normative_reference_from_normalized, extract_summary_from_normalized
from src.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from src.llm.providers import AnthropicProvider, GeminiProvider, OpenAIProvider, call_with_retry

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "reports_control_spotcheck"
PROMPT_VERSION = "v1"
SEED = 42
N_SUBJECTS = 4


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    controls = load_control_excel(str(ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx"))
    complete = [t for t in controls if all(not np.isnan(c).all() for c in t.emg_norm.values())]
    print(f"{len(complete)}/{len(controls)} controls have complete 7/7-muscle EMG data")

    rng = random.Random(SEED)
    rng.shuffle(complete)
    selected = complete[:N_SUBJECTS]
    print("Selected:", [t.subject_id for t in selected])

    normative = build_normative_reference_from_normalized(controls)
    print("Normative reference built.")

    providers = [AnthropicProvider(), OpenAIProvider(), GeminiProvider()]
    total = len(selected) * len(providers)
    done = 0

    for trial in selected:
        summary = extract_summary_from_normalized(trial, normative=normative)
        user_prompt = build_user_prompt(summary)

        for provider in providers:
            fname = OUT_DIR / f"{trial.subject_id}__{provider.name}__{provider.model}__{PROMPT_VERSION}.json"
            if fname.exists():
                done += 1
                print(f"[{done}/{total}] {trial.subject_id} x {provider.name}: SKIP (exists)")
                continue

            t0 = time.time()
            try:
                result = call_with_retry(provider, SYSTEM_PROMPT, user_prompt)
                record = {
                    "subject_id": trial.subject_id,
                    "group": "control",
                    "provider": result.provider,
                    "model": result.model,
                    "prompt_version": PROMPT_VERSION,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "report_text": result.text,
                    "stop_reason": result.stop_reason,
                    "truncated": result.truncated,
                }
                fname.write_text(json.dumps(record, indent=2, ensure_ascii=False))
                elapsed = time.time() - t0
                done += 1
                flag = " *** TRUNCATED ***" if result.truncated else ""
                print(f"[{done}/{total}] {trial.subject_id} x {provider.name}: OK ({elapsed:.1f}s, {len(result.text)} chars, stop={result.stop_reason}){flag}")
            except Exception as exc:
                done += 1
                print(f"[{done}/{total}] {trial.subject_id} x {provider.name}: FAILED - {type(exc).__name__}: {exc}")

    print("Done.")


if __name__ == "__main__":
    main()
