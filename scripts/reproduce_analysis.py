"""Verify and replay an extracted, self-contained analysis bundle without APIs."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PRIVATE = 'data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_bundle(root):
    """Fail closed on missing, changed, escaped or symlinked inputs."""
    root = root.resolve()
    manifest = json.loads((root / 'REPRODUCTION_MANIFEST.json').read_text())
    if manifest.get('schema') != 1 or not manifest.get('files'):
        raise ValueError('Unsupported or empty reproduction manifest')
    for name, expected in manifest['files'].items():
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or '\\' in name:
            raise ValueError(f'Unsafe manifest path: {name}')
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Escaped or symlinked source: {name}')
        if sha(path.read_bytes()) != expected:
            raise ValueError(f'Source hash mismatch: {name}')
    return manifest


def compare(actual, expected, label):
    if actual != expected:
        raise ValueError(f'Reproduction differs from recorded result: {label}')


def run(root, output):
    root, output = root.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError('Output must be a new directory outside the extracted bundle')
    manifest = verify_bundle(root)
    import numpy as np
    from src.eval.formal_analysis import binary_summary
    from src.eval.frozen_model_analysis import analyze_report_metrics
    from src.eval.three_rater_blinded import blinded_report_metrics, pairwise_blinded_agreement
    from src.eval.wording_sensitivity import overlay_reports
    from src.eval.agreement_sensitivity import analyze_original_agreement

    def read(name):
        if name not in manifest['files']:
            raise ValueError(f'Unregistered input: {name}')
        return json.loads((root / name).read_text())

    frozen = read('docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json')
    mapping = read(PRIVATE + 'mapping_snapshot.json')['mapping']
    models = sorted({r['model_key'] for r in mapping.values()})
    compare(set(mapping), {r['report_id'] for r in frozen['reports']}, 'report membership')
    coverage, groups = defaultdict(list), defaultdict(list)
    for row in frozen['coverage']:
        coverage[row['Report ID']].append(row)
    for group in frozen['issue_groups']:
        groups[group['report_id']].append(group)
    for row in frozen['reports']:
        rid = row['report_id']
        compare(mapping[rid]['case_id'], row['case_id'], 'case mapping')
        cs = [c for c in coverage[rid] if c['Requirement'] != 'G03']
        for c in coverage[rid]:
            compare(len({c[w + ' decision'] for w in ('rater1','rater2','rater3')}), 1, 'frozen coverage agreement')
        counts = Counter(c['rater1 decision'] for c in cs)
        compare(len(cs), row['K'], 'coverage denominator')
        compare({k: counts[k] for k in row['counts']}, row['counts'], 'coverage counts')
        compare(counts['Covered']/len(cs), row['coverage'], 'coverage proportion')
        compare(sum(g['decision']=='Error' for g in groups[rid]), row['confirmed_issue_count'], 'error count')
        compare(sum(g['decision']=='Pending adjudication' for g in groups[rid]), row['pending_issue_count'], 'pending count')
        name = f'docs/formal_study/rating_delivery_v1/rater2/reports/{rid}.txt'
        raw = (root / name).read_bytes()
        compare(sha(raw), mapping[rid]['report_sha256'], 'saved report')
        text = raw.decode('utf-8')
        for g in groups[rid]:
            if g['exact_anchor'] not in text or any(v['Exact quote'] not in text for v in g['individual_records'].values()):
                raise ValueError(f'Claim quotation mismatch: {g["group_id"]}')

    def metrics(rows):
        return {(r['case_id'], mapping[r['report_id']]['model_key']):
                {k:v for k,v in r.items() if k not in
                 ('report_id','outcome_basis','control_flags_by_rater','flag_disagreements')}
                for r in rows}

    final, indices = analyze_report_metrics(frozen['roster'], models, metrics(frozen['reports']))
    compare(final, read(PRIVATE + 'final_outcomes.json')['estimates'], 'frozen estimates')
    reviews = read('reproduction_inputs/original_reviews.json')['reviews']
    independent = {}
    for who, review in reviews.items():
        rows = blinded_report_metrics(review, frozen['roster'])
        slots = {(r['case_id'], mapping[rid]['model_key']): r for rid, r in rows.items()}
        independent[who], original_indices = analyze_report_metrics(frozen['roster'], models, slots)
        if not np.array_equal(indices, original_indices):
            raise ValueError('Resampling indices changed across rating stages')
    compare(independent, read(PRIVATE + 'independent_sensitivity.json'), 'original independent estimates')
    pairs = pairwise_blinded_agreement(reviews, frozen['roster'])
    saved_pairs = read('docs/formal_study/three_rater_analysis_v1/INDEPENDENT_AGREEMENT.json')['pairs']
    compare({k:v['cohorts'] for k,v in pairs.items()}, {k:v['cohorts'] for k,v in saved_pairs.items()}, 'original agreement')
    ac1 = analyze_original_agreement(reviews, frozen['roster'])
    compare(ac1, read('docs/formal_study/agreement_sensitivity_v1/AC1_ANALYSIS.json'), 'post-hoc original AC1')

    saved = read('data/rating_packets_formal_v1/private/wording_sensitivity_v1/ANALYSIS.json')
    summaries, per_report = [], []
    fields = ('report_id','case_id','cohort','any_error','joint','joint_complete_review',
              'confirmed_issue_count','pending_issue_count','coverage','control_flags')
    for scenario in saved['scenario_definitions']:
        rows = overlay_reports(frozen, scenario['decisions'], pathology_overrides=scenario['flags'])
        for row in rows:
            per_report.append({'scenario':scenario['id'], 'model':mapping[row['report_id']]['model_key'],
                               **{k:row[k] for k in fields}})
        for expected in (s for s in saved['summaries'] if s['scenario']==scenario['id']):
            cohort, model = expected['cohort'], expected['model']
            subset = [r for r in rows if r['cohort']==cohort and mapping[r['report_id']]['model_key']==model]
            actual = {k:expected[k] for k in ('scenario','label','cohort','model','model_identifier')}
            actual.update(coverage_mean=sum(r['coverage'] for r in subset)/len(subset),
                any_error=binary_summary([r['any_error'] for r in subset], control=cohort=='control'),
                joint=binary_summary([r['joint'] for r in subset], control=cohort=='control',
                                     point_eligible=[r['joint_complete_review'] for r in subset]),
                control_flags={flag:binary_summary([r['control_flags'][flag] for r in subset],control=True)
                               for flag in ('pathology','normality')} if cohort=='control' else {},
                confirmed_groups=sum(r['confirmed_issue_count'] for r in subset),
                pending_groups=sum(r['pending_issue_count'] for r in subset))
            compare(actual, expected, 'wording scenario summary')
            summaries.append(actual)
    compare(per_report, saved['per_report'], 'wording per-report scenarios')
    output.mkdir(parents=True, exist_ok=False)
    for name, data in [('final_outcomes.json',final),('independent_outcomes.json',independent),
                       ('independent_agreement.json',pairs),('wording_summaries.json',summaries),
                       ('original_ac1.json',ac1)]:
        (output/name).write_text(json.dumps(data,indent=2)+'\n')
    np.save(output/'resample_indices.npy',indices)
    subprocess.run([sys.executable, '-B', str(root/'scripts/build_manuscript_draft.py'),
                    '--root',str(root),'--output',str(output/'manuscript')],check=True)
    compare(json.loads((output/'manuscript/TABLE_DATA.json').read_text())['tables'],
            read('docs/formal_study/manuscript_v1/TABLE_DATA.json')['tables'], 'all manuscript tables')
    verify_bundle(root)
    result = {'status':'PASS','python':platform.python_version(), 'manifest_sha256':sha((root/'REPRODUCTION_MANIFEST.json').read_bytes()),
              'files_verified':len(manifest['files']), 'reports':len(frozen['reports']), 'participants':len(frozen['roster']),
              'original_reviews':len(reviews), 'manuscript_tables':len(read('docs/formal_study/manuscript_v1/TABLE_DATA.json')['tables']), 'wording_scenarios':len(saved['scenario_definitions']),
              'frozen_estimates_exact':True,'original_estimates_exact':True,'agreement_exact':True,
              'original_ac1_exact':True,
              'wording_summaries_and_report_rows_exact':True,'manuscript_tables_exact':True,
              'source_inputs_modified':False,'api_calls':0,
              'scope_limit':'Starts from preserved judgments and supplied summaries; does not regenerate model outputs or independently rerate reports or rebuild features from raw recordings.'}
    (output/'REPRODUCTION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory outside this bundle')
    args = parser.parse_args()
    run(ROOT, args.output)
