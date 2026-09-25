"""Record explicit study-lead authorization and expert v2 returns in a new version."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/formal_study/execution_analysis_v2_draft"
OUT = ROOT / "docs/formal_study/execution_analysis_v3_draft"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def records(sheet):
    rows = list(sheet.values)
    return [dict(zip(rows[0], row)) for row in rows[1:]]


def build():
    if OUT.exists():
        raise FileExistsError("Preserve the existing version; do not overwrite approval evidence.")
    prior_manifest = read_json(BASE / "manifest.json")
    sources = {}
    for name, digest in prior_manifest["output_sha256"].items():
        p = BASE / name
        assert sha(p) == digest, name
        sources[str(p.relative_to(ROOT))] = digest
    for name in ["STUDY_LEAD_PREAPPROVAL_AUDIT.md", "STUDY_LEAD_PREAPPROVAL_AUDIT.json"]:
        sources[str((BASE / name).relative_to(ROOT))] = sha(BASE / name)
    audit = (BASE / "STUDY_LEAD_PREAPPROVAL_AUDIT.md").read_text()
    assert sha(BASE / "STUDY_LEAD_PREAPPROVAL_AUDIT.md") == read_json(BASE / "STUDY_LEAD_PREAPPROVAL_AUDIT.json")["audit_sha256"]
    template = load_workbook(BASE / "Targeted_confirmation.xlsx")
    original = {s.title: records(s) for s in template}
    returns = {}
    for who in ["rater1", "rater2"]:
        path = BASE / f"Targeted_confirmation_{who}.xlsx"
        sources[str(path.relative_to(ROOT))] = sha(path)
        wb = load_workbook(path)
        assert wb.sheetnames == template.sheetnames
        sheets = {s.title: records(s) for s in wb}
        for name in ["Read first", "Flag examples", "Study lead"]:
            assert sheets[name] == original[name], (who, name)
        for name, prefix in [("Targeted review", 4), ("Capacity", 4)]:
            assert len(sheets[name]) == len(original[name])
            for before, after in zip(original[name], sheets[name]):
                assert all(before[key] == after[key] for key in list(before)[:prefix])
                if before["reviewer"] != who:
                    assert before == after
                else:
                    assert after["confirmed_by"] == who and after["date"] == "2026-09-18"
                    if name == "Targeted review":
                        assert after["decision"] == "Accept as written"
        for sheet in wb:
            for row in sheet:
                for cell in row:
                    assert cell.data_type != "f"
                    if isinstance(cell.value, str):
                        assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", cell.value)
        returns[who] = sheets
    r1_comment = returns["rater1"]["Targeted review"][0]["comments_or_replacement"]
    assert sha(BASE / "PROTOCOL.md") in r1_comment
    assert sha(BASE / "Targeted_confirmation.xlsx") in r1_comment

    # Take the authorized changes from the actual audit, not a paraphrase.
    def quoted(section):
        body = audit.split(section, 1)[1].split("\n## ", 1)[0]
        matches = re.findall(r"^> (.+)$", body, re.M)
        assert len(matches) == 1
        return matches[0]
    joint = quoted("## D03: make the joint outcome explicit")
    capture = quoted("## D08: define capture, not quality")
    configuration = quoted("## D09: budget and effective model configuration")
    old = (BASE / "PROTOCOL.md").read_text()
    new = old.replace("# Execution and analysis plan v2", "# Execution and analysis plan v3", 1)
    old_status = old.splitlines()[2]
    new_status = "Status: **Study-lead decisions recorded with the authorized D03/D08 clarifications; D09 verification policy accepted, concrete provider configuration pending.** Expert D02/D04/D07 content and the D04 examples are confirmed. Rater2 delivery clarification is confirmed; rater1 capacity remains pending. This is not a fully released batch: no live compatibility check or formal generation is authorized by this record. See APPROVAL_STATUS.md for exact scope."
    new = new.replace(old_status, new_status, 1)
    joint_anchor = "Apply analogous accounting to the two control flags and the secondary joint measure."
    assert joint_anchor in new
    new = new.replace(joint_anchor, "Apply analogous accounting to the two control flags; use the explicit joint-success rule below for the secondary joint measure.", 1)
    new = new.replace("\nShow each rater's independent full-coverage results", "\n" + joint + "\n\nShow each rater's independent full-coverage results", 1)
    old_budget = next(line for line in old.splitlines() if line.startswith("Proposal: retain the existing 8,000-token"))
    new = new.replace(old_budget, configuration, 1)
    new = new.replace("\nAfter allowed transient attempts are exhausted", "\n" + capture + "\n\nAfter allowed transient attempts are exhausted", 1)
    # Keep the actual expert-reviewed section 6 byte-for-byte; the approval status
    # supersedes its historical pending sentence without altering reviewed content.
    OUT.mkdir()
    (OUT / "PROTOCOL.md").write_text(new)
    write_json(OUT / "expert_return_records.json", returns)
    user_record = dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(), date="2026-09-18",
        authority="User acting as study lead in the active conversation",
        confirmation_english="Okay, proceed as you recommended.",
        context="The user first expressed agreement with all seven Study lead items, requested a critical audit, and then explicitly authorized proceeding with the audit recommendations.",
        language_provenance="English translation; original-language statements remain in the conversation. Administrative recording by the assistant, not an invented handwritten or expert signature.",
        audit_source_sha256=sha(BASE / "STUDY_LEAD_PREAPPROVAL_AUDIT.md"),
        accept_as_written=["D01", "D05", "D06", "D11"],
        accept_with_exact_audit_clarification=["D03", "D08"],
        D09="Verification policy accepted; concrete configuration not frozen",
        does_not_authorize=["Live API compatibility calls", "Formal 105-report generation", "Changing expert requirements", "Claiming completed readiness checks", "Confirming another person's availability"])
    write_json(OUT / "STUDY_LEAD_CONFIRMATION.json", user_record)
    plan = copy.deepcopy(read_json(BASE / "plan.json"))
    plan.update(version="execution-analysis-v3-draft", status="Scientific/operational decisions recorded; configuration, rater1 capacity and readiness pending",
        clinical_operational_items_approved=True, expert_content_items_approved=["D02", "D04", "D07"],
        expert_reconfirmation_required=[], pending_study_lead_items=["D09 concrete provider configuration"],
        plan_approved=False, study_lead_policy_approved=True, provider_configuration_frozen=False,
        generation_authorized=False, live_compatibility_check_authorized=False, model_calls=0,
        joint_success_rule=joint, captured_response_rule=capture, provider_configuration_policy=configuration)
    plan["generation"]["historical_output_token_budget_candidate"] = plan["generation"].pop("proposed_output_token_budget")
    plan["generation"]["approved_output_token_budget"] = None
    for item in plan["generation"]["candidate_models"]:
        item["verification"] = "Identifier documented by official sources during prior audit; account access, exact settings and live behavior not verified"
    approved = []
    for row in plan["decisions"]:
        identifier = row["decision_id"]
        if identifier in ["D01", "D03", "D05", "D06", "D08", "D09", "D11"]:
            status = "Accepted as written"
            note = "Study-lead policy approval; not a declaration that implementation checks have passed."
            if identifier == "D03": status, note = "Accepted with recorded clarification", joint
            if identifier == "D08": status, note = "Accepted with recorded clarification", capture
            if identifier == "D09": status, note = "Verification policy accepted; settings pending", configuration
            row.update(reviewer_decision=status, comments_or_revision=note,
                       reviewer="Study lead (user confirmation in conversation; recorded by assistant)", date="2026-09-18")
            approved.append(dict(decision_id=identifier, topic=row["topic"], decision=status,
                                 exact_scope_or_clarification=note, confirmation_source="STUDY_LEAD_CONFIRMATION.json",
                                 confirmed_by="Study lead via conversation", recorded_by="Assistant", date="2026-09-18"))
    plan["capacity"] = {who: next(r for r in sheets["Capacity"] if r["reviewer"] == who) for who, sheets in returns.items()}
    plan["capacity_status"] = {"rater1": "Pending: no availability/schedule commitment", "rater2": "Accepted conditional on delivery; interleaved delivery order explicitly accepted"}
    plan.pop("delivery_condition_to_clarify", None)
    plan["delivery_order_clarification"] = "Closed by explicit rater2 acceptance in Targeted_confirmation_rater2.xlsx"
    write_json(OUT / "plan.json", plan)
    write_json(OUT / "change_log.json", dict(changes=[
        dict(id="D03", operation="Add exact authorized audit clarification in section 9", text=joint),
        dict(id="D08", operation="Add exact authorized audit clarification in section 10", text=capture),
        dict(id="D09", operation="Replace historical budget paragraph in section 10", old_text=old_budget, text=configuration),
        dict(id="Administrative", operation="Update title/status and record user/expert confirmations; preserve original return files")],
        no_expert_case_requirement_changes=True, section_6_byte_identical=True))
    book = Workbook(); sheet = book.active; sheet.title="Study lead decisions"
    sheet.append(list(approved[0]))
    for row in approved: sheet.append(list(row.values()))
    sheet.freeze_panes="C2"; sheet.auto_filter.ref=sheet.dimensions
    for cell in sheet[1]:cell.font=Font(bold=True,color="FFFFFF");cell.fill=PatternFill("solid",fgColor="24476B")
    for col in sheet.columns:
        sheet.column_dimensions[col[0].column_letter].width=min(75,max(18,max(len(str(c.value or "")) for c in col)+2))
        for cell in col:cell.alignment=Alignment(wrap_text=True,vertical="top")
    for i in range(2,sheet.max_row+1):sheet.row_dimensions[i].height=160
    book.save(OUT / "Study_lead_decisions.xlsx")
    assert all(sha(ROOT/rel)==h for rel,h in sources.items())
    write_json(OUT / "manifest.json",dict(created_at_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__)),
        source_sha256=sources,output_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}))
    print(json.dumps(dict(study_lead_decisions_recorded=7, expert_D04="Both accepted", rater2_delivery="Accepted",
                         rater1_capacity="Pending", provider_configuration="Pending", model_calls=0),indent=2))


if __name__ == "__main__":
    build()
