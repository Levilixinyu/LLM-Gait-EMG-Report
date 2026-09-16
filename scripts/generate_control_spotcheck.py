"""HEALTHY-control robustness spot-check, v2 entry point. **Calls paid APIs -- do not
run without the user's go-ahead.**

Post-audit framing (handoff v2 §8.6 / P0-4): this is a LABEL-KNOWN interpretation
task ("how does the model discuss deviations when told the subject is healthy"), not
a hidden-label identification test; 4 subjects x 3 models is not 12 independent
cases, and no false-positive rate may be claimed from it.

Changes vs. the v1 script (audit round 2, R1):
- output to data/reports_control_spotcheck_v2/ with prompt_version=v2 -- the v1
  directory is historical and untouched;
- LEAVE-ONE-OUT reference: each tested control's deviations are computed against a
  reference built from the OTHER 137 controls, removing the self-inclusion the v1
  run had (each subject was ~1/138 of its own baseline);
- task identity / validity / no-overwrite placement from generation_cache (R2) --
  bare file existence no longer suppresses regeneration, and a config change can no
  longer emit new results under old names.
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
from src.llm.generation_cache import build_code_manifest, build_data_manifest
from src.llm.generation_runner import generate_batch
from src.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from src.llm.providers import AnthropicProvider, GeminiProvider, OpenAIProvider, call_with_retry

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "reports_control_spotcheck_v2"
PROMPT_VERSION = "v2"
SEED = 42
N_SUBJECTS = 4

CODE_FILES = [
    ROOT / "src" / "features" / "emg_signal.py",
    ROOT / "src" / "features" / "pipeline.py",
    ROOT / "src" / "features" / "figshare_loader.py",
    ROOT / "src" / "features" / "kinematic.py",
    ROOT / "src" / "features" / "spatiotemporal.py",
    ROOT / "src" / "features" / "data_types.py",
    ROOT / "src" / "llm" / "prompt_templates.py",
    ROOT / "src" / "llm" / "providers.py",
    ROOT / "src" / "llm" / "generation_cache.py",
    ROOT / "src" / "llm" / "generation_runner.py",
    Path(__file__).resolve(),  # the entry script itself is part of the frozen config
]
DATA_FILES = [ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx"]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("hashing code + data manifests...")
    code_manifest = build_code_manifest(CODE_FILES)
    data_manifest = build_data_manifest(DATA_FILES)

    controls = load_control_excel(str(ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx"))
    complete = [t for t in controls if all(not np.isnan(c).all() for c in t.emg_norm.values())]
    print(f"{len(complete)}/{len(controls)} controls have complete 7/7-muscle EMG data")

    rng = random.Random(SEED)
    rng.shuffle(complete)
    selected = complete[:N_SUBJECTS]
    print("Selected:", [t.subject_id for t in selected])

    providers = [AnthropicProvider(), OpenAIProvider(), GeminiProvider()]

    batch_tasks = []
    for trial in selected:
        # leave-one-out reference: exclude the tested subject from their own baseline
        loo_controls = [t for t in controls if t.subject_id != trial.subject_id]
        normative = build_normative_reference_from_normalized(
            loo_controls,
            source="main_cohort_excel",
            method="leave_one_out",
            excluded_subjects=(trial.subject_id,),
        )
        summary = extract_summary_from_normalized(trial, normative=normative)
        batch_tasks.append({
            "subject_id": trial.subject_id,
            "side": None,
            "user_prompt": build_user_prompt(summary),
            "reference_id": f"main_cohort_excel/loo:{trial.subject_id}",
            "extra_fields": {
                "group": "control",
                "reference_note": "leave-one-out (subject excluded from own reference)",
            },
        })

    counters = generate_batch(
        batch_tasks, providers, OUT_DIR, PROMPT_VERSION, SYSTEM_PROMPT,
        data_manifest, code_manifest,
    )
    print(f"batch counters: {counters}")
    print("Done.")


if __name__ == "__main__":
    main()
