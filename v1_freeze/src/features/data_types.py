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
    cycle grid and (for EMG) amplitude-normalized to that subject's own peak -- the
    format the Van Criekinge et al. (2023) Figshare post-processed Excel files ship in.
    No fs/events needed since the segmentation and normalization are already done."""

    subject_id: str
    group: str  # "stroke" | "control"
    side: str  # "P" (paretic) | "N" (non-paretic) | "avg" (single trace, e.g. controls)
    joint_angles: dict  # joint_name -> 1D np.ndarray, angle trace (deg), fixed length
    emg_norm: dict  # muscle_name -> 1D np.ndarray, peak-normalized envelope, same length


@dataclass
class MuscleFinding:
    muscle: str
    onset_pct_gait_cycle: float | None
    offset_pct_gait_cycle: float | None
    peak_amplitude_norm: float
    deviation_z_peak: float | None  # peak |z-score| vs normative, None if no reference


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
