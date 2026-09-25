"""Additive post-unblinding sensitivity; never modify frozen or rater inputs."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from src.eval.formal_analysis import binary_summary
from src.eval.wording_sensitivity import overlay_reports

BASE = ROOT / 'docs/formal_study/wording_boundary_confirmation_v1'
OUT = ROOT / 'docs/formal_study/wording_sensitivity_v1'
OLD = ROOT / 'data/rating_packets_formal_v1/private/three_rater_model_analysis_v1'
PRIVATE = ROOT / 'data/rating_packets_formal_v1/private/wording_sensitivity_v1'
FROZEN = ROOT / 'docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json'
RATERS = ('rater1', 'rater2', 'rater3')
NAMES = {'anthropic': 'Claude Opus 5', 'gemini': 'Gemini 3.1 Pro preview', 'openai': 'GPT-6-astra'}
SCOPE = ('AG004', 'AG011', 'AG019', 'AG023', 'AG028', 'AG048', 'AG050', 'AG051')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def table(headers, rows):
    return '| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join('---' for _ in headers) + ' |\n' + ''.join(
        '| ' + ' | '.join(str(v) for v in row) + ' |\n' for row in rows)


def bounds(values):
    return f'{values[0]:.0%}-{values[1]:.0%}'


def main():
    sources = {}

    def read(path):
        raw = path.read_bytes()
        sources[str(path.relative_to(ROOT))] = sha(raw)
        return raw

    def read_json(path):
        return json.loads(read(path))

    prior_build = read_json(OLD / 'ANALYSIS_BUILD_RECORD.json')
    frozen = read_json(FROZEN)
    assert sources[str(FROZEN.relative_to(ROOT))] == prior_build['frozen_dataset_sha256']
    mapping = read_json(OLD / 'mapping_snapshot.json')['mapping']
    assert sources[str((OLD / 'mapping_snapshot.json').relative_to(ROOT))] == prior_build['source_sha256'][str((OLD / 'mapping_snapshot.json').relative_to(ROOT))]
    prior = read_json(OLD / 'final_outcomes.json')
    assert sources[str((OLD / 'final_outcomes.json').relative_to(ROOT))] == prior_build['output_sha256'][str((OLD / 'final_outcomes.json').relative_to(ROOT))]
    receipt = read_json(BASE / 'return_review/RETURN_CHECK.json')
    assert receipt['frozen_sha256'] == prior_build['frozen_dataset_sha256']
    read(BASE / 'return_review/RATER2_RATIONALE_CORRECTION.json')
    for who in RATERS:
        r = receipt['returns'][who]
        assert r['form_complete_and_template_intact'] and r['human_review_and_adoption_confirmed']
        assert set(r['decisions']) == set(SCOPE)
        assert sha(read(ROOT / r['source'])) == r['sha256']
    read(Path(__file__).resolve())
    read(ROOT / 'src/eval/wording_sensitivity.py')
    read(ROOT / 'src/eval/formal_analysis.py')
    groups = {g['group_id']: g for g in frozen['issue_groups']}
    baseline_reports = {r['report_id']: r for r in frozen['reports']}
    assert len(mapping) == len(baseline_reports) == 105 and set(mapping) == set(baseline_reports)
    assert all(mapping[rid]['case_id'] == r['case_id'] for rid, r in baseline_reports.items())
    assert all(groups[gid]['decision'] == 'Error' for gid in SCOPE)
    submitted = {who: {gid: receipt['returns'][who]['decisions'][gid]['decision'] for gid in SCOPE}
                 for who in RATERS}
    disputed = [gid for gid in SCOPE if len({submitted[w][gid] for w in RATERS}) > 1]
    agreed = [gid for gid in SCOPE if gid not in disputed]
    assert disputed == ['AG011', 'AG028', 'AG048', 'AG050']
    assert all(submitted[w][gid] == 'Error' for w in RATERS for gid in agreed)
    control_rid = groups['AG023']['report_id']
    flag_values = {'Yes': True, 'No': False, 'Uncertain': None}
    flags = {w: flag_values[receipt['returns'][w]['control_annotation']['flag']] for w in RATERS}

    scenarios = [{'id': 'frozen', 'label': 'Frozen baseline', 'decisions': {}, 'flags': {},
                  'basis': 'Original shared frozen outcome layer; unchanged.'}]
    for who in RATERS:
        scenarios.append({'id': who, 'label': f'{who} targeted overlay', 'decisions': submitted[who],
                          'flags': {control_rid: flags[who]},
                          'basis': 'Only the eight targeted decisions and the AG023 pathology annotation use this reviewer; every other rating retains the shared frozen baseline. This is a hybrid sensitivity, not this reviewer\'s complete independent assessment.'})
    for key, label, decision, flag in (
            ('disputed_pending', 'Disagreements kept unknown', 'Pending adjudication', None),
            ('disputed_acceptable', 'Disputed claims cleared', 'Acceptable', False),
            ('disputed_error', 'Disputed claims counted', 'Error', True)):
        scenarios.append({'id': key, 'label': label, 'decisions': {gid: decision for gid in disputed},
                          'flags': {control_rid: flag},
                          'basis': 'Analyst-defined post-hoc scenario, not a new expert consensus. Four matching Error labels are retained. The four disputed claims and the separate disputed pathology flag vary; all pre-existing Pending groups remain Pending.'})

    summaries, private_rows, changed_rows, decision_rows = [], [], [], []
    for gid in SCOPE:
        decision_rows.append({'Item': gid, **{w: submitted[w][gid] for w in RATERS},
                              'Label status': 'Divergent' if gid in disputed else 'Matching Error'})
    selected_fields = ('report_id', 'case_id', 'cohort', 'any_error', 'joint', 'joint_complete_review',
                       'confirmed_issue_count', 'pending_issue_count', 'coverage', 'control_flags')
    for scenario in scenarios:
        rows = overlay_reports(frozen, scenario['decisions'], pathology_overrides=scenario['flags'])
        for row in rows:
            original = baseline_reports[row['report_id']]
            for k in ('coverage', 'counts', 'unknown_items', 'coverage_bounds', 'g03', 'available', 'issue_review_complete'):
                assert row[k] == original[k]
            if scenario['id'] == 'frozen':
                for k in selected_fields:
                    assert row[k] == original[k], (row['report_id'], k)
            model = mapping[row['report_id']]['model_key']
            private_rows.append({'scenario': scenario['id'], 'model': model,
                                 **{k: row[k] for k in selected_fields}})
            changes = {k: {'before': original[k], 'after': row[k]} for k in selected_fields if row[k] != original[k]}
            if changes:
                changed_rows.append({'scenario': scenario['id'], 'model': model,
                                     'report_id': row['report_id'], 'case_id': row['case_id'], 'changes': changes})
        for cohort in ('stroke', 'control'):
            for model in NAMES:
                subset = [r for r in rows if r['cohort'] == cohort and mapping[r['report_id']]['model_key'] == model]
                assert len(subset) == (25 if cohort == 'stroke' else 10)
                error = binary_summary([r['any_error'] for r in subset], control=cohort == 'control')
                joint = binary_summary([r['joint'] for r in subset], control=cohort == 'control',
                                       point_eligible=[r['joint_complete_review'] for r in subset])
                flag_summary = {flag: binary_summary([r['control_flags'][flag] for r in subset], control=True)
                                for flag in ('pathology', 'normality')} if cohort == 'control' else {}
                if scenario['id'] == 'frozen':
                    saved = prior['estimates']['cohort_summaries'][cohort]['by_model'][model]
                    assert error == saved['any_error'] and joint == saved['joint']
                    assert flag_summary == saved['control_flags']
                summaries.append({'scenario': scenario['id'], 'label': scenario['label'], 'cohort': cohort,
                    'model': model, 'model_identifier': prior['model_labels_from_saved_generation_metadata'][model],
                    'coverage_mean': sum(r['coverage'] for r in subset) / len(subset),
                    'any_error': error, 'joint': joint, 'control_flags': flag_summary,
                    'confirmed_groups': sum(r['confirmed_issue_count'] for r in subset),
                    'pending_groups': sum(r['pending_issue_count'] for r in subset)})

    # No changed report must escape the explicitly reviewed report set.
    assert {r['report_id'] for r in changed_rows} <= {groups[gid]['report_id'] for gid in SCOPE}
    assert {r['report_id'] for r in changed_rows if 'any_error' in r['changes']} == {
        groups['AG011']['report_id'], groups['AG048']['report_id']}
    # All control any-error and all non-Gemini error summaries remain unchanged.
    for s in summaries:
        baseline = next(x for x in summaries if x['scenario'] == 'frozen' and x['cohort'] == s['cohort'] and x['model'] == s['model'])
        assert abs(s['coverage_mean'] - baseline['coverage_mean']) < 1e-12
        if s['cohort'] == 'control' or s['model'] != 'gemini':
            assert s['any_error'] == baseline['any_error']
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    analysis = {'computed_at_utc': stamp, 'status': 'Post-unblinding exploratory sensitivity; no replacement freeze',
                'scenario_definitions': scenarios, 'summaries': summaries, 'targeted_positions': decision_rows,
                'control_annotation_by_rater': flags, 'primary_coverage_reused_unchanged': prior['estimates']['primary_stroke'],
                'per_report': private_rows, 'changed_reports': changed_rows,
                'source_sha256': sources, 'source_ratings_modified': False, 'frozen_outcomes_modified': False}
    (PRIVATE / 'ANALYSIS.json').write_text(json.dumps(analysis, indent=2) + '\n')

    def summary_row(s):
        e = s['any_error']
        return {'Scenario': s['label'], 'Cohort': s['cohort'], 'Model': s['model_identifier'],
                'Error reports': e['events'], 'Evaluable': e['evaluable'], 'Unknown': e['unknown'],
                'Planned': e['planned'], 'Error proportion': e['proportion'],
                'All-planned lower': e['all_planned_bounds'][0], 'All-planned upper': e['all_planned_bounds'][1],
                'Confirmed groups': s['confirmed_groups'], 'Pending groups': s['pending_groups']}

    w = Workbook()
    w.remove(w.active)

    def sheet(name, records):
        ws = w.create_sheet(name)
        ws.append(list(records[0]))
        for record in records:
            ws.append(list(record.values()))
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='23475A')
        for row in ws:
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                if isinstance(cell.value, str):
                    cell.data_type = 's'
        for column in ws.columns:
            ws.column_dimensions[column[0].column_letter].width = 26
        for row in range(2, ws.max_row + 1):
            ws.row_dimensions[row].height = 48
        for cell in ws[1]:
            if cell.value in ('Error proportion', 'All-planned lower', 'All-planned upper', 'Mean full coverage'):
                for row in range(2, ws.max_row + 1):
                    ws.cell(row, cell.column).number_format = '0.0%'
        return ws

    notes = [
        {'Topic': 'Scope', 'Explanation': 'Exploratory post-unblinding analysis of eight targeted claims. Original frozen outcomes, original independent ratings and source returns are unchanged.'},
        {'Topic': 'Hybrid overlays', 'Explanation': 'A named-rater scenario substitutes only that reviewer\'s eight latest labels and one flag. It does not represent a full independent re-rating by that reviewer.'},
        {'Topic': 'Disagreement scenarios', 'Explanation': 'No voting or forced consensus. Pending/cleared/counted scenarios are analyst-defined alternatives. Previously frozen Pending groups remain Pending in every scenario.'},
        {'Topic': 'Bounds', 'Explanation': 'All-planned bounds count unknown report status as 0/1. They are not confidence intervals. A report is positive if any confirmed error remains; negative requires a complete review without confirmed or pending errors.'},
        {'Topic': 'Joint outcome', 'Explanation': 'The point estimate uses complete nonpending reviews, as in the existing protocol. Known failure with an unresolved issue can be outside that denominator but still constrains all-planned bounds.'},
        {'Topic': 'Categories and flags', 'Explanation': 'No shared E-code set is imposed. The AG023 pathology annotation varies independently of its matching Error decision; E02 is not required. Category-tag differences do not multiply issue counts.'},
        {'Topic': 'Interpretation', 'Explanation': 'Selected internal sample; one response per model and case. These scenarios do not assess all possible wording disputes or establish general model superiority. The original-independent sensitivity must still accompany these results.'}]
    sheet('Read first', notes).column_dimensions['B'].width = 110
    sheet('Scenario definitions', [{'Scenario': s['label'], 'Basis': s['basis']} for s in scenarios]).column_dimensions['B'].width = 110
    sheet('Error report sensitivity', [summary_row(s) for s in summaries])
    joint_rows, flag_rows = [], []
    for s in summaries:
        j = s['joint']
        joint_rows.append({'Scenario': s['label'], 'Cohort': s['cohort'], 'Model': s['model_identifier'],
                           'Joint successes': j['events'], 'Complete-review denominator': j['evaluable'],
                           'Unknown status': j['unknown'], 'All-planned lower': j['all_planned_bounds'][0],
                           'All-planned upper': j['all_planned_bounds'][1]})
        for flag, f in s['control_flags'].items():
            flag_rows.append({'Scenario': s['label'], 'Model': s['model_identifier'], 'Flag': flag,
                              'Positive': f['events'], 'Evaluable': f['evaluable'], 'Unknown': f['unknown'],
                              'All-planned lower': f['all_planned_bounds'][0], 'All-planned upper': f['all_planned_bounds'][1]})
    sheet('Joint sensitivity', joint_rows)
    sheet('Control annotations', flag_rows)
    sheet('Targeted personal positions', decision_rows)
    sheet('Coverage unchanged', [{'Cohort': s['cohort'], 'Model': s['model_identifier'], 'Mean full coverage': s['coverage_mean']}
                                 for s in summaries if s['scenario'] == 'frozen'])
    w.save(OUT / 'Wording_sensitivity.xlsx')

    gemini = [s for s in summaries if s['cohort'] == 'stroke' and s['model'] == 'gemini']
    md = '# Wording-boundary sensitivity analysis\n\n'
    md += 'This is an exploratory supplement created after the analysis team was unblinded. It preserves the original frozen outcomes and all human reviewers\' individual decisions. No new consensus, ranking or confirmatory test is introduced.\n\n'
    md += '## What changes\n\nThe coverage scores and their previously computed paired intervals are identical in every scenario: the targeted returns change no coverage judgment. Stroke mean full coverage remains Claude 98.2%, GPT 97.0%, Gemini 81.8%. The Claude-GPT contrast still includes zero. This invariance follows from the scope of the review, not an independent validation of coverage scoring.\n\n'
    md += '## Stroke error reports\n\nClaude remains 11/22 evaluable (3 unknown; all-planned bounds 44%-56%). GPT remains 2/25 (0 unknown; bounds 8%-8%). Gemini varies as follows:\n\n'
    md += table(['Scenario', 'Error / evaluable', 'Unknown', 'All-planned bounds', 'Confirmed groups', 'Pending groups'],
                [[s['label'], f"{s['any_error']['events']}/{s['any_error']['evaluable']}", s['any_error']['unknown'],
                  bounds(s['any_error']['all_planned_bounds']), s['confirmed_groups'], s['pending_groups']] for s in gemini])
    md += '\nAcross these scenarios, Gemini has 10-12 confirmed-error stroke reports out of 25 planned slots; counting unknown states as 0/1 gives an overall envelope of 40%-56%. The lowest corresponding Claude bound is 44%, while GPT remains 8%. Thus the descriptive finding of fewer flagged stroke reports for GPT persists within this targeted sensitivity. This is not a confidence-interval comparison, a significance test, or proof of general superiority. Claude versus Gemini does not have a stable error ordering across these choices.\n\n'
    md += 'Two report-level any-error statuses can change under these scenarios. Other changed issue labels leave an existing confirmed error in their report. A report with no remaining confirmed error but another Pending issue stays unknown, not error-free. Detailed report attribution is retained only in the protected analysis directory.\n\n'
    md += '## Controls and pathology annotation\n\nControl any-error results do not change: Claude 6/9 evaluable (1 unknown; bounds 60%-70%), Gemini 8/10 (80%), GPT 0/10. Other confirmed groups remain in each affected control report.\n\n'
    md += 'For the single disputed Gemini pathology annotation, rater1 and rater3 give Yes while rater2 gives No. The corresponding targeted overlays are 1/10, 0/10 and 1/10. A scenario retaining that disagreement as unknown gives 0/9 evaluable, one unknown, and all-planned bounds 0%-10%. Do not report it as a newly unanimous confirmed pathology event or as evidence of no event. Normality annotations remain zero for every model, and the other models\' pathology annotations remain zero. These semantic annotations are not diagnostic false-positive rates.\n\n'
    md += '## How to use this supplement\n\n'
    md += '\n'.join(f"- **{n['Topic']}:** {n['Explanation']}" for n in notes[1:])
    md += '\n\nThe original independent-review sensitivity remains necessary: rater3\'s original error pattern did not reproduce the later Claude-GPT ordering. These targeted scenarios do not resolve that between-stage difference.\n\n'
    md += 'Files: [aggregate workbook](Wording_sensitivity.xlsx), [manuscript wording](MANUSCRIPT_ADDENDUM.md), [provenance record](BUILD_RECORD.json). Per-report scenarios and the identity join remain in `data/rating_packets_formal_v1/private/wording_sensitivity_v1/ANALYSIS.json`, outside reviewer packets.\n'
    (OUT / 'README.md').write_text(md)
    manuscript = '''# Suggested manuscript addendum

## Methods

After model identities had been released to the analysis team, a source audit identified eight wording-sensitive confirmed issue groups for targeted personal review by the three human experts. The review materials omitted model identities, model-comparison results and peer positions. All three reviewers declared no model-identity knowledge or exposure to model-comparison results; their earlier discussion exposure was retained. This follow-up was not a fresh independent rating round. Four issue decisions matched as Error, four remained divergent, and one control pathology annotation remained divergent. One reviewer's logical overstatement about 95% coverage was corrected without changing that reviewer's final decision. No agreement was required.

We retained the original frozen analysis and performed an exploratory sensitivity analysis. For each reviewer, only the eight targeted decisions and the control annotation were substituted into the shared frozen baseline; all other judgments, coverage scores and previously Pending groups remained fixed. These hybrid overlays isolate the targeted changes and are not full independent-rater outcome estimates. Additional analyst-defined scenarios treated the four divergent decisions as Pending, Acceptable or Error and the disputed annotation as unknown, negative or positive, respectively. A report remained error-positive if any confirmed issue remained, and otherwise remained unknown if any issue was Pending. All-planned bounds counted unknown report states as zero or one. Bounds describe unresolved classification, not sampling uncertainty. No new inferential test or shared error-category set was introduced.

## Results

Coverage scores and their original paired contrasts were unchanged because the targeted review did not reassess coverage. Claude retained 11 confirmed-error stroke reports among 22 evaluable reports (three unknown), and GPT retained 2/25 (none unknown). Gemini had 10-12 confirmed-error stroke reports among the 25 planned reports across the scenarios; its overall all-planned uncertainty envelope was 40%-56%. The corresponding bounds remained 44%-56% for Claude and 8% for GPT. Fewer flagged stroke reports for GPT therefore persisted within this targeted sensitivity, whereas the Claude-Gemini error ordering was not stable. These findings do not establish statistical or general model superiority. Control report-level any-error outcomes were unchanged. The single Gemini control pathology annotation was positive for rater1/rater3 and negative for rater2; preserving disagreement as unknown yielded zero known-positive reports, nine evaluable reports and one unknown (all-planned bounds 0%-10%).

## Interpretation

The primary frozen dataset remains a historical outcome layer and should be presented together with these later disagreements. Coverage invariance is a consequence of the review scope. This purposive eight-item analysis cannot establish robustness to every possible rating interpretation or remedy the selected internal sample and single-generation design. Original independent-rating sensitivity must also be reported: the original rater3 error pattern did not reproduce the later Claude-GPT ordering. No pathology claim should be described as unanimous after this follow-up. The semantic control annotations do not estimate diagnostic false-positive rates.
'''
    (OUT / 'MANUSCRIPT_ADDENDUM.md').write_text(manuscript)
    # Refuse a mixed snapshot if a reviewer or another process changed an input.
    for name, digest in sources.items():
        assert sha((ROOT / name).read_bytes()) == digest, f'Input changed during analysis: {name}'
    outputs = [OUT / 'README.md', OUT / 'MANUSCRIPT_ADDENDUM.md', OUT / 'Wording_sensitivity.xlsx', PRIVATE / 'ANALYSIS.json']
    record = {'computed_at_utc': stamp, 'analysis_type': 'Exploratory post-unblinding targeted sensitivity',
              'authorization': 'Study lead requested continuation after receipt of all three final targeted returns.',
              'source_sha256': sources, 'output_sha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in outputs},
              'scenarios': [s['id'] for s in scenarios], 'reports_per_scenario': 105,
              'coverage_recomputed': False, 'original_independent_ratings_replaced': False,
              'frozen_outcomes_modified': False, 'rater_workbooks_modified': False,
              'majority_vote_used': False, 'shared_categories_created': False,
              'baseline_parity': 'All frozen report endpoints and cohort binary summaries exactly reproduced before overlay.'}
    (OUT / 'BUILD_RECORD.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'output': str(OUT), 'stroke_gemini': [summary_row(s) for s in gemini]}, indent=2))


if __name__ == '__main__':
    main()
