"""Spatiotemporal gait parameters, symmetry indices, and ambulation classification.

For the Van Criekinge et al. (2023) dataset, gait speed / cadence / step length are
NOT in the post-processed Excel export -- they're derived from the raw MAT file's gait
events and marker trajectories, see mat_spatiotemporal.py. For a dataset that does
publish these directly, pass values straight into PatientFeatureSummary; use
symmetry_index() below to derive the affected-vs-unaffected asymmetry either way.
"""
from __future__ import annotations


def symmetry_index(value_affected: float, value_unaffected: float) -> float:
    """Robinson symmetry index (%). 0 = perfect symmetry; positive = affected side larger."""
    if value_affected + value_unaffected == 0:
        return 0.0
    return 200 * (value_affected - value_unaffected) / (value_affected + value_unaffected)


def stance_swing_ratio(stance_time: float, swing_time: float) -> float:
    if swing_time == 0:
        return float("inf")
    return stance_time / swing_time


def cadence_steps_per_min(n_steps: int, duration_s: float) -> float:
    if duration_s == 0:
        return 0.0
    return n_steps / duration_s * 60


def classify_ambulation(gait_speed_m_s: float) -> str:
    """Perry et al. (1995, Stroke 26(6):982-9) household/community ambulation
    classification -- the paper itself is confirmed real (verified via PubMed/NCBI
    eutils: correct authors/journal/year/volume), but its abstract describes a more
    granular 6-category modified Hoffer scale, not these exact three speed bands with
    these exact 0.4/0.8 m/s cutoffs. The <0.4 / 0.4-0.8 / >0.8 m/s three-tier framing is
    the standard, consistently-cited simplification attributed to this paper throughout
    the stroke rehab literature (independently corroborated by Bansal et al. 2024 below,
    which uses the same three categories without disputing the cutoffs) -- but this
    hasn't been verified character-for-character against Perry et al.'s full text
    (only the abstract was accessible). If exact fidelity to the original matters
    (e.g. a reviewer presses on it), track down the full text before citing further.

    Computed by the pipeline rather than left for the LLM to infer from memory: the
    exact cutoffs are well-established but not universally memorized identically across
    models, and letting each model apply its own recalled threshold would confound
    "model interpreted the data correctly" with "model happens to recall the same
    clinical cutoff" -- so this is supplied as a data fact, same as a muscle name.

    Caveat (cite in methods/limitations): Bansal, Fox, Clark, Fulk & Rose (2024,
    Neurorehabil Neural Repair 38(8):582-594) found this speed-based scheme reliably
    separates household from community ambulators, but does NOT reliably distinguish
    "limited" from "full" community ambulation in terms of real-world (GPS/accelerometer
    -measured) daily steps. Don't let report text overclaim real-world functional status
    from gait speed alone -- the system prompt already restricts this to objective
    findings + flagged-for-follow-up language, not prognosis.
    """
    if gait_speed_m_s < 0.4:
        return "household ambulator (<0.4 m/s)"
    if gait_speed_m_s < 0.8:
        return "limited community ambulator (0.4-0.8 m/s)"
    return "full community ambulator (>0.8 m/s)"
