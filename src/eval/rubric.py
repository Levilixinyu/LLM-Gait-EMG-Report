"""Blinded expert-rating rubric for comparing LLM-generated interpretive gait reports."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RubricDimension:
    key: str
    label: str
    description: str
    scale: tuple[int, int] = (1, 5)


# Rating conventions shared by all Likert dimensions (audit §8.6; user step-2 spec):
# - Judge against the case's data card: the exact model input, the curves, and the
#   reference card, which states WHICH reference applies (pooled main-cohort for
#   stroke cases; leave-one-out for the healthy case -- their calibration columns
#   differ and are both printed on the card). Never judge from report style alone.
# - TWO DISTINCT "NA" situations, never conflated:
#   (a) the MODEL correctly declares something indeterminate given the supplied data
#       -- that is CORRECT model behavior: score the dimension normally (often
#       favorably) and record it under model_indeterminate_handling=correct;
#   (b) the RATER cannot rate a dimension (material missing, outside expertise,
#       ambiguous rule) -- enter NA-cannot-rate with a reason; this is a statement
#       about the rating process, not about the model, and flags a material/rule gap
#       for the trial round to fix.
RUBRIC: list[RubricDimension] = [
    RubricDimension(
        key="clinical_accuracy",
        label="Clinical accuracy",
        description=(
            "Are the interpretive statements consistent with the numeric findings, the "
            "supplied metric definitions, and the case's applicable reference? Anchors: "
            "1 = multiple statements contradict the input or misapply references "
            "(e.g. calls an in-range CCI 'elevated', reads max-|z| by the 2-SD rule); "
            "2 = one clear contradiction plus several shaky readings; "
            "3 = no outright contradiction but several imprecise or reference-free "
            "characterizations; 4 = accurate with at most minor imprecision that would "
            "not mislead; 5 = every characterization traceable to the input and its "
            "stated references, including correct handling of caveated metrics. "
            "NA-cannot-rate allowed with reason."
        ),
    ),
    RubricDimension(
        key="completeness",
        label="Completeness",
        description=(
            "Does the report address the case checklist's must-describe findings? "
            "Anchors: 1 = misses most must-describe items; 2 = misses several "
            "including at least one central finding; 3 = covers the central findings "
            "but omits multiple secondary ones; 4 = covers all but 1-2 minor items; "
            "5 = every must-describe item addressed (including missing-data "
            "disclosures). Rate against the adjudicated checklist, not personal "
            "expectation. NA-cannot-rate allowed with reason."
        ),
    ),
    RubricDimension(
        key="hallucination",
        label="Freedom from unsupported claims",
        description=(
            "Does the report avoid stating findings/values/muscles not in the input, "
            "AND avoid the checklist's cannot-infer assertions (mechanisms, treatment, "
            "real-world function, cross-muscle strength)? Anchors: 1 = fabricated data "
            "or confident mechanism/treatment claims; 2 = at least one clear "
            "unsupported assertion stated as fact; 3 = no fabricated data but "
            "pathologizing language without reference basis; 4 = essentially clean, "
            "hedged appropriately; 5 = fully clean -- uncertain things are explicitly "
            "marked indeterminate or framed as questions. A correct indeterminate "
            "declaration by the model counts FOR this dimension, not against it. "
            "NA-cannot-rate allowed with reason."
        ),
    ),
    RubricDimension(
        key="usefulness",
        label="Clinical usefulness / readability",
        description=(
            "Would this report, as a first draft, save a clinician meaningful time "
            "writing the interpretive section? Anchors: 1 = rewriting from scratch "
            "would be faster; 2 = only fragments salvageable; 3 = usable skeleton but "
            "substantial editing needed; 4 = minor edits only; 5 = near-ready draft "
            "with well-prioritized findings. Length alone is not usefulness -- a "
            "longer report earns nothing for length per se. NA-cannot-rate allowed "
            "with reason."
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
            "For every finding the report characterizes as within or outside the "
            "reference, does the characterization respect the METRIC-SPECIFIC reference "
            "supplied in the input (e.g. per-muscle max-|z| healthy 95th percentiles, "
            "CCI healthy quantiles, composite-score quantiles) -- never the generic "
            "2-SD convention, which does not apply to these statistics? A value inside "
            "the supplied healthy range called abnormal, or far outside it called "
            "normal, is a Fail. If the input provides no applicable reference for a "
            "metric, the correct report behavior is to say the abnormality status is "
            "INDETERMINATE -- rate such statements as correct, and rate confident "
            "normal/abnormal claims without a reference as a Fail. Pass/Fail per "
            "report, with an 'indeterminate-handling correct' note."
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
