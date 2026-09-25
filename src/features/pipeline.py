"""Orchestrates feature extraction from RawTrialData into a PatientFeatureSummary,
builds a normative reference from healthy-control trials, and converts a summary
into LLM-ready prompt text / JSON."""
from __future__ import annotations

from .emg_provenance import RAW_PIPELINE_EMG

import json
from dataclasses import asdict

import numpy as np

from .data_types import JointFinding, MuscleFinding, NormalizedTrialData, PatientFeatureSummary, RawTrialData
from .emg_signal import (
    analyze_activation,
    co_contraction_index,
    deviation_from_normative,
    normalize_amplitude,
    normalize_to_gait_cycle,
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


def _muscle_finding(muscle: str, curve: np.ndarray, normative: dict | None) -> MuscleFinding | None:
    """Shared per-muscle feature extraction for both paths. `curve` must already be on
    the 0-100% grid AND in the same normalization as the normative reference (both
    paths now pass peak-normalized-family curves -- the v1 raw path compared an
    unnormalized envelope against a peak-normalized reference, so its z-scores scaled
    with raw signal amplitude; audit P1-2, fixed by normalizing before this call)."""
    profile = analyze_activation(curve)
    if profile is None:
        return None

    deviation_z_peak = deviation_z_signed = deviation_phase_pct = None
    if normative and muscle in normative.get("emg", {}):
        nm_mean, nm_sd = normative["emg"][muscle]
        z = deviation_from_normative(curve, nm_mean, nm_sd)
        finite = np.isfinite(z)
        if finite.any():
            idx = int(np.nanargmax(np.abs(np.where(finite, z, 0))))
            deviation_z_peak = float(abs(z[idx]))
            deviation_z_signed = float(z[idx])
            deviation_phase_pct = float(100 * idx / (len(z) - 1))

    first = profile.intervals[0] if profile.intervals else (None, None)
    return MuscleFinding(
        muscle=muscle,
        onset_pct_gait_cycle=first[0],
        offset_pct_gait_cycle=first[1],
        peak_amplitude_norm=profile.peak_value,
        deviation_z_peak=deviation_z_peak,
        activation_intervals=list(profile.intervals),
        above_threshold_pct=profile.above_threshold_pct,
        crosses_cycle_boundary=profile.crosses_cycle_boundary,
        deviation_z_signed=deviation_z_signed,
        deviation_phase_pct=deviation_phase_pct,
        nan_pct=profile.nan_pct,
    )


def _gait_cycle_event_times(trial: RawTrialData, side: str) -> list[float]:
    return trial.gait_events.get(f"heel_strike_{side}", [])


def build_normative_reference(
    control_trials: list[RawTrialData],
    events_side: str = "L",
    source: str = "unspecified",
    method: str = "pooled",
    excluded_subjects: tuple = (),
) -> dict:
    """Aggregate healthy-control trials into normative mean/SD reference curves,
    keyed for use as the `normative` argument to extract_patient_summary(). Carries
    the same "meta" block as build_normative_reference_from_normalized() -- see there
    for why (audit round 3, T2). Raw-path references are typically small/custom, so
    source stays "unspecified" (=> no main-cohort calibration text) unless the caller
    genuinely built it from the main cohort."""
    emg_cycles: dict[str, list] = {}
    joint_cycles: dict[str, list] = {}
    n_points = None

    for trial in control_trials:
        events = _gait_cycle_event_times(trial, events_side)
        for muscle, raw in trial.emg.items():
            envelope = raw_to_envelope(raw, trial.fs_emg)
            cycles = normalize_to_gait_cycle(envelope, events, trial.fs_emg)
            if cycles.size == 0:
                continue
            norm_cycle = normalize_amplitude(cycles.mean(axis=0), method="peak")
            emg_cycles.setdefault(muscle, []).append(norm_cycle)
            n_points = n_points or len(norm_cycle)
        for joint, angle in trial.joint_angles.items():
            cycles = resample_to_gait_cycle(angle, events, trial.fs_kinematic)
            if cycles.size == 0:
                continue
            joint_cycles.setdefault(joint, []).append(cycles.mean(axis=0))
            n_points = n_points or cycles.shape[1]

    normative_emg = {m: (np.mean(c, axis=0), np.std(c, axis=0)) for m, c in emg_cycles.items()}
    normative_joint = {j: np.mean(c, axis=0) for j, c in joint_cycles.items()}
    meta = {
        "source": source,
        "method": method,
        "excluded_subjects": list(excluded_subjects),
        "n_subjects": len(control_trials),
        "n_points": n_points,
        "calibration_family": "main_cohort_excel" if source == "main_cohort_excel" else None,
    }
    return {"emg": normative_emg, "joint_angles": normative_joint, "meta": meta}


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
    missing_channels = []
    envelopes_norm_cycle = {}
    for muscle, raw in trial.emg.items():
        envelope = raw_to_envelope(raw, trial.fs_emg)
        cycles = normalize_to_gait_cycle(envelope, events, trial.fs_emg)
        if cycles.size == 0:
            missing_channels.append(muscle)
            continue
        mean_cycle = cycles.mean(axis=0)
        # peak-normalize BEFORE comparing to the (peak-normalized) reference -- the v1
        # code compared the unnormalized mean_cycle here, so z scaled with raw signal
        # amplitude (10x amplitude => TA z 370.58 -> 967.72; audit P1-2)
        norm_cycle = normalize_amplitude(mean_cycle, method="peak")
        envelopes_norm_cycle[muscle] = norm_cycle

        finding = _muscle_finding(muscle, norm_cycle, normative)
        if finding is not None:
            muscle_findings.append(finding)
        else:
            missing_channels.append(muscle)

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
        emg_processing=RAW_PIPELINE_EMG,
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
        missing_emg_channels=missing_channels,
        # reference description comes from the normative dict's own meta block, not
        # from the mere fact a reference was passed (audit R5 + round 3 T2)
        reference_source=(normative.get("meta", {}).get("calibration_family") or "unspecified_raw")
        if normative else None,
        reference_meta=normative.get("meta") if normative else None,
    )


def to_json(summary: PatientFeatureSummary) -> dict:
    return json.loads(json.dumps(asdict(summary)))


# -- metric-definition text is assembled per reference source (audit round 2, R5):
# cohort-specific calibration claims (n, phase-point count, quantiles, speed range)
# may ONLY ship with data actually referenced against that cohort. A raw-path summary
# built on e.g. 5 synthetic controls must not be captioned with main-cohort numbers.

# Historical v2 text is retained for byte-comparable replay only.
# Prospective interpretation uses src.llm.candidate_prompts with explicit preprocessing
# provenance; the old normalization sentence must not be reused in new studies.
_DEFS_COMMON = """Metric definitions (read before interpreting any number below):
- All joint angles and ROM values are SAGITTAL PLANE only. Coronal/transverse data are not included.
- EMG curves are ensemble averages of per-cycle envelopes, each cycle normalized to that subject's own per-muscle maximum before averaging. Amplitudes are therefore relative within-muscle values -- they are NOT absolute activation, force, or strength, and must not be compared across muscles as "stronger/weaker".
- Activation intervals are the regions where the averaged envelope exceeds 20% of that curve's own peak, minimum retained interval 3% of the cycle (by sample count). An interval written as (X%-Y%) with X > Y wraps across the 100%->0% cycle boundary (activity continuous across the cycle-defining event). An onset of 0% is the analysis-window boundary, not necessarily a physiological onset. "No interval detected" means no region met the threshold + duration criteria; it does NOT mean the muscle is inactive or non-functional.
- CCI is the Falconer-Winter co-contraction index computed on the full continuous envelopes (2*common area / summed areas), so it can be non-zero even when the DETECTED burst intervals of the pair do not overlap (sub-threshold activity contributes).
- The composite kinematic deviation score is the RMS of the per-joint Gait Variable Scores over the sagittal channels provided ("GPS-like", not the validated 9-variable GPS).
- Step length symmetry index: 200*(paretic - non-paretic)/(paretic + non-paretic), in %. NEGATIVE means the paretic-side step is SHORTER. Two operational step-length definitions exist (successive-footfall: each heel's position at its own initial contact; instantaneous: both heels at the same instant) and give different values for some subjects -- the definition actually used is stated next to the symmetry value."""

_DEFS_MAIN_COHORT = """- "Max |z| deviation" is the LARGEST absolute z-score across all 1001 phase points of the cycle, comparing this curve to the healthy-cohort mean/SD at each phase. This is an extreme-value statistic, NOT a single-observation z-score: in this dataset every one of 109 healthy controls exceeds |z| = 2 on at least one muscle, and per-muscle healthy 95th percentiles for this statistic run 3.65 (ERS) to 4.61 (TA) -- higher still under leave-one-out. Do not label a value abnormal by the conventional 2-SD rule; use the healthy reference range given per muscle where provided.
- Healthy-cohort CCI reference (this dataset): RF-vs-BF median 0.68 (2.5th-97.5th pct 0.48-0.83); TA-vs-GAS median 0.39 (0.24-0.59). Composite score reference: median 5.1, 95th percentile 10.7.
- COHORT BACKGROUND (calibration context, not necessarily the exact reference used for this subject -- the actual reference composition is stated in a dedicated line with the subject data below): the full healthy cohort is 138 subjects for kinematics, effective n = 106-109 per muscle for EMG (29 controls have no usable EMG; completeness varies by age), pooling both body sides and all ages; it is not age- or speed-matched to this subject. A leave-one-out run uses one subject fewer than these counts.
- SPEED SUPPORT LIMIT (applies to most stroke subjects in this dataset): the healthy reference cohort's self-selected walking speeds span 0.80-1.79 m/s. If this subject's gait speed is below 0.80 m/s, NO speed-matched healthy reference exists in this dataset -- 41 of the 50 stroke subjects are below that floor. Deviations from the reference then conflate slow-walking effects with stroke-specific control changes, and the two cannot be separated from these data. Describe deviations from the reference as such; do not attribute them wholly to stroke pathology.
- Fields NOT included in this summary but existing in the source dataset (deliberately out of scope for this version, not missing from the data): age, sex, time post-stroke, clinical scores (FAC/POMA/TIS), non-paretic-side curves, per-subject toe-off timing. Do not state that such information "does not exist" -- say it was not provided. Where a finding is absent because no interval met detection criteria or a channel is missing, that specific reason is stated inline."""

_DEFS_GENERIC_REFERENCE = """- "Max |z| deviation" is the LARGEST absolute z-score across the phase points of the cycle vs. the reference curves supplied by the caller. This is an extreme-value statistic, NOT a single-observation z-score, and NO calibrated healthy reference distribution is available for this data source -- neither the conventional 2-SD rule nor any cohort percentile applies. Treat these values as relative indicators only.
- No population reference ranges are available for CCI or the composite score for this data source."""


def metric_definitions(reference_source: str | None) -> str:
    if reference_source == "main_cohort_excel":
        return _DEFS_COMMON + "\n" + _DEFS_MAIN_COHORT
    return _DEFS_COMMON + "\n" + _DEFS_GENERIC_REFERENCE


# kept as the main-cohort text for backward compatibility with docs referencing it
METRIC_DEFINITIONS = metric_definitions("main_cohort_excel")

# Subjects whose all-channel EMG absence has a DOCUMENTED cause in the source study
# (supplement: participants with no analog signals captured). Keyed by (group,
# project subject id) so a healthy or synthetic case that happens to share an id can
# never inherit a stroke subject's documented reason (audit round 3, T5).
# Stroke-cohort mapping to the original TVC ids: Sub08=TVC11, Sub47=TVC55,
# Sub48=TVC57 -- all three documented as no-analog-capture. Sub43's all-missing
# EMG has NO documented cause; it stays "not recorded" deliberately.
DOCUMENTED_NO_ANALOG = {
    ("stroke", "Sub08"),
    ("stroke", "Sub47"),
    ("stroke", "Sub48"),
}


def to_prompt_text(summary: PatientFeatureSummary, include_definitions: bool = True) -> str:
    lines = []
    if include_definitions:
        lines.append(metric_definitions(summary.reference_source))
        lines.append("")
    lines.append(
        f"Subject: {summary.subject_id} (group: {summary.group}, affected side: {summary.affected_side or 'N/A'})"
    )
    if summary.gait_speed_m_s is not None:
        category = classify_ambulation(summary.gait_speed_m_s)
        lines.append(f"Gait speed: {summary.gait_speed_m_s:.2f} m/s ({category})")
    if summary.cadence_steps_min is not None:
        lines.append(f"Cadence: {summary.cadence_steps_min:.1f} steps/min")
    if summary.step_length_symmetry_index is not None:
        sl_def = summary.step_length_definition or "successive_footfall"
        lines.append(
            f"Step length symmetry index: {summary.step_length_symmetry_index:.1f}% "
            f"(step-length definition: {sl_def})"
        )
    if summary.gait_profile_score is not None:
        lines.append(f"Composite kinematic deviation score (GPS-like): {summary.gait_profile_score:.2f}")

    # the reference ACTUALLY used, from its own metadata -- e.g. a leave-one-out run
    # says 137 subjects with the exclusion named, never a hardcoded cohort size
    # (audit round 3, T2)
    if summary.reference_meta:
        rm = summary.reference_meta
        excl = f", excluding {', '.join(rm['excluded_subjects'])}" if rm.get("excluded_subjects") else ""
        method = {"pooled": "pooled", "leave_one_out": "leave-one-out"}.get(rm.get("method"), rm.get("method"))
        lines.append(
            f"Deviation reference actually used for this subject: {rm.get('n_subjects')} healthy "
            f"subjects ({method}{excl}), {rm.get('n_points')} phase points, source: {rm.get('source')}."
        )
    elif any(m.deviation_z_peak is not None for m in summary.muscle_findings):
        lines.append(
            "Deviation reference composition: unspecified (no reference metadata was "
            "recorded for this run)."
        )

    base_subject = summary.subject_id.split("_")[0]
    if (summary.group, base_subject) in DOCUMENTED_NO_ANALOG:
        missing_reason = (
            "the source study documents that no analog (EMG) signals were captured for "
            "this participant"
        )
    else:
        missing_reason = (
            "the per-subject reason -- electrode issue vs. analog signals not captured -- "
            "is not recorded in the public data"
        )

    lines.append("\nMuscle activation findings:")
    if not summary.muscle_findings:
        lines.append(f"No valid EMG data available for this trial ({missing_reason}).")
    for m in summary.muscle_findings:
        if m.activation_intervals:
            parts = []
            for a, b in m.activation_intervals:
                if a > b:
                    parts.append(f"{a:.0f}%-{b:.0f}% (wraps cycle boundary)")
                else:
                    parts.append(f"{a:.0f}%-{b:.0f}%")
            intervals_txt = "; ".join(parts)
        else:
            intervals_txt = "no interval met detection criteria"
        boundary = ", active across cycle boundary" if m.crosses_cycle_boundary else ""
        above = f", {m.above_threshold_pct:.0f}% of cycle above threshold" if m.above_threshold_pct is not None else ""
        if m.deviation_z_signed is not None:
            sign = "above" if m.deviation_z_signed > 0 else "below"
            dev = (
                f", max |z| vs healthy reference: {abs(m.deviation_z_signed):.1f} "
                f"({sign} reference, at {m.deviation_phase_pct:.0f}% of cycle)"
            )
        elif m.deviation_z_peak is not None:
            dev = f", max |z| vs healthy reference: {m.deviation_z_peak:.1f}"
        else:
            dev = ""
        quality = (
            f" [DATA QUALITY: {m.nan_pct:.0f}% of samples missing in this curve, "
            f"masked as below-threshold -- intervals may be split by gaps]"
            if m.nan_pct else ""
        )
        lines.append(
            f"- {m.muscle}: activation interval(s) {intervals_txt}{above}{boundary}, "
            f"peak normalized amplitude {m.peak_amplitude_norm:.2f}{dev}{quality}"
        )
    if summary.muscle_findings and summary.missing_emg_channels:
        lines.append(
            f"- Channels with NO usable data for this trial ({missing_reason}): "
            + ", ".join(summary.missing_emg_channels)
        )

    if summary.cci_findings:
        lines.append("\nCo-contraction indices:")
        for pair, cci in summary.cci_findings.items():
            lines.append(f"- {pair}: CCI = {cci:.2f}")

    lines.append("\nJoint kinematic findings (sagittal plane):")
    for j in summary.joint_findings:
        gvs = f", Gait Variable Score {j.gvs:.2f}" if j.gvs is not None else ""
        lines.append(f"- {j.joint}: range of motion {j.rom_deg:.1f} deg{gvs}")

    return "\n".join(lines)


def build_normative_reference_from_normalized(
    control_trials: list[NormalizedTrialData],
    source: str = "unspecified",
    method: str = "pooled",
    excluded_subjects: tuple = (),
) -> dict:
    """Same as build_normative_reference() but for data that's already stride-normalized
    (see figshare_loader.py) -- no envelope extraction or resampling needed, just
    stacking each control subject's pre-normalized curves and taking mean/SD.

    Uses nan-aware aggregation: roughly 20-30% of control subjects have NaN at some
    gait-cycle points in some EMG channels in the source file (dropped/invalid strides),
    so a plain mean would silently poison the whole normative curve at those points.

    The returned dict carries a "meta" block describing WHAT this reference actually
    is (source, pooled vs leave-one-out, exclusions, subject count, phase points).
    Downstream serialization derives its reference description from this metadata --
    it is NOT inferred from "a normative dict was passed" (audit round 3, T2: a
    leave-one-out 137-subject reference was described as 138, and a 3-subject custom
    reference was captioned with main-cohort calibration). Callers building the
    reference from the main-cohort Excel controls must say so via
    source="main_cohort_excel"; only then do main-cohort calibration numbers attach.
    """
    emg_stack: dict[str, list] = {}
    joint_stack: dict[str, list] = {}
    n_points = None
    for trial in control_trials:
        for muscle, curve in trial.emg_norm.items():
            emg_stack.setdefault(muscle, []).append(curve)
            n_points = n_points or len(curve)
        for joint, curve in trial.joint_angles.items():
            joint_stack.setdefault(joint, []).append(curve)
            n_points = n_points or len(curve)
    normative_emg = {m: (np.nanmean(c, axis=0), np.nanstd(c, axis=0)) for m, c in emg_stack.items()}
    normative_joint = {j: np.nanmean(c, axis=0) for j, c in joint_stack.items()}
    meta = {
        "source": source,
        "method": method,
        "excluded_subjects": list(excluded_subjects),
        "n_subjects": len(control_trials),
        "n_points": n_points,
        "calibration_family": "main_cohort_excel" if source == "main_cohort_excel" else None,
    }
    return {"emg": normative_emg, "joint_angles": normative_joint, "meta": meta}


def extract_summary_from_normalized(
    trial: NormalizedTrialData,
    normative: dict | None = None,
    antagonist_pairs: list[tuple[str, str]] | None = None,
    gait_speed_m_s: float | None = None,
    cadence_steps_min: float | None = None,
    step_length_symmetry_index: float | None = None,
    step_length_definition: str | None = None,
) -> PatientFeatureSummary:
    """Extract features from supplied mean curves without rescaling their amplitudes.
    The released cohort uses a shared maximum across available strides before
    averaging, not independent per-stride peak normalization. Custom inputs need
    their own explicit emg_processing provenance. A mean curve need not peak at 1:
    interval detection uses 20% of that curve's own peak (see analyze_activation),
    not an absolute cutoff of 0.2 (the historical P0-2 bug). Channels entirely NaN
    are recorded in
    missing_emg_channels rather than silently omitted; the per-subject REASON is
    handled at serialization (documented no-analog-capture subjects vs. unrecorded --
    audit R6)."""
    antagonist_pairs = antagonist_pairs or DEFAULT_ANTAGONIST_PAIRS_SHORT

    muscle_findings = []
    missing_channels = []
    for muscle, curve in trial.emg_norm.items():
        finding = _muscle_finding(muscle, curve, normative)
        if finding is None:
            missing_channels.append(muscle)
        if finding is not None:
            muscle_findings.append(finding)

    cci_findings = {}
    for agonist, antagonist in antagonist_pairs:
        pair = trial.emg_norm.get(agonist), trial.emg_norm.get(antagonist)
        # require FULLY finite curves: a partial-NaN curve would propagate NaN into
        # the CCI (breaking strict JSON) or silently distort the area ratio. No such
        # curves exist in the main dataset (verified all-or-nothing missingness), so
        # this is a generic-path guard, not a change to main-data results (audit R8).
        if all(c is not None and np.isfinite(c).all() for c in pair):
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
        emg_processing=trial.emg_processing,
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
        missing_emg_channels=missing_channels,
        step_length_definition=step_length_definition,
        # derived from the reference's own meta -- a custom/LOO/other-source reference
        # no longer gets blanket-labeled as the main cohort (audit round 3, T2)
        reference_source=normative.get("meta", {}).get("calibration_family") if normative else None,
        reference_meta=normative.get("meta") if normative else None,
    )
