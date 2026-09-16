"""Blinded expert-rating rubric for comparing LLM-generated interpretive gait reports."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RubricDimension:
    key: str
    label: str
    description: str
    scale: tuple[int, int] = (1, 5)


RUBRIC: list[RubricDimension] = [
    RubricDimension(
        key="clinical_accuracy",
        label="Clinical accuracy",
        description=(
            "Are the interpretive statements consistent with the numeric findings and "
            "standard gait-analysis knowledge? (1 = frequent incorrect interpretation, "
            "5 = fully accurate)"
        ),
    ),
    RubricDimension(
        key="completeness",
        label="Completeness",
        description=(
            "Does the report address all clinically salient findings present in the "
            "input data, without omitting notable ones? (1 = major omissions, 5 = complete)"
        ),
    ),
    RubricDimension(
        key="hallucination",
        label="Freedom from unsupported claims",
        description=(
            "Does the report avoid stating findings, values, or muscles not present in "
            "the input data? (1 = frequent fabrication, 5 = no unsupported claims)"
        ),
    ),
    RubricDimension(
        key="usefulness",
        label="Clinical usefulness / readability",
        description=(
            "Would this report, as a first draft, save a clinician meaningful time "
            "writing the interpretive section? (1 = not useful, 5 = highly useful as-is)"
        ),
    ),
]


def rubric_as_dict() -> list[dict]:
    return [{"key": d.key, "label": d.label, "description": d.description, "scale": d.scale} for d in RUBRIC]


@dataclass
class SafetyCriticalCheck:
    key: str
    label: str
    description: str


SAFETY_CRITICAL_CHECKS: list[SafetyCriticalCheck] = [
    SafetyCriticalCheck(
        key="side_consistency",
        label="Correct side/limb throughout",
        description=(
            "Does the report consistently refer to the correct limb (paretic vs "
            "non-paretic, as given in the input) everywhere in the text, with no side "
            "inversion? Pass/Fail, not a Likert score -- a single side-flip makes a "
            "report clinically dangerous regardless of everything else it gets right, so "
            "it shouldn't be averaged away inside a 1-5 accuracy score."
        ),
    ),
    SafetyCriticalCheck(
        key="normal_abnormal_direction",
        label="Correct normal-vs-abnormal direction",
        description=(
            "For every finding the report characterizes as normal or abnormal (e.g. a "
            "GVS near baseline called 'within normative limits', an SD deviation of 4+ "
            "called 'markedly deviant'), does the direction match the input data -- no "
            "case where a normal finding is called abnormal, or an abnormal one called "
            "normal? Pass/Fail."
        ),
    ),
]
# Design precedent: a hybrid rule+LLM electrodiagnostic reporting system (PMC, two-center
# retrospective eval of EMG/NCS report drafting) tracks side-inversion and normal/abnormal
# -inversion as a separate binary safety flag, outside their main agreement metric, for
# exactly this reason -- these errors are rare but severe enough that averaging them into
# a continuous score hides them. Same logic applies here even though our task (free-text
# interpretive narrative) and their task (constrained diagnostic-label selection) differ.


def safety_checks_as_dict() -> list[dict]:
    return [{"key": c.key, "label": c.label, "description": c.description} for c in SAFETY_CRITICAL_CHECKS]
