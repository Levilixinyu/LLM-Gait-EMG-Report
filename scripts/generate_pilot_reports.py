"""Generates LLM interpretive reports for the pilot subset (data/pilot_subset.json)
across the three provider arms (Claude / GPT / Gemini). Run from the project root:
`python3 scripts/generate_pilot_reports.py`. **Calls paid APIs -- do not run without
the user's go-ahead.**

PROMPT_VERSION v2, output data/reports_v2/. v1 outputs (data/reports/, v1_freeze/)
are historical results generated under the pre-audit extraction and must not be
touched.

Task identity, artifact validity and no-overwrite placement all come from
src/llm/generation_cache.py (audit round 2, R1/R2): the task hash covers subject/side,
full system+user prompts, provider/model/params, the reference id, data-file hashes
and the source-code manifest; existing artifacts are reused only if they pass the
full validity check (never on bare file existence), and stale files are preserved as
*.superseded-* rather than overwritten.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.figshare_loader import load_stroke_excel, load_control_excel
from src.features.mat_spatiotemporal import load_stroke_spatiotemporal, build_spatiotemporal_lookup
from src.features.pipeline import build_normative_reference_from_normalized, extract_summary_from_normalized
from src.llm.generation_cache import build_code_manifest, build_data_manifest
from src.llm.generation_runner import generate_batch
from src.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from src.llm.providers import AnthropicProvider, OpenAIProvider, GeminiProvider, call_with_retry

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "reports_v2"
PROMPT_VERSION = "v2"
REFERENCE_ID = "main_cohort_excel/all-controls"

CODE_FILES = [
    ROOT / "src" / "features" / "emg_signal.py",
    ROOT / "src" / "features" / "pipeline.py",
    ROOT / "src" / "features" / "figshare_loader.py",
    ROOT / "src" / "features" / "mat_spatiotemporal.py",
    ROOT / "src" / "features" / "kinematic.py",
    ROOT / "src" / "features" / "spatiotemporal.py",
    ROOT / "src" / "features" / "data_types.py",
    ROOT / "src" / "llm" / "prompt_templates.py",
    ROOT / "src" / "llm" / "providers.py",
    ROOT / "src" / "llm" / "generation_cache.py",
    ROOT / "src" / "llm" / "generation_runner.py",
    Path(__file__).resolve(),  # the entry script itself is part of the frozen config
]
DATA_FILES = [
    ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx",
    ROOT / "data" / "raw" / "PostStrokeAdults.xlsx",
    ROOT / "data" / "raw" / "MAT_normalizedData_PostStrokeAdults.mat",
    ROOT / "data" / "pilot_subset.json",
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pilot = json.loads((ROOT / "data" / "pilot_subset.json").read_text())
    print(f"Pilot subset: {len(pilot)} subjects")

    print("hashing code + data manifests...")
    code_manifest = build_code_manifest(CODE_FILES)
    data_manifest = build_data_manifest(DATA_FILES)

    controls = load_control_excel(str(ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx"))
    stroke = load_stroke_excel(str(ROOT / "data" / "raw" / "PostStrokeAdults.xlsx"))
    normative = build_normative_reference_from_normalized(controls, source="main_cohort_excel")
    st_lookup = build_spatiotemporal_lookup(
        load_stroke_spatiotemporal(str(ROOT / "data" / "raw" / "MAT_normalizedData_PostStrokeAdults.mat"))
    )
    print("Normative reference + spatiotemporal lookup built.")

    providers = [AnthropicProvider(), OpenAIProvider(), GeminiProvider()]
    trials_by_id = {(t.subject_id, t.side): t for t in stroke}

    batch_tasks = []
    for entry in pilot:
        subject_id, side = entry["subject_id"], entry["side"]
        trial = trials_by_id[(subject_id, side)]
        st = st_lookup.get((subject_id, side), {})
        summary = extract_summary_from_normalized(trial, normative=normative, **st)
        batch_tasks.append({
            "subject_id": subject_id,
            "side": side,
            "user_prompt": build_user_prompt(summary),
            "reference_id": REFERENCE_ID,
        })

    counters = generate_batch(
        batch_tasks, providers, OUT_DIR, PROMPT_VERSION, SYSTEM_PROMPT,
        data_manifest, code_manifest,
    )
    print(f"batch counters: {counters}")
    print("Done.")


if __name__ == "__main__":
    main()
