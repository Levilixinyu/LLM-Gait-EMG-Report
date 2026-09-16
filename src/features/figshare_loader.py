"""Loader for the Van Criekinge et al. (2023, Scientific Data) Figshare post-processed
Excel files -- stride-normalized (1001-point), per-subject sheets of sagittal joint
angles and peak-normalized EMG envelopes.

Stroke file (PostStrokeAdults.xlsx): one sheet per subject (Sub01..Sub50), columns
prefixed Pside_/Nside_ (paretic / non-paretic side), each already averaged over that
subject's strides and EMG-normalized to that subject's own peak muscle activity.
No moments/powers/GRF (not enough good force-plate data for the stroke cohort).

Able-bodied file (AbleBodiedAdults.xlsx): one sheet per subject (Sub01..Sub138),
unprefixed columns (symmetric gait, single averaged trace per subject); also includes
AnkleMoment/KneeMoment/HipMoment, AnklePower/KneePower/HipPower, and GRF_ap/ml/vert,
which the stroke file lacks and this pipeline does not currently use.

Source: https://doi.org/10.6084/m9.figshare.c.6503791.v1
"""
from __future__ import annotations

import numpy as np
import openpyxl

from .data_types import NormalizedTrialData

EMG_MUSCLES = ["GAS", "RF", "VL", "BF", "ST", "TA", "ERS"]
KINEMATIC_JOINTS = ["AnkleAngles", "KneeAngles", "HipAngles", "PelvisAngles"]


def _read_sheet_columns(ws) -> dict[str, np.ndarray]:
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    columns: dict[str, list] = {name: [] for name in header if name is not None}
    for row in rows[1:]:
        for name, value in zip(header, row):
            if name is not None:
                columns[name].append(value)
    return {name: np.array(values, dtype=float) for name, values in columns.items()}


def load_stroke_excel(xlsx_path: str) -> list[NormalizedTrialData]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    trials = []
    for sheet_name in wb.sheetnames:
        if not sheet_name.startswith("Sub"):
            continue
        columns = _read_sheet_columns(wb[sheet_name])
        for side_prefix, side_label in [("Pside", "P"), ("Nside", "N")]:
            joint_angles = {
                joint: columns[f"{side_prefix}_{joint}"]
                for joint in KINEMATIC_JOINTS
                if f"{side_prefix}_{joint}" in columns
            }
            emg_norm = {
                muscle: columns[f"{side_prefix}_{muscle}norm"]
                for muscle in EMG_MUSCLES
                if f"{side_prefix}_{muscle}norm" in columns
            }
            trials.append(
                NormalizedTrialData(
                    subject_id=sheet_name,
                    group="stroke",
                    side=side_label,
                    joint_angles=joint_angles,
                    emg_norm=emg_norm,
                )
            )
    return trials


def load_control_excel(xlsx_path: str) -> list[NormalizedTrialData]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    trials = []
    for sheet_name in wb.sheetnames:
        if not sheet_name.startswith("Sub"):
            continue
        columns = _read_sheet_columns(wb[sheet_name])
        joint_angles = {joint: columns[joint] for joint in KINEMATIC_JOINTS if joint in columns}
        emg_norm = {muscle: columns[f"{muscle}norm"] for muscle in EMG_MUSCLES if f"{muscle}norm" in columns}
        trials.append(
            NormalizedTrialData(
                subject_id=sheet_name,
                group="control",
                side="avg",
                joint_angles=joint_angles,
                emg_norm=emg_norm,
            )
        )
    return trials
