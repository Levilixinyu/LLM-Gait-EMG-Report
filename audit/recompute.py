"""Read-only audit of the original experiment; writes only to audit/outputs.

Run from the project root with numpy/scipy/openpyxl/h5py installed:
    python audit/recompute.py
No provider imports, API calls, or modifications to experiment data.
"""
from pathlib import Path
import sys, json, csv, warnings, hashlib, collections, random
import numpy as np
import h5py

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.features.figshare_loader import load_stroke_excel, load_control_excel
from src.features.pipeline import build_normative_reference_from_normalized, extract_summary_from_normalized, to_json, to_prompt_text
from src.features.mat_spatiotemporal import load_stroke_spatiotemporal, build_spatiotemporal_lookup
from src.features.emg_signal import onset_offset_pct_from_cycle, co_contraction_index
from src.features.spatiotemporal import symmetry_index, classify_ambulation

OUT = ROOT / 'audit/outputs'
OUT.mkdir(parents=True, exist_ok=True)

def save(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False))

def csvout(name, rows):
    if rows:
        with (OUT/name).open('w', newline='') as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def windows(c, threshold=.2):
    above=c>threshold
    changes=np.diff(np.r_[False,above,False].astype(int))
    starts=np.flatnonzero(changes==1); ends=np.flatnonzero(changes==-1)
    return [(int(a),int(b)) for a,b in zip(starts,ends) if b-a>=max(1,int(.03*len(c)))]

print('Loading all 188 Excel subject sheets', flush=True)
controls=load_control_excel(str(ROOT/'data/raw/AbleBodiedAdults.xlsx'))
stroke=load_stroke_excel(str(ROOT/'data/raw/PostStrokeAdults.xlsx'))
norm=build_normative_reference_from_normalized(controls)
pilot=json.loads((ROOT/'data/pilot_subset.json').read_text())
pids={r['subject_id'] for r in pilot}
print('Excel loaded; computing quality, burst, normative metrics', flush=True)
quality=[]; bursts=[]; zs=[]; summaries=[]
mat_path=ROOT/'data/raw/MAT_normalizedData_PostStrokeAdults.mat'
st_records=load_stroke_spatiotemporal(str(mat_path)); lookup=build_spatiotemporal_lookup(st_records)
save('spatiotemporal_original.json',st_records)
for t in controls+stroke:
    s=extract_summary_from_normalized(t,norm,**lookup.get((t.subject_id,t.side),{}))
    summaries.append(to_json(s))
    for kind, curves in [('emg',t.emg_norm),('kinematic',t.joint_angles)]:
        for name,c in curves.items():
            quality.append(dict(group=t.group,subject=t.subject_id,side=t.side,kind=kind,channel=name,n=len(c),nan=int(np.isnan(c).sum()),infinite=int(np.isinf(c).sum())))
            if kind!='emg' or not np.isfinite(c).all(): continue
            win=windows(c); rel=windows(c,.2*c.max())
            first=onset_offset_pct_from_cycle(c)
            bursts.append(dict(group=t.group,subject=t.subject_id,side=t.side,muscle=name,pilot=t.subject_id in pids and t.side=='P',peak=float(c.max()),n_bursts=len(win),intervals_pct=str([(round(a/len(c)*100,2),round(b/len(c)*100,2)) for a,b in win]),first_onset=first[0],first_offset=first[1],total_above_pct=float(np.mean(c>.2)*100),boundary_active=bool(c[0]>.2 and c[-1]>.2),relative_peak_onset_changed=win!=rel,relative_peak_intervals=str(rel)))
            mean,sd=norm['emg'][name]; z=(c-mean)/sd; k=int(np.argmax(abs(z)))
            loo=None
            if t.group=='control':
                ref=np.array([x.emg_norm[name] for x in controls if x.subject_id!=t.subject_id])
                loo=float(np.max(abs((c-np.nanmean(ref,axis=0))/np.nanstd(ref,axis=0))))
            zs.append(dict(group=t.group,subject=t.subject_id,side=t.side,muscle=name,max_abs_z=float(abs(z[k])),signed_z_at_peak=float(z[k]),peak_phase_pct=k/(len(c)-1)*100,patient_at_peak=float(c[k]),norm_mean_at_peak=float(mean[k]),norm_sd_at_peak=float(sd[k]),cycle_over_2sd_pct=float(np.mean(abs(z)>2)*100),loo_max_abs_z=loo))
save('all_summaries.json',summaries);csvout('data_quality.csv',quality);csvout('activation_windows.csv',bursts);csvout('z_scores.csv',zs)
(OUT/'pilot_inputs.txt').write_text('\n\n'.join(to_prompt_text(extract_summary_from_normalized(t,norm,**lookup[(t.subject_id,'P')])) for t in stroke if t.side=='P' and t.subject_id in pids))
norm_stats={}
for name in norm['emg']:
    vals=[r['max_abs_z'] for r in zs if r['group']=='control' and r['muscle']==name]
    loo=[r['loo_max_abs_z'] for r in zs if r['group']=='control' and r['muscle']==name]
    norm_stats[name]=dict(n=len(vals),n_over_2=int(np.sum(np.array(vals)>2)),n_over_3=int(np.sum(np.array(vals)>3)),n_over_4=int(np.sum(np.array(vals)>4)),z_quantiles=np.quantile(vals,[.5,.9,.95,.99]).tolist(),loo_z_quantiles=np.quantile(loo,[.5,.9,.95,.99]).tolist())
for pair in [('TA','GAS'),('RF','BF')]:
    vals=[co_contraction_index(t.emg_norm[pair[0]],t.emg_norm[pair[1]]) for t in controls if all(np.isfinite(t.emg_norm[m]).all() for m in pair)]
    norm_stats['_CCI_'+'_'.join(pair)]=dict(n=len(vals),quantiles=np.quantile(vals,[.025,.5,.975]).tolist())
cs=[s for s in summaries if s['group']=='control']
norm_stats['_gps_control_quantiles']=np.quantile([s['gait_profile_score'] for s in cs],[.025,.5,.95,.975,.99]).tolist()
save('normative_calibration.json',norm_stats)

print('Auditing MAT identity, Excel averaging, event and step definitions',flush=True)
identity=[]; matches=[]; steps=[]; eventissues=[]; metadata=[]
with h5py.File(mat_path,'r') as f:
    sub=f['Sub']
    def arr(g,k): return np.asarray(g[k]).ravel()
    for i in range(50):
        sid=f'Sub{i+1:02d}'; md={'subject':sid}
        for field in sub:
            if field not in ['name','Name','ID','sub_char','meas_char']: continue
            g=f[sub[field][i,0]]
            if isinstance(g,h5py.Dataset):
                if g.dtype.kind in 'ui': md[field]=''.join(chr(int(x)) for x in np.asarray(g).ravel())
            elif field=='sub_char':
                for k in g:
                    if isinstance(g[k],h5py.Dataset) and g[k].dtype.kind in 'fiu' and g[k].size==1: md[k]=float(arr(g,k)[0])
        metadata.append(md)
        ev=f[sub['events'][i,0]]
        for side,ownkey,otherkey in [('P','PsideSegm_PsideData','PsideSegm_NsideData'),('N','NsideSegm_NsideData','NsideSegm_PsideData')]:
            t=next(t for t in stroke if t.subject_id==sid and t.side==side)
            own=f[sub[ownkey][i,0]]; other=f[sub[otherkey][i,0]]
            for kind,curves in [('emg',t.emg_norm),('joint',t.joint_angles)]:
                for name,c in curves.items():
                    key=name+'norm' if kind=='emg' else name
                    dims=own[key]; axis='n' if kind=='emg' else 'x'
                    raw=np.asarray(dims[axis])
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore',RuntimeWarning); avg=np.nanmean(raw,axis=0)
                    same=bool(np.allclose(avg,c,equal_nan=True))
                    finite=np.isfinite(avg)&np.isfinite(c)
                    diff=float(np.max(abs(avg[finite]-c[finite]))) if finite.any() else None
                    matches.append(dict(subject=sid,side=side,channel=name,strides=raw.shape[0],equal=same,max_abs_difference=diff))
            start=arr(ev,side+'_ICstart');end=arr(ev,side+'_ICstop');cnt=arr(ev,side+'_IC_cnt')
            x=np.asarray(own['HEE']['x']); y=np.asarray(other['HEE']['x'])
            with np.errstate(invalid='ignore',divide='ignore'):frac=(cnt-start)/(end-start)
            mask=np.isfinite(frac)&np.isfinite(x[:,-1]-x[:,0])&((end-start)>0)
            idx=np.round(np.clip(frac[mask],0,1)*1000).astype(int); a=x[mask]; b=y[mask]; n=np.arange(len(idx))
            old=np.abs(b[n,idx]-a[:,0])/1000
            simultaneous=np.abs(b[n,idx]-a[n,idx])/1000
            signed=(b[n,idx]-a[n,idx])*np.sign(a[:,-1]-a[:,0])/1000
            startstep=np.abs(a[:,0]-b[:,0])/1000
            stride=np.abs(a[:,-1]-a[:,0])/1000
            steps.append(dict(subject=sid,side=side,n=len(idx),old_step_m=float(old.mean()),simultaneous_step_m=float(simultaneous.mean()),signed_step_m=float(signed.mean()),mean_heel_motion_mm=float(np.mean(abs(a[n,idx]-a[:,0]))),max_heel_motion_mm=float(np.max(abs(a[n,idx]-a[:,0]))),negative_steps=int(np.sum(signed<0)),closure_old_mean_abs_m=float(np.mean(abs(stride-startstep-old)))))
            issue={'subject':sid,'side':side,'n':len(start),'invalid_duration':int(np.sum(end<=start)),'cnt_outside':int(np.sum((frac<0)|(frac>1))),'cnt_missing':int(np.sum(~np.isfinite(cnt)))}
            if side+'_IC_cntnorm' in ev:
                cn=arr(ev,side+'_IC_cntnorm')[mask]
                issue['max_index_difference_vs_published']=float(np.nanmax(abs(idx-(cn-1))))
            if side+'_TOnorm' in ev:
                toe=arr(ev,side+'_TOnorm'); finite=toe[np.isfinite(toe)]
                issue['toe_off_mean_pct']=float(np.mean((finite-1)/10)) if len(finite) else None
            eventissues.append(issue)
csvout('mat_excel_comparison.csv',matches);csvout('step_definition_comparison.csv',steps);save('metadata.json',metadata);save('event_checks.json',eventissues)
sym=[]
for sid in sorted({r['subject'] for r in steps}):
    p=next(r for r in steps if r['subject']==sid and r['side']=='P');n=next(r for r in steps if r['subject']==sid and r['side']=='N')
    a=symmetry_index(n['old_step_m'],p['old_step_m']);b=symmetry_index(n['simultaneous_step_m'],p['simultaneous_step_m'])
    sym.append(dict(subject=sid,pilot=sid in pids,original_si=a,simultaneous_si=b,difference_pp=b-a))
csvout('symmetry_comparison.csv',sym)

rows=[]
for t in stroke:
    if t.side!='P': continue
    speed=lookup[(t.subject_id,'P')]['gait_speed_m_s']
    rows.append(dict(subject_id=t.subject_id,side='P',gait_speed_m_s=speed,category=classify_ambulation(speed),n_valid_muscles=sum(not np.isnan(c).all() for c in t.emg_norm.values())))
rng=random.Random(42); selected=[]
for cat in ['household ambulator (<0.4 m/s)','limited community ambulator (0.4-0.8 m/s)','full community ambulator (>0.8 m/s)']:
    complete=[r for r in rows if r['category']==cat and r['n_valid_muscles']==7]; incomplete=[r for r in rows if r['category']==cat and r['n_valid_muscles']<7]
    rng.shuffle(complete);rng.shuffle(incomplete);selected.extend(complete[:5 if incomplete else 6]+incomplete[:1])
selected.sort(key=lambda r:r['gait_speed_m_s'])
facts=dict(n_controls=len(controls),n_stroke_sides=len(stroke),all_excel_mat_curves_match=all(r['equal'] for r in matches),compared_curves=len(matches),partial_nan_curves=sum(0<r['nan']<r['n'] for r in quality),infinite_values=sum(r['infinite'] for r in quality),pilot_reproduced=selected==pilot)
for label, subset in [('all',bursts),('pilot',[r for r in bursts if r['pilot']]),('control',[r for r in bursts if r['group']=='control'])]:
    facts[label+'_valid_emg_curves']=len(subset)
    facts[label+'_multiple_bursts']=sum(r['n_bursts']>1 for r in subset)
    facts[label+'_boundary_active']=sum(r['boundary_active'] for r in subset)
    facts[label+'_threshold_semantics_changed']=sum(r['relative_peak_onset_changed'] for r in subset)
save('audit_facts.json',facts)
np.savez_compressed(OUT/'curves.npz',**{f'{t.group}_{t.subject_id}_{t.side}_{m}':c for t in controls+stroke for m,c in {**t.emg_norm,**t.joint_angles}.items()})
print(json.dumps(facts,indent=2),flush=True)
print('Audit numerical outputs written:',OUT,flush=True)
