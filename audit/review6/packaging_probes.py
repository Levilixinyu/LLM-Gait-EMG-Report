"""Independent packaging checks; synthetic reports, temporary directories, no API."""
import sys,json,tempfile,contextlib,io,csv
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,'/private/tmp/gait-review6')
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
  return create_rating_packets(str(d),str(out),prompt_version='v2',expected_providers=providers,expected_tasks={(subject,p):task_hash(spec(subject,p)) for p in providers})
for case in ['valid','content_filter','wrong_provider_stop','corrupt_archives','mixed_input','missing_subject']:
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'reports';d.mkdir();out=Path(td)/'out'
  for p in providers:put(d,'Sub01',p,user='DIFFERENT' if case=='mixed_input' and p=='gemini' else 'SAME',stop=('content_filter' if case=='content_filter' else 'end_turn') if case in ['content_filter','wrong_provider_stop'] and p=='openai' else None)
  if case=='corrupt_archives':
   for n,value in enumerate(['{broken','[]','null']):(d/f'old.superseded-{n}.json').write_text(value)
  try:
   batch=build(d,out,'Sub99' if case=='missing_subject' else 'Sub01')
   results[case]={'accepted':True,'packet_items':len(json.loads((batch/'packets/Sub01.json').read_text()))}
  except Exception as e:results[case]={'accepted':False,'exception':type(e).__name__,'message':str(e)}
with tempfile.TemporaryDirectory() as td:
 import hashlib
 from unittest.mock import patch
 root=Path(td);a=root/'a';b=root/'b';a.mkdir();b.mkdir();out=root/'out'
 for p in providers:put(a,'Sub01',p);put(b,'Sub02',p)
 def hashes(d):return {str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in d.rglob('*') if p.is_file()}
 def aligned(d,subject):
  packets=[r for f in (d/'packets').glob('*.json') for r in json.loads(f.read_text())]
  with (d/'answer_key_DO_NOT_SHARE.csv').open() as fh:keys=list(csv.DictReader(fh))
  return len(packets)==len(keys)==3 and {r['anon_id'] for r in packets}=={r['anon_id'] for r in keys} and {r['subject_id'] for r in keys}=={subject}
 with patch('src.eval.blinding.time.strftime',return_value='20260916T000000Z'):
  first=build(a,out,'Sub01');before=hashes(first)
  second=build(b,out,'Sub02');third=build(b,out,'Sub02')
 results['independent_batches']={'three_unique_same_second_batches':len({first,second,third})==3,'first_batch_byte_identical':before==hashes(first),'all_keys_align':aligned(first,'Sub01') and aligned(second,'Sub02') and aligned(third,'Sub02'),'batch_components':sorted(p.name for p in first.iterdir()),'no_key_in_rater_packets':not any('answer_key' in p.name for d in [first,second,third] for p in (d/'packets').rglob('*'))}
 # Inject a write failure before publication: no incomplete final batch, old batches unchanged.
 previous={d.name:hashes(d) for d in out.iterdir()};original=Path.write_text
 def fail_manifest(self,*args,**kwargs):
  if self.name=='packaging_manifest.json':raise OSError('injected write failure')
  return original(self,*args,**kwargs)
 try:
  with patch.object(Path,'write_text',fail_manifest):build(b,out,'Sub02')
 except OSError:pass
 finals=[d for d in out.iterdir() if not d.name.endswith('.building')]
 results['publication_failure']={'no_new_final_batch':len(finals)==3,'old_batches_unchanged':all(previous[d.name]==hashes(d) for d in finals),'incomplete_staging_only':any(d.name.endswith('.building') for d in out.iterdir())}
(O/'packaging_probes.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
