"""Freeze the approved five-case trial, generate exact-input reports, and blind them.

Run prepare, generate, then package. Generation calls the project's configured APIs.
Private artifacts stay beneath the ignored expert_rate directory. No rubric weights.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import random
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.generation_cache import TaskSpec, task_hash, record_from_result, SUCCESS_STOP_REASONS

BASE = ROOT / 'docs/expert_trial/expert_rate'
WORK = BASE / 'working_review_2026-09-17'
DEFAULT_OUT = BASE / 'trial_2026-09-17_v1'
MODELS = [('anthropic', 'claude-opus-5'), ('openai', 'gpt-6-astra'), ('gemini', 'gemini-3.1-pro-preview')]
CASES = ['stroke_Sub09_P','stroke_Sub05_P','stroke_Sub50_P','stroke_Sub47_P','control_Sub49_avg']
VERSION = 'expert-trial-2026-09-17-v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(p)


def verify(out):
    manifest = json.loads((out/'freeze_manifest.json').read_text())
    for name, digest in manifest['files_sha256'].items():
        if sha(out/name) != digest:
            raise ValueError(f'Frozen file changed: {name}')
    for name, digest in manifest['runtime_code_sha256'].items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Runtime code changed: {name}; create a new trial version')
    return manifest


def prepare(out):
    if (out/'freeze_manifest.json').exists():
        verify(out)
        print('Existing freeze verified; nothing overwritten.')
        return
    if out.exists():
        raise ValueError('Output exists without a freeze manifest; inspect before continuing')
    source = ROOT/'docs/expert_trial/data_cards_v5'
    cards = json.loads((source/'manifest.json').read_text())
    approval = json.loads((WORK/'wording_confirmation_check.json').read_text())
    assert approval['human_expert_confirmation_provenance']['status']=='USER_ATTESTED_HUMAN_EXPERT'
    assert sha(WORK/approval['integrated_file']) == approval['integrated_sha256']
    out.mkdir(parents=True)
    frozen = out/'frozen'; frozen.mkdir()
    shutil.copy2(WORK/approval['integrated_file'], frozen/'confirmed_checklist.xlsx')
    shutil.copy2(WORK/'Five_case_independent_rating_form_blank.xlsx', frozen/'rating_template.xlsx')
    shutil.copy2(WORK/'wording_confirmation_check.json', frozen/'expert_confirmation_provenance.json')
    tasks=[]
    for cid in CASES:
        case = next(c for c in cards['cases'] if c['case_id']==cid)
        dest=frozen/'cases'/cid; dest.mkdir(parents=True)
        for name in ['model_system_prompt.txt','model_user_prompt.txt','model_messages.json','summary.json','facts.json','reference_card.md','curves_emg.png','curves_kinematics.png']:
            assert sha(source/cid/name)==case['files_sha256'][name], (cid,name)
            shutil.copy2(source/cid/name,dest/name)
        messages=json.loads((dest/'model_messages.json').read_text())
        system=(dest/'model_system_prompt.txt').read_text();user=(dest/'model_user_prompt.txt').read_text()
        assert messages==[{'role':'system','content':system},{'role':'user','content':user}]
        for provider,model in MODELS:
            spec=TaskSpec(subject_id=case['subject_id'],side=case['side'],provider=provider,model=model,
                prompt_version=VERSION,system_prompt=system,user_prompt=user,
                generation_params={'max_tokens':8000},
                reference_id='main_cohort_excel/'+('loo:Sub49' if cid.startswith('control') else 'all-controls'),
                data_manifest={'card_manifest':sha(source/'manifest.json'),'summary':sha(dest/'summary.json')},
                code_manifest={n:sha(ROOT/n) for n in ['src/llm/providers.py','src/llm/generation_cache.py', 'scripts/run_five_case_trial.py']})
            tasks.append({'case_id':cid,'task_hash':task_hash(spec),'spec':asdict(spec)})
    save(frozen/'tasks.json',tasks)
    shutil.copy2(source/'manifest.json',frozen/'source_card_manifest.json')
    save(out/'freeze_manifest.json',{
        'version':VERSION,'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Operational trial freeze of confirmed checklist and exact text inputs; not approval of weights or a full clinical reference standard',
        'human_expert_confirmation':'User attested that rater1 personally confirmed the six wording changes',
        'n_cases':5,'n_tasks':15,'weights':None,'model_parameters':'Existing project roster; max_tokens 8000; other provider defaults unchanged',
        'old_reports':'All 15 target v1 reports lack complete prompt snapshots; no task manifests found under data; excluded',
        'runtime_code_sha256':tasks[0]['spec']['code_manifest'],
        'files_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(frozen.rglob('*')) if p.is_file()}})
    (out/'README.md').write_text('# Five-case pilot rating v1\n\nThe expert-confirmed checklist and complete text inputs for the five cases have been fixed for this round; see freeze_manifest.json for hashes. This is an operational version for pilot rating and does not indicate approval of weights or a clinical ground-truth framework.\n\n- frozen: fixed inputs, confirmed checklist, and rating-form template; do not send the entire directory to the models.\n- private: original model reports and anonymization mapping table, retained by researchers only.\n- raters: generated only after all 15 reports pass completeness and input verification; send the rater1 or rater2 subfolder separately.\n\nReport generation sends only model_system_prompt.txt and model_user_prompt.txt for each case, not the expert checklist or curves. Old v1 reports were not reused. Rating does not calculate weights or total scores.\n\nSee generation_status.json for run status; rating must not begin before the raters directory has been generated.\n')
    print('Frozen: five cases, 15 exact-input tasks, confirmed checklist and blank ratings.')


def valid(record, task):
    spec=TaskSpec(**task['spec'])
    return (record.get('task_hash')==task_hash(spec)==task['task_hash']
        and all(record.get(k)==v for k,v in asdict(spec).items())
        and record.get('case_id')==task['case_id']
        and isinstance(record.get('report_text'),str) and bool(record['report_text'].strip())
        and record.get('truncated') is False
        and record.get('stop_reason') in SUCCESS_STOP_REASONS[spec.provider])


def report_path(out, task):
    return out/'private/reports'/f"{task['case_id']}__{task['spec']['provider']}.json"


def generate(out):
    verify(out)
    from src.llm.providers import AnthropicProvider, OpenAIProvider, GeminiProvider
    classes={'anthropic':AnthropicProvider,'openai':OpenAIProvider,'gemini':GeminiProvider}
    tasks=json.loads((out/'frozen/tasks.json').read_text());clients={};status=[]
    for task in tasks:
        spec=TaskSpec(**task['spec']); path=report_path(out,task)
        if path.exists():
            record=json.loads(path.read_text())
            if not valid(record,task):raise ValueError(f'Invalid existing report retained for inspection: {path.name}')
            state='REUSED_VALID'
        else:
            try:
                if spec.provider not in clients:clients[spec.provider]=classes[spec.provider](model=spec.model,max_tokens=8000)
                result=clients[spec.provider].generate(spec.system_prompt,spec.user_prompt)
                record=record_from_result(spec,result);record['case_id']=task['case_id']
                save(path,record)
                state='GENERATED_VALID' if valid(record,task) else 'GENERATED_INVALID'
            except Exception as exc:
                # Do not print exception strings: SDK errors may contain credential or payload details.
                state='FAILED:'+type(exc).__name__
        status.append({'case_id':task['case_id'],'provider':spec.provider,'status':state})
        save(out/'generation_status.json',{'tasks':status,'complete':len(status)==15 and all(x['status'] in ['REUSED_VALID','GENERATED_VALID'] for x in status)})
        print(task['case_id'],spec.provider,state,flush=True)
        if state.startswith('FAILED:') or state=='GENERATED_INVALID':
            raise RuntimeError(f'Generation paused: {state}. Successful reports retained; no blind package published.')


def package(out):
    verify(out)
    import openpyxl
    from src.eval.blinding import _build_strip_patterns_from_records, _strip_identifying_tokens
    tasks=json.loads((out/'frozen/tasks.json').read_text());records=[]
    for task in tasks:
        record=json.loads(report_path(out,task).read_text())
        if not valid(record,task):raise ValueError('Incomplete/mismatched report set')
        records.append(record)
    assert len(records)==15
    if (out/'raters').exists():raise ValueError('Rater package already exists; do not replace a distributed package')
    stage=out/'raters.building'
    if stage.exists():raise ValueError('Inspect existing staging directory before retrying')
    stage.mkdir()
    patterns=_build_strip_patterns_from_records(records)
    registry=[];key=[];rng=random.SystemRandom()
    for cid in CASES:
        group=[r for r in records if r['case_id']==cid];rng.shuffle(group)
        for slot,record in zip('ABC',group):
            anon=f'R{len(registry)+1:03d}'
            text=_strip_identifying_tokens(record['report_text'],patterns)
            entry={'case_id':cid,'slot':slot,'anon_id':anon,'text':text,
                   'blinded_text_sha256':hashlib.sha256(text.encode()).hexdigest()}
            registry.append(entry)
            key.append({k:v for k,v in entry.items() if k!='text'} | {'provider':record['provider'],'model':record['model'], 'response_model':record.get('response_model'),'task_hash':record['task_hash'], 'source_sha256':sha(out/'private/reports'/f"{cid}__{record['provider']}.json"), 'redacted':text!=record['report_text']})
    save(out/'private/answer_key_DO_NOT_SHARE.json',key)
    lookup={(x['case_id'],x['slot']):x for x in registry}
    # Raters receive separate workbooks and no original confirmation identities or answer key.
    for number in [1,2]:
        folder=stage/f'rater{number}';folder.mkdir()
        wb=openpyxl.load_workbook(out/'frozen/rating_template.xlsx')
        for name in list(wb.sheetnames):
            if name.startswith(f'Rater{3-number}_'):del wb[name]
        for s in wb:
            if s.title=='Completion instructions':
                for row in s.iter_rows(min_row=2):
                    if row[0].value=='Report binding':row[1].value='Anonymous report IDs have been bound; please read the corresponding cases and reports through index.html. Do not disclose your judgments to the other rater.'
                    if row[0].value=='Version':row[1].value=VERSION+'; the 6 wording changes were confirmed by the expert personally; record only coverage and errors, without a total score.'
                continue
            for row in s.iter_rows(min_row=2):
                entry=lookup[(row[0].value,row[1].value)];row[2].value=entry['anon_id']
                if s.title=='Report Binding_Researcher':row[3].value='Complete inputs consistent; completion status verified';row[4].value=entry['blinded_text_sha256']
        wb.save(folder/'Independent_rating_form.xlsx')
        checklist=openpyxl.load_workbook(out/'frozen/confirmed_checklist.xlsx')
        clean=openpyxl.Workbook();clean.remove(clean.active)
        for name in ['Sub09_P','Sub05_P','Sub50_P','Sub47_P','Sub49_avg']:
            ws=clean.create_sheet(name)
            for row in checklist[name].values:ws.append(row[:6])
            ws.freeze_panes='C2'
            for row in ws:
                for cell in row:cell.alignment=openpyxl.styles.Alignment(wrap_text=True,vertical='top')
            for col in ['C','D','E','F']:ws.column_dimensions[col].width=65
        clean.save(folder/'Confirmed_execution_checklist.xlsx')
        sections=[]
        for cid in CASES:
            inputs=out/'frozen/cases'/cid;dest=folder/cid;dest.mkdir()
            for name in ['model_system_prompt.txt','model_user_prompt.txt','reference_card.md','curves_emg.png','curves_kinematics.png']:shutil.copy2(inputs/name,dest/name)
            sections.append(f'<h2 id="{cid}">{cid}</h2><p><a href="{cid}/model_system_prompt.txt\">Model system input</a> · <a href=\"{cid}/model_user_prompt.txt\">Model case input</a> · <a href=\"{cid}/reference_card.md\">Reference notes</a></p><details><summary>Expert reference curves (not supplied to the text models)</summary><img src=\"{cid}/curves_emg.png"><img src="{cid}/curves_kinematics.png"></details>')
            for entry in [e for e in registry if e['case_id']==cid]:
                sections.append(f'<h3>{entry["anon_id"]} · Report slot {entry["slot"]}</h3><pre>{html.escape(entry["text"])}</pre>')
        page='<!doctype html><html lang="en"><meta charset="utf-8"><title>Five-case independent pilot rating</title><style>body{max-width:1000px;margin:40px auto;font:17px/1.7 sans-serif;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f5f7f8;padding:24px}img{width:100%}h2{border-top:2px solid #456;padding-top:30px}</style><h1>Five-case independent pilot rating</h1><p>Independently complete "Independent_rating_form.xlsx" in this folder, following "Confirmed_execution_checklist.xlsx." Record coverage and errors only; do not calculate a total score. Plots are for expert reference only; the models did not receive curve images.</p>'+''.join(sections)+'</html>'
        (folder/'index.html').write_text(page)
        (folder/'Read_first.txt').write_text('First open index.html to read the anonymous reports, then complete Independent_rating_form.xlsx against Confirmed_execution_checklist.xlsx. Return only the rating form when finished. The two raters should not discuss with each other; leave disagreements for subsequent adjudication.\n')
    stage.rename(out/'raters')
    save(out/'packaging_check.json',{'n_cases':5,'n_reports':15,'n_raters':2,'input_and_completion_verified':True,'weights_assigned':False,'answer_key_outside_rater_folders':True,'files_sha256':{str(p.relative_to(out)):sha(p) for p in sorted((out/'raters').rglob('*')) if p.is_file()}})
    print('Published two independent rater folders; 15 blinded reports per rater.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','generate','package','verify']);parser.add_argument('--out',type=Path,default=DEFAULT_OUT)
    args=parser.parse_args();globals()[args.action](args.out)
