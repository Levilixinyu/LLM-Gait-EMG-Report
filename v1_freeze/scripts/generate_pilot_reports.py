"""Generates LLM interpretive reports for the pilot subset (data/pilot_subset.json)
across the three provider arms (Claude / GPT / Gemini). Run from the project root with
the venv active: `python3 scripts/generate_pilot_reports.py`.

Prints progress to stdout as it goes (one line per subject x provider) since some
providers (Gemini in particular, likely due to default extended thinking) can take a
couple of minutes per call -- silent waiting for tens of minutes is not reassuring.
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
from src.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from src.llm.providers import AnthropicProvider, OpenAIProvider, GeminiProvider, call_with_retry

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "reports"
PROMPT_VERSION = "v1"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pilot = json.loads((ROOT / "data" / "pilot_subset.json").read_text())
    print(f"Pilot subset: {len(pilot)} subjects")

    controls = load_control_excel(str(ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx"))
    stroke = load_stroke_excel(str(ROOT / "data" / "raw" / "PostStrokeAdults.xlsx"))
    normative = build_normative_reference_from_normalized(controls)
    st_lookup = build_spatiotemporal_lookup(
        load_stroke_spatiotemporal(str(ROOT / "data" / "raw" / "MAT_normalizedData_PostStrokeAdults.mat"))
    )
    print("Normative reference + spatiotemporal lookup built.")

    providers = [AnthropicProvider(), OpenAIProvider(), GeminiProvider()]

    trials_by_id = {(t.subject_id, t.side): t for t in stroke}

    total = len(pilot) * len(providers)
    done = 0
    for entry in pilot:
        subject_id, side = entry["subject_id"], entry["side"]
        trial = trials_by_id[(subject_id, side)]
        st = st_lookup.get((subject_id, side), {})
        summary = extract_summary_from_normalized(trial, normative=normative, **st)
        user_prompt = build_user_prompt(summary)

        for provider in providers:
            fname = OUT_DIR / f"{subject_id}_{side}__{provider.name}__{provider.model}__{PROMPT_VERSION}.json"
            if fname.exists():
                done += 1
                print(f"[{done}/{total}] {subject_id}_{side} x {provider.name}: SKIP (already exists)")
                continue

            t0 = time.time()
            try:
                result = call_with_retry(provider, SYSTEM_PROMPT, user_prompt)
                record = {
                    "subject_id": subject_id,
                    "side": side,
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
                print(f"[{done}/{total}] {subject_id}_{side} x {provider.name}: OK ({elapsed:.1f}s, {len(result.text)} chars, stop={result.stop_reason}){flag}")
            except Exception as exc:
                done += 1
                print(f"[{done}/{total}] {subject_id}_{side} x {provider.name}: FAILED - {type(exc).__name__}: {exc}")

    print("Done.")


if __name__ == "__main__":
    main()
