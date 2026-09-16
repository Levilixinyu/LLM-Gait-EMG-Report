from pathlib import Path
from io import BytesIO
from dataclasses import asdict
import sys,json,hashlib,collections,importlib.metadata as md
import numpy as np
P=Path('/Users/lixinyu/Desktop/LLM-Gait-EMG-Report');O=P/'audit/readiness';sys.path.insert(0,'/private/tmp/gait-readiness')
from src.features.data_types import NormalizedTrialData
from src.features.pipeline import build_normative_reference_from_normalized,extract_summary_from_normalized,to_prompt_text
from src.features.mat_spatiotemporal import build_spatiotemporal_lookup
original=json.loads((P/'audit/sha256_manifest.json').read_text());checks={}
for n in ['outputs/curves.npz','outputs/metadata.json','outputs/spatiotemporal_original.json']:
 checks[n]=hashlib.sha256((P/'audit'/n).read_bytes()).hexdigest()==original[n]
assert all(checks.values()),checks
x=np.load(BytesIO((P/'audit/outputs/curves.npz').read_bytes()));groups={}
for k in x.files:
 g,s,side,ch=k.split('_');groups.setdefault((g,s,side),{})[ch]=x[k]
trials=[NormalizedTrialData(s,g,side,{k:v for k,v in c.items() if k.endswith('Angles')},{k:v for k,v in c.items() if not k.endswith('Angles')}) for (g,s,side),c in groups.items()]
controls=[t for t in trials if t.group=='control'];norm=build_normative_reference_from_normalized(controls,source='main_cohort_excel');st=build_spatiotemporal_lookup(json.loads((P/'audit/outputs/spatiotemporal_original.json').read_text()))
summaries=[];counts={};examples={}
for t in trials:
 kw=st.get((t.subject_id,t.side),{}) if t.group=='stroke' else {}
 n=norm
 if t.group=='control':n=build_normative_reference_from_normalized([c for c in controls if c.subject_id!=t.subject_id],source='main_cohort_excel',method='leave_one_out',excluded_subjects=(t.subject_id,))
 a=extract_summary_from_normalized(t,n,**kw);json.dumps(asdict(a),allow_nan=False);summaries.append(a)
 key=f'{t.group}_{t.side}';counts.setdefault(key,collections.Counter())[sum(np.isfinite(v).all() for v in t.emg_norm.values())]+=1
 if (t.side=='P' and t.subject_id in ['Sub09','Sub05','Sub50','Sub47','Sub46']) or (t.group=='control' and t.subject_id=='Sub49'):
  text=to_prompt_text(a);(O/f'{t.group}_{t.subject_id}_{t.side}_input.txt').write_text(text);examples[f'{t.group}_{t.subject_id}_{t.side}']={'speed':a.gait_speed_m_s,'gps':a.gait_profile_score,'reference':a.reference_meta,'assistance_mentioned':any(z in text.lower() for z in ['holding hand','hands-on','physical support','assisted walking'])}
pilot=json.loads((P/'data/pilot_subset.json').read_text());dev={r['subject_id'] for r in pilot};complete={t.subject_id for t in trials if t.group=='stroke' and t.side=='P' and all(np.isfinite(v).all() for v in t.emg_norm.values())}
smoke=json.loads((P/'audit/outputs/sdk_smoke_check.json').read_text());pkgbad=[]
for line in (P/'requirements.lock.txt').read_text().splitlines():
 if '==' in line and not line.startswith('#'):
  name,v=line.split('==');got=md.version(name)
  if got!=v:pkgbad.append(name)
result={'verified_cache_hashes':checks,'summaries_strict_json':len(summaries),'channel_completeness':{k:{int(n):c for n,c in v.items()} for k,v in counts.items()},'pilot_n':len(dev),'pilot_complete_n':len(dev&complete),'complete_paretic_outside_18_development':sorted(complete-dev),'complete_paretic_outside_18_development_n':len(complete-dev),'examples':examples,'sdk_existing_artifact_all_pass':not smoke['failures'] and all(all(r['checks'].values()) for r in smoke['results'].values()),'installed_lock_mismatches':pkgbad,'report_counts':{d:len(list((P/'data'/d).glob('*.json'))) for d in ['reports','reports_control_spotcheck','reports_v2','reports_control_spotcheck_v2']}}
(O/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
