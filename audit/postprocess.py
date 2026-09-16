"""Supplementary-table cross-checks and audit figures after recompute.py.

Requires pypdf and matplotlib, and sources/VanCriekinge_2023_supplement.pdf.
"""
from pathlib import Path
import os, json, re, csv
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/gait-audit-matplotlib')
import numpy as np
from pypdf import PdfReader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parent; OUT=BASE/'outputs'
pdf=PdfReader(BASE/'sources/VanCriekinge_2023_supplement.pdf')
text='\n'.join(p.extract_text(extraction_mode='layout') for p in pdf.pages)
(BASE/'sources/VanCriekinge_2023_supplement.txt').write_text(text)
ages={int(n):int(age) for n,age in re.findall(r'SUBJ(\d+)\s+(\d+)\s+[MF]\s+',text.split('Supplementary Table 2.')[0])}
speeds=re.findall(r'(TVC\d+)\s+([\d.]+)\s+([\d.]+)',pdf.pages[-1].extract_text(extraction_mode='layout'))
orig=json.loads((OUT/'spatiotemporal_original.json').read_text()); comparison=[]
assert len(speeds)==50 and len(ages)==138
for i,(sid,pv,nv) in enumerate(speeds):
    for side,val in [('P',pv),('N',nv)]:
        a=next(r for r in orig if r['subject_id']==f'Sub{i+1:02d}' and r['side']==side)
        comparison.append(dict(subject=a['subject_id'],source_id=sid,side=side,computed=a['gait_speed_m_s'],published=float(val),difference=a['gait_speed_m_s']-float(val)))
with (OUT/'published_speed_comparison.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=comparison[0]);w.writeheader();w.writerows(comparison)
x=np.load(OUT/'curves.npz'); results={}
for muscle in ['ERS','GAS','BF']:
    for cohort,side in [('stroke','P'),('control','avg')]:
        curves=[x[k] for k in x.files if k.startswith(cohort+'_') and k.endswith('_'+side+'_'+muscle) and np.isfinite(x[k]).all()]
        results[cohort+'_'+muscle]={'n':len(curves),'fixed_0_2':int(sum(np.mean(c>.2)>=.95 for c in curves)),'relative_0_2_peak':int(sum(np.mean(c>.2*c.max())>=.95 for c in curves))}
(OUT/'readme_threshold_reproduction.json').write_text(json.dumps(results,indent=2))
sums=json.loads((OUT/'all_summaries.json').read_text()); ctrl=[s for s in sums if s['group']=='control'];valid=[s for s in ctrl if s['muscle_findings']]
facts={'control_ages_n':len(ages),'max_speed_abs_error':max(abs(r['difference']) for r in comparison),'controls_with_emg':len(valid),'controls_with_any_peak_z_over_2':sum(any(m['deviation_z_peak']>2 for m in s['muscle_findings']) for s in valid)}
facts['spotcheck']={}
for sid in ['Sub10','Sub49','Sub93','Sub98']:
    s=next(s for s in ctrl if s['subject_id']==sid)
    facts['spotcheck'][sid]={'age':ages[int(sid[3:])],'gps':s['gait_profile_score'],'gps_within_cohort_percentile':sum(t['gait_profile_score']<=s['gait_profile_score'] for t in ctrl)/len(ctrl)*100}
muscles=['GAS','RF','VL','BF','ST','TA','ERS']; joints=['AnkleAngles','KneeAngles','HipAngles','PelvisAngles']
# Exploratory age-only reference sensitivity, not a validated matched normative model.
old_ids=[sid for sid,age in ages.items() if age>=75 and sid!=10]
matched_gvs=[]
for joint in joints:
    mean=np.mean([x[f'control_Sub{sid:02d}_avg_{joint}'] for sid in old_ids],axis=0)
    matched_gvs.append(float(np.sqrt(np.mean((x[f'control_Sub10_avg_{joint}']-mean)**2))))
facts['Sub10_age_75plus_reference_sensitivity']={'n_reference':len(old_ids),'gvs':dict(zip(joints,matched_gvs)),'gps':float(np.sqrt(np.mean(np.array(matched_gvs)**2)))}
facts['readme_thresholds']=results
(OUT/'supplement_and_control_checks.json').write_text(json.dumps(facts,indent=2))
fig,ax=plt.subplots(2,2,figsize=(13,9),layout='constrained')
phase=np.linspace(0,100,1001)
for a,subject,muscle,title in [(ax[0,0],'Sub50','TA','Sub50 TA: later activation omitted'),(ax[0,1],'Sub05','GAS','Sub05 GAS: peak deviation is in omitted segment')]:
    c=x[f'stroke_{subject}_P_{muscle}'];a.plot(phase,c,label='Excel mean envelope',color='#126a92')
    a.axhline(.2,color='#b54545',ls='--',label='Pipeline threshold = 0.2')
    a.fill_between(phase,0,c,where=c>.2,color='#2c9987',alpha=.25,label='Above threshold')
    if subject=='Sub50':a.axvspan(0,7.09,alpha=.2,color='orange',label='Only interval sent to LLM')
    else:
        a.axvspan(24.98,37.76,alpha=.2,color='orange',label='Only interval sent to LLM');a.axvline(80.3,color='purple',ls=':',label='Peak |z| = 13.33')
    a.set(title=title,xlabel='Gait cycle (%)',ylabel='Normalized EMG',xlim=(0,100));a.legend(fontsize=8)
v=[s['gait_profile_score'] for s in ctrl];a=ax[1,0];a.hist(v,bins=20,color='#6698b1',edgecolor='white');a.axvline(facts['spotcheck']['Sub10']['gps'],color='#b54545',label='Sub10: 7.19 (81st percentile)');a.set(title='All 138 controls: same GPS-like calculation',xlabel='Four-variable RMS deviation (degrees)',ylabel='Participants');a.legend(fontsize=8)
z=list(csv.DictReader((OUT/'z_scores.csv').open())); a=ax[1,1]
rates=[100*np.mean([float(r['max_abs_z'])>2 for r in z if r['group']=='control' and r['muscle']==m]) for m in muscles]
a.bar(muscles,rates,color='#2c9987');a.set(title='Controls frequently exceed peak |z| > 2',ylabel='Control curves exceeding threshold (%)',ylim=(0,100));a.text(.03,.9,'109/109 controls with EMG exceed 2 in at least one muscle',transform=a.transAxes,fontsize=8)
fig.savefig(OUT/'audit_evidence.png',dpi=180);fig.savefig(OUT/'audit_evidence.pdf');plt.close(fig)
print(json.dumps(facts,indent=2))
