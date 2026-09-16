"""Exercise real generation entrypoints with fake providers/loaders; no network/data mutation."""
import sys,json,tempfile,importlib.util,contextlib,io
from pathlib import Path
from types import SimpleNamespace
import numpy as np
S=Path('/private/tmp/gait-review3');sys.path.insert(0,str(S));O=Path(__file__).resolve().parent
from src.features.data_types import NormalizedTrialData
controls=[NormalizedTrialData(f'C{i}','control','avg',{'AnkleAngles':np.linspace(i,20+i,1001)},{'TA':np.linspace(.1+i*.02,.8,1001)}) for i in range(3)]
patient=NormalizedTrialData('S01','stroke','P',{'AnkleAngles':np.linspace(0,30,1001)},{'TA':np.linspace(.1,1,1001)})
results={}
for script in ['generate_pilot_reports','generate_control_spotcheck']:
 spec=importlib.util.spec_from_file_location(script,S/'scripts'/f'{script}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 calls=[];refs=[]
 class Fake:
  def __init__(self,name):self.name=name;self.model='fake-'+name;self.max_tokens=8000
  def generate(self,system,user):
   calls.append((self.name,user));return SimpleNamespace(text='Valid '+self.name,stop_reason={'anthropic':'end_turn','openai':'stop','gemini':'STOP'}[self.name],truncated=False,response_model='snapshot',request_id='fake',usage={'tokens':1})
 for cls,name in [('AnthropicProvider','anthropic'),('OpenAIProvider','openai'),('GeminiProvider','gemini')]:setattr(m,cls,lambda n=name:Fake(n))
 m.build_code_manifest=lambda ps:{'source':'fixed'};m.build_data_manifest=lambda ps:{'data':'fixed'}
 m.load_control_excel=lambda p:controls
 original=m.build_normative_reference_from_normalized
 def capture(ts):refs.append([t.subject_id for t in ts]);return original(ts)
 m.build_normative_reference_from_normalized=capture
 with tempfile.TemporaryDirectory() as td:
  m.ROOT=Path(td);(m.ROOT/'data').mkdir();m.OUT_DIR=m.ROOT/'data'/'v2';m.N_SUBJECTS=1
  if script=='generate_pilot_reports':
   (m.ROOT/'data/pilot_subset.json').write_text(json.dumps([{'subject_id':'S01','side':'P'}]));m.load_stroke_excel=lambda p:[patient];m.load_stroke_spatiotemporal=lambda p:[];m.build_spatiotemporal_lookup=lambda _:{}
  with contextlib.redirect_stdout(io.StringIO()):m.main();first_calls=len(calls);m.main()
  records=[json.loads(p.read_text()) for p in m.OUT_DIR.glob('*.json')]
  results[script]={'first_calls':first_calls,'second_run_additional_calls':len(calls)-first_calls,'records':len(records),'versions':[r['prompt_version'] for r in records],'reference_ids':[r['reference_id'] for r in records],'reference_members':refs,'subjects':[r['subject_id'] for r in records]}
(O/'entrypoint_checks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
