"""Prepare an English control-supplement planning workbook; never select or generate cases."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'docs/formal_study/sample_eligibility_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build(out):
    if out.exists():
        raise FileExistsError(f'Output already exists: {out}')
    baseline = {}
    for dirname in ['candidate_v3_1', 'rubric_v2_draft', 'sample_eligibility_v1']:
        for p in (ROOT / 'docs/formal_study' / dirname).rglob('*'):
            if p.is_file():
                baseline[str(p.relative_to(ROOT))] = digest(p)
    manifest = json.loads((LEDGER / 'manifest.json').read_text())
    for name, expected in manifest['outputs_sha256'].items():
        assert digest(LEDGER / name) == expected, name
    participants = list(csv.DictReader((LEDGER / 'participant_eligibility.csv').open()))
    controls = [r for r in participants if r['group'] == 'control'
                and r['technical_complete_primary_side'] == 'True'
                and int(r['prior_pilot_or_spotcheck_report_count']) == 0
                and r['five_case_expert_development'] == 'False']
    assert len(controls) == 98
    assert not {'Sub10', 'Sub49', 'Sub93', 'Sub98'} & {r['subject'] for r in controls}
    pool = [dict(participant_key=r['participant_key'], subject=r['subject'], source_id=r['source_id'],
                 side='avg', age_years=float(r['age_years']),
                 published_bilateral_speed_m_s=float(r['published_bilateral_speed_m_s']),
                 complete_emg_channels=7, complete_sagittal_kinematic_channels=4,
                 previous_reference_and_calibration_use=True,
                 model_input_age_and_speed='Not added; administrative design metadata only',
                 external_exposure_attestation='Pending', formal_selection='Pending') for r in controls]
    z = NormalDist().inv_cdf(0.975)
    options = []
    for n in [10, 15, 20, 25, 30, 40, 50, 98]:
        # Reference calculations assume independent equal-probability Bernoulli outcomes.
        # These are not power calculations or a design-based finite-population analysis.
        half = z * math.sqrt(.25/n + z*z/(4*n*n)) / (1 + z*z/n)
        options.append(dict(control_participants=n, planned_stroke_participants=25,
            control_reports_three_models=3*n, total_reports_three_models=3*(25+n),
            additional_reviews_per_rater=3*n, total_reviews_per_rater=3*(25+n),
            total_reviews_two_raters=6*(25+n),
            extra_hours_per_rater_at_15_min_each=3*n*15/60,
            extra_hours_per_rater_at_30_min_each=3*n*30/60,
            wilson_95_planning_half_width_at_p_0_5_percentage_points=100*half,
            exact_one_sided_95_upper_if_zero_events_percent=100*(1-.05**(1/n)),
            probability_at_least_one_event_if_p_0_10_percent=100*(1-.9**n),
            planning_recommendation=n == 40, final_size_decision='Pending'))
    assert math.ceil(math.log(.05)/math.log(.9)) == 29
    assert options[4]['total_reports_three_models'] == 165
    assert options[4]['additional_reviews_per_rater'] == 90
    assert options[4]['exact_one_sided_95_upper_if_zero_events_percent'] < 10

    decisions = [
        ('D01', 'Study lead and experts', 'Cohort role',
         'Keep the stroke cohort as the main evaluation and controls as a separately reported internal supplementary evaluation.',
         'User agreed to the inclusion principle; final sample, endpoints and analysis remain proposals.'),
        ('D02', 'Experts and study lead', 'Supplementary primary endpoint',
         'Per-model proportion of assessable control reports with at least one confirmed unsupported pathological or normal-function inference.',
         'Use the union of the two semantic categories, deduplicated per report. A rubric error tag alone does not identify this endpoint.'),
        ('D03', 'Experts', 'Semantic endpoint examples',
         'Accept evidence-supported differences and descriptive empirical comparisons; reject unsupported disease/function and normal-physiology conclusions.',
         'Confirm the coding examples in README before output review. Healthy-group membership is not proof that every measurement is normal.'),
        ('D04', 'Study lead', 'Sampling and exposure',
         'Use simple random sampling without replacement from the externally checked candidate pool; fix size and archive seed before sampling.',
         'No output-based selection, no normality-based filtering, no case replacement for difficult findings. Any targeted extreme-case set is separate.'),
        ('D05', 'Study lead and experts', 'Reference and model-input scope',
         'Retain the approved v3.1 input contract; verify self-exclusion from each control reference and label pooled calibration dependence.',
         'These are internal reference-used controls. Do not add age or published speed from this administrative table to model inputs.'),
        ('D06', 'Study lead and both raters', 'Sample size and workload',
         'Consider the recommended 40 controls and document a precision/resource justification using Sample size options.',
         'Forty gives about 14.8-percentage-point maximum Wilson half-width under the stated assumptions. Counts remain pending; record each rater\'s capacity and accepted precision limitation.'),
        ('D07', 'Study lead and analyst', 'Analysis and missing outcomes',
         'Report cohorts separately, preserve participant-level pairing across models and distinguish raters from independent participants.',
         'Finalize confidence intervals, paired comparisons, pending adjudications and technical-failure rules before generation; do not silently count missing as error-free.'),
        ('D08', 'Experts and study lead', 'Case requirements and freeze',
         'Create requirements for selected new controls and stroke cases from frozen model-visible inputs before inspecting generated outputs.',
         'The five-case annex is not a ready-made answer key for new cases. This workbook does not authorize a model batch.')]
    review = [dict(decision_id=i, responsible_role=role, topic=t, proposal=p, scope_note=note,
                   reviewer_decision='', reviewer='', date='', comments='') for i,role,t,p,note in decisions]
    notes = [dict(topic='Status', instruction='Draft design extension. The user accepted the inclusion principle, not a specific sample size or expert endpoint definition.'),
             dict(topic='Recommendation', instruction='Forty controls are proposed for review, targeting approximately 15-percentage-point maximum 95% Wilson half-width. This is not model-comparison power or proof of clinical validity.'),
             dict(topic='Use', instruction='Read README, compare sample-size options, and save a separate review copy. Complete only items within your role. Blank fields are not approvals.'),
             dict(topic='Units', instruction='One subject supplies three paired model reports. Two raters supply repeated assessments, not twice as many subjects.'),
             dict(topic='Workload', instruction='All options assume 25 stroke cases, three models, one saved response per case-model and two raters. Fifteen/thirty minutes are scenarios, not measured rates. Reconciliation and case-card preparation add time.'),
             dict(topic='Precision', instruction='Binomial calculations illustrate one model and one binary endpoint under independent equal-probability observations. They do not justify model comparisons, matched-cohort inference or clinical generalization.'),
             dict(topic='References', instruction='All candidate controls were previously available to normative reference/calibration construction. No independent external validation is claimed.'),
             dict(topic='Selection', instruction='No participants have been drawn. External exposure checks, size and random seed remain pending. The pool is an administrative inventory, not an expert rating packet.')]
    out.mkdir(parents=True)
    write_csv(out/'control_candidate_pool.csv',pool)
    write_csv(out/'sample_size_options.csv',options)
    wb=Workbook();wb.remove(wb.active)
    for title, rows in [('Read first',notes),('Design decisions',review),('Sample size options',options),('Control candidate pool',pool)]:
        ws=wb.create_sheet(title);ws.append(list(rows[0]))
        for row in rows: ws.append(list(row.values()))
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;ws.row_dimensions[1].height=64
        for cell in ws[1]:
            cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='24476B')
        for column in ws.columns:
            ws.column_dimensions[column[0].column_letter].width=min(55,max(18,max(len(str(c.value or '')) for c in column)+2))
            for cell in column:
                cell.alignment=Alignment(wrap_text=True,vertical='top')
                if isinstance(cell.value,float):cell.number_format='0.00'
        if title in ['Read first','Design decisions']:
            for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=105
    ws=wb['Design decisions']
    dv=DataValidation(type='list',formula1='"Agree,Revise,Needs discussion,Outside my role"',allow_blank=True)
    dv.error='Choose a listed decision.';dv.showErrorMessage=True
    ws.add_data_validation(dv);dv.add(f'F2:F{ws.max_row}')
    for row in ws.iter_rows(min_row=2,min_col=6,max_col=9):
        for cell in row:cell.fill=PatternFill('solid',fgColor='E8F1FA')
    wb.save(out/'Control_supplement_design_review.xlsx')
    for p,expected in baseline.items():assert digest(ROOT/p)==expected,p
    record=dict(status='Draft; no sample drawn and no generation performed',
        script_sha256=digest(Path(__file__)),protected_sources_sha256=baseline,
        control_candidate_count=98,recommended_control_count=40,recommendation_status='Agent proposal; not approved sample size',
        proposed_maximum_wilson_half_width=.15,minimum_n_for_proposed_wilson_precision=39,
        final_control_sample_size=None,selected_participants=[],
        precision_assumptions='Independent equal-probability Bernoulli outcomes, one model, one binary report-level endpoint; no finite-population correction or paired-model power claim.',
        references=['https://doi.org/10.1525/collabra.33267',
                    'https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm',
                    'https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm'])
    (out/'design_record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(candidate_controls=98,options=len(options),protected_files_unchanged=len(baseline),outputs=str(out)),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    build(parser.parse_args().out.resolve())
