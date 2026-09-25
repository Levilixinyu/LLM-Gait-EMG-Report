"""Prospective formal-study estimands; no report interpretation or API calls.

Inputs must be human ratings, never labels inferred from report wording. Final
outcomes and independent agreement are separate entry points. This module does
not authorize a batch or turn an agent suggestion into a human adjudication.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from scipy.stats import beta, norm

LABELS = ("Covered", "Partially covered", "Not covered")
ERRORS = {f"E{i:02d}" for i in range(1, 10)}
FLAGS = {"pathology", "normality"}


@dataclass(frozen=True)
class Coverage:
    label: str | None = None
    pending: bool = False

    def __post_init__(self):
        if self.label not in (*LABELS, "Cannot assess", None):
            raise ValueError("Unknown coverage label")

    @property
    def final(self):
        return self.label in LABELS and not self.pending


@dataclass(frozen=True)
class Issue:
    issue_id: str
    decision: str
    categories: tuple[str, ...] = ()
    quote: str = ""
    flags: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.issue_id or self.decision not in (
            "Error", "Acceptable", "Pending adjudication", "Outside case-error scope"
        ):
            raise ValueError("Invalid issue identity or decision")
        if not set(self.categories) <= ERRORS or not set(self.flags) <= FLAGS:
            raise ValueError("Unknown error category or control flag")
        if self.decision in ("Error", "Pending adjudication"):
            if not self.categories or not self.quote.strip():
                raise ValueError("An error or pending issue needs a category and exact quote")
        if self.flags and self.decision not in ("Error", "Pending adjudication"):
            raise ValueError("Control flags annotate confirmed or pending in-scope issues")


@dataclass(frozen=True)
class Assessment:
    case_id: str
    model: str
    available: bool
    coverage: dict[str, Coverage] = field(default_factory=dict)
    g03: Coverage = field(default_factory=Coverage)
    issue_review_complete: bool = False
    issues: tuple[Issue, ...] = ()


def report_metrics(assessment, required_ids, cohort):
    """Keep fixed denominators, pending labels, and partial content distinct."""
    required_ids = tuple(required_ids)
    if not required_ids or len(set(required_ids)) != len(required_ids):
        raise ValueError("Requirements must be nonempty and unique")
    if cohort not in {"stroke", "control"}:
        raise ValueError("Unknown cohort")
    if set(assessment.coverage) - set(required_ids):
        raise ValueError("Unregistered coverage requirement")
    if len({i.issue_id for i in assessment.issues}) != len(assessment.issues):
        raise ValueError("Repeated issue group; combine tags and locations first")
    if cohort != "control" and any(i.flags for i in assessment.issues):
        raise ValueError("Control semantic flags cannot be applied to stroke reports")
    if not assessment.available and (
        assessment.coverage or assessment.g03 != Coverage()
        or assessment.issues or assessment.issue_review_complete
    ):
        raise ValueError("Unavailable output cannot have invented ratings")
    labels = [assessment.coverage.get(key, Coverage()) for key in required_ids]
    counts = Counter(row.label for row in labels if row.final)
    unknown = sum(not row.final for row in labels)
    k = len(labels)
    confirmed = [i for i in assessment.issues if i.decision == "Error"]
    pending = [i for i in assessment.issues if i.decision == "Pending adjudication"]
    any_error = True if confirmed else (
        False if assessment.available and assessment.issue_review_complete and not pending else None
    )
    control_flags = {}
    if cohort == "control":
        for flag in sorted(FLAGS):
            control_flags[flag] = True if any(flag in i.flags for i in confirmed) else (
                False if assessment.available and assessment.issue_review_complete
                and not any(flag in i.flags for i in pending) else None
            )
    g03 = assessment.g03.label if assessment.g03.final else None
    complete_review = bool(assessment.available and not unknown and g03 is not None
                           and assessment.issue_review_complete and not pending)
    joint = None
    if assessment.available:
        if confirmed or any(row.final and row.label != "Covered" for row in labels) or (
            assessment.g03.final and g03 != "Covered"
        ):
            joint = False
        elif complete_review:
            joint = True
    return {
        "K": k, "counts": {label: counts[label] for label in LABELS}, "unknown_items": unknown,
        "coverage": counts["Covered"] / k if unknown == 0 else None,
        "coverage_bounds": [counts["Covered"] / k, (counts["Covered"] + unknown) / k],
        "g03": g03, "any_error": any_error, "confirmed_issue_count": len(confirmed),
        "pending_issue_count": len(pending), "issue_review_complete": assessment.issue_review_complete,
        "error_categories": {tag: sum(tag in i.categories for i in confirmed) for tag in sorted(ERRORS)},
        "joint": joint, "joint_complete_review": complete_review, "control_flags": control_flags,
        "available": assessment.available,
    }


def binary_summary(states, *, control=False, point_eligible=None):
    """Exact binomial intervals on explicit denominators; bounds on all slots."""
    states = list(states)
    if any(s is not None and type(s) is not bool for s in states):
        raise ValueError("Binary states must be True, False or None")
    if point_eligible is None:
        point_eligible = [True] * len(states)
    if len(point_eligible) != len(states):
        raise ValueError("Eligibility length mismatch")
    observed = [s for s, eligible in zip(states, point_eligible) if eligible and s is not None]
    n, x = len(observed), sum(observed)
    interval = None if not n else [
        0.0 if x == 0 else float(beta.ppf(0.025, x, n - x + 1)),
        1.0 if x == n else float(beta.ppf(0.975, x + 1, n - x)),
    ]
    total, positive, unknown = len(states), sum(s is True for s in states), states.count(None)
    return {
        "events": x, "evaluable": n, "planned": total, "unknown": unknown,
        "proportion": x / n if n else None, "exact_95_interval": interval,
        "all_planned_bounds": [positive / total, (positive + unknown) / total] if total else None,
        "zero_event_one_sided_95_upper": float(1 - 0.05 ** (1 / n))
        if control and n and x == 0 else None,
    }


def bca_mean_interval(values, indices, confidence):
    """BCa mean interval with an explicitly shared resample-index matrix.

    Bias correction uses the midrank convention also used by SciPy. Acceleration
    is the leave-one-case-out jackknife formula, simplified for the mean.
    No fallback interval is selected when BCa is unavailable.
    """
    values = np.asarray(values, dtype=float)
    indices = np.asarray(indices)
    if not 0 < confidence < 1 or values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("Invalid BCa arguments")
    if len(values) < 2:
        return {"interval": None, "reason": "Fewer than two complete paired cases"}
    if (indices.ndim != 2 or indices.shape[1] != len(values) or len(indices) < 2
            or not np.issubdtype(indices.dtype, np.integer)
            or np.any(indices < 0) or np.any(indices >= len(values))):
        raise ValueError("Invalid resampling matrix")
    observed = values.mean()
    centered = values - observed
    denominator = np.sum(centered ** 2)
    if denominator == 0:
        return {"interval": None, "reason": "Degenerate jackknife distribution"}
    boot = values[indices].mean(axis=1)
    percentile = (np.sum(boot < observed) + np.sum(boot <= observed)) / (2 * len(boot))
    if percentile in (0, 1):
        return {"interval": None, "reason": "Undefined bias correction"}
    z0 = norm.ppf(percentile)
    acceleration = np.sum(centered ** 3) / (6 * denominator ** 1.5)
    z = norm.ppf([(1 - confidence) / 2, (1 + confidence) / 2])
    divisors = 1 - acceleration * (z0 + z)
    if np.any(divisors <= 0):
        return {"interval": None, "reason": "Undefined BCa adjusted quantiles"}
    quantiles = norm.cdf(z0 + (z0 + z) / divisors)
    interval = np.quantile(boot, quantiles, method="linear")
    if not np.isfinite(interval).all() or interval[0] >= interval[1]:
        return {"interval": None, "reason": "Undefined or degenerate BCa interval"}
    return {"interval": interval.tolist(), "reason": None}


def coverage_agreement(left, right):
    """Input keyed original independent rows, never reconciled labels."""
    if set(left) != set(right):
        raise ValueError("Independent reviews must have the same planned row keys")
    matrix = np.zeros((3, 3), dtype=np.int64)
    excluded = 0
    for key in sorted(left):
        a, b = left[key], right[key]
        if not a.final or not b.final:
            excluded += 1
            continue
        matrix[LABELS.index(a.label), LABELS.index(b.label)] += 1
    n = int(matrix.sum())
    observed = float(np.trace(matrix) / n) if n else None
    expected = float(np.dot(matrix.sum(axis=0), matrix.sum(axis=1)) / n ** 2) if n else None
    return {
        "labels": list(LABELS), "cross_tabulation": matrix.tolist(), "jointly_assessable": n,
        "excluded_unknown_or_pending": excluded, "raw_agreement": observed,
        "unweighted_kappa": (observed - expected) / (1 - expected)
        if n and expected < 1 else None,
    }


def binary_agreement(left, right):
    """Completed independent report-level any-error flags, not issue-level kappa."""
    if set(left) != set(right):
        raise ValueError("Binary reviews must have identical planned keys")
    matrix = np.zeros((2, 2), dtype=np.int64)
    for key in sorted(left):
        if left[key] is not None and right[key] is not None:
            matrix[int(left[key]), int(right[key])] += 1
    n = int(matrix.sum())
    observed = float(np.trace(matrix) / n) if n else None
    expected = float(np.dot(matrix.sum(axis=0), matrix.sum(axis=1)) / n ** 2) if n else None
    return {"labels": [False, True], "cross_tabulation": matrix.tolist(), "jointly_assessable": n,
            "excluded_incomplete_or_unknown": len(left) - n, "raw_agreement": observed,
            "unweighted_kappa": (observed - expected) / (1 - expected) if n and expected < 1 else None}


def independent_agreement(roster, models, left, right):
    """Separate cohort/domain summaries from two locked independent assessments."""
    expected = {(c, m) for c in roster for m in models}
    by_rater = []
    for assessments in (left, right):
        rows = {(a.case_id, a.model): a for a in assessments}
        if len(rows) != len(assessments) or set(rows) != expected:
            raise ValueError("Independent review slot roster mismatch")
        by_rater.append(rows)
    results = {}
    for group in ("stroke", "control"):
        domains = {"case_requirements": [], "G03": [], "any_error": []}
        for rows in by_rater:
            case_rows, g03_rows, errors = {}, {}, {}
            for key in sorted(expected):
                case, model = key
                if roster[case]["group"] != group:
                    continue
                a = rows[key]
                metric = report_metrics(a, roster[case]["required_ids"], group)
                for requirement in roster[case]["required_ids"]:
                    case_rows[case, model, requirement] = a.coverage.get(requirement, Coverage())
                g03_rows[key] = a.g03
                errors[key] = metric["any_error"] if a.issue_review_complete else None
            domains["case_requirements"].append(case_rows)
            domains["G03"].append(g03_rows)
            domains["any_error"].append(errors)
        results[group] = {"case_requirements": coverage_agreement(*domains["case_requirements"]),
                          "G03": coverage_agreement(*domains["G03"]),
                          "any_error": binary_agreement(*domains["any_error"])}
    return results


def assessments_from_review(normalized, mapping, roster):
    """Convert a validated locked return without changing any human label.

    Call only after both independent locks have passed validation if opening the
    model mapping. This is not a final consensus/adjudication importer.
    """
    reviews = {r["report_id"]: r for r in normalized["review"]}
    if len(reviews) != len(normalized["review"]) or set(reviews) != set(mapping):
        raise ValueError("Locked review and mapping roster differ")
    coverage = {rid: {} for rid in mapping}
    issues = {rid: [] for rid in mapping}
    for row in normalized["coverage"]:
        rid, requirement = row["report_id"], row["requirement_id"]
        if rid not in mapping or requirement in coverage[rid] or row["case_id"] != mapping[rid]["case_id"]:
            raise ValueError("Coverage identity mismatch")
        coverage[rid][requirement] = Coverage(row["decision"], row["adjudication_status"] == "Pending")
    for row in normalized["issues"]:
        rid = row["report_id"]
        if rid not in mapping:
            raise ValueError("Issue identity mismatch")
        issues[rid].append(Issue(row["issue_id"], row["decision"],
                                tuple(x.strip() for x in (row["categories"] or "").split(";") if x.strip()),
                                row["exact_quote"] or "",
                                tuple(f for f in sorted(FLAGS) if row[f"{f}_flag"] == "Yes")))
    output = []
    for rid, source in mapping.items():
        case = source["case_id"]
        if case not in roster or reviews[rid]["case_id"] != case or set(coverage[rid]) != set(roster[case]["required_ids"]) | {"G03"}:
            raise ValueError("Requirement membership mismatch")
        if reviews[rid]["material_status"] == "Unavailable":
            if issues[rid] or any(v.final for v in coverage[rid].values()):
                raise ValueError("Unavailable report has content ratings")
            output.append(Assessment(case, source["model_key"], False))
        else:
            g03 = coverage[rid].pop("G03")
            output.append(Assessment(case, source["model_key"], True, coverage[rid], g03,
                                     reviews[rid]["issue_review_complete"] == "Yes", tuple(issues[rid])))
    return output


def analyze(roster, models, assessments, *, seed=20260918, resamples=20000):
    """Return final outcome summaries and the matrix to save before publication.

    roster maps case ID to {group, required_ids}. Every planned case/model slot
    must be represented, including unavailable reports. Never discover a sample
    by globbing only successful reports. Model keys belong to restricted analysis
    material until independent reviews are locked.
    """
    models = tuple(sorted(models))
    if len(set(models)) != 3 or len(models) != 3 or not roster:
        raise ValueError("Require three distinct models and an explicit roster")
    if any(row["group"] not in {"stroke", "control"} for row in roster.values()):
        raise ValueError("Unknown roster cohort")
    expected = {(case, model) for case in roster for model in models}
    by_slot = {(a.case_id, a.model): a for a in assessments}
    if len(by_slot) != len(assessments) or set(by_slot) != expected:
        raise ValueError("Missing, duplicate or unregistered planned slots")
    metrics = {
        key: report_metrics(a, roster[key[0]]["required_ids"], roster[key[0]]["group"])
        for key, a in by_slot.items()
    }
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
                "confirmed_issue_categories": {tag: sum(r["error_categories"][tag] for r in rows) for tag in sorted(ERRORS)},
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
