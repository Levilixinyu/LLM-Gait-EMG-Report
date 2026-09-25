"""Synthetic checks for stage separation and unknown handling without a model key."""
from copy import deepcopy

import pytest

from src.eval.three_rater_blinded import blinded_report_metrics, pairwise_blinded_agreement

ROSTER = {'stroke_S_P': {'group': 'stroke', 'required_ids': ['C1']},
          'control_H_avg': {'group': 'control', 'required_ids': ['C2']}}


def review(who='rater1'):
    cases = {'opaque-S': 'stroke_S_P', 'opaque-H': 'control_H_avg'}
    return {'rater': who, 'stage': 'original_independent',
            'review': [{'report_id': rid, 'case_id': case, 'material_status': 'Available',
                        'issue_review_complete': 'Yes'} for rid, case in cases.items()],
            'coverage': [{'report_id': rid, 'case_id': case, 'requirement_id': req,
                          'decision': 'Covered', 'adjudication_status': 'Final'}
                         for rid, case in cases.items() for req in (*ROSTER[case]['required_ids'], 'G03')],
            'issues': []}


def issue(decision='Pending adjudication', pathology='No', normality='No'):
    return {'report_id': 'opaque-H', 'issue_id': 'I1', 'decision': decision,
            'categories': 'E01;E03', 'exact_quote': 'recorded claim',
            'pathology_flag': pathology, 'normality_flag': normality}


def test_three_original_pairs_and_domain_separation():
    reviews = {who: review(who) for who in ('rater1', 'rater2', 'rater3')}
    reviews['rater3']['coverage'][0]['decision'] = 'Partially covered'
    result = pairwise_blinded_agreement(reviews, ROSTER)
    assert len(result) == 3
    assert result['rater1__rater2']['role'] == 'originally_planned'
    assert result['rater1__rater3']['role'] == 'supplementary_proposal'
    assert result['rater1__rater3']['cohorts']['stroke']['case_requirements']['raw_agreement'] == 0
    assert result['rater1__rater3']['cohorts']['stroke']['G03']['raw_agreement'] == 1
    assert result['rater1__rater3']['cohorts']['control']['case_requirements']['raw_agreement'] == 1


def test_post_feedback_cannot_be_used_for_independent_agreement():
    reviews = {who: review(who) for who in ('rater1', 'rater2', 'rater3')}
    reviews['rater3']['stage'] = 'post_feedback_individual'
    with pytest.raises(ValueError, match='original independent'):
        pairwise_blinded_agreement(reviews, ROSTER)


def test_closed_pending_is_not_error_or_error_free_and_keeps_coverage():
    r = review(); r['issues'] = [issue()]
    m = blinded_report_metrics(r, ROSTER)['opaque-H']
    assert m['coverage'] == 1 and m['confirmed_issue_count'] == 0
    assert m['pending_issue_count'] == 1 and m['any_error'] is None and m['joint'] is None
    assert m['control_flags'] == {'pathology': False, 'normality': False}


def test_positive_error_with_pending_and_one_group_not_two_tags():
    r = review(); r['issues'] = [issue('Error'), {**issue(), 'issue_id': 'I2'}]
    m = blinded_report_metrics(r, ROSTER)['opaque-H']
    assert m['confirmed_issue_count'] == 1 and m['pending_issue_count'] == 1
    assert m['any_error'] is True and m['joint'] is False


@pytest.mark.parametrize('decision', ['Error', 'Pending adjudication'])
def test_missing_flag_remains_unknown_and_flags_are_separate(decision):
    r = review(); r['issues'] = [issue(decision, pathology=None)]
    assert blinded_report_metrics(r, ROSTER)['opaque-H']['control_flags'] == {
        'pathology': None, 'normality': False}
    r['issues'].append({**issue('Error', pathology='Yes'), 'issue_id': 'I2'})
    assert blinded_report_metrics(r, ROSTER)['opaque-H']['control_flags']['pathology'] is True


def test_unknown_coverage_and_incomplete_issue_review_excluded_from_agreement():
    reviews = {who: review(who) for who in ('rater1', 'rater2', 'rater3')}
    reviews['rater2']['coverage'][0]['adjudication_status'] = 'Pending'
    reviews['rater2']['review'][0]['issue_review_complete'] = 'No'
    r = pairwise_blinded_agreement(reviews, ROSTER)['rater1__rater2']['cohorts']['stroke']
    assert r['case_requirements']['jointly_assessable'] == 0
    assert r['any_error']['jointly_assessable'] == 0


def test_membership_and_duplicate_guards():
    r = review(); r['coverage'].pop()
    with pytest.raises(ValueError, match='membership'):
        blinded_report_metrics(r, ROSTER)
    r = review(); r['issues'] = [issue(), issue()]
    with pytest.raises(ValueError, match='Duplicate'):
        blinded_report_metrics(r, ROSTER)
    reviews = {who: review(who) for who in ('rater1', 'rater2', 'rater3')}
    other = deepcopy(reviews['rater3'])
    for table in ('review', 'coverage'):
        for row in other[table]:
            if row['report_id'] == 'opaque-S': row['report_id'] = 'different-ID'
    reviews['rater3'] = other
    with pytest.raises(ValueError, match='rosters differ'):
        pairwise_blinded_agreement(reviews, ROSTER)
