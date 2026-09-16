"""Independent local review probes. No provider imports or API calls.
Run against the source snapshot made in /private/tmp/gait-review2.
"""
from pathlib import Path
import sys,ast,json,hashlib,copy,tempfile
import numpy as np
S=Path('/private/tmp/gait-review2');sys.path.insert(0,str(S))
from src.features.emg_signal import analyze_activation
from src.features.pipeline import extract_patient_summary,build_normative_reference,to_prompt_text,extract_summary_from_normalized,build_normative_reference_from_normalized
from src.features.data_types import NormalizedTrialData
from tests.synthetic_data import make_synthetic_trial
O=Path(__file__).resolve().parent;out={}
# Existing suite only checks finite interval endpoints for partial NaN. Inspect full summary.
c=np.zeros(1001);c[100:400]=1;c[200:220]=np.nan
trial=NormalizedTrialData('partial','stroke','P',{'AnkleAngles':np.zeros(1001)}, {'TA':c,'GAS':np.ones(1001)})
summary=extract_summary_from_normalized(trial)
out['partial_nan']={'profile':analyze_activation(c).__dict__,'cci':summary.cci_findings,'missing_warning_in_text':'missing' in to_prompt_text(summary,False).lower()}
try:json.dumps(summary.__dict__,default=lambda x:x.__dict__,allow_nan=False);out['partial_nan']['strict_json_ok']=True
except ValueError:out['partial_nan']['strict_json_ok']=False
ctl=[make_synthetic_trial(f'C{i}',group='control',seed=i) for i in range(5)];norm=build_normative_reference(ctl);t=make_synthetic_trial('S',seed=100);b=copy.deepcopy(t);b.emg={m:x*10 for m,x in b.emg.items()}
a=extract_patient_summary(t,norm);bb=extract_patient_summary(b,norm);text=to_prompt_text(a)
out['raw_scaling']=[{'muscle':x.muscle,'z1':x.deviation_z_peak,'z10':y.deviation_z_peak,'relative_difference':abs(x.deviation_z_peak-y.deviation_z_peak)/max(abs(x.deviation_z_peak),1e-12)} for x,y in zip(a.muscle_findings,bb.muscle_findings)]
out['raw_prompt_reference_mismatch']={'actual_reference_subjects':5,'actual_reference_points':len(next(iter(norm['emg'].values()))[0]),'actual_joint_count':len(a.joint_findings),'says_138':'138 subjects' in text,'says_1001':'1001 phase points' in text,'says_four':'4 sagittal channels' in text}
# Execute only the two pure helper functions from the generation script's AST.
path=S/'scripts/generate_pilot_reports.py';tree=ast.parse(path.read_text());ns={'Path':Path,'hashlib':hashlib,'json':json,'PROMPT_VERSION':'v2','SYSTEM_PROMPT':'test','_FEATURE_SOURCES':[S/f'src/features/{n}.py' for n in ['emg_signal','pipeline','figshare_loader','mat_spatiotemporal']]+[S/'src/llm/prompt_templates.py']}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['_config_hash','_existing_record_valid']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
h0=ns['_config_hash']('same-model');checks={}
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'record.json'
 for name,record in [('wrong_subject_and_input',{'config_hash':h0,'subject_id':'WRONG','user_prompt':'OUTDATED INPUT','report_text':'old result','truncated':False,'stop_reason':'stop'}),('missing_status_whitespace',{'config_hash':h0,'report_text':'   '})]:
  p.write_text(json.dumps(record));checks[name]=ns['_existing_record_valid'](p,h0)
for rel in ['src/llm/providers.py','src/features/kinematic.py','src/features/spatiotemporal.py']:
 p=S/rel;orig=p.read_bytes()
 try:
  p.write_bytes(orig+b'\n# independently changed configuration/algorithm\n');checks['hash_unchanged_when_'+rel]=ns['_config_hash']('same-model')==h0
 finally:p.write_bytes(orig)
out['cache_validation']=checks
# False positive in the acceptance script: any wrapped interval passes even without target overlap.
ivs=[(95,5)];expect=(74,87)
hit=any((a<=expect[1] and b>=expect[0]) if a<=b else (a<=expect[1] or b>=expect[0]) for a,b in ivs) and len(ivs)>=2 or any(a>b for a,b in ivs)
out['acceptance_false_positive']={'intervals':ivs,'expected':expect,'reported_hit':hit,'actual_overlap':False}
# Probe min-duration endpoint convention, without declaring it a main blocker.
c=np.zeros(1001);c[100:130]=1
out['min_duration_boundary']={'configured_min_pct':3,'intervals':analyze_activation(c).intervals}
(O/'probes.json').write_text(json.dumps(out,indent=2,allow_nan=True));print(json.dumps(out,indent=2))
