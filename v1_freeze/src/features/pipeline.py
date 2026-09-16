"""Orchestrates feature extraction from RawTrialData into a PatientFeatureSummary,
builds a normative reference from healthy-control trials, and converts a summary
into LLM-ready prompt text / JSON."""
from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np

from .data_types import JointFinding, MuscleFinding, NormalizedTrialData, PatientFeatureSummary, RawTrialData
from .emg_signal import (
    co_contraction_index,
    deviation_from_normative,
    normalize_amplitude,
    normalize_to_gait_cycle,
    onset_offset_pct_from_cycle,
    raw_to_envelope,
)
from .kinematic import gait_profile_score, gait_variable_score, range_of_motion, resample_to_gait_cycle
from .spatiotemporal import classify_ambulation

DEFAULT_ANTAGONIST_PAIRS = [
    ("tibialis_anterior", "gastrocnemius_medialis"),
    ("rectus_femoris", "biceps_femoris"),
]

# Short muscle codes as they appear in the Figshare post-processed Excel files
# (see figshare_loader.py) -- ankle and knee antagonist pairs.
DEFAULT_ANTAGONIST_PAIRS_SHORT = [("TA", "GAS"), ("RF", "BF")]


def _gait_cycle_event_times(trial: RawTrialData, side: str) -> list[float]:
    return trial.gait_events.get(f"heel_strike_{side}", [])


def build_normative_reference(control_trials: list[RawTrialData], events_side: str = "L") -> dict:
    """Aggregate healthy-control trials into normative mean/SD reference curves,
    keyed for use as the `normative` argument to extract_patient_summary()."""
    emg_cycles: dict[str, list] = {}
    joint_cycles: dict[str, list] = {}

    for trial in control_trials:
        events = _gait_cycle_event_times(trial, events_side)
        for muscle, raw in trial.emg.items():
            envelope = raw_to_envelope(raw, trial.fs_emg)
            cycles = normalize_to_gait_cycle(envelope, events, trial.fs_emg)
            if cycles.size == 0:
                continue
            norm_cycle = normalize_amplitude(cycles.mean(axis=0), method="peak")
            emg_cycles.setdefault(muscle, []).append(norm_cycle)
        for joint, angle in trial.joint_angles.items():
            cycles = resample_to_gait_cycle(angle, events, trial.fs_kinematic)
            if cycles.size == 0:
                continue
            joint_cycles.setdefault(joint, []).append(cycles.mean(axis=0))

    normative_emg = {m: (np.mean(c, axis=0), np.std(c, axis=0)) for m, c in emg_cycles.items()}
    normative_joint = {j: np.mean(c, axis=0) for j, c in joint_cycles.items()}
    return {"emg": normative_emg, "joint_angles": normative_joint}


def extract_patient_summary(
    trial: RawTrialData,
    normative: dict | None = None,
    antagonist_pairs: list[tuple[str, str]] | None = None,
    gait_speed_m_s: float | None = None,
    cadence_steps_min: float | None = None,
    step_length_symmetry_index: float | None = None,
) -> PatientFeatureSummary:
    """normative: optional dict with keys 'emg' -> {muscle: (mean_cycle, sd_cycle)} and
    'joint_angles' -> {joint: mean_cycle}, both on a 0-100% gait cycle grid (see
    build_normative_reference). Pass None to skip deviation-from-normative features
    (e.g. when extracting the normative reference itself from the control cohort).

    gait_speed_m_s / cadence_steps_min / step_length_symmetry_index are expected to come
    from the dataset's own spatiotemporal export rather than being recomputed here.
    """
    antagonist_pairs = antagonist_pairs or DEFAULT_ANTAGONIST_PAIRS
    side = trial.affected_side or "L"
    events = _gait_cycle_event_times(trial, side)

    muscle_findings = []
    envelopes_norm_cycle = {}
    for muscle, raw in trial.emg.items():
        envelope = raw_to_envelope(raw, trial.fs_emg)
        cycles = normalize_to_gait_cycle(envelope, events, trial.fs_emg)
        if cycles.size == 0:
            continue
        mean_cycle = cycles.mean(axis=0)
        norm_cycle = normalize_amplitude(mean_cycle, method="peak")
        envelopes_norm_cycle[muscle] = norm_cycle

        onset_pct, offset_pct = onset_offset_pct_from_cycle(norm_cycle)

        deviation_z_peak = None
        if normative and muscle in normative.get("emg", {}):
            nm_mean, nm_sd = normative["emg"][muscle]
            z = deviation_from_normative(mean_cycle, nm_mean, nm_sd)
            deviation_z_peak = float(np.max(np.abs(z)))

        muscle_findings.append(
            MuscleFinding(
                muscle=muscle,
                onset_pct_gait_cycle=onset_pct,
                offset_pct_gait_cycle=offset_pct,
                peak_amplitude_norm=float(norm_cycle.max()),
                deviation_z_peak=deviation_z_peak,
            )
        )

    cci_findings = {}
    for agonist, antagonist in antagonist_pairs:
        if agonist in envelopes_norm_cycle and antagonist in envelopes_norm_cycle:
            cci = co_contraction_index(envelopes_norm_cycle[agonist], envelopes_norm_cycle[antagonist])
            cci_findings[f"{agonist}_vs_{antagonist}"] = round(cci, 3)

    joint_findings = []
    gvs_by_joint = {}
    for joint, angle in trial.joint_angles.items():
        cycles = resample_to_gait_cycle(angle, events, trial.fs_kinematic)
        if cycles.size == 0:
            continue
        mean_cycle = cycles.mean(axis=0)
        rom = range_of_motion(mean_cycle)
        gvs = None
        if normative and joint in normative.get("joint_angles", {}):
            nm_mean = normative["joint_angles"][joint]
            gvs = gait_variable_score(mean_cycle, nm_mean)
            gvs_by_joint[joint] = gvs
        joint_findings.append(JointFinding(joint=joint, rom_deg=rom, gvs=gvs))

    gps = gait_profile_score(gvs_by_joint) if gvs_by_joint else None

    return PatientFeatureSummary(
        subject_id=trial.subject_id,
        group=trial.group,
        affected_side=trial.affected_side,
        gait_speed_m_s=gait_speed_m_s,
        cadence_steps_min=cadence_steps_min,
        step_length_symmetry_index=step_length_symmetry_index,
        muscle_findings=muscle_findings,
        joint_findings=joint_findings,
        cci_findings=cci_findings,
        gait_profile_score=gps,
    )


def to_json(summary: PatientFeatureSummary) -> dict:
    return json.loads(json.dumps(asdict(summary)))


def to_prompt_text(summary: PatientFeatureSummary) -> str:
    lines = [
        f"Subject: {summary.subject_id} (group: {summary.group}, affected side: {summary.affected_side or 'N/A'})",
    ]
    if summary.gait_speed_m_s is not None:
        category = classify_ambulation(summary.gait_speed_m_s)
        lines.append(f"Gait speed: {summary.gait_speed_m_s:.2f} m/s ({category})")
    if summary.cadence_steps_min is not None:
        lines.append(f"Cadence: {summary.cadence_steps_min:.1f} steps/min")
    if summary.step_length_symmetry_index is not None:
        lines.append(f"Step length symmetry index: {summary.step_length_symmetry_index:.1f}%")
    if summary.gait_profile_score is not None:
        lines.append(f"Composite kinematic deviation score (GPS-like): {summary.gait_profile_score:.2f}")

    lines.append("\nMuscle activation findings:")
    if not summary.muscle_findings:
        lines.append("No valid EMG data available for this trial (all channels dropped for data-quality reasons).")
    for m in summary.muscle_findings:
        onset = f"{m.onset_pct_gait_cycle:.0f}%" if m.onset_pct_gait_cycle is not None else "not detected"
        offset = f"{m.offset_pct_gait_cycle:.0f}%" if m.offset_pct_gait_cycle is not None else "not detected"
        dev = f", deviation from normative: {m.deviation_z_peak:.1f} SD" if m.deviation_z_peak is not None else ""
        lines.append(
            f"- {m.muscle}: onset {onset}, offset {offset} of gait cycle, "
            f"peak normalized amplitude {m.peak_amplitude_norm:.2f}{dev}"
        )

    if summary.cci_findings:
        lines.append("\nCo-contraction indices:")
        for pair, cci in summary.cci_findings.items():
            lines.append(f"- {pair}: CCI = {cci:.2f}")

    lines.append("\nJoint kinematic findings:")
    for j in summary.joint_findings:
        gvs = f", Gait Variable Score {j.gvs:.2f}" if j.gvs is not None else ""
        lines.append(f"- {j.joint}: range of motion {j.rom_deg:.1f} deg{gvs}")

    return "\n".join(lines)


def build_normative_reference_from_normalized(control_trials: list[NormalizedTrialData]) -> dict:
    """Same as build_normative_reference() but for data that's already stride-normalized
    (see figshare_loader.py) -- no envelope extraction or resampling needed, just
    stacking each control subject's pre-normalized curves and taking mean/SD.

    Uses nan-aware aggregation: roughly 20-30% of control subjects have NaN at some
    gait-cycle points in some EMG channels in the source file (dropped/invalid strides),
    so a plain mean would silently poison the whole normative curve at those points.
    """
    emg_stack: dict[str, list] = {}
    joint_stack: dict[str, list] = {}
    for trial in control_trials:
        for muscle, curve in trial.emg_norm.items():
            emg_stack.setdefault(muscle, []).append(curve)
        for joint, curve in trial.joint_angles.items():
            joint_stack.setdefault(joint, []).append(curve)
    normative_emg = {m: (np.nanmean(c, axis=0), np.nanstd(c, axis=0)) for m, c in emg_stack.items()}
    normative_joint = {j: np.nanmean(c, axis=0) for j, c in joint_stack.items()}
    return {"emg": normative_emg, "joint_angles": normative_joint}


def extract_summary_from_normalized(
    trial: NormalizedTrialData,
    normative: dict | None = None,
    antagonist_pairs: list[tuple[str, str]] | None = None,
    gait_speed_m_s: float | None = None,
    cadence_steps_min: float | None = None,
    step_length_symmetry_index: float | None = None,
) -> PatientFeatureSummary:
    """Same as extract_patient_summary() but for NormalizedTrialData -- the curves are
    already gait-cycle-normalized and peak-amplitude-normalized, so this skips straight
    to onset/offset detection, CCI, ROM, and deviation-from-normative."""
    antagonist_pairs = antagonist_pairs or DEFAULT_ANTAGONIST_PAIRS_SHORT

    muscle_findings = []
    for muscle, curve in trial.emg_norm.items():
        if np.isnan(curve).all():
            # This subject-side has no valid data for this muscle (dropped electrode /
            # bad signal quality in the source file) -- omit rather than report garbage.
            continue
        onset_pct, offset_pct = onset_offset_pct_from_cycle(curve)
        deviation_z_peak = None
        if normative and muscle in normative.get("emg", {}):
            nm_mean, nm_sd = normative["emg"][muscle]
            z = deviation_from_normative(curve, nm_mean, nm_sd)
            deviation_z_peak = float(np.max(np.abs(z)))
        muscle_findings.append(
            MuscleFinding(
                muscle=muscle,
                onset_pct_gait_cycle=onset_pct,
                offset_pct_gait_cycle=offset_pct,
                peak_amplitude_norm=float(curve.max()),
                deviation_z_peak=deviation_z_peak,
            )
        )

    cci_findings = {}
    for agonist, antagonist in antagonist_pairs:
        pair = trial.emg_norm.get(agonist), trial.emg_norm.get(antagonist)
        if all(c is not None and not np.isnan(c).all() for c in pair):
            cci = co_contraction_index(*pair)
            cci_findings[f"{agonist}_vs_{antagonist}"] = round(cci, 3)

    joint_findings = []
    gvs_by_joint = {}
    for joint, curve in trial.joint_angles.items():
        rom = range_of_motion(curve)
        gvs = None
        if normative and joint in normative.get("joint_angles", {}):
            gvs = gait_variable_score(curve, normative["joint_angles"][joint])
            gvs_by_joint[joint] = gvs
        joint_findings.append(JointFinding(joint=joint, rom_deg=rom, gvs=gvs))

    gps = gait_profile_score(gvs_by_joint) if gvs_by_joint else None

    side_map = {"P": "paretic", "N": "non-paretic", "avg": None}
    subject_label = f"{trial.subject_id}_{trial.side}" if trial.side != "avg" else trial.subject_id

    return PatientFeatureSummary(
        subject_id=subject_label,
        group=trial.group,
        affected_side=side_map.get(trial.side),
        gait_speed_m_s=gait_speed_m_s,
        cadence_steps_min=cadence_steps_min,
        step_length_symmetry_index=step_length_symmetry_index,
        muscle_findings=muscle_findings,
        joint_findings=joint_findings,
        cci_findings=cci_findings,
        gait_profile_score=gps,
    )
