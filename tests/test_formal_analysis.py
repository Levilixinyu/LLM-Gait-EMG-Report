"""Synthetic expected-answer checks for the approved prospective estimands."""
from dataclasses import replace

import numpy as np
import pytest
from scipy.stats import bootstrap

from src.eval.frozen_model_analysis import analyze_report_metrics

from src.eval.formal_analysis import (
    Assessment, Coverage, Issue, analyze, bca_mean_interval, binary_summary,
    coverage_agreement, independent_agreement, report_metrics,
)


def assessment(**changes):
    base = Assessment("stroke_A_P", "A", True,
                      {"r1": Coverage("Covered"), "r2": Coverage("Partially covered")},
                      Coverage("Covered"), True)
    return replace(base, **changes)


def metrics(a):
    return report_metrics(a, ["r1", "r2"], "stroke")


def test_fixed_denominator_and_no_half_credit():
    row = metrics(assessment())
    assert row["coverage"] == 0.5
    assert row["coverage_bounds"] == [0.5, 0.5]
    assert row["joint"] is False
    assert row["joint_complete_review"] is True


def test_pending_provisional_covered_is_unknown():
    row = metrics(assessment(coverage={"r1": Coverage("Covered"), "r2": Coverage("Covered", True)}))
    assert row["coverage"] is None
    assert row["coverage_bounds"] == [0.5, 1.0]
    assert row["joint"] is None


def test_missing_report_neither_zero_nor_error_free():
    row = metrics(Assessment("stroke_A_P", "A", False))
    assert row["coverage"] is row["any_error"] is row["joint"] is None
    assert row["coverage_bounds"] == [0, 1]
    with pytest.raises(ValueError, match="invented"):
        metrics(assessment(available=False))


def test_error_group_not_tag_or_location_count_and_pending_positive():
    issues = (Issue("i1", "Error", ("E01", "E02"), "exact statement"),
              Issue("i2", "Pending adjudication", ("E02",), "ambiguous statement"))
    row = metrics(assessment(issues=issues, issue_review_complete=False))
    assert row["confirmed_issue_count"] == 1
    assert row["any_error"] is True and row["joint"] is False
    assert row["joint_complete_review"] is False
    with pytest.raises(ValueError, match="Repeated"):
        metrics(assessment(issues=(issues[0], issues[0])))


def test_joint_failure_known_despite_other_unknowns_but_not_main_denominator():
    row = metrics(assessment(coverage={"r1": Coverage("Not covered")}))
    result = binary_summary([row["joint"]], point_eligible=[row["joint_complete_review"]])
    assert row["joint"] is False
    assert result["evaluable"] == 0
    assert result["all_planned_bounds"] == [0, 0]


def test_success_requires_all_coverage_g03_and_issue_review():
    a = assessment(coverage={key: Coverage("Covered") for key in ("r1", "r2")})
    assert metrics(a)["joint"] is True
    assert metrics(replace(a, g03=Coverage()))["joint"] is None
    assert metrics(replace(a, issue_review_complete=False))["joint"] is None
    assert metrics(replace(a, g03=Coverage("Not covered")))["joint"] is False


def test_control_flags_independent_and_positive_even_with_pending():
    a = Assessment("control_A_avg", "A", True, {"r1": Coverage("Covered")},
                   Coverage("Covered"), True,
                   (Issue("i1", "Pending adjudication", ("E02",), "quote", ("pathology",)),))
    assert report_metrics(a, ["r1"], "control")["control_flags"] == {"normality": False, "pathology": None}
    a = replace(a, issues=a.issues + (Issue("i2", "Error", ("E02",), "quote", ("pathology",)),))
    assert report_metrics(a, ["r1"], "control")["control_flags"]["pathology"] is True


def test_exact_zero_event_control_uncertainty():
    summary = binary_summary([False] * 10, control=True)
    assert summary["zero_event_one_sided_95_upper"] == pytest.approx(0.2588655509)
    assert summary["exact_95_interval"] == pytest.approx([0, 0.3084971078])
    summary = binary_summary([True, None, False])
    assert summary["evaluable"] == 2 and summary["events"] == 1
    assert summary["all_planned_bounds"] == pytest.approx([1 / 3, 2 / 3])


@pytest.mark.parametrize("confidence", [0.95, 1 - 0.05 / 3])
def test_bca_matches_independent_scipy_implementation(confidence):
    values = np.array([-0.25, 0, 0.2, 0.25, 0.75, 0.5, -0.6, 0.4])
    seed = 20260918
    indices = np.random.default_rng(seed).integers(0, len(values), size=(20000, len(values)))
    expected = bootstrap((values,), np.mean, n_resamples=20000, method="BCa",
                         rng=np.random.default_rng(seed), confidence_level=confidence)
    actual = bca_mean_interval(values, indices, confidence)
    assert actual["interval"] == pytest.approx(expected.confidence_interval, abs=1e-12)


def test_degenerate_bca_unavailable_no_method_switch():
    assert bca_mean_interval([1], np.zeros((20000, 1), dtype=int), .95)["interval"] is None
    assert bca_mean_interval([.2, .2], np.zeros((20000, 2), dtype=int), .95)["interval"] is None


def test_complete_triads_equal_case_weights_and_all_planned_bounds():
    roster = {"stroke_A_P": {"group": "stroke", "required_ids": ["a", "b"]},
              "stroke_B_P": {"group": "stroke", "required_ids": ["a", "b", "c", "d"]},
              "stroke_C_P": {"group": "stroke", "required_ids": ["a", "b"]}}
    rows = []
    for case, metadata in roster.items():
        for model in "ABC":
            if (case, model) == ("stroke_C_P", "C"):
                rows.append(Assessment(case, model, False))
                continue
            labels = {key: Coverage("Covered" if i == 0 else "Not covered")
                      for i, key in enumerate(metadata["required_ids"])}
            rows.append(Assessment(case, model, True, labels))
    result, indices = analyze(roster, "ABC", rows)
    primary = result["primary_stroke"]
    assert primary["n"] == 2
    assert primary["paired_model_means"] == {"A": .375, "B": .375, "C": .375}
    assert primary["excluded_case_ids"] == ["stroke_C_P"]
    assert primary["contrasts"]["A - C"]["all_planned_missingness_bounds_percentage_points"] == pytest.approx([-100/6, 100/6])
    repeat, repeat_indices = analyze(dict(reversed(list(roster.items()))), "CBA", list(reversed(rows)))
    assert result == repeat
    assert indices.shape == (20000, 2) and np.array_equal(indices, repeat_indices)
    with pytest.raises(ValueError, match="planned slots"):
        analyze(roster, "ABC", rows[:-1])
    with pytest.raises(ValueError, match="planned slots"):
        analyze(roster, "ABC", rows + [rows[0]])


def test_agreement_excludes_pending_and_cannot_assess_not_consensus():
    left = dict(enumerate([Coverage("Covered"), Coverage("Partially covered"),
                           Coverage("Covered", True), Coverage("Cannot assess")]))
    right = dict(enumerate([Coverage("Covered"), Coverage("Not covered"),
                            Coverage("Covered"), Coverage("Covered")]))
    result = coverage_agreement(left, right)
    assert result["jointly_assessable"] == 2
    assert result["excluded_unknown_or_pending"] == 2
    assert result["raw_agreement"] == .5
    assert result["unweighted_kappa"] == pytest.approx(1/3)
    assert coverage_agreement({0: Coverage("Covered")}, {0: Coverage("Covered")})["unweighted_kappa"] is None
    with pytest.raises(ValueError, match="same planned"):
        coverage_agreement(left, {})


def test_independent_agreement_separates_cohorts_g03_and_complete_error_reviews():
    roster = {"stroke_Same_P": {"group": "stroke", "required_ids": ["r1"]},
              "control_Same_avg": {"group": "control", "required_ids": ["r1"]}}
    left = [Assessment(case, model, True, {"r1": Coverage("Covered")}, Coverage("Not covered"), True)
            for case in roster for model in "ABC"]
    right = list(left)
    # A confirmed error is positive for outcomes but this unfinished independent
    # issue review must be excluded from error-detection agreement.
    right[0] = replace(right[0], issue_review_complete=False,
                       issues=(Issue("I1", "Error", ("E01",), "quote"),))
    result = independent_agreement(roster, "ABC", left, right)
    assert result["stroke"]["case_requirements"]["jointly_assessable"] == 3
    assert result["stroke"]["G03"]["jointly_assessable"] == 3
    assert result["stroke"]["any_error"]["jointly_assessable"] == 2
    assert result["control"]["any_error"]["jointly_assessable"] == 3


def test_no_complete_triads_retains_planned_bounds_and_no_interval():
    roster = {"stroke_A_P": {"group": "stroke", "required_ids": ["r1"]}}
    rows = [Assessment("stroke_A_P", m, False) for m in "ABC"]
    result, indices = analyze(roster, "ABC", rows)
    assert indices.shape == (20000, 0)
    assert result["primary_stroke"]["n"] == 0
    for contrast in result["primary_stroke"]["contrasts"].values():
        assert contrast["descriptive_95"]["interval"] is None
        assert contrast["all_planned_missingness_bounds_percentage_points"] == [-100, 100]
    assert result["cohort_summaries"]["stroke"]["by_model"]["A"]["any_error"]["all_planned_bounds"] == [0, 1]


def test_frozen_outcome_entry_point_preserves_estimands_without_forced_categories():
    roster = {"stroke_A_P": {"group": "stroke", "required_ids": ["r1", "r2"]},
              "stroke_B_P": {"group": "stroke", "required_ids": ["r1", "r2"]}}
    rows = [replace(assessment(), case_id=case, model=model) for case in roster for model in 'ABC']
    original, original_indices = analyze(roster, 'ABC', rows)
    metrics_by_slot = {(a.case_id, a.model): report_metrics(a, ['r1', 'r2'], 'stroke') for a in rows}
    same, indices = analyze_report_metrics(roster, 'ABC', metrics_by_slot)
    assert same == original and np.array_equal(indices, original_indices)
    for row in metrics_by_slot.values(): row.pop('error_categories')
    unclassified, _ = analyze_report_metrics(roster, 'ABC', metrics_by_slot)
    assert unclassified['primary_stroke'] == original['primary_stroke']
    assert unclassified['cohort_summaries']['stroke']['by_model']['A']['confirmed_issue_categories'] is None
    assert unclassified['cohort_summaries']['stroke']['by_model']['A']['any_error'] == original['cohort_summaries']['stroke']['by_model']['A']['any_error']
    metrics_by_slot['stroke_A_P', 'A']['K'] = 3
    with pytest.raises(ValueError, match='denominator'):
        analyze_report_metrics(roster, 'ABC', metrics_by_slot)
