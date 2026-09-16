"""Generates a synthetic RawTrialData object with plausible EMG/kinematic signals, so
the feature-extraction and prompt-generation pipeline can be validated end-to-end before
the real dataset is downloaded and adapted via src/features/data_loader.py."""
from __future__ import annotations

import numpy as np

from src.features.data_types import RawTrialData


def make_synthetic_trial(
    subject_id: str,
    group: str = "stroke",
    affected_side: str = "L",
    seed: int = 0,
) -> RawTrialData:
    rng = np.random.default_rng(seed)
    fs_emg = 1000.0
    fs_kin = 100.0
    duration_s = 20.0  # ~ a handful of gait cycles

    n_emg = int(duration_s * fs_emg)
    n_kin = int(duration_s * fs_kin)
    t_emg = np.arange(n_emg) / fs_emg
    t_kin = np.arange(n_kin) / fs_kin

    cycle_s = 1.4 if group == "stroke" else 1.1  # slower cadence in stroke
    delay = 0.15 if group == "stroke" else 0.0  # simulate delayed onset

    def bursty_emg(phase_offset: float, burst_width: float = 0.12) -> np.ndarray:
        phase = ((t_emg / cycle_s) + phase_offset) % 1.0
        envelope = np.exp(-((phase - 0.2) ** 2) / (2 * burst_width**2))
        noise = rng.normal(0, 1, n_emg)
        return envelope * noise * 0.5 + noise * 0.05

    emg = {
        "tibialis_anterior": bursty_emg(delay + 0.0),
        "gastrocnemius_medialis": bursty_emg(delay + 0.5),
        "rectus_femoris": bursty_emg(delay + 0.05),
        "biceps_femoris": bursty_emg(delay + 0.55),
    }

    phase_kin = (t_kin / cycle_s) % 1.0
    rom_scale = 0.7 if group == "stroke" else 1.0
    joint_angles = {
        "knee_flexion": 30 + 25 * rom_scale * np.sin(2 * np.pi * phase_kin) + rng.normal(0, 1, n_kin),
        "ankle_dorsiflexion": 5 + 10 * rom_scale * np.sin(2 * np.pi * phase_kin + 0.3) + rng.normal(0, 1, n_kin),
        "hip_flexion": 20 + 20 * rom_scale * np.sin(2 * np.pi * phase_kin + 1.5) + rng.normal(0, 1, n_kin),
    }

    n_strikes = int(duration_s / cycle_s)
    heel_strikes_s = [round(i * cycle_s, 3) for i in range(n_strikes)]

    return RawTrialData(
        subject_id=subject_id,
        group=group,
        fs_emg=fs_emg,
        fs_kinematic=fs_kin,
        emg=emg,
        joint_angles=joint_angles,
        gait_events={f"heel_strike_{affected_side}": heel_strikes_s},
        affected_side=affected_side if group == "stroke" else None,
    )
