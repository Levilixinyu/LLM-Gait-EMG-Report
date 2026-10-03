"""Safety and evidence checks for the new supplement; no live network calls."""
from copy import deepcopy
from collections import Counter
from importlib.metadata import version
import json
import socket
import pytest
from src.llm import repeatability_batch as runner
from src.llm.compatibility_check import HTTPFixture, PACKAGES
from src.llm.formal_generation import digest, IntegrityError, read_journal
from tests.test_formal_providers import fixture_events


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket,'connect',lambda *a,**k:pytest.fail('No test network'))
    monkeypatch.setattr(socket.socket,'connect_ex',lambda *a,**k:pytest.fail('No test network'))


def plan():
    old=json.loads((runner.ROOT/'docs/formal_study/formal_execution_v2_candidate/plan.json').read_text())
    tasks=[]
    for i,original in enumerate(old['tasks'][:3]):
        t=deepcopy(original);t.update(slot_id='fixture_'+t['provider'],case_id='fixture',repeat=1,sequence=i+1,
           system_prompt='Synthetic interface test.',user_prompt='Values 1 and 3.')
        t['input_pair_sha256']=digest([t['system_prompt'],t['user_prompt']]);tasks.append(t)
    return {'scope':'Synthetic repeatability fixture','tasks':tasks,'sdk_versions':{p:version(p) for p in PACKAGES},
        'max_attempts_per_slot':3,'max_total_attempts':9,'attempt_deadline_seconds':600,
        'reservation_usd_per_attempt':{'anthropic':1,'gemini':1,'openai':1},'budget_limit_usd':9}


def fixtures(p):return {t['slot_id']:(HTTPFixture(),)*3 for t in p['tasks']}


def emit(task,persist,kind='complete'):
    persist({'type':'dispatch_requested','task_sha256':digest(task)})
    if kind!='empty':persist({'type':'text','text':'Retained original output.'})
    if kind=='partial':persist({'type':'error','code':'timeout','remote_completion_possible':True})
    else:persist({'type':'completed','metadata':{'response_model':task['model'],'finish_reason':'MAX_TOKENS','usage':{}}})


@pytest.mark.parametrize('kind',['complete','empty','partial'])
def test_first_output_retained_and_resume_idempotent(tmp_path,monkeypatch,kind):
    p=plan();calls=[]
    def process(task,key,fixture,deadline,persist):calls.append(task['slot_id']);emit(task,persist,kind)
    monkeypatch.setattr(runner,'_process_events',process)
    result=runner.run(tmp_path,p,fixtures=fixtures(p))
    assert result['status']=='complete' and len(calls)==3
    assert runner.run(tmp_path,p,fixtures={})==result and len(calls)==3
    rows=runner.summarize_records(p,read_journal(tmp_path)[0])
    assert all(r['attempts']==1 for r in rows)
    assert all((r['report_text'] is None)==(kind=='empty') for r in rows)


def test_actual_sdk_streams_keep_full_text_and_truncation(tmp_path):
    p=plan()
    fs={t['slot_id']:(HTTPFixture(chunks=tuple(fixture_events(t['provider']))),) for t in p['tasks']}
    assert runner.run(tmp_path,p,fixtures=fs)['completed_slots']==3
    rows=runner.summarize_records(p,read_journal(tmp_path)[0])
    assert all(r['report_text']=='First. Second.' and r['token_limit_finish'] for r in rows)
    assert all(r['metadata']['usage'] for r in rows)


def test_transient_retry_cap_and_persistent_count(tmp_path,monkeypatch):
    p=plan();calls=[];sleeps=[]
    def process(task,key,fixture,deadline,persist):
        calls.append(task['slot_id']);persist({'type':'error','code':'transient_server','http_status':503})
    monkeypatch.setattr(runner,'_process_events',process)
    result=runner.run(tmp_path,p,fixtures=fixtures(p),sleep=sleeps.append,now=lambda:100)
    assert result['attempts']==9 and result['states']=={'exhausted':3}
    assert sleeps==[5,30]*3
    assert runner.run(tmp_path,p,fixtures={})==result and len(calls)==9


@pytest.mark.parametrize('code,state',[('timeout','paused'),('billing','stopped')])
def test_no_blind_retry_on_unknown_remote_completion_or_billing(tmp_path,monkeypatch,code,state):
    p=plan();calls=[]
    def process(task,key,fixture,deadline,persist):
        calls.append(task['slot_id']);persist({'type':'dispatch_requested','task_sha256':digest(task)})
        persist({'type':'error','code':code,'remote_completion_possible':True})
    monkeypatch.setattr(runner,'_process_events',process)
    for _ in range(2):assert runner.run(tmp_path,p,fixtures=fixtures(p))['status']==state
    assert len(calls)==1


@pytest.mark.parametrize('partial',[True,False])
def test_interrupted_capture_cannot_be_replaced(tmp_path,monkeypatch,partial):
    p=plan();calls=[]
    def crash(task,key,fixture,deadline,persist):
        calls.append(task['slot_id']);persist({'type':'dispatch_requested','task_sha256':digest(task)})
        if partial:persist({'type':'text','text':'Already captured.'})
        raise KeyboardInterrupt()
    monkeypatch.setattr(runner,'_process_events',crash)
    with pytest.raises(KeyboardInterrupt):runner.run(tmp_path,p,fixtures=fixtures(p))
    def finish(task,key,fixture,deadline,persist):calls.append(task['slot_id']);emit(task,persist)
    monkeypatch.setattr(runner,'_process_events',finish)
    result=runner.run(tmp_path,p,fixtures=fixtures(p))
    if partial:
        assert result['status']=='complete' and len(calls)==3
        assert runner.summarize_records(p,read_journal(tmp_path)[0])[0]['report_text']=='Already captured.'
    else:assert result['status']=='paused' and len(calls)==1


def test_budget_stops_before_an_extra_transmission(tmp_path,monkeypatch):
    p=plan();p['budget_limit_usd']=2;calls=[]
    def process(task,key,fixture,deadline,persist):calls.append(task['slot_id']);emit(task,persist)
    monkeypatch.setattr(runner,'_process_events',process)
    for _ in range(2):assert runner.run(tmp_path,p,fixtures=fixtures(p))['status']=='budget_paused'
    assert len(calls)==2


def test_missing_authorization_precedes_credentials_and_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'load_keys',lambda:pytest.fail('Early credential load'))
    with pytest.raises(IntegrityError,match='authorization'):runner.run(tmp_path/'new',plan(),mode='live')
    assert not (tmp_path/'new').exists()


def test_resume_cannot_change_parameters_or_prompt(tmp_path,monkeypatch):
    p=plan()
    monkeypatch.setattr(runner,'_process_events',lambda task,key,fixture,deadline,persist:emit(task,persist))
    runner.run(tmp_path,p,fixtures=fixtures(p))
    altered=deepcopy(p);altered['tasks'][0]['parameters']['temperature']=0
    with pytest.raises(IntegrityError,match='manifest'):runner.run(tmp_path,altered,fixtures={})


def test_terminal_text_mismatch_is_detected():
    p=plan();t=p['tasks'][0]
    records=[{'kind':'attempt_started','slot_id':t['slot_id'],'attempt':1,'task_sha256':digest(t),'time':1},
      {'kind':'stream_event','slot_id':t['slot_id'],'attempt':1,'event':{'type':'text','text':'actual'}},
      {'kind':'attempt_resolved','slot_id':t['slot_id'],'attempt':1,'state':'captured','text':'replaced'}]
    with pytest.raises(IntegrityError,match='stream'):runner.summarize_records(p,records)


def test_whitespace_only_completed_output_remains_terminal(tmp_path,monkeypatch):
    p=plan();calls=[]
    def process(task,key,fixture,deadline,persist):
        calls.append(task['slot_id']);persist({'type':'text','text':'  \n'})
        persist({'type':'completed','metadata':{}})
    monkeypatch.setattr(runner,'_process_events',process)
    assert runner.run(tmp_path,p,fixtures=fixtures(p))['states']=={'empty':3}
    assert len(calls)==3


def test_registered_225_slot_manifest_and_exact_resume(tmp_path,monkeypatch):
    p=runner.build_execution_plan()
    runner.validate_plan(p,live=True)
    assert len(p['tasks'])==225
    calls=[]
    def process(task,key,fixture,deadline,persist):calls.append(task['slot_id']);emit(task,persist)
    monkeypatch.setattr(runner,'_process_events',process)
    result=runner.run(tmp_path,p,fixtures=fixtures(p))
    assert result['completed_slots']==225 and len(calls)==len(set(calls))==225
    assert Counter(t['repeat'] for t in p['tasks'])=={1:75,2:75,3:75}
    assert runner.run(tmp_path,p,fixtures={})==result and len(calls)==225
    bad=deepcopy(p);bad['tasks'][0]['parameters']['temperature']=0
    with pytest.raises(IntegrityError,match='exact'):runner.validate_plan(bad,live=True)
