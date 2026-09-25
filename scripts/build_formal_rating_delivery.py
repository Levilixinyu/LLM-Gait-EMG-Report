#!/usr/bin/env python3
"""Create shareable rater-only copies with offline reading pages and guidance.

Keep the canonical package and its private integrity/key files unchanged.
Only public metadata key ordering is normalized; report and workbook bytes stay exact.
"""
from pathlib import Path
from html import escape
import hashlib
import json
import shutil
import sys
import zipfile
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'data/rating_packets_formal_v1'
OUT = ROOT / 'docs/formal_study/rating_delivery_v1'
STYLE = '''body{font:17px/1.6 system-ui,sans-serif;color:#182c35;background:#f3f6f7;margin:0}main{max-width:1100px;margin:auto;padding:28px}header,section,details{background:white;padding:20px 25px;border:1px solid #d4dfe3;border-radius:10px;margin:18px 0}h1{line-height:1.25;font-size:29px}h2{font-size:23px}a{color:#075c78}nav{display:flex;gap:18px;flex-wrap:wrap}.notice{background:#eaf4f5;padding:14px;border-left:4px solid #187786}table{border-collapse:collapse;width:100%;background:white}th,td{border:1px solid #d4dfe3;padding:10px;text-align:left;vertical-align:top}th{background:#eaf0f3}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:16px/1.65 system-ui,sans-serif}code{overflow-wrap:anywhere}img{max-width:100%;height:auto}summary{cursor:pointer;font-weight:650}.scroll{overflow:auto}.small{font-size:14px;color:#465e69}@media print{nav{display:none}body{background:white}main{max-width:none;padding:0}details{break-inside:avoid}table{font-size:12px}}'''


def page(title, content):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><style>'+STYLE+'</style></head><body><main>'+content+'</main></body></html>'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n')


def guide(rater, categories):
    tags=''.join('<tr><td>'+escape(c['id'])+'</td><td>'+escape(c['name'])+'</td></tr>' for c in categories)
    return page('How to complete the independent review', f'''<header><nav><a href="START_HERE.html">Report list</a><a href="Independent_ratings.xlsx">Open rating workbook</a><a href="reading/RUBRIC.html">Approved rubric</a><a href="reading/EXAMPLES.html">Examples</a></nav><h1>Independent review: {rater}</h1><p>105 reports, 35 cases, 552 coverage judgments. Use your own packet and follow its fixed order across sessions. Do not compare ratings with the other reviewer until both independent reviews are locked.</p></header>
<section><h2>1. Start with the workbook and report list</h2><p>Extract the whole ZIP first. Open <strong>START_HERE.html</strong> in a browser and <strong>Independent_ratings.xlsx</strong> in Excel or another spreadsheet editor that supports dropdown lists. The reading pages work offline. Record all judgments in the workbook; the browser pages do not save ratings.</p><p>Save your working copy as <strong>Independent_ratings_{rater}_completed.xlsx</strong>. Keep the delivered template unchanged. Do not rename sheets, columns, report IDs or requirements, and do not sort the review order.</p></section>
<section><h2>2. Read one report with its evidence</h2><p>Open reports in the numbered list order. Each page shows the exact report, its case requirements, links to the exact model inputs, the reference card and the EMG/kinematic curves. The model received the saved system and user text, not the expert curves. Do not require observations that were visible only in the expert plots.</p><p>The approved rubric retains historical draft wording and a five-case developmental annex. Its later approval is documented in the <a href="reading/RUBRIC_APPROVAL_STATUS.html">approval status</a>. For these 35 cases, use the requirements already populated in <strong>Coverage</strong>, including G03 once per report. Read the <a href="reading/CURRENT_REVIEW_SCOPE.html">current review scope</a>.</p></section>
<section><h2>3. Complete Coverage</h2><p>For the current report ID, fill columns F-H. The reading page identifies the corresponding spreadsheet rows.</p><table><tr><th>Column</th><th>What to enter</th></tr><tr><td>F: decision</td><td>Covered, Partially covered or Not covered. Use the substantive meaning and AND/OR branches, not word matching. Cannot assess is for missing, corrupt or mismatched review materials, not a cautious or poor report.</td></tr><tr><td>G: adjudication_status</td><td>Final when your independent judgment is settled; Pending when a reading remains unresolved. Final here is your own judgment, not agreement with the other reviewer.</td></tr><tr><td>H: evidence_and_reason</td><td>Record supporting evidence and the missing/wrong component where relevant. For Pending, explain the competing readings; a provisional category is permitted and a final category need not be forced.</td></tr></table><p>Coverage and errors are separate: a correct required statement may earn coverage even if an unretracted contradiction elsewhere also needs an issue row. Do not convert partial coverage into a numerical score. G03 requires reference-comparability and inference limits; age and speed are not individually mandatory keywords.</p></section>
<section><h2>4. Record issues in Issues</h2><p>Add one row per distinct issue group, starting at row 2. If you find no issues, leave this sheet without a row for that report; completion is recorded in Review. Do not add a placeholder error.</p><table><tr><th>Field</th><th>What to enter</th></tr><tr><td>report_id</td><td>Copy the exact report ID from the reading page or Review.</td></tr><tr><td>issue_id</td><td>Use a unique ID within that report, for example I001, I002.</td></tr><tr><td>decision</td><td>Error, Acceptable, Pending adjudication or Outside case-error scope.</td></tr><tr><td>categories</td><td>Use E01-E09; separate multiple tags with semicolons, for example E02;E09. An Error or Pending adjudication row needs at least one applicable tag.</td></tr><tr><td>exact_quote</td><td>Copy an exact contiguous passage from the saved report, preserving spelling and punctuation. Do not paraphrase or join separate passages into one quotation. Error and Pending adjudication rows require a quote.</td></tr><tr><td>locations</td><td>Identify the section/paragraph and all repetitions of that same issue. A repeated presupposition in a question belongs to the same group when it asserts the same problem.</td></tr><tr><td>reason</td><td>Explain the judgment using the supplied input and approved rubric. Keep design concerns and format issues separate from case errors.</td></tr></table><details><summary>Error category names</summary><table><tr><th>Tag</th><th>Name</th></tr>{tags}</table><p>Apply the full scope and boundaries in the approved rubric; these names do not replace its definitions.</p></details></section>
<section><h2>5. Add the two control flags only where applicable</h2><p>For each issue row on a control report, fill both <strong>pathology_flag</strong> and <strong>normality_flag</strong> with Yes or No. These annotate an existing Error or Pending adjudication issue; they are not extra errors or penalties.</p><ul><li><strong>pathology_flag:</strong> unsupported disease, pathological deficit/mechanism or clinical impairment.</li><li><strong>normality_flag:</strong> unsupported normal physiology, timing/function or overall normal gait.</li></ul><p>Yes on a pending issue marks its potentially qualifying meaning; it does not turn that issue into a confirmed error. Acceptable and Outside case-error scope rows use No for both flags. For stroke rows, leave these two fields blank or select No.</p><p>Do not mark a flag merely because a report states control membership, a displayed reference comparison or a qualified open assessment question. Judge a question that presupposes a deficit under the existing error rules. The later report-level aggregation keeps confirmed, pending and negative states separate; you do not need to calculate it.</p></section>
<section><h2>6. Mark that report completed in Review</h2><p>Complete columns D-H. Set <strong>review_state = Completed</strong> and <strong>issue_review_complete = Yes</strong> after reading the whole report and recording any issues. Yes means the issue search is complete, not that the report is error-free. This can coexist with documented Pending judgments.</p><p>Record <strong>four_section_format</strong> separately using Yes, No or Cannot assess. Record <strong>incidental_unblinding</strong> as Yes or No; if the text explicitly reveals a model identity or identity becomes known, describe the circumstance in notes. Do not search for the model or edit the report. A stylistic guess is not a confirmed identity.</p><p>If review materials are missing or mismatched, document the problem and request the correct copy. Do not silently score a missing file as a model omission. A short or incomplete captured report remains assessable as the actual output.</p></section>
<section><h2>7. Check and return your completed workbook</h2><p>After all 105 reports, check all 552 coverage rows and finish the Instructions sheet: reviewer name (B15), completion date (B16, ISO YYYY-MM-DD as text), and independent review complete (B17: Yes). If your editor converts the date into a date object, prefix it with an apostrophe to keep text. Do not enter a name, completion date or Yes until you have completed your independent review.</p><p>Return only your saved <strong>Independent_ratings_{rater}_completed.xlsx</strong>, unless you need to attach a separate material-problem note. Keep pending judgments with their reasons for later discussion. Do not send or request the other reviewer's ratings before both independent submissions are locked.</p></section>''')


def build():
    if OUT.exists():
        raise FileExistsError('Delivery already exists; do not replace a delivered package')
    integrity=json.loads((CANONICAL/'private/package_integrity.json').read_text())
    OUT.mkdir()
    result={}
    for rater in ('rater1','rater2'):
        source=CANONICAL/'raters'/rater; dest=OUT/rater
        # Named rater subtree only: never copy the package root or private key.
        shutil.copytree(source,dest)
        public=json.loads((dest/'reports.json').read_text())
        public['reports']=dict(sorted(public['reports'].items()))
        write_json(dest/'reports.json',public)
        original=json.loads((source/'reports.json').read_text())
        assert public==original
        book=load_workbook(source/'Independent_ratings.xlsx',read_only=True,data_only=False)
        coverage={rid:[] for rid in public['order']}
        for number,row in enumerate(book['Coverage'].iter_rows(min_row=2,values_only=True),2):
            coverage[row[0]].append((number,row))
        book.close()
        reading=dest/'reading';reading.mkdir()
        categories=json.loads((dest/'materials/rubric.json').read_text())['error_categories']
        (dest/'HOW_TO_REVIEW.html').write_text(guide(rater,categories))
        for name in ('RUBRIC','EXAMPLES','RUBRIC_APPROVAL_STATUS','CURRENT_REVIEW_SCOPE'):
            raw=(dest/'materials'/f'{name}.md').read_text()
            content='<nav><a href="../START_HERE.html">Report list</a><a href="../HOW_TO_REVIEW.html">How to review</a></nav><section><h1>'+escape(name.replace('_',' ').title())+'</h1><p class="small">Verbatim saved document. The approval status and current review scope explain historical draft and five-case wording.</p><pre id="document-text">'+escape(raw)+'</pre></section>'
            (reading/f'{name}.html').write_text(page(name,content))
        table=[]
        for position,rid in enumerate(public['order'],1):
            case=public['reports'][rid]['case_id']
            text=(source/'reports'/f'{rid}.txt').read_text()
            previous=f'<a href="{public["order"][position-2]}.html">Previous report</a>' if position>1 else ''
            following=f'<a href="{public["order"][position]}.html">Next report</a>' if position<len(public['order']) else ''
            requirements=''.join('<tr><td>'+str(n)+'</td><td>'+escape(row[2])+'</td><td>'+escape(row[3])+'</td><td>'+escape(row[4])+'</td></tr>' for n,row in coverage[rid])
            asset=f'../materials/{case}/'
            system=(dest/'materials'/case/'model_system_prompt.txt').read_text()
            user=(dest/'materials'/case/'model_user_prompt.txt').read_text()
            reference=(dest/'materials'/case/'reference_card.md').read_text()
            content=f'''<header><nav><a href="../START_HERE.html">Report list</a><a href="../HOW_TO_REVIEW.html">Filling instructions</a><a href="../Independent_ratings.xlsx">Rating workbook</a>{previous}{following}</nav><p class="small">{rater} / Report {position} of 105 / Review spreadsheet row {position+1}</p><h1>{rid}</h1><p>Case: <strong>{case}</strong></p><p class="notice">Read this report independently. Record judgments in the workbook. Browser pages do not save ratings.</p></header>
<section><h2>Report: exact saved text</h2><p><a href="../reports/{rid}.txt">Open the original text file</a></p><pre id="report-text">{escape(text)}</pre></section>
<section><h2>Requirements for this report</h2><p>Fill the corresponding Coverage rows in the workbook. G03 is included once. These are the approved requirements, not prefilled judgments.</p><div class="scroll"><table><tr><th>Excel row</th><th>ID</th><th>Required content</th><th>Components / optional content</th></tr>{requirements}</table></div></section>
<details><summary>Exact model input: system instruction</summary><p><a href="{asset}model_system_prompt.txt">Original file</a></p><pre id="system-text">{escape(system)}</pre></details>
<details><summary>Exact model input: case summary</summary><p><a href="{asset}model_user_prompt.txt">Original file</a></p><pre id="user-text">{escape(user)}</pre></details>
<details><summary>Reference context for expert review</summary><p><a href="{asset}reference_card.md">Original file</a></p><pre id="reference-text">{escape(reference)}</pre></details>
<details><summary>EMG and kinematic curves</summary><p>The curves are supplementary expert evidence. Only the saved text inputs were supplied to the model; do not require curve-only observations.</p><h2>EMG</h2><a href="{asset}curves_emg.png"><img src="{asset}curves_emg.png" alt="EMG curves for {case}" loading="lazy"></a><h2>Kinematics</h2><a href="{asset}curves_kinematics.png"><img src="{asset}curves_kinematics.png" alt="Kinematic curves for {case}" loading="lazy"></a></details>
<section><nav>{previous}<a href="../START_HERE.html">Report list</a>{following}</nav></section>'''
            (reading/f'{rid}.html').write_text(page(f'{rid} - independent review',content))
            table.append(f'<tr><td>{position}</td><td><a href="reading/{rid}.html">{rid}</a></td><td>{case}</td><td>{position+1}</td></tr>')
        content=f'''<header><h1>Independent formal review: {rater}</h1><p>105 anonymous reports / 35 cases / 552 coverage judgments.</p><nav><a href="HOW_TO_REVIEW.html">Read the filling guide</a><a href="Independent_ratings.xlsx">Open the rating workbook</a><a href="reading/RUBRIC.html">Approved rubric</a><a href="reading/EXAMPLES.html">Examples</a><a href="reading/CURRENT_REVIEW_SCOPE.html">Current scope</a></nav></header><section><h2>Start here</h2><ol><li>Extract the complete ZIP before opening these pages.</li><li>Save a separate working copy of the workbook and follow its Instructions sheet.</li><li>Review reports in the order below across sessions. The workbook uses the same order.</li><li>For each report, complete Coverage, record any Issues, then complete its Review row.</li></ol><p class="notice">Only the workbook records your ratings. Keep your judgments independent until both reviewers' submissions are locked. No model identity key or other reviewer's ratings are included.</p><p>The approved rubric retains historical draft wording. Its <a href="reading/RUBRIC_APPROVAL_STATUS.html">approval record</a> and the <a href="reading/CURRENT_REVIEW_SCOPE.html">current scope</a> govern its use here. Current requirements are already populated in Coverage.</p></section><section><h2>Fixed reading order</h2><p>Use your browser's Find command to locate a report ID when resuming. Do not reorder by case or compare same-case reports side by side.</p><div class="scroll"><table><tr><th>Position</th><th>Open report and evidence</th><th>Case</th><th>Review row</th></tr>{''.join(table)}</table></div></section>'''
        (dest/'START_HERE.html').write_text(page(f'{rater} - start here',content))
        # Verify every canonical file retained in this copy. Only dictionary-key order differs.
        count=0
        for name,expected in integrity['files_sha256'].items():
            prefix=f'raters/{rater}/'
            if not name.startswith(prefix):continue
            relative=name[len(prefix):]
            if relative=='reports.json':
                assert json.loads((dest/relative).read_text())==json.loads((CANONICAL/name).read_text())
            else:assert sha(dest/relative)==expected,relative
            count+=1
        archive=OUT/f'Formal_review_{rater}.zip'
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for file in sorted(dest.rglob('*')):
                if not file.is_file():continue
                info=zipfile.ZipInfo(str(Path(rater)/file.relative_to(dest)),date_time=(2026,9,19,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,file.read_bytes())
        result[rater]={'reports':105,'review_rows':105,'coverage_rows':552,'canonical_files_verified':count,
                       'zip':archive.name,'zip_sha256':sha(archive),'zip_bytes':archive.stat().st_size,
                       'metadata_change':'reports.json dictionary keys sorted by opaque report ID; values and independent reading order unchanged',
                       'workbook_bytes_unchanged':True,'report_bytes_unchanged':True}
    write_json(OUT/'BUILD_RECORD.json',{'source':'data/rating_packets_formal_v1/raters only','private_key_read':False,'human_ratings_created':False,'model_calls':0,'delivery_sent':False,'raters':result,'script_sha256':sha(Path(__file__))})
    print(json.dumps(result,indent=2))


if __name__=='__main__':build()
