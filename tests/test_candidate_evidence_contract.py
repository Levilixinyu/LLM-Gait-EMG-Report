"""Regression checks for preprocessing provenance and prospective input boundaries."""
from dataclasses import asdict
import numpy as np
import openpyxl
from src.features.data_types import NormalizedTrialData
from src.features.emg_provenance import RELEASED_COHORT_EMG, RAW_PIPELINE_EMG
from src.features.figshare_loader import load_stroke_excel
from src.features.pipeline import extract_summary_from_normalized, extract_patient_summary
from src.llm.candidate_prompts import build_user_prompt, SYSTEM_PROMPT
from src.llm.prompt_templates import build_user_prompt as legacy_prompt
from tests.synthetic_data import make_synthetic_trial


def released_trial(processing=RELEASED_COHORT_EMG):
    return NormalizedTrialData('Sub01', 'stroke', 'P', {},
                               {'RF':np.linspace(0.05,0.6,1001)}, processing)


def test_released_curve_is_not_renormalized_for_candidate():
    trial=released_trial();before=trial.emg_norm['RF'].copy()
    summary=extract_summary_from_normalized(trial)
    before_summary=asdict(summary)
    prompt=build_user_prompt(summary)
    assert 'shared maximum across the available strides before averaging' in prompt
    assert 'individual strides are not independently rescaled' in prompt
    assert summary.muscle_findings[0].peak_amplitude_norm == 0.6
    assert 'above-threshold interval(s)' in prompt
    assert asdict(summary)==before_summary
    np.testing.assert_array_equal(trial.emg_norm['RF'],before)


def test_reference_membership_does_not_invent_processing_provenance():
    summary=extract_summary_from_normalized(released_trial(None))
    summary.reference_source='main_cohort_excel'
    text=build_user_prompt(summary)
    assert 'denominator and averaging order were not specified' in text
    assert 'shared maximum across' not in text
    assert '3.65 (ERS)' not in text


def test_raw_path_states_its_actual_order_without_release_claim():
    summary=extract_patient_summary(make_synthetic_trial('raw'))
    assert summary.emg_processing==RAW_PIPELINE_EMG
    text=build_user_prompt(summary)
    assert 'averages them, and then divides' in text
    assert 'uses a shared maximum' not in text
    assert all(np.isclose(m.peak_amplitude_norm,1) for m in summary.muscle_findings)


def test_loader_sets_provenance_from_source_not_reference(tmp_path):
    book=openpyxl.Workbook();sheet=book.active;sheet.title='Sub01'
    sheet.append(['Pside_RFnorm','Nside_RFnorm']);sheet.append([0.2,0.4]);sheet.append([0.3,0.5])
    path=tmp_path/'release.xlsx';book.save(path)
    trials=load_stroke_excel(str(path))
    assert len(trials)==2
    assert all(t.emg_processing==RELEASED_COHORT_EMG for t in trials)


def test_candidate_exposes_missing_speed_and_keeps_legacy_route_separate():
    summary=extract_summary_from_normalized(released_trial())
    new=build_user_prompt(summary);old=legacy_prompt(summary)
    assert 'Gait speed: not provided' in new
    assert 'Gait speed: not provided' not in old
    assert 'each cycle normalized' in old
    assert 'each cycle normalized' not in new
    assert 'limited-evidence-v3.1-candidate' in new
    assert 'Individual toe-off' in SYSTEM_PROMPT
    assert 'Do not assign stance/swing' in SYSTEM_PROMPT
    assert 'strength' in SYSTEM_PROMPT and 'stride-to-stride variability' in SYSTEM_PROMPT


def test_release_boundary_and_normalization_are_group_specific():
    stroke = extract_summary_from_normalized(released_trial())
    text = build_user_prompt(stroke)
    assert "side-, and muscle-specific" in text
    assert "paretic-side cycle runs from initial contact" in text
    control = NormalizedTrialData('Sub49', 'control', 'avg', {},
                                  {'RF': np.linspace(.05,.6,1001)}, RELEASED_COHORT_EMG)
    control_summary = extract_summary_from_normalized(control)
    control_summary.reference_source = "main_cohort_excel"
    text = build_user_prompt(control_summary)
    assert "initial-contact-aligned pooled cycle" in text
    assert "not numerically verified by the stroke audit" in text
    assert "Cadence: not provided" in text
    assert "not applicable (this task's paretic/non-paretic index" in text
    assert "general left/right step-length symmetry measure" in text
    assert "apply only to the stroke cohort" in text


def test_unknown_processing_never_acquires_a_release_event_anchor():
    summary = extract_summary_from_normalized(released_trial(None))
    summary.reference_source = 'main_cohort_excel'
    assert "cycle-defining event is not established" in build_user_prompt(summary)
    assert "cycle runs from initial contact" not in build_user_prompt(summary)


def test_speed_label_and_z_direction_get_interpretation_limits():
    summary = extract_summary_from_normalized(released_trial(), gait_speed_m_s=.83)
    text = build_user_prompt(summary)
    assert "speed band only, not measured walking independence" in text
    assert "Gait speed: 0.83" in text
    assert "not necessarily the time of peak envelope amplitude" in SYSTEM_PROMPT
    assert "physiologically normal co-activation" in SYSTEM_PROMPT
    assert "do not transfer values or thresholds" in SYSTEM_PROMPT
    assert "section 2 may simply state" in SYSTEM_PROMPT
