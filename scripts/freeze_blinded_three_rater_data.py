"""Freeze source-linked blinded outcomes without inventing expert confirmations.

Registered categories and personal proposals remain separate. No model mapping
is read and no majority vote, new grouping, or Pending resolution is performed.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
from io import BytesIO
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
    base = 'docs/formal_study/consolidated_ratings_v1/'
    prep = 'docs/formal_study/three_rater_analysis_v1/'
    destination = ROOT / 'docs/formal_study/analysis_freeze_v1'
    assert not destination.exists(), 'Frozen version already exists; do not overwrite.'
    source_hashes = {}
    source_bytes, source_metadata = {}, {}

    def read(relative):
        if relative in source_bytes:
            return source_bytes[relative]
        p = ROOT / relative
        # Report a pending cloud read explicitly. The main preload captures all
        # currently local registered sources before waiting on a placeholder.
        if sys.platform == 'darwin' and getattr(p.stat(), 'st_flags', 0) & 0x40000000:
            print(f'Waiting for cloud source: {relative}', flush=True)
        content = p.read_bytes()
        source_hashes[relative] = hashlib.sha256(content).hexdigest()
        source_bytes[relative] = content
        st = p.stat()
        source_metadata[relative] = (st.st_size, st.st_mtime_ns)
        return content

    confirmation = json.loads(read(prep + 'SEMANTIC_FLAG_CONFIRMATION.json'))
    assert confirmation['instruction_english_translation'] == 'Do not require E02 to be selected at the same time.'
    build = json.loads(read(base + 'BUILD_RECORD.json'))
    read(base + 'Consolidated_ratings_working.xlsx')
    assert source_hashes[base + 'Consolidated_ratings_working.xlsx'] == build['workbook_sha256']
    for relative, expected in build['source_hashes'].items():
        if not (getattr((ROOT/relative).stat(), 'st_flags', 0) & 0x40000000):
            read(relative)
            assert source_hashes[relative] == expected, f'Changed source: {relative}'
    for relative, expected in build['source_hashes'].items():
        read(relative)
        assert source_hashes[relative] == expected, f'Changed source: {relative}'
    current = load_workbook(BytesIO(read(base + 'Consolidated_ratings_working.xlsx')), data_only=False)
    read(base + 'SCORING_AUDIT_2026-09-21.xlsx')
    audit = load_workbook(BytesIO(read(base + 'SCORING_AUDIT_2026-09-21.xlsx')), data_only=False)
    individual_issues = {r['Record key']: r for r in rows(current['Issues current'])}
    assert len(individual_issues) == 329
    coverage = rows(current['Coverage current'])
    assert len(coverage) == 552
    for row in coverage:
        assert len({row[who + ' decision'] for who in RATERS}) == 1
        assert all(row[who + ' status'] == 'Final' for who in RATERS)
    groups = []
    for row in rows(audit['Confirmed group crosswalk']):
        groups.append({'group_id': row['Audit group'], 'report_id': row['Report ID'],
                       'case_id': row['Case'], 'decision': 'Error', 'exact_anchor': row['Anchor'],
                       'record_keys': {who: row[who + ' key'] for who in RATERS},
                       'grouping_source': base + 'SCORING_AUDIT_2026-09-21.xlsx | Confirmed group crosswalk',
                       'scope': row['Scope']})
    groups.append({'group_id': 'AUDIT_F01', 'report_id': 'RDB18B7C593D48194',
                   'case_id': 'stroke_Sub15_P', 'decision': 'Error',
                   'exact_anchor': 'medial gastrocnemius (GAS)',
                   'record_keys': {who: f'{who}|RDB18B7C593D48194|AUDIT_F01' for who in RATERS},
                   'grouping_source': base + 'Consolidated_ratings_working.xlsx | Audit issue decisions',
                   'scope': 'One explicitly assessed anatomical-specificity claim, separate from other Sub15 issues.'})
    crosswalk = rows(current['Discussion crosswalk'])
    for row in rows(current['Discussion dispositions']):
        if row['decision'] != 'Pending adjudication':
            continue
        linked = [r for r in crosswalk if r['Claim ID'] == row['claim_id']]
        assert len(linked) == 3 and {r['Rater'] for r in linked} == set(RATERS)
        groups.append({'group_id': 'PENDING_' + row['claim_id'], 'report_id': row['report_id'],
                       'case_id': row['case_id'], 'decision': row['decision'],
                       'exact_anchor': row['exact_quote'],
                       'record_keys': {r['Rater']: r['Record key'] for r in linked},
                       'grouping_source': base + 'Consolidated_ratings_working.xlsx | Discussion dispositions and crosswalk',
                       'scope': row['basis']})
    assert Counter(g['decision'] for g in groups) == {'Error': 52, 'Pending adjudication': 16}
    assert len({g['group_id'] for g in groups}) == 68
    seen = set()
    for group in groups:
        text_path = f"docs/formal_study/rating_delivery_v1/rater2/reports/{group['report_id']}.txt"
        assert group['exact_anchor'] in read(text_path).decode('utf-8')
        group['individual_records'] = {}
        for who, key in group['record_keys'].items():
            assert key not in seen
            seen.add(key)
            row = individual_issues[key]
            assert row['Rater'] == who and row['Report ID'] == group['report_id']
            assert row['Case ID'] == group['case_id'] and row['Current decision'] == group['decision']
            group['individual_records'][who] = row
    assert seen == {key for key, row in individual_issues.items()
                    if row['Current decision'] in ('Error', 'Pending adjudication')}
    proposals = rows(current['Audit category proposals'])
    assert len(proposals) == 18
    for proposal in proposals:
        # Restrict matching to the established group registry and known exact
        # anchors; do not infer shared categories from any overlap.
        matching = [g for g in groups if g['report_id'] == proposal['Report ID']
                    and any(proposal['Exact quote'] in r['Exact quote'] or r['Exact quote'] in proposal['Exact quote']
                            for r in g['individual_records'].values())]
        assert len(matching) == 1, 'Ambiguous category-proposal link'
        matching[0].setdefault('personal_category_proposals', {})[proposal['Rater']] = proposal
    assert sum(len(g.get('personal_category_proposals', {})) for g in groups) == 18
    assert all(len(g['personal_category_proposals']) == 3 for g in groups if 'personal_category_proposals' in g)
    roster = {}
    for row in coverage:
        case = row['Case ID']
        roster.setdefault(case, {'group': case.split('_')[0], 'required_ids': set()})
        if row['Requirement'] != 'G03': roster[case]['required_ids'].add(row['Requirement'])
    for r in roster.values(): r['required_ids'] = sorted(r['required_ids'])
    assert Counter(r['group'] for r in roster.values()) == {'stroke': 25, 'control': 10}
    metrics, baselines = {}, {}
    for who in RATERS:
        p = f'docs/formal_study/three_rater_review_v1/private/{who}_submitted.xlsx'
        original = load_workbook(BytesIO(read(p)), data_only=False)
        baselines[who] = {'path': p, 'sha256': source_hashes[p],
                          'stage': 'Original independent; use for independent reliability and sensitivity only.'}
        review = {'rater': who, 'stage': 'post_feedback_individual', 'review': rows(original['Review']),
                  'coverage': [{'report_id': r['Report ID'], 'case_id': r['Case ID'],
                                'requirement_id': r['Requirement'], 'decision': r[who + ' decision'],
                                'adjudication_status': r[who + ' status']} for r in coverage],
                  'issues': [{'report_id': r['Report ID'], 'issue_id': r['Local issue ID'],
                              'decision': r['Current decision'], 'categories': r['Categories'],
                              'exact_quote': r['Exact quote'], 'pathology_flag': r['Pathology flag'],
                              'normality_flag': r['Normality flag']}
                             for r in individual_issues.values() if r['Rater'] == who]}
        metrics[who] = blinded_report_metrics(review, roster)
    reports = []
    for rid in sorted(metrics['rater1']):
        values = [metrics[who][rid] for who in RATERS]
        # The shared outcome view includes only identically recorded outcomes;
        # categories remain per-rater and no majority/union is manufactured.
        shared_fields = ('case_id', 'cohort', 'K', 'counts', 'unknown_items', 'coverage',
                         'coverage_bounds', 'g03', 'any_error', 'confirmed_issue_count',
                         'pending_issue_count', 'issue_review_complete', 'joint',
                         'joint_complete_review', 'available')
        assert all(all(v[k] == values[0][k] for v in values) for k in shared_fields)
        report = {'report_id': rid, **{k: values[0][k] for k in shared_fields},
                  'outcome_basis': 'Matching source-linked individual outcomes; no new human signature.'}
        report['control_flags_by_rater'] = {who: metrics[who][rid]['control_flags'] for who in RATERS}
        report['control_flags'] = {}
        report['flag_disagreements'] = []
        if report['cohort'] == 'control':
            for flag in ('pathology', 'normality'):
                states = [v['control_flags'][flag] for v in values]
                report['control_flags'][flag] = states[0] if all(s == states[0] for s in states) else None
                if any(s != states[0] for s in states): report['flag_disagreements'].append(flag)
        reports.append(report)
        linked = [g for g in groups if g['report_id'] == rid]
        assert sum(g['decision'] == 'Error' for g in linked) == report['confirmed_issue_count']
        assert sum(g['decision'] == 'Pending adjudication' for g in linked) == report['pending_issue_count']
    assert len(reports) == 105
    example = next(r for r in reports if r['report_id'] == 'R25F5AA9361D9E14F')
    assert example['control_flags']['pathology'] is True
    for p in ('scripts/freeze_blinded_three_rater_data.py', 'src/eval/three_rater_blinded.py',
              'src/eval/formal_analysis.py', prep + 'ANALYSIS_ADDENDUM_DRAFT.md',
              prep + 'AGREEMENT_AUTHORIZATION.json'):
        read(p)
    dataset = {'status': 'Frozen blinded administrative outcome dataset; no new expert signatures or model comparison',
               'frozen_at_utc': datetime.now(timezone.utc).isoformat(), 'model_mapping_read': False,
               'category_policy': 'Prior registered sets and latest personal proposals are separate; no common tags imposed.',
               'semantic_flag_policy_source': prep + 'SEMANTIC_FLAG_CONFIRMATION.json',
               'pending_policy': 'Administratively closed; substantively unresolved, neither Error nor Acceptable.',
               'original_independent_sources': baselines, 'roster': roster, 'reports': reports,
               'coverage': coverage, 'issue_groups': groups}
    payload = json.dumps(dataset, indent=2, ensure_ascii=False) + '\n'
    # Verify the exact captured bytes and check for on-disk revisions without
    # rehydrating files that iCloud has already evicted again. No source write is
    # performed; the manifest binds the verified snapshot, not future versions.
    assert all(hashlib.sha256(source_bytes[p]).hexdigest() == h for p, h in source_hashes.items())
    for p, expected_metadata in source_metadata.items():
        st = (ROOT/p).stat()
        assert (st.st_size, st.st_mtime_ns) == expected_metadata, f'Source changed during capture: {p}'
    destination.mkdir()
    (destination/'BLINDED_OUTCOMES.json').write_text(payload)
    frozen_hash = hashlib.sha256(payload.encode()).hexdigest()
    record = {'frozen_at_utc': dataset['frozen_at_utc'], 'dataset_sha256': frozen_hash,
              'reports': 105, 'participants': 35, 'coverage_rows': 552,
              'confirmed_issue_groups': 52, 'closed_pending_groups': 16,
              'individual_in_scope_records': len(seen), 'personal_category_proposals': 18,
              'category_proposal_groups_with_differences': sum(len({p['Personal proposed categories'] for p in g['personal_category_proposals'].values()}) > 1 for g in groups if 'personal_category_proposals' in g),
              'reports_with_control_flag_disagreements': sum(bool(r['flag_disagreements']) for r in reports),
              'model_mapping_read': False, 'new_human_signatures_created': 0,
              'capture_policy': 'Read each source once; verify captured bytes against registered hashes, parse those same bytes, and check source size/mtime for concurrent revisions. No repeated cloud reads.',
              'source_workbooks_modified': False, 'source_sha256': source_hashes}
    (destination/'FREEZE_RECORD.json').write_text(json.dumps(record, indent=2)+'\n')
    (destination/'README.md').write_text('''# Frozen blinded three-rater outcome data

This is an administrative analysis-input freeze from recorded human judgments, not a new expert signature or model-comparison result. Original independent reviews remain separately referenced for reliability and sensitivity analyses.

- 105 reports from 35 participants (25 stroke, 10 controls).
- 552 coverage rows, including 105 separate G03 judgments.
- 52 confirmed report-scoped issue groups and 16 closed Pending groups.
- Registered categories and all 18 personal category proposals remain separately visible; four claim groups have different proposed sets.
- Pathology annotations do not require a simultaneous E02 tag, under the study-lead confirmation dated 2026-09-23. Explicit expert annotations and confirmed issue status remain required. No new flags or diagnoses were inferred.

`BLINDED_OUTCOMES.json` contains the cohort-qualified roster, report outcomes, coverage rows, claim-group crosswalk, per-rater source records, and separate category proposals. `FREEZE_RECORD.json` binds the exact dataset and input hashes. The builder refuses to overwrite this directory. Future corrections require an explicit new version.

All original independent scores, reviewer workbooks and the historical protocol remain unchanged. Pending is not converted to Error or Acceptable; missing annotations are not No. Disagreement in a control-flag outcome would remain unknown in the shared view, with individual outcomes preserved. No majority vote or pooled category decision is introduced.

Source hashes and references preserve provenance but do not authenticate human identities or create full-dataset signatures. No protected model mapping has been read. A model-identity join and model-level analysis remain a separate step; the old two-rater adjudicator importer must not be used unchanged.
''')
    print(json.dumps({k: v for k, v in record.items() if k != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
