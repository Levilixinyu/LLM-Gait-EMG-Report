"""Targeted remaining packaging checks, temp files only, no network."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,tempfile,contextlib,io
sys.path.insert(0,'/private/tmp/gait-review4')
from src.llm.generation_cache import TaskSpec,artifact_name,record_from_result,place_record
from src.eval.blinding import create_rating_packets
O=Path(__file__).resolve().parent;out={};providers={'anthropic','openai','gemini'}
def put(d,provider,user='SAME INPUT',stop=None):
 s=TaskSpec('Sub01','P',provider,'test-'+provider,'v2','SYSTEM',user)
 z=SimpleNamespace(text='REPORT '+provider,stop_reason=stop or {'anthropic':'end_turn','openai':'stop','gemini':'STOP'}[provider],truncated=False)
 p=d/artifact_name(s);place_record(p,record_from_result(s,z));return p
for case in ['non_success_stop','malformed_archive','mixed_input']:
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'reports';d.mkdir();dest=Path(td)/'packets'
  for p in sorted(providers):
   put(d,p,user='DIFFERENT INPUT' if case=='mixed_input' and p=='gemini' else 'SAME INPUT',stop='content_filter' if case=='non_success_stop' and p=='openai' else None)
  if case=='malformed_archive':
   p=next(d.glob('*anthropic*.json'));valid=json.loads(p.read_text());p.write_text('{broken json');place_record(p,valid)
  try:
   with contextlib.redirect_stdout(io.StringIO()):create_rating_packets(str(d),str(dest),prompt_version='v2',expected_providers=providers)
   out[case]={'packaged':True,'items':len(json.loads((dest/'packets/Sub01.json').read_text()))}
  except Exception as e:out[case]={'packaged':False,'exception':type(e).__name__,'message':str(e)}
# An old subject packet remains on a repeated build with fewer subjects.
with tempfile.TemporaryDirectory() as td:
 d=Path(td)/'reports';d.mkdir();dest=Path(td)/'out'
 for p in providers:put(d,p)
 create_rating_packets(str(d),str(dest),prompt_version='v2',expected_providers=providers)
 (dest/'packets/RemovedSubject.json').write_text('[{"anon_id":"R0001","report_text":"STALE"}]')
 create_rating_packets(str(d),str(dest),prompt_version='v2',expected_providers=providers)
 out['stale_output_packet_remains']=(dest/'packets/RemovedSubject.json').exists()
(O/'packaging_probes.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
