"""Export captured repeatability reports and technical status without rating content."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.llm.repeatability_batch_v2 import PACKAGE,LIVE_ROOT,summarize_records,validate_plan,sha
from src.llm.formal_generation import digest,read_journal,write_once


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--save',action='store_true');args=p.parse_args()
    plan=json.loads((PACKAGE/'EXECUTION_PLAN.json').read_text())
    validate_plan(plan,live=True)
    envelope=json.loads((LIVE_ROOT/'run_manifest_v2.json').read_text())
    if envelope['plan']!=plan or envelope['mode']!='live':raise ValueError('Unexpected execution envelope')
    records,head=read_journal(LIVE_ROOT)
    rows=summarize_records(plan,records)
    starts=[r for r in records if r['kind']=='attempt_started']
    dispatches=[r for r in records if r['kind']=='stream_event' and r['event']['type']=='dispatch_requested']
    newst={p:[] for p in ('anthropic','gemini','openai')}
    for r in rows:newst[r['provider']].append(r)
    latest={}
    for r in records:
        if r['kind']=='attempt_resolved':latest[r['slot_id']]=r['state']
    status={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'scope':plan['scope'],
        'planned_reports':len(plan['tasks']),'terminal_slots':len(rows),'captured_reports':sum(r['state']=='captured' for r in rows),
        'attempts_reserved':len(starts),'dispatches_reserved':len(dispatches),'retry_attempts':len(starts)-len({r['slot_id'] for r in starts}),
        'reservation_consumed_usd':round(sum(plan['reservation_usd_per_attempt'][r['provider']] for r in starts),6),
        'reservation_is_invoice':False,'states':dict(Counter(r['state'] for r in rows)),
        'paused_or_stopped':{k:v for k,v in latest.items() if v in {'paused','stopped'}},
        'completed_by_wave':dict(Counter(r['repeat'] for r in rows)),
        'completed_by_provider':{p:len(v) for p,v in newst.items()},
        'returned_model_identifiers':{p:sorted({r['metadata'].get('response_model') or 'Unavailable' for r in v}) for p,v in newst.items()},
        'token_limit_finishes':sum(r['token_limit_finish'] for r in rows),'normal_stream_completions':sum(r['normal_stream_completion'] for r in rows),
        'incomplete_captures':sum(r['state']=='captured' and not r['normal_stream_completion'] for r in rows),
        'journal_head':head,'execution_plan_sha256':digest(plan),'original_reports_modified':False,'clinical_quality_assessed':False}
    if args.save:
        output=LIVE_ROOT/'captured_reports';output.mkdir(exist_ok=True)
        for row in rows:
            if row['state']=='captured':
                path=output/(row['slot_id']+'.txt');raw=row['report_text'].encode()
                if path.exists():
                    if path.read_bytes()!=raw:raise ValueError('Exported report changed: '+row['slot_id'])
                else:
                    with path.open('xb') as f:f.write(raw)
        path=PACKAGE/'GENERATION_STATUS.json'
        # This is a replaceable progress summary; the source journal is immutable.
        tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(status,indent=2)+'\n');tmp.replace(path)
        if len(rows)==len(plan['tasks']):
            results={'plan_sha256':digest(plan),'journal_head':head,'reports':rows}
            path=LIVE_ROOT/'RESULTS.json'
            if path.exists():
                if json.loads(path.read_text())!=results:raise ValueError('Existing results differ')
            else:write_once(path,results)
            done=PACKAGE/'GENERATION_COMPLETION.json'
            if not done.exists():
                write_once(done,{**status,'results_sha256':sha(path),'all_slots_terminal':True,
                    'report_file_sha256':{str(p.relative_to(ROOT)):sha(p) for p in output.glob('*.txt')}})
    print(json.dumps(status))

if __name__=='__main__':main()
