"""Build prospective sample decision support from local evidence; no model calls.

Does not read blinded identity keys, archive directories, or report narratives.
Refuses to overwrite an existing output directory. No participant is selected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.features.mat_spatiotemporal import load_stroke_spatiotemporal
from src.features.figshare_loader import load_control_excel, load_stroke_excel

MUSCLES = ['GAS', 'RF', 'VL', 'BF', 'ST', 'TA', 'ERS']
JOINTS = ['AnkleAngles', 'KneeAngles', 'HipAngles', 'PelvisAngles']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build(out):
    if out.exists():
        raise FileExistsError(f'Output already exists: {out}')
    sources = {}

    def source(rel):
        path = ROOT / rel
        sources[rel] = sha(path)
        return path

    # Snapshot reviewed materials and historical trial files without opening keys.
    protected = {}
    for folder in ['docs/formal_study/candidate_v3', 'docs/formal_study/candidate_v3_1',
                   'docs/formal_study/rubric_v1_draft', 'docs/formal_study/rubric_v2_draft',
                   'docs/expert_trial/expert_rate/trial_2026-09-17_v1']:
        for path in (ROOT / folder).rglob('*'):
            if path.is_file() and 'private' not in path.parts and 'answer_key' not in path.name.lower():
                protected[str(path.relative_to(ROOT))] = sha(path)

    manifest = read_json(source('audit/sha256_manifest.json'))
    for name in ['data_quality.csv', 'curves.npz', 'event_checks.json', 'metadata.json', 'control_ages.json']:
        path = source('audit/outputs/' + name)
        assert sha(path) == manifest['outputs/' + name], name
    quality = list(csv.DictReader((ROOT / 'audit/outputs/data_quality.csv').open()))
    cache = np.load(ROOT / 'audit/outputs/curves.npz')
    assert len(quality) == len(cache.files) == 2618
    for row in quality:
        a = cache['_'.join(row[k] for k in ['group', 'subject', 'side', 'channel'])]
        assert (a.size, int(np.isnan(a).sum()), int(np.isinf(a).sum())) == tuple(int(row[k]) for k in ['n', 'nan', 'infinite'])

    norm = read_json(source('docs/formal_study/candidate_v3/normalization_verification.json'))
    for rel, expected in norm['source_sha256'].items():
        assert sha(source(rel)) == expected, rel
    source('data/raw/AbleBodiedAdults.xlsx')
    # Compare the previously audited cache directly with current released Excel curves.
    compared = 0
    for group, loader, filename in [('stroke', load_stroke_excel, 'PostStrokeAdults.xlsx'),
                                    ('control', load_control_excel, 'AbleBodiedAdults.xlsx')]:
        for trial in loader(str(ROOT / 'data/raw' / filename)):
            for channel, arr in {**trial.emg_norm, **trial.joint_angles}.items():
                key = f'{group}_{trial.subject_id}_{trial.side}_{channel}'
                assert np.array_equal(arr, cache[key], equal_nan=True), key
                compared += 1
    assert compared == 2618

    supplement = source('audit/sources/VanCriekinge_2023_supplement.txt').read_text()
    speed_section = supplement.split('Supplementary table 5.')[1]
    stroke_speed = re.findall(r'(TVC\d+)\s+([\d.]+)\s+([\d.]+)', speed_section)
    control_speed = {int(s): (float(l)+float(r))/2 for s,l,r in re.findall(r'SUBJ(\d+)\s+([\d.]+)\s+([\d.]+)', speed_section)}
    assert len(stroke_speed) == 50 and len(control_speed) == 138
    ids = {f'Sub{i+1:02d}': row[0] for i,row in enumerate(stroke_speed)}
    metadata = {r['subject']: r for r in read_json(ROOT / 'audit/outputs/metadata.json')}
    ages = read_json(ROOT / 'audit/outputs/control_ages.json')
    clinical = supplement.split('Supplementary Table 2.')[1].split('Supplementary Table 3.')[0]
    pattern = r'(TVC\d+)\s+(\d+)\s+([MF])\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([LR])\s+([IH])\s+(\d+)\s+(\d+)\s+(\d+)'
    records = re.findall(pattern, clinical)
    assert len(records) == 50
    for i, row in enumerate(records):
        sid, age, sex, _, _, _, tps, lesion, _, fac, poma, tis = row
        sub = f'Sub{i+1:02d}'
        assert ids[sub] == sid
        for k,v in dict(Age=float(age), Male=float(sex=='M'), TPS=float(tps), FAC=float(fac),
                        POMA=float(poma), TIS=float(tis), LesionLeft=float(lesion=='L')).items():
            assert metadata[sub][k] == v, (sub,k)

    source('src/features/mat_spatiotemporal.py')
    spatio = load_stroke_spatiotemporal(str(ROOT / 'data/raw/MAT_normalizedData_PostStrokeAdults.mat'))
    spatio_by = {(r['subject_id'], r['side']): r for r in spatio}
    old_spatio = read_json(source('audit/outputs/spatiotemporal_original.json'))
    for r in old_spatio:
        current = spatio_by[(r['subject_id'], r['side'])]
        for k in ['gait_speed_m_s', 'cadence_steps_min', 'step_length_m', 'n_strides']:
            assert np.isclose(current[k], r[k], rtol=0, atol=1e-12)

    stride_rows = list(csv.DictReader(source('audit/outputs/main_dataset_stride_emg_quality.csv').open()))
    stride_by = {(r['subject'],r['side'],r['muscle']): r for r in stride_rows}
    events = read_json(ROOT / 'audit/outputs/event_checks.json')
    event_by = {(r['subject'],r['side']): r for r in events}
    sub43 = {}
    with h5py.File(ROOT / 'data/raw/MAT_normalizedData_PostStrokeAdults.mat') as f:
        for i in range(50):
            sub = f'Sub{i+1:02d}'
            ev = f[f['Sub']['events'][i,0]]
            for side, field in [('P','PsideSegm_PsideData'), ('N','NsideSegm_NsideData')]:
                g = f[f['Sub'][field][i,0]]
                start, stop, cnt = [np.asarray(ev[f'{side}_{k}']).ravel() for k in ['ICstart','ICstop','IC_cnt']]
                bad = (~np.isfinite(start)) | (~np.isfinite(stop)) | (stop <= start)
                assert int(bad.sum()) == event_by[(sub,side)]['invalid_duration']
                for muscle in MUSCLES:
                    x = np.asarray(g[muscle+'norm']['n'])
                    expected = stride_by[(sub,side,muscle)]
                    assert expected['source_id'] == ids[sub]
                    actual = (x.shape[0], int(np.isfinite(x).all(axis=1).sum()),
                              int(((np.isnan(x).sum(axis=1)>0)&(np.isnan(x).sum(axis=1)<x.shape[1])).sum()))
                    assert actual == tuple(int(expected[k]) for k in ['total_strides','valid_strides','partial_nan_strides'])
                if sub == 'Sub43' and side == 'P':
                    assert np.flatnonzero(bad).tolist() == [3]
                    joints = {}
                    for joint in JOINTS:
                        x = np.asarray(g[joint]['x'])
                        assert np.isnan(x[3]).all()
                        mean = np.nanmean(x,axis=0)
                        without = np.nanmean(x[~bad],axis=0)
                        assert np.array_equal(mean,without)
                        error = float(np.max(np.abs(mean-cache[f'stroke_Sub43_P_{joint}'])))
                        assert error < 1e-10
                        joints[joint] = dict(invalid_row_finite_samples=0, mean_change_after_removal=0, maximum_excel_difference=error)
                    sub43 = dict(invalid_zero_based_stride_index=3, ICstart=float(start[3]), ICstop=float(stop[3]),
                                 kinematic_checks=joints, current_spatiotemporal=spatio_by[('Sub43','P')],
                                 conclusion='Known invalid stride is excluded by current spatiotemporal code and is all-NaN in sagittal kinematics; no mean-curve repair required.')

    evidence = []
    def add(key, kind, path, locator, note):
        evidence.append(dict(participant_key=key, exposure_type=kind, source=path, locator=locator, note=note))

    pilot = read_json(source('data/pilot_subset.json'))
    pilot_ids = {r['subject_id'] for r in pilot}
    generated = Counter()
    inventory = []
    for group, folder in [('stroke','data/reports'),('control','data/reports_control_spotcheck')]:
        for path in sorted((ROOT / folder).glob('*.json')):
            match = re.match(r'(Sub\d+)(?:_P)?__', path.name)
            assert match, path
            key = f'{group}_{match[1]}'
            generated[key] += 1
            rel = str(path.relative_to(ROOT))
            source(rel)
            inventory.append(dict(participant_key=key, source=rel, sha256=sources[rel]))
        for key in sorted(k for k in generated if k.startswith(group+'_')):
            add(key, 'prior_report_generation', folder, f'{generated[key]} report JSON files',
                'Generation evidence; does not assert that every report was read by a human.')
    assert sum(generated.values()) == 66 and len(generated) == 22
    assert {k.removeprefix('stroke_') for k in generated if k.startswith('stroke_')} == pilot_ids
    for sub in sorted(pilot_ids):
        add('stroke_'+sub,'pilot_selection','data/pilot_subset.json',sub,'Exposure applies to the participant, including the other side.')

    trial_root = 'docs/expert_trial/expert_rate/trial_2026-09-17_v1/frozen/cases'
    trial_keys = set()
    for path in sorted((ROOT / trial_root).iterdir()):
        if not path.is_dir():
            continue
        key = path.name.rsplit('_',1)[0]
        trial_keys.add(key)
        add(key,'expert_trial_case',trial_root,path.name,'Previously used in the five-case expert trial and prospective rule development.')
    assert trial_keys == {'stroke_Sub09','stroke_Sub05','stroke_Sub50','stroke_Sub47','control_Sub49'}

    targeted = {'Sub03': 'step-length definition sensitivity', 'Sub45': 'step-length definition sensitivity and missing EMG',
                'Sub08': 'missing EMG', 'Sub37': 'partial EMG', 'Sub41': 'documented hands-on assistance',
                'Sub43': 'invalid event, absent EMG and assistance', 'Sub46': 'partial EMG and assistance',
                'Sub47': 'absent EMG', 'Sub48': 'absent EMG'}
    method_doc = 'audit/PROJECT_AUDIT_2026-09-16.md'
    quality_doc = 'audit/MAIN_DATASET_SUITABILITY_2026-09-16.md'
    source(method_doc); source(quality_doc)
    source('audit/review5/packaging_probes.py')
    source('reference/tamaya, 2023.pdf')
    source('data/normative_calibration_v2.json')
    source('audit/outputs/all_summaries.json')
    for sub, why in targeted.items():
        path = method_doc if sub in ['Sub03','Sub45'] else quality_doc
        assert sub in (ROOT / path).read_text()
        add('stroke_'+sub,'targeted_method_or_quality_audit',path,sub,why)

    by_side = defaultdict(list)
    for r in quality:
        by_side[(r['group'],r['subject'],r['side'])].append(r)
    side_rows = []
    for (group,sub,side), rows in sorted(by_side.items()):
        valid = lambda kind: sorted(r['channel'] for r in rows if r['kind']==kind and int(r['n'])==1001 and int(r['nan'])==0 and int(r['infinite'])==0)
        emg,kin = valid('emg'),valid('kinematic')
        st = spatio_by.get((sub,side),{}) if group=='stroke' else {}
        strides = [int(stride_by[(sub,side,m)]['valid_strides']) for m in emg] if group=='stroke' else []
        side_rows.append(dict(participant_key=f'{group}_{sub}',group=group,subject=sub,side=side,
            complete_emg_channels=len(emg),complete_kinematic_channels=len(kin),missing_emg_channels=';'.join(sorted(set(MUSCLES)-set(emg))),
            minimum_valid_emg_strides=min(strides) if strides else '',
            gait_speed_m_s=st.get('gait_speed_m_s',''),valid_spatiotemporal_strides=st.get('n_strides',''),
            source_invalid_duration_strides=event_by[(sub,side)]['invalid_duration'] if group=='stroke' else '',
            technical_complete=len(emg)==7 and len(kin)==4 and (st.get('n_strides',0)>0 if group=='stroke' else True),
            prior_report_exposure_at_participant_level=bool(generated[f'{group}_{sub}'])))
    sides = {(r['participant_key'],r['side']):r for r in side_rows}
    participants = []
    for group, number, side in [('stroke',50,'P'),('control',138,'avg')]:
        for i in range(1,number+1):
            sub=f'Sub{i:02d}'; key=f'{group}_{sub}'; current=sides[(key,side)]
            audit = group=='stroke' and sub in targeted
            report = generated[key]>0
            full = current['technical_complete']
            assistance = group=='stroke' and ids[sub] in ['TVC48','TVC51','TVC54']
            if report: status='development_report_case'
            elif not full: status='incomplete_EMG_challenge_candidate'
            elif audit: status='targeted_audit_case_no_report_found'
            elif group=='control': status='reference_used_control_no_report_found'
            else: status='potential_new_report_case_external_history_unconfirmed'
            participants.append(dict(participant_key=key,group=group,subject=sub,
                source_id=ids[sub] if group=='stroke' else f'SUBJ{i}',
                proposed_analysis_side=side,age_years=metadata[sub]['Age'] if group=='stroke' else ages[str(i)],
                primary_emg_channels=current['complete_emg_channels'],primary_kinematic_channels=current['complete_kinematic_channels'],
                other_side_emg_channels=sides[(key,'N')]['complete_emg_channels'] if group=='stroke' else '',
                primary_minimum_valid_emg_strides=current['minimum_valid_emg_strides'],
                primary_gait_speed_m_s=current['gait_speed_m_s'],
                published_bilateral_speed_m_s=(float(stroke_speed[i-1][1])+float(stroke_speed[i-1][2]))/2 if group=='stroke' else control_speed[i],
                documented_hands_on_assistance='yes' if assistance else ('not_among_three_documented_cases' if group=='stroke' else 'not_evaluated'),
                prior_pilot_or_spotcheck_report_count=generated[key],five_case_expert_development=key in trial_keys,
                targeted_method_or_quality_audit=audit,cohort_feature_processing=True,
                normative_reference_and_calibration_use=group=='control',technical_complete_primary_side=full,
                candidate_complete_no_prior_report=group=='stroke' and full and not report,
                candidate_conservative_no_report_or_targeted_audit=group=='stroke' and full and not report and not audit and not assistance,
                provisional_status=status,external_exposure_attestation='pending',formal_selection='pending'))
            add(key,'cohort_feature_processing','audit/outputs/all_summaries.json',sub,'Mechanical cohort processing; not evidence of individual human report review.')
            if group=='control':
                add(key,'normative_reference_and_calibration_use','data/normative_calibration_v2.json','healthy cohort',
                    'Contributed where channels were available. Own-reference LOO does not remove prior cohort calibration use.')
    assert len(participants)==188 and len(side_rows)==238
    assert len({r['participant_key'] for r in participants})==188
    assert sum(r['candidate_complete_no_prior_report'] for r in participants)==27
    assert sum(r['candidate_conservative_no_report_or_targeted_audit'] for r in participants)==25
    assert all(s['prior_report_exposure_at_participant_level'] for s in side_rows if s['participant_key']=='stroke_Sub05')
    assert not next(r for r in participants if r['participant_key']=='stroke_Sub49')['five_case_expert_development']
    assert next(r for r in participants if r['participant_key']=='control_Sub49')['five_case_expert_development']

    decisions = [
        ('D01','Exposure rule','Use the 25-case conservative stroke pool for planning; keep 27 as an explicitly broader alternative.','Exclude report-development participants across both sides. The 25-case option additionally excludes individually audited Sub03 and Sub41. Neither count is a final sample size.'),
        ('D02','External exposure history','Study lead checks terminal work, external conversations and any unregistered reports.','Absence of a local record cannot certify no prior exposure. Mark each selected participant only after this check.'),
        ('D03','Side and missing-data policy','Primary stroke assessment uses P-side complete EMG and sagittal kinematics; incomplete cases form a separate optional challenge set.','Do not count P and N as independent participants. Record effective stride counts; no new minimum-stride cutoff is imposed here.'),
        ('D04','Assistance policy','Keep the three documented hands-on-assisted cases outside an unassisted primary pool.','Sub41, Sub43 and Sub46. This is human assistance, not a documented device-use label. Other cases are not automatically proven fully independent.'),
        ('D05','Healthy-control role','Treat current healthy controls as internal reference-used challenge cases, unless a separate reference/evaluation design is adopted.','102 have complete EMG, including 4 report-exposed cases. The remaining 98 are not an independent untouched reference-validation cohort. LOO alone does not undo prior calibration use.'),
        ('D06','Final sample and analysis','Choose target population, sample size/strata, outcomes and uncertainty analysis before selecting final participants.','The 25-case planning pool is not an approved sample, statistical power calculation or batch size. No weights or technical-failure exclusions are set.'),
        ('D07','New-case requirements and generation','Prepare and approve requirements for selected new cases before generating their reports.','The approved five-case annex does not supply requirements for new cases. Freeze prompt, inputs, rubric, failure/retry rules and rating forms before the batch.')]

    stats = dict(participants=188,side_records=238,verified_current_excel_curves=compared,
        stroke_primary_emg_distribution=dict(Counter(r['primary_emg_channels'] for r in participants if r['group']=='stroke')),
        control_emg_distribution=dict(Counter(r['primary_emg_channels'] for r in participants if r['group']=='control')),
        stroke_both_sides_complete=sum(r['primary_emg_channels']==7 and r['other_side_emg_channels']==7 for r in participants if r['group']=='stroke'),
        previous_report_participants=22,previous_pilot_or_spotcheck_reports=66,stroke_report_participants=18,control_report_participants=4,
        complete_stroke_no_prior_report_pool=27,conservative_stroke_planning_pool=25,
        conservative_stroke_ids=[r['subject'] for r in participants if r['candidate_conservative_no_report_or_targeted_audit']],
        complete_controls_no_report_found=98,formal_selected_participants=0,
        stroke_below_published_control_speed_min=sum(r['published_bilateral_speed_m_s']<min(control_speed.values()) for r in participants if r['group']=='stroke'))
    assert sum(r['primary_emg_channels']==7 and not r['prior_pilot_or_spotcheck_report_count'] for r in participants if r['group']=='control')==98
    assert all(sha(ROOT / rel)==h for rel,h in protected.items()), 'Protected evidence changed during build'
    out.mkdir(parents=True)
    write_csv(out/'participant_eligibility.csv',participants)
    write_csv(out/'side_data_quality.csv',side_rows)
    write_csv(out/'exposure_evidence.csv',evidence)
    write_json(out/'sub43_verification.json',sub43)
    write_json(out/'summary.json',stats)
    write_json(out/'report_file_inventory.json',inventory)
    workbook=Workbook();workbook.remove(workbook.active)
    sheets = [('Read first',[{'topic':'Status','instruction':'Draft decision support. No final sample selection or report-generation approval.'},
        {'topic':'Participant identity','instruction':'Always use group plus subject. Exposure applies to both sides of a stroke participant.'},
        {'topic':'Evidence scope','instruction':'Local report inventories and selected audit evidence. External history is unconfirmed. No private identity keys or report narratives were read.'},
        {'topic':'Technical completeness','instruction':'Seven finite 1001-point EMG means, four finite sagittal kinematic means; stroke also requires valid current spatiotemporal strides. Not clinical validity.'},
        {'topic':'Workbook use','instruction':'Filter Participants; fill Decision record and per-participant external exposure status in a separately saved review copy. Keep CSV and original workbook unchanged.'}]),
        ('Decision record',[dict(decision_id=i,topic=t,proposed_rule=p,reason=n,study_lead_decision='',reviewer='',date='',comment='') for i,t,p,n in decisions]),
        ('Participants',participants),('Side quality',side_rows),('Exposure evidence',evidence)]
    for title,rows in sheets:
        ws=workbook.create_sheet(title);ws.append(list(rows[0]))
        for row in rows: ws.append(list(row.values()))
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.font=Font(color='FFFFFF',bold=True);cell.fill=PatternFill('solid',fgColor='24476B')
        for column in ws.columns:
            letter=column[0].column_letter
            ws.column_dimensions[letter].width=min(64,max(18,max(len(str(c.value or '')) for c in column)+2))
            for cell in column:cell.alignment=Alignment(vertical='top',wrap_text=True)
        if title in ['Read first','Decision record']:
            for row in range(2,ws.max_row+1):ws.row_dimensions[row].height=85
    workbook.save(out/'Sample_eligibility_and_decisions.xlsx')
    source('scripts/build_sample_eligibility_ledger.py')
    write_json(out/'verification.json',dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),
        current_source_sha256=sources,source_hash_note='Hashes identify current working evidence. Historical original-language hashes remain in existing conversion provenance records.',
        checks=dict(audit_cache_hashes=True,all_current_excel_curves_equal_cache=True,stroke_source_hashes_equal_normalization_audit=True,
                    all_700_stroke_muscle_side_stride_counts_recomputed=True,all_100_current_spatiotemporal_records_equal_prior=True,
                    all_50_clinical_id_mappings_crosschecked=True,group_identity_and_side_exposure_checks=True,
                    protected_files_unchanged=len(protected),no_private_identity_keys_read=True,no_model_calls=True),
        protected_current_file_sha256=protected))
    print(json.dumps(stats,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    build(args.out.resolve())
