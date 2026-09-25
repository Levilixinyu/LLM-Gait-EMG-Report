"""Authorized model comparison of the immutable blinded outcome dataset."""
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.formal_analysis import ERRORS
from src.eval.frozen_model_analysis import analyze_report_metrics
from src.eval.three_rater_blinded import RATERS, blinded_report_metrics


def records(sheet):
    data = list(sheet.values)
    return [dict(zip(data[0], row)) for row in data[1:]]


def main():
    public = ROOT / 'docs/formal_study/model_comparison_v1'
    private = ROOT / 'data/rating_packets_formal_v1/private/three_rater_model_analysis_v1'
    assert not (private / 'ANALYSIS_BUILD_RECORD.json').exists(), 'Do not overwrite a completed analysis.'
    source_hashes = {}

    def read(path, expected=None):
        path = Path(path)
        raw = path.read_bytes(); h = hashlib.sha256(raw).hexdigest()
        if expected: assert h == expected, str(path)
        source_hashes[str(path.relative_to(ROOT))] = h
        return raw

    auth_raw = read(public / 'AUTHORIZATION.json'); auth = json.loads(auth_raw)
    assert auth['unblinding_authorized_for_analysis']
    unblind = json.loads(read(private / 'UNBLINDING_RECORD.json'))
    assert hashlib.sha256(auth_raw).hexdigest() == unblind['authorization_sha256']
    frozen = json.loads(read(ROOT/'docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json', auth['frozen_dataset_sha256']))
    freeze = json.loads(read(ROOT/'docs/formal_study/analysis_freeze_v1/FREEZE_RECORD.json'))
    assert freeze['dataset_sha256'] == auth['frozen_dataset_sha256'] == unblind['frozen_dataset_sha256']
    mapping_raw = read(private/'mapping_snapshot.json', unblind['mapping_sha256'])
    mapping = json.loads(mapping_raw)['mapping']
    integrity = json.loads(read(private/'package_integrity_snapshot.json', unblind['package_integrity_sha256']))
    assert hashlib.sha256(mapping_raw).hexdigest() == integrity['files_sha256']['private/answer_key_DO_NOT_SHARE.json']
    roster, report_rows = frozen['roster'], {r['report_id']: r for r in frozen['reports']}
    assert set(report_rows) == set(mapping) and len(report_rows) == 105
    models = sorted({r['model_key'] for r in mapping.values()})
    assert len(models) == 3
    names, model_metadata = {}, {}
    for model in models:
        entries = [r for r in mapping.values() if r['model_key'] == model]
        requested = sorted({r['metadata']['requested_model'] for r in entries})
        returned = sorted({r['metadata']['response_model'] for r in entries})
        assert len(entries) == 35 and len(requested) == 1
        names[model] = requested[0]
        model_metadata[model] = {'requested_model': requested, 'returned_model': returned,
                                 'reports': 35, 'terminal_statuses': dict(Counter(r['terminal_status'] for r in entries)),
                                 'truncation': dict(Counter(str(r['truncation']) for r in entries)),
                                 'normal_stream_completion': dict(Counter(str(r['normal_stream_completion']) for r in entries))}
    metric_slots = {}
    for rid, r in report_rows.items():
        identity = mapping[rid]
        assert identity['case_id'] == r['case_id']
        report_path = f'docs/formal_study/rating_delivery_v1/rater2/reports/{rid}.txt'
        assert identity['report_sha256'] == freeze['source_sha256'][report_path]
        key = r['case_id'], identity['model_key']
        assert key not in metric_slots
        metric_slots[key] = {k: v for k, v in r.items() if k not in (
            'report_id', 'outcome_basis', 'control_flags_by_rater', 'flag_disagreements')}
        assert not r['flag_disagreements']
    estimates, indices = analyze_report_metrics(roster, models, metric_slots)
    sensitivity, sensitivity_indices, operations = {}, {}, {}
    for who in RATERS:
        original = frozen['original_independent_sources'][who]
        wb = load_workbook(BytesIO(read(ROOT/original['path'], original['sha256'])), data_only=False)
        review = {'rater': who, 'stage': 'original_independent',
                  **{sn.lower(): records(wb[sn]) for sn in ('Review', 'Coverage', 'Issues')}}
        per_report = blinded_report_metrics(review, roster)
        assert set(per_report) == set(mapping)
        slots = {(r['case_id'], mapping[rid]['model_key']): r for rid, r in per_report.items()}
        sensitivity[who], sensitivity_indices[who] = analyze_report_metrics(roster, models, slots)
        operations[who] = review['review']
    categories = {(cohort, model, who): Counter({tag: 0 for tag in ERRORS})
                  for cohort in ('stroke', 'control') for model in models for who in RATERS}
    category_trace = []
    for g in frozen['issue_groups']:
        if g['decision'] != 'Error': continue
        cohort = roster[g['case_id']]['group']; model = mapping[g['report_id']]['model_key']
        for who, r in g['individual_records'].items():
            proposal = g.get('personal_category_proposals', {}).get(who)
            tags = proposal['Personal proposed categories'] if proposal else r['Categories']
            assert set(tags.split(';')) <= ERRORS
            categories[cohort, model, who].update(set(tags.split(';')))
            category_trace.append({'group_id': g['group_id'], 'case_id': g['case_id'], 'model': model,
                                   'rater': who, 'registered_categories': r['Categories'],
                                   'latest_individual_tag_view': tags,
                                   'basis': 'Personal proposal, not shared consensus' if proposal else 'Registered individual tags'})
    category_rows = [{'cohort': c, 'model': m, 'rater': r, 'counts': dict(sorted(v.items()))}
                     for (c, m, r), v in sorted(categories.items())]
    # Independent arithmetic cross-checks of the actual primary data, before export.
    assert estimates['primary_stroke']['n'] == 25 and not estimates['primary_stroke']['excluded_case_ids']
    assert indices.shape == (20000, 25)
    assert sum(r['confirmed_issue_count'] for r in estimates['per_report']) == 52
    assert sum(r['pending_issue_count'] for r in estimates['per_report']) == 16
    for model in models:
        fractions = [r['coverage'] for r in estimates['per_report'] if r['cohort'] == 'stroke' and r['model'] == model]
        assert abs(sum(fractions)/25 - estimates['primary_stroke']['paired_model_means'][model]) < 1e-12
    for relative in ('scripts/analyze_frozen_three_rater_models.py', 'src/eval/frozen_model_analysis.py',
                     'src/eval/formal_analysis.py', 'src/eval/three_rater_blinded.py',
                     'docs/formal_study/three_rater_analysis_v1/SEMANTIC_FLAG_CONFIRMATION.json'):
        read(ROOT/relative)
    assert source_hashes['src/eval/formal_analysis.py'] == freeze['source_sha256']['src/eval/formal_analysis.py']
    stamp = datetime.now(timezone.utc).isoformat()
    final = {'computed_at_utc': stamp, 'frozen_dataset_sha256': auth['frozen_dataset_sha256'],
             'model_labels_from_saved_generation_metadata': names, 'estimates': estimates,
             'interpretation': 'Selected internal cases; post-feedback source-linked outcomes. Not diagnostic accuracy or repeated-generation reliability.',
             'common_category_counts': 'Not imposed. See per-rater tag views; one issue group is counted once regardless of tags.'}
    private_outputs = {'final_outcomes.json': final, 'independent_sensitivity.json': sensitivity,
                       'category_counts_by_rater.json': {'counts': category_rows, 'claim_trace': category_trace},
                       'model_metadata.json': model_metadata, 'original_review_operations.json': operations}
    assert not any((private/name).exists() for name in private_outputs)
    for name, value in private_outputs.items(): (private/name).write_text(json.dumps(value, indent=2)+'\n')
    np.save(private/'final_resample_indices.npy', indices, allow_pickle=False)
    for who in RATERS: np.save(private/f'{who}_resample_indices.npy', sensitivity_indices[who], allow_pickle=False)

    wb = Workbook(); wb.remove(wb.active)

    def sheet(name, headers, values):
        ws = wb.create_sheet(name); ws.append(headers)
        for row in values: ws.append(row)
        ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions
        for c in ws[1]:
            c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='24476A')
        for row in ws:
            for c in row:
                if isinstance(c.value, (dict, list)): raise ValueError('Flatten workbook values explicitly')
                c.alignment = Alignment(wrap_text=True, vertical='top'); ws.column_dimensions[c.column_letter].width = 24
        return ws

    def interval(x):
        return 'Unavailable' if x is None else f'{x[0]:.3f} to {x[1]:.3f}'

    summary_rows = []
    for cohort in ('stroke', 'control'):
        for model in models:
            r = estimates['cohort_summaries'][cohort]['by_model'][model];e = r['any_error'];j=r['joint']
            summary_rows.append([cohort, names[model], r['available_case_coverage_n'], r['available_case_coverage_mean'],
                                 e['events'], e['evaluable'], e['unknown'], e['proportion'], interval(e['exact_95_interval']),
                                 interval(e['all_planned_bounds']), sum(r['confirmed_issue_counts']),
                                 sum(x['pending_issue_count'] for x in estimates['per_report'] if x['cohort']==cohort and x['model']==model),
                                 j['events'], j['evaluable'], j['proportion'], interval(j['all_planned_bounds'])])
    sheet('Read first', ['Topic','Meaning'], [
        ['Scope','25 stroke cases primary; 10 controls separate exploratory supplement. One response per case/configuration.'],
        ['Coverage','Mean of participant-specific Covered/K; equal case weight. G03 separate; partial is not half credit.'],
        ['Uncertainty','Pending-only any-error is unknown. Show evaluable denominators and all-planned bounds.'],
        ['Categories','Personal tag views are not consensus categories. Tags and repeated locations do not multiply an issue group.'],
        ['Independent reviews','Original independent sensitivity is separate from post-feedback results. Do not compute reliability from the latter.'],
        ['Model labels','Requested and returned identifiers from this project; no claim of current API availability.'],
        ['Intervals','Paired participant BCa: 20,000 resamples, seed 20260918; 95% descriptive and 98.3333% family-adjusted. Degenerate intervals remain unavailable.'],
        ['Limits','Selected internal sample and shared references; no clinical deployment, diagnostic-accuracy or universal-superiority claim.'],
    ])
    sheet('Cohort model summary', ['Cohort','Model','Cases with coverage','Mean full coverage','Error-positive reports','Error evaluable reports','Unknown error reports','Error proportion','Exact 95 interval','All-planned error bounds','Confirmed groups','Pending groups','Joint successes','Joint eligible reports','Joint proportion','All-planned joint bounds'], summary_rows)
    contrast_rows=[]
    for contrast, r in estimates['primary_stroke']['contrasts'].items():
        a,b=contrast.split(' - '); contrast_rows.append([names[a],names[b],r['mean_difference_percentage_points'],interval(r['descriptive_95']['interval']),interval(r['family_adjusted_98_3333']['interval']),r['descriptive_95']['reason'],r['family_adjusted_98_3333']['reason']])
    sheet('Primary paired contrasts',['Model A','Model B','A minus B percentage points','95% BCa','98.3333% BCa','95% unavailable reason','98.3333% unavailable reason'],contrast_rows)
    sheet('Per case outcomes',['Case','Cohort','Model','K','Covered','Partially covered','Not covered','Coverage','G03','Confirmed groups','Pending groups','Any error','Joint','Complete joint review','Pathology','Normality'],
          [[r['case_id'],r['cohort'],names[r['model']],r['K'],r['counts']['Covered'],r['counts']['Partially covered'],r['counts']['Not covered'],r['coverage'],r['g03'],r['confirmed_issue_count'],r['pending_issue_count'],r['any_error'],r['joint'],r['joint_complete_review'],r['control_flags'].get('pathology'),r['control_flags'].get('normality')] for r in estimates['per_report']])
    sheet('Category views',['Cohort','Model','Rater',*sorted(ERRORS)],[[r['cohort'],names[r['model']],r['rater'],*[r['counts'][t] for t in sorted(ERRORS)]] for r in category_rows])
    flags=[]
    for model in models:
        for flag,r in estimates['cohort_summaries']['control']['by_model'][model]['control_flags'].items():
            flags.append([names[model],flag,r['events'],r['evaluable'],r['unknown'],r['proportion'],interval(r['exact_95_interval']),interval(r['all_planned_bounds']),r['zero_event_one_sided_95_upper']])
    sheet('Control semantic flags',['Model','Flag','Events','Evaluable','Unknown','Proportion','Exact 95 interval','All-planned bounds','Zero-event one-sided 95 upper'],flags)
    sheet('Independent sensitivity',['Rater','Cohort','Model','Mean full coverage','Error events','Error evaluable','Unknown error reports','Error all-planned bounds'],
          [[who,cohort,names[model],r['available_case_coverage_mean'],r['any_error']['events'],r['any_error']['evaluable'],r['any_error']['unknown'],interval(r['any_error']['all_planned_bounds'])]
           for who,result in sensitivity.items() for cohort in ('stroke','control') for model,r in result['cohort_summaries'][cohort]['by_model'].items()])
    sheet('Generation capture',['Model','Reports','Requested IDs','Returned IDs','Terminal status','Truncation','Normal stream completion'],
          [[names[m],r['reports'],'; '.join(r['requested_model']),'; '.join(r['returned_model']),json.dumps(r['terminal_statuses']),json.dumps(r['truncation']),json.dumps(r['normal_stream_completion'])] for m,r in model_metadata.items()])
    workbook=public/'Model_comparison.xlsx';assert not workbook.exists();wb.save(workbook)
    lines=['# Model comparison from the frozen three-rater dataset','',f'Computed UTC: {stamp}. Frozen dataset SHA-256: `{auth["frozen_dataset_sha256"]}`.','',
           'Model identities were joined only after the blinded freeze and study-lead authorization. The historical two-rater adjudicator importer was not used. Original scores and the frozen dataset were not modified.','',
           '## Main and supplementary outcomes','',
           '| Cohort | Model identifier | Mean full coverage | Confirmed-error reports / evaluable | Unknown error reports | All-planned error bounds | Confirmed issue groups | Pending groups |',
           '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in summary_rows:
        lohi=estimates['cohort_summaries'][row[0]]['by_model'][next(m for m in models if names[m]==row[1])]['any_error']['all_planned_bounds']
        lines.append(f'| {row[0]} | {row[1]} | {row[3]:.1%} | {row[4]}/{row[5]} | {row[6]} | {lohi[0]:.1%}–{lohi[1]:.1%} | {row[10]} | {row[11]} |')
    lines+=['','Coverage is the mean of each participant\'s Covered/K, not the pooled item fraction. G03 is excluded from K. The primary paired stroke analysis includes all 25 participants. Error proportions use evaluable reports; the bounds retain all planned slots. Pending is not an error-free judgment.','',
            '## Paired primary stroke contrasts','',
            '| A minus B | Mean difference, percentage points | Descriptive 95% BCa | Family-adjusted 98.3333% BCa |','| --- | --- | --- | --- |']
    for row in contrast_rows:lines.append(f'| {row[0]} minus {row[1]} | {row[2]:.3f} | {row[3]} | {row[4]} |')
    lines+=['','Intervals use 20,000 shared participant-resampling indices, seed 20260918. An unavailable interval is retained as unavailable; no alternative interval method is chosen after seeing results. Zero-crossing intervals do not establish equivalence. No secondary-outcome confirmatory tests or omnibus model-quality score are introduced.','',
            '## Control semantic flags','', '| Model | Flag | Events / evaluable | Unknown | Exact 95% interval | Zero-event one-sided 95% upper |','| --- | --- | --- | --- | --- | --- |']
    for row in flags:lines.append(f'| {row[0]} | {row[1]} | {row[2]}/{row[3]} | {row[4]} | {row[6]} | {row[8]:.1%} |' if row[8] is not None else f'| {row[0]} | {row[1]} | {row[2]}/{row[3]} | {row[4]} | {row[6]} | Not applicable |')
    lines+=['','These are unsupported semantic inferences in reports, not diagnostic false-positive rates. A pathology annotation need not carry E02 if the human reviewer explicitly confirms the impairment inference. Ten controls per model provide limited precision; zero observed flags do not establish zero risk.','',
            '## Interpretation and provenance','',
            '- The sample is selected and internal; controls contributed to reference construction. One report per configuration cannot quantify repeated-generation variation.',
            '- Primary outcomes are post-feedback source-linked human judgments. The independent sensitivity sheet preserves the original judgments; it is not interchangeable with final outcomes or new reliability.',
            '- Category tables retain each reviewer\'s latest explicit proposal where present and registered tags otherwise. There is no majority category, tag-order rule, or multiplication of error groups.',
            '- Requested/returned model identifiers are taken from the saved generation metadata, not a claim about current product availability.',
            '- The protected analysis directory retains the raw estimates, independent sensitivities, category trace, generation capture metadata, source hashes, and exact resampling matrices. The identity key was not placed in rater materials.',
            '- See Model_comparison.xlsx for per-case values, cohort summaries, denominators, control flags, category views and original-independent sensitivity.', '']
    report=public/'RESULTS.md';assert not report.exists();report.write_text('\n'.join(lines))
    outputs=[private/name for name in private_outputs]+[private/'final_resample_indices.npy']+[private/f'{who}_resample_indices.npy' for who in RATERS]+[workbook,report]
    manifest={'computed_at_utc':stamp,'frozen_dataset_sha256':auth['frozen_dataset_sha256'],
              'source_sha256':source_hashes,'output_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},
              'primary_paired_stroke_n':25,'resamples':20000,'seed':20260918,
              'model_mapping_joined':True,'source_ratings_modified':False,'shared_category_set_imposed':False}
    (private/'ANALYSIS_BUILD_RECORD.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'model_labels':names,'summary_rows':summary_rows,'paired_contrasts':contrast_rows,'control_flags':flags,'primary_n':25},indent=2))


if __name__=='__main__':main()
