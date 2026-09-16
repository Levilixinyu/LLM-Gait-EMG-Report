"""Failure-mode tests for analyze_activation() -- each case below is one of the modes
the audit (PROJECT_AUDIT_2026-09-16, P0-1) showed the v1 single-interval function got
wrong or could not represent: multiple bursts, cycle-boundary wrap, full-cycle
activity, no qualifying activity, and missing data."""
from __future__ import annotations

import numpy as np

from src.features.emg_signal import analyze_activation, onset_offset_pct_from_cycle

N = 1001


def _pct(i: int) -> float:
    return 100 * i / (N - 1)


def make_curve(segments: list[tuple[int, int, float]], base: float = 0.02) -> np.ndarray:
    curve = np.full(N, base)
    for start, end, level in segments:
        curve[start:end] = level
    return curve


def test_two_bursts_both_reported():
    # the Sub05-GAS shape: two separated bursts; v1 dropped the second
    curve = make_curve([(250, 380, 0.8), (745, 866, 0.7)])
    prof = analyze_activation(curve)
    assert len(prof.intervals) == 2
    (a1, b1), (a2, b2) = prof.intervals
    assert abs(a1 - _pct(250)) < 0.2 and abs(b1 - _pct(379)) < 0.2
    assert abs(a2 - _pct(745)) < 0.2 and abs(b2 - _pct(865)) < 0.2
    assert not prof.crosses_cycle_boundary
    # v1 behavior really did drop the second burst (regression guard on the deprecated path)
    onset, offset = onset_offset_pct_from_cycle(curve, threshold=0.2)
    assert offset is not None and offset < 40


def test_boundary_wrap_is_one_interval():
    # the Sub50-TA shape: active at both ends of the cycle -- one wrapped interval,
    # not two, and flagged as crossing the boundary
    curve = make_curve([(0, 75, 0.9), (567, N, 0.85)])
    prof = analyze_activation(curve)
    assert prof.crosses_cycle_boundary
    wrapped = [iv for iv in prof.intervals if iv[0] > iv[1]]
    assert len(wrapped) == 1
    a, b = wrapped[0]
    assert abs(a - _pct(567)) < 0.2 and abs(b - _pct(74)) < 0.2


def test_full_cycle_activity():
    curve = np.full(N, 0.6)
    prof = analyze_activation(curve)
    assert prof.intervals == [(0.0, 100.0)]
    assert prof.above_threshold_pct == 100.0
    assert prof.crosses_cycle_boundary


def test_no_qualifying_activity_still_reports_fraction():
    # a burst shorter than min_duration_pct: no interval retained, but the
    # above-threshold fraction still reflects that activity existed
    curve = make_curve([(500, 515, 0.9)])  # 1.5% of cycle < 3% minimum
    prof = analyze_activation(curve)
    assert prof.intervals == []
    assert prof.above_threshold_pct > 0


def test_all_nan_returns_none():
    assert analyze_activation(np.full(N, np.nan)) is None


def test_partial_nan_treated_as_inactive():
    curve = make_curve([(250, 380, 0.8)])
    curve[300:320] = np.nan
    prof = analyze_activation(curve)
    assert prof is not None
    assert all(np.isfinite(v) for iv in prof.intervals for v in iv)


def test_threshold_is_fraction_of_peak():
    # scale invariance: multiplying the curve by 10 must not change the intervals
    curve = make_curve([(250, 380, 0.8), (745, 866, 0.7)])
    p1 = analyze_activation(curve)
    p2 = analyze_activation(curve * 10)
    assert p1.intervals == p2.intervals
    assert abs(p2.threshold_value - 10 * p1.threshold_value) < 1e-12
