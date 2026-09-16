"""Third-round independent probes. All artifacts go to temporary/audit paths; no APIs."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from io import BytesIO
import sys,json,tempfile,ast
import numpy as np
S=Path('/private/tmp/gait-review3');sys.path.insert(0,str(S));O=Path(__file__).resolve().parent;R=O.parents[1]
from src.llm.generation_cache import TaskSpec,artifact_name,place_record,record_from_result,existing_record_valid
from src.eval.blinding import create_rating_packets
from src.features.pipeline import build_normative_reference_from_normalized,extract_summary_from_normalized,to_prompt_text,build_normative_reference,extract_patient_summary
from src.features.data_types import NormalizedTrialData
from src.llm.providers import extract_openai_metadata
from tests.synthetic_data import make_synthetic_trial
out={}
def spec():return TaskSpec('Sub01','P','anthropic','model-test','v2','SYS','INPUT')
def result(text,stop='end_turn',truncated=False):return SimpleNamespace(text=text,stop_reason=stop,truncated=truncated)
with tempfile.TemporaryDirectory() as td:
 d=Path(td);reports=d/'reports';reports.mkdir();p=reports/artifact_name(spec())
 place_record(p,record_from_result(spec(),result('OLD_INVALID_TRUNCATED','max_tokens',True)))
 place_record(p,record_from_result(spec(),result('NEW_VALID')))
 create_rating_packets(str(reports),str(d/'packets'))
 entries=json.loads((d/'packets/packets/Sub01.json').read_text())
 out['superseded_in_blinding']={'expected_current_reports':1,'actual_packet_entries':len(entries),'texts':[r['report_text'] for r in entries]}
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/artifact_name(spec())
 with patch('src.llm.generation_cache.time.strftime',return_value='20260916T160000Z'):
  for text in ['FIRST','SECOND','THIRD']:place_record(p,record_from_result(spec(),result(text)))
 files=list(Path(td).glob('*.json'));out['same_second_archive_collision']={'writes':3,'preserved_files':len(files),'texts':[json.loads(f.read_text())['report_text'] for f in files]}
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/artifact_name(spec());p.write_text('[]')
 try:out['non_object_json_validation']={'returns':existing_record_valid(p,spec())}
 except Exception as e:out['non_object_json_validation']={'exception':type(e).__name__}
# Generic normalized reference still falsely classified as main-cohort.
cs=[NormalizedTrialData('C'+str(i),'control','avg',{'AnkleAngles':np.linspace(i,i+20,101)},{'TA':np.linspace(.1+i*.1,1,101)}) for i in range(3)]
n=build_normative_reference_from_normalized(cs);a=extract_summary_from_normalized(cs[0],n);txt=to_prompt_text(a)
out['normalized_reference_mislabel']={'actual_n':3,'actual_points':101,'source_label':a.reference_source,'claims_138':'138 subjects' in txt,'claims_1001':'1001 phase points' in txt}
ctl=[make_synthetic_trial(f'C{i}',group='control',seed=i) for i in range(5)];a=extract_patient_summary(make_synthetic_trial('S',seed=100),build_normative_reference(ctl));txt=to_prompt_text(a)
out['raw_reference_fixed']={'source_label':a.reference_source,'claims_138':'138 subjects' in txt,'claims_1001':'1001 phase points' in txt}
c=np.zeros(1001);c[100:400]=1;c[200:220]=np.nan
s=extract_summary_from_normalized(NormalizedTrialData('partial','stroke','P',{'AnkleAngles':np.zeros(1001)},{'TA':c,'GAS':np.ones(1001)}));json.dumps(s.__dict__,default=lambda a:a.__dict__,allow_nan=False)
out['partial_nan_fixed']={'cci':s.cci_findings,'quality_warning':'DATA QUALITY' in to_prompt_text(s),'strict_json_ok':True}
out['openai_ids']=extract_openai_metadata(SimpleNamespace(model='M',id='chatcmpl-RESPONSE',_request_id='req-REQUEST',usage=None))
# Exact interval helper in acceptance script (AST extracted; do not run its main).
tree=ast.parse((S/'scripts/audit_fix_verification.py').read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='interval_covers');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'interval-helper','exec'),ns)
out['interval_false_positive_fixed']=not ns['interval_covers']((95,5),(74,87))
# Actual released curves previously fully checked against MAT/Excel.
x=np.load(BytesIO((R/'audit/outputs/curves.npz').read_bytes()));groups={}
for k in x.files:
 g,s,side,ch=k.split('_');groups.setdefault((g,s,side),{})[ch]=x[k]
trials=[NormalizedTrialData(s,g,side,{k:v for k,v in c.items() if k.endswith('Angles')},{k:v for k,v in c.items() if not k.endswith('Angles')}) for (g,s,side),c in groups.items()];controls=[t for t in trials if t.group=='control'];norm=build_normative_reference_from_normalized(controls)
bad=[];examples={}
for t in trials:
 a=extract_summary_from_normalized(t,norm)
 try:json.dumps(a.__dict__,default=lambda a:a.__dict__,allow_nan=False)
 except ValueError:bad.append(a.subject_id)
 if t.side=='P' and t.subject_id in ['Sub08','Sub46','Sub47','Sub48','Sub50','Sub05']:
  text=to_prompt_text(a);examples[t.subject_id]=[l for l in text.splitlines() if 'No valid EMG' in l or 'NO usable' in l or l.startswith(('- TA:','- GAS:'))]
out['real_curves']={'n':len(trials),'strict_json_failures':bad,'examples':examples}
t=next(t for t in controls if t.subject_id=='Sub10');loo=[c for c in controls if c.subject_id!=t.subject_id];s=extract_summary_from_normalized(t,build_normative_reference_from_normalized(loo));txt=to_prompt_text(s);(O/'Sub10_LOO_input.txt').write_text(txt)
out['loo_reference_text']={'actual_kinematic_n':len(loo),'source_label':s.reference_source,'claims_138':'138 subjects' in txt,'mentions_LOO_method_as_actual_reference':'leave-one-out reference' in txt.lower(),'gps':s.gait_profile_score}
(O/'probes.json').write_text(json.dumps(out,indent=2,allow_nan=False));print(json.dumps(out,indent=2))
