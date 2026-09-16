"""EMG signal processing: filtering, envelope extraction, onset/offset detection,
amplitude normalization, co-contraction, and deviation from a normative reference."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, filtfilt


def bandpass_filter(signal: np.ndarray, fs: float, low_hz: float = 20.0, high_hz: float = 450.0, order: int = 4) -> np.ndarray:
    nyq = fs / 2
    high_hz = min(high_hz, nyq * 0.99)
    b, a = butter(order, [low_hz / nyq, high_hz / nyq], btype="band")
    return filtfilt(b, a, signal)


def linear_envelope(signal: np.ndarray, fs: float, lowpass_hz: float = 6.0, order: int = 4) -> np.ndarray:
    nyq = fs / 2
    b, a = butter(order, lowpass_hz / nyq, btype="low")
    rectified = np.abs(signal)
    return filtfilt(b, a, rectified)


def raw_to_envelope(raw_emg: np.ndarray, fs: float) -> np.ndarray:
    filtered = bandpass_filter(raw_emg, fs)
    return linear_envelope(filtered, fs)


def detect_onset_offset(
    envelope: np.ndarray,
    fs: float,
    baseline_window: tuple[int, int] | None = None,
    k: float = 3.0,
    min_duration_ms: float = 25.0,
) -> list[tuple[int, int]]:
    """Hodges & Bui (1996) threshold-based onset/offset detection on a continuous,
    time-domain envelope. Returns a list of (onset_idx, offset_idx) burst windows.

    When no static baseline_window is given (common for gait-only exports with no
    quiet-standing reference trial), the lowest 10th percentile of the envelope is used
    as a baseline proxy. Validate this against the dataset's actual reference trials
    once the real file format is available — see data_loader.py.
    """
    if baseline_window is not None:
        start, end = baseline_window
        baseline = envelope[start:end]
    else:
        baseline = envelope[envelope <= np.percentile(envelope, 10)]

    threshold = baseline.mean() + k * baseline.std()
    above = envelope > threshold

    min_samples = int(min_duration_ms / 1000 * fs)
    bursts = []
    i = 0
    n = len(above)
    while i < n:
        if above[i]:
            j = i
            while j < n and above[j]:
                j += 1
            if j - i >= min_samples:
                bursts.append((i, j))
            i = j
        else:
            i += 1
    return bursts


@dataclass
class ActivationProfile:
    """Full above-threshold description of one ensemble-averaged, gait-cycle-resampled
    envelope. Replaces the single (onset, offset) pair that v1 used -- audit
    PROJECT_AUDIT_2026-09-16 P0-1 showed the single-pair version silently dropped
    later bursts (e.g. Sub50 paretic TA's 56.74-100% swing burst, Sub05 paretic GAS's
    74.53-86.61% burst containing that subject's max |z|), which then induced
    over-interpretation downstream ("absent swing-phase TA activation").

    intervals: list of (onset_pct, offset_pct). onset > offset means the interval
    wraps across the 100%->0% cycle boundary (the cycle is treated as circular; a
    wrapped run is ONE interval, not two). All retained intervals satisfy
    min_duration_pct.
    above_threshold_pct: % of cycle samples above threshold -- reported separately
    because "intervals" alone understate activity when many short sub-min-duration
    runs exist.
    crosses_cycle_boundary: whether the envelope is above threshold at both 0% and
    100% (activity continuing across the cycle-defining event; an onset reported at
    0% is then a window boundary, not a physiological onset).
    threshold_value / threshold_frac_of_peak / peak_value: the absolute threshold
    actually applied, how it was derived, and the curve peak -- so the definition
    travels with every result instead of living only in code.
    """

    intervals: list  # list[tuple[float, float]]
    above_threshold_pct: float
    crosses_cycle_boundary: bool
    threshold_value: float
    threshold_frac_of_peak: float
    peak_value: float
    peak_pct: float
    nan_pct: float = 0.0  # % of samples that were NaN (treated as below threshold --
    # a masking policy, which can split an interval; nonzero values are a data-quality
    # flag that must reach the serialized output. Main dataset has none (audit R8).


def analyze_activation(
    cycle: np.ndarray,
    threshold_frac: float = 0.2,
    min_duration_pct: float = 3.0,
) -> ActivationProfile | None:
    """Circular multi-interval activation analysis on a 0-100% gait-cycle envelope.

    Threshold semantics (v2 primary definition, frozen 2026-09-16): the absolute
    threshold is `threshold_frac * nanmax(cycle)` -- a fraction of THIS curve's own
    peak. v1's Excel-path code compared against a fixed absolute 0.2 while its
    docstring claimed fraction-of-peak; the raw path normalized to peak=1 first, making
    fixed 0.2 accidentally equal 20%-of-peak there. This function makes the
    fraction-of-peak semantics explicit and identical for both paths. Fixed-absolute
    thresholding remains available for sensitivity analysis by passing a pre-scaled
    curve or post-filtering.

    NaN samples are treated as below threshold (masking policy -- can split an
    interval; the NaN fraction is reported in nan_pct as a quality flag). Returns
    None for an all-NaN curve.

    Min-duration convention (audit R8): the criterion is SAMPLE COUNT --
    `min_samples = int(min_duration_pct/100 * n)` consecutive above-threshold samples
    (30 of 1001 at the default 3%). The reported endpoint span (b - a) of a retained
    interval is computed on the 0..n-1 grid and is a distinct quantity from the
    sample-count fraction; do not treat the two as interchangeable.
    """
    valid = np.isfinite(cycle)
    if not valid.any():
        return None
    n = len(cycle)
    peak_value = float(np.nanmax(cycle))
    peak_pct = float(100 * int(np.nanargmax(cycle)) / (n - 1))
    threshold = threshold_frac * peak_value
    above = np.where(valid, cycle > threshold, False)

    above_threshold_pct = float(100 * above.mean())
    crosses = bool(above[0] and above[-1])

    # circular run detection: rotate so the scan starts at a below-threshold sample,
    # which turns any boundary-wrapping run into a single contiguous run
    if above.all():
        intervals = [(0.0, 100.0)]
    else:
        start = int(np.argmin(above))  # first False
        rotated = np.roll(above, -start)
        min_samples = max(1, int(min_duration_pct / 100 * n))
        intervals = []
        i = 0
        while i < n:
            if rotated[i]:
                j = i
                while j < n and rotated[j]:
                    j += 1
                if j - i >= min_samples:
                    a = (i + start) % n
                    b = (j - 1 + start) % n
                    intervals.append((100 * a / (n - 1), 100 * b / (n - 1)))
                i = j
            else:
                i += 1
        intervals.sort(key=lambda t: t[0])

    return ActivationProfile(
        intervals=intervals,
        above_threshold_pct=above_threshold_pct,
        crosses_cycle_boundary=crosses,
        threshold_value=float(threshold),
        threshold_frac_of_peak=threshold_frac,
        peak_value=peak_value,
        peak_pct=peak_pct,
        nan_pct=float(100 * (~valid).mean()),
    )


def onset_offset_pct_from_cycle(
    mean_cycle_norm: np.ndarray,
    threshold: float = 0.2,
    min_duration_pct: float = 3.0,
) -> tuple[float | None, float | None]:
    """DEPRECATED v1 behavior kept only for comparison against frozen v1 outputs:
    returns the FIRST qualifying interval and drops everything after it, does not
    handle cycle-boundary wrap, and applies `threshold` as an ABSOLUTE value (its v1
    docstring wrongly said fraction-of-peak). Use analyze_activation() for anything
    new -- see audit PROJECT_AUDIT_2026-09-16 P0-1/P0-2 for the failure cases.
    """
    n = len(mean_cycle_norm)
    above = mean_cycle_norm > threshold
    min_samples = max(1, int(min_duration_pct / 100 * n))
    i = 0
    while i < n:
        if above[i]:
            j = i
            while j < n and above[j]:
                j += 1
            if j - i >= min_samples:
                return (100 * i / n, 100 * j / n)
            i = j
        else:
            i += 1
    return (None, None)


def normalize_to_gait_cycle(
    signal: np.ndarray,
    event_times_s: list[float],
    fs: float,
    n_points: int = 101,
) -> np.ndarray:
    """Resample each inter-event segment (e.g. consecutive heel strikes, in seconds)
    to a common 0-100% gait cycle grid. Returns shape (n_cycles, n_points)."""
    event_idx = [int(round(t * fs)) for t in event_times_s]
    cycles = []
    for start, end in zip(event_idx[:-1], event_idx[1:]):
        segment = signal[start:end]
        if len(segment) < 2:
            continue
        x_old = np.linspace(0, 100, len(segment))
        x_new = np.linspace(0, 100, n_points)
        cycles.append(np.interp(x_new, x_old, segment))
    return np.array(cycles)


def normalize_amplitude(envelope: np.ndarray, method: str = "peak") -> np.ndarray:
    if method == "peak":
        ref = envelope.max()
    elif method == "mean":
        ref = envelope.mean()
    else:
        raise ValueError(f"unknown normalization method: {method}")
    if ref == 0:
        return envelope
    return envelope / ref


def co_contraction_index(agonist_norm: np.ndarray, antagonist_norm: np.ndarray) -> float:
    """Falconer & Winter (1985) CCI. Inputs should be amplitude-normalized (0-1 scale),
    same length, same time base (e.g. both on the 0-100% gait cycle grid)."""
    common = np.minimum(agonist_norm, antagonist_norm)
    denom = agonist_norm.sum() + antagonist_norm.sum()
    if denom == 0:
        return 0.0
    return 2 * common.sum() / denom


def deviation_from_normative(
    patient_cycle_mean: np.ndarray,
    normative_mean: np.ndarray,
    normative_sd: np.ndarray,
) -> np.ndarray:
    """Per-sample z-score of a patient's cycle-mean curve relative to a normative
    reference, both on the same 0-100% gait cycle grid."""
    sd_safe = np.where(normative_sd == 0, np.finfo(float).eps, normative_sd)
    return (patient_cycle_mean - normative_mean) / sd_safe
