"""Independent, bounded repeated-generation run using the preserved stream policy."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from importlib.metadata import version
import json
from pathlib import Path
import time

from .compatibility_check import HTTPFixture, PACKAGES, _process_events, attempt_resolution, load_keys
from .formal_batch import Ledger
from .formal_generation import IntegrityError, batch_lock, digest, read_journal, write_once

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'docs/formal_study/repeatability_supplement_v1'
LIVE_ROOT=ROOT/'data/reports_repeatability_v1'
SCOPE='Three new responses for all 25 original stroke cases and three models'
TERMINAL={'captured','empty','exhausted'}
CODE=['src/llm/repeatability_batch.py','scripts/run_repeatability_batch.py',
      'src/llm/formal_batch.py','src/llm/formal_generation.py',
      'src/llm/compatibility_check.py','src/llm/formal_providers.py']


def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def registered_sources(record):
    for name,h in record.items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or path.is_symlink() or sha(path)!=h:
            raise IntegrityError('Registered source changed: '+name)


def build_execution_plan():
    read=lambda name:json.loads((PACKAGE/name).read_text())
    prepared=read('BUILD_RECORD.json')
    registered_sources(prepared['source_sha256'])
    for name,h in prepared['output_sha256'].items():
        if sha(PACKAGE/name)!=h:raise IntegrityError('Planning record changed: '+name)
    planning=read('PLAN.json')
    confirmation=read('STUDY_LEAD_CONFIRMATION.json')
    if not confirmation.get('generation_requested') or not confirmation.get('three_human_raters_full_workload_confirmed'):
        raise IntegrityError('Study-lead instruction and scoring capacity are required')
    access=read('PROVIDER_ACCESS.json')
    if not access['all_metadata_requests_succeeded']:
        raise IntegrityError('Model metadata access unresolved')
    prices=read('CURRENT_CONFIGURATION.json')
    if prices['requested_identifiers']!={t['provider']:t['model'] for t in planning['tasks']}:
        raise IntegrityError('Requested models changed')
    original=json.loads((ROOT/'docs/formal_study/formal_execution_v2_candidate/plan.json').read_text())
    previous={t['slot_id']:t for t in original['tasks']}
    tasks=[]
    for slot in planning['tasks']:
        old=previous[slot['original_slot_id']]
        if digest(old)!=slot['original_task_sha256']:raise IntegrityError('Original task mismatch')
        t=deepcopy(old)
        t.update(slot_id=slot['slot_id'],repeat=slot['repeat'],sequence=slot['sequence'],
            provider_position_within_case=slot['provider_position_within_case'],original_slot_id=slot['original_slot_id'])
        tasks.append(t)
    paths=['BUILD_RECORD.json','PLAN.json','PROTOCOL.md','STUDY_LEAD_CONFIRMATION.json',
           'PROVIDER_ACCESS.json','CURRENT_CONFIGURATION.json','REVIEW_INSTRUCTIONS.md']
    source={str((PACKAGE/n).relative_to(ROOT)):sha(PACKAGE/n) for n in paths}
    source.update({name:sha(ROOT/name) for name in CODE})
    return {'version':'repeatability-execution-v1','scope':SCOPE,'tasks':tasks,
       'source_sha256':source,'planning_plan_sha256':digest(planning),
       'sdk_versions':planning['sdk_versions_original'],'live_output_directory':str(LIVE_ROOT.relative_to(ROOT)),
       'max_attempts_per_slot':3,'max_total_attempts':675,'attempt_deadline_seconds':600,
       'reservation_usd_per_attempt':prices['reservation_usd_per_attempt'],
       'budget_limit_usd':prices['reservation_ceiling_usd'],
       'cost_scope':'Conservative reservation gate; not an enforceable provider invoice limit.',
       'word_limit':None,'no_added_length_constraint':True,
       'historical_backend_equivalence_established':False}


def validate_plan(plan,*,live=False):
    tasks=plan['tasks']
    if len({t['slot_id'] for t in tasks})!=len(tasks):raise IntegrityError('Duplicate new slot')
    if plan['max_attempts_per_slot']!=3 or plan['max_total_attempts']!=3*len(tasks) or plan['attempt_deadline_seconds']!=600:
        raise IntegrityError('Attempt policy mismatch')
    for t in tasks:
        if not t['system_prompt'].strip() or not t['user_prompt'].strip() or digest([t['system_prompt'],t['user_prompt']])!=t['input_pair_sha256']:
            raise IntegrityError('Input hash mismatch')
        # Byte count is a deliberately conservative screening proxy, with extra
        # allowance for message serialization; actual token usage is also retained.
        if len((t['system_prompt']+t['user_prompt']).encode())>15000:
            raise IntegrityError('Input exceeds the registered 16K token reservation screen')
    rates=plan['reservation_usd_per_attempt']
    if set(rates)!={'anthropic','openai','gemini'} or any(Decimal(str(v))<=0 for v in rates.values()):
        raise IntegrityError('Invalid reservation rates')
    if Decimal(str(plan['budget_limit_usd']))<=0:raise IntegrityError('Invalid budget ceiling')
    if plan['sdk_versions']!={p:version(p) for p in PACKAGES}:raise IntegrityError('SDK versions changed')
    if live:
        if plan['scope']!=SCOPE or len(tasks)!=225 or plan!=build_execution_plan():
            raise IntegrityError('Live execution requires the exact 225-slot supplement')
    elif plan['scope'] not in {SCOPE,'Synthetic repeatability fixture'}:
        raise IntegrityError('Unknown offline scope')


def validate_authorization(plan,auth):
    required={'approved':True,'scope':SCOPE,'plan_sha256':digest(plan),
              'max_total_attempts':plan['max_total_attempts'],'budget_limit_usd':plan['budget_limit_usd'],
              'slot_ids':[t['slot_id'] for t in plan['tasks']]}
    if any(auth.get(k)!=v for k,v in required.items()) or not all(auth.get(k) for k in ('confirmation_source','recorded_at_utc','recorded_by')):
        raise IntegrityError('Exact supplement authorization required')
    evidence=auth.get('offline_test_evidence',{})
    path=(ROOT/evidence.get('path','')).resolve()
    if not path.is_relative_to(PACKAGE) or not path.is_file() or sha(path)!=evidence.get('sha256'):
        raise IntegrityError('Offline execution test evidence changed')


def summarize_records(plan,records):
    expected={t['slot_id']:t for t in plan['tasks']}
    if any(r.get('slot_id') not in expected for r in records):raise IntegrityError('Unregistered journal slot')
    groups={slot:[] for slot in expected}
    for r in records:groups[r['slot_id']].append(r)
    result=[]
    for slot,t in expected.items():
        rows=groups[slot];starts=[r for r in rows if r['kind']=='attempt_started']
        decisions=[r for r in rows if r['kind']=='attempt_resolved']
        if [r['attempt'] for r in starts]!=list(range(1,len(starts)+1)) or len(starts)>3:
            raise IntegrityError('Attempt sequence invalid')
        if any(r['task_sha256']!=digest(t) for r in starts):raise IntegrityError('Task identity mismatch')
        if not decisions or not starts or decisions[-1]['attempt']!=starts[-1]['attempt']:
            continue
        final=decisions[-1]
        if final['state'] not in TERMINAL:continue
        for prior in starts[:-1]:
            es=[r['event'] for r in rows if r['kind']=='stream_event' and r['attempt']==prior['attempt']]
            if any(e.get('text','').strip() or e['type']=='completed' for e in es):
                raise IntegrityError('A retained response was replaced')
        events=[r['event'] for r in rows if r['kind']=='stream_event' and r['attempt']==final['attempt']]
        text=''.join(e.get('text','') for e in events if e['type']=='text')
        if final['state']=='captured' and final.get('text','')!=text:raise IntegrityError('Saved text differs from stream')
        if bool(text.strip())!=(final['state']=='captured'):raise IntegrityError('Terminal state discards text')
        metadata=next((e['metadata'] for e in reversed(events) if e.get('metadata')),{})
        result.append({'slot_id':slot,'case_id':t['case_id'],'provider':t['provider'],'requested_model':t['model'],
            'repeat':t['repeat'],'state':final['state'],'attempts':len(starts),'report_text':text or None,
            'metadata':metadata,'normal_stream_completion':any(e['type']=='completed' for e in events),
            'token_limit_finish':metadata.get('finish_reason') in {'length','max_tokens','MAX_TOKENS'},
            'task_sha256':digest(t),'first_attempt_timestamp':starts[0]['time'],
            'last_event_timestamp':max(r.get('time',0) for r in rows),
            'word_count':len(text.split()),'slot_records_sha256':digest(rows)})
    return result


def run(root,plan,*,mode='mock',authorization=None,fixtures=None,deadline=None,sleep=time.sleep,now=time.time,progress=None):
    if mode=='live':validate_authorization(plan,authorization or {})
    validate_plan(plan,live=mode=='live')
    root=Path(root).resolve()
    if mode=='live':
        if root!=LIVE_ROOT.resolve() or fixtures is not None or deadline is not None:raise IntegrityError('Live path and transport are fixed')
        keys=load_keys();deadline=600
    elif mode=='mock':
        if root.is_relative_to(ROOT/'data') or not isinstance(fixtures,dict):raise IntegrityError('Mock requires fixtures and a separate path')
        keys={p:'fake-offline-key' for p in ('anthropic','gemini','openai')};deadline=deadline or 600
    else:raise IntegrityError('Mode must be live or mock')
    with batch_lock(root):
        envelope={'plan':plan,'plan_sha256':digest(plan),'mode':mode,'authorization':authorization if mode=='live' else None}
        manifest=root/'run_manifest.json'
        if manifest.exists():
            if json.loads(manifest.read_text())!=envelope:raise IntegrityError('Run manifest identity changed')
        elif read_journal(root)[0]:raise IntegrityError('Journal without manifest')
        else:write_once(manifest,envelope)
        ledger=Ledger(root)
        # Validate retained responses, including previous waves, before resuming.
        summarize_records(plan,ledger.records)
        complete=0
        for task in plan['tasks']:
            slot=task['slot_id']
            while True:
                rows=ledger.slot(slot)
                starts=[r for r in rows if r['kind']=='attempt_started']
                decisions=[r for r in rows if r['kind']=='attempt_resolved']
                if starts and (not decisions or decisions[-1]['attempt']<starts[-1]['attempt']):
                    n=starts[-1]['attempt']
                    es=[r['event'] for r in rows if r['kind']=='stream_event' and r['attempt']==n]
                    resolution=attempt_resolution(es,n,now())
                    if resolution['state']=='retry_wait':resolution={'state':'paused','text':'','reason':'Interrupted persistence needs technical review'}
                    decision={'kind':'attempt_resolved','slot_id':slot,'attempt':n,'time':now(),**resolution}
                    ledger.append(decision);decisions.append(decision)
                if decisions:
                    d=decisions[-1]
                    if d['state'] in TERMINAL:
                        complete+=1
                        if progress:progress({'completed_slots':complete,'planned_slots':len(plan['tasks']),'wave':task['repeat'],'slot_id':slot,'state':d['state']})
                        break
                    if d['state'] in {'paused','stopped'}:
                        return {'status':d['state'],'slot_id':slot,'completed_slots':complete,'journal_head':ledger.head}
                    if d['state']!='retry_wait':raise IntegrityError('Unknown attempt decision')
                    remaining=max(0,d['retry_not_before']-now())
                    while remaining>0:
                        duration=min(remaining,30);sleep(duration);remaining-=duration
                n=len(starts)+1
                if n>3:raise IntegrityError('Attempt cap exceeded')
                all_starts=[r for r in ledger.records if r['kind']=='attempt_started']
                reservation=sum(Decimal(str(plan['reservation_usd_per_attempt'][r['provider']])) for r in all_starts)
                if len(all_starts)>=plan['max_total_attempts'] or reservation+Decimal(str(plan['reservation_usd_per_attempt'][task['provider']]))>Decimal(str(plan['budget_limit_usd'])):
                    return {'status':'budget_paused','slot_id':slot,'completed_slots':complete}
                fixture=None
                if mode=='mock':
                    fixture=fixtures[slot][n-1]
                    if type(fixture) is not HTTPFixture:raise IntegrityError('Explicit HTTP mock required')
                ledger.append({'kind':'attempt_started','slot_id':slot,'provider':task['provider'],
                    'attempt':n,'repeat':task['repeat'],'task_sha256':digest(task),'time':now(),'possible_duplicate':n>1})
                events=[]
                def persist(event):
                    if event.get('task_sha256',digest(task))!=digest(task):raise IntegrityError('Stream attribution mismatch')
                    ledger.append({'kind':'stream_event','slot_id':slot,'attempt':n,'time':now(),'event':event});events.append(event)
                if progress:progress({'status':'attempt_started','completed_slots':complete,'planned_slots':len(plan['tasks']),'wave':task['repeat'],'slot_id':slot,'attempt':n})
                _process_events(task,keys[task['provider']],fixture,deadline,persist)
                decision=attempt_resolution(events,n,now())
                ledger.append({'kind':'attempt_resolved','slot_id':slot,'attempt':n,'time':now(),**decision})
        rows=summarize_records(plan,ledger.records)
        if len(rows)!=len(plan['tasks']):raise IntegrityError('Incomplete terminal evidence')
        result={'status':'complete','completed_slots':len(rows),'journal_head':ledger.head,
             'attempts':sum(r['attempts'] for r in rows),'states':dict(Counter(r['state'] for r in rows))}
        path=root/'COMPLETION.json'
        if path.exists():
            if json.loads(path.read_text())!=result:raise IntegrityError('Completion differs')
        else:write_once(path,result)
        return result
