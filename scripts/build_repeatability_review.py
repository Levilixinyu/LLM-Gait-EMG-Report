"""Build three independent reviewer packets for the completed two-wave supplement.

No model calls, original ratings, or new expert decisions are involved.
Provider/repeat identities and randomization seeds stay in an ignored private store.
"""
from collections import Counter
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import csv
import hashlib
import json
import os
import random
import re
import secrets
import sys
import tempfile
import zipfile

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.formal_rating import _workbook, _literal_row
from src.llm.formal_generation import digest
from src.llm.repeatability_batch_v2 import validate_plan
from scripts.build_formal_rating_delivery import page

PACKAGE = ROOT / 'docs/formal_study/repeatability_supplement_v2'
RESULTS = ROOT / 'data/reports_repeatability_v1'
ASSETS = ROOT / 'docs/formal_study/rating_delivery_v1/rater2/materials'
OUT = ROOT / 'docs/formal_study/repeatability_rating_delivery_v2'
PRIVATE = ROOT / 'data/rating_packets_repeatability_v2/private'
RATERS = ('rater1', 'rater2', 'rater3')
CASE_FILES = ('model_system_prompt.txt', 'model_user_prompt.txt', 'reference_card.md',
              'curves_emg.png', 'curves_kinematics.png')
CJK = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n')


def spaced_order(groups, seed, minimum_distance=8):
    """Six hidden construction blocks, independent of generation wave and content."""
    if len(groups) != 25 or any(len(v) != 6 for v in groups.values()):
        raise ValueError('Expected 25 cases with six new texts per case')
    rng = random.Random(seed)
    queues = {case: list(ids) for case, ids in sorted(groups.items())}
    for ids in queues.values():
        rng.shuffle(ids)
    order, case_sequence = [], []
    for block in range(6):
        for _ in range(10000):
            cases = list(queues)
            rng.shuffle(cases)
            joined = case_sequence[-(minimum_distance - 1):] + cases
            if all(joined[i] not in joined[max(0, i-minimum_distance+1):i] for i in range(len(joined))):
                break
        else:
            raise ValueError('Could not satisfy case spacing')
        order.extend(queues[c][block] for c in cases)
        case_sequence.extend(cases)
    return order


GUIDE = '''# How to review the repeated-generation reports

## Start

Extract the entire ZIP. Open START_HERE.html in a browser and Independent_ratings.xlsx in Excel. Everything needed for review is included and works offline. Browser pages do not save ratings. Save a separate working copy as Independent_ratings_{rater}_completed.xlsx; keep the delivered template unchanged.

Complete the Pre_review sheet before scoring: your name, start date, relevant prior access and any reservations. Prior case familiarity is expected. Model-identity exposure and exposure to peer judgments are separate questions; describe either honestly. Do not search for model identities or read peer ratings while scoring. Your view does not have to agree with another reviewer's view.

## For each report

Follow the fixed numbered order, resuming where you stopped. Each reading page links the exact report, exact text inputs, reference card, curves and applicable Coverage rows. Only the saved text inputs were supplied to the model. Curves help check the evidence but do not create mandatory findings that were unavailable to the model.

1. Read the whole report and its case requirements. Apply the current supplement instructions and the approved rubric. The rubric's historical five-case annex is illustrative; the requirements already populated in this workbook govern these 25 cases.
2. Fill Coverage columns F-H: decision, Final/Pending status and evidence/reason. Covered requires the substantive components of one permitted route. Partially covered means a meaningful subset. Not covered means none. Correct numbers without the required interpretation, including a magnitude-sorted list without explanation, receive Partially covered. Equivalent phrasing elsewhere in the report is sufficient. Do not assign half-points.
3. G03 appears once per report. Judge whether meaningful reference-comparability and inference limits are conveyed; do not require an age/speed keyword checklist or a duplicate sentence. Cannot assess is for missing, corrupt or mismatched materials, not for a cautious, poor or short report. A provisional coverage decision can remain Pending with an explanation; Final means your settled judgment, not consensus.
4. Add one Issues row for each distinct issue group. Use a report ID from Review and a local issue ID such as I001. Choose Error, Acceptable, Pending adjudication or Outside case-error scope. Give E01-E09 category tags separated by semicolons, an exact contiguous quotation copied from the text file, locations and your reason. Repeated equivalent claims in one report share an issue group; different claims remain separate. Leave Issues empty for a report with no issues. Do not add a placeholder error.
5. A clinical question may propose a possibility for verification. It is not an error merely for mentioning a mechanism or impairment. Separately inspect false numbers, wrong identities and explicit unsupported factual premises. Explain unresolved interpretations as Pending; do not force a common answer. Coverage and errors remain separate, and an error need not remove coverage earned elsewhere.
6. Complete Review columns D-H: Completed, issue_review_complete = Yes, four-section format, incidental unblinding and notes. Yes means your issue search is complete, not that the report is error-free. Pending can coexist with a completed review. Mark incidental_unblinding only for an actually known identity or explicit identification, not a stylistic guess; describe the circumstance.

All cases in this packet are stroke cases. The two control-only fields in Issues are retained for format compatibility; leave them blank or select No. They are not additional stroke endpoints.

## Partial capture

One report contains only the text saved before an administrative interruption. Its reading page and Delivery_status sheet identify it without a model name. Read and rate what is present; do not infer missing text or replace it with a prior report. A requirement absent from the captured text is assessed as absent from that text, without attributing the interruption to the model. Record uncertainty where appropriate. The study analysis separately flags this capture, excludes its pair from the principal complete-capture comparison and retains it in operational accounting and sensitivity analyses. This is an operational record, not a prefilled quality judgment.

## Return

There are 150 Review rows and 864 Coverage rows (714 case-specific judgments and 150 G03 judgments). Check them all, including issue-free reports. After completing your independent review, enter your name, completion date as YYYY-MM-DD text, and Yes in Instructions B15-B17. Do not enter a completion confirmation early. Retain any Pending judgments with reasons.

Return only Independent_ratings_{rater}_completed.xlsx. Keep worksheet names, IDs, requirement wording and reading order unchanged. Do not send your scores to the other reviewers before all three independent submissions have been saved. Questions about missing files may go to the study lead; scoring uncertainty belongs in your own reasons and Pending fields.
'''


def enhance_workbook(path, rater, order, public, partial_ids):
    book = load_workbook(path)
    instructions = book['Instructions']
    instructions['B2'] = 'Use only your packet. Do not consult peer ratings before all three independent submissions are saved.'
    instructions['B9'] = 'Stroke-only packet: leave both control-only issue flags blank or select No.'
    instructions['B10'] = 'Do not infer physiological normality from descriptive reference comparisons.'
    instructions['B14'] = 'Complete Pre_review first. Complete Review, Coverage and Issues; sign B15-B17 only after finishing. Return a separate completed workbook.'
    _literal_row(instructions, ['Workload', '150 reports; 714 case requirements plus 150 G03 judgments = 864 coverage rows.'])
    _literal_row(instructions, ['Partial capture', 'See Delivery_status and the reading-page notice. Judge the available text without reconstructing missing content.'])
    pre = book.create_sheet('Pre_review')
    for row in [
        ['Field', 'Reviewer response', 'Instructions'],
        ['Reviewer name', '', 'Enter before starting; not prefilled.'],
        ['Start date', '', 'YYYY-MM-DD as text.'],
        ['Prior case/rubric involvement', '', 'Describe prior case review and criteria development or clarification involvement.'],
        ['Prior access to model identities or comparison results', '', 'Yes/No/Unsure; describe what and when. This need not prevent review, but must be recorded.'],
        ['Prior access to these new report identities', '', 'Yes/No/Unsure; describe any identities already known.'],
        ['Prior access to peer ratings or proposed answers for these new reports', '', 'Yes/No/Unsure; distinguish these new texts from prior historical discussions.'],
        ['Prior access to the supplement interruption record', '', 'Yes/No/Unsure; state whether it revealed a model identity.'],
        ['Relevant EMG / neuromuscular-control experience', '', 'Optional update if already recorded with the study lead.'],
        ['Reservations or material questions before review', '', 'Write None if none; this is not a request to endorse prior decisions.'],
        ['Independent review arrangement understood', '', 'Enter Yes when understood; this is not a completion signature.'],
    ]:
        _literal_row(pre, row)
    delivery = book.create_sheet('Delivery_status')
    _literal_row(delivery, ['report_id', 'case_id', 'capture_status', 'review_handling'])
    for rid in order:
        _literal_row(delivery, [rid, public[rid]['case_id'],
            'Partial text: administrative interruption' if rid in partial_ids else 'Normal stream completion',
            'Rate only captured text; operationally flagged separately.' if rid in partial_ids else 'Review the verbatim text.'])
    book.defined_names.add(DefinedName('ReportIDs', attr_text="'Review'!$A$2:$A$151"))
    dv = DataValidation(type='list', formula1='ReportIDs', allow_blank=True)
    dv.showErrorMessage = True
    book['Issues'].add_data_validation(dv)
    dv.add('A2:A5000')
    for sheet in book:
        sheet.freeze_panes = 'F2' if sheet.title == 'Coverage' else 'A2'
        for cell in sheet[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='254B60')
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
        sheet.sheet_view.showGridLines = True
    for col in ('A', 'B'):
        book['Coverage'].column_dimensions[col].width = 25
    for col in ('D', 'E', 'H'):
        book['Coverage'].column_dimensions[col].width = 64
    for col in ('A', 'B', 'C'):
        pre.column_dimensions[col].width = 58
    delivery.column_dimensions['A'].width = 25
    delivery.column_dimensions['B'].width = 25
    delivery.column_dimensions['C'].width = 45
    delivery.column_dimensions['D'].width = 64
    book.save(path)


class InspectHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.pre_id = None
        self.blocks = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.links.extend(a[k] for k in ('href', 'src') if k in a)
        if tag == 'pre':
            self.pre_id = a.get('id')
            if self.pre_id:
                self.blocks[self.pre_id] = ''

    def handle_data(self, data):
        if self.pre_id:
            self.blocks[self.pre_id] += data

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.pre_id = None


def verify_folder(folder, order, public, texts, requirements):
    book = load_workbook(folder/'Independent_ratings.xlsx', data_only=False)
    assert book['Review'].max_row == 151 and book['Coverage'].max_row == 865
    assert book['Issues'].max_row == 1
    assert [r[0] for r in book['Review'].iter_rows(min_row=2, values_only=True)] == order
    assert all(book['Instructions'].cell(n, 2).value is None for n in (15, 16, 17))
    assert all(r[1] is None for r in book['Pre_review'].iter_rows(min_row=2, values_only=True))
    expected_coverage = []
    from src.eval.formal_rating import G03
    for rid in order:
        case = public[rid]['case_id']
        for req in requirements[case] + [{'requirement_id':'G03', 'required_wording':G03, 'components':'AND: comparability and inference limitations'}]:
            expected_coverage.append((rid, case, req['requirement_id'], req['required_wording'], req['components']))
    observed = list(book['Coverage'].iter_rows(min_row=2, values_only=True))
    assert [r[:5] for r in observed] == expected_coverage
    assert all(all(v is None for v in r[5:]) for r in observed)
    assert all(r[3] == 'Not started' and all(v is None for v in r[4:]) for r in book['Review'].iter_rows(min_row=2, values_only=True))
    assert len(book['Coverage'].data_validations.dataValidation) == 2
    for sheet in book:
        assert sheet.sheet_state == 'visible'
        for row in sheet:
            for cell in row:
                assert cell.data_type != 'f'
                if isinstance(cell.value, str):
                    assert not CJK.search(cell.value)
    book.close()
    assert len(list((folder/'reports').glob('*.txt'))) == 150
    for rid in order:
        assert (folder/'reports'/f'{rid}.txt').read_bytes() == texts[rid]
        inspector = InspectHTML()
        inspector.feed((folder/'reading'/f'{rid}.html').read_text())
        assert inspector.blocks['report-text'] == texts[rid].decode()
        for label, filename in [('system-text','model_system_prompt.txt'), ('user-text','model_user_prompt.txt')]:
            assert inspector.blocks[label] == (folder/'materials'/public[rid]['case_id']/filename).read_text()
    for file in folder.rglob('*'):
        if not file.is_file():
            continue
        assert not any(w in file.name.lower() for w in ('answer_key', 'completed', 'manifest', 'build_record'))
        if file.suffix in ('.md', '.txt', '.json', '.csv', '.html'):
            raw = file.read_text()
            assert not CJK.search(raw), file
            assert 'repeat_v1_r0' not in raw and '/Users/' not in raw
        if file.suffix == '.html':
            inspector = InspectHTML(); inspector.feed(file.read_text())
            for link in inspector.links:
                assert '://' not in link and not link.startswith('/'), (file, link)
                target = (file.parent/link.split('#')[0]).resolve()
                assert target.is_relative_to(folder.resolve()) and target.is_file(), (file, link)
    return {'reports':150, 'review_rows':150, 'coverage_rows':864, 'all_judgments_blank':True,
        'report_bytes_and_html_verified':True, 'all_html_links_resolve':True, 'all_text_english':True}


def build():
    if OUT.exists() or PRIVATE.exists():
        raise FileExistsError('Do not overwrite an issued packet or private mapping')
    plan = json.loads((PACKAGE/'EXECUTION_PLAN.json').read_text())
    validate_plan(plan, live=True)
    done = json.loads((PACKAGE/'GENERATION_COMPLETION.json').read_text())
    assert done['all_slots_terminal'] and done['terminal_slots'] == 150
    assert sha(RESULTS/'RESULTS.json') == done['results_sha256']
    result = json.loads((RESULTS/'RESULTS.json').read_text())
    assert result['plan_sha256'] == digest(plan)
    rows = result['reports']; tasks = {t['slot_id']:t for t in plan['tasks']}
    assert len(rows) == len(tasks) == 150
    assert {r['slot_id'] for r in rows} == set(tasks)
    assert Counter(r['repeat'] for r in rows) == {1:75, 2:75}
    for row in rows:
        assert row['task_sha256'] == digest(tasks[row['slot_id']])
        file = RESULTS/'captured_reports'/(row['slot_id']+'.txt')
        assert sha(file) == done['report_file_sha256'][str(file.relative_to(ROOT))]
        assert file.read_bytes() == row['report_text'].encode()
    cases = sorted({r['case_id'] for r in rows})
    source_requirements = ROOT/'docs/formal_study/case_requirements_v1/case_requirements.csv'
    req_rows = list(csv.DictReader(source_requirements.open()))
    requirements = {c:[] for c in cases}
    for row in req_rows:
        if row['case_id'] in requirements and row['included'] == 'Yes':
            assert row['confirmation_status'] == 'Confirmed by both reviewers'
            requirements[row['case_id']].append({'requirement_id':row['record_id'],
                'required_wording':row['required_wording'], 'components':row['required_components_and_optional_content']})
    integrity = json.loads((ROOT/'data/rating_packets_formal_v1/private/package_integrity.json').read_text())
    assert sum(map(len, requirements.values())) == 119
    assert all(requirements[c] == integrity['requirements'][c] for c in cases)
    case_assets = {}
    sources = {str(p.relative_to(ROOT)):sha(p) for p in [PACKAGE/'EXECUTION_PLAN.json', PACKAGE/'GENERATION_COMPLETION.json',
        RESULTS/'RESULTS.json', source_requirements, PACKAGE/'REVIEW_INSTRUCTIONS.md', Path(__file__).resolve()]}
    for case in cases:
        case_assets[case] = {}
        for name in CASE_FILES:
            file = ASSETS/case/name
            assert sha(file) == integrity['files_sha256'][f'raters/rater2/materials/{case}/{name}']
            case_assets[case][name] = file.read_bytes()
            sources[str(file.relative_to(ROOT))] = sha(file)
        for task in [t for t in tasks.values() if t['case_id']==case]:
            assert case_assets[case]['model_system_prompt.txt'] == task['system_prompt'].encode()
            assert case_assets[case]['model_user_prompt.txt'] == task['user_prompt'].encode()
    common = {}
    for name in ('RUBRIC.md','EXAMPLES.md','RUBRIC_APPROVAL_STATUS.md','rubric.json'):
        file = ASSETS/name
        assert sha(file) == integrity['files_sha256'][f'raters/rater2/materials/{name}']
        common[name] = file.read_bytes(); sources[str(file.relative_to(ROOT))] = sha(file)
    common['REVIEW_INSTRUCTIONS.md'] = (PACKAGE/'REVIEW_INSTRUCTIONS.md').read_bytes()
    common['CURRENT_REVIEW_SCOPE.md'] = b'''# Current supplement review scope

Review 150 new texts from 25 stroke cases. Use the 119 unchanged case-specific requirements already populated in Coverage, plus G03 once per report. There are no new control reports. The approved rubric is preserved verbatim; its historical draft wording and five-case annex are superseded in scope by this packet's requirements and supplement instructions. Its approval-status document is historical, not a request to repeat earlier study preparation. D01-D03 apply from the outset as explained in REVIEW_INSTRUCTIONS.md. Preserve your own first-pass judgments and any Pending interpretations. Do not copy historical scores or seek agreement before independent submissions are saved.
'''
    public, mapping, texts, groups, partial_ids = {}, {}, {}, {c:[] for c in cases}, set()
    for row in rows:
        rid = 'R'+secrets.token_hex(8).upper()
        assert rid not in public
        public[rid] = {'case_id':row['case_id'], 'material_status':'Available'}
        mapping[rid] = {k:v for k,v in row.items() if k != 'report_text'}
        texts[rid] = row['report_text'].encode()
        groups[row['case_id']].append(rid)
        if not row['normal_stream_completion']:
            partial_ids.add(rid)
    assert len(partial_ids) == 1
    seeds = {r:secrets.randbits(128) for r in RATERS}
    orders = {r:spaced_order(groups, seeds[r]) for r in RATERS}
    assert len({tuple(x) for x in orders.values()}) == 3
    stage = Path(tempfile.mkdtemp(prefix='repeatability_review_', suffix='.building', dir=OUT.parent))
    summaries = {}
    for rater in RATERS:
        folder = stage/rater
        for sub in ('reports','materials','reading'):
            (folder/sub).mkdir(parents=True)
        for name, raw in common.items():
            (folder/'materials'/name).write_bytes(raw)
        for case, assets in case_assets.items():
            dest = folder/'materials'/case; dest.mkdir()
            for name, raw in assets.items():
                (dest/name).write_bytes(raw)
        for rid, raw in sorted(texts.items()):
            (folder/'reports'/f'{rid}.txt').write_bytes(raw)
        order = orders[rater]
        save_json(folder/'reports.json', {'order':order, 'reports':dict(sorted(public.items()))})
        with (folder/'materials/case_requirements.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=['case_id','requirement_id','required_wording','components'])
            writer.writeheader()
            writer.writerows({'case_id':c, **r} for c in cases for r in requirements[c])
        _workbook(folder/'Independent_ratings.xlsx', rater, order, public, requirements)
        enhance_workbook(folder/'Independent_ratings.xlsx', rater, order, public, partial_ids)
        guide = GUIDE.format(rater=rater)
        (folder/'HOW_TO_REVIEW.md').write_text(guide)
        (folder/'HOW_TO_REVIEW.html').write_text(page('How to review', '<nav><a href="START_HERE.html">Report list</a> <a href="Independent_ratings.xlsx">Workbook</a></nav><section><pre>'+escape(guide)+'</pre></section>'))
        for name in ('RUBRIC','EXAMPLES','RUBRIC_APPROVAL_STATUS','CURRENT_REVIEW_SCOPE','REVIEW_INSTRUCTIONS'):
            (folder/'reading'/f'{name}.html').write_text(page(name.replace('_',' '), '<nav><a href="../START_HERE.html">Report list</a> <a href="../HOW_TO_REVIEW.html">Filling guide</a></nav><section><pre>'+escape(common[name+'.md'].decode())+'</pre></section>'))
        book = load_workbook(folder/'Independent_ratings.xlsx', read_only=True)
        coverage = {rid:[] for rid in order}
        for n, row in enumerate(book['Coverage'].iter_rows(min_row=2, values_only=True), 2):
            coverage[row[0]].append((n,row))
        book.close()
        links = []
        for pos, rid in enumerate(order, 1):
            case = public[rid]['case_id']; assets = case_assets[case]
            nav = '<a href="../START_HERE.html">Report list</a> <a href="../HOW_TO_REVIEW.html">Guide</a> <a href="../Independent_ratings.xlsx">Workbook</a>'
            if pos>1: nav += f' <a href="{order[pos-2]}.html">Previous</a>'
            if pos<len(order): nav += f' <a href="{order[pos]}.html">Next</a>'
            notice = '<p class="notice">Partial text saved before an administrative interruption. Rate only the captured text; this is separately flagged in the analysis.</p>' if rid in partial_ids else ''
            table = ''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in (n,row[2],row[3],row[4]))+'</tr>' for n,row in coverage[rid])
            content = f'<header><nav>{nav}</nav><h1>{rid}</h1><p>{rater} / {pos} of 150 / Case {case} / Review row {pos+1}</p>{notice}</header><section><h2>Report: verbatim text</h2><a href="../reports/{rid}.txt">Text file for exact quotations</a><pre id="report-text">{escape(texts[rid].decode())}</pre></section><section><h2>Coverage rows</h2><table><tr><th>Excel row</th><th>ID</th><th>Required content</th><th>Components</th></tr>{table}</table></section>'
            for label, name, title in [('system-text','model_system_prompt.txt','Exact system input'),('user-text','model_user_prompt.txt','Exact case input'),('reference-text','reference_card.md','Reference card')]:
                content += f'<details><summary>{title}</summary><a href="../materials/{case}/{name}">Saved file</a><pre id="{label}">{escape(assets[name].decode())}</pre></details>'
            content += '<details><summary>Expert reference curves</summary><p>Only text inputs were supplied to the model. Do not require curve-only findings.</p>'
            for name,title in [('curves_emg.png','EMG'),('curves_kinematics.png','Kinematics')]:
                content += f'<h2>{title}</h2><a href="../materials/{case}/{name}"><img src="../materials/{case}/{name}" alt="{title} curves: {case}" loading="lazy"></a>'
            content += f'</details><section><nav>{nav}</nav></section>'
            (folder/'reading'/f'{rid}.html').write_text(page(rid, content))
            links.append(f'<tr><td>{pos}</td><td><a href="reading/{rid}.html">{rid}</a></td><td>{case}</td><td>{pos+1}</td></tr>')
        content = f'<header><h1>Independent supplement review: {rater}</h1><p>150 texts / 25 stroke cases / 864 coverage judgments</p><nav><a href="HOW_TO_REVIEW.html">Step-by-step guide</a><a href="Independent_ratings.xlsx">Rating workbook</a><a href="reading/REVIEW_INSTRUCTIONS.html">Supplement rules</a><a href="reading/RUBRIC.html">Rubric</a><a href="reading/EXAMPLES.html">Examples</a><a href="reading/RUBRIC_APPROVAL_STATUS.html">Rubric approval</a><a href="reading/CURRENT_REVIEW_SCOPE.html">Current scope</a></nav></header><section><h2>Before starting</h2><p>Save a separate working copy of the workbook and complete Pre_review. Follow the fixed order below across sessions. Keep your judgments independent; do not consult the other reviewers. The browser does not save ratings.</p><p>One capture is incomplete because of an administrative interruption and is marked on its page. All report text is preserved verbatim. Model and repetition labels are withheld; wording may still suggest an identity. Record known exposure without guessing.</p></section><section><h2>Reading order</h2><table><tr><th>Position</th><th>Report</th><th>Case</th><th>Review row</th></tr>{"".join(links)}</table></section>'
        (folder/'START_HERE.html').write_text(page('Start here', content))
        (folder/'README.md').write_text(f'# Independent supplement review: {rater}\n\nExtract the full ZIP, open START_HERE.html, and read HOW_TO_REVIEW.html. Complete Pre_review before scoring. Record judgments in Independent_ratings.xlsx and return a separate Independent_ratings_{rater}_completed.xlsx. There are 150 reports and 864 coverage rows. No prior scores or model identity mapping are included. Keep your independent judgments separate from later discussion.\n')
        checks = verify_folder(folder, order, public, texts, requirements)
        archive = stage/f'Repeatability_review_{rater}.zip'
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for file in sorted(folder.rglob('*')):
                if file.is_file():
                    info = zipfile.ZipInfo(str(Path(rater)/file.relative_to(folder)), date_time=(2026,9,25,0,0,0))
                    info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
                    z.writestr(info, file.read_bytes())
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for name in z.namelist():
                assert z.read(name) == (stage/name).read_bytes()
        summaries[rater] = {**checks, 'zip':archive.name, 'zip_sha256':sha(archive), 'zip_bytes':archive.stat().st_size}
        (stage/f'MESSAGE_TO_{rater.upper()}.md').write_text(f'''Dear {rater},

Please independently review the 150 new stroke-gait reports in Repeatability_review_{rater}.zip. Extract the whole archive and open {rater}/START_HERE.html. It contains the reports, exact inputs, reference cards and curves, current case requirements, rubric, examples and filling instructions.

Before scoring, complete Pre_review in Independent_ratings.xlsx. Then follow your assigned reading order and complete Review, Coverage and any Issues. There are 864 coverage rows. One administratively interrupted capture is clearly marked; assess only the available text as explained in the guide.

Use your own judgment and retain Pending where needed. Agreement with another reviewer is not required. Please do not consult peer ratings or prior case-level scores during this review. Record any prior knowledge of model identities/results and any incidental unblinding.

Save a separate completed copy as Independent_ratings_{rater}_completed.xlsx. Enter the completion name/date/confirmation only after finishing, and return that workbook to me. Keep the original template unchanged. Thank you.
''')
    now = datetime.now(timezone.utc).isoformat()
    record = {'created_utc':now, 'source_sha256':sources, 'raters':summaries,
        'new_reports':150, 'case_requirements':119, 'coverage_rows_per_reviewer':864,
        'normal_captures':149, 'partial_captures':1, 'model_calls':0, 'human_judgments_created':False,
        'delivery_sent':False, 'independent_orders':True, 'minimum_same_case_position_distance':8,
        'blinding_limit':'Identifiers withheld; verbatim style, prior exposure and operational knowledge may reveal identity.'}
    save_json(stage/'BUILD_RECORD.json', record)
    (stage/'README.md').write_text('# Repeatability review delivery\n\nSend each reviewer only their named Repeatability_review_raterN.zip and matching message. Each ZIP is self-contained and has its own reading order. Do not send the project root or private output store. Start with raterN/START_HERE.html after extraction. All judgments and confirmations are blank.\n\n150 new report records, including one partial administrative capture; 25 stroke cases; 864 coverage rows per reviewer. The original reports and original ratings are not included. Private model/repeat mappings and randomization seeds are stored outside this delivery directory. No files have been sent.\n')
    PRIVATE.mkdir(parents=True, mode=0o700)
    save_json(PRIVATE/'answer_key_DO_NOT_SHARE.json', {'mapping':mapping, 'order_seeds':seeds, 'orders':orders})
    os.chmod(PRIVATE/'answer_key_DO_NOT_SHARE.json', 0o600)
    save_json(PRIVATE/'package_integrity.json', {'requirements':requirements,
        'files_sha256':{str(f.relative_to(stage)):sha(f) for f in sorted(stage.rglob('*')) if f.is_file()}})
    os.rename(stage, OUT)
    print(json.dumps({'delivery':str(OUT), 'raters':summaries}, indent=2))


if __name__ == '__main__':
    build()
