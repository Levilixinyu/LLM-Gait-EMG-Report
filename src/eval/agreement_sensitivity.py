"""Post-hoc nominal AC1 using original independent ratings and participant clusters."""
from itertools import combinations

import numpy as np

from .three_rater_blinded import RATERS, blinded_report_metrics, pairwise_blinded_agreement, validate_review


def ac1_from_counts(counts):
    """Compute nominal, unweighted AC1; keep the full predefined category alphabet.

    The last two axes are the complete-case pairwise contingency table. Leading
    axes allow vectorized participant-bootstrap replicates. Empty tables yield NaN.
    """
    x = np.asarray(counts, dtype=float)
    if x.ndim < 2 or x.shape[-1] != x.shape[-2] or x.shape[-1] < 2:
        raise ValueError('Expected square contingency tables with at least two categories')
    if not np.isfinite(x).all() or (x < 0).any() or not np.equal(x, np.floor(x)).all():
        raise ValueError('Counts must be finite nonnegative integers')
    n = x.sum(axis=(-2, -1))
    with np.errstate(invalid='ignore', divide='ignore'):
        p = (x.sum(axis=-1) + x.sum(axis=-2)) / (2 * n[..., None])
        pa = np.trace(x, axis1=-2, axis2=-1) / n
        pe = (p * (1-p)).sum(axis=-1) / (x.shape[-1]-1)
        ac1 = (pa-pe) / (1-pe)
    return ac1


def cluster_interval(case_counts, indices):
    """Resample whole participants, retaining every included row within each case."""
    x = np.asarray(case_counts)
    ix = np.asarray(indices)
    if x.ndim != 3 or ix.ndim != 2 or ix.shape[1] != len(x):
        raise ValueError('Expected one square table per case and full-case bootstrap indices')
    if not np.issubdtype(ix.dtype, np.integer) or (ix < 0).any() or (ix >= len(x)).any():
        raise ValueError('Invalid participant indices')
    values = ac1_from_counts(x[ix].sum(axis=1))
    valid = values[np.isfinite(values)]
    return {'percentile_95': np.quantile(valid, [.025, .975], method='linear').tolist() if len(valid) else None,
            'valid_resamples': len(valid), 'undefined_resamples': int(len(values)-len(valid))}


def analyze_original_agreement(reviews, roster, *, resamples=20000, seed=20260925):
    if set(reviews) != set(RATERS) or any(r['stage'] != 'original_independent' for r in reviews.values()):
        raise ValueError('Only all three original independent reviews are allowed')
    if not isinstance(resamples, int) or resamples < 1:
        raise ValueError('Positive integer resample count required')
    parsed = {who: validate_review(r, roster) for who,r in reviews.items()}
    metrics = {who: blinded_report_metrics(r, roster) for who,r in reviews.items()}
    baseline = pairwise_blinded_agreement(reviews, roster)
    rng = np.random.default_rng(seed)
    cases = {c: sorted(k for k,v in roster.items() if v['group']==c) for c in ('stroke','control')}
    indices = {c:rng.integers(0,len(ids),size=(resamples,len(ids))) for c,ids in cases.items()}
    rows = []
    for left,right in combinations(RATERS, 2):
        pair = left+'__'+right
        for cohort,domains in baseline[pair]['cohorts'].items():
            ids = cases[cohort]
            for domain,d in domains.items():
                labels = d['labels']
                # Labels come from the established rubric, not the observed subset.
                assert len(labels) == (2 if domain=='any_error' else 3)
                counts = np.zeros((len(ids),len(labels),len(labels)), dtype=np.int64)
                planned = 0
                for rid,r in parsed[left][0].items():
                    case = r['case_id']
                    if case not in ids: continue
                    requirements = roster[case]['required_ids'] if domain=='case_requirements' else [domain]
                    for req in requirements:
                        planned += 1
                        if domain=='any_error':
                            a,b = metrics[left][rid]['any_error'],metrics[right][rid]['any_error']
                            eligible = (parsed[left][0][rid]['issue_review_complete'] == parsed[right][0][rid]['issue_review_complete'] == 'Yes'
                                        and a is not None and b is not None)
                        else:
                            ca,cb = parsed[left][1][rid,req],parsed[right][1][rid,req]
                            a,b,eligible = ca.label,cb.label,ca.final and cb.final
                        if eligible:
                            counts[ids.index(case),labels.index(a),labels.index(b)] += 1
                total = counts.sum(axis=0)
                assert total.tolist() == d['cross_tabulation']
                n = int(total.sum())
                assert n == d['jointly_assessable']
                value = float(ac1_from_counts(total))
                excluded = d.get('excluded_unknown_or_pending',d.get('excluded_incomplete_or_unknown'))
                assert planned-n == excluded
                row = {'pair':pair,'cohort':cohort,'domain':domain,'labels':labels,
                       'planned':planned,'assessable':n,'excluded':excluded,
                       'participants':len(ids),'participants_with_assessable_rows':int((counts.sum(axis=(1,2))>0).sum()),
                       'raw_agreement':d['raw_agreement'],'kappa':d['unweighted_kappa'],
                       'ac1':value if np.isfinite(value) else None,
                       **cluster_interval(counts,indices[cohort]),
                       'constant_pooled_labels':bool(n and np.count_nonzero(total.sum(axis=0)+total.sum(axis=1))==1),
                       'cross_tabulation':total.tolist(),'case_ids':ids,'case_cross_tabulations':counts.tolist()}
                rows.append(row)
    return {'stage':'original_independent','analysis_role':'post_hoc_sensitivity',
            'resamples':resamples,'seed':seed,'interval_method':'participant-cluster percentile bootstrap, 95%, NumPy linear quantiles',
            'category_policy':'Three fixed nominal coverage categories; two fixed binary any-error categories; no weights or category dropping',
            'estimand':'Agreement on jointly assessable original rating rows; original item/report weighting retained',
            'resampling':'Within cohort, sample participants with replacement; retain all reports/items and original exclusions within each sampled participant. Share draws across pairs/domains.',
            'constant_label_policy':'AC1 can equal 1 with constant labels; this shows agreement only in the observed category and does not demonstrate discrimination.',
            'rows':rows}
