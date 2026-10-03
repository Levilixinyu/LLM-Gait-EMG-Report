"""Populate the published 2025 TRIPOD-LLM items with evidence and remaining gaps."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/formal_study/reporting_checklist_v1'
M = 'docs/formal_study/manuscript_v1/MANUSCRIPT.md'
S = 'docs/formal_study/manuscript_v1/SUPPLEMENTARY_METHODS.md'
A = 'docs/formal_study/manuscript_v1/AUTHOR_CONFIRMATION.md'
GUIDELINE = 'https://www.tripod-statement.org/wp-content/uploads/2025/01/TRIPOD-LLM-Article.pdf'
# Short navigation labels are ours; the linked published tables supply full wording.
# Tuple: identifier, label, status, location keys, project evidence / remaining work.
MAIN = [
('1','Title','Partial','title','The retained title names LLM gait reports and both dimensions, but omits the stroke population and explicit evaluation design. Title changes remain an author decision.'),
('2','Abstract','Partial','abstract','The separate abstract checklist records the remaining reporting gaps; no complete-compliance claim is made.'),
('3a','Context','Reported','intro','Numerical gait interpretation is distinguished from diagnosis, with AMAP, clinical summarization, CLEVER and gait-reporting research providing context.'),
('3b','Users','Reported','intro;inputs','Stroke participants and healthy controls are identified. Candidate users are researchers and gait professionals; only offline expert evaluation was tested.'),
('4','Objectives','Reported','intro;design','The comparison evaluates existing configurations and separate coverage/error outcomes; there was no model development or clinical deployment.'),
('5a','Data sources','Reported','design;inputs','Released participant-average motion-capture/EMG data supply evaluation inputs. Provider training data are not established by the records; the project did not fine-tune models.'),
('5b','Data profile','Reported','sample;table1;inputs','Counts, age, sex, speed, channels and English task language are reported. Supplementary methods identify M2OCEAN in Antwerp, Belgium as the original collection setting.'),
('5c','Data dates','Partial','inputs;config','Inference dates are known; participant-level collection-date ranges and proprietary training-date ranges are not established. Do not substitute publication dates for collection dates.'),
('5d','Preprocessing','Reported','features','Common case inputs, released normalization, pooling, phase grid, thresholding and reference calculations are described, including unequal documentary/numerical validation depth.'),
('5e','Missingness','Reported','sample;features;inputs','The eligibility flow and available-muscle reference denominators are reported. Unavailable/inapplicable inputs remain explicit; the task does not ask models to impute missing channels.'),
('6a','Model identity','Reported with limits','config;inputs','Exact recorded API identifiers and inference dates are given. Final training dates are not established; permanent version pinning is not claimed.'),
('6b','Model building','Not applicable','inputs','The project used existing services without training or fine-tuning. Development-only item; proprietary internal training was not investigated.'),
('6c','Generation','Reported with limits','config;generation;inputs','Identical saved prompts, reasoning/output settings, provider-managed sampling and single-response design are reported. Within-model repeatability was not measured.'),
('6d','Output handling','Reported','generation;review','Saved prose and metadata were retained. Reviewer packets concealed identifiers and provider metadata while preserving report wording.'),
('6e','Classification','Not applicable','design;features','The LLM task generated reports, not class probabilities or outcome forecasts. EMG thresholds describe input features; they are not LLM decision cutoffs.'),
('7a','Output quality','Reported','outcomes;review','Case requirements and report-scoped errors are separate outcomes; unresolved claims remain distinct. The reference is researcher-defined, not clinical ground truth.'),
('7b','Task relevance','Reported with limits','intro;outcomes;discussion','Coverage and supported claims matter for interpreting supplied summaries. No association with clinical benefit or downstream decisions was measured.'),
('7c','Endpoints','Reported','outcomes;config','Definitions, API configurations, inference date, error denominators and paired participant analysis are supplied.'),
('7d','Assessors','Reported with limits','review;agreement','Three human UT Austin PhD students have at least five years of EMG/neuromuscular-control experience. Development roles and original agreement are disclosed; clinical credentials and further demographics are not established.'),
('7e','Comparators','Reported','outcomes;table3','All models receive identical within-case inputs. Paired coverage contrasts are distinguished from exploratory errors; no human-authored report benchmark was included.'),
('8a','Annotation guide','Reported','review;inputs','The approved rubric, worked examples, formal case requirements and later clarifications are separately identified. Those materials should accompany any permitted submission release.'),
('8b','Annotation extent','Reported','review;agreement','All 105 reports had original independent review by three humans. Assessed/excluded denominators and original pairwise agreement are reported by cohort and domain.'),
('8c','Annotator expertise','Reported','review','Academic status, institution, experience and involvement in criterion development are stated without inferring clinical licensure.'),
('9a','Prompt design','Reported with limits','inputs','The five-case trial and expert-reviewed interpretation instructions precede the formal batch. Exact prompts and approval records are available locally; no exhaustive prompt search is claimed.'),
('9b','Prompt cases','Reported','inputs;sample','Development cases are named: stroke Sub09, Sub05, Sub50, Sub47 and control Sub49. Formal case selection accounts for recorded prior exposure.'),
('10','Summarization inputs','Not applicable','features','Primary task is document generation from numerical features, not shortening source prose. Numerical preprocessing is nevertheless reported in Methods.'),
('11','Alignment','Not applicable','inputs','No project instruction tuning, preference training or alignment optimization occurred; prompting is described separately.'),
('12','Compute','Partial','config;generation;inputs','Output allowances and batch timing are supplied. Provider hardware, actual comparable compute, total inference cost and per-model latency summaries were not measured here.'),
('13','Ethics','Awaiting author','design;declarations;author','Original dataset approvals do not establish this secondary analysis determination. Obtain the actual institutional determination and applicable reference number.'),
('14a','Funding','Awaiting author','declarations;author','Authors must provide funding sources, grant identifiers and funder roles, or explicitly confirm no funding.'),
('14b','Conflicts','Awaiting author','declarations;author','Obtain each author\'s relevant financial and nonfinancial interests; do not infer a no-conflict statement.'),
('14c','Protocol','Not applicable','review','The published item targets live healthcare evaluation. Voluntary disclosure: an internal protocol exists at docs/formal_study/execution_analysis_v3_draft/PROTOCOL.md; the main text describes material departures.'),
('14d','Registration','Not applicable','review','The published item targets live healthcare evaluation. Voluntary disclosure: the main manuscript explicitly states that the study was not preregistered.'),
('14e','Data access','Partial','design;declarations;author','The source dataset is public. Permissions and exact public scope for derived inputs, reports and human ratings still require author confirmation.'),
('14f','Code access','Partial','suppreport;author','An offline replay bundle exists locally. A publishable version, repository access and licensing must be specified; local reproducibility is not public availability.'),
('15','Public involvement','Not applicable','design','No live healthcare evaluation was conducted. This applicability decision does not assert an unverified history of patient/public involvement.'),
('16a','Participant flow','Reported','sample;completion','Stroke flow is 50 to 43 complete to 27 without prior local reports to 25 after exclusions; 10 controls selected from 98 eligible; all 105 slots completed.'),
('16b','Characteristics','Partial','sample;table1;inputs','Cohort characteristics, selection and prompt-development cases are described. Source collection-date ranges are not reconstructed, and provider training overlap remains unknown.'),
('16c','Clinical outcomes','Not applicable','design;limitations','No patient outcome was predicted or evaluated and no clinical development/evaluation outcome comparison exists.'),
('16d','Denominators','Reported','table2;agreement','Participant, report, requirement, evaluable and unknown counts are distinguished; rating assignments are not independent participants.'),
('17','Performance','Reported','results','Main and original-independent results, paired coverage intervals, descriptive error counts, unresolved bounds and targeted sensitivity are reported without a global ranking.'),
('18','Model updates','Not applicable','config','No model updating was performed as part of this evaluation. Later service behavior is outside the saved-response study.'),
('19a','Interpretation','Reported with limits','discussion;inputs','Interpretation separates coverage from evidence fidelity and notes rating-stage dependence. Demographic fairness and subgroup performance were not assessed.'),
('19b','Limitations','Reported','limitations','Selected sample, single generation, researcher-defined reference, review changes, shared references, uncertain errors, length/compute and version drift are disclosed.'),
('19c','Data constraints','Reported','features;limitations','Pooled references, missing muscle data, cohort differences and documentary validation limits constrain transfer and interpretation.'),
('19d','Intended use','Reported with limits','inputs;design','Only offline draft-report evaluation by specialists is supported. Autonomous clinical decisions and patient-facing deployment were not tested.'),
('19e','Input quality','Not applicable','inputs;sample','Clinical deployment is not part of this study. Research eligibility and missingness rules are reported; no validated deployment quality-control policy is claimed.'),
('19f','User interaction','Not applicable','inputs;review','No implemented clinical workflow or end-user interaction study exists. Expert-review requirements are described, but clinical training requirements remain unvalidated.'),
('19g','Next studies','Reported','discussion;conclusion','Independent cases, prospectively specified wording rules, repeated outputs and a separate evaluation of clinical utility are proposed, not reported as completed.')]
ABSTRACT = [
('2a','Title','Partial','title','The title omits the stroke population and explicit evaluation label; see main item 1.'),
('2b','Rationale','Reported','abstract','The objective explains that fluent gait reports may omit findings or overstate evidence.'),
('2c','Objective','Reported','abstract','The stated objective is evaluation of completeness and evidence fidelity using a paired comparison.'),
('2d','Setting','Reported','abstract','An offline study using public motion-capture and EMG data is identified.'),
('2e','Data selection','Partial','abstract','The 25/10 cohort sizes are stated; eligibility selection and development-case exclusions remain in Methods rather than the abstract.'),
('2f','Models','Reported','abstract;config','The abstract supplies all three recorded model identifiers; Methods explains their versioning limits.'),
('2g','Building','Not applicable','inputs','No model building, fine-tuning or preference training occurred.'),
('2h','Task','Reported','abstract','Structured gait summaries are interpreted into reports; inputs, outputs and separate coverage/error assessment are identified.'),
('2i','Evaluation','Partial','abstract;sample','Cohorts and endpoints are given. External holdout status and unknown provider pretraining exposure are explained in Methods/supplement, not the abstract.'),
('2j','Findings','Reported','abstract','Coverage, paired-interval interpretation, evaluable errors, original error disagreement and targeted sensitivity are reported.'),
('2k','Implications','Reported','abstract','The conclusion separates the two quality dimensions and limits inference to the studied outputs and scoring procedure.'),
('2l','Registration','Not applicable','review','No live healthcare evaluation. Lack of preregistration is disclosed in the main Methods.')]

LOCATIONS = {
 'title':(M,'# Completeness and evidence fidelity'), 'abstract':(M,'## Abstract'),
 'intro':(M,'## Introduction'), 'design':(M,'### Study design'),
 'sample':(M,'### Case selection'), 'features':(M,'### Model-visible'),
 'config':(M,'### Model configuration'), 'review':(M,'### Expert assessment'),
 'outcomes':(M,'### Outcomes and analysis'), 'completion':(M,'### Sample and report completion'),
 'table1':(M,'### Table 1.'),'table2':(M,'### Table 2.'),'table3':(M,'### Table 3.'),
 'results':(M,'## Results'),'agreement':(M,'### Original independent agreement'),
 'discussion':(M,'## Discussion'),'limitations':(M,'## Limitations'),
 'conclusion':(M,'## Conclusion'),'declarations':(M,'## Declarations'),
 'inputs':(S,'## Inputs, prompts'),'generation':(S,'## Generation'),
 'suppreport':(S,'## Reporting scope'),'author':(A,'# Author confirmations')}


def main():
    source_paths = [M,S,A,'scripts/build_reporting_checklist.py',
      'docs/formal_study/candidate_v3_1/APPROVAL_RECORD.json',
      'docs/formal_study/rubric_v2_draft/RUBRIC.md',
      'docs/formal_study/rubric_v2_draft/EXAMPLES.md',
      'docs/formal_study/case_requirements_v1/case_requirements.csv',
      'docs/formal_study/execution_analysis_v3_draft/PROTOCOL.md']
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths}
    locations={}
    for key,(path,heading) in LOCATIONS.items():
        lines=(ROOT/path).read_text().splitlines()
        hits=[(i+1,line) for i,line in enumerate(lines) if line.startswith(heading)]
        assert len(hits)==1,(key,hits)
        line,title=hits[0]
        anchor=re.sub(r'[^a-z0-9_\- ]','',title.lstrip('# ').lower()).replace(' ','-')
        locations[key]={'file':path,'line':line,'section':title.lstrip('# '),'link':'../manuscript_v1/'+Path(path).name+'#'+anchor}
    rows=[]
    for section,items in [('Main',MAIN),('Abstract',ABSTRACT)]:
        for ident,label,status,keys,evidence in items:
            loc=[locations[k] for k in keys.split(';')]
            rows.append({'checklist':section,'item':ident,'topic':label,'status':status,'locations':loc,'evidence_or_remaining_work':evidence})
    assert len({(r['checklist'],r['item']) for r in rows})==len(rows)
    assert len(MAIN)==49 and len(ABSTRACT)==12
    OUT.mkdir(parents=True,exist_ok=True)
    intro=f'''# TRIPOD-LLM reporting checklist

Completed reporting assessment for the current manuscript; not an expert signature or certification of study quality.

Source: Gallifant et al., Nature Medicine 2025, published Tables 2 and 3 ([full official wording]({GUIDELINE})). This file uses that named version, accessed September 25, 2026, rather than claiming the latest living revision. Item identifiers follow the printed tables; short navigation labels below are not replacements for their full questions.

Scope: evaluation of existing LLMs (E), document generation (DG), offline. No model training, classification, outcome forecasting or live clinical deployment. Numerical feature preprocessing is described even though the summarization module is not selected. Every printed main and abstract identifier is addressed, including reasons for non-applicability.

Statuses: Reported = addressed for this study; Reported with limits = explicit unavailable information or unmeasured capability; Partial = additional reporting needed; Awaiting author = factual declaration not supplied; Not applicable = outside the selected design/task. None is an expert approval or a numerical quality score. Do not remove partial items to claim compliance.

Locations refer to the Markdown build; line numbers are navigation aids, not journal page numbers. The source hashes in BUILD_RECORD.json identify that build. Rebuild this checklist after manuscript changes; complete author declarations and verify target-journal requirements before submission.
'''
    md=intro
    wb=Workbook();readme=wb.active;readme.title='Read me'
    for line in intro.splitlines():readme.append([line])
    readme.column_dimensions['A'].width=125
    for section in ('Main','Abstract'):
        md+='\n## '+section+' checklist\n\n| Item | Topic | Status | Manuscript location | Evidence / remaining work |\n| --- | --- | --- | --- | --- |\n'
        ws=wb.create_sheet(section+' checklist');ws.append(['Item','Topic','Status','Manuscript section and line','Evidence / remaining work'])
        for r in [r for r in rows if r['checklist']==section]:
            loc='; '.join(f"[{l['section']}]({l['link']}) (line {l['line']})" for l in r['locations'])
            md+=f"| {r['item']} | {r['topic']} | {r['status']} | {loc} | {r['evidence_or_remaining_work']} |\n"
            ws.append([r['item'],r['topic'],r['status'],'; '.join(f"{l['file']}:{l['line']} ({l['section']})" for l in r['locations']),r['evidence_or_remaining_work']])
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for col,width in zip('ABCDE',[10,24,24,80,110]):ws.column_dimensions[col].width=width
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='224B63')
        for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=82
    for ws in wb:
        for row in ws:
            for cell in row:cell.alignment=Alignment(wrap_text=True,vertical='top')
    (OUT/'TRIPOD_LLM_CHECKLIST.md').write_text(md)
    (OUT/'CHECKLIST.json').write_text(json.dumps({'guideline':GUIDELINE,'version':'published 2025','research_design':'E','task':'DG','rows':rows},indent=2)+'\n')
    wb.save(OUT/'TRIPOD_LLM_CHECKLIST.xlsx')
    counts={section:dict(Counter(r['status'] for r in rows if r['checklist']==section)) for section in ('Main','Abstract')}
    record={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':sources,'counts':counts,
        'guideline':GUIDELINE,'complete_compliance_claimed':False,'new_expert_approval':False,
        'output_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('TRIPOD_LLM_CHECKLIST.md','TRIPOD_LLM_CHECKLIST.xlsx','CHECKLIST.json')}}
    for path,digest in sources.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    (OUT/'BUILD_RECORD.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'counts':counts}))

if __name__=='__main__':main()
