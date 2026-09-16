"""Derives per-subject-side spatiotemporal gait parameters (speed, cadence, step-length
symmetry) from the Van Criekinge et al. (2023) raw MATLAB v7.3 (HDF5) release --
MAT_normalizedData_PostStrokeAdults.mat. Not provided as precomputed columns anywhere in
the public post-processed Excel exports (see figshare_loader.py); derived here from gait
events (ICstart/ICstop/IC_cnt, absolute video-frame indices) and the HEE marker's
stride-normalized anterior-posterior trajectory, both already present in the MAT file.

Subject ordering in the MAT file's `Sub` struct array is documented (in the Excel
ReadMe: "numbered consistently with the MAT structure") as matching the Excel files'
Sub01..Sub50 sheet order -- confirmed against figshare_loader.py's subject_id scheme.

File is MATLAB v7.3 (HDF5); read with h5py rather than scipy.io.loadmat.
"""
from __future__ import annotations

import h5py
import numpy as np


def _to_1d(dataset) -> np.ndarray:
    return np.array(dataset).flatten()


def load_stroke_spatiotemporal(
    mat_path: str,
    step_length_definition: str = "successive_footfall",
) -> list[dict]:
    """Returns one dict per (subject, side) with gait_speed_m_s, cadence_steps_min,
    step_length_m, and n_strides (strides averaged over). Step-length *symmetry* is a
    subject-level (not side-level) quantity -- see build_spatiotemporal_lookup() below.

    "side" here labels which leg's heel-strike *defines* the stride window (P_ICstart..
    P_ICstop for side="P"), NOT which leg's step length gets reported for that entry --
    see step_length_m note below, this matters and is easy to get backwards.

    Stride length: own-foot HEE marker anterior-posterior (x) displacement over one full
    stride (ICstart -> ICstop of the same side) -- standard definition, needs only the
    stride-defining leg's own marker.

    Step length -- TWO operational definitions exist and give different numbers for
    some subjects; neither is declared clinical ground truth here (audit P1-3):

    - "successive_footfall" (default; the v1 behavior): contralateral HEE position at
      the contralateral IC (IC_cnt) minus the stride-side HEE position at STRIDE START
      (its own IC). Successive-footfall distance in the Vicon tradition. A v1 docstring
      wrongly described this as "distance between the two feet at the moment the other
      foot lands" -- that wording matches the OTHER definition below; the code and
      docstring now agree.
    - "instantaneous": both heels' positions sampled at the SAME instant (the
      contralateral IC), i.e. true inter-foot distance at that moment. Audit
      sensitivity check: switching definitions moved Sub45's symmetry index from
      +5.80% to -0.27% and Sub03's from -81.35% to -89.93% -- material for some
      subjects, so the choice must be stated, not assumed.

    Either way, the step-length entry for side="P" reports the NON-paretic leg's step
    (the P-foot is planted while the N-foot swings and lands), and vice versa -- easy
    to get backwards. The contralateral marker comes from the MAT's paired field
    (e.g. PsideSegm_NsideData, time-aligned to the P-stride's 0-1000 grid); using only
    the stride-defining leg's own marker (an early version did) computes near-zero
    garbage since a planted foot barely moves. IC_cnt is an absolute frame index, so
    it's located in the 0-1000 grid by linear interpolation between ICstart/ICstop.

    Internal consistency (NOT ground-truth validation): under the default definition,
    a stride's own stride_length ≈ non-paretic step + paretic step. The independent
    external check is on SPEED: computed speeds match the original paper's
    Supplementary Table 5 to its published 4-decimal precision (max diff 0.00005 m/s),
    which does not depend on the step-length definition choice.
    """
    results = []
    with h5py.File(mat_path, "r") as f:
        sub = f["Sub"]
        n_subjects = sub["events"].shape[0]

        for i in range(n_subjects):
            subject_id = f"Sub{i + 1:02d}"
            events = f[sub["events"][i, 0]]
            meas = f[sub["meas_char"][i, 0]]
            video_fs = float(_to_1d(meas["VideoFrameRate"])[0])

            side_config = [
                ("P", "PsideSegm_PsideData", "PsideSegm_NsideData"),
                ("N", "NsideSegm_NsideData", "NsideSegm_PsideData"),
            ]
            for side, own_key, other_key in side_config:
                ic_start = _to_1d(events[f"{side}_ICstart"])
                ic_stop = _to_1d(events[f"{side}_ICstop"])
                ic_cnt = _to_1d(events[f"{side}_IC_cnt"])
                own_group = f[sub[own_key][i, 0]]
                other_group = f[sub[other_key][i, 0]]
                if ic_start.size == 0 or "HEE" not in own_group or "HEE" not in other_group:
                    continue

                own_hee_x = np.array(own_group["HEE"]["x"])  # (n_strides, 1001), mm
                other_hee_x = np.array(other_group["HEE"]["x"])
                stride_time_s = (ic_stop - ic_start) / video_fs
                stride_length_m = np.abs(own_hee_x[:, -1] - own_hee_x[:, 0]) / 1000.0
                with np.errstate(invalid="ignore", divide="ignore"):
                    # a stride with ic_stop == ic_start (0/0) yields NaN here by design --
                    # excluded below via the isfinite(frac) check, not an error to surface.
                    frac = np.clip((ic_cnt - ic_start) / (ic_stop - ic_start), 0, 1)

                valid = (
                    np.isfinite(stride_time_s) & (stride_time_s > 0)
                    & np.isfinite(stride_length_m) & np.isfinite(frac)
                )
                if not valid.any():
                    continue

                speed = stride_length_m[valid] / stride_time_s[valid]
                cadence = 120.0 / stride_time_s[valid]  # 2 steps/stride

                idx = np.round(frac[valid] * 1000).astype(int)
                own_valid = own_hee_x[valid]
                other_valid = other_hee_x[valid]
                if step_length_definition == "successive_footfall":
                    own_ref = own_valid[:, 0]  # stride-side heel at its own IC (stride start)
                elif step_length_definition == "instantaneous":
                    own_ref = own_valid[np.arange(len(idx)), idx]  # both heels at contralateral IC
                else:
                    raise ValueError(f"unknown step_length_definition: {step_length_definition!r}")
                step_length_m = np.abs(other_valid[np.arange(len(idx)), idx] - own_ref) / 1000.0

                results.append(
                    {
                        "subject_id": subject_id,
                        "side": side,
                        "gait_speed_m_s": float(np.mean(speed)),
                        "cadence_steps_min": float(np.mean(cadence)),
                        # step_length_m here is the CONTRALATERAL leg's step (see docstring)
                        "step_length_m": float(np.mean(step_length_m)),
                        "n_strides": int(valid.sum()),
                        "step_length_definition": step_length_definition,
                    }
                )

    return results


def build_spatiotemporal_lookup(records: list[dict]) -> dict:
    """Combines the per-side records above into a lookup keyed by (subject_id, side) ->
    {gait_speed_m_s, cadence_steps_min, step_length_symmetry_index} ready to pass into
    extract_summary_from_normalized(). Symmetry index is computed per subject (needs
    both sides) via spatiotemporal.symmetry_index() and attached to both of that
    subject's side entries.

    Mind the label flip from load_stroke_spatiotemporal(): the side="N" record's
    step_length_m is the PARETIC leg's step (contralateral to the N-stride that defines
    it), and the side="P" record's step_length_m is the NON-paretic leg's step -- so
    the "affected" value for symmetry_index() comes from the side="N" record.
    """
    from .spatiotemporal import symmetry_index

    by_subject: dict[str, dict] = {}
    for r in records:
        by_subject.setdefault(r["subject_id"], {})[r["side"]] = r

    lookup = {}
    for subject_id, sides in by_subject.items():
        sym = None
        if "P" in sides and "N" in sides:
            paretic_step_m = sides["N"]["step_length_m"]
            non_paretic_step_m = sides["P"]["step_length_m"]
            sym = symmetry_index(paretic_step_m, non_paretic_step_m)
        for side, r in sides.items():
            lookup[(subject_id, side)] = {
                "gait_speed_m_s": r["gait_speed_m_s"],
                "cadence_steps_min": r["cadence_steps_min"],
                "step_length_symmetry_index": sym,
                # carried so serialized text can never claim a different definition
                # than the one the number was computed under (audit round 2, R6)
                "step_length_definition": r.get("step_length_definition"),
            }
    return lookup
