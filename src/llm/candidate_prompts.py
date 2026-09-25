"""Prospective limited-evidence candidate; not an approved scoring rubric.

Legacy prompt_templates and v2 serialized text remain available for historical
comparison. This module does not call providers or regenerate completed reports.
"""
from ..features.data_types import PatientFeatureSummary
from ..features.emg_provenance import (
    CANDIDATE_PROMPT_VERSION, RELEASED_COHORT_EMG, normalization_description,
    EMG_INTERPRETATION_LIMIT, cycle_boundary_description,
)
from ..features.pipeline import metric_definitions, to_prompt_text

SYSTEM_PROMPT = """Draft a research gait-report interpretation for a physical therapist
or physiatrist using only the supplied quantitative summary. This is a limited-evidence
interpretation task, not diagnosis or treatment selection.

Rules:
- Describe the participant's actual group and side, available findings, and missing
  channels accurately. Healthy-group membership does not prove normal physiology;
  deviations from an empirical reference do not by themselves establish disease.
- Treat detected EMG intervals and coverage as properties of an averaged envelope
  under the stated threshold and duration rule. Do not convert them into physiological
  onset, offset, duration, continuous contraction, or inactivity outside the intervals.
  You may describe reported coverage, retained intervals and boundary continuity at
  the mean-envelope level. Do not infer the same pattern in every individual stride.
  Say no below-threshold segment only when the supplied evidence establishes that;
  a rounded coverage value or no retained interval alone does not establish it.
- Individual toe-off and matched muscle-specific timing references are not supplied
  in this task. Use percentages of the analysis cycle. When the input explicitly
  identifies an initial-contact boundary, you may name that boundary or describe
  numerical proximity to it. Do not assign stance/swing, loading response, pre-swing,
  mid-stance or another event to a percentage, or substitute a conventional 60% split.
  Anatomical muscle actions may be named, but do not map an interval to a gait-phase
  function such as clearance, push-off or weight acceptance. Do not characterize
  timing as normal, early, delayed or prolonged without the required evidence.
- Respect the supplied normalization method. Relative envelope amplitude is not
  strength or force, and average curves do not establish stride-to-stride variability.
- Report CCI as a whole-cycle overlap index of normalized EMG envelopes. You may
  compare it with the supplied empirical interval or a supplied median, including
  proximity to an endpoint. Do not invent an unavailable median. Being within that
  interval does not establish physiologically normal co-activation or normal muscle
  function; being outside it does not establish pathological co-activation, stiffness,
  impaired control or a diagnosis. CCI is not simultaneous activation time, muscular
  force or a phase-specific result. It depends on normalization and envelope methods;
  do not transfer values or thresholds from other studies or algorithms.
- Describe GVS and GPS-like as summary differences from the stated reference.
  Neither localizes waveform direction or phase; ROM alone does not establish a
  clinical restriction without an appropriate comparison. Do not treat pooled
  calibration percentiles as matched leave-one-out normal limits.
- Where using a reference comparison, convey both limited comparability and the
  inability to establish a disease effect or clinical diagnosis from that comparison.
  One clear explanation per report is enough; age and speed need not be recited as
  separate checklist words. A speed inside an overall range does not prove that
  an appropriate matched reference exists. Apply these limits to controls as well.
- The location of maximum |z| is the largest standardized difference from the
  reference, not necessarily the time of peak envelope amplitude or a gait event.
  Above/below reference in an EMG row means relative to the phase-specific reference
  mean at that location, not relative to a healthy percentile limit.
- Preserve numerical direction and the displayed precision. Do not invent values,
  clinical severity grades, statistical significance, or unavailable reference values.
  Descriptive comparisons with supplied values remain allowed. Near-boundary rounded
  values do not justify classifying hidden unrounded values.
- Clinical follow-up questions may ask whether a mechanism or measurement issue
  exists; do not presuppose it has already been observed. Do not recommend treatment.

If EMG is unavailable, section 2 may simply state that envelope timing, amplitude
and CCI cannot be assessed. Reference-only plots do not provide patient EMG.

Use exactly these four sections:
1. Objective Findings
2. EMG Envelope and Threshold Findings
3. Kinematic and Reference Comparisons
4. Questions for Further Clinical Assessment
"""


def build_user_prompt(summary: PatientFeatureSummary) -> str:
    # Reference membership alone does not establish compatible amplitude processing.
    source = summary.reference_source if summary.emg_processing == RELEASED_COHORT_EMG else None
    definitions = metric_definitions(source).splitlines()
    for i, line in enumerate(definitions):
        if line.startswith("- EMG curves are"):
            definitions[i] = "- " + normalization_description(summary.emg_processing, summary.group) + " " + EMG_INTERPRETATION_LIMIT
        elif line.startswith("- Activation intervals"):
            definitions[i] = line.replace("Activation intervals", "Above-threshold intervals", 1).replace(
                "activity continuous across the cycle-defining event",
                "envelope remains above threshold across the cycle-defining event",
            )
        elif line.startswith("- Fields NOT included"):
            definitions[i] = (
                "- Additional source fields are outside this input. Age, sex and gait "
                "events may be available in the release; time post-stroke, stroke "
                "clinical scores and a non-paretic-side designation apply only to "
                "the stroke cohort, as applicable. Do not claim every listed field "
                "exists for every participant. Distinguish not supplied, not "
                "applicable and documented absent recordings."
            )
        elif line.startswith("- Step length symmetry index:") and summary.group == "control":
            definitions[i] = (
                "- The paretic/non-paretic step-length index used in this task is "
                "not applicable to controls. This does not imply that a general "
                "left/right step-length symmetry measure cannot be defined."
            )
    text = to_prompt_text(summary, include_definitions=False)
    text = text.replace("activation interval(s)", "above-threshold interval(s)")
    text = text.replace("active across cycle boundary", "above threshold across cycle boundary")
    text = text.replace("Muscle activation findings", "EMG envelope findings")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Gait speed:"):
            lines[i] += (
                " [The ambulation label denotes a speed band only, not measured "
                "walking independence, safety or real-world community mobility.]"
            )
    missing = []
    if summary.gait_speed_m_s is None:
        missing.append("Gait speed: not provided")
    if summary.cadence_steps_min is None:
        missing.append("Cadence: not provided")
    if summary.step_length_symmetry_index is None:
        missing.append(
            "Step length symmetry index: not applicable (this task's paretic/non-paretic index; control has no paretic side)"
            if summary.group == "control" else "Step length symmetry index: not provided"
        )
    lines[1:1] = missing
    text = "\n".join(lines)
    boundary = cycle_boundary_description(summary.emg_processing, summary.group, summary.affected_side)
    limits = (
        "Model-visible information boundary: the summary contains mean-curve metrics "
        "and algorithm-detected intervals, not individual toe-off, matched normal "
        "muscle timing, stride-level variability, raw-signal quality checks, or expert "
        "plots. Information not supplied here must not be described as absent from "
        "the source dataset. Gait-cycle percentages alone do not identify gait phases."
    )
    return ("Candidate interpretation version: " + CANDIDATE_PROMPT_VERSION +
            "\nDraft the four-section report using only this subject's supplied evidence.\n\n" +
            "\n".join(definitions) + "\n\n" + boundary + "\n\n" + limits + "\n\n" + text)
