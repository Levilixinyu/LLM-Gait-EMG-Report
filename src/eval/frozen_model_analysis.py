"""Planned model analysis for frozen metrics with per-rater category differences.

The original hash-bound formal_analysis module remains unchanged.
"""
from itertools import combinations

import numpy as np

from .formal_analysis import ERRORS, FLAGS, LABELS, bca_mean_interval, binary_summary


def analyze_report_metrics(roster, models, metrics, *, seed=20260918, resamples=20000):
    """Apply the same planned estimands to validated report-outcome snapshots.

    A shared outcome snapshot may intentionally omit error_categories when
    raters have different category sets. In that case category totals remain
    unavailable, rather than selecting one rater or manufacturing a union.
    """
    models = tuple(sorted(models))
    if len(models) != 3 or len(set(models)) != 3 or not roster:
        raise ValueError("Require three distinct models and an explicit roster")
    if any(row["group"] not in {"stroke", "control"} for row in roster.values()):
        raise ValueError("Unknown roster cohort")
    if set(metrics) != {(case, model) for case in roster for model in models}:
        raise ValueError("Missing or unregistered planned metric slots")
    for (case, _), row in metrics.items():
        if row['K'] != len(roster[case]['required_ids']):
            raise ValueError("Frozen coverage denominator mismatch")
        if sum(row['counts'].values()) + row['unknown_items'] != row['K']:
            raise ValueError("Coverage counts do not match fixed denominator")
        for field in ('any_error', 'joint'):
            if row[field] is not None and type(row[field]) is not bool:
                raise ValueError("Binary outcomes must preserve True/False/None")
        expected_coverage = row['counts']['Covered'] / row['K'] if not row['unknown_items'] else None
        if row['coverage'] != expected_coverage:
            raise ValueError("Full coverage must retain the fixed denominator and unknowns")
    cases = sorted(case for case in roster if roster[case]["group"] == "stroke")
    complete = [case for case in cases if all(metrics[case, m]["coverage"] is not None for m in models)]
    if resamples != 20000 or seed != 20260918:
        raise ValueError("Changing the prespecified resampling settings needs an amendment")
    indices = np.random.default_rng(seed).integers(0, len(complete), size=(resamples, len(complete))) \
        if complete else np.empty((resamples, 0), dtype=np.int64)
    primary = {"case_ids": complete, "excluded_case_ids": sorted(set(cases) - set(complete)),
               "n": len(complete), "seed": seed, "resamples": resamples, "paired_model_means": {},
               "contrasts": {}}
    for model in models:
        primary["paired_model_means"][model] = float(np.mean([metrics[c, model]["coverage"] for c in complete])) \
            if complete else None
    for a, b in combinations(models, 2):
        differences = np.array([metrics[c, a]["coverage"] - metrics[c, b]["coverage"] for c in complete]) * 100
        primary["contrasts"][f"{a} - {b}"] = {
            "mean_difference_percentage_points": float(differences.mean()) if len(differences) else None,
            "descriptive_95": bca_mean_interval(differences, indices, 0.95),
            "family_adjusted_98_3333": bca_mean_interval(differences, indices, 1 - 0.05 / 3),
            "all_planned_missingness_bounds_percentage_points": [
                float(np.mean([metrics[c, a]["coverage_bounds"][0] - metrics[c, b]["coverage_bounds"][1]
                               for c in cases])) * 100,
                float(np.mean([metrics[c, a]["coverage_bounds"][1] - metrics[c, b]["coverage_bounds"][0]
                               for c in cases])) * 100,
            ] if cases else None,
        }
    cohorts = {}
    for group in ("stroke", "control"):
        group_cases = sorted(c for c in roster if roster[c]["group"] == group)
        summaries = {}
        for model in models:
            rows = [metrics[c, model] for c in group_cases]
            known = [row["coverage"] for row in rows if row["coverage"] is not None]
            summaries[model] = {
                "available_case_coverage_mean": float(np.mean(known)) if known else None,
                "available_case_coverage_n": len(known),
                "all_planned_coverage_bounds": np.mean([r["coverage_bounds"] for r in rows], axis=0).tolist()
                if rows else None,
                "coverage_category_counts": {label: sum(r["counts"][label] for r in rows) for label in LABELS},
                "unknown_coverage_items": sum(r["unknown_items"] for r in rows),
                "any_error": binary_summary([r["any_error"] for r in rows], control=group == "control"),
                "joint": binary_summary([r["joint"] for r in rows], control=group == "control",
                                        point_eligible=[r["joint_complete_review"] for r in rows]),
                "G03_counts": {(label if label is not None else "Unknown"): sum(r["g03"] == label for r in rows)
                               for label in (*LABELS, None)},
                "confirmed_issue_counts": [r["confirmed_issue_count"] for r in rows],
                "confirmed_issue_count_case_order": group_cases,
                "completed_nonpending_issue_reviews": sum(r["issue_review_complete"] and r["pending_issue_count"] == 0 for r in rows),
                "confirmed_issue_categories": {tag: sum(r["error_categories"][tag] for r in rows) for tag in sorted(ERRORS)}
                if all(r.get('error_categories') is not None for r in rows) else None,
                "control_flags": {flag: binary_summary([r["control_flags"][flag] for r in rows], control=True)
                                  for flag in sorted(FLAGS)} if group == "control" else {},
            }
        matched = {}
        outcomes = ["any_error", "joint"] + (["pathology", "normality"] if group == "control" else [])
        for outcome in outcomes:
            matched[outcome] = {}
            for a, b in combinations(models, 2):
                pairs = []
                for case in group_cases:
                    left, right = metrics[case, a], metrics[case, b]
                    x = left["control_flags"][outcome] if outcome in FLAGS else left[outcome]
                    y = right["control_flags"][outcome] if outcome in FLAGS else right[outcome]
                    if outcome == "joint" and not (left["joint_complete_review"] and right["joint_complete_review"]):
                        continue
                    if x is not None and y is not None:
                        pairs.append((x, y))
                matched[outcome][f"{a} - {b}"] = {
                    "matched_n": len(pairs), "A_positive_B_negative": pairs.count((True, False)),
                    "A_negative_B_positive": pairs.count((False, True)),
                    "both_positive": pairs.count((True, True)), "both_negative": pairs.count((False, False)),
                    "difference_percentage_points": float(np.mean([int(x) - int(y) for x, y in pairs]) * 100)
                    if pairs else None,
                }
        cohorts[group] = {"by_model": summaries, "exploratory_matched_binary": matched}
    return {"primary_stroke": primary, "cohort_summaries": cohorts,
            "per_report": [{"case_id": c, "model": m, **metrics[c, m]} for c, m in sorted(metrics)]}, indices
