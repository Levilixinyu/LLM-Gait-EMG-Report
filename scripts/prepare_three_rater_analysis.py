"""Validate three-rater analysis inputs without model identities or comparisons.

Writes only a preparation manifest. Source workbooks and prior protocol remain
unchanged. This command does not freeze final decisions or approve an amendment.
"""
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import sys

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.three_rater_blinded import RATERS, blinded_report_metrics


def rows(sheet):
    data = list(sheet.values)
    return [dict(zip(data[0], row)) for row in data[1:]]


def main():
    sources = {}

    def source(relative):
        p = ROOT / relative
        sources[relative] = hashlib.sha256(p.read_bytes()).hexdigest()
        return p

    base = 'docs/formal_study/consolidated_ratings_v1/'
    manifest = json.loads(source(base + 'BUILD_RECORD.json').read_text())
    current_path = source(base + 'Consolidated_ratings_working.xlsx')
    assert sources[base + current_path.name] == manifest['workbook_sha256']
    current = load_workbook(current_path, data_only=False)
    for relative, expected in manifest['source_hashes'].items():
        source(relative)
        assert sources[relative] == expected, relative
    required_path = source('docs/formal_study/case_requirements_v1/case_requirements.csv')
    with required_path.open(newline='') as stream:
        requirements = [row for row in csv.DictReader(stream) if row['included'] == 'Yes']
    roster = {}
    for row in requirements:
        case = row['case_id']
        roster.setdefault(case, {'group': case.split('_')[0], 'required_ids': []})['required_ids'].append(row['record_id'])
    assert len(requirements) == 149 and len(roster) == 35
    assert Counter(row['group'] for row in roster.values()) == {'stroke': 25, 'control': 10}
    original, post_feedback, diagnostics = {}, {}, {}
    current_coverage = rows(current['Coverage current'])
    current_issues = rows(current['Issues current'])
    frozen = {r['record_id']: r for r in requirements}
    for r in current_coverage:
        if r['Requirement'] == 'G03':
            continue
        expected = frozen[r['Requirement']]
        assert r['Case ID'] == expected['case_id']
        assert r['Required wording'] == expected['required_wording']
        assert r['Components'] == expected['required_components_and_optional_content']
    source_reports = None
    for who in RATERS:
        path = source(f'docs/formal_study/three_rater_review_v1/private/{who}_submitted.xlsx')
        wb = load_workbook(path, data_only=False)
        review = {'rater': who, 'stage': 'original_independent',
                  **{sn.lower(): rows(wb[sn]) for sn in ('Review', 'Coverage', 'Issues')}}
        report_roster = {r['report_id']: r['case_id'] for r in review['review']}
        assert len(report_roster) == 105
        assert Counter(report_roster.values()) == {case: 3 for case in roster}
        assert source_reports is None or source_reports == report_roster
        source_reports = report_roster
        for sn in ('Coverage', 'Issues'):
            headers = list(wb[sn].values)[0]
            embedded = rows(current['Independent ' + sn.lower()])
            assert [{key: r[key] for key in headers} for r in embedded if r['Rater'] == who] == review[sn.lower()]
        original[who] = review
        updates = {'rater': who, 'stage': 'post_feedback_individual', 'review': review['review'],
                   'coverage': [{'report_id': r['Report ID'], 'case_id': r['Case ID'],
                                 'requirement_id': r['Requirement'], 'decision': r[who + ' decision'],
                                 'adjudication_status': r[who + ' status']} for r in current_coverage],
                   'issues': [{'report_id': r['Report ID'], 'issue_id': r['Local issue ID'],
                               'decision': r['Current decision'], 'categories': r['Categories'],
                               'exact_quote': r['Exact quote'], 'pathology_flag': r['Pathology flag'],
                               'normality_flag': r['Normality flag']}
                              for r in current_issues if r['Rater'] == who]}
        post_feedback[who] = updates
        independent_metrics = blinded_report_metrics(review, roster)
        working_metrics = blinded_report_metrics(updates, roster)
        registered = {r['Report ID']: r for r in rows(current['Report summaries']) if r['Rater'] == who}
        for rid, metric in working_metrics.items():
            saved = registered[rid]
            assert metric['confirmed_issue_count'] == saved['Confirmed records']
            assert metric['pending_issue_count'] == saved['Pending records']
            assert {True: 'Yes', False: 'No', None: 'Unknown'}[metric['any_error']] == saved['Any error']
            assert metric['coverage'] == saved['Coverage fraction']
            assert {True: 'Yes', False: 'No', None: 'Unknown'}[metric['joint']] == saved['Joint outcome']
        diagnostics[who] = {'reports': len(report_roster), 'original_coverage_rows': len(review['coverage']),
                            'original_issue_rows': len(review['issues']), 'working_issue_rows': len(updates['issues']),
                            'working_confirmed_records': sum(m['confirmed_issue_count'] for m in working_metrics.values()),
                            'working_pending_records': sum(m['pending_issue_count'] for m in working_metrics.values()),
                            'original_rows_preserved_exactly': True, 'working_metrics_match_existing_summaries': True,
                            'independent_review_parsed_without_model_mapping': len(independent_metrics) == 105}
    # Proposals are carried separately, never silently substituted for categories.
    proposals = rows(current['Audit category proposals'])
    by_claim = {}
    for row in proposals:
        by_claim.setdefault(row['Report ID'], {})[row['Rater']] = row['Personal proposed categories']
    assert len(proposals) == 18 and len(by_claim) == 6
    assert all(set(values) == set(RATERS) for values in by_claim.values())
    for relative in ('src/eval/three_rater_blinded.py', 'scripts/prepare_three_rater_analysis.py',
                     'tests/test_three_rater_blinded.py',
                     'docs/formal_study/three_rater_analysis_v1/ANALYSIS_ADDENDUM_DRAFT.md',
                     'src/eval/formal_analysis.py', 'docs/formal_study/execution_analysis_v3_draft/PROTOCOL.md',
                     'docs/formal_study/rating_delivery_rater3_v1/REVIEWER_ADDITION_RECORD.md'):
        source(relative)
    result = {'status': 'Blinded preparation validated; analysis amendment draft, no final release or unblinding',
              'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
              'model_mapping_read': False, 'model_comparisons_run': False,
              'actual_independent_agreement_statistics_run': False,
              'original_protocol_and_ratings_modified': False,
              'reports': 105, 'participants': 35, 'stroke_cases': 25, 'control_cases': 10,
              'diagnostics': diagnostics, 'category_proposals': by_claim,
              'category_proposal_groups_with_differences': sum(len(set(v.values())) > 1 for v in by_claim.values()),
              'pending_policy': 'Closed Pending remains unresolved content, neither Error nor Acceptable.',
              'ready_for': 'Review of the concrete analysis addendum and data-assembly checks',
              'remaining': ['Study-lead confirmation of analysis addendum',
                            'Explicit final dataset freeze with source-linked decisions and retained category differences',
                            'Separately authorized mapping join and model-level analysis'],
              'source_sha256': sources}
    out = ROOT / 'docs/formal_study/three_rater_analysis_v1'
    out.mkdir(exist_ok=True)
    (out / 'PREPARATION_CHECK.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('source_sha256', 'category_proposals')}, indent=2))


if __name__ == '__main__':
    main()
