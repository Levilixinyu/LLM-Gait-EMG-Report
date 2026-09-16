"""Adapters that turn dataset files into RawTrialData.

The CSV loader below assumes a generic per-subject export (one CSV of EMG channels,
one of joint-angle channels, one of gait-event times in seconds) as a placeholder.
Replace load_subject_csv (or add a sibling loader) to match the actual file format
once the Van Criekinge et al. (2023, Figshare, doi via Scientific Data paper) raw
files have been inspected -- likely .mat or .c3d rather than flat CSV.
"""
from __future__ import annotations

import pandas as pd

from .data_types import RawTrialData


def load_subject_csv(
    subject_id: str,
    group: str,
    emg_csv: str,
    kinematics_csv: str,
    events_csv: str,
    fs_emg: float,
    fs_kinematic: float,
    affected_side: str | None = None,
) -> RawTrialData:
    """events_csv: one column per event type (e.g. "heel_strike_L", "heel_strike_R"),
    each cell an event time in seconds. Missing values are dropped."""
    emg_df = pd.read_csv(emg_csv)
    kin_df = pd.read_csv(kinematics_csv)
    events_df = pd.read_csv(events_csv)

    emg = {col: emg_df[col].to_numpy() for col in emg_df.columns}
    joint_angles = {col: kin_df[col].to_numpy() for col in kin_df.columns}
    gait_events = {col: events_df[col].dropna().astype(float).tolist() for col in events_df.columns}

    return RawTrialData(
        subject_id=subject_id,
        group=group,
        fs_emg=fs_emg,
        fs_kinematic=fs_kinematic,
        emg=emg,
        joint_angles=joint_angles,
        gait_events=gait_events,
        affected_side=affected_side,
    )
