"""Check scenario missingness against the existing endpoint implementation."""
from copy import deepcopy
from itertools import product

import pytest

from src.eval.formal_analysis import Assessment, Coverage, Issue, report_metrics
from src.eval.wording_sensitivity import overlay_reports


@pytest.mark.parametrize('first,second,coverage', list(product(
    ['Error', 'Acceptable', 'Pending adjudication'],
    ['Error', 'Acceptable', 'Pending adjudication'],
    ['Covered', 'Partially covered', None])))
def test_overlay_matches_existing_endpoints(first, second, coverage):
    def assess(a, b):
        return Assessment('case', 'model', True, {'C01': Coverage(coverage)},
                          Coverage('Covered'), True,
                          (Issue('G1', a, ('E01',), 'first'),
                           Issue('G2', b, ('E03',), 'second')))
    base = report_metrics(assess('Error', 'Pending adjudication'), ['C01'], 'control')
    base.update(report_id='R1', cohort='control')
    frozen = {'reports': [base], 'issue_groups': [
        {'group_id': 'G1', 'report_id': 'R1', 'decision': 'Error'},
        {'group_id': 'G2', 'report_id': 'R1', 'decision': 'Pending adjudication'}]}
    before = deepcopy(frozen)
    result = overlay_reports(frozen, {'G1': first, 'G2': second})[0]
    expected = report_metrics(assess(first, second), ['C01'], 'control')
    for key in ('any_error', 'joint', 'joint_complete_review',
                'confirmed_issue_count', 'pending_issue_count'):
        assert result[key] == expected[key]
    for key in ('counts', 'coverage', 'coverage_bounds', 'g03', 'control_flags'):
        assert result[key] == base[key]
    assert frozen == before


def test_flag_disagreement_is_unknown_independently_of_error():
    frozen = {'reports': [dict(report_id='R1', cohort='control', available=True,
        issue_review_complete=True, unknown_items=0, g03='Covered',
        counts={'Covered': 1, 'Partially covered': 0, 'Not covered': 0},
        control_flags={'normality': False, 'pathology': True})],
        'issue_groups': [{'group_id': 'G1', 'report_id': 'R1', 'decision': 'Error'}]}
    result = overlay_reports(frozen, {}, pathology_overrides={'R1': None})[0]
    assert result['any_error'] is True
    assert result['control_flags'] == {'normality': False, 'pathology': None}
    with pytest.raises(ValueError):
        overlay_reports(frozen, {'G1': 'Acceptable'}, pathology_overrides={'R1': True})
    with pytest.raises(ValueError):
        overlay_reports(frozen, {'missing': 'Error'})
