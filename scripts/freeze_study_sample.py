"""Record the 25-stroke/10-control decision and one provisional control draw.

Local eligibility is checked; external exposure remains pending. Never generate
model responses, infer expert approval, or redraw into an existing directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import secrets
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / 'docs/formal_study'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def build(out):
    if out.exists():
        raise FileExistsError(f'Refusing to overwrite or redraw: {out}')
    protected = {}
    for name in ['candidate_v3_1', 'rubric_v2_draft', 'sample_eligibility_v1', 'control_supplement_v1_draft']:
        for path in (FORMAL/name).rglob('*'):
            if path.is_file(): protected[str(path.relative_to(ROOT))] = sha(path)
    for name in ['sample_eligibility_v1', 'control_supplement_v1_draft']:
        manifest = json.loads((FORMAL/name/'manifest.json').read_text())
        for filename, expected in manifest['outputs_sha256'].items():
            assert sha(FORMAL/name/filename) == expected, (name, filename)
    ledger = FORMAL/'sample_eligibility_v1'
    all_people = read_csv(ledger/'participant_eligibility.csv')
    people = {r['participant_key']: r for r in all_people}
    pool_path = FORMAL/'control_supplement_v1_draft/control_candidate_pool.csv'
    control_pool = read_csv(pool_path)
    assert len(control_pool) == 98
    stroke = [r for r in all_people if r['candidate_conservative_no_report_or_targeted_audit']=='True']
    assert len(stroke) == 25
    prior_checks = json.loads((ledger/'verification.json').read_text())
    current_sources = {}
    for rel in ['data/raw/AbleBodiedAdults.xlsx','data/raw/PostStrokeAdults.xlsx',
                'audit/outputs/data_quality.csv','audit/outputs/curves.npz','data/pilot_subset.json']:
        current_sources[rel] = sha(ROOT/rel)
        assert current_sources[rel] == prior_checks['current_source_sha256'][rel], rel
    # Check exact report inventory without opening response text or identity keys.
    inventory = json.loads((ledger/'report_file_inventory.json').read_text())
    actual_paths = {str(p.relative_to(ROOT)) for folder in ['data/reports','data/reports_control_spotcheck']
                    for p in (ROOT/folder).glob('*.json')}
    assert actual_paths == {r['source'] for r in inventory}, 'Report inventory changed; review exposure first'
    generated_keys = {r['participant_key'] for r in inventory}
    for r in inventory:
        current_sources[r['source']] = sha(ROOT/r['source'])
        assert current_sources[r['source']] == r['sha256'], r['source']
    curves = np.load(ROOT/'audit/outputs/curves.npz')
    for row in control_pool + stroke:
        key = row['participant_key']; p = people[key]
        assert key not in generated_keys and p['five_case_expert_development']=='False'
        side = 'avg' if p['group']=='control' else 'P'
        for channel in ['GAS','RF','VL','BF','ST','TA','ERS','AnkleAngles','KneeAngles','HipAngles','PelvisAngles']:
            a = curves[f'{key}_{side}_{channel}']
            assert a.size == 1001 and np.isfinite(a).all(), (key, channel)
    keys = sorted(r['participant_key'] for r in control_pool)
    assert len(set(keys))==98
    out.mkdir(parents=True)
    frame = [{**r, 'external_exposure_attestation':'Pending'} for r in sorted(control_pool,key=lambda r:r['participant_key'])]
    write_csv(out/'control_sampling_frame.csv',frame)
    seed = secrets.token_hex(32)
    registration = dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),
        user_confirmed_target=dict(stroke_participants=25,control_participants=10,models=3,
                                   reports_per_case_model=1,planned_reports=105,raters=2,planned_ratings=210),
        authorization_source='Conversation: user agreed after explicit clarification of 10 control participants, 30 control reports, and 105 reports overall.',
        authorization_scope='Sample-size decision, local qualification checks, and provisional random draw; not expert sign-off or model generation.',
        seed_hex=seed, seed_source='One call to secrets.token_hex(32); no seed screening or reroll.',
        algorithm='Sort ascending by SHA-256 of UTF-8(seed_hex + newline + participant_key), breaking ties by participant_key.',
        python_version=platform.python_version(),sampling_frame_sha256=sha(out/'control_sampling_frame.csv'),
        candidate_count=98,control_count=10,external_exposure_status='Pending for all candidates',
        selection_scope='One provisional permutation of the locally eligible pool. First ten are proposed; no final external eligibility is asserted.',
        deviation_from_v1='Register a full permutation before external history is confirmed. After objective history-based exclusions, retain the first ten eligible cases in this same order. Do not redraw.',
        replacement_rule='Record objective ineligibility evidence; promote the first eligible reserve in order. No replacement based on model performance or desired findings.',
        stroke_rule='Use the 25-case conservative planning pool, pending external exposure confirmation. No automatic replacement or relaxation of stroke exclusions.',
        script_sha256=sha(Path(__file__)))
    # Persist the frame, size, seed and rules before computing any random rank.
    write_json(out/'sampling_registration.json',registration)
    rank_hash = lambda key: hashlib.sha256((seed+'\n'+key).encode()).hexdigest()
    order = sorted(keys,key=lambda key:(rank_hash(key),key))
    lookup = {r['participant_key']:r for r in frame}
    ordered = [dict(draw_rank=i,**lookup[key],draw_hash=rank_hash(key),
                    allocation='Provisional selected' if i<=10 else 'Ordered reserve',
                    eligibility_decision='Pending external exposure review',exclusion_reason='')
               for i,key in enumerate(order,1)]
    write_csv(out/'control_sampling_order.csv',ordered)
    selected = []
    for group, selected_keys in [('stroke',sorted(r['participant_key'] for r in stroke)),('control',order[:10])]:
        for key in selected_keys:
            p=people[key]
            selected.append(dict(participant_key=key,group=group,subject=p['subject'],
                side='P' if group=='stroke' else 'avg',role='Main evaluation' if group=='stroke' else 'Exploratory supplement',
                control_draw_rank=order.index(key)+1 if group=='control' else '',
                age_years=float(p['age_years']),published_bilateral_speed_m_s=float(p['published_bilateral_speed_m_s']),
                selection_status='Provisional; external exposure review pending',external_exposure_attestation='Pending',
                case_requirements_status='Not prepared for the new batch',generation_status='Not started',planned_model_reports=3))
    assert len(selected)==35 and len({r['participant_key'] for r in selected})==35
    write_csv(out/'selected_study_cases.csv',selected)
    notes=[dict(topic='Current decision',instruction='User confirmed 25 stroke participants plus 10 healthy controls. Three models, one report per case-model: 105 reports; two raters: 210 rating assignments.'),
           dict(topic='Status',instruction='Random order is registered. Case membership remains provisional until external exposure history is checked. No model reports have been generated.'),
           dict(topic='Priority',instruction='Stroke is the main evaluation; controls are a small exploratory supplement. Report the cohorts separately.'),
           dict(topic='Exposure review',instruction='Save a separate review copy. Record only known prior external use, supporting details, reviewer and date. Pending is not No additional use known.'),
           dict(topic='Reserve order',instruction='If a proposed control is objectively ineligible, document the reason and take the next eligible reserve in order. Never redraw for preferred age, speed or model results.'),
           dict(topic='Metadata',instruction='Age and published speed are administrative metadata, not new model input fields. Controls previously contributed to normative references/calibration.'),
           dict(topic='Next work',instruction='Prepare new-case inputs and expert requirements, then finalize assessment and generation rules. Existing expert approvals do not approve this new batch.')]
    history_rows=[dict(participant_key=r['participant_key'],group=r['group'],external_history='',evidence_or_details='',reviewer='',date='') for r in selected]
    wb=Workbook();wb.remove(wb.active)
    for title, rows in [('Read first',notes),('Selected cases',selected),('Exposure review',history_rows),
                       ('Control draw',ordered[:10]),('Ordered reserves',ordered[10:])]:
        ws=wb.create_sheet(title);ws.append(list(rows[0]))
        for r in rows:ws.append(list(r.values()))
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;ws.row_dimensions[1].height=55
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24476B')
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(65,max(18,max(len(str(c.value or '')) for c in col)+2))
            for c in col:
                c.alignment=Alignment(wrap_text=True,vertical='top')
                if isinstance(c.value,float):c.number_format='0.00'
        if title=='Read first':
            for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=65
    dv=DataValidation(type='list',formula1='"No additional use known,Additional use identified,Unable to confirm"',allow_blank=True)
    dv.showErrorMessage=True;dv.error='Choose a listed history status.'
    wb['Exposure review'].add_data_validation(dv);dv.add('C2:C36')
    wb.save(out/'Study_sample_and_exposure_review.xlsx')
    for rel,expected in protected.items():assert sha(ROOT/rel)==expected,rel
    write_json(out/'selection_record.json',dict(status='User-confirmed counts; provisional membership; generation not started',
        confirmed_stroke_target=25,confirmed_control_target=10,previous_40_control_recommendation='Superseded by user decision',
        selected_control_keys=order[:10],ordered_reserve_keys=order[10:],selected_stroke_keys=sorted(r['participant_key'] for r in stroke),
        external_history_confirmation=None,sampling_registration_sha256=sha(out/'sampling_registration.json'),
        current_source_sha256=current_sources,protected_source_sha256=protected,
        checks=dict(control_frame_count=98,control_draw_count=10,reserve_count=88,stroke_count=25,
                    finite_curves_checked=(98+25)*11,prior_report_files_checked=len(inventory),
                    no_expert_decisions_fabricated=True,no_model_calls=True,no_archived_originals_or_private_keys_read=True)))
    print(json.dumps(dict(controls=order[:10],reserves=88,stroke=25,total_planned_reports=105,status='Provisional membership'),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    build(parser.parse_args().out.resolve())
