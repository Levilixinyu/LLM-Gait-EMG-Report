"""Sanity checks: run the full feature-extraction + prompt-generation pipeline on
synthetic data (no LLM calls, no real dataset needed) and assert it doesn't crash
and produces plausible values."""
from __future__ import annotations

from src.features.pipeline import build_normative_reference, extract_patient_summary, to_json, to_prompt_text
from src.llm.prompt_templates import build_user_prompt
from tests.synthetic_data import make_synthetic_trial


def test_end_to_end():
    controls = [make_synthetic_trial(f"CTRL{i:02d}", group="control", seed=i) for i in range(5)]
    stroke_trial = make_synthetic_trial("STK01", group="stroke", seed=100)

    normative = build_normative_reference(controls)
    summary = extract_patient_summary(
        stroke_trial,
        normative=normative,
        gait_speed_m_s=0.62,
        cadence_steps_min=78.4,
        step_length_symmetry_index=18.3,
    )

    assert summary.subject_id == "STK01"
    assert len(summary.muscle_findings) == 4
    assert len(summary.joint_findings) == 3
    assert summary.gait_profile_score is not None and summary.gait_profile_score >= 0

    prompt_text = to_prompt_text(summary)
    assert "tibialis_anterior" in prompt_text
    assert "deviation score" in prompt_text

    full_prompt = build_user_prompt(summary)
    assert prompt_text in full_prompt

    payload = to_json(summary)
    assert payload["subject_id"] == "STK01"

    print(prompt_text)
    print(f"\nCCI findings: {summary.cci_findings}")


if __name__ == "__main__":
    test_end_to_end()
    print("\nOK: pipeline ran end-to-end on synthetic data.")
