"""Reproducible, offline expert-review drafts. No model calls or report reading.

Default: read released Excel/MAT files. --verified-cache uses the original audited
curve/event cache only after verifying its SHA256 against audit/sha256_manifest.json.
Existing outputs are never overwritten. All clinical checklist items remain drafts.
"""
from __future__ import annotations
import argparse, base64, csv, hashlib, html, io, json, platform, sys, tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.features.data_types import NormalizedTrialData
from src.features.figshare_loader import EMG_MUSCLES, KINEMATIC_JOINTS, load_control_excel, load_stroke_excel
from src.features.mat_spatiotemporal import load_stroke_spatiotemporal, build_spatiotemporal_lookup
from src.features.pipeline import build_normative_reference_from_normalized, extract_summary_from_normalized, to_prompt_text
from src.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt

CASES = [('stroke','Sub09','P'), ('stroke','Sub05','P'), ('stroke','Sub50','P'), ('stroke','Sub47','P'), ('control','Sub49','avg')]
STATUS = 'DRAFT — agent-prepared, not an expert reference standard'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def verified_bytes(root, rel, expected):
    data=(root/rel).read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError(f'Audited cache hash mismatch: {rel}')
    return data

def load_inputs(root, cached):
    if cached:
        am=root/'audit/sha256_manifest.json'; manifest=json.loads(am.read_text())
        paths=['outputs/curves.npz','outputs/spatiotemporal_original.json']
        blobs={p:verified_bytes(root/'audit',p,manifest[p]) for p in paths}
        with np.load(io.BytesIO(blobs[paths[0]]),allow_pickle=False) as arrays:
            groups={}
            for k in arrays.files:
                g,s,side,ch=k.split('_');groups.setdefault((g,s,side),{})[ch]=arrays[k]
        trials=[NormalizedTrialData(s,g,side,{k:v for k,v in c.items() if k in KINEMATIC_JOINTS},
                {k:v for k,v in c.items() if k in EMG_MUSCLES}) for (g,s,side),c in groups.items()]
        events=json.loads(blobs[paths[1]])
        # The original audited event cache predates this descriptive field. Its
        # default formula is successive-footfall, as documented in the audit.
        for r in events:r.setdefault('step_length_definition','successive_footfall')
        sources={f'audit/{p}':manifest[p] for p in paths}
        sources['audit/sha256_manifest.json']=digest(am)
        mode='SHA256-verified audited release cache; no new full raw-signal QC'
    else:
        names=['AbleBodiedAdults.xlsx','PostStrokeAdults.xlsx','MAT_normalizedData_PostStrokeAdults.mat']
        sources={f'data/raw/{n}':digest(root/'data/raw'/n) for n in names}
        trials=load_control_excel(str(root/'data/raw'/names[0]))+load_stroke_excel(str(root/'data/raw'/names[1]))
        events=load_stroke_spatiotemporal(str(root/'data/raw'/names[2]))
        mode='released Excel and processed MAT, read directly'
    return trials,build_spatiotemporal_lookup(events),{'mode':mode,'sha256':sources}

def reference_for(trial, controls):
    is_control=trial.group=='control'
    members=[c for c in controls if not (is_control and c.subject_id==trial.subject_id)]
    norm=build_normative_reference_from_normalized(members,source='main_cohort_excel',
            method='leave_one_out' if is_control else 'pooled',
            excluded_subjects=(trial.subject_id,) if is_control else ())
    return members,norm

def fact_rows(summary):
    """Facts without automatic claims of clinical importance or abnormality."""
    rows=[]
    def add(key,value,evidence):rows.append({'fact_id':key,'value':value,'evidence':evidence,'model_visible':True})
    add('identity',f'{summary.group}/{summary.subject_id}/{summary.affected_side or "avg"}','Subject line')
    for name in ['gait_speed_m_s','cadence_steps_min','step_length_symmetry_index','gait_profile_score']:
        v=getattr(summary,name)
        if v is not None:add(name,round(v,6),name)
    for m in summary.muscle_findings:
        add(f'{m.muscle}.intervals',m.activation_intervals,f'Muscle activation findings: {m.muscle}')
        add(f'{m.muscle}.above_threshold_pct',m.above_threshold_pct,f'Muscle activation findings: {m.muscle}')
        add(f'{m.muscle}.peak',m.peak_amplitude_norm,f'Muscle activation findings: {m.muscle}')
        if m.deviation_z_peak is not None:
            add(f'{m.muscle}.z_signed',m.deviation_z_signed,f'Muscle activation findings: {m.muscle}')
            add(f'{m.muscle}.z_phase_pct',m.deviation_phase_pct,f'Muscle activation findings: {m.muscle}')
    for j in summary.joint_findings:
        add(f'{j.joint}.rom_deg',j.rom_deg,f'Joint kinematic findings: {j.joint}')
        add(f'{j.joint}.gvs_deg',j.gvs,f'Joint kinematic findings: {j.joint}')
    for pair,v in summary.cci_findings.items():add(pair,v,f'Co-contraction indices: {pair}')
    add('missing_emg_channels',summary.missing_emg_channels,'Missing channel/No valid EMG statement')
    return rows

MUSCLE_NAMES = {'RF':'股直肌','VL':'股外侧肌','BF':'股二头肌','ST':'半腱肌','TA':'胫骨前肌','GAS':'腓肠肌','ERS':'竖脊肌'}
JOINT_NAMES = {'PelvisAngles':'骨盆','HipAngles':'髋关节','KneeAngles':'膝关节','AnkleAngles':'踝关节'}

def checklist(summary):
    items=[]
    def add(text,evidence,kind='must_describe_candidate'):
        items.append({'item_id':f'C{len(items)+1:02d}','category':kind,'draft_statement':text,
                      'evidence':evidence,'expert_decision':'PENDING','expert_edit':'','expert_id':'','review_date':''})
    if summary.gait_speed_m_s is not None:
        slow='（低于本研究健康参考人群的步速范围）' if summary.gait_speed_m_s<.80 else ''
        add(f'行走速度为 {summary.gait_speed_m_s:.2f} m/s{slow}。这一点是否需要写进报告？','gait_speed_m_s')
    ranked=sorted(summary.joint_findings,key=lambda j:j.gvs or 0,reverse=True)
    joint_text='、'.join(f'{JOINT_NAMES.get(j.joint,j.joint)} {j.gvs:.2f}°' for j in ranked)
    add(f'关节运动曲线与参考的差异由大到小为：{joint_text}。请选出报告应重点描述的关节和变化；不必逐项复述评分。','Joint kinematic findings')
    if not summary.muscle_findings:
        add('本例没有可用肌电记录。报告应说明只能评价已有的关节运动和行走参数；不能把EMG缺失写成无肌肉活动。','missing_emg_channels; model input missing-data statement')
    else:
        available=[m for m in summary.muscle_findings if m.deviation_z_peak is not None]
        if available:
            m=max(available,key=lambda m:m.deviation_z_peak)
            add(f'{MUSCLE_NAMES.get(m.muscle,m.muscle)}（{m.muscle}）在本例中相对参考的标准化差异最大，位于步态周期约 {m.deviation_phase_pct:.0f}%处，曲线{"高于" if m.deviation_z_signed>0 else "低于"}参考。请结合图形判断是否值得重点描述，或修改为更重要的发现。',f'{m.muscle}.z_signed; {m.muscle}.z_phase_pct')
        muscles=[MUSCLE_NAMES.get(m.muscle,m.muscle) for m in summary.muscle_findings if len(m.activation_intervals)>1 or m.crosses_cycle_boundary]
        if muscles:
            add('请看'+ '、'.join(muscles)+'的肌电曲线：哪些活动时段值得报告？如需描述，请写出肌肉和主要时段，无需逐段核对算法划分。','Muscle activation findings; intervals')
        sustained=[f'{MUSCLE_NAMES.get(m.muscle,m.muscle)} {m.above_threshold_pct:.1f}%' for m in summary.muscle_findings if m.above_threshold_pct is not None and m.above_threshold_pct>=95]
        if sustained:
            add('以下曲线几乎全程高于本例所用的相对阈值：'+ '、'.join(sustained)+'。这是否值得报告？可以选择“不必写入”；该数值本身不能说明持续异常收缩。','Muscle activation findings; above_threshold_pct')
        if summary.cci_findings:
            pairs=[]
            for pair,v in summary.cci_findings.items():
                label=pair
                for short,name in MUSCLE_NAMES.items():label=label.replace(short,name)
                pairs.append(f'{label} {v:.2f}')
            add('肌肉共同活动指标（CCI）：'+ '；'.join(pairs)+'。结合给出的参考范围，是否有值得写进报告的发现？','Co-contraction indices')
    if summary.group=='control':
        add('本例来自健康对照组，比较时已排除本人。请判断哪些差异值得描述；不能仅凭这些差异认定其患病或标签错误。','identity; reference_meta')
    return items

def common_checklist():
    texts=[
        ('allowed_interpretation','报告应抓住有意义的发现，不必复述每个数字。证据不足时可以写“目前无法判断”；请用“修改”写出您希望报告采用的说法。'),
        ('cannot_infer','这些资料不能单独确诊痉挛、肌无力或挛缩，也不能据此开出治疗方案。没有记录到的信息，不应猜测或当作正常。'),
        ('cannot_infer','图中的参考带和计算指标只帮助比较，不是疾病诊断界限。走得快慢也会影响比较；肌电曲线的高低不能直接当作肌力大小。'),
        ('allowed_interpretation','不必反复核对每个活动区间：曲线从0%开始不代表肌肉此时才启动，全程超过阈值也不代表持续异常收缩。只在报告误解这些含义时指出问题。模型没收到的图形和详细参考，不能作为漏报扣分依据。')]
    return [{'item_id':f'G{i:02d}','category':kind,'draft_statement':text,'evidence':'统一报告要求；技术定义见完整模型输入与参考说明','expert_decision':'PENDING','expert_edit':'','expert_id':'','review_date':''} for i,(kind,text) in enumerate(texts,1)]


def review_block(section_id, title, items, version):
    seed=json.dumps({'case_id':section_id,'version':version,'items':items},ensure_ascii=False).replace('<','\\u003c')
    return f'<h3 id="review-heading-{section_id}">{title}</h3><p>选择是否保留；需要改写时填入您建议的说法。还可补充重要发现。</p><p class="review-progress" id="progress-{section_id}"></p><fieldset class="review-fields" id="review-{section_id}" disabled></fieldset><script type="application/json" class="review-seed">{seed}</script>'


def plots(case_dir, trial, members, summary):
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    findings={m.muscle:m for m in summary.muscle_findings}; counts={}
    for kind,channels,shape,figsize in [('emg',EMG_MUSCLES,(4,2),(11,12)),('kinematics',KINEMATIC_JOINTS,(2,2),(11,7))]:
        fig,axes=plt.subplots(*shape,figsize=figsize,sharex=True);axes=np.array(axes).ravel()
        for ax,ch in zip(axes,channels):
            attr='emg_norm' if kind=='emg' else 'joint_angles';curve=getattr(trial,attr)[ch]
            valid=[getattr(c,attr)[ch] for c in members if np.isfinite(getattr(c,attr)[ch]).all()]
            stack=np.stack(valid);mean,sd=stack.mean(0),stack.std(0);x=np.linspace(0,100,len(curve));counts[ch]=len(valid)
            ax.fill_between(x,mean-sd,mean+sd,color='#377ca4',alpha=.18,label='Reference mean ±1 SD')
            ax.plot(x,mean,color='#377ca4',lw=1.2,label='Reference mean')
            if np.isfinite(curve).all():
                ax.plot(x,curve,color='#b34439',lw=1.6,label='Subject average')
                if kind=='emg':
                    threshold=.2*float(np.max(curve));ax.axhline(threshold,color='#b57612',ls='--',lw=1,label='20% of subject curve peak')
                    for a,b in findings[ch].activation_intervals:
                        for lo,hi in ([(a,b)] if a<=b else [(a,100),(0,b)]):ax.axvspan(lo,hi,color='#e5b257',alpha=.18)
                    m=findings[ch]
                    if m.deviation_phase_pct is not None:
                        idx=round(m.deviation_phase_pct/100*(len(curve)-1));ax.scatter([x[idx]],[curve[idx]],color='#222',s=14,zorder=5,label='Max |z| phase')
            else:
                ax.text(.5,.57,'NO SUBJECT EMG DATA\nReference shown for context only',transform=ax.transAxes,ha='center',va='center',bbox={'facecolor':'white','alpha':.95,'edgecolor':'#bbb'},fontsize=10)
            ax.set_title(f'{ch} • effective reference n={len(valid)}',loc='left',fontweight='bold')
            ax.set_ylabel('Peak-normalized amplitude (a.u.)' if kind=='emg' else 'Angle (degrees)')
            ax.set_xlim(0,100);ax.grid(alpha=.15)
        handles,labels=axes[0].get_legend_handles_labels()
        if len(axes)>len(channels):
            axes[-1].axis('off');axes[-1].legend(handles,labels,loc='upper left',frameon=False,fontsize=8.5)
            axes[-1].text(0,.05,('Orange spans: retained activation intervals' if findings else 'No subject envelope or activation threshold')+'\nSD band is descriptive, not a diagnostic limit.\nNo individual toe-off timing supplied.\nDraft for expert review.',transform=axes[-1].transAxes,fontsize=8,va='bottom')
        else:fig.legend(handles,labels,loc='lower center',ncol=3,bbox_to_anchor=(.5,.012),frameon=False)
        method='LOO, excluding '+trial.subject_id if trial.group=='control' else 'pooled healthy cohort'
        fig.suptitle(f'{trial.group} / {trial.subject_id} / {trial.side} — {kind}\n{method} • DRAFT',fontsize=13,fontweight='bold')
        fig.supxlabel('Gait cycle (%)',y=.075 if kind=='kinematics' else .015)
        fig.tight_layout(rect=(0,.10 if kind=='kinematics' else .03,1,.93))
        fig.savefig(case_dir/f'curves_{kind}.png',dpi=150)
        fig.savefig(case_dir/f'curves_{kind}.pdf')
        plt.close(fig)
    return counts

def table(headers,rows):
    return '<table><thead><tr>'+''.join('<th>'+html.escape(str(c))+'</th>' for c in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(c))+'</td>' for c in r)+'</tr>' for r in rows)+'</tbody></table>'

def reference_notes(case_id, summary, calib, counts):
    healthy=summary.group=='control';col='loo_p95' if healthy else 'p95'
    lines=[f'# 参考说明：{case_id}', '', '**草稿。经验分布不是临床诊断阈值。**', '',
           f'实际参考：{summary.reference_meta["n_subjects"]}人，{summary.reference_meta["method"]}；排除：{summary.reference_meta["excluded_subjects"]}。',
           '', '## A. 模型实际获得的信息', '',
           '请以 model_user_prompt.txt 原文为准：max|z|定义、pooled p95总体跨度3.65–4.61（仅端点肌肉）、LOO更高的提醒、CCI范围、pooled GPS-like背景和速度限制。未逐肌肉完整提供LOO数值。',
           '', '## B. 仅供专家准备阶段核查的补充表', '',
           '**下表精确数值和图形没有发送给模型；不得把遗漏它们自动计为模型错误。正式评分前专家必须决定是否把这些参考加入未来统一输入，或维持允许不可判定的当前任务。**',
           '', '| 肌肉 | 本例有效参考n | 校准分布n | pooled p95 | LOO p95 | 本例方法对应的背景列 |',
           '|---|---:|---:|---:|---:|---|']
    for m in EMG_MUSCLES:
        c=calib[m];lines.append(f'| {m} | {counts[m]} | {c["n"]} | {c["p95"]} | {c["loo_p95"]} | {col} |')
    lines += ['', 'LOO列是全体有效健康者各自排除本人的经验分布，并非专为Sub49重新校准的137人诊断阈值；包含该例作为校准观察的可能性也不应隐去。患者的pooled比较也只表示相对这组自选步速健康者的偏差。',
              '', 'CCI在输入中给出TA–GAS 0.24–0.59、RF–BF 0.48–0.83的经验2.5–97.5分位数；它不依赖z参考均值。',
              '输入GPS-like中位5.1/p95 10.7来自pooled背景。健康例GPS-like计算使用LOO均值，不能把背景p95直接冒充匹配的LOO诊断界限。',
              '', '图中的均值±1 SD仅描述相位分布，不是个体曲线95%区间或临床正常界限；负的带下界只是均值减SD的显示，不代表观察到负EMG。',
              'EMG为发布的平均包络；原数据使用每人每肌肉跨可用周期的共同峰值归一化。图上阈值另外取平均曲线峰值的20%，二者不要混淆。',
              '未提供每人toe-off，因此图上不标精确支撑/摆动期；七块肌肉并不代表全部肌肉。',
              '', '资料来源：原数据 https://doi.org/10.6084/m9.figshare.c.6503791.v1 ；方法 https://www.nature.com/articles/s41597-023-02767-y ；本地 data/normative_calibration_v2.json（哈希见manifest）。']
    boundary_rows=[]
    for m in summary.muscle_findings:
        intervals=m.activation_intervals
        if m.above_threshold_pct == 100:
            note='全周期过阈值；未检出明确起止转换。'
        elif m.crosses_cycle_boundary:
            note='跨100%→0%连续；0%不是新一次生理起始。'
        elif any(a == 0 for a,b in intervals):
            note='0%为窗口边界，非确认的生理起始。'
        else:
            continue
        boundary_rows.append(f'| {m.muscle} | {intervals} | {note} |')
    if boundary_rows:
        lines += ['', '## 本例区间注释（阅读提示，不是必须复述项）', '',
                  '| 肌肉 | 阈值区间（%周期） | 注释 |', '|---|---|---|']+boundary_rows
    return '\n'.join(lines)+'\n'

def build(root, destination, cached=False):
    root=Path(root);destination=Path(destination)
    if destination.exists():raise FileExistsError('Choose a new output directory; existing expert edits must not be overwritten.')
    trials,st,source=load_inputs(root,cached);controls=[t for t in trials if t.group=='control']
    if len(controls)!=138:raise ValueError('Expected 138 released controls')
    calib=json.loads((root/'data/normative_calibration_v2.json').read_text())
    code_paths=[Path(__file__).resolve()]+sorted((root/'src/features').glob('*.py'))+[root/'src/llm/prompt_templates.py',root/'scripts/generate_pilot_reports.py',root/'scripts/generate_control_spotcheck.py']
    code_paths += sorted((root/'src/eval/assets').glob('card_review.*'))
    code_hashes={str(p.relative_to(root)):digest(p) for p in code_paths}
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='trial-cards-building-',dir=destination.parent))
    manifest={'status':STATUS,'created_at':datetime.now(timezone.utc).isoformat(),'data_sources':source,
              'code_sha256':code_hashes,'calibration_sha256':digest(root/'data/normative_calibration_v2.json'),
              'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__,
              'model_calls':0,'expert_approved':False,'cases':[]}
    common_items=common_checklist()
    common_version=hashlib.sha256(json.dumps(common_items,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    write_json(staging/'common_checklist_DRAFT.json',common_items)
    with (staging/'common_checklist_DRAFT.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(common_items[0]));w.writeheader();w.writerows(common_items)
    (staging/'common_checklist_DRAFT.md').write_text('# 通用审核清单（五例共用，仅审核一次）\n\n'+ '\n'.join(f'- [ ] {i["item_id"]} [{i["category"]}] {i["draft_statement"]}' for i in common_items)+'\n')
    manifest['common_review']={'section_id':'common_rules','review_version':common_version,'n_items':len(common_items)}
    common_body='<section id="common_rules"><h2>开始前：共同要求</h2><p>下面4项适用于所有病例，只需确认一次。每例通常有3—6项需要您判断，其他数字与方法可按需展开。</p>'+review_block('common_rules','共同要求（只确认一次）',common_items,common_version)+'</section>'
    sections=[];toc=[]
    for group,sid,side in CASES:
        trial=next(t for t in trials if (t.group,t.subject_id,t.side)==(group,sid,side));case_id=f'{group}_{sid}_{side}'
        members,norm=reference_for(trial,controls);summary=extract_summary_from_normalized(trial,norm,**(st.get((sid,side),{}) if group=='stroke' else {}))
        d=staging/case_id;d.mkdir();user=build_user_prompt(summary)
        (d/'model_system_prompt.txt').write_text(SYSTEM_PROMPT);(d/'model_user_prompt.txt').write_text(user)
        (d/'input_text.txt').write_text(to_prompt_text(summary))
        write_json(d/'model_messages.json',[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':user}])
        write_json(d/'summary.json',asdict(summary));facts=fact_rows(summary);write_json(d/'facts.json',facts)
        items=checklist(summary)
        with (d/'expert_checklist_DRAFT.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
        notes=['# 专家清单草稿：'+case_id,'','所有条目待专家审定。must_describe_candidate不是已经生效的扣分规则；临床重要性不能由数值排序自动决定。','']
        labels={'must_describe_candidate':'必须描述：候选，待专家筛选','allowed_interpretation':'允许解释：候选','cannot_infer':'不能据此推断：待专家核定'}
        for category,label in labels.items():
            notes += ['## '+label,'']+[f'- [ ] {i["item_id"]} {i["draft_statement"]}（依据：{i["evidence"]}）' for i in items if i['category']==category]+['']
        notes+=['## 专家定稿记录','','第一位专家：____  日期：____','第二位专家：____  日期：____','版本：____；分歧/修改说明：____','不得先看模型输出后倒推参考；如需调整，保留原草稿和版本。']
        (d/'checklist_DRAFT.md').write_text('\n'.join(notes)+'\n')
        counts=plots(d,trial,members,summary);ref=reference_notes(case_id,summary,calib,counts);(d/'reference_card.md').write_text(ref)
        item_manifest={'case_id':case_id,'group':group,'subject_id':sid,'side':side,'prompt_version':'v2',
                       'reference_meta':summary.reference_meta,'reference_members':[c.subject_id for c in members],
                       'effective_reference_n':counts,'files_sha256':{p.name:digest(p) for p in sorted(d.iterdir())}}
        manifest['cases'].append(item_manifest)
        case_title=f'{sid} · '+('卒中，患侧' if group=='stroke' else '健康对照，双侧平均')
        header=f'<h2 id="{case_id}">{case_title}</h2><p class="badge">供专家确认 · 尚未定稿</p><p><a href="#review-heading-{case_id}">直接审核本例清单 ↓</a></p>'
        rows=[('步速',f'{summary.gait_speed_m_s:.2f} m/s' if summary.gait_speed_m_s is not None else '未提供'),('EMG有效通道',f'{len(summary.muscle_findings)}/7'),('关节曲线综合差异',f'{summary.gait_profile_score:.2f}°（研究用指标）'),('参考',f'{len(members)}人 / {summary.reference_meta["method"]}')]
        body=header+table(['项目','值'],rows)+'<p>先看曲线，再确认下方哪些发现值得写进报告。蓝色为健康参考，红色为本例；参考带不是正常与异常的分界。</p>'
        for kind in ['emg','kinematics']:
            b64=base64.b64encode((d/f'curves_{kind}.png').read_bytes()).decode();body+=f'<img alt="{case_id} {kind} curves" src="data:image/png;base64,{b64}">'
        body+='<details><summary>查看参考依据与计算方法（需要时展开）</summary><pre>'+html.escape(ref)+'</pre></details>'
        version=hashlib.sha256(json.dumps([SYSTEM_PROMPT,user,items,ref,common_version],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        item_manifest['review_version']=version
        body+=review_block(case_id,'本例需要您确认的发现',items,version)
        body+='<details><summary>查看完整模型输入（system + user）</summary><pre>'+html.escape(SYSTEM_PROMPT+'\n\n'+user)+'</pre></details>'
        (d/'card.html').write_text(page(case_id,common_body+body))
        item_manifest['files_sha256']['card.html']=digest(d/'card.html')
        sections.append('<section>'+body+'</section>');toc.append(f'<li><a href="#{case_id}">{case_id}</a></li>')
        print('Built',case_id,flush=True)
    intro='<h1>5例专家试评数据卡</h1><p class="badge">DRAFT · 机器起草，供专家审核</p><p>请帮助确定：哪些发现值得写进步态报告、应该怎样表述、哪些结论证据不足。本页还不是模型报告评分，也不是诊断工具。</p><ol>'+''.join(toc)+'</ol><p><a href="#common_rules">先审核通用问题 ↓</a></p>'
    (staging/'index.html').write_text(page('Expert trial data cards',intro+common_body+''.join(sections)))
    (staging/'README.md').write_text('''# 5例数据卡草稿

打开 index.html 浏览并交互审核全部病例（图和审核功能内嵌，可离线使用）。每例 card.html 可单独分享。
最前面的通用审核区只审一次；导出包含common_rules及五例病例区，common_rules不是第六例受试者。
单例页面也附带同一版通用区，便于独立使用。
先填写专家编号并点击“开始／载入审核”，再逐条接受/修改/删除和补充条目。
完成后导出 JSON 交回研究者；CSV可用Excel查看，JSON可跨设备续填。不同专家使用不同编号。
浏览器暂存不是正式交回，也不会修改磁盘上的原始文件；请务必导出。
每例还提供 PNG/PDF 图、model_system_prompt.txt、model_user_prompt.txt、model_messages.json、
summary.json、facts.json、reference_card.md、checklist_DRAFT.md 和专家可编辑 CSV。

这是专家准备材料，没有模型报告、模型身份或答案键。先由专家审定清单，再开展盲评。
不要将候选“必须描述”条目直接作为扣分标准；不得因模型没有提及专家补充图或未提供的
详细分位数而扣分。核查数值时考虑模型输入的显示精度，不能用机器全精度追责。

模型输入快照与当前正式入口使用相同函数；任何后续prompt/数据变动都应重新生成新版本，
并核对实际报告中保存的system_prompt/user_prompt，而不是假定永远一致。
健康Sub49使用排除本人的137人参考，各肌肉有效n另列；经验校准分布与本例参考成员不是同一个概念。
此项目仅评估给定证据下的报告忠实性与解释边界，不验证诊断或治疗。

生成命令示例：
`python scripts/build_expert_trial_package.py --verified-cache --out docs/expert_trial/data_cards_vNEXT`
也可省略 --verified-cache 直接读取发布Excel/MAT。已有目录不覆盖，以保留专家编辑。
manifest.json记录来源、源码和所有交付物哈希；缓存不在Git中，需本地数据或选择直接读取。
''')
    manifest['package_files_sha256']={p.name:digest(p) for p in staging.iterdir() if p.is_file()}
    if any(digest(root/name)!=h for name,h in code_hashes.items()):raise RuntimeError('Source changed during build; do not publish mixed-version cards')
    write_json(staging/'manifest.json',manifest);staging.rename(destination)
    return destination

def page(title, body):
    markup = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{max-width:1100px;margin:40px auto;padding:0 24px;font:16px/1.75 system-ui,sans-serif;color:#233444;background:#f8fafb}h1,h2,h3{color:#173f54}section{background:white;padding:28px;margin:32px 0;border:1px solid #dbe4e8;border-radius:12px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;margin:18px 0}td,th{padding:8px 12px;border:1px solid #d6e1e6;text-align:left}th{background:#edf3f6}.badge{color:#8a5700;background:#fff1cc;padding:8px 14px;border-radius:5px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.65 ui-monospace,monospace;background:#f3f6f8;padding:16px}small{display:block;color:#64717c}li{margin-bottom:10px}summary{cursor:pointer;font-weight:bold}@media print{body{background:white;margin:0;font-size:11pt}section{break-before:page;border:0;padding:0}img{max-height:230mm;object-fit:contain}details{display:none}h2,h3{break-after:avoid}li,tr{break-inside:avoid}}</style><body>'+body+'</body></html>'


    css=(ROOT/'src/eval/assets/card_review.css').read_text()
    js=(ROOT/'src/eval/assets/card_review.js').read_text()
    toolbar = '<aside class="review-toolbar" aria-label="专家审核工具"><strong>专家清单审核</strong><div class="review-identity"><label>专家姓名／编号<br><input id="reviewer-id" autocomplete="off" placeholder="例如 Rater01" maxlength="100"></label><label>审核日期<br><input type="date" id="review-date"></label><button type="button" id="review-start">开始／载入审核</button></div><p id="review-progress"></p><div class="review-actions"><button type="button" id="export-review-json">导出审核 JSON（交回／续填）</button><button type="button" id="export-review-csv">导出 CSV（Excel）</button><label class="review-import-label">导入已有审核 JSON<br><input type="file" accept=".json,application/json" id="review-import"></label></div><p id="review-status" role="status" aria-live="polite">填写专家编号后开始审核。修改暂存于本机浏览器；完成后必须导出交回，不会自动发送或改写原文件。</p><noscript>交互审核需要启用浏览器JavaScript；也可编辑随附expert_checklist_DRAFT.csv。</noscript></aside>'
    return markup.replace('</style>','</style><style>'+css+'</style>',1).replace('<body>','<body>'+toolbar,1).replace('</body>','<script>'+js+'</script></body>',1)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'docs/expert_trial/data_cards_v5')
    parser.add_argument('--verified-cache',action='store_true')
    args=parser.parse_args();print(build(ROOT,args.out,args.verified_cache))
