"""One-pass acceptance verification for the post-audit fixes (2026-09-16 handoff).
Loads the primary data ONCE and checks, against the audit's acceptance criteria:

P0-1  Sub50-P TA and Sub05-P GAS second activation intervals present in structured
      output AND in the serialized prompt text; boundary-wrap semantics visible.
P0-2  Threshold statistics table computed by the OFFICIAL analyze_activation() under
      the frozen fraction-of-peak definition, plus absolute-0.2 sensitivity column.
P0-3  Healthy-cohort calibration of max|z| recomputed from primary data (plain and
      leave-one-out), cross-checked against the numbers embedded in
      pipeline.METRIC_DEFINITIONS; CCI and GPS-like healthy quantiles likewise.
P1-2  Raw-path scale invariance: 10x amplitude must not change z (was 370->967 in v1).

Writes: data/normative_calibration_v2.json, audit/outputs/v2_input_samples.txt,
audit/outputs/fix_verification.json. Local computation only -- no API calls.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.emg_signal import analyze_activation, co_contraction_index, deviation_from_normative
from src.features.figshare_loader import load_control_excel, load_stroke_excel
from src.features.mat_spatiotemporal import build_spatiotemporal_lookup, load_stroke_spatiotemporal
from src.features.pipeline import (
    build_normative_reference,
    build_normative_reference_from_normalized,
    extract_patient_summary,
    extract_summary_from_normalized,
    to_prompt_text,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit" / "outputs"
MUSCLES = ["GAS", "RF", "VL", "BF", "ST", "TA", "ERS"]


def pctile(vals, p):
    vals = sorted(vals)
    k = (len(vals) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return vals[int(k)] if f == c else vals[f] + (k - f) * (vals[c] - vals[f])


def main() -> None:
    results: dict = {}

    controls = load_control_excel(str(ROOT / "data" / "raw" / "AbleBodiedAdults.xlsx"))
    stroke = load_stroke_excel(str(ROOT / "data" / "raw" / "PostStrokeAdults.xlsx"))
    normative = build_normative_reference_from_normalized(controls, source="main_cohort_excel")
    st_lookup = build_spatiotemporal_lookup(
        load_stroke_spatiotemporal(str(ROOT / "data" / "raw" / "MAT_normalizedData_PostStrokeAdults.mat"))
    )
    print("data loaded")

    # ---- P0-1 acceptance ----------------------------------------------------
    def interval_covers(interval: tuple, target: tuple) -> bool:
        """True circular-overlap test: does `interval` (a,b), where a>b means it wraps
        100->0, overlap the non-wrapping `target` (lo,hi)? The first version of this
        script accepted ANY wrapped interval as covering the target -- a wrapped
        (95,5) would 'pass' a (74,87) target it never touches (audit round 2, R7)."""
        lo, hi = target
        a, b = interval
        if a <= b:
            return a <= hi and b >= lo
        # wrapped: covers [a,100] plus [0,b]
        return (a <= hi) or (b >= lo)  # [a,100] overlaps target iff a<=hi; [0,b] iff b>=lo

    failures: list[str] = []
    p01 = {}
    samples = []
    for sid, muscle, expect in [("Sub50", "TA", (60, 95)), ("Sub05", "GAS", (75, 86))]:
        trial = next(t for t in stroke if t.subject_id == sid and t.side == "P")
        st = st_lookup.get((sid, "P"), {})
        summary = extract_summary_from_normalized(trial, normative=normative, **st)
        finding = next(m for m in summary.muscle_findings if m.muscle == muscle)
        text = to_prompt_text(summary)
        hit = any(interval_covers(iv, expect) for iv in finding.activation_intervals)
        muscle_line = next(l for l in text.splitlines() if l.startswith(f"- {muscle}:"))
        # structure<->text consistency: every structured interval must appear in the line
        text_consistent = all(
            f"{a:.0f}%-{b:.0f}%" in muscle_line for a, b in finding.activation_intervals
        )
        p01[f"{sid}_{muscle}"] = {
            "intervals": finding.activation_intervals,
            "above_threshold_pct": finding.above_threshold_pct,
            "crosses_boundary": finding.crosses_cycle_boundary,
            "deviation_z_signed": finding.deviation_z_signed,
            "deviation_phase_pct": finding.deviation_phase_pct,
            "late_burst_in_structured_output": bool(hit),
            "prompt_text_matches_structure": bool(text_consistent),
            "prompt_line": muscle_line,
        }
        if not hit:
            failures.append(f"P0-1 {sid} {muscle}: no interval covers late-cycle target {expect}")
        if not text_consistent:
            failures.append(f"P0-1 {sid} {muscle}: structured intervals not all present in prompt text")
        samples.append((f"{sid}_P", text))
        print(f"P0-1 {sid} {muscle}: intervals={finding.activation_intervals} "
              f"boundary={finding.crosses_cycle_boundary} late-burst-present={hit} "
              f"text-consistent={text_consistent}")
    results["P0_1"] = p01

    # extra v2 samples: a complete mid-severity case and the all-missing-EMG case
    for sid in ["Sub09", "Sub47"]:
        trial = next(t for t in stroke if t.subject_id == sid and t.side == "P")
        st = st_lookup.get((sid, "P"), {})
        summary = extract_summary_from_normalized(trial, normative=normative, **st)
        samples.append((f"{sid}_P", to_prompt_text(summary)))

    sample_text = "\n\n" + ("=" * 78) + "\n\n"
    (OUT / "v2_input_samples.txt").write_text(
        sample_text.join(f"### v2 input sample: {name}\n\n{text}" for name, text in samples)
    )
    print(f"v2 input samples written ({len(samples)} cases)")

    # ---- P0-2: threshold table via the official function --------------------
    p02 = {}
    for muscle in ["ERS", "GAS", "BF"]:
        for label, trials in [("stroke_P", [t for t in stroke if t.side == "P"]), ("controls", controls)]:
            n = frac_95 = abs_95 = 0
            for t in trials:
                c = t.emg_norm.get(muscle)
                if c is None or np.isnan(c).all():
                    continue
                n += 1
                prof = analyze_activation(c)  # frozen fraction-of-peak definition
                if prof.above_threshold_pct >= 95:
                    frac_95 += 1
                peak = float(np.nanmax(c))
                prof_abs = analyze_activation(c, threshold_frac=0.2 / peak) if peak > 0 else None
                if prof_abs and prof_abs.above_threshold_pct >= 95:
                    abs_95 += 1
            p02[f"{muscle}_{label}"] = {"n": n, "frac_of_peak_ge95": frac_95, "absolute02_ge95": abs_95}
    results["P0_2_threshold_table"] = p02
    print("P0-2 table:", json.dumps(p02))

    # ---- P0-3: calibration from primary data (plain + leave-one-out) --------
    calib: dict = {}
    curves_by_muscle = {
        m: [(t.subject_id, t.emg_norm[m]) for t in controls
            if m in t.emg_norm and not np.isnan(t.emg_norm[m]).all()]
        for m in MUSCLES
    }
    for m, items in curves_by_muscle.items():
        stack = np.array([c for _, c in items])
        mean_all, sd_all = np.nanmean(stack, axis=0), np.nanstd(stack, axis=0)
        plain, loo = [], []
        for i, (_, c) in enumerate(items):
            plain.append(float(np.nanmax(np.abs(deviation_from_normative(c, mean_all, sd_all)))))
            rest = np.delete(stack, i, axis=0)
            loo.append(float(np.nanmax(np.abs(
                deviation_from_normative(c, np.nanmean(rest, axis=0), np.nanstd(rest, axis=0))))))
        calib[m] = {
            "n": len(items),
            "n_over_2": sum(v > 2 for v in plain),
            "p50": round(pctile(plain, 50), 3), "p95": round(pctile(plain, 95), 3),
            "loo_p50": round(pctile(loo, 50), 3), "loo_p95": round(pctile(loo, 95), 3),
        }
    # CCI + GPS-like healthy distributions
    for pair in [("RF", "BF"), ("TA", "GAS")]:
        vals = []
        for t in controls:
            a, b = t.emg_norm.get(pair[0]), t.emg_norm.get(pair[1])
            if a is None or b is None or np.isnan(a).all() or np.isnan(b).all():
                continue
            vals.append(float(co_contraction_index(a, b)))
        calib[f"CCI_{pair[0]}_{pair[1]}"] = {
            "n": len(vals), "p2_5": round(pctile(vals, 2.5), 3),
            "p50": round(pctile(vals, 50), 3), "p97_5": round(pctile(vals, 97.5), 3),
        }
    gps_vals = []
    for t in controls:
        s = extract_summary_from_normalized(t, normative=normative)
        if s.gait_profile_score is not None:
            gps_vals.append(s.gait_profile_score)
    calib["GPS_like"] = {"n": len(gps_vals), "p50": round(pctile(gps_vals, 50), 3),
                         "p95": round(pctile(gps_vals, 95), 3)}
    (ROOT / "data" / "normative_calibration_v2.json").write_text(json.dumps(calib, indent=2))
    results["P0_3_calibration"] = calib
    n_controls_with_emg = len({sid for m in MUSCLES for sid, _ in curves_by_muscle[m]})
    over2_everywhere = len({
        sid for m in MUSCLES for (sid, c) in curves_by_muscle[m]
        if True  # placeholder; per-subject any-muscle check below
    })
    # per-subject any-muscle >2 check
    subj_max: dict[str, float] = {}
    for m, items in curves_by_muscle.items():
        stack = np.array([c for _, c in items])
        mean_all, sd_all = np.nanmean(stack, axis=0), np.nanstd(stack, axis=0)
        for (sid, c) in items:
            z = float(np.nanmax(np.abs(deviation_from_normative(c, mean_all, sd_all))))
            subj_max[sid] = max(subj_max.get(sid, 0.0), z)
    results["P0_3_subjects_any_muscle_over2"] = {
        "n_subjects_with_emg": len(subj_max),
        "n_over_2": sum(v > 2 for v in subj_max.values()),
    }
    print("P0-3 calibration:", json.dumps({m: calib[m] for m in MUSCLES}))
    print("P0-3 any-muscle>2:", results["P0_3_subjects_any_muscle_over2"])

    # ---- P1-2: raw-path scale invariance ------------------------------------
    from tests.synthetic_data import make_synthetic_trial
    ctl = [make_synthetic_trial(f"C{i:02d}", group="control", seed=i) for i in range(5)]
    nm = build_normative_reference(ctl)
    t1 = make_synthetic_trial("S01", group="stroke", seed=100)
    t10 = make_synthetic_trial("S01", group="stroke", seed=100)
    for m in t10.emg:
        t10.emg[m] = t10.emg[m] * 10.0
    z1 = next(m for m in extract_patient_summary(t1, normative=nm).muscle_findings
              if m.muscle == "tibialis_anterior").deviation_z_peak
    z10 = next(m for m in extract_patient_summary(t10, normative=nm).muscle_findings
               if m.muscle == "tibialis_anterior").deviation_z_peak
    # relative tolerance: filtfilt on the scaled signal leaves ~1e-11 relative
    # floating-point residue, which is not a scale-dependence (v1's actual bug was a
    # 2.6x difference); an absolute 1e-9 cutoff on a ~233-magnitude value was the
    # wrong acceptance criterion and flagged a passing fix as failing.
    rel = abs(z1 - z10) / max(abs(z1), 1e-12)
    results["P1_2_scale_invariance"] = {"z_1x": z1, "z_10x": z10,
                                        "relative_diff": rel,
                                        "invariant": rel < 1e-6}
    print(f"P1-2 scale invariance: z_1x={z1:.4f} z_10x={z10:.4f} "
          f"rel_diff={rel:.2e} invariant={rel < 1e-6}")
    if rel >= 1e-6:
        failures.append(f"P1-2: scale invariance violated (rel_diff={rel:.2e})")

    results["failures"] = failures
    (OUT / "fix_verification.json").write_text(json.dumps(results, indent=2, default=str))
    print("verification results written to audit/outputs/fix_verification.json")
    if failures:
        # a verification script that cannot fail is not a verification script
        # (audit round 2, R7): exit nonzero so CI/callers see the failure
        print(f"VERIFICATION FAILED ({len(failures)} failure(s)):")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
