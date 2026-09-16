"""Recheck v2 against the previously verified full released-curve snapshot; no APIs."""
from pathlib import Path
from io import BytesIO
import sys,json
import numpy as np
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/gait-review2')
from src.features.data_types import NormalizedTrialData
from src.features.pipeline import build_normative_reference_from_normalized,extract_summary_from_normalized,to_prompt_text
from src.features.emg_signal import analyze_activation
x=np.load(BytesIO((R/'audit/outputs/curves.npz').read_bytes()))
groups={}
for k in x.files:
 g,s,side,ch=k.split('_');groups.setdefault((g,s,side),{})[ch]=x[k]
trials=[NormalizedTrialData(s,g,side,{k:v for k,v in cs.items() if k.endswith('Angles')},{k:v for k,v in cs.items() if not k.endswith('Angles')}) for (g,s,side),cs in groups.items()]
controls=[t for t in trials if t.group=='control'];norm=build_normative_reference_from_normalized(controls)
out={'n_summaries':len(trials),'strict_json_failures':[],'target_cases':{},'threshold_counts':{},'calibration':{}}
for t in trials:
 s=extract_summary_from_normalized(t,norm)
 try:json.dumps(s.__dict__,default=lambda x:x.__dict__,allow_nan=False)
 except ValueError:out['strict_json_failures'].append(s.subject_id)
 if t.side=='P' and t.subject_id in ['Sub50','Sub05','Sub46','Sub47']:
  text=to_prompt_text(s);(O/(t.subject_id+'_input.txt')).write_text(text)
  out['target_cases'][t.subject_id]={'muscles':[m.muscle for m in s.muscle_findings],'lines':[l for l in text.splitlines() if l.startswith(('- TA:','- GAS:','- ERS:','No valid EMG'))]}
for m in ['ERS','GAS','BF']:
 for g,ts in [('controls',controls),('stroke_P',[t for t in trials if t.group=='stroke' and t.side=='P'])]:
  cs=[t.emg_norm[m] for t in ts if np.isfinite(t.emg_norm[m]).all()]
  out['threshold_counts'][m+'_'+g]={'n':len(cs),'relative':sum(analyze_activation(c).above_threshold_pct>=95 for c in cs),'fixed':sum(analyze_activation(c,threshold_frac=.2/float(c.max())).above_threshold_pct>=95 for c in cs)}
for m in ['GAS','RF','VL','BF','ST','TA','ERS']:
 cs=np.array([t.emg_norm[m] for t in controls if np.isfinite(t.emg_norm[m]).all()]);zs=np.max(abs((cs-cs.mean(0))/cs.std(0)),axis=1);loo=[]
 for i,c in enumerate(cs):
  other=np.delete(cs,i,0);loo.append(float(np.max(abs((c-other.mean(0))/other.std(0)))))
 out['calibration'][m]={'n':len(cs),'p95':float(np.quantile(zs,.95)),'loo_p95':float(np.quantile(loo,.95))}
(O/'real_curve_checks.json').write_text(json.dumps(out,indent=2,allow_nan=False));print(json.dumps(out,indent=2))
