"""Authorized original-review agreement for three human raters, still blinded.

No model identity mapping, consensus importer, or post-feedback score is read.
Pairwise exclusions and cross-tabs are exported with exact original labels.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from itertools import combinations
import csv
import hashlib
import json
from pathlib import Path
import sys

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.three_rater_blinded import (
    RATERS, blinded_report_metrics, pairwise_blinded_agreement, validate_review,
)

OUT = ROOT / 'docs/formal_study/three_rater_analysis_v1'


def records(sheet):
    values = list(sheet.values)
    return [dict(zip(values[0], row)) for row in values[1:]]


def main():
    authorization_path = OUT / 'AGREEMENT_AUTHORIZATION.json'
    authorization = json.loads(authorization_path.read_text())
    assert authorization['authorized_pairs'] == ['rater1__rater2', 'rater1__rater3', 'rater2__rater3']
    assert authorization['stage'] == 'original_independent' and not authorization['unblinding_authorized']
    preparation = json.loads((OUT / 'PREPARATION_CHECK.json').read_text())
    sources = {}

    def source(relative, *, locked=True):
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if locked:
            assert actual == preparation['source_sha256'][relative], f'Changed preparation input: {relative}'
        sources[relative] = actual
        return path

    source(str(authorization_path.relative_to(ROOT)), locked=False)
    requirements = source('docs/formal_study/case_requirements_v1/case_requirements.csv')
    roster = {}
    with requirements.open(newline='') as stream:
        for row in csv.DictReader(stream):
            if row['included'] == 'Yes':
                case = row['case_id']
                roster.setdefault(case, {'group': case.split('_')[0], 'required_ids': []})['required_ids'].append(row['record_id'])
    assert len(roster) == 35 and sum(len(r['required_ids']) for r in roster.values()) == 149
    reviews, parsed, metrics = {}, {}, {}
    for who in RATERS:
        p = source(f'docs/formal_study/three_rater_review_v1/private/{who}_submitted.xlsx')
        wb = load_workbook(p, data_only=False)
        reviews[who] = {'rater': who, 'stage': 'original_independent',
                        **{name.lower(): records(wb[name]) for name in ('Review', 'Coverage', 'Issues')}}
        parsed[who] = validate_review(reviews[who], roster)
        metrics[who] = blinded_report_metrics(reviews[who], roster)
        assert len(parsed[who][0]) == 105
        assert Counter(row['case_id'] for row in reviews[who]['review']) == {case: 3 for case in roster}
    for relative in ('src/eval/three_rater_blinded.py', 'src/eval/formal_analysis.py'):
        source(relative)
    source('scripts/analyze_three_rater_agreement.py', locked=False)
    results = pairwise_blinded_agreement(reviews, roster)
    summaries, trace, cells, marginals = [], [], [], []
    for pair, result in results.items():
        # Scope approval is kept outside the generic calculation function.
        result['role'] = 'originally_planned' if pair == 'rater1__rater2' else 'authorized_supplementary'
        left, right = pair.split('__')
        for cohort, domains in result['cohorts'].items():
            ids = sorted(rid for rid, r in parsed[left][0].items() if roster[r['case_id']]['group'] == cohort)
            for domain, output in domains.items():
                labels, matrix = output['labels'], output['cross_tabulation']
                eligible_rows = []
                for rid in ids:
                    case = parsed[left][0][rid]['case_id']
                    requirements_for_domain = roster[case]['required_ids'] if domain == 'case_requirements' else ['G03' if domain == 'G03' else 'any_error']
                    for req in requirements_for_domain:
                        if domain == 'any_error':
                            a, b = metrics[left][rid]['any_error'], metrics[right][rid]['any_error']
                            sa, sb = parsed[left][0][rid]['issue_review_complete'], parsed[right][0][rid]['issue_review_complete']
                            eligible = sa == sb == 'Yes' and a is not None and b is not None
                            reason = '' if eligible else 'Incomplete issue review or unknown any-error state; Pending without a confirmed Error is unknown.'
                        else:
                            ca, cb = parsed[left][1][rid, req], parsed[right][1][rid, req]
                            a, b = ca.label, cb.label
                            sa, sb = ('Pending/unspecified' if ca.pending else 'Final'), ('Pending/unspecified' if cb.pending else 'Final')
                            eligible = ca.final and cb.final
                            reason = '' if eligible else 'At least one label is Pending, Cannot assess, missing, or lacks final status.'
                        if eligible:
                            eligible_rows.append((a, b))
                        trace.append([pair, cohort, domain, rid, case, req, a, sa, b, sb,
                                      'Yes' if eligible else 'No', 'Yes' if eligible and a == b else ('No' if eligible else None), reason])
                # Verify with exact integer/fraction arithmetic, independent of
                # the numpy implementation used by the analysis module.
                reconstructed = [[sum(a == la and b == lb for a, b in eligible_rows) for lb in labels] for la in labels]
                assert reconstructed == matrix
                n = len(eligible_rows)
                agree = sum(a == b for a, b in eligible_rows)
                chance_numerator = sum(sum(matrix[i]) * sum(row[i] for row in matrix) for i in range(len(labels)))
                exact_kappa = Fraction(agree * n - chance_numerator, n*n - chance_numerator) if n and n*n != chance_numerator else None
                assert n == output['jointly_assessable']
                assert output['raw_agreement'] is None if not n else abs(output['raw_agreement'] - agree/n) < 1e-12
                if exact_kappa is None:
                    assert output['unweighted_kappa'] is None
                else:
                    assert abs(output['unweighted_kappa'] - float(exact_kappa)) < 1e-12
                excluded = output.get('excluded_unknown_or_pending', output.get('excluded_incomplete_or_unknown'))
                summaries.append([pair, result['role'], cohort, domain, n+excluded, n, excluded,
                                  agree, n-agree, output['raw_agreement'], output['unweighted_kappa']])
                for i, a in enumerate(labels):
                    marginals.append([pair, cohort, domain, left, a, sum(matrix[i])])
                    marginals.append([pair, cohort, domain, right, a, sum(row[i] for row in matrix)])
                    for j, b in enumerate(labels):
                        cells.append([pair, cohort, domain, a, b, matrix[i][j]])
    assert len(summaries) == 18 and len(trace) == 3 * (552+105)
    result_document = {
        'status': 'Authorized descriptive original independent agreement; no model comparison',
        'computed_at_utc': datetime.now(timezone.utc).isoformat(),
        'stage': 'original_independent', 'participants': 35, 'reports': 105,
        'model_mapping_read': False, 'post_feedback_ratings_used': False,
        'pathology_flag_clarification_approved_by_this_run': False,
        'pairs': results, 'source_sha256': sources,
        'checks': {'all_cross_tabs_reconstructed_from_trace': True,
                   'all_kappas_verified_with_exact_fraction_arithmetic': True,
                   'all_source_hashes_match_preparation': True},
        'limitations': ['Agreement is not correctness; no expert is treated as ground truth.',
                        'Pairwise denominators differ when original Pending states exclude reports.',
                        'Multiple items and reports from each participant are correlated; no naive independent-row intervals or tests are used.',
                        'Supplementary pairs were authorized after blinded rating information had been inspected.',
                        'Post-feedback consensus is not used as independent reliability.'],
    }
    headers = ['Pair', 'Role', 'Cohort', 'Domain', 'Planned rows', 'Assessable rows', 'Excluded rows',
               'Agreements', 'Disagreements', 'Raw agreement', 'Unweighted kappa']
    wb = Workbook(); wb.remove(wb.active)

    def sheet(name, columns, data):
        ws = wb.create_sheet(name); ws.append(columns)
        for row in data: ws.append(row)
        ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions
        for c in ws[1]:
            c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='24476A')
        for row in ws:
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical='top')
                ws.column_dimensions[c.column_letter].width = 24
        return ws

    sheet('Read first', ['Topic', 'Meaning'], [
        ['Stage', 'Only preserved original independent reviews; no later corrections or reconciliation.'],
        ['Scope', 'All three reviewer pairs. Stroke/control and core coverage/G03/any-error remain separate.'],
        ['Any-error', 'Completed review required. Confirmed Error is positive even with another Pending; Pending-only is unknown.'],
        ['Trace states', 'Coverage status is Final or Pending/unspecified. For any-error, status columns hold issue-review completion Yes/No.'],
        ['Undefined kappa', 'Blank means undefined, including constant identical labels; it is not zero.'],
        ['Interpretation', 'Read kappa with raw agreement, marginals and exclusions. No threshold bands, rater ranking, correctness claim or row-independent confidence intervals.'],
        ['Scope of approval', 'User authorized all three independent agreement comparisons, not final model analysis or the separate pathology-flag clarification.'],
    ])
    ws = sheet('Pairwise summary', headers, summaries)
    for row in ws.iter_rows(min_row=2): row[9].number_format = '0.0%'; row[10].number_format = '0.000'
    sheet('Cross tabulations', ['Pair', 'Cohort', 'Domain', 'Left label', 'Right label', 'Count'], cells)
    sheet('Assessed marginals', ['Pair', 'Cohort', 'Domain', 'Rater', 'Label', 'Count'], marginals)
    sheet('Row inclusion trace', ['Pair', 'Cohort', 'Domain', 'Report ID', 'Case ID', 'Requirement',
                                  'Left original state', 'Left status', 'Right original state', 'Right status',
                                  'Included', 'Agreement', 'Exclusion reason'], trace)
    sheet('Sources', ['Path', 'SHA-256'], list(sources.items()))
    artifacts = [OUT/'INDEPENDENT_AGREEMENT.json', OUT/'Independent_agreement.xlsx', OUT/'INDEPENDENT_AGREEMENT.md']
    old_record_path = OUT/'AGREEMENT_BUILD_RECORD.json'
    if old_record_path.exists():
        prior = json.loads(old_record_path.read_text())
        assert sources == prior['source_sha256'], 'Changed inputs require an explicit new analysis version.'
        for p in artifacts:
            assert hashlib.sha256(p.read_bytes()).hexdigest() == prior['output_sha256'][p.name], 'Do not overwrite edited outputs.'
    else:
        assert not any(p.exists() for p in artifacts), 'Unregistered output already exists.'
    artifacts[0].write_text(json.dumps(result_document, indent=2) + '\n')
    wb.save(artifacts[1])
    lines = ['# Original independent agreement: three human raters', '',
             'All three pairwise comparisons were authorized by the study lead on 2026-09-23. Only the preserved original independent submissions were used. No model mapping was read. This analysis does not approve the separate semantic-flag clarification or final model-level analysis.', '',
             'Raw agreement measures identical labels; unweighted Cohen\'s kappa adjusts for expected agreement from the observed marginals. Neither establishes correctness. NA means undefined, not zero. No interpretation bands or rater ranking are assigned.', '']
    for cohort in ('stroke', 'control'):
        lines += [f'## {cohort.capitalize()}', '', '| Pair | Domain | Assessed / planned | Excluded | Agreement | Kappa |', '| --- | --- | --- | --- | --- | --- |']
        for row in summaries:
            if row[2] != cohort: continue
            agreement = f'{row[9]:.1%}' if row[9] is not None else 'NA'
            kappa = f'{row[10]:.3f}' if row[10] is not None else 'NA'
            lines.append(f'| {row[0]} | {row[3]} | {row[5]} / {row[4]} | {row[6]} | {agreement} | {kappa} |')
        lines.append('')
    lines += ['## Denominators and interpretation', '',
              '- Case requirements use three labels, with G03 analyzed separately. Pending, Cannot assess and unspecified-final-status rows are excluded from the relevant pair.',
              '- Any-error concerns a report, not a particular claim or category. Unknown states and incomplete reviews are excluded. A confirmed error makes the state positive even with another Pending claim. The original Pending states need not equal the later closed set of 16 groups.',
              '- Read the pair-specific denominators before comparing percentages. Different pairs may assess different report subsets.',
              '- Each participant contributes three reports and several coverage items. These are descriptive item/report summaries, not independent participant samples; no naive row-level confidence intervals or significance tests are provided.',
              '- Rater1-rater2 is the originally planned comparison. The two comparisons involving rater3 are authorized supplementary analyses after blinded rating information was available.',
              '- The workbook includes all 18 cross-tabulations, assessed marginals and every included/excluded row. It preserves disagreements rather than changing ratings.', '',
              'All cross-tabs were reconstructed from the exported row trace and all kappas checked independently using exact fraction arithmetic. Source hashes match the preparation record. Source workbooks are unchanged.', '']
    artifacts[2].write_text('\n'.join(lines))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in sources.items())
    old_record_path.write_text(json.dumps({'computed_at_utc': result_document['computed_at_utc'],
        'source_sha256': sources, 'output_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
        'source_workbooks_unchanged': True, 'model_mapping_read': False, 'summary_rows': 18, 'trace_rows': len(trace)}, indent=2)+'\n')
    print(json.dumps({'summary_headers': headers, 'summary_rows': summaries}, indent=2))


if __name__ == '__main__':
    main()
