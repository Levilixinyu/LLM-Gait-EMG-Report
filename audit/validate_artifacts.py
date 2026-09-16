"""Checks saved reports, blinding, and known algorithm failure modes; no API calls."""
import sys, json, tempfile, csv, re, collections, copy
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.eval.blinding import _build_strip_patterns, _strip_identifying_tokens, create_rating_packets
from src.features.pipeline import build_normative_reference, extract_patient_summary
from tests.synthetic_data import make_synthetic_trial
OUT=ROOT/'audit/outputs'
results={};records=[]
for cohort in ['reports','reports_control_spotcheck']:
    for p in sorted((ROOT/'data'/cohort).glob('*.json')):
        r=json.loads(p.read_text());r['_file']=str(p.relative_to(ROOT));r['_cohort']=cohort;records.append(r)
results['report_count']=len(records)
results['report_keys']=sorted(set.intersection(*(set(r) for r in records)))
results['empty_reports']=[r['_file'] for r in records if not r['report_text'].strip()]
results['truncated_reports']=[r['_file'] for r in records if r.get('truncated')]
results['stop_reasons']={str(k):v for k,v in collections.Counter((r['provider'],r.get('stop_reason')) for r in records).items()}
results['length_by_provider']={p:{'n':len(v:=[len(r['report_text']) for r in records if r['provider']==p]),'median_chars':float(np.median(v)),'min_chars':min(v),'max_chars':max(v)} for p in ['anthropic','openai','gemini']}
key=list(csv.DictReader((ROOT/'data/rating_packets/answer_key_DO_NOT_SHARE.csv').open()))
packets={}
for f in (ROOT/'data/rating_packets/packets').glob('*.json'):
    for r in json.loads(f.read_text()): packets[r['anon_id']]=r
problems=[]
patterns=_build_strip_patterns(ROOT/'data/reports')
for row in key:
    source=ROOT/'data/reports'/Path(row['source_file']).name
    rec=json.loads(source.read_text());expected=_strip_identifying_tokens(rec['report_text'],patterns)
    if packets[row['anon_id']]['report_text']!=expected:problems.append(row['anon_id'])
results['packets']={'n_entries':len(packets),'n_answer_key_rows':len(key),'text_mismatches':problems,'packet_entry_keys':list(next(iter(packets.values())))}
results['identity_tokens_in_reports']=[r['_file'] for r in records if re.search(r'\b(?:claude|gemini|gpt|openai|anthropic)\b',r['report_text'],re.I)]
with tempfile.TemporaryDirectory() as td:
    d=Path(td)
    rs=[dict(subject_id='S',provider=p,model=m,report_text=m,prompt_version='v1') for p,m in [('anthropic','claude-opus-5'),('openai','gpt-6-astra'),('gemini','gemini-3.1-pro-preview')]]
    for label, seq in [('forward',rs),('reverse',rs[::-1])]:
        rd=d/label;rd.mkdir()
        for r in seq:(rd/(r['provider']+'.json')).write_text(json.dumps(r))
        create_rating_packets(str(rd),str(d/(label+'_out')),seed=42)
    results['blinding_redaction_examples']={r['model']:_strip_identifying_tokens(r['model'],_build_strip_patterns(d/'forward')) for r in rs}
    def order(label):
        return [r['provider'] for r in csv.DictReader((d/(label+'_out')/'answer_key_DO_NOT_SHARE.csv').open())]
    results['same_seed_different_directory_order']={'forward':order('forward'),'reverse':order('reverse')}
control=[make_synthetic_trial(f'C{i}',group='control',seed=i) for i in range(5)]
trial=make_synthetic_trial('S',seed=100)
norm=build_normative_reference(control)
a=extract_patient_summary(trial,norm)
scaled=copy.deepcopy(trial);scaled.emg={k:v*10 for k,v in scaled.emg.items()}
b=extract_patient_summary(scaled,norm)
results['raw_path_amplitude_scale_test']=[{'muscle':x.muscle,'original_z':x.deviation_z_peak,'tenfold_amplitude_z':y.deviation_z_peak,'original_peak_normalized':x.peak_amplitude_norm,'scaled_peak_normalized':y.peak_amplitude_norm} for x,y in zip(a.muscle_findings,b.muscle_findings)]
(OUT/'artifact_checks.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
# All candidate excerpts are navigation aids, not automatic clinical error labels.
terms=['absence','absent','swing','severe','moderate','correlat','amplitude','normaliz','lower than','control','symmetr','spastic','contracture']
excerpts=[]
for r in records:
    lines=[line for line in r['report_text'].splitlines() if any(t in line.lower() for t in terms)]
    excerpts.append({'file':r['_file'],'sentences':lines})
(OUT/'report_review_excerpts.json').write_text(json.dumps(excerpts,indent=2,ensure_ascii=False))
print(json.dumps(results,indent=2,ensure_ascii=False))
