"""Validate returned expert reviews and prepare a narrowly scoped v2 revision."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/formal_study/execution_analysis_v1_draft"
OUT = ROOT / "docs/formal_study/execution_analysis_v2_draft"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(sheet):
    rows = list(sheet.values)
    return [dict(zip(rows[0], row)) for row in rows[1:]]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def build():
    if OUT.exists():
        raise FileExistsError("Preserve the existing revision; do not overwrite it.")
    old_manifest = json.loads((BASE / "manifest.json").read_text())
    source_hashes = {}
    for name, expected in old_manifest["output_sha256"].items():
        p = BASE / name
        assert sha(p) == expected, name
        source_hashes[str(p.relative_to(ROOT))] = expected
    template = load_workbook(BASE / "Study_plan_review.xlsx")
    template_records = {s.title: records(s) for s in template}
    returns = {}
    for who in ["rater1", "rater2"]:
        p = BASE / f"Study_plan_review_{who}.xlsx"
        source_hashes[str(p.relative_to(ROOT))] = sha(p)
        wb = load_workbook(p)
        assert wb.sheetnames == template.sheetnames
        sheets = {s.title: records(s) for s in wb}
        for name in ["Read first", "Exposure review"]:
            assert sheets[name] == template_records[name], (who, name)
        assert len(sheets["Plan decisions"]) == 11
        for original, row in zip(template_records["Plan decisions"], sheets["Plan decisions"]):
            for key in list(original)[:5]:
                assert original[key] == row[key], (who, row["decision_id"], key)
            assert row["reviewer"] == who and row["date"] == "2026-09-18"
            assert row["reviewer_decision"] in {"Accept", "Revise", "Outside my review scope"}
        for original, row in zip(template_records["Capacity"], sheets["Capacity"]):
            for key in ["reviewer", "report_assignments", "coverage_judgments"]:
                assert original[key] == row[key]
            if row["reviewer"] != who:
                assert row == original
        for original, row in zip(template_records["Overall review"], sheets["Overall review"]):
            assert row["reviewer_role"] == original["reviewer_role"]
            if row["reviewer_role"] != who:
                assert row == original
            else:
                assert row["reviewer"] == who and row["overall_decision"] and row["date"]
        for sheet in wb:
            for row in sheet:
                for cell in row:
                    assert cell.data_type != "f"
                    if isinstance(cell.value, str):
                        assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", cell.value)
        returns[who] = sheets
    assert sha(BASE / "Study_plan_review_rater2.xlsx") == "ec8698a75a0f0e112d132e9c96a496b7734f8f24b123d459822561d75b34c2be"
    r1 = {r["decision_id"]: r for r in returns["rater1"]["Plan decisions"]}
    r2 = {r["decision_id"]: r for r in returns["rater2"]["Plan decisions"]}
    assert all(r1[k]["reviewer_decision"] == r2[k]["reviewer_decision"] == "Accept" for k in ["D02", "D07"])
    assert r1["D04"]["reviewer_decision"] == r1["D10"]["reviewer_decision"] == "Revise"
    assert r2["D04"]["reviewer_decision"] == r2["D10"]["reviewer_decision"] == "Accept"
    lead_ids = ["D01", "D03", "D05", "D06", "D08", "D09", "D11"]
    assert all(r[k]["reviewer_decision"] == "Outside my review scope" for r in [r1, r2] for k in lead_ids)
    r1_overall = next(r for r in returns["rater1"]["Overall review"] if r["reviewer"] == "rater1")
    assert sha(BASE / "Study_plan_review.xlsx") in r1_overall["scope_approved_or_exceptions"]
    flag_rule = r1["D04"]["comments_or_revision"].split('Complete replacement: "', 1)[1].split('"', 1)[0]
    assert flag_rule.startswith("Determine each semantic flag separately.")
    clarification = (
        "A control EMG route-C statement that all seven displayed max |z| values are below the supplied 3.65 endpoint is a displayed-value comparison and does not itself trigger the normality flag. "
        "A question presupposing an unsupported clinical deficit is assessed as an assertion under the existing rubric; the pathology flag for that presupposition requires a confirmed E02 issue, not question syntax alone. "
        "Other flag-qualifying assertions remain assessed under their applicable existing error categories. No new mandatory report content, error category or penalty is introduced."
    )
    old_protocol = (BASE / "PROTOCOL.md").read_text()
    new_protocol = old_protocol.replace("# Execution and analysis plan v1", "# Execution and analysis plan v2", 1)
    old_status = old_protocol.splitlines()[2]
    new_status = "Status: **Targeted revision awaiting confirmation; no formal API generation authorized or performed.** Both experts accepted D02 and D07 in v1. Section 6 below incorporates rater1's exact D04 correction and rater2's relevant examples for both experts to confirm. Rater1 capacity remains pending; rater2's schedule is conditional. Study-lead decisions remain pending. No finalized case requirement has changed."
    assert old_status in new_protocol
    new_protocol = new_protocol.replace(old_status, new_status, 1)
    new_protocol = new_protocol.replace("see `exposure_confirmation.json`", "see `../execution_analysis_v1_draft/exposure_confirmation.json`", 1)
    old_flags = "The flags add descriptive labels to existing confirmed issue groups, not new errors or extra penalties. One report may trigger both. Cases with pending potentially qualifying issues remain indeterminate for that flag. Both experts must confirm these operational flag definitions before they are used; until then they remain proposed. Do not label their proportions diagnostic false-positive rates, sensitivity or specificity."
    new_flags = "The flags add descriptive labels to existing confirmed issue groups, not new errors or extra penalties. One report may trigger both.\n\n" + flag_rule + "\n\n" + clarification + "\n\nBoth experts must confirm this revised operational wording before use. Rater2's v1 approval is not approval of the changed wording. Do not label their proportions diagnostic false-positive rates, sensitivity or specificity."
    assert old_flags in new_protocol
    new_protocol = new_protocol.replace(old_flags, new_flags, 1)
    OUT.mkdir()
    (OUT / "PROTOCOL.md").write_text(new_protocol)
    write_json(OUT / "source_review_records.json", returns)
    old_plan = json.loads((BASE / "plan.json").read_text())
    plan = copy.deepcopy(old_plan)
    plan.update(version="execution-analysis-v2-draft", status="D04 revised; expert reconfirmation, rater1 capacity and study-lead decisions pending",
                expert_accepted_v1_items=["D02", "D07"], expert_reconfirmation_required=["D04"],
                pending_study_lead_items=lead_ids, flag_status_rule=flag_rule, flag_clarifications=clarification)
    for row in plan["decisions"]:
        row["prior_rater1_decision"] = r1[row["decision_id"]]["reviewer_decision"]
        row["prior_rater2_decision"] = r2[row["decision_id"]]["reviewer_decision"]
        if row["decision_id"] == "D04":
            row["proposed_decision"] = "Confirm the unchanged semantic definitions plus the revised per-flag status rule and contextual examples in v2 section 6."
    plan["capacity"] = {who: next(r for r in sheets["Capacity"] if r["reviewer"] == who) for who, sheets in returns.items()}
    plan["capacity_status"] = {"rater1": "Workload acknowledged; capacity and dates pending", "rater2": "Accepted conditional on packet delivery; proposed dates are not a project delivery commitment"}
    plan["delivery_condition_to_clarify"] = "Interpret case blocks as delivery batches preserving the fixed interleaved rater order, not adjacent same-case comparisons; obtain rater2 acknowledgment."
    write_json(OUT / "plan.json", plan)
    audit = dict(status="Returns verified; targeted revision prepared", source_sha256=source_hashes,
                 both_experts_accepted_v1=["D02", "D07"], revised_item="D04",
                 rater1_capacity="Pending", rater2_capacity="Conditionally accepted",
                 study_lead_approval="Pending", source_fields_unchanged=True,
                 original_exposure_record_unchanged=True, no_other_reviewer_signed=True,
                 model_calls=0, final_case_requirements_unchanged=True)
    write_json(OUT / "review_audit.json", audit)
    write_json(OUT / "change_log.json", dict(changes=[
        dict(id="V2-01", location="Section 6", old_text=old_flags, revised_text=new_flags,
             reason="Confirmed-positive precedence and independent status for each flag, plus contextual examples.", confirmation="Both experts pending"),
        dict(id="V2-02", location="Title/status/source link", reason="Accurate revision status and link to unchanged exposure evidence.", confirmation="Administrative only")],
        unchanged="All other substantive protocol paragraphs, including sample, primary outcome, statistics, retries, blinding and required case content, are byte-identical to v1."))

    targeted = [
        dict(item_id="D04", reviewer=who, text_to_confirm="PROTOCOL.md section 6; exact revised flag status and examples", requested_action="Accept as written or give complete replacement wording. Earlier acceptance does not approve this revision.", decision="", comments_or_replacement="", confirmed_by="", date="") for who in ["rater1", "rater2"]
    ]
    targeted += [dict(item_id="D10-delivery", reviewer="rater2", text_to_confirm="Delivery batches retain the already accepted fixed interleaved rater order; reports for one case are separated by at least two other reports.", requested_action="Clarify whether this satisfies the case-block condition in your schedule. Do not infer or create a delivery-date commitment.", decision="", comments_or_replacement="", confirmed_by="", date="")]
    capacity_rows = [dict(reviewer=who, prior_capacity=plan["capacity_status"][who], prior_start=plan["capacity"][who]["planned_start"],
                         prior_completion=plan["capacity"][who]["planned_completion"],
                         capacity_confirmed="", actual_or_conditional_delivery_date="", independent_review_start="", independent_review_completion="",
                         reconciliation_window="", available_sessions_or_conditions="", confirmed_by="", date="") for who in ["rater1", "rater2"]]
    lead_rows = [dict(decision_id=r["decision_id"], topic=r["topic"], proposal=r["proposed_decision"],
                      decision="", comments_or_revision="", confirmed_by="", date="") for r in plan["decisions"] if r["decision_id"] in lead_ids]
    first = [dict(topic="Scope", instruction="Expert D02/D07 acceptances remain recorded. Reconfirm revised D04 only; address capacity/packet conditions separately. Final case requirements are not reopened."),
             dict(topic="Save", instruction="Save a separate Targeted_confirmation_rater1.xlsx or Targeted_confirmation_rater2.xlsx. Complete only your own fields; study-lead decisions belong to the study lead."),
             dict(topic="Capacity", instruction="Previous values are evidence, not prefilled new commitments. Rater1 has not confirmed availability. Rater2 dates depend on delivery. If delivery dates remain unknown, record a conditional window or Pending; do not invent calendar dates."),
             dict(topic="Approval", instruction="All new decision fields are blank. This workbook neither appoints a third reviewer nor authorizes API generation.")]
    examples = [
        dict(example="F01", confirmed_qualifying_issue="Yes", pending_same_flag="Yes", relevant_review_complete="Either", expected_flag="Positive", reason="A confirmed qualifying issue establishes the flag."),
        dict(example="F02", confirmed_qualifying_issue="No", pending_same_flag="Yes", relevant_review_complete="Either", expected_flag="Indeterminate", reason="No confirmed positive; unresolved potentially qualifying issue remains."),
        dict(example="F03", confirmed_qualifying_issue="No", pending_same_flag="No", relevant_review_complete="Yes", expected_flag="Negative", reason="Complete relevant review without qualifying confirmed or pending issues."),
        dict(example="F04", confirmed_qualifying_issue="No", pending_same_flag="No", relevant_review_complete="No", expected_flag="Indeterminate", reason="An incomplete assessment does not establish a negative."),
        dict(example="F05", confirmed_qualifying_issue="No", pending_same_flag="No; only other flag has a pending issue", relevant_review_complete="Yes", expected_flag="Negative for this flag", reason="Determine the two flags independently."),
        dict(example="F06", confirmed_qualifying_issue="None; correct all-seven-below-3.65 comparison only", pending_same_flag="No", relevant_review_complete="Yes", expected_flag="Negative for normality flag", reason="The displayed comparison alone is not a clinical normality claim."),
    ]
    book = Workbook(); book.remove(book.active)
    for title, rows in [("Read first",first),("Targeted review",targeted),("Flag examples",examples),("Capacity",capacity_rows),("Study lead",lead_rows)]:
        ws=book.create_sheet(title);ws.append(list(rows[0]))
        for row in rows:ws.append(list(row.values()))
        ws.freeze_panes="C2";ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color="FFFFFF");c.fill=PatternFill("solid",fgColor="24476B")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(70,max(18,max(len(str(c.value or "")) for c in col)+2))
            for c in col:c.alignment=Alignment(wrap_text=True,vertical="top")
        for index in range(2,ws.max_row+1):ws.row_dimensions[index].height=120
        headers=list(rows[0])
        if "decision" in headers:
            letter=ws.cell(1,headers.index("decision")+1).column_letter
            dv=DataValidation(type="list",formula1='"Accept as written,Revise,Pending"',allow_blank=True);dv.showErrorMessage=True
            ws.add_data_validation(dv);dv.add(f"{letter}2:{letter}{ws.max_row}")
    book.save(OUT / "Targeted_confirmation.xlsx")
    assert all(sha(ROOT / rel) == expected for rel, expected in source_hashes.items())
    write_json(OUT / "manifest.json",dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        script_sha256=sha(Path(__file__)),source_sha256=source_hashes,
        output_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}))
    print(json.dumps({k:v for k,v in audit.items() if k!="source_sha256"},indent=2))


if __name__ == "__main__":
    build()
