"""Prompt templates for generating LLM-drafted interpretive summaries of EMG/kinematic
gait findings. The system prompt is deliberately scoped to interpretive summary only
(no treatment prescriptions) to keep model output within a realistic pre-report drafting
role and reduce the surface for unsupported clinical claims."""
from __future__ import annotations

from ..features.data_types import PatientFeatureSummary
from ..features.pipeline import to_prompt_text

SYSTEM_PROMPT = """You are assisting a physical therapist / physiatrist by drafting the \
objective findings and interpretation section of a clinical gait analysis report, based \
strictly on quantitative EMG and kinematic data extracted from an instrumented gait \
analysis. You are NOT diagnosing the patient and you are NOT recommending treatment.

Rules:
- Base every statement only on the numeric findings provided. Do not invent muscles, \
joints, or values not present in the input.
- If a finding is ambiguous or the data is insufficient to interpret confidently, say so \
explicitly rather than guessing.
- Use standard gait-analysis terminology (e.g., "prolonged activation", "delayed onset", \
"co-contraction", "reduced range of motion").
- Do not suggest specific treatments, exercises, or interventions.

Structure your output in exactly these sections:
1. Objective Findings — a factual restatement of the key numeric findings.
2. Muscle Activation Pattern — interpretation of onset/offset timing, amplitude, and \
co-contraction findings relative to normative gait.
3. Gait Deviation Summary — interpretation of the kinematic / composite deviation score \
findings.
4. Areas for Further Clinical Assessment — findings that warrant closer clinical \
examination, phrased as questions/flags, not conclusions."""

COT_SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    + """

Before writing the final report, first reason step by step (inside a "Reasoning:" \
section) about what each finding suggests physiologically, then write the final report \
(inside a "Report:" section) using the 4-section structure above. Only the Report \
section will be shown to the clinician."""
)


def build_user_prompt(summary: PatientFeatureSummary) -> str:
    return (
        "Here are the quantitative gait analysis findings for one patient. "
        "Draft the report described in the system instructions.\n\n"
        f"{to_prompt_text(summary)}"
    )
