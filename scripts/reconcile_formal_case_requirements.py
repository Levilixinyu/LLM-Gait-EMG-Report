"""Compare two returned expert workbooks without deciding clinical consensus."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/formal_study/case_review_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(ws):
    rows=list(ws.values)
    return [dict(zip(rows[0],r)) for r in rows[1:] if any(v is not None for v in r)]


def addition_present(text):
    return str(text or '').strip().lower().rstrip('.') not in {'','none','none proposed','no additions','no additional findings'}


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def json_write(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,default=str)+'\n')


def build(out):
    if out.exists():raise FileExistsError('Preserve the existing discussion package; choose a new version.')
    manifest=json.loads((BASE/'manifest.json').read_text())
    sources={};visual_assets={};deferred_assets={}
    for rel,h in manifest['package_files_sha256'].items():
        if Path(rel).suffix in {'.html','.png','.pdf'}:
            visual_assets[str((BASE/rel).relative_to(ROOT))]=h
            continue
        if (BASE/rel).stat().st_flags & 0x40000000:
            deferred_assets[str((BASE/rel).relative_to(ROOT))]=h
            continue
        assert sha(BASE/rel)==h,rel
        sources[str((BASE/rel).relative_to(ROOT))]=h
    for case in manifest['cases']:
        for filename,h in case['files_sha256'].items():
            path=BASE/case['case_id']/filename
            if path.suffix in {'.html','.png','.pdf'}:
                visual_assets[str(path.relative_to(ROOT))]=h
                continue
            if path.stat().st_flags & 0x40000000:
                deferred_assets[str(path.relative_to(ROOT))]=h
                continue
            assert sha(path)==h,path
            sources[str(path.relative_to(ROOT))]=h
    template=load_workbook(BASE/'Expert_case_requirements_review.xlsx',data_only=False)
    original=records(template['Requirements']);assert len(original)==200
    original_keys=[(r['case_id'],r['item_id']) for r in original]
    expected_cases={r['case_id'] for r in original}
    returns={};checks={};chinese=re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
    for who in ['rater1','rater2']:
        path=BASE/f'Expert_case_requirements_review_{who}.xlsx';sources[str(path.relative_to(ROOT))]=sha(path)
        wb=load_workbook(path,data_only=False)
        sheets={ws.title:records(ws) for ws in wb}
        req=sheets['Requirements'];assert [(r['case_id'],r['item_id']) for r in req]==original_keys
        for src,row in zip(original,req):
            assert all(row[k]==src[k] for k in list(src)[:6]),(who,row['case_id'],row['item_id'],'source altered')
            assert row['reviewer_decision'] in {'Retain','Modify','Omit'}
            assert row['reviewer']==who and row['date']
            if row['reviewer_decision']=='Modify':assert str(row['revised_required_wording'] or '').strip()
            else:assert not row['revised_required_wording'], 'Non-Modify replacement requires clarification'
        assert list(wb['Cases'].values)==list(template['Cases'].values)
        assert {r['case_id'] for r in sheets['Additional findings']}==expected_cases
        for ws in wb:
            for row in ws:
                for cell in row:
                    assert cell.data_type!='f',(who,ws.title,cell.coordinate,'unexpected formula')
                    if isinstance(cell.value,str):assert not chinese.search(cell.value),(who,ws.title,cell.coordinate)
        provenance_checks=[]
        for r in sheets.get('Review provenance',[]):
            rel=r['Source path relative to project'];p=Path(rel)
            assert not p.is_absolute() and '..' not in p.parts and 'private' not in p.parts and 'answer_key' not in rel.lower()
            assert (ROOT/p).is_file() and sha(ROOT/p)==r['SHA-256'],(who,rel,'provenance mismatch')
            provenance_checks.append(rel)
        addition_checks=[]
        for r in sheets['Additional findings']:
            if not addition_present(r.get('new_required_finding')):continue
            user=(BASE/r['case_id']/'model_user_prompt.txt').read_text()
            evidence=str(r.get('exact_input_evidence') or '')
            parts=evidence.split(' | ') if ' | ' in evidence else evidence.splitlines()
            assert parts and all(p.strip() and p.strip() in user for p in parts),(who,r['case_id'],'addition evidence')
            addition_checks.append(r['case_id'])
        checks[who]=dict(source_fields_match=True,complete_decisions=200,all_modifications_have_wording=True,
            reviewer_and_date_present=True,english_text_checked=True,provenance_hashes_verified=len(provenance_checks),
            addition_evidence_checked=len(addition_checks),counts=dict(Counter(r['reviewer_decision'] for r in req)))
        returns[who]=sheets
    topics=[
        ('T01','How to choose essential EMG findings',
         'Rater1 proposes at least one substantive descriptive EMG route for every complete-EMG control. Rater2 omits all initial EMG core items in seven controls, using the pooled 4.61 endpoint as a priority heuristic with exceptions.',
         'Do not equate percentile classification with whether a descriptive finding merits inclusion. Consider at least one input-supported EMG finding or explicit alternative in each complete-EMG control. A pooled endpoint is not a matched LOO threshold. This is a proposal, not a new accepted rule.',
         'Agree a content-priority principle and revisit the seven affected controls; distinguish optional descriptive content from clinical normality.'),
        ('T02','Joint priorities, rankings and GVS-versus-ROM contrasts',
         'Rater1 often narrows to one joint or permits a second-joint alternative. Rater2 sometimes requires both secondary joints or a small/comparable-magnitude summary. Pelvic GVS-versus-excursion contrasts overlap in three cases.',
         'Define essential joints and any OR alternatives case by case. Preserve explicit GVS-versus-excursion contrasts where jointly justified. Do not convert the approximate 1.5-degree or 8-degree review heuristics into validated clinical thresholds.',
         'Resolve N02 rows, especially Sub07, Sub13, Sub15, Sub18, Sub22, Sub30, Sub38 and controls Sub07/Sub14/Sub117.'),
        ('T03','One or two EMG findings, alternatives and mixed directions',
         'Both may include EMG but disagree on mandatory second muscles or alternatives. Rater1 sometimes replaces the draft channel, for example ERS with below-mean TA/VL in stroke Sub34.',
         'Compare muscle identity, above/below direction, approximate location and AND/OR logic, not just Retain versus Modify labels. A replacement can change the required content substantially.',
         'Resolve retained-core routes, including stroke Sub02/Sub15/Sub18/Sub19/Sub21/Sub22/Sub24/Sub27/Sub34/Sub40/Sub49 and control Sub31.'),
        ('T04','Threshold coverage as a required finding',
         'Rater1 proposes case-specific N05 replacements in stroke Sub10, Sub13 and Sub24. Rater2 omits every N05 row.',
         'Decide these three cases on descriptive value and redundancy. The approved rubric does not create a universal ban on threshold findings; retaining a case-specific requirement still needs agreement. Rounded 100% does not establish physiological duration.',
         'Decide each of the three N05 rows, and coordinate any interval alternatives already included in N03.'),
        ('T05','Three proposed CCI additions',
         'Rater1 adds TA-GAS CCI in stroke Sub25/Sub33 and RF-BF CCI in Sub40. Rater2 proposes no added stroke requirement and states that CCI remains optional.',
         'The supplied comparisons are supported (0.71/0.78 above 0.24-0.59; 0.46 below 0.48-0.83). Whether they are essential is a content-priority decision. Do not generalize these comparisons to physiology or automatically require every out-of-range CCI.',
         'Retain, revise or omit each addition; record the final core and any numeric requirement.'),
        ('T06','Control GPS-like and duplicate coverage',
         'Rater1 omits all control N01 items, sometimes allowing GPS-like under N02. Rater2 requires N01 for four controls above the supplied median: Sub62, Sub73, Sub06 and Sub39.',
         'Decide whether GPS-like adds an essential finding beyond joint summaries. Above the pooled median is not itself a validated importance cutoff or a matched LOO normality test. Permit an explicit OR route if this avoids duplicate mandatory content.',
         'Resolve four inclusion disputes and N02 alternatives for controls Sub07/Sub14.'),
        ('T07','Shared control provenance addition',
         'Both propose healthy-control identity, self-exclusion from the reference and domain-specific conditional handling of missing speed/cadence or inapplicable paretic/non-paretic index for all ten controls.',
         'Proposed common wording: identify healthy-control membership AND that the comparison excludes this participant. IF speed is discussed, state it was not supplied; IF cadence is discussed, state it was not supplied; IF the task-specific paretic/non-paretic index is discussed, state it is not applicable. Each branch triggers only for its own domain. Exact count 137 is optional; G03 remains separate.',
         'Confirm one shared wording and explicitly record that it applies to all ten new control cases.'),
        ('T08','Required components, optional anchors and contextual caveats',
         'Retain comments can qualify the draft. Modified text differs on exact magnitude, ranking, indeterminate classification and negative disclaimers; some comments mention routes not present in replacement wording.',
         'State the final core and component logic separately from optional anchors and prohibited inferences. Do not require a standalone negative disclaimer simply to earn coverage. About 5% for a small step difference is not a validated severity cutoff.',
         'Check comments alongside wording, including stroke Sub16 N03 and the scope of small/comparable degree words; record a complete final requirement, not only Agree.')]
    def topic_ids(case,item):
        if item=='N02':return 'T02;T08'
        if item in ['N03','N04']:return 'T01;T03;T08'
        if item=='N05':return 'T04'
        if item=='N01' and case.startswith('control_'):return 'T06'
        return 'T08'
    comparisons=[]
    for i,(source,a,b) in enumerate(zip(original,returns['rater1']['Requirements'],returns['rater2']['Requirements']),1):
        d1,d2=a['reviewer_decision'],b['reviewer_decision']
        category=('Both omit original' if d1==d2=='Omit' else 'Both retain original' if d1==d2=='Retain'
                  else 'Core inclusion differs' if (d1=='Omit')!=(d2=='Omit') else 'Both include; wording/components to align')
        comparisons.append(dict(comparison_id=f'R{i:03d}',case_id=source['case_id'],item_id=source['item_id'],
            comparison_status=category,discussion_topics=topic_ids(source['case_id'],source['item_id']),
            original_core=source['draft_core'],original_components=source['proposed_components'],original_input_evidence=source['exact_input_evidence'],
            rater1_decision=d1,rater1_effective_wording=a['revised_required_wording'] if d1=='Modify' else source['draft_core'] if d1=='Retain' else '',
            rater1_comments=a['comments'] or '',rater2_decision=d2,
            rater2_effective_wording=b['revised_required_wording'] if d2=='Modify' else source['draft_core'] if d2=='Retain' else '',
            rater2_comments=b['comments'] or '',final_decision='',final_required_wording='',final_components_and_optional_content='',
            consensus_evidence='',confirmed_by='',confirmation_date=''))
    add_maps={who:{r['case_id']:r for r in sheets['Additional findings']} for who,sheets in returns.items()}
    additions=[]
    for case in [r['case_id'] for r in records(template['Cases'])]:
        a,b=add_maps['rater1'][case],add_maps['rater2'][case]
        p1,p2=addition_present(a.get('new_required_finding')),addition_present(b.get('new_required_finding'))
        if not (p1 or p2):continue
        additions.append(dict(addition_id=f'A{len(additions)+1:03d}',case_id=case,
            comparison_status='Both propose; wording to confirm' if p1 and p2 else 'Rater1 proposal; no Rater2 addition',
            discussion_topic='T07' if case.startswith('control_') else 'T05',
            rater1_proposal=a.get('new_required_finding') if p1 else '',rater1_components=a.get('components_or_alternatives') or '',
            rater1_evidence=a.get('exact_input_evidence') or '',rater1_reason=a.get('reason') or '',
            rater2_proposal=b.get('new_required_finding') if p2 else '',rater2_components=b.get('components_or_alternatives') or '',
            rater2_evidence=b.get('exact_input_evidence') or '',rater2_reason=b.get('reason') or '',
            final_decision='',final_required_wording='',final_components_and_optional_content='',consensus_evidence='',confirmed_by='',confirmation_date=''))
    counts=dict(Counter(r['comparison_status'] for r in comparisons))
    assert counts=={'Both retain original':47,'Both include; wording/components to align':82,'Both omit original':52,'Core inclusion differs':19}
    assert len(additions)==13 and sum(r['case_id'].startswith('control_') for r in additions)==10
    no_emg={who:[case for case in sorted(expected_cases) if case.startswith('control_') and
                  all(r['reviewer_decision']=='Omit' for r in sheets['Requirements'] if r['case_id']==case and r['item_id'] in ['N03','N04','N05'])]
            for who,sheets in returns.items()}
    out.mkdir(parents=True)
    write_csv(out/'item_comparison.csv',comparisons);write_csv(out/'additional_findings_comparison.csv',additions)
    json_write(out/'source_returns.json',returns)
    workbook=Workbook();workbook.remove(workbook.active)
    instructions=[dict(topic='Status',instruction='Two completed independent returns received. This is a comparison and discussion aid, not signed consensus.'),
        dict(topic='Order',instruction='Discuss Shared questions first; then Priority items, Wording alignment and Additions. All 200 original rows remain in Full comparison.'),
        dict(topic='Decision location',instruction='Enter final case decisions only in Full comparison or Additions. Navigation sheets link to those authoritative rows. Shared-question decisions guide but do not silently finalize case rows.'),
        dict(topic='Meaning of counts',instruction='47 both retain, 52 both omit, 82 both include with wording/components to align, and 19 inclusion disputes. These are descriptive comparison counts, not inter-rater reliability or formal consensus.'),
        dict(topic='Comments matter',instruction='Retain can be qualified by comments. Both Modify does not imply the same requirement. Numeric anchors, AND/OR routes and replacement muscle identities must be checked.'),
        dict(topic='New additions',instruction='Ten common control-provenance proposals plus three CCI proposals from rater1. A None/None proposed entry is not a requirement.'),
        dict(topic='No approval inference',instruction='Final decision, wording, evidence, confirmer and date fields are intentionally blank. Preserve both original workbooks; no expert signature or exposure confirmation is inferred.'),
        dict(topic='Generation',instruction='Do not generate reports from unresolved candidate requirements. Exposure, new-case consensus, outcome analysis and generation/failure rules remain separate pending work.')]
    shared=[dict(topic_id=i,topic=t,observed_difference=d,agent_advice_for_discussion=a,decision_needed=n,
                 agreed_rule='',confirmed_by='',confirmation_date='',notes='') for i,t,d,a,n in topics]
    priority=[];wording=[]
    for i,row in enumerate(comparisons,2):
        target=priority if row['comparison_status']=='Core inclusion differs' else wording if row['comparison_status']=='Both include; wording/components to align' else None
        if target is not None:target.append(dict(comparison_id=row['comparison_id'],case_id=row['case_id'],item_id=row['item_id'],
            topics=row['discussion_topics'],rater1=row['rater1_decision'],rater2=row['rater2_decision'],comparison_row=i))
    sheet_rows=[('Read first',instructions),('Shared questions',shared),('Priority items',priority),('Wording alignment',wording),('Additions',additions),('Full comparison',comparisons)]
    for title,rows in sheet_rows:
        ws=workbook.create_sheet(title);ws.append(list(rows[0]))
        for row in rows:ws.append(list(row.values()))
        ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions;ws.row_dimensions[1].height=45
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24476B')
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(65,max(16,max(len(str(c.value or '')) for c in col)+2))
            for c in col:c.alignment=Alignment(wrap_text=True,vertical='top')
        for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=140 if title not in ['Priority items','Wording alignment'] else 45
        headers=list(rows[0])
        if 'final_decision' in headers:
            col=headers.index('final_decision')+1;letter=ws.cell(1,col).column_letter
            dv=DataValidation(type='list',formula1='"Retain,Modify,Omit,Pending discussion"',allow_blank=True);dv.showErrorMessage=True
            ws.add_data_validation(dv);dv.add(f'{letter}2:{letter}{ws.max_row}')
            for row in ws.iter_rows(min_row=2,min_col=col):
                for c in row:c.fill=PatternFill('solid',fgColor='E8F1FA')
        if title in ['Priority items','Wording alignment']:
            for row in ws.iter_rows(min_row=2):
                row[-1].hyperlink=f"#'Full comparison'!A{row[-1].value}";row[-1].style='Hyperlink'
    workbook.save(out/'Case_requirements_reconciliation.xlsx')
    summary=dict(status='Independent reviews complete; consensus pending',review_validation=checks,
        comparison_counts=counts,addition_rows=13,both_propose_control_additions=10,rater1_only_stroke_additions=3,
        controls_without_required_EMG_under_each_return=no_emg,
        return_sha256={who:sources[str((BASE/f'Expert_case_requirements_review_{who}.xlsx').relative_to(ROOT))] for who in returns},
        final_consensus=False,external_exposure_confirmation='Pending',model_calls=0,
        verification_scope='Locally available non-visual package files, both source workbooks, and reviewer provenance hashes verified. Visual assets and other iCloud placeholders were not rehashed in the package sweep; their prior manifest hashes are retained separately. Addition evidence was checked against actual model input text.',
        inference_limits='Comparison labels are mechanical. Agent discussion advice is not an expert adjudication. Independence is stated in returns, not independently witnessed.')
    json_write(out/'summary.json',summary)
    assert all(sha(ROOT/p)==h for p,h in sources.items())
    json_write(out/'manifest.json',dict(created_at_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__)),
        source_sha256=sources,prior_visual_asset_sha256_not_reverified=visual_assets,
        prior_placeholder_sha256_not_reverified=deferred_assets,
        output_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},no_original_evidence_modified=True))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    build(parser.parse_args().out.resolve())
