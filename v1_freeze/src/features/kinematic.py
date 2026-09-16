"""Kinematic feature extraction: gait cycle resampling, range of motion, and a
simplified Gait Variable Score / Gait Profile Score (cf. Baker et al., 2009)."""
from __future__ import annotations

import numpy as np


def resample_to_gait_cycle(
    angle_trace: np.ndarray,
    event_times_s: list[float],
    fs: float,
    n_points: int = 101,
) -> np.ndarray:
    event_idx = [int(round(t * fs)) for t in event_times_s]
    cycles = []
    for start, end in zip(event_idx[:-1], event_idx[1:]):
        segment = angle_trace[start:end]
        if len(segment) < 2:
            continue
        x_old = np.linspace(0, 100, len(segment))
        x_new = np.linspace(0, 100, n_points)
        cycles.append(np.interp(x_new, x_old, segment))
    return np.array(cycles)


def range_of_motion(cycle: np.ndarray) -> float:
    return float(cycle.max() - cycle.min())


def gait_variable_score(patient_cycle_mean: np.ndarray, normative_mean: np.ndarray) -> float:
    """RMS difference between a patient's cycle-mean curve and the normative mean
    curve over the gait cycle (simplified Gait Variable Score)."""
    return float(np.sqrt(np.mean((patient_cycle_mean - normative_mean) ** 2)))


def gait_profile_score(gvs_by_variable: dict) -> float:
    """RMS of Gait Variable Scores across all tracked kinematic variables.

    This is a simplification of the canonical 9-variable GPS (Baker et al., 2009):
    it is computed here over whatever kinematic channels the dataset provides, not
    the fixed Conventional Gait Analysis variable set. Report it as "GPS-like" /
    "composite kinematic deviation score" in any manuscript, not as the validated GPS,
    unless the full 9-variable set is reproduced.
    """
    values = np.array(list(gvs_by_variable.values()))
    return float(np.sqrt(np.mean(values ** 2)))
