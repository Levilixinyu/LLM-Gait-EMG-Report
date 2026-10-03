"""Read model metadata only; no generation, clinical input, or credential output."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.llm.compatibility_check import load_keys
from src.llm.formal_generation import write_once
import httpx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--live',action='store_true');args=ap.parse_args()
    if not args.live:ap.error('Explicit --live required for authenticated metadata GET requests')
    folder=ROOT/'docs/formal_study/repeatability_supplement_v1'
    if not json.loads((folder/'STUDY_LEAD_CONFIRMATION.json').read_text())['generation_requested']:
        raise ValueError('Study-lead generation instruction missing')
    out=folder/'PROVIDER_ACCESS.json'
    if out.exists():raise FileExistsError('Preserve the existing metadata record')
    keys=load_keys()
    requests=[('openai','gpt-6-astra','https://api.openai.com/v1/models/gpt-6-astra',{'Authorization':'Bearer '+keys['openai']}),
      ('anthropic','claude-opus-5','https://api.anthropic.com/v1/models/claude-opus-5',{'x-api-key':keys['anthropic'],'anthropic-version':'2023-06-01'}),
      ('gemini','gemini-3.1-pro-preview','https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview',{'x-goog-api-key':keys['gemini']})]
    rows=[]
    with httpx.Client(timeout=30,follow_redirects=False,trust_env=False) as client:
        for provider,model,url,headers in requests:
            try:
                response=client.get(url,headers=headers)
                body=response.json()
                allow=('id','name','display_name','displayName','version','created','created_at','owned_by','max_input_tokens','max_tokens','inputTokenLimit','outputTokenLimit','supportedGenerationMethods')
                row={'provider':provider,'requested_model':model,'http_status':response.status_code,
                     'metadata':{k:body[k] for k in allow if k in body},'checked_at_utc':datetime.now(timezone.utc).isoformat()}
                if response.status_code!=200:row['error_type']=str(body.get('error',{}).get('type',body.get('error',{}).get('status','unknown')))
            except httpx.TransportError as exc:
                # Permit a sandbox/network retry without pretending to have queried a model.
                print(json.dumps({'provider':provider,'network_error_type':type(exc).__name__,'metadata_record_written':False}),flush=True)
                raise SystemExit(2)
            rows.append(row)
    record={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'requests':rows,'metadata_get_requests':len(rows),
        'generation_calls':0,'clinical_input_sent':False,'all_metadata_requests_succeeded':all(r['http_status']==200 for r in rows),
        'limits':'Metadata access does not establish generation quota, support for every request parameter, or identical historical weights.'}
    write_once(out,record)
    print(json.dumps(record))

if __name__=='__main__':main()
