"""Two-new-response amendment; preserves original evidence and imported captures."""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import time
from . import repeatability_batch as original
from .repeatability_batch import sha, registered_sources, summarize_records, TERMINAL
from .compatibility_check import HTTPFixture, _process_events, attempt_resolution, load_keys
from .formal_batch import Ledger
from .formal_generation import IntegrityError, batch_lock, digest, read_journal, write_once
ROOT=original.ROOT
PACKAGE=ROOT/'docs/formal_study/repeatability_supplement_v2'
LIVE_ROOT=original.LIVE_ROOT
SCOPE='Two new responses for all 25 original stroke cases and three models'


def build_execution_plan():
    old=json.loads((original.PACKAGE/'EXECUTION_PLAN.json').read_text())
    original.validate_plan(old,live=True)
    plan=deepcopy(old)
    plan.update(version='repeatability-execution-v2',scope=SCOPE,
        tasks=[t for t in old['tasks'] if t['repeat'] in (1,2)],max_total_attempts=450,budget_limit_usd=255.60,
        original_execution_plan_sha256=digest(old))
    paths=['AMENDMENT.json','PROTOCOL.md','REVIEW_INSTRUCTIONS.md']
    plan['source_sha256'].update({str((PACKAGE/n).relative_to(ROOT)):sha(PACKAGE/n) for n in paths})
    plan['source_sha256'].update({n:sha(ROOT/n) for n in ['src/llm/repeatability_batch_v2.py','scripts/run_repeatability_batch_v2.py']})
    plan['inherited_journal']=json.loads((PACKAGE/'AMENDMENT.json').read_text())
    return plan


def validate_plan(plan,*,live=False):
    candidate=deepcopy(plan);candidate['scope']=original.SCOPE if plan['scope']==SCOPE else plan['scope']
    original.validate_plan(candidate,live=False)
    if live and (plan!=build_execution_plan() or len(plan['tasks'])!=150):
        raise IntegrityError('Live execution requires the exact 150-slot amendment')


def validate_authorization(plan,auth):
    required={'approved':True,'scope':SCOPE,'plan_sha256':digest(plan),'max_total_attempts':450,
        'budget_limit_usd':255.60,'slot_ids':[t['slot_id'] for t in plan['tasks']]}
    if any(auth.get(k)!=v for k,v in required.items()) or not all(auth.get(k) for k in ('confirmation_source','recorded_at_utc','recorded_by')):
        raise IntegrityError('Exact amended authorization required')
    evidence=auth.get('offline_test_evidence',{});path=(ROOT/evidence.get('path','')).resolve()
    if not path.is_relative_to(PACKAGE) or not path.is_file() or sha(path)!=evidence.get('sha256'):
        raise IntegrityError('Amendment test evidence changed')


def validate_inherited_journal(root,plan):
    a=plan.get('inherited_journal',{});records,head=read_journal(root)
    if len(records)!=a.get('prior_journal_record_count') or head!=a.get('prior_journal_head') or digest(records)!=a.get('prior_payloads_sha256'):
        raise IntegrityError('Inherited journal differs from amendment snapshot')
    if sha(Path(root)/'run_manifest.json')!=a.get('prior_manifest_sha256'):
        raise IntegrityError('Original manifest changed')
    summarize_records(plan,records)


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
        manifest=root/'run_manifest_v2.json'
        if manifest.exists():
            if json.loads(manifest.read_text())!=envelope:raise IntegrityError('Run manifest identity changed')
        elif read_journal(root)[0]:
            validate_inherited_journal(root,plan)
            write_once(manifest,envelope)
        else:write_once(manifest,envelope)
        ledger=Ledger(root)
        # Validate retained responses, including previous waves, before resuming.
        summarize_records(plan,ledger.records)
        complete=0
        for task in plan['tasks']:
            slot=task['slot_id']
            while True:
                if mode=='live' and (PACKAGE/'PAUSE_REQUESTED').exists():
                    return {'status':'user_paused','completed_slots':complete,'next_slot':slot}
                rows=ledger.slot(slot)
                starts=[r for r in rows if r['kind']=='attempt_started']
                decisions=[r for r in rows if r['kind']=='attempt_resolved']
                if starts and (not decisions or decisions[-1]['attempt']<starts[-1]['attempt']):
                    n=starts[-1]['attempt']
                    es=[r['event'] for r in rows if r['kind']=='stream_event' and r['attempt']==n]
                    if slot==plan.get('inherited_journal',{}).get('interrupted_slot') and not any(e['type'] in {'completed','error'} for e in es):
                        event={'type':'error','code':'administrative_interruption','remote_completion_possible':True,
                            'reason':'Study-lead pause and reduction to two additional responses; preserve captured text without replacement.'}
                        ledger.append({'kind':'stream_event','slot_id':slot,'attempt':n,'time':now(),'event':event});es.append(event)
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
