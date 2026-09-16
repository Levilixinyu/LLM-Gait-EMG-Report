"""T2 acceptance (audit round 3): the serialized reference description must come from
the reference's own metadata -- a leave-one-out reference says its real subject count
and exclusion; a small custom reference must NOT be captioned with main-cohort
calibration numbers. Synthetic NormalizedTrialData only -- no data files needed."""
from __future__ import annotations

import numpy as np

from src.features.data_types import NormalizedTrialData
from src.features.pipeline import (
    build_normative_reference_from_normalized,
    extract_summary_from_normalized,
    to_prompt_text,
)


def make_trial(subject_id, n_points=101, group="control", side="avg", seed=0):
    rng = np.random.default_rng(seed)
    phase = np.linspace(0, 1, n_points)
    curve = 0.5 + 0.4 * np.sin(2 * np.pi * phase) ** 2 + rng.normal(0, 0.02, n_points)
    return NormalizedTrialData(
        subject_id=subject_id, group=group, side=side,
        joint_angles={"KneeAngles": 30 + 20 * np.sin(2 * np.pi * phase)},
        emg_norm={"TA": np.clip(curve, 0, None)},
    )


def test_loo_reference_line_reports_actual_composition():
    controls = [make_trial(f"C{i:02d}", n_points=1001, seed=i) for i in range(6)]
    loo = [t for t in controls if t.subject_id != "C03"]
    normative = build_normative_reference_from_normalized(
        loo, source="main_cohort_excel", method="leave_one_out", excluded_subjects=("C03",)
    )
    subject = make_trial("C03", n_points=1001, seed=99)
    text = to_prompt_text(extract_summary_from_normalized(subject, normative=normative))
    assert "5 healthy subjects" in text          # actual n = 6 - 1, never the pool size
    assert "leave-one-out" in text
    assert "excluding C03" in text
    # cohort-background block may appear (calibration family is main cohort),
    # but it must be marked as background, and the actual-reference line governs
    assert "COHORT BACKGROUND" in text


def test_custom_reference_never_gets_main_cohort_calibration():
    controls = [make_trial(f"X{i}", n_points=101, seed=i) for i in range(3)]
    normative = build_normative_reference_from_normalized(controls)  # source unspecified
    subject = make_trial("P1", n_points=101, group="stroke", side="P", seed=50)
    summary = extract_summary_from_normalized(subject, normative=normative)
    assert summary.reference_source is None  # not main cohort
    text = to_prompt_text(summary)
    assert "3 healthy subjects" in text and "101 phase points" in text
    # main-cohort calibration claims must be absent; generic no-calibration text present
    assert "138 subjects" not in text
    assert "3.65" not in text and "4.61" not in text
    assert "NO calibrated healthy reference" in text


def test_main_cohort_source_still_gets_calibration_block():
    controls = [make_trial(f"C{i:02d}", n_points=1001, seed=i) for i in range(6)]
    normative = build_normative_reference_from_normalized(controls, source="main_cohort_excel")
    subject = make_trial("P1", n_points=1001, group="stroke", side="P", seed=50)
    summary = extract_summary_from_normalized(subject, normative=normative)
    assert summary.reference_source == "main_cohort_excel"
    text = to_prompt_text(summary)
    assert "6 healthy subjects (pooled)" in text
    assert "3.65 (ERS) to 4.61 (TA)" in text  # calibration attaches only here
