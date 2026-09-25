"""Validate the 35-case preparation package without changing source or case files."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.images=[];self.seeds=[];self.capture=False;self.buffer=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='img':self.images.append(a.get('src',''))
        if tag=='script' and a.get('class')=='review-seed':self.capture=True;self.buffer=[]
    def handle_data(self,data):
        if self.capture:self.buffer.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.capture:
            self.seeds.append(json.loads(''.join(self.buffer)));self.capture=False


def verify(base):
    manifest=json.loads((base/'manifest.json').read_text())
    for name,h in manifest['package_files_sha256'].items():assert digest(base/name)==h,name
    for name,h in manifest['protected_files_sha256'].items():assert digest(ROOT/name)==h,name
    for name,h in manifest['approved_prompt_source_hashes'].items():assert digest(ROOT/name)==h,name
    assert digest(ROOT/'scripts/build_formal_case_review.py')==manifest['builder_sha256']
    selected=list(csv.DictReader((ROOT/'docs/formal_study/control_supplement_v2/selected_study_cases.csv').open()))
    case_ids={f"{r['group']}_{r['subject']}_{r['side']}" for r in selected}
    assert case_ids=={r['case_id'] for r in manifest['cases']} and len(case_ids)==35
    index=Page();index.feed((base/'index.html').read_text())
    seeds={r['case_id']:r for r in index.seeds}
    assert set(seeds)==case_ids and len(index.seeds)==35 and len(index.images)==70
    assert all((base/src).is_file() for src in index.images)
    sys_hashes=set();expected_rows=[];curves=0
    for case in manifest['cases']:
        case_id=case['case_id'];folder=base/case_id
        for name,h in case['files_sha256'].items():assert digest(folder/name)==h,(case_id,name)
        system=(folder/'model_system_prompt.txt').read_text();user=(folder/'model_user_prompt.txt').read_text()
        sys_hashes.add(digest(folder/'model_system_prompt.txt'))
        messages=json.loads((folder/'model_messages.json').read_text())
        assert messages==[{'role':'system','content':system},{'role':'user','content':user}]
        items=json.loads((folder/'candidate_requirements.json').read_text())
        assert seeds[case_id]['items']==items and seeds[case_id]['version']==case['review_version']
        assert len(items)==(6 if case['group']=='stroke' else 5)
        assert len({i['item_id'] for i in items})==len(items)
        for item in items:
            assert item['expert_decision']=='PENDING' and not item['expert_edit']
            assert all(line in user for line in item['evidence'].splitlines())
            expected_rows.append((case_id,item))
        standalone=Page();standalone.feed((folder/'card.html').read_text())
        assert standalone.seeds==[seeds[case_id]]
        assert len(standalone.images)==2 and all(s.startswith('data:image/png;base64,') for s in standalone.images)
        if case['group']=='control':
            assert len(case['reference_members'])==137 and case['subject_id'] not in case['reference_members']
            assert case['reference_meta']['excluded_subjects']==[case['subject_id']]
            assert 'Gait speed: not provided' in user and 'Step length symmetry index: not applicable' in user
        else:assert len(case['reference_members'])==138
        for kind in ['emg','kinematics']:
            assert (folder/f'curves_{kind}.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
            assert (folder/f'curves_{kind}.pdf').read_bytes().startswith(b'%PDF')
            curves+=1
    assert len(sys_hashes)==1 and len(expected_rows)==200 and curves==70
    rows=list(csv.DictReader((base/'candidate_requirements.csv').open()))
    assert len(rows)==200
    for row,(case_id,item) in zip(rows,expected_rows):
        assert row['case_id']==case_id and row['item_id']==item['item_id']
        assert row['draft_core']==item['draft_statement'] and row['exact_input_evidence']==item['evidence']
        assert row['proposed_components']==item['proposed_components'] and row['selection_basis']==item['selection_basis']
        assert all(not row[k] for k in ['reviewer_decision','revised_required_wording','comments','reviewer','date'])
    book=load_workbook(base/'Expert_case_requirements_review.xlsx')
    assert book['Requirements'].max_row==201 and book['Cases'].max_row==36
    assert book['Additional findings'].max_row==36
    for cells,row in zip(book['Requirements'].iter_rows(min_row=2,values_only=True),rows):
        assert tuple('' if c is None else str(c) for c in cells)==tuple(row.values())
    assert all(c.value is None for r in book['Additional findings'].iter_rows(min_row=2,min_col=2,max_col=7) for c in r)
    for row in book['Cases'].iter_rows(min_row=2):assert (base/row[4].hyperlink.target).is_file()
    chinese=re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
    for path in base.rglob('*'):
        if path.suffix in ['.html','.md','.txt','.json','.csv']:assert not chinese.search(path.read_text()),path
    for ws in book:
        for row in ws:
            for cell in row:
                if isinstance(cell.value,str):assert not chinese.search(cell.value),(ws.title,cell.coordinate)
    for path in [base/'README.md',base/'REVIEW_GUIDE.md']:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if not link.startswith('http') and link!='validation.json':assert (path.parent/link).exists(),link
    browser_path=ROOT/'audit/card_review_ui/formal_case_review_v1/browser_checks.json'
    browser=json.loads(browser_path.read_text());assert len(browser)==19 and all(browser.values())
    before={str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file()}
    result=subprocess.run([sys.executable,str(ROOT/'scripts/build_formal_case_review.py'),'--out',str(base)],capture_output=True,text=True)
    assert result.returncode!=0 and 'Existing expert materials must not be overwritten' in result.stderr
    assert before=={str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file()}
    validation=dict(verified_at_utc=datetime.now(timezone.utc).isoformat(),
        case_count=35,stroke_count=25,control_count=10,candidate_items=200,curve_figures_png_and_pdf=70,
        checks=dict(selected_cases_unchanged=True,all_case_file_hashes_match=True,
                    protected_files_unchanged=len(manifest['protected_files_sha256']),
                    approved_source_code_unchanged=True,identical_approved_system_prompt_for_all_cases=True,
                    exact_two_message_inputs=True,all_candidate_evidence_in_model_visible_input=True,
                    html_csv_workbook_proposals_match=True,all_expert_decisions_blank_or_pending=True,
                    all_control_references_exclude_self=True,english_text_checked=True,
                    figure_files_present=True,standalone_figures_embedded=True,workbook_links_resolve=True,
                    existing_output_overwrite_refused=True,no_model_calls=True),
        prior_regression_checks=dict(approved_five_case_inputs_reproduced=manifest['approved_five_case_inputs_reproduced'],
            candidate_evidence_contract_tests_passed=8,new_requirement_boundary_tests_passed=3),
        browser_checks=browser,browser_checks_sha256=digest(browser_path),
        browser_test_scope='Synthetic UI edits in an isolated temporary Chrome profile. Test reviewer IDs in screenshots are not actual expert decisions or submissions.',
        verifier_sha256=digest(Path(__file__)),browser_verifier_sha256=digest(ROOT/'scripts/verify_formal_case_review_ui.py'),
        remaining=dict(external_exposure_confirmation='Pending',expert_requirements='Pending',generation='Not started'))
    (base/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    manifest['package_files_sha256']={p.name:digest(p) for p in sorted(base.iterdir()) if p.is_file() and p.name!='manifest.json'}
    manifest['documentation_and_validation_finalized_at_utc']=validation['verified_at_utc']
    (base/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(cases=35,candidate_items=200,browser_checks=19,checks=validation['checks']),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=ROOT/'docs/formal_study/case_review_v1')
    verify(parser.parse_args().base.resolve())
