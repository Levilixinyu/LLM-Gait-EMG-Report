"""Main-dataset suitability checks; reads released files and prior audit outputs, no APIs."""
from pathlib import Path
import json,csv,re,collections
import numpy as np
import h5py
B=Path(__file__).resolve().parent;O=B/'outputs';R=B.parent
quality=list(csv.DictReader((O/'data_quality.csv').open()))
meta=json.loads((O/'metadata.json').read_text());ages=json.loads((O/'control_ages.json').read_text())
text=(B/'sources/VanCriekinge_2023_supplement.txt').read_text()
sp=text.split('Supplementary table 5.')[1]
ctrl_speed={int(s):(float(l)+float(r))/2 for s,l,r in re.findall(r'SUBJ(\d+)\s+([\d.]+)\s+([\d.]+)',sp)}
stroke_speed=re.findall(r'(TVC\d+)\s+([\d.]+)\s+([\d.]+)',sp)
assert len(ctrl_speed)==138 and len(stroke_speed)==50
idmap={f'Sub{i+1:02d}':s for i,(s,p,n) in enumerate(stroke_speed)}
result={};complete={};validcounts={}
for group,side in [('control','avg'),('stroke','P'),('stroke','N')]:
 rows=[r for r in quality if r['group']==group and r['side']==side]
 counts=collections.Counter(r['subject'] for r in rows if r['kind']=='emg' and int(r['nan'])==0)
 ids=sorted(set(r['subject'] for r in rows));key=f'{group}_{side}';validcounts[key]=counts
 complete[key]=[s for s in ids if counts[s]==7]
 result[key]={'n_subjects':len(ids),'valid_emg_channel_count_distribution':dict(sorted(collections.Counter(counts[s] for s in ids).items())),'complete_emg_ids':complete[key],'no_emg_ids':[s for s in ids if counts[s]==0],'partial_emg':{s:counts[s] for s in ids if 0<counts[s]<7},'missing_kinematic_curves':sum(int(r['nan'])>0 for r in rows if r['kind']=='kinematic')}
result['stroke_both_sides_complete_n']=len(set(complete['stroke_P'])&set(complete['stroke_N']))
result['clinical_summary']={k:dict(min=float(min(v:=[r[k] for r in meta])),median=float(np.median(v)),max=float(max(v))) for k in ['Age','TPS','FAC','TIS','POMA']}
result['FAC_counts']=dict(collections.Counter(int(r['FAC']) for r in meta))
result['TIS_ge_20']=[dict(subject=r['subject'],source_id=idmap[r['subject']],TIS=r['TIS']) for r in meta if r['TIS']>=20]
result['assistance_source_ids']=['TVC48','TVC51','TVC54']
result['assistance_project_ids']=[s for s,t in idmap.items() if t in result['assistance_source_ids']]
result['control_age_bins']=[]
for lo,hi in [(20,39),(40,59),(60,79),(80,99)]:
 ids=[int(s) for s,a in ages.items() if lo<=a<=hi]
 result['control_age_bins'].append({'ages':f'{lo}-{hi}','n':len(ids),'any_emg':sum(validcounts['control_avg'][f'Sub{s:02d}']>0 for s in ids),'complete_emg':sum(f'Sub{s:02d}' in complete['control_avg'] for s in ids)})
cv=np.array(list(ctrl_speed.values()));sv=np.array([(float(p)+float(n))/2 for _,p,n in stroke_speed]);cut=float(cv.min())
result['speed_subject_bilateral_mean']={'control_min_median_max':np.quantile(cv,[0,.5,1]).tolist(),'stroke_min_median_max':np.quantile(sv,[0,.5,1]).tolist(),'stroke_below_control_min_n':int(sum(sv<cut)),'stroke_complete_emg_below_control_min_n':int(sum(sv[i]<cut and f'Sub{i+1:02d}' in complete['stroke_P'] for i in range(50))),'control_complete_emg_min':min(ctrl_speed[int(s[3:])] for s in complete['control_avg'])}
# Check published clinical table vs MAT, rather than assuming ordinal mapping.
table=text.split('Supplementary Table 2.')[1].split('Supplementary Table 3.')[0]
pat=r'(TVC\d+)\s+(\d+)\s+([MF])\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([LR])\s+([IH])\s+(\d+)\s+(\d+)\s+(\d+)'
records=re.findall(pat,table);assert len(records)==50
mismatches=[]
for m,row in zip(meta,records):
 sid,age,sex,weight,height,leg,tps,lesion,stype,fac,poma,tis=row
 expect={'Age':float(age),'Male':float(sex=='M'),'TPS':float(tps),'FAC':float(fac),'POMA':float(poma),'TIS':float(tis),'LesionLeft':float(lesion=='L')}
 for k,v in expect.items():
  if m[k]!=v:mismatches.append({'subject':m['subject'],'field':k,'mat':m[k],'table':v})
 if idmap[m['subject']]!=sid:mismatches.append({'subject':m['subject'],'id_disagreement':sid})
result['published_clinical_table_checked_n']=len(records);result['published_clinical_mismatches']=mismatches
# Per-stride availability in the actual MAT, beyond nonempty mean curves.
rows=[]
with h5py.File(R/'data/raw/MAT_normalizedData_PostStrokeAdults.mat','r') as f:
 sub=f['Sub']
 for i in range(50):
  for side,key in [('P','PsideSegm_PsideData'),('N','NsideSegm_NsideData')]:
   g=f[sub[key][i,0]]
   for muscle in ['GAS','RF','VL','BF','ST','TA','ERS']:
    x=np.asarray(g[muscle+'norm']['n']);valid=np.isfinite(x).all(axis=1)
    rows.append(dict(subject=f'Sub{i+1:02d}',source_id=idmap[f'Sub{i+1:02d}'],side=side,muscle=muscle,total_strides=x.shape[0],valid_strides=int(valid.sum()),partial_nan_strides=int(((np.isnan(x).sum(axis=1)>0)&(np.isnan(x).sum(axis=1)<x.shape[1])).sum())))
with (O/'main_dataset_stride_emg_quality.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
v=[r['valid_strides'] for r in rows if r['valid_strides']>0]
result['nonempty_stroke_emg_valid_stride_count_min_median_max']=np.quantile(v,[0,.5,1]).tolist()
result['emg_partial_nan_stride_count']=sum(r['partial_nan_strides'] for r in rows)
result['emg_channels_with_one_valid_stride']=[r for r in rows if r['valid_strides']==1]
(O/'main_dataset_suitability.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
print(json.dumps({k:v for k,v in result.items() if k not in ['control_avg','stroke_P','stroke_N']},indent=2))
