"""Shared data structures for raw trial data and extracted patient feature summaries."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawTrialData:
    subject_id: str
    group: str  # "stroke" | "control"
    fs_emg: float
    fs_kinematic: float
    emg: dict  # muscle_name -> 1D np.ndarray, raw signal
    joint_angles: dict  # joint_name -> 1D np.ndarray, angle trace (deg)
    gait_events: dict  # e.g. "heel_strike_L" -> list[float] (event times in seconds)
    affected_side: str | None = None  # "L" | "R" | None for controls


@dataclass
class NormalizedTrialData:
    """One subject-side trial already stride-time-normalized to a fixed-length gait
    cycle grid. EMG amplitude processing is recorded separately in emg_processing;
    for the released cohort, scaling precedes stride averaging and uses a shared
    across-stride maximum per recorded muscle.
    No fs/events needed since the segmentation and normalization are already done."""

    subject_id: str
    group: str  # "stroke" | "control"
    side: str  # "P" (paretic) | "N" (non-paretic) | "avg" (single trace, e.g. controls)
    joint_angles: dict  # joint_name -> 1D np.ndarray, angle trace (deg), fixed length
    emg_norm: dict  # muscle_name -> 1D np.ndarray, supplied mean envelope, same length; see emg_processing
    emg_processing: str | None = None  # provenance, independent of reference membership


@dataclass
class MuscleFinding:
    muscle: str
    # v1 legacy pair = FIRST activation interval only (kept for comparison with frozen
    # v1 outputs). v2 consumers must use activation_intervals, which carries ALL
    # retained intervals -- audit P0-1 showed the single pair silently dropped real
    # later bursts and induced downstream over-interpretation.
    onset_pct_gait_cycle: float | None
    offset_pct_gait_cycle: float | None
    peak_amplitude_norm: float
    deviation_z_peak: float | None  # max |z| across the cycle vs normative -- NOT a
    # single-point z-score; do not apply the conventional 2-SD abnormality reading
    # (109/109 healthy controls exceed 2 somewhere; healthy 95th percentiles run
    # ~3.3-3.9 per muscle, higher under leave-one-out). See audit P0-3.
    activation_intervals: list = field(default_factory=list)  # [(onset_pct, offset_pct)];
    # onset > offset means the interval wraps the 100->0% cycle boundary
    above_threshold_pct: float | None = None  # % of cycle above threshold
    crosses_cycle_boundary: bool | None = None  # active at both 0% and 100%
    deviation_z_signed: float | None = None  # signed z at the phase of max |z|
    deviation_phase_pct: float | None = None  # phase (% gait cycle) where max |z| occurs
    nan_pct: float | None = None  # % of samples NaN in the source curve (quality flag;
    # NaN samples are masked as below-threshold and can split intervals -- audit R8)


@dataclass
class JointFinding:
    joint: str
    rom_deg: float
    gvs: float | None  # gait variable score vs normative, None if no reference


@dataclass
class PatientFeatureSummary:
    subject_id: str
    group: str
    affected_side: str | None
    gait_speed_m_s: float | None
    cadence_steps_min: float | None
    step_length_symmetry_index: float | None
    muscle_findings: list = field(default_factory=list)  # list[MuscleFinding]
    joint_findings: list = field(default_factory=list)  # list[JointFinding]
    cci_findings: dict = field(default_factory=dict)  # "muscleA_vs_muscleB" -> CCI value
    gait_profile_score: float | None = None
    # channels present in the source's channel set but with no usable data for this
    # subject -- listed explicitly so "only ERS reported" is never mistaken for "only
    # ERS was measured" (audit round 2, R6)
    missing_emg_channels: list = field(default_factory=list)
    # operational step-length definition actually used for the symmetry index
    # ("successive_footfall" | "instantaneous"); carried as metadata so the serialized
    # description can never silently disagree with the number (audit round 2, R6)
    step_length_definition: str | None = None
    # which reference/calibration family the deviation stats were computed against --
    # gates whether main-cohort calibration numbers may be attached to the output
    # ("main_cohort_excel" | "unspecified_raw" | None). Prevents hardcoded main-cohort
    # claims (n=138, 1001 points, quantiles) being shipped with e.g. synthetic raw
    # data (audit round 2, R5)
    reference_source: str | None = None
    # full composition of the reference actually used (source, pooled vs leave-one-out,
    # exclusions, n_subjects, n_points) -- copied from the normative dict's meta block
    # so serialized text describes the REAL reference, not an assumed one (audit
    # round 3, T2: a 137-subject LOO reference was being described as 138)
    reference_meta: dict | None = None
    emg_processing: str | None = None
