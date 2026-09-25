#!/usr/bin/env python3
"""Verify prepared rater delivery files without opening the model-identity key."""
from collections import Counter
from datetime import datetime,timezone
from html import unescape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import zipfile
from openpyxl import load_workbook
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/formal_study/rating_delivery_v1'
CANONICAL=ROOT/'data/rating_packets_formal_v1'
CJK=re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
IDENTITY=re.compile(r'\b(?:Claude|Anthropic|OpenAI|GPT(?:-\d+)?|Gemini|Google)\b',re.I)
REQUEST=re.compile(r'\b(?:chatcmpl-|msg_01|req_01|AIza|sk-ant-)')


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.remote=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v:
                self.links.append(v)
                if v.startswith(('https:','http:','//')):self.remote.append(v)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    integrity=json.loads((CANONICAL/'private/package_integrity.json').read_text())
    requirements=integrity['requirements']
    validations={};publics={};incidental=[];verified_images=set()
    for rater in ('rater1','rater2'):
        folder=BASE/rater;source=CANONICAL/'raters'/rater
        public=json.loads((folder/'reports.json').read_text());publics[rater]=public
        assert set(public)=={'order','reports'}
        assert len(public['order'])==len(set(public['order']))==len(public['reports'])==105
        assert list(public['reports'])==sorted(public['reports'])
        assert all(set(meta)=={'case_id','material_status'} for meta in public['reports'].values())
        assert all(meta['material_status']=='Available' for meta in public['reports'].values())
        cases=[public['reports'][rid]['case_id'] for rid in public['order']]
        assert len(set(cases))==35 and set(Counter(cases).values())=={3}
        assert sum(case.startswith('stroke_') for case in cases)==75
        assert sum(case.startswith('control_') for case in cases)==30
        assert all(case not in cases[max(0,i-2):i] for i,case in enumerate(cases))
        workbook=folder/'Independent_ratings.xlsx'
        assert sha(workbook)==sha(source/'Independent_ratings.xlsx')
        book=load_workbook(workbook,data_only=False)
        assert book.sheetnames==['Instructions','Review','Coverage','Issues']
        assert book['Review'].max_row==106 and book['Coverage'].max_row==553 and book['Issues'].max_row==1
        assert [row[0].value for row in list(book['Review'].rows)[1:]]==public['order']
        for row in book['Review'].iter_rows(min_row=2,values_only=True):
            assert row[2]=='Available' and row[3]=='Not started' and all(v is None for v in row[4:])
        requirement_count=Counter()
        for row in book['Coverage'].iter_rows(min_row=2,values_only=True):
            rid,case,req,wording,components,*judgments=row
            assert case==public['reports'][rid]['case_id'] and all(v is None for v in judgments)
            expected=requirements[case]
            if req!='G03':
                original=next(r for r in expected if r['requirement_id']==req)
                assert wording==original['required_wording'] and components==original['components']
            requirement_count[rid]+=1
        assert all(requirement_count[rid]==len(requirements[meta['case_id']])+1 for rid,meta in public['reports'].items())
        assert sum(row[2]=='G03' for row in book['Coverage'].iter_rows(min_row=2,values_only=True))==105
        assert all(book['Instructions'].cell(r,2).value is None for r in (15,16,17))
        assert len(book['Review'].data_validations.dataValidation)==4
        assert len(book['Coverage'].data_validations.dataValidation)==2
        assert len(book['Issues'].data_validations.dataValidation)==3
        for sheet in book:
            for row in sheet:
                for cell in row:
                    assert cell.data_type!='f'
                    if isinstance(cell.value,str):assert not CJK.search(cell.value)
        book.close()
        for rid in public['order']:
            text=(folder/'reports'/f'{rid}.txt').read_text()
            assert (folder/'reports'/f'{rid}.txt').read_bytes()==(source/'reports'/f'{rid}.txt').read_bytes()
            view=(folder/'reading'/f'{rid}.html').read_text()
            def embedded(key):return unescape(re.search(r'<pre id="'+key+r'">(.*?)</pre>',view,re.S).group(1))
            case=public['reports'][rid]['case_id']
            assert embedded('report-text')==text
            for key,filename in [('system-text','model_system_prompt.txt'),('user-text','model_user_prompt.txt'),('reference-text','reference_card.md')]:
                assert embedded(key)==(folder/'materials'/case/filename).read_text()
            if IDENTITY.search(text):incidental.append({'rater':rater,'report_id':rid,'action':'Retained verbatim; identity terms require human contextual review, not automatic removal'})
            assert not REQUEST.search(text)
        checked_links=0
        for file in folder.rglob('*'):
            if not file.is_file():continue
            relative=str(file.relative_to(folder))
            assert not any(x in file.parts for x in ('private','__MACOSX'))
            assert not any(x in relative.lower() for x in ('answer_key','mapping','run_manifest','event-'))
            assert not IDENTITY.search(relative)
            if file.suffix in {'.txt','.md','.json','.html'}:
                text=file.read_text();assert not CJK.search(text),relative
                assert not REQUEST.search(text),relative
                if file.suffix=='.html':
                    parser=Links();parser.feed(text);assert not parser.remote
                    for link in parser.links:
                        if link.startswith('#'):continue
                        target=(file.parent/link.split('#')[0]).resolve()
                        assert target.is_relative_to(folder.resolve()) and target.is_file(),(relative,link)
                        checked_links+=1
                # Exact text is retained, even if a model names itself. Non-report metadata must not name providers.
                if file.suffix=='.json':assert not IDENTITY.search(text),relative
            elif file.suffix=='.png':
                h=sha(file)
                if h not in verified_images:
                    with Image.open(file) as img:img.verify()
                    verified_images.add(h)
        for name,expected in integrity['files_sha256'].items():
            prefix=f'raters/{rater}/'
            if name.startswith(prefix):
                relative=name[len(prefix):]
                if relative=='reports.json':assert json.loads((folder/relative).read_text())==json.loads((source/relative).read_text())
                else:assert sha(folder/relative)==expected
        archive=BASE/f'Formal_review_{rater}.zip'
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            files={str(Path(rater)/p.relative_to(folder)):p for p in folder.rglob('*') if p.is_file()}
            assert set(z.namelist())==set(files)
            assert len({i.date_time for i in z.infolist()})==1
            for name,path in files.items():assert z.read(name)==path.read_bytes()
        validations[rater]={'reports':105,'cases':35,'review_rows':105,'coverage_rows':552,'case_specific_coverage_rows':447,'g03_rows':105,'human_judgments_blank':True,'minimum_same_case_spacing':'At least two other reports','all_canonical_report_workbook_and_material_bytes_preserved':True,'report_html_and_input_html_text_exact':True,'local_links_verified':checked_links,'archive_crc_and_all_entry_bytes_verified':True,'archive_entry_count':len(files),'metadata_sorted_by_opaque_id':True,'model_identity_fields_absent_from_public_metadata':True,'no_private_files_in_delivery':True,'no_chinese_characters_in_text_or_workbook_cells':True,'zip_sha256':sha(archive)}
    assert publics['rater1']['order']!=publics['rater2']['order']
    assert publics['rater1']['reports']==publics['rater2']['reports']
    # Check workbook XML/properties too; public IDs, not provider identities, are permitted.
    for rater in validations:
        with zipfile.ZipFile(BASE/rater/'Independent_ratings.xlsx') as z:
            for name in z.namelist():
                if name.endswith('.xml'):
                    text=z.read(name).decode()
                    assert not IDENTITY.search(text) and not REQUEST.search(text),name
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'status':'Passed artifact, workbook, archive and static navigation checks','raters':validations,'independent_orders_differ':True,'report_id_set_shared_for_later_reconciliation':True,'unique_curve_images_verified':len(verified_images),'possible_report_self_identification':incidental,'private_model_key_read':False,'human_ratings_created':False,'model_calls':0,'delivery_sent':False,'browser_rendering_test_performed':False,'validation_script_sha256':sha(Path(__file__))}
    (BASE/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'reports_per_rater':105,'coverage_rows_per_rater':552,'independent_orders_differ':True,'possible_report_self_identification_count':len(incidental),'zip_files_verified':2,'all_judgments_blank':True},indent=2))


if __name__=='__main__':main()
