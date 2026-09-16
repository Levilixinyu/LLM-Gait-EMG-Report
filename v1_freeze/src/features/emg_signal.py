"""EMG signal processing: filtering, envelope extraction, onset/offset detection,
amplitude normalization, co-contraction, and deviation from a normative reference."""
from __future__ import annotations

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


def onset_offset_pct_from_cycle(
    mean_cycle_norm: np.ndarray,
    threshold: float = 0.2,
    min_duration_pct: float = 3.0,
) -> tuple[float | None, float | None]:
    """Threshold-crossing onset/offset, expressed as % of gait cycle, on an
    amplitude-normalized ensemble-averaged envelope already resampled to 0-100%
    (see normalize_to_gait_cycle). `threshold` is a fraction of peak amplitude.
    Returns (None, None) if no burst exceeds `min_duration_pct` of the cycle.
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
