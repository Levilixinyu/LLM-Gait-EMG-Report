"""Analytical edge cases and participant-cluster resampling for nominal AC1."""
import numpy as np
import pytest
from src.eval.agreement_sensitivity import ac1_from_counts, cluster_interval, analyze_original_agreement


def test_binary_balanced_independence_and_perfect_disagreement():
    assert ac1_from_counts([[25,25],[25,25]])==0
    assert ac1_from_counts([[0,50],[50,0]])==-1


def test_skewed_marginals_and_fixed_unused_category():
    # Pa=.9; binary Pe=.095. Third predefined category changes Pe to .0475.
    assert ac1_from_counts([[90,5],[5,0]])==pytest.approx((.9-.095)/.905)
    assert ac1_from_counts([[90,5,0],[5,0,0],[0,0,0]])==pytest.approx((.9-.0475)/.9525)


def test_constant_and_empty_tables():
    assert ac1_from_counts([[100,0],[0,0]])==1
    assert np.isnan(ac1_from_counts([[0,0],[0,0]]))
    assert ac1_from_counts(np.ones((3,3)))==pytest.approx(0,abs=1e-15)


def test_participant_resampling_keeps_correlated_rows_together():
    cases=np.array([[[10,0],[0,0]],[[0,10],[0,0]]])
    result=cluster_interval(cases,np.array([[0,0],[1,1]]))
    # The only bootstrap tables are twice the whole first or whole second case.
    assert result['percentile_95']==pytest.approx([-.95,.95])
    assert result['valid_resamples']==2


def test_empty_bootstrap_draws_are_explicit():
    result=cluster_interval(np.array([[[0,0],[0,0]],[[2,0],[0,0]]]),np.array([[0,0],[1,1]]))
    assert result=={'percentile_95':[1.,1.],'valid_resamples':1,'undefined_resamples':1}


def test_invariance_to_rater_and_category_order():
    x=np.array([[7,1,2],[3,5,1],[0,2,9]])
    assert ac1_from_counts(x)==pytest.approx(ac1_from_counts(x.T))
    assert ac1_from_counts(x)==pytest.approx(ac1_from_counts(x[::-1,::-1]))


@pytest.mark.parametrize('x',[[[1]],[[1,-1],[0,1]],[[1,.5],[0,1]],[[np.nan,0],[0,1]]])
def test_invalid_counts_rejected(x):
    with pytest.raises(ValueError):ac1_from_counts(x)


def test_consensus_cannot_be_used_as_original_independent_data():
    reviews={who:{'stage':'post_feedback_individual'} for who in ('rater1','rater2','rater3')}
    with pytest.raises(ValueError,match='original independent'):analyze_original_agreement(reviews,{})
