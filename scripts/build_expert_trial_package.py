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
from src.features.emg_provenance import CANDIDATE_PROMPT_VERSION, RELEASED_COHORT_EMG, normalization_description, EMG_INTERPRETATION_LIMIT, cycle_boundary_description
from src.llm import candidate_prompts

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
        for trial in trials:trial.emg_processing=RELEASED_COHORT_EMG
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

MUSCLE_NAMES = {'RF':'Rectus femoris','VL':'Vastus lateralis','BF':'Biceps femoris','ST':'Semitendinosus','TA':'Tibialis anterior','GAS':'Gastrocnemius','ERS':'Erector spinae'}
JOINT_NAMES = {'PelvisAngles':'Pelvis','HipAngles':'Hip','KneeAngles':'Knee','AnkleAngles':'Ankle'}

def checklist(summary):
    items=[]
    def add(text,evidence,kind='must_describe_candidate'):
        items.append({'item_id':f'C{len(items)+1:02d}','category':kind,'draft_statement':text,
                      'evidence':evidence,'expert_decision':'PENDING','expert_edit':'','expert_id':'','review_date':''})
    if summary.gait_speed_m_s is not None:
        slow=' (below the gait-speed range of the healthy reference cohort in this study)' if summary.gait_speed_m_s<.80 else ''
        add(f'Gait speed is {summary.gait_speed_m_s:.2f} m/s{slow}. Should this be included in the report?','gait_speed_m_s')
    ranked=sorted(summary.joint_findings,key=lambda j:j.gvs or 0,reverse=True)
    joint_text=', '.join(f'{JOINT_NAMES.get(j.joint,j.joint)} {j.gvs:.2f}°' for j in ranked)
    add(f'Joint-motion curve differences from the reference, in descending order: {joint_text}. Select which model-visible joint summary differences merit emphasis; unseen waveform direction is not required model content. There is no need to repeat every score.','Joint kinematic findings')
    if not summary.muscle_findings:
        add('No EMG recordings are available for this case. The report should state that only the available joint kinematics and walking parameters can be evaluated; missing EMG must not be described as no muscle activity.','missing_emg_channels; model input missing-data statement')
    else:
        available=[m for m in summary.muscle_findings if m.deviation_z_peak is not None]
        if available:
            m=max(available,key=lambda m:m.deviation_z_peak)
            add(f'{MUSCLE_NAMES.get(m.muscle,m.muscle)}({m.muscle}) has the largest standardized difference relative to the reference in this case, at approximately {m.deviation_phase_pct:.0f}% of the gait cycle; the curve is {'above' if m.deviation_z_signed>0 else 'below'} the reference. Use the plots to judge whether this merits emphasis, or replace it with a more important finding.',f'{m.muscle}.z_signed; {m.muscle}.z_phase_pct')
        muscles=[MUSCLE_NAMES.get(m.muscle,m.muscle) for m in summary.muscle_findings if len(m.activation_intervals)>1 or m.crosses_cycle_boundary]
        if muscles:
            add('Examples selected for multiple retained intervals or boundary continuity (not a complete channel list): '+ ', '.join(muscles)+'. Which detected above-threshold intervals merit reporting? Other measured channels, including those with a single non-wrapping interval, remain available in the full input. Do not infer missing data from this selection.','Muscle activation findings; intervals')
        sustained=[f'{MUSCLE_NAMES.get(m.muscle,m.muscle)} {m.above_threshold_pct:.1f}%' for m in summary.muscle_findings if m.above_threshold_pct is not None and m.above_threshold_pct>=95]
        if sustained:
            add('The following curves remain above the relative threshold used for this case for nearly the entire cycle: '+ ', '.join(sustained)+'. Does this merit reporting? You may select "No need to include"; this value alone does not establish sustained abnormal contraction.','Muscle activation findings; above_threshold_pct')
        if summary.cci_findings:
            pairs=[]
            for pair,v in summary.cci_findings.items():
                label=pair
                for short,name in MUSCLE_NAMES.items():label=label.replace(short,name)
                pairs.append(f'{label} {v:.2f}')
            add('Muscle co-activation index (CCI): '+ '; '.join(pairs)+'. Given the supplied reference ranges, are there findings worth including in the report?','Co-contraction indices')
    if summary.group=='control':
        add('This case is from the healthy control group, and the participant was excluded from their own comparison reference. Please judge which differences are worth describing; these differences alone cannot establish disease or a labeling error.','identity; reference_meta')
    return items

def common_checklist(candidate=False):
    texts=[
        ('allowed_interpretation','The report should capture meaningful findings and need not repeat every number. When evidence is insufficient, it may state “currently indeterminate”; please use “Modify” to enter the wording you would like the report to use.'),
        ('cannot_infer','These materials alone cannot establish a diagnosis of spasticity, muscle weakness, or contracture, nor can they be used to prescribe a treatment plan. Information not recorded should not be guessed or treated as normal.'),
        ('cannot_infer','The reference bands in the figures and the calculated metrics only aid comparison; they are not diagnostic cutoffs for disease. Walking speed also affects comparison; EMG curve amplitude cannot be directly equated with muscle strength.'),
        ('allowed_interpretation','There is no need to repeatedly check every activity interval: a curve starting at 0% does not mean the muscle only begins activation at that point, and remaining above threshold throughout does not mean sustained abnormal contraction. Flag issues only when the report misinterprets these meanings. Figures and detailed references not received by the model cannot be grounds for omission deductions.')]
    if candidate:
        texts[2] = ('cannot_infer', 'When using a reference comparison, explain both its limited comparability and why it cannot establish a disease effect or clinical diagnosis. Naming age and speed separately is not required. A pooled label or speed range alone is insufficient. Case-specific speed findings remain separate requirements. For controls, do not use the comparison to establish disease or overall normality.')
        texts[3] = ('allowed_interpretation', 'Describe threshold findings as properties of the average EMG envelope. They do not establish physiological activation timing or normal gait phases. CCI comparisons describe an empirical range, not normal muscle function. Assess content coverage separately from incorrect assertions. Supplementary plots and reference values not provided to the model cannot be required content.')
    return [{'item_id':f'G{i:02d}','category':kind,'draft_statement':text,'evidence':'Uniform reporting requirements; see the full model input and reference notes for technical definitions','expert_decision':'PENDING','expert_edit':'','expert_id':'','review_date':''} for i,(kind,text) in enumerate(texts,1)]


def review_block(section_id, title, items, version):
    seed=json.dumps({'case_id':section_id,'version':version,'items':items},ensure_ascii=False).replace('<','\\u003c')
    return f'<h3 id="review-heading-{section_id}">{title}</h3><p>Choose whether to retain each item; if rewriting is needed, enter your suggested wording. You may also add important findings.</p><p class=\"review-progress\" id=\"progress-{section_id}"></p><fieldset class="review-fields" id="review-{section_id}" disabled></fieldset><script type="application/json" class="review-seed">{seed}</script>'


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
            axes[-1].text(0,.05,('Orange spans: retained above-threshold intervals' if findings else 'No subject envelope or activation threshold')+'\nSD band is descriptive, not a diagnostic limit.\nNo individual toe-off timing supplied.\nDraft for expert review.',transform=axes[-1].transAxes,fontsize=8,va='bottom')
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
    lines=[f'# Reference notes: {case_id}', '', '**Draft. An empirical distribution is not a clinical diagnostic threshold.**', '',
           f'Actual reference: {summary.reference_meta["n_subjects"]} participants, {summary.reference_meta["method"]}; excluded: {summary.reference_meta["excluded_subjects"]}.',
           '', '## A. Information actually provided to the model', '',
           'Please refer to the original text in model_user_prompt.txt: the definition of max|z|, the overall pooled p95 span of 3.65–4.61 (only the muscles at the endpoints), the reminder that LOO is higher, CCI ranges, pooled GPS-like background, and speed limitations. Complete LOO values were not provided for each muscle.',
           '', '## B. Supplementary table solely for expert verification during preparation', '',
           '**The exact values in the table below and the plots were not sent to the model; their omission must not automatically be counted as a model error. Before formal scoring, experts must decide whether to add these references to future standardized inputs or retain the current task, which permits indeterminate judgments.**',
           '', "| Muscle | Valid reference n for this case | Calibration distribution n | pooled p95 | LOO p95 | Background column corresponding to this case's method |",
           '|---|---:|---:|---:|---:|---|']
    for m in EMG_MUSCLES:
        c=calib[m];lines.append(f'| {m} | {counts[m]} | {c["n"]} | {c["p95"]} | {c["loo_p95"]} | {col} |')
    lines += ['', "The LOO column is the empirical distribution for all valid healthy individuals, each with themselves excluded, not a diagnostic threshold recalibrated specifically for Sub49 using 137 individuals; the possibility that this case is included as a calibration observation should not be concealed either. The patient's pooled comparison likewise indicates only deviation relative to this group of healthy individuals walking at self-selected speeds.",
              '', 'The input provides empirical 2.5–97.5 percentiles for CCI: TA–GAS 0.24–0.59 and RF–BF 0.48–0.83; CCI does not depend on the z reference mean.',
              'The input GPS-like median 5.1/p95 10.7 comes from the pooled background. GPS-like calculations for healthy cases use the LOO mean; the background p95 must not be directly passed off as a matched LOO diagnostic limit.',
              '', 'The mean±1 SD in the plots describes only the phase-wise distribution, not a 95% interval for individual curves or a clinical normal limit; a negative lower band boundary merely displays the mean minus SD and does not mean that negative EMG was observed.',
              normalization_description(summary.emg_processing, summary.group) + " " + EMG_INTERPRETATION_LIMIT + " Separately, interval detection uses 20% of the supplied mean envelope's own peak; do not confuse the detection threshold with the amplitude-normalization denominator.",
              cycle_boundary_description(summary.emg_processing, summary.group, summary.affected_side),
              'Individual toe-off was not provided, so precise stance/swing phases are not marked on the plots; the seven muscles do not represent all muscles.',
              '', 'Sources: original data https://doi.org/10.6084/m9.figshare.c.6503791.v1 ; methods https://www.nature.com/articles/s41597-023-02767-y ; local file data/normative_calibration_v2.json (see manifest for hash).']
    boundary_rows=[]
    for m in summary.muscle_findings:
        intervals=m.activation_intervals
        if m.above_threshold_pct == 100:
            note='Above threshold throughout the cycle; no clear onset/offset transition detected.'
        elif m.crosses_cycle_boundary:
            note='Continuous across 100%→0%; 0% is not a new physiological onset.'
        elif any(a == 0 for a,b in intervals):
            note='0% is the window boundary, not a confirmed physiological onset.'
        else:
            continue
        boundary_rows.append(f'| {m.muscle} | {intervals} | {note} |')
    if boundary_rows:
        lines += ['', '## Interval annotations for this case (reading guidance, not items that must be repeated)', '',
                  '| Muscle | Threshold intervals (% of cycle) | Annotation |', '|---|---|---|']+boundary_rows
    return '\n'.join(lines)+'\n'

def build(root, destination, cached=False, prompt_version="v2"):
    if prompt_version not in ["v2", CANDIDATE_PROMPT_VERSION]:raise ValueError("Unknown prompt version")
    system = candidate_prompts.SYSTEM_PROMPT if prompt_version == CANDIDATE_PROMPT_VERSION else SYSTEM_PROMPT
    make_user = candidate_prompts.build_user_prompt if prompt_version == CANDIDATE_PROMPT_VERSION else build_user_prompt
    root=Path(root);destination=Path(destination)
    if destination.exists():raise FileExistsError('Choose a new output directory; existing expert edits must not be overwritten.')
    trials,st,source=load_inputs(root,cached);controls=[t for t in trials if t.group=='control']
    if len(controls)!=138:raise ValueError('Expected 138 released controls')
    calib=json.loads((root/'data/normative_calibration_v2.json').read_text())
    code_paths=[Path(__file__).resolve()]+sorted((root/'src/features').glob('*.py'))+[root/'src/llm/prompt_templates.py',root/'src/llm/candidate_prompts.py',root/'scripts/generate_pilot_reports.py',root/'scripts/generate_control_spotcheck.py']
    code_paths += sorted((root/'src/eval/assets').glob('card_review.*'))
    code_hashes={str(p.relative_to(root)):digest(p) for p in code_paths}
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='trial-cards-building-',dir=destination.parent))
    manifest={'status':STATUS,'created_at':datetime.now(timezone.utc).isoformat(),'data_sources':source,
              'code_sha256':code_hashes,'calibration_sha256':digest(root/'data/normative_calibration_v2.json'),
              'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__,
              'model_calls':0,'expert_approved':False,'prompt_version':prompt_version,'cases':[]}
    common_items=common_checklist(candidate=prompt_version == CANDIDATE_PROMPT_VERSION)
    common_version=hashlib.sha256(json.dumps(common_items,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    write_json(staging/'common_checklist_DRAFT.json',common_items)
    with (staging/'common_checklist_DRAFT.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(common_items[0]));w.writeheader();w.writerows(common_items)
    (staging/'common_checklist_DRAFT.md').write_text('# Common review checklist (shared by all five cases, review only once)\n\n'+ '\n'.join(f'- [ ] {i["item_id"]} [{i["category"]}] {i["draft_statement"]}' for i in common_items)+'\n')
    manifest['common_review']={'section_id':'common_rules','review_version':common_version,'n_items':len(common_items)}
    common_body='<section id="common_rules"><h2>Before starting: common requirements</h2><p>The following 4 items apply to all cases and need confirmation only once. Each case typically has 3–6 items for your judgment; other values and methods can be expanded as needed.</p>'+review_block('common_rules','Common requirements (confirm only once)',common_items,common_version)+'</section>'
    sections=[];toc=[]
    for group,sid,side in CASES:
        trial=next(t for t in trials if (t.group,t.subject_id,t.side)==(group,sid,side));case_id=f'{group}_{sid}_{side}'
        members,norm=reference_for(trial,controls);summary=extract_summary_from_normalized(trial,norm,**(st.get((sid,side),{}) if group=='stroke' else {}))
        d=staging/case_id;d.mkdir();user=make_user(summary)
        (d/'model_system_prompt.txt').write_text(system);(d/'model_user_prompt.txt').write_text(user)
        (d/'input_text.txt').write_text(user if prompt_version == CANDIDATE_PROMPT_VERSION else to_prompt_text(summary))
        write_json(d/'model_messages.json',[{'role':'system','content':system},{'role':'user','content':user}])
        write_json(d/'summary.json',asdict(summary));facts=fact_rows(summary);write_json(d/'facts.json',facts)
        items=checklist(summary)
        with (d/'expert_checklist_DRAFT.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
        notes=['# Draft expert checklist: '+case_id,'','All items are pending expert approval. must_describe_candidate is not a deduction rule already in effect; clinical importance cannot be determined automatically by numerical ranking.','']
        labels={'must_describe_candidate':'Must describe: candidates for expert selection','allowed_interpretation':'Permitted interpretation: candidates','cannot_infer':'Cannot infer: pending expert confirmation'}
        for category,label in labels.items():
            notes += ['## '+label,'']+[f'- [ ] {i["item_id"]} {i["draft_statement"]} (basis: {i["evidence"]}）' for i in items if i['category']==category]+['']
        notes+=['## Expert finalization record','','First expert: ____  Date: ____','Second expert: ____  Date: ____','Version: ____; Disagreement/revision notes: ____','Do not view model outputs first and then reverse-engineer the reference; if adjustments are needed, retain the original draft and version.']
        (d/'checklist_DRAFT.md').write_text('\n'.join(notes)+'\n')
        counts=plots(d,trial,members,summary);ref=reference_notes(case_id,summary,calib,counts);(d/'reference_card.md').write_text(ref)
        item_manifest={'case_id':case_id,'group':group,'subject_id':sid,'side':side,'prompt_version':prompt_version,
                       'reference_meta':summary.reference_meta,'reference_members':[c.subject_id for c in members],
                       'effective_reference_n':counts,'files_sha256':{p.name:digest(p) for p in sorted(d.iterdir())}}
        manifest['cases'].append(item_manifest)
        case_title=f'{sid} · '+('Stroke, paretic side' if group=='stroke' else 'Healthy control, bilateral average')
        header=f'<h2 id="{case_id}">{case_title}</h2><p class=\"badge\">For expert confirmation · Not yet finalized</p><p><a href=\"#review-heading-{case_id}\">Go directly to this case\'s checklist review ↓</a></p>'
        rows=[('Walking speed',f'{summary.gait_speed_m_s:.2f} m/s' if summary.gait_speed_m_s is not None else 'Not provided'),('Valid EMG channels',f'{len(summary.muscle_findings)}/7'),('Composite joint-curve difference',f'{summary.gait_profile_score:.2f}° (research metric)'),('Reference',f'{len(members)} participants / {summary.reference_meta["method"]}')]
        body=header+table(['Item','Value'],rows)+'<p>First examine the curves, then confirm which findings below are worth including in the report. Blue represents the healthy reference and red represents this case; the reference band is not a boundary between normal and abnormal.</p>'
        for kind in ['emg','kinematics']:
            b64=base64.b64encode((d/f'curves_{kind}.png').read_bytes()).decode();body+=f'<img alt="{case_id} {kind} curves" src="data:image/png;base64,{b64}">'
        body+='<details><summary>View reference basis and calculation methods (expand as needed)</summary><pre>'+html.escape(ref)+'</pre></details>'
        version=hashlib.sha256(json.dumps([system,user,items,ref,common_version],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        item_manifest['review_version']=version
        body+=review_block(case_id,'Findings in this case requiring your confirmation',items,version)
        body+='<details><summary>View full model input (system + user)</summary><pre>'+html.escape(system+'\n\n'+user)+'</pre></details>'
        (d/'card.html').write_text(page(case_id,common_body+body))
        item_manifest['files_sha256']['card.html']=digest(d/'card.html')
        sections.append('<section>'+body+'</section>');toc.append(f'<li><a href="#{case_id}">{case_id}</a></li>')
        print('Built',case_id,flush=True)
    intro='<h1>Data cards for 5-case expert trial evaluation</h1><p class="badge">DRAFT · Machine-drafted for expert review</p><p>Please help determine which findings merit inclusion in a gait report, how they should be worded, and which conclusions lack sufficient evidence. This page is not yet for scoring model reports, nor is it a diagnostic tool.</p><ol>'+''.join(toc)+'</ol><p><a href="#common_rules">Review general questions first ↓</a></p>'
    (staging/'index.html').write_text(page('Expert trial data cards',intro+common_body+''.join(sections)))
    (staging/'README.md').write_text('# Five-case draft data cards\n\nOpen index.html to browse and interactively review all cases (plots and review tools are embedded for offline use). Each card.html can be shared separately.\nReview the common section at the front only once; exports contain common_rules and the five case sections. common_rules is not a sixth participant.\nIndividual case pages also include the same common section for standalone use.\nFirst enter your reviewer ID and click "Start / load review," then accept/edit/delete items and add new ones.\nWhen finished, export JSON and return it to the researcher; CSV can be viewed in Excel, and JSON supports resuming across devices. Different experts must use different IDs.\nBrowser storage is not a formal submission and does not modify original files on disk; be sure to export.\nEach case also provides PNG/PDF plots, model_system_prompt.txt, model_user_prompt.txt, model_messages.json,\nsummary.json, facts.json, reference_card.md, checklist_DRAFT.md, and an expert-editable CSV.\n\nThese are expert preparation materials, without model reports, model identities, or an answer key. Have experts approve the checklist before blinded rating.\nDo not directly use candidate "Must describe" items as penalty criteria; do not penalize models for omitting supplementary expert plots or detailed percentiles\nnot supplied to them. Consider the display precision of the model input when checking numbers; do not hold models to full machine precision.\n\nModel-input snapshots use the selected prompt version. The candidate version is opt-in and is not yet the approved formal generation route. Any subsequent prompt/data change requires a new version,\nwith checks against the system_prompt/user_prompt saved in the actual reports rather than an assumption of perpetual consistency.\nHealthy Sub49 uses a 137-person reference excluding that participant; valid n is listed separately for each muscle. Empirical calibration distributions and case-specific reference membership are distinct concepts.\nThis project evaluates only report fidelity and interpretation boundaries under the supplied evidence; it does not validate diagnosis or treatment.\n\nExample generation command:\n`python scripts/build_expert_trial_package.py --verified-cache --prompt-version limited-evidence-v3.1-candidate --out docs/expert_trial/data_cards_vNEXT`\nAlternatively, omit --verified-cache to read the released Excel/MAT directly. Existing directories are not overwritten, preserving expert edits.\nmanifest.json records source, code, and all deliverable hashes; the cache is not in Git, so local data or direct reading is required.\n')
    manifest['package_files_sha256']={p.name:digest(p) for p in staging.iterdir() if p.is_file()}
    if any(digest(root/name)!=h for name,h in code_hashes.items()):raise RuntimeError('Source changed during build; do not publish mixed-version cards')
    write_json(staging/'manifest.json',manifest);staging.rename(destination)
    return destination

def page(title, body):
    markup = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{max-width:1100px;margin:40px auto;padding:0 24px;font:16px/1.75 system-ui,sans-serif;color:#233444;background:#f8fafb}h1,h2,h3{color:#173f54}section{background:white;padding:28px;margin:32px 0;border:1px solid #dbe4e8;border-radius:12px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;margin:18px 0}td,th{padding:8px 12px;border:1px solid #d6e1e6;text-align:left}th{background:#edf3f6}.badge{color:#8a5700;background:#fff1cc;padding:8px 14px;border-radius:5px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.65 ui-monospace,monospace;background:#f3f6f8;padding:16px}small{display:block;color:#64717c}li{margin-bottom:10px}summary{cursor:pointer;font-weight:bold}@media print{body{background:white;margin:0;font-size:11pt}section{break-before:page;border:0;padding:0}img{max-height:230mm;object-fit:contain}details{display:none}h2,h3{break-after:avoid}li,tr{break-inside:avoid}}</style><body>'+body+'</body></html>'


    css=(ROOT/'src/eval/assets/card_review.css').read_text()
    js=(ROOT/'src/eval/assets/card_review.js').read_text()
    toolbar = '<aside class="review-toolbar" aria-label="Expert review tools"><strong>Expert checklist review</strong><div class="review-identity"><label>Expert name / ID<br><input id="reviewer-id" autocomplete="off" placeholder="e.g. Rater01" maxlength="100"></label><label>Review date<br><input type="date" id="review-date"></label><button type="button" id="review-start">Start / load review</button></div><p id="review-progress"></p><div class="review-actions"><button type="button" id="export-review-json">Export review JSON (return / resume)</button><button type="button" id="export-review-csv">Export CSV (Excel)</button><label class="review-import-label">Import existing review JSON<br><input type="file" accept=".json,application/json" id="review-import"></label></div><p id="review-status" role="status" aria-live="polite">Enter your reviewer ID to start. Changes are stored in this browser; export and return them when finished. Nothing is sent automatically or written to the original file.</p><noscript>Interactive review requires browser JavaScript; alternatively, edit the accompanying expert_checklist_DRAFT.csv.</noscript></aside>'
    return markup.replace('</style>','</style><style>'+css+'</style>',1).replace('<body>','<body>'+toolbar,1).replace('</body>','<script>'+js+'</script></body>',1)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'docs/expert_trial/data_cards_v5')
    parser.add_argument('--verified-cache',action='store_true')
    parser.add_argument('--prompt-version',choices=['v2',CANDIDATE_PROMPT_VERSION],default='v2')
    args=parser.parse_args();print(build(ROOT,args.out,args.verified_cache,args.prompt_version))
