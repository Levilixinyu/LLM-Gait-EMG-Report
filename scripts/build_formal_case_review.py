"""Prepare the provisional 35-case expert requirements package, without model calls.

Reuses the approved numerical and prompt routes. Candidate requirements are derived
only from displayed input text; they are not an expert-approved scoring standard.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import re
import shutil
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import build_expert_trial_package as cards
from src.llm import candidate_prompts
from src.features.pipeline import extract_summary_from_normalized
from src.features.emg_provenance import CANDIDATE_PROMPT_VERSION

VERSION='formal-case-requirements-v1-draft'
SELECTION=ROOT/'docs/formal_study/control_supplement_v2'
BASELINE=ROOT/'docs/expert_trial/data_cards_v7_candidate'


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def candidate_items(user,group):
    """Select review prompts from rounded model-visible values, not hidden precision."""
    rows=[]
    def add(code,text,evidence,components,basis):
        assert all(line in user for line in evidence)
        rows.append(dict(item_id=code,category='must_describe_candidate',draft_statement=text,
            evidence='\n'.join(evidence),proposed_components=components,selection_basis=basis,
            expert_decision='PENDING',expert_edit='',expert_id='',review_date=''))
    lines=user.splitlines()
    speed=next(x for x in lines if x.startswith('Gait speed:'))
    gps=next(x for x in lines if x.startswith('Composite kinematic deviation score'))
    if group=='stroke':
        value=float(re.search(r'Gait speed: ([\d.]+)',speed)[1])
        relation=('below the stated 0.80 m/s reference floor; no reference at this speed is supplied'
                  if value<.8 else 'within the stated reference speed range; this does not establish individual matching'
                  if value<=1.79 else 'above the stated 1.79 m/s reference ceiling; individual matching is not established')
        add('N01',f'Draft core: describe walking speed {value:.2f} m/s and that it is {relation}.',
            [speed],'Displayed speed AND relation to reference speed support. Disease-attribution limits remain under common G03.',
            'Case-specific speed; comparison uses displayed precision. Retain, modify or omit based on expert judgment.')
    else:
        value=gps.split(':',1)[1].strip()
        add('N01',f'Draft core: describe the GPS-like value {value} as a composite difference from the reference. It does not classify overall gait as normal or abnormal.',
            [gps],'Displayed composite finding; no required claim of clinical normality. Decide whether this adds essential content beyond N02.',
            'Control input supplies no individual walking speed. This proposal can be omitted if redundant with joint findings.')
    joints=[]
    for line in lines:
        m=re.match(r'- (\w+Angles): range of motion ([\d.]+) deg, Gait Variable Score ([\d.]+)',line)
        if m:joints.append(dict(joint=m[1],gvs=float(m[3]),line=line))
    assert len(joints)==4
    ranked=sorted(joints,key=lambda r:(-r['gvs'],r['joint']))
    cutoff=ranked[1]['gvs']; chosen=[r for r in ranked if r['gvs']>=cutoff]
    label='; '.join(f"{cards.JOINT_NAMES[r['joint']]} GVS {r['gvs']:.2f} degrees" for r in chosen)
    add('N02',f'Draft core: identify these leading displayed joint-curve differences: {label}. Choose which joints actually deserve emphasis; ranking is not clinical severity.',
        [r['line'] for r in chosen],'Named joint findings selected by the expert. No unseen waveform direction or phase is required.',
        'Two largest displayed GVS values, including ties at the cutoff; not an automatic importance rule.')
    muscles=[]
    for line in lines:
        m=re.match(r'- (GAS|RF|VL|BF|ST|TA|ERS): .*max \|z\| vs healthy reference: ([\d.]+) \((above|below) reference, at ([\d.]+)% of cycle\)',line)
        if m:
            coverage=float(re.search(r'([\d.]+)% of cycle above threshold',line)[1])
            muscles.append(dict(muscle=m[1],z=float(m[2]),direction=m[3],phase=m[4],coverage=coverage,line=line))
    assert len(muscles)==7
    # Exact rankings among hidden unrounded values must not become requirements.
    ranked_m=sorted(muscles,key=lambda r:(-r['z'],r['muscle']))
    for code,m in zip(['N03','N04'],ranked_m[:2]):
        name=cards.MUSCLE_NAMES[m['muscle']]
        add(code,f"Draft core: describe {name} ({m['muscle']}) as {m['direction']} the phase-specific reference mean at about {m['phase']}% of the analysis cycle, with displayed max |z| {m['z']:.1f}. Decide whether it merits inclusion or replace it with a more relevant input-supported finding.",
            [m['line']],'Muscle AND mean-relative direction AND approximate cycle location; magnitude provides descriptive context, not a diagnostic threshold.',
            'One of two largest displayed max-|z| values; alphabetical tie-break only selects a review candidate. No uniqueness or exact rank is required.')
    m=sorted(muscles,key=lambda r:(-r['coverage'],r['muscle']))[0]
    add('N05',f"Optional candidate for a core finding: {cards.MUSCLE_NAMES[m['muscle']]} ({m['muscle']}) has {m['coverage']:.0f}% displayed above-threshold coverage. Select this only if the envelope-extent finding adds useful case-specific content; otherwise omit it. Use the retained intervals in the input if helpful.",
        [m['line']],'If retained, describe measured above-threshold extent. Do not equate rounded coverage with continuous physiological activation or absence of brief threshold gaps.',
        'Largest displayed coverage, alphabetical tie-break. Optional candidate; the 100% display alone is not a pathological or physiological duration claim.')
    if group=='stroke':
        line=next(x for x in lines if x.startswith('Step length symmetry index:'))
        value=float(re.search(r'index: ([-\d.]+)%',line)[1])
        meaning='the paretic step is shorter' if value<0 else 'the paretic step is longer' if value>0 else 'the displayed index rounds to zero; direction is not resolved at this precision'
        add('N06',f'Draft core: describe the supplied successive-footfall step-length index {value:.1f}% and its meaning: {meaning}. Do not infer overall gait symmetry from this index.',
            [line],'Displayed index AND supported direction/rounded-zero meaning. A separate whole-gait disclaimer is not automatically required if no generalization is made.',
            'Step-length finding available to the model; not a validated severity category.')
    return rows


def page(title,body):
    css=(ROOT/'src/eval/assets/card_review.css').read_text()
    js=(ROOT/'src/eval/assets/card_review.js').read_text().replace('five-case overview','35-case overview')
    toolbar='''<aside class="review-toolbar"><strong>New-case requirements review</strong><div class="review-identity"><label>Reviewer ID<input id="reviewer-id" autocomplete="off" maxlength="100"></label><label>Date<input type="date" id="review-date"></label><button id="review-start">Start / load review</button></div><p id="review-progress"></p><div class="review-actions"><button id="export-review-json">Export review JSON</button><button id="export-review-csv">Export CSV</button><label>Resume from JSON<input type="file" accept=".json,application/json" id="review-import"></label></div><p id="review-status" role="status">Enter your reviewer ID to start. Export and return the JSON when finished. Nothing is submitted automatically.</p></aside>'''
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{max-width:1150px;margin:30px auto;padding:0 22px;font:16px/1.65 system-ui;color:#233444;background:#f8fafb}section{padding:24px;background:white;border:1px solid #dbe4e8;margin:25px 0}img{max-width:100%;height:auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #dbe4e8;padding:8px;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f6;padding:14px;font-size:13px}.badge{background:#fff1cc;padding:10px}summary{cursor:pointer;font-weight:600}details{margin:12px 0}h1,h2{color:#173f54}</style><style>'+css+'</style></head><body>'+toolbar+body+'<script>'+js+'</script></body></html>'


def references(summary,counts):
    method=summary.reference_meta
    lines=[f'# Reference context: {summary.group}/{summary.subject_id}', '',
        f"Mean/SD reference: {method['n_subjects']} controls; method {method['method']}; exclusions: {method['excluded_subjects']}.",
        '', 'Effective reference counts: '+', '.join(f'{k}={v}' for k,v in counts.items())+'.', '',
        'The exact system and user input files define what the model receives. The EMG and kinematic plots are supplementary expert evidence, not model inputs.',
        'The plotted mean plus/minus one SD is descriptive, not a clinical normal band. Negative lower EMG bands can result from mean minus SD; they do not imply negative recorded EMG.',
        'The max-|z| p95 span in the input is pooled calibration context. Complete muscle-specific LOO thresholds are not supplied; an appropriately indeterminate classification is allowed.',
        'Controls are excluded from their own mean/SD reference, but cohort-level calibration has prior reference-data reuse. It is not an independent matched clinical limit.',
        'GPS-like is a four-channel sagittal composite, not the validated nine-variable GPS. The pooled median/p95 background is not a matched LOO normality boundary.',
        'CCI uses continuous normalized envelopes over the whole analysis cycle. An empirical interval comparison does not establish normal muscle function.',
        'Threshold intervals and rounded coverage describe the averaged envelope. Rounded 100% coverage and one interval do not prove absence of short below-threshold gaps.',
        'Use the group-specific cycle and normalization provenance in the actual input. No individual intermediate gait events or matched normal muscle timing are supplied.',
        'Administrative age and published bilateral speed are not added to this input. Expert-visible plots do not justify requiring unseen direction, phase or morphology.',
        '', 'For a new-case requirement, cite exact input evidence. Select clinically useful descriptive content without inferring a diagnosis or severity from rank alone.']
    return '\n'.join(lines)+'\n'


def build(out):
    if out.exists():raise FileExistsError('Existing expert materials must not be overwritten.')
    protected={}
    for folder in ['candidate_v3_1','rubric_v2_draft','control_supplement_v2']:
        for p in (ROOT/'docs/formal_study'/folder).rglob('*'):
            if p.is_file():protected[str(p.relative_to(ROOT))]=cards.digest(p)
    selection_manifest=json.loads((SELECTION/'manifest.json').read_text())
    for f,h in selection_manifest['outputs_sha256'].items():assert cards.digest(SELECTION/f)==h,f
    selected=list(csv.DictReader((SELECTION/'selected_study_cases.csv').open()))
    assert len(selected)==35 and sum(r['group']=='stroke' for r in selected)==25
    report_inventory=json.loads((ROOT/'docs/formal_study/sample_eligibility_v1/report_file_inventory.json').read_text())
    paths={str(p.relative_to(ROOT)) for folder in ['data/reports','data/reports_control_spotcheck'] for p in (ROOT/folder).glob('*.json')}
    assert paths=={r['source'] for r in report_inventory}
    for r in report_inventory:assert cards.digest(ROOT/r['source'])==r['sha256']
    assert not {r['participant_key'] for r in selected}&{r['participant_key'] for r in report_inventory}
    baseline=json.loads((BASELINE/'manifest.json').read_text())
    for f,h in baseline['code_sha256'].items():assert cards.digest(ROOT/f)==h,f
    assert cards.digest(ROOT/'data/normative_calibration_v2.json')==baseline['calibration_sha256']
    trials,st,sources=cards.load_inputs(ROOT,True)
    controls=[t for t in trials if t.group=='control'];assert len(controls)==138
    lookup={(t.group,t.subject_id,t.side):t for t in trials}
    # Regression against the five approved snapshots; never regenerate historical reports.
    golden=[]
    for group,sid,side in cards.CASES:
        t=lookup[(group,sid,side)];_,norm=cards.reference_for(t,controls)
        s=extract_summary_from_normalized(t,norm,**(st[(sid,side)] if group=='stroke' else {}))
        d=BASELINE/f'{group}_{sid}_{side}'
        assert candidate_prompts.SYSTEM_PROMPT==(d/'model_system_prompt.txt').read_text()
        assert candidate_prompts.build_user_prompt(s)==(d/'model_user_prompt.txt').read_text()
        golden.append(f'{group}_{sid}_{side}')
    out.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='formal-cards-building-',dir=out.parent))
    manifest=dict(version=VERSION,created_at_utc=datetime.now(timezone.utc).isoformat(),
        status='Draft requirements for provisional selected cases; no expert approval and no generation authorization',
        selection_source_sha256=cards.digest(SELECTION/'selected_study_cases.csv'),
        prompt_version=CANDIDATE_PROMPT_VERSION,model_calls=0,expert_approved=False,
        external_exposure_confirmation='Pending; user agreement to proceed is not an attestation',
        sources=sources,calibration_sha256=baseline['calibration_sha256'],
        approved_prompt_source_hashes=baseline['code_sha256'],
        builder_sha256=cards.digest(Path(__file__)),protected_files_sha256=protected,
        approved_five_case_inputs_reproduced=golden,cases=[])
    common='<section id="common_rules"><h2>Read once: existing rules and this review</h2><p>Interpretation instructions v3.1 and rubric v2 have already been approved. This review selects essential findings for new cases; it does not reopen the shared rules.</p><p>Read the actual model input before choosing requirements. Plots are additional expert evidence: do not require unseen waveform details, hidden reference values, or administrative metadata. Mean-relative direction, empirical percentile comparison and clinical normality are different claims. Appropriate uncertainty is allowed.</p><p>G03 remains one common requirement per reference-bearing report: limited comparability plus the limit on disease/normality inference. Do not repeat it as a new item in every case. Coverage and errors remain separate. Optional CCI/cadence claims can still be wrong even when not required.</p><p>Retain, modify or omit each candidate. Numerical ranking proposes review priorities; it is not a validated importance rule. Add another input-supported finding if needed. Do not add a requirement only because a model later omitted it.</p><p>Use this interactive page or the companion Excel workbook, not two conflicting copies. Each expert works independently. Export JSON to preserve and return browser edits; browser storage is not a submission.</p><p class="badge">These 35 memberships are provisional pending external exposure review. No generated model reports are included.</p></section>'
    sections=[];toc=[];all_rows=[];case_rows=[]
    for entry in selected:
        group,sid,side=entry['group'],entry['subject'],entry['side'];case=f'{group}_{sid}_{side}'
        trial=lookup[(group,sid,side)];members,norm=cards.reference_for(trial,controls)
        assert len(members)==(137 if group=='control' else 138)
        if group=='control':assert sid not in {m.subject_id for m in members}
        summary=extract_summary_from_normalized(trial,norm,**(st[(sid,side)] if group=='stroke' else {}))
        user=candidate_prompts.build_user_prompt(summary);system=candidate_prompts.SYSTEM_PROMPT
        assert len(summary.muscle_findings)==7 and not summary.missing_emg_channels
        if group=='control':
            assert summary.gait_speed_m_s is None and 'Gait speed: not provided' in user
            assert 'Step length symmetry index: not applicable' in user
        # Independent finite-curve mean/SD checks, not just metadata checks.
        checks={}
        for muscle in cards.EMG_MUSCLES:
            a=np.stack([m.emg_norm[muscle] for m in members if np.isfinite(m.emg_norm[muscle]).all()])
            np.testing.assert_allclose(norm['emg'][muscle][0],a.mean(0),rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(norm['emg'][muscle][1],a.std(0),rtol=1e-12,atol=1e-12)
            checks[muscle]=len(a)
        for joint in cards.KINEMATIC_JOINTS:
            a=np.stack([m.joint_angles[joint] for m in members])
            np.testing.assert_allclose(norm['joint_angles'][joint],a.mean(0),rtol=1e-12,atol=1e-12)
        d=stage/case;d.mkdir()
        (d/'model_system_prompt.txt').write_text(system);(d/'model_user_prompt.txt').write_text(user)
        cards.write_json(d/'model_messages.json',[{'role':'system','content':system},{'role':'user','content':user}])
        cards.write_json(d/'summary.json',asdict(summary))
        items=candidate_items(user,group);cards.write_json(d/'candidate_requirements.json',items)
        for i in items:
            all_rows.append(dict(case_id=case,item_id=i['item_id'],draft_core=i['draft_statement'],
                proposed_components=i['proposed_components'],exact_input_evidence=i['evidence'],
                selection_basis=i['selection_basis'],reviewer_decision='',revised_required_wording='',comments='',reviewer='',date=''))
        counts=cards.plots(d,trial,members,summary)
        assert all(counts[m]==n for m,n in checks.items())
        ref=references(summary,counts);(d/'reference_card.md').write_text(ref)
        version=hashlib.sha256(json.dumps([VERSION,system,user,items,ref],sort_keys=True).encode()).hexdigest()
        header=f'<h2 id="{case}">{html.escape(case)}</h2><p class="badge">Draft case requirements; participant eligibility remains provisional</p>'
        body=header+'<details open><summary>Actual model input: read before selecting required findings</summary><pre>'+html.escape(user)+'</pre><details><summary>System instructions</summary><pre>'+html.escape(system)+'</pre></details></details>'
        body+='<details><summary>Supplementary curves and reference context (not model inputs)</summary>'
        for kind in ['emg','kinematics']:
            body+=f'<img loading="lazy" alt="{case} {kind} curves" src="{case}/curves_{kind}.png">'
        body+='<pre>'+html.escape(ref)+'</pre></details>'
        body+=cards.review_block(case,'Choose the essential findings for this case',items,version)
        standalone=body
        for kind in ['emg','kinematics']:
            uri='data:image/png;base64,'+base64.b64encode((d/f'curves_{kind}.png').read_bytes()).decode()
            standalone=standalone.replace(f'{case}/curves_{kind}.png',uri)
        (d/'card.html').write_text(page(case,common+standalone))
        sections.append('<section>'+body+'</section>');toc.append(f'<li><a href="#{case}">{case}</a></li>')
        record=dict(case_id=case,group=group,subject_id=sid,side=side,review_version=version,
                    n_candidate_items=len(items),reference_meta=summary.reference_meta,
                    reference_members=[m.subject_id for m in members],effective_reference_n=counts,
                    files_sha256={p.name:cards.digest(p) for p in sorted(d.iterdir())})
        manifest['cases'].append(record)
        case_rows.append(dict(case_id=case,group=group,side=side,candidate_items=len(items),
            card=f'{case}/card.html',input=f'{case}/model_user_prompt.txt',reference_participants=len(members),
            exposure_status='Pending external confirmation',expert_requirements_status='Pending'))
        print('Prepared',case,flush=True)
    intro='<h1>35-case expert requirements review</h1><p>25 stroke cases and 10 healthy controls. This package contains input snapshots and candidate requirements, not model reports.</p><p><a href="Expert_case_requirements_review.xlsx">Alternative Excel review workbook</a> | <a href="REVIEW_GUIDE.md">Review instructions</a></p><details><summary>Case navigation</summary><ol>'+''.join(toc)+'</ol></details>'
    (stage/'index.html').write_text(page('35-case expert requirements review',intro+common+''.join(sections)))
    write_csv(stage/'candidate_requirements.csv',all_rows);write_csv(stage/'case_index.csv',case_rows)
    wb=Workbook();wb.remove(wb.active)
    instructions=[dict(topic='Scope',instruction='Review new-case requirements only. Existing shared rules remain approved. Participant exposure review remains pending.'),
        dict(topic='Workflow',instruction='Open each case card, inspect the actual model input and optional plots, then Retain, Modify or Omit each candidate. Add findings only when the input supports them.'),
        dict(topic='Meaning of Retain',instruction='The stated core and its components become your proposed requirement for this case. Numerical rank alone is not a reason to require a finding. Expert consensus is established separately.'),
        dict(topic='Modify',instruction='Write complete replacement wording, including which findings are AND requirements or alternative OR routes. Clarify any partial-coverage boundary in Comments.'),
        dict(topic='Omit',instruction='This is not required content. It can remain an allowed optional observation and can still be evaluated for factual correctness if stated.'),
        dict(topic='Common rules',instruction='Apply approved G03 once per report. Do not duplicate it as an additional case deduction. No unapproved severity weights or partial-credit scores are introduced.'),
        dict(topic='Return',instruction='Save a reviewer-specific copy. Fill reviewer and date, make all decisions, add any missing essential findings, and leave the other reviewer independent. Use Excel OR browser JSON as the authoritative return.'),
        dict(topic='No signature inference',instruction='Blank fields and the machine draft are not expert approvals. This workbook is not a report-scoring sheet or a batch authorization.')]
    additions=[dict(case_id=r['case_id'],new_required_finding='',exact_input_evidence='',components_or_alternatives='',reason='',reviewer='',date='') for r in case_rows]
    for title,rows in [('Read first',instructions),('Cases',case_rows),('Requirements',all_rows),('Additional findings',additions)]:
        ws=wb.create_sheet(title);ws.append(list(rows[0]));ws.freeze_panes='A2'
        for row in rows:ws.append(list(row.values()))
        ws.auto_filter.ref=ws.dimensions;ws.row_dimensions[1].height=48
        for cell in ws[1]:cell.font=Font(color='FFFFFF',bold=True);cell.fill=PatternFill('solid',fgColor='24476B')
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(70,max(18,max(len(str(c.value or '')) for c in col)+2))
            for c in col:c.alignment=Alignment(wrap_text=True,vertical='top')
        if title in ['Read first','Requirements']:
            for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=115
    ws=wb['Requirements'];dv=DataValidation(type='list',formula1='"Retain,Modify,Omit"',allow_blank=True)
    dv.showErrorMessage=True;ws.add_data_validation(dv);dv.add(f'G2:G{ws.max_row}')
    for row in ws.iter_rows(min_row=2,min_col=7,max_col=11):
        for c in row:c.fill=PatternFill('solid',fgColor='E8F1FA')
    for i,r in enumerate(case_rows,2):
        wb['Cases'].cell(i,5).hyperlink=r['card'];wb['Cases'].cell(i,5).style='Hyperlink'
    wb.save(stage/'Expert_case_requirements_review.xlsx')
    manifest['candidate_requirement_count']=len(all_rows)
    for f,h in protected.items():assert cards.digest(ROOT/f)==h,f
    for f,h in baseline['code_sha256'].items():assert cards.digest(ROOT/f)==h,f
    manifest['package_files_sha256']={p.name:cards.digest(p) for p in stage.iterdir() if p.is_file()}
    cards.write_json(stage/'manifest.json',manifest)
    stage.rename(out)
    print('Completed',len(selected),'cases and',len(all_rows),'candidate items',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    build(parser.parse_args().out.resolve())
