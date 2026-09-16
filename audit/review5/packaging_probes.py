"""Independent packaging checks; synthetic reports, temporary directories, no API."""
import sys,json,tempfile,contextlib,io,csv
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,'/private/tmp/gait-review5')
from src.llm.generation_cache import TaskSpec,artifact_name,record_from_result,place_record,task_hash
from src.eval.blinding import create_rating_packets
O=Path(__file__).resolve().parent
providers={'anthropic','openai','gemini'}; results={}
def spec(subject,provider,user='SAME'):
 return TaskSpec(subject,'P',provider,'model-'+provider,'v2','SYSTEM',user)
def put(d,subject,provider,user='SAME',stop=None):
 s=spec(subject,provider,user);r=SimpleNamespace(text='Report '+subject+' '+provider,stop_reason=stop or {'anthropic':'end_turn','openai':'stop','gemini':'STOP'}[provider],truncated=False)
 place_record(d/artifact_name(s),record_from_result(s,r))
def build(d,out,subject):
 with contextlib.redirect_stdout(io.StringIO()):
  create_rating_packets(str(d),str(out),prompt_version='v2',expected_providers=providers,expected_tasks={(subject,p):task_hash(spec(subject,p)) for p in providers})
for case in ['valid','content_filter','wrong_provider_stop','corrupt_archives','mixed_input','missing_subject']:
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'reports';d.mkdir();out=Path(td)/'out'
  for p in providers:put(d,'Sub01',p,user='DIFFERENT' if case=='mixed_input' and p=='gemini' else 'SAME',stop=('content_filter' if case=='content_filter' else 'end_turn') if case in ['content_filter','wrong_provider_stop'] and p=='openai' else None)
  if case=='corrupt_archives':
   for n,value in enumerate(['{broken','[]','null']):(d/f'old.superseded-{n}.json').write_text(value)
  try:
   build(d,out,'Sub99' if case=='missing_subject' else 'Sub01')
   results[case]={'accepted':True,'packet_items':len(json.loads((out/'packets/Sub01.json').read_text()))}
  except Exception as e:results[case]={'accepted':False,'exception':type(e).__name__,'message':str(e)}
with tempfile.TemporaryDirectory() as td:
 root=Path(td);a=root/'a';b=root/'b';a.mkdir();b.mkdir();out=root/'out'
 for p in providers:put(a,'Sub01',p);put(b,'Sub02',p)
 build(a,out,'Sub01');oldkey=(out/'answer_key_DO_NOT_SHARE.csv').read_text()
 build(b,out,'Sub02');currentkey=(out/'answer_key_DO_NOT_SHARE.csv').read_text()
 results['republish']={'current_packet_files':sorted(p.name for p in (out/'packets').glob('*.json')),'old_packet_archived':any(out.glob('packets.previous-*/Sub01.json')),'current_key_only_new_subject':'Sub02' in currentkey and 'Sub01' not in currentkey,'previous_key_preserved':any(p.read_text()==oldkey for p in out.rglob('*.csv')),'archive_contents':{p.name:sorted(x.name for x in p.iterdir()) for p in out.glob('packets.previous-*')}}
(O/'packaging_probes.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
