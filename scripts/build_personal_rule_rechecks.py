"""Prepare own-rating-only rechecks and English reviewer messages."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/formal_study/three_rater_review_v1'
DEST = BASE / 'personal_rechecks'
PACK = ROOT / 'data/rating_packets_formal_v1/raters/rater1'

GUIDE = '''# Personal recheck after clarification of discussion rules

This is a targeted recheck of your own ratings, not a fresh independent scoring round or a request to agree with another reviewer. The study lead clarified these rules after the original independent submissions. Model identities remain blinded. No peer ratings, agent-proposed answers, or model identity mapping are included.

## Rules

1. **D01: numerical findings without interpretation.** When correct substantive numerical findings are present but the required interpretation of the principal differences is missing, use Partially covered. Names alone or unrelated content do not earn partial coverage.
2. **D02: ordering needs explanation.** A list sorted by magnitude still needs a brief explanation of the required finding. Equivalent wording anywhere in the report is sufficient; no particular keyword is mandatory. Follow each checklist component: do not demand a second principal joint where the requirement only asks for another joint difference. Required contrasts and similar-magnitude relationships still need to be conveyed.
3. **D03: clinical questions propose possibilities for verification.** A follow-up question about a possible mechanism, compensation, impairment, or clinical correlate is not by itself an assertion that it exists. Do not mark an error solely because a question mentions such a possibility. Separately check wrong numbers, incorrect metric/muscle identities, and explicit assertions that an abnormal finding has already been observed. Preserve any unresolved scope disagreement with a reason.

## What to review

- **Coverage recheck:** your 105 GVS-related requirements, one per report. These include originally agreed items to apply the rules consistently. Review the relevant passages, not every coverage item or the whole report from scratch. Enter Keep, Revise, or Unresolved. If revising, enter the revised label and status; explain changes or unresolved readings with source evidence.
- **Clinical questions:** Section 4 from all 105 reports, with references to your own recorded question-related issues. Mark Keep, Changes recorded, or Unresolved after reviewing the questions under D03. Keep means no changes are needed to your recorded issue decisions for that report; it does not mean every question is automatically acceptable. This focused sweep also allows you to notice a relevant claim you had not previously recorded.
- **Question issue recheck:** your own issue records selected because the quotation contains a question mark or the location names Section 4/a question. This mechanical selection does not mean the issue is wrong. Review Keep, Revise, or Unresolved; leave original columns unchanged. Correct revised quotes must be exact substrings of the saved report, including Markdown. Check the full context in your original blinded materials when necessary.
- **Additional findings:** add a relevant issue missed by the selection, or a new issue discovered during the targeted check. Existing local issue IDs refer only to your own report; do not reuse an existing ID for a different claim. Give exact evidence and a reason. An empty sheet is allowed if nothing additional was found.
- **Quote corrections, if present:** replace the listed non-exact quotations with verbatim report text in the correction column. A quote mismatch is not itself a clinical scoring error. If multiple passages are needed, use one exact quote plus additional locations in the reason. Record any changed judgment explicitly in the relevant recheck sheet or Additional findings.

Use your original blinded reports, model inputs, requirement wording, and approved rubric. This supplement does not reproduce the full original review package. Do not open the cross-rater discussion workbook or agent advice before your personal recheck. If you already saw peer judgments or recommendations, disclose that fact in Completion; you can still complete this recheck, but it is not a new independent assessment. Model-identity blinding and freedom from peer influence are separate matters.

## Return

Save a new file named Personal_recheck_<rater>_completed.xlsx. Fill Completion with your name, date, prior exposure, completion status, and any reservations about the clarified rules. Leave the original submitted workbook unchanged. The expected outcome is your reasoned personal recheck, not a particular score or agreement with others. Do not prefill signatures or mark other reviewers as approving. Original independent ratings remain the baseline; post-clarification revisions and subsequent consensus remain separate records.
'''


def main():
    if DEST.exists():
        raise FileExistsError('Do not overwrite personal recheck materials or returned work.')
    DEST.mkdir()
    (DEST/'RECHECK_INSTRUCTIONS.md').write_text(GUIDE)
    receipt = json.loads((BASE/'SUBMISSION_RECEIPT.json').read_text())
    texts = {p.stem: p.read_text() for p in (PACK/'reports').glob('*.txt')}
    inventory = {}
    for rater, source in receipt['sources'].items():
        snapshot = ROOT/source['snapshot']
        assert sha256(snapshot.read_bytes()).hexdigest() == source['sha256']
        original = load_workbook(snapshot)
        data = {}
        for name in ('Review','Coverage','Issues'):
            values = list(original[name].values)
            data[name] = [dict(zip(values[0], row), source_excel_row=i) for i,row in enumerate(values[1:],2) if any(v is not None for v in row)]
        cov = [x for x in data['Coverage'] if re.search(r'GVS|joint.curve',x['required_wording']+' '+x['components'],re.I)]
        issue = [x for x in data['Issues'] if '?' in (x['exact_quote'] or '') or re.search(r'(?:section|sec\.?)\s*4|question',x['locations'] or '',re.I)]
        mismatch = [x for x in data['Issues'] if x['exact_quote'] and x['exact_quote'] not in texts[x['report_id']]]
        wb = Workbook(); wb.remove(wb.active)

        def sheet(name, headers, rows):
            ws = wb.create_sheet(name);ws.append(headers)
            for row in rows: ws.append(row)
            ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
            for c in ws[1]:
                c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='244760')
            for col in ws.columns:
                title=str(col[0].value).lower()
                ws.column_dimensions[col[0].column_letter].width=65 if any(x in title for x in ('reason','wording','components','text','instructions','quote','response')) else 26
                for c in col[1:]:
                    c.alignment=Alignment(wrap_text=True,vertical='top')
                    if isinstance(c.value,str):
                        assert len(c.value)<32767
                        c.data_type='s'
            return ws

        def choices(ws,col,items):
            dv=DataValidation(type='list',formula1='"'+','.join(items)+'"',allow_blank=True)
            ws.add_data_validation(dv);dv.add(f'{col}2:{col}{max(2,ws.max_row)}')

        sheet('Instructions',['Item','Instructions'],[
            ['Assigned reviewer',rater],['Scope','Your own ratings only. No peer decisions or agent answers are included.'],
            ['Guide',GUIDE],['Original submission',source['path']],['Original SHA-256',source['sha256']],
            ['Materials','Use the full reports, model inputs and rubric from your original blinded scoring package. The Clinical questions sheet reproduces Section 4 only.'],
        ])
        completion=sheet('Completion',['Field','Reviewer response'],[[x,None] for x in (
            'Reviewer name','Date (YYYY-MM-DD)','Seen peer ratings or cross-rater comparisons before this recheck? Yes/No/Unsure',
            'Seen agent-proposed decisions before this recheck? Yes/No/Unsure','Know or accidentally learned any report model identity? Yes/No/Unsure',
            'Exposure details if applicable','All targeted recheck rows completed? Yes/No','Reservations about rules or remaining questions')])
        ws=sheet('Coverage recheck',['Report ID','Case ID','Requirement ID','Required wording','Components','Original decision','Original status','Original reason','Original Excel row','Action','Revised decision','Revised status','Reason and source evidence'],[
            [x[k] for k in ('report_id','case_id','requirement_id','required_wording','components','decision','adjudication_status','evidence_and_reason','source_excel_row')]+[None]*4 for x in cov])
        choices(ws,'J',['Keep','Revise','Unresolved']);choices(ws,'K',['Covered','Partially covered','Not covered']);choices(ws,'L',['Final','Pending'])
        qrows=[]
        for x in data['Review']:
            rid=x['report_id'];text=texts[rid]
            match=re.search(r'(?im)^[#*\s]*4[.)]\s[^\n]*(?:questions|clinical|assessment)[^\n]*',text)
            assert match,rid
            section=text[match.start():].strip()
            records='; '.join(x['issue_id'] for x in issue if x['report_id']==rid) or 'No question-related issue record selected from your submission'
            qrows.append([rid,x['case_id'],section,records,None,None])
        ws=sheet('Clinical questions',['Report ID','Case ID','Section 4 text','Your selected issue IDs','Action','Reason or changed issue IDs'],qrows)
        choices(ws,'E',['Keep','Changes recorded','Unresolved'])
        ws=sheet('Question issue recheck',['Report ID','Your issue ID','Original decision','Original categories','Original quote','Original locations','Original reason','Original pathology flag','Original normality flag','Original Excel row','Action','Revised decision','Revised categories','Revised exact quote','Revised locations','Revised pathology flag','Revised normality flag','Reason'],[
            [x[k] for k in ('report_id','issue_id','decision','categories','exact_quote','locations','reason','pathology_flag','normality_flag','source_excel_row')]+[None]*8 for x in issue])
        choices(ws,'K',['Keep','Revise','Unresolved']);choices(ws,'L',['Error','Acceptable','Pending adjudication','Outside case-error scope'])
        sheet('Additional findings',['Report ID','Existing issue ID or new local ID','Decision','Categories','Exact quote','Locations','Pathology flag','Normality flag','Reason','New issue or correction to existing record'],[])
        if mismatch:
            sheet('Quote corrections',['Report ID','Your issue ID','Original Excel row','Original decision','Original quote','Original locations','Corrected exact quote','Corrected locations','Reason if interpretation changes'],[
                [x[k] for k in ('report_id','issue_id','source_excel_row','decision','exact_quote','locations')]+[None]*3 for x in mismatch])
        folder=DEST/rater;folder.mkdir()
        name=f'Personal_recheck_{rater}.xlsx'
        wb.save(folder/name)
        for s in wb:
            for row in s:
                for c in row:assert not re.search(r'[\u3400-\u9fff]',str(c.value or ''))
        inventory[rater]={'file':str((folder/name).relative_to(ROOT)),'coverage_rows':len(cov),'clinical_question_sections':len(qrows),'own_question_issue_records':len(issue),'quote_corrections':len(mismatch),'source_sha256':source['sha256']}
        assert len(cov)==105 and len(qrows)==105
    messages=[]
    for rater,v in inventory.items():
        extra=' Please also correct the 15 verbatim-quotation mismatches listed in Quote corrections; these are evidence-format checks, not requests to change the clinical judgment.' if rater=='rater2' else ''
        messages.append(f'''## Message to {rater}

Hi {rater},

Thank you for completing the review. We have clarified three discussion rules and would like you to recheck the affected parts of your own ratings before the group discussion:

1. Correct numerical findings without the required interpretation of the principal differences should receive **Partially covered**.
2. A list sorted by magnitude still needs a brief explanation of the required finding. No specific keyword is required; follow the actual checklist components.
3. Clinical follow-up questions should be read as possibilities to be verified, not as established diagnoses or mechanisms. Separately assess incorrect facts and explicit statements that an abnormality has already been observed.

Please use your personal workbook below and the shared instructions, together with your original blinded review materials. This is a targeted recheck of the GVS requirements and Section 4 questions across the reports, not a repeat of the full assessment. Include analogous originally agreed items so the rules are applied consistently. The workbook contains only your own prior ratings, with no peer scores or suggested answers.{extra}

For each listed item, record Keep, Revise/Changes recorded, or Unresolved as appropriate. Give evidence and a reason for changes or unresolved judgments. You do not need to change a judgment simply because it is included. Please note any disagreement with the clarified rules.

Please do not consult other raters' results or the cross-rater discussion workbook before finishing this personal recheck. If you have already seen peer judgments, agent suggestions, or model identities, disclose that in Completion; this does not prevent the recheck. We will preserve your original independent submission and describe this round as a post-clarification personal recheck, not a new independent rating round.

Save your return as **Personal_recheck_{rater}_completed.xlsx**, without overwriting your original submission. Complete the name, date, exposure and completion fields. We will discuss remaining differences after collecting the returns.

Files on the study computer:
- Personal workbook: `{ROOT / v['file']}`
- Shared instructions: `{DEST / 'RECHECK_INSTRUCTIONS.md'}`

Thank you.
''')
    (DEST/'MESSAGES_TO_RATERS.md').write_text('# Messages for the three personal rechecks\n\nAttach only the recipient\'s workbook and the shared instructions. Local paths identify files on the study computer; send the actual attachments to remote reviewers. Original blinded materials remain necessary. Do not send the cross-rater comparison or agent-advice files.\n\n'+'\n'.join(messages))
    (DEST/'BUILD_RECORD.json').write_text(json.dumps({'status':'Blank personal recheck supplements; no new expert decisions','contents':inventory,'model_identity_key_read':False},indent=2)+'\n')
    print(json.dumps(inventory,indent=2))


if __name__=='__main__':main()
