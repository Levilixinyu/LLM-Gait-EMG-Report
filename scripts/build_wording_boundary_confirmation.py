"""Build eight-item personal review packets without identities or peer ratings."""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/formal_study/wording_boundary_confirmation_v1"
SOURCE = ROOT / "docs/formal_study/independent_expert_review_template_v1/Independent_expert_review_template.zip"
FREEZE = ROOT / "docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json"
INTEGRITY = ROOT / "data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/package_integrity_snapshot.json"
AUDIT = ROOT / "docs/formal_study/confirmed_error_source_audit_v1/BUILD_RECORD.json"

# Balanced questions, not proposed decisions. No prior rater positions are copied.
ITEMS = [
    ("AG004", "Meaning of reduced ROM in a clinical question", [31, 43],
     "Does 'reduced sagittal joint ROMs observed here' assert a reduction against an unavailable reference, or describe the supplied excursion while asking what it means?",
     "An observed reduction is presupposed; the input supplies no matched ROM comparator. Asking about causes does not necessarily remove that premise.",
     "The report says ROM alone does not confirm clinical restriction and asks about possible explanations. Reduced could be descriptive shorthand rather than a confirmed abnormality.",
     "System: ROM alone does not establish clinical restriction. Rubric 8-9 and D03: distinguish a question about a possibility from an assertion that an abnormal finding was observed."),
    ("AG011", "Step-length index versus percentage shortening", [2, 40],
     "Does 'paretic step 6.6% shorter' change the index's denominator, or refer back to the explicitly named symmetry index?",
     "Ordinary percentage shortening relative to the non-paretic step uses a different denominator. The supplied -6.6% index corresponds to approximately 6.389% by that convention.",
     "Section 1 names the index, value and direction correctly; the question calls it the noted asymmetry. It may be shorthand for that index without asserting another denominator.",
     "User input: index = 200*(paretic - non-paretic)/(paretic + non-paretic). Rubric E01 concerns wrong metric identity/arithmetic. D03 permits follow-up questions but not independently false facts."),
    ("AG019", "Retained-list wording versus a no-gap assertion", [48, 49],
     "In the complete paragraph, is 'no retained below-threshold segment' an imprecise list description or an assertion that no below-threshold segment exists?",
     "The detector retains above-threshold runs, not below-threshold segments. 'Envelope that stays above' may turn the statement into a stronger signal-level assertion.",
     "Retained and under-this-rule language may describe the displayed list. The next paragraph warns that the list is not exhaustive. Terminology alone may not settle the intended scope.",
     "System and rubric 8: reported intervals and boundary continuity are allowed; rounded coverage alone cannot establish absence. Review this target separately from the neighboring 3% filter explanation, which is outside this return's scope."),
    ("AG023", "Constrained pelvic excursion versus an open clinical question", [25, 38, 42],
     "Does constrained assert an unsupported clinical restriction, or describe the supplied small excursion while asking whether it is typical?",
     "The adjective constrained can presuppose a limitation for which no matched ROM comparison is supplied; offering possible explanations need not remove that premise.",
     "The question explicitly offers the participant's typical mechanics as an alternative. It may be asking about significance without asserting disease or a pathological examination finding.",
     "System: ROM alone does not establish restriction. D03 allows possible clinical correlates. Also complete the separate pathology annotation; a simultaneous E02 category is not required."),
    ("AG028", "Functional classification versus naming a speed band", [4],
     "Does categorized functionally claim assessed walking function, or merely name the supplied speed band imprecisely?",
     "Functionally goes beyond the supplied instruction that the ambulator label is a speed band, not measured independence, safety or real-world mobility.",
     "The phrase still ends in band, and no separate claim of independence or safety is made. It could be imprecise naming rather than an additional functional conclusion.",
     "Case input: the ambulation label denotes a speed band only. Rubric E02 addresses unsupported functional inference. Judge the actual assertion, not the word alone."),
    ("AG048", "Continuous coverage in a follow-up question", [8, 9, 33],
     "Does continuous 100% coverage observed assert full-precision uninterrupted exceedance, or summarize the displayed mean-envelope result?",
     "The continuous-coverage heading and observed wording can assert uninterrupted signal coverage, which the rounded display does not guarantee.",
     "The report discusses supplied mean-envelope coverage and distinguishes it from contraction. It does not explicitly say no below-threshold sample exists; the clinical correlates remain questions.",
     "System and rubric 8 allow displayed coverage and boundary continuity. D03 protects questions about possible correlates, while separately assessable signal assertions still require evidence."),
    ("AG050", "Meaning of continuous coverage for BF at 95%", [15, 18, 47],
     "For the BF component only, does high continuous envelope coverage assert one uninterrupted run, or refer loosely to high coverage of a continuous envelope?",
     "BF has two retained intervals and 95% coverage. Reading continuous as a single uninterrupted BF interval conflicts with that structure.",
     "Section 2 correctly lists both BF intervals and 95%. The phrase may refer to the continuous-envelope representation rather than a single retained run, and does not claim BF coverage is 100%.",
     "User input provides BF intervals 60%-66% and 68%-56% wrapping. Rubric E01/E03 and D03 require identifying the actual factual assertion. The ERS component is a different existing group and is outside this item."),
    ("AG051", "Whole-cycle wording versus supplied boundary continuity", [9, 11, 38],
     "Does the heading plus maintained-for-100% wording assert a whole-cycle guarantee beyond the displayed result, given that continuously explicitly modifies the boundary clause?",
     "The continuous-activity heading and maintained-for-100% predicate can imply uninterrupted exceedance over the whole cycle.",
     "The 100% values are supplied, and continuous crossing of the cycle boundary is also supplied. The explicit continuously clause may refer only to that allowed boundary property.",
     "System and rubric 8: reporting coverage and supplied boundary continuity is allowed. A whole-cycle no-gap guarantee is stronger. Do not equate boundary continuity with physiological continuous contraction."),
]

CSS = """body{font:17px/1.6 system-ui,sans-serif;color:#20313a;background:#f5f7f8;margin:0}main{max-width:1050px;margin:auto;padding:28px}section,header{background:white;border:1px solid #d5dfe4;border-radius:10px;padding:22px;margin:18px 0}h1{font-size:28px}h2{font-size:23px}h3{font-size:19px}a{color:#065985}table{width:100%;border-collapse:collapse}th,td{border:1px solid #d5dfe4;padding:10px;text-align:left;vertical-align:top}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 system-ui,sans-serif}.note{border-left:4px solid #367180;padding:12px;background:#edf5f7}.reading{display:grid;grid-template-columns:1fr 1fr;gap:20px}.reading>div{padding:14px;border:1px solid #d5dfe4}summary{cursor:pointer;font-weight:600}@media(max-width:720px){.reading{grid-template-columns:1fr}}@media print{body{background:white}main{max-width:none;padding:0}section{break-inside:avoid}}"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def page(title: str, body: str) -> bytes:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>{body}</main></body></html>').encode()


def numbered(text: str, wanted: list[int] | None = None) -> str:
    lines = text.splitlines()
    indexes = range(len(lines)) if wanted is None else sorted({j for n in wanted for j in range(max(0,n-2),min(len(lines),n+1))})
    return html.escape("\n".join(f"{i+1}: {lines[i]}" for i in indexes))


def workbook(rater: str, groups: dict) -> bytes:
    w = Workbook()
    instructions = w.active
    instructions.title = "Instructions"
    for row in [
        ("Assigned return", rater + " (routing label only; not a signature)"),
        ("Open first", "Extract the entire ZIP. Open START_HERE.html and EVIDENCE.html; complete this workbook."),
        ("Scope", "Eight passages only. Read each in the complete report and actual model inputs. No whole-report rescore is requested."),
        ("Judgment", "Enter Error, Acceptable or Pending adjudication and your own evidence/reason for each item. Neither reading is a proposed answer. Agreement is not required."),
        ("Error category", "If Error, enter applicable E codes in your own judgment. Multiple tags do not create extra groups. For other decisions leave this field blank."),
        ("Pathology", "Complete the one AG023 row on Control annotation. This is separate from the item decision; E02 need not be selected simultaneously."),
        ("Missing material", "If a required file is corrupt/mismatched, do not invent a decision or call this clinical Pending. Leave the affected decision blank and describe the material problem in Completion."),
        ("Exposure", "Study lead/analysis team already unblinded before this request. This packet omits identities, model results and peer positions. Declare your actual exposure; this is targeted follow-up, not a fresh independent baseline."),
        ("Return", f"Save as Wording_boundary_confirmation_{rater}_completed.xlsx. Complete name/date/exposure/status. Do not edit historical submissions."),
    ]:
        instructions.append(row)
    s = w.create_sheet("Decisions")
    s.append(["Item ID", "Report ID", "Case ID", "Focus", "Evidence", "Your decision", "Your reason: exact wording, input and rule", "Error categories if Error", "Rule reservation or other reading (optional)"])
    for row, item in enumerate(ITEMS, 2):
        gid, title, *_ = item
        g = groups[gid]
        s.append([gid,g["report_id"],g["case_id"],title,"Open evidence",None,None,None,None])
        s.cell(row,5).hyperlink = f"EVIDENCE.html#{gid}"
        s.cell(row,5).style = "Hyperlink"
    dv = DataValidation(type="list",formula1='"Error,Acceptable,Pending adjudication"',allow_blank=True)
    dv.errorTitle = "Use a listed decision"
    dv.error = "Choose Error, Acceptable or Pending adjudication; explain your own reasoning."
    dv.showErrorMessage = True
    dv.errorStyle = "stop"
    s.add_data_validation(dv)
    dv.add("F2:F9")
    s.auto_filter.ref = "A1:I9"
    s.freeze_panes = "F2"
    c = w.create_sheet("Control annotation")
    c.append(["Item ID", "Report ID", "Question", "Your flag", "Your reason"])
    c.append(["AG023",groups["AG023"]["report_id"],"Does this specific passage make an unsupported pathological/clinical-impairment assertion about the control participant?",None,None])
    cv = DataValidation(type="list",formula1='"Yes,No,Uncertain"',allow_blank=True)
    cv.showErrorMessage = True
    cv.errorStyle = "stop"
    c.add_data_validation(cv)
    cv.add("D2")
    c.append(["Meaning",None,"Yes requires the assertion itself, not just a possible correlate or a numerical deviation. A positive confirmed endpoint also requires a confirmed in-scope Error; Pending plus Yes is not automatically confirmed."])
    c.append(["Category independence",None,"A simultaneous E02 tag is not required. No flag is inferred automatically from E07, a question, or healthy-group membership."])
    t = w.create_sheet("Completion")
    t.append(["Field", "Your response"])
    completion = ["Reviewer name", "Confirmation date (YYYY-MM-DD; optionally time zone)",
                  "All eight items and the control annotation completed? (Yes/No)",
                  "Model identity knowledge for these reports (None/Some/All/Unsure)",
                  "Exposure to model comparison results before/during this return (None/Some/Unsure)",
                  "Peer or outside advice seen during this targeted round (describe, or None)",
                  "Do these responses reflect your own judgments without a required consensus? (Yes/No)",
                  "Material problems or unfinished items (describe, or None)",
                  "Overall reservations about the existing rules (describe, or None)"]
    for f in completion:
        t.append([f,None])
    for sh in w:
        for cell in sh[1]:
            cell.font = Font(bold=True,color="FFFFFF")
            cell.fill = PatternFill("solid",fgColor="21475B")
        for row in sh:
            for cell in row:
                cell.alignment = Alignment(vertical="top",wrap_text=True)
                if isinstance(cell.value,str):
                    cell.data_type = "s"
        sh.freeze_panes = sh.freeze_panes or "A2"
        sh.sheet_view.showGridLines = False
        for col in "ABCDEFGHI":
            sh.column_dimensions[col].width = 23
        for n in range(2,sh.max_row+1):
            sh.row_dimensions[n].height = 90
    instructions.column_dimensions["B"].width = 105
    s.column_dimensions["D"].width = 44
    s.column_dimensions["G"].width = 78
    s.column_dimensions["I"].width = 65
    c.column_dimensions["C"].width = 76
    c.column_dimensions["E"].width = 75
    t.column_dimensions["A"].width = 78
    t.column_dimensions["B"].width = 90
    blue = PatternFill("solid",fgColor="E5F1FB")
    for sh,area in ((s,"F2:I9"),(c,"D2:E2"),(t,"B2:B10")):
        for row in sh[area]:
            for cell in row:
                cell.fill = blue
                assert cell.value is None
    w.properties.creator = "Study review preparation"
    w.properties.title = "Eight-item wording-boundary confirmation"
    b = io.BytesIO()
    w.save(b)
    return b.getvalue()


def main() -> None:
    if OUT.exists():
        raise SystemExit("Output exists; do not overwrite a distributed packet or reviewer return.")
    fb = FREEZE.read_bytes()
    frozen = json.loads(fb)
    integrity_bytes = INTEGRITY.read_bytes()
    hashes = json.loads(integrity_bytes)["files_sha256"]
    audit = json.loads(AUDIT.read_bytes())
    assert sha(fb) == audit["frozen_dataset_sha256"]
    assert {i[0] for i in ITEMS} == set(audit["wording_sensitive_groups"])
    groups = {g["group_id"]:g for g in frozen["issue_groups"] if g["group_id"] in {i[0] for i in ITEMS}}
    source_bytes = SOURCE.read_bytes()
    z = ZipFile(io.BytesIO(source_bytes))
    shared: dict[str,bytes] = {}
    receipts = []
    reports, inputs = {}, {}

    def capture(rel: str, destination: str) -> bytes:
        b = z.read("independent_expert_review/"+rel)
        assert sha(b) == hashes["raters/rater2/"+rel],rel
        shared[destination] = b
        receipts.append({"source_member":rel,"packet_path":destination,"sha256":sha(b)})
        return b

    for gid, *_ in ITEMS:
        g = groups[gid]
        rid,cid = g["report_id"],g["case_id"]
        reports[rid] = capture(f"reports/{rid}.txt",f"reports/{rid}.txt").decode()
        assert g["exact_anchor"] in reports[rid]
        if cid not in inputs:
            user = capture(f"materials/{cid}/model_user_prompt.txt",f"inputs/{cid}/model_user_prompt.txt").decode()
            system = capture(f"materials/{cid}/model_system_prompt.txt",f"inputs/{cid}/model_system_prompt.txt").decode()
            inputs[cid] = (user,system)
            shared[f"inputs/{cid}/READ_INPUT.html"] = page(cid + " actual model input",f'<p><a href="../../START_HERE.html">Start</a> | <a href="../../EVIDENCE.html">Eight items</a></p><h1>{html.escape(cid)}</h1><p>Exact source bytes are retained in the linked TXT files. Line numbers below are reading aids only.</p><h2>System input</h2><p><a href="model_system_prompt.txt">Original TXT</a></p><pre>{numbered(system)}</pre><h2>User input</h2><p><a href="model_user_prompt.txt">Original TXT</a></p><pre>{numbered(user)}</pre>')
        shared[f"reports/{rid}.html"] = page(rid + " original report",f'<p><a href="../EVIDENCE.html#{gid}">Target item</a> | <a href="{rid}.txt">Original TXT</a></p><h1>{rid}</h1><p>{cid}. Verbatim report with added line numbers for navigation.</p><pre>{numbered(reports[rid])}</pre>')
    for name in ("RUBRIC.md","RUBRIC_APPROVAL_STATUS.md","CURRENT_REVIEW_SCOPE.md","EXAMPLES.md","rubric.json"):
        capture("materials/"+name,"rules/"+name)
    rb = json.loads(shared["rules/rubric.json"])
    rules_log_path = ROOT / "docs/formal_study/three_rater_review_v1/DISCUSSION_RULES_LOG.json"
    rules_log_bytes = rules_log_path.read_bytes()
    d03 = next(r["interpretation"] for r in json.loads(rules_log_bytes)["rules"] if r["id"]=="D03")
    semantic_path = ROOT / "docs/formal_study/three_rater_analysis_v1/SEMANTIC_FLAG_CONFIRMATION.json"
    semantic_bytes = semantic_path.read_bytes()
    semantic = json.loads(semantic_bytes)
    # Extract the rule only: do not distribute the source record's peer judgments.
    rule_note = "# Applicable discussion and annotation rules\n\nD03 (study-lead clarification after initial independent scoring):\n\n"+d03+"\n\nPathology annotation (study-lead confirmation, 2026-09-23):\n\n"+semantic["scope"]+"\n\n"+"\n".join("- "+r for r in semantic["rules"])+"\n"
    shared["rules/APPLICABLE_CLARIFICATIONS.md"] = rule_note.encode()
    categories = "".join(f'<tr><td>{html.escape(r["id"])}</td><td>{html.escape(r["name"])}</td><td>{html.escape(r["scope"])}</td><td>{html.escape(r["boundary"])}</td></tr>' for r in rb["error_categories"])
    rules_body = f'''<p><a href="START_HERE.html">Start</a> | <a href="EVIDENCE.html">Eight items</a></p><h1>Applicable rules</h1><section><h2>Use the existing standard</h2><p>No new scoring threshold or preferred outcome is introduced. The unchanged rubric retains historical draft wording; its dated approval record confirms subsequent approval. Historical links to old approval workbooks or the developmental five-case annex are provenance references, not extra tasks for this return.</p><p><a href="rules/RUBRIC.md">Complete original rubric</a> | <a href="rules/RUBRIC_APPROVAL_STATUS.md">Approval status</a> | <a href="rules/EXAMPLES.md">Original examples</a> | <a href="rules/CURRENT_REVIEW_SCOPE.md">Original scope note</a></p><h3>D03: questions and assertions</h3><p>{html.escape(d03)}</p><h3>Control annotation</h3><p>{html.escape(semantic["scope"])}</p><ul>{''.join('<li>'+html.escape(r)+'</li>' for r in semantic['rules'])}</ul></section><section><h2>Decision options</h2><ul><li>Error: identify the actual unsupported or false assertion and its applicable rule.</li><li>Acceptable: explain why the passage, read in context, does not make that prohibited assertion.</li><li>Pending adjudication: preserve competing readings when the existing rule and context do not resolve them. This is not a confirmed error.</li></ul><p>Missing or mismatched files are a material problem, not interpretive Pending. Record them in Completion rather than guessing a decision.</p></section><section><h2>Threshold evidence: a scope check, not an answer key</h2><p>Reported 100% coverage, a displayed 0%-100% retained interval and supplied boundary continuity may be described. The stronger claim that no sample fell below threshold is different. Even these three displayed fields together need not guarantee that stronger claim: on a synthetic 1001-sample curve, two dips at indices 1 and 999 leave a long run 0.2%-99.8% (displayed 0%-100%), coverage 99.8002% (displayed 100%) and both boundary samples above threshold. The short two-sample boundary run is discarded by the ABOVE-threshold duration rule.</p><p>This is an assistant-checked logical example, not participant data, a new expert-approved rule or evidence that any reviewed participant had dips. Still decide whether the actual report asserts a stronger guarantee or merely describes the supplied output. Boundary continuity does not by itself assert physiological contraction.</p></section><section><h2>Existing error definitions</h2><table><tr><th>ID</th><th>Name</th><th>Scope</th><th>Boundary</th></tr>{categories}</table></section>'''
    shared["RULES.html"] = page("Applicable rules",rules_body)
    cards = []
    for idx,item in enumerate(ITEMS):
        gid,title,locations,question,strong,permissive,rule = item
        g = groups[gid]
        rid,cid = g["report_id"],g["case_id"]
        readings = [strong,permissive] if idx%2==0 else [permissive,strong]
        cards.append(f'''<section id="{gid}"><h2>{gid}: {html.escape(title)}</h2><p>{rid} | {cid}</p><p><a href="reports/{rid}.html">Complete original report</a> | <a href="inputs/{cid}/READ_INPUT.html">Actual system and user inputs</a> | <a href="RULES.html">Rules</a></p><h3>Question to decide</h3><p>{html.escape(question)}</p><h3>Registered target quotation</h3><blockquote>{html.escape(g['exact_anchor'])}</blockquote><h3>Original context and relevant cross-references</h3><pre>{numbered(reports[rid],locations)}</pre><div class="reading"><div><h3>Possible reading A</h3><p>{html.escape(readings[0])}</p></div><div><h3>Possible reading B</h3><p>{html.escape(readings[1])}</p></div></div><p>These are assistant-prepared readings, not expert positions or an exhaustive choice. You may reject either or both, state another reading, or remain uncertain. A/B order varies across items and is the same for all reviewers.</p><h3>Applicable boundary</h3><p>{html.escape(rule)}</p><p>Record your decision and reason in the workbook. Review only the identified claim; neighboring claims are context, not additional requested decisions.</p></section>''')
    shared["EVIDENCE.html"] = page("Eight wording-boundary items",'<p><a href="START_HERE.html">Start</a> | <a href="RULES.html">Rules</a></p><h1>Eight targeted passages</h1><p>No model identities, model comparisons or peer ratings are included. The evidence and questions are identical across the three packets.</p>'+''.join(cards))
    OUT.mkdir(parents=True)
    outputs = {}
    all_hashes = {}
    for rater in ("rater1","rater2","rater3"):
        filename = f"Wording_boundary_confirmation_{rater}.xlsx"
        packet = dict(shared)
        packet[filename] = workbook(rater,groups)
        links = ''.join(f'<tr><td><a href="EVIDENCE.html#{i[0]}">{i[0]}</a></td><td>{html.escape(i[1])}</td></tr>' for i in ITEMS)
        packet["START_HERE.html"] = page("Targeted wording-boundary confirmation",f'''<header><h1>Eight-item personal confirmation</h1><p>Assigned return: {rater}. This identifies the recipient only; it is not a signature.</p><p class="note">The study lead/analysis team had already unblinded before this request. This packet contains no identity mapping, model comparison results or peer positions. Your own actual exposure must be declared. This is targeted follow-up after earlier review and discussion, not a new independent baseline or a guaranteed blinded assessment.</p></header><section><h2>What to do</h2><ol><li>Extract the entire ZIP into one folder; keep its subfolders together.</li><li>Read <a href="RULES.html">the applicable rules</a> and each of the <a href="EVIDENCE.html">eight passages</a>. The complete original reports and actual inputs are linked for context.</li><li>Open <a href="{filename}">{filename}</a>. On Decisions, fill the blue decision and reason fields for all eight items. If Error, add your applicable category codes.</li><li>On Control annotation, answer the one AG023 pathology question and give a reason. It does not require simultaneous E02 selection.</li><li>Fill Completion, including name, date and actual exposure. Save a new copy named <strong>Wording_boundary_confirmation_{rater}_completed.xlsx</strong> and return that workbook to the study lead.</li></ol></section><section><h2>Scope and freedom of judgment</h2><p>You may retain or revise your view, or leave a genuine interpretation Pending. No requested direction, numerical target, majority vote or agreement with another reviewer applies. Assess each item on its own wording, evidence and existing rule. Do not treat a general disclaimer as automatically curing a false assertion, or a question mark/particular adjective as automatically proving an error.</p><p>Only these eight passages and the one control annotation are requested. Do not rescore overall report coverage, grade clinical severity, revisit unrelated closed Pending items or edit original submissions. If you notice a material concern outside scope, note it in Completion without silently changing unrelated scores.</p><p>This subset was selected by an assistant source audit after analysis-team unblinding for wording-dependent boundaries. The proposed readings are not new expert judgments. Existing frozen outcomes remain unchanged until any later disposition is explicitly documented.</p></section><section><h2>Item index</h2><table><tr><th>Item</th><th>Focus</th></tr>{links}</table></section>''')
        packet["README.md"] = (f"# Eight-item personal confirmation: {rater}\n\nExtract the entire ZIP and open START_HERE.html. Complete {filename}, then save as Wording_boundary_confirmation_{rater}_completed.xlsx. Read the exposure/scope statement before beginning. Decisions, reasons, annotation, name and date are blank. No agreement or particular outcome is requested.\n").encode()
        # Scan distributable text, including workbook cells, for accidental identity/peer leakage.
        banned = re.compile(r"claude|gemini|gpt[- ]?6|anthropic|openai|answer_key|model_key|mapping_snapshot|rater[123] decision|rater[123] frozen reason",re.I)
        for name,b in packet.items():
            assert not name.startswith(("/","private/")) and ".." not in Path(name).parts
            if name.endswith(".xlsx"):
                book = load_workbook(io.BytesIO(b))
                strings = []
                for sh in book:
                    for row in sh:
                        for cell in row:
                            assert cell.data_type not in ("f","e")
                            if isinstance(cell.value,str): strings.append(cell.value)
                for row in book["Decisions"].iter_rows(min_row=2,max_row=9,min_col=6,max_col=9):
                    assert all(c.value is None for c in row)
                assert book["Control annotation"]["D2"].value is None
                assert book["Control annotation"]["E2"].value is None
                assert all(book["Completion"].cell(n,2).value is None for n in range(2,11))
                value = "\n".join(strings)
            else:
                value = b.decode()
            assert not banned.search(value),(name,banned.search(value))
            assert not re.search(r"[\u4e00-\u9fff]",value),name
        name = f"Wording_boundary_confirmation_{rater}.zip"
        target = OUT/name
        with ZipFile(target,"w",ZIP_DEFLATED) as dest:
            for path,b in sorted(packet.items()):
                dest.writestr(path,b)
        with ZipFile(target) as read:
            assert read.testzip() is None
            for path,b in packet.items():
                assert read.read(path)==b
        outputs[name] = sha(target.read_bytes())
        all_hashes[rater] = {p:sha(b) for p,b in packet.items()}
    for name in shared:
        assert len({all_hashes[r][name] for r in all_hashes})==1
    assert FREEZE.read_bytes()==fb
    root_readme = """# Eight-item wording-boundary confirmation packets

Send each human reviewer only their own ZIP below. Each package contains the same eight target passages, eight complete original reports, seven case input pairs, existing scoring rules, balanced non-prescriptive readings, and one blank personal return workbook. No model identities, comparative results, peer judgments or report-level outcome dependencies are distributed.

- [Rater1 packet](Wording_boundary_confirmation_rater1.zip)
- [Rater2 packet](Wording_boundary_confirmation_rater2.zip)
- [Rater3 packet](Wording_boundary_confirmation_rater3.zip)

Recipients extract the entire ZIP, open START_HERE.html, complete Decisions, Control annotation and Completion, and return their separately saved `_completed.xlsx` file. The single control annotation concerns AG023; the flag is not mechanically inferred from category E02. All decision, reason, annotation, name, date and exposure cells are blank.

This targeted follow-up was requested after study-lead/analysis-team unblinding. The packets omit identities but do not claim fresh independent scoring or certify each reviewer's blinding. Actual reviewer exposure must be declared. No unanimous decision is required and no old judgment has been changed.

After receipt, check completeness and source references before interpreting responses. Preserve all personal positions. Any correction or sensitivity analysis must be separately documented as post-unblinding; do not silently replace the frozen primary analysis, automatically majority-vote, or convert Pending into a confirmed error or an error-free report. A return is an individual assessment, not approval of a new study-wide rule or a full-dataset signature.

The unchanged rubric's historical approval links and developmental annex references describe prior documentation, not additional requested reviews. The current eight-item source evidence and applicable rules are inside each packet.

The duplicate evidence across the ZIPs is intentional: each reviewer receives a self-contained package. No additional extracted package copies are stored here. Use [the message template](MESSAGE_TO_REVIEWERS.md) when sending; no message has been sent by the preparation script.
"""
    (OUT/"README.md").write_text(root_readme)
    message = """# Message to each reviewer

Please send this message separately, attaching only the recipient's own ZIP. Replace the greeting with the appropriate reviewer name.

Dear Reviewer,

Please complete a targeted follow-up on the eight passages in the attached packet. This is not a new full review, and you are not being asked to agree with another reviewer or to change your decisions in any particular direction.

For each item, read the original wording in context, check the actual model inputs and existing rules, and record your own decision: Error, Acceptable, or Pending adjudication. Give a brief reason tied to the exact wording and evidence. The two readings provided are assistant-prepared discussion aids, not an answer key; you may reject either or both or offer another interpretation.

Please also complete the single AG023 control annotation. An unsupported pathological/impairment inference does not require E02 to be selected simultaneously. A question mentioning a clinical possibility does not automatically justify a positive flag.

For transparency, the study lead/analysis team had already unblinded before this request. The packet does not include model identities, comparative results or peer ratings. Please declare your actual exposure in Completion. This return will be retained as targeted follow-up after the earlier review and discussion, not presented as a new independent baseline.

Steps:

1. Extract the entire ZIP and open START_HERE.html.
2. Review the eight items, using the linked complete reports, inputs and rules.
3. Fill Decisions, Control annotation and Completion in your workbook.
4. Save a new copy with `_completed` before `.xlsx` and return it to me. Leave historical submissions unchanged.

Keep any genuine interpretation unresolved if needed; agreement is not required. If materials are missing or a concern falls outside these eight items, record it in Completion rather than silently changing other scores.

Thank you.
"""
    (OUT/"MESSAGE_TO_REVIEWERS.md").write_text(message)
    for name in ("README.md","MESSAGE_TO_REVIEWERS.md"):
        outputs[name]=sha((OUT/name).read_bytes())
    record = {
        "created_at_utc":datetime.now(timezone.utc).isoformat(),
        "purpose":"User-authorized blank targeted confirmation packets; no submissions changed",
        "stage":"Post-unblinding for study lead/analysis team; reviewer exposure to be self-reported",
        "items":[i[0] for i in ITEMS],"reports":len(reports),"case_inputs":len(inputs),
        "assigned_reviewers":["rater1","rater2","rater3"],"new_human_decisions":0,
        "frozen_dataset_sha256":sha(fb),"source_package_sha256":sha(source_bytes),
        "integrity_snapshot_sha256":sha(integrity_bytes),"audit_record_sha256":sha(AUDIT.read_bytes()),
        "D03_source_sha256":sha(rules_log_bytes),"semantic_rule_source_sha256":sha(semantic_bytes),
        "script_sha256":sha(Path(__file__).read_bytes()),
        "source_receipts":receipts,"outputs_sha256":outputs,"packet_members_sha256":all_hashes,
        "checks":{"reports_and_inputs_byte_verified":True,"identical_shared_evidence":True,"blank_response_cells":True,"no_formula_or_error_cells":True,"english_only":True,"identity_and_peer_label_scan_passed":True,"zip_integrity":True,"frozen_dataset_unchanged":True},
    }
    (OUT/"BUILD_RECORD.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"output":str(OUT),"packets":3,"items_per_packet":8,"reports":len(reports),"cases":len(inputs)}))


if __name__=="__main__":
    main()
