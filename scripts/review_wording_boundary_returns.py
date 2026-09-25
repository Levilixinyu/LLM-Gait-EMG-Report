"""Receive targeted returns without replacing frozen outcomes or expert identity."""
from __future__ import annotations

import hashlib
import io
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/formal_study/wording_boundary_confirmation_v1"
FROZEN = ROOT / "docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def allowed(sheet: str, row: int, column: int) -> bool:
    return ((sheet == "Decisions" and 2 <= row <= 9 and 6 <= column <= 9)
            or (sheet == "Control annotation" and row == 2 and column in (4, 5))
            or (sheet == "Completion" and 2 <= row <= 10 and column == 2))


def main() -> None:
    build = json.loads((BASE / "BUILD_RECORD.json").read_bytes())
    confirmation_path = BASE / "HUMAN_REVIEW_CONFIRMATION.json"
    confirmation = json.loads(confirmation_path.read_bytes()) if confirmation_path.exists() else {}
    frozen_bytes = FROZEN.read_bytes()
    assert sha(frozen_bytes) == build["frozen_dataset_sha256"]
    frozen = json.loads(frozen_bytes)
    item_ids = build["items"]
    frozen_groups = {g["group_id"]: g for g in frozen["issue_groups"]}
    returns = {}
    for who in ("rater1", "rater2", "rater3"):
        filename = f"Wording_boundary_confirmation_{who}_completed.xlsx"
        matches = sorted(set(p for base in (ROOT / "docs", ROOT / "outputs", ROOT / "data/rating_packets_formal_v1") for p in base.rglob(filename)))
        if not matches:
            returns[who] = {"receipt_status": "Not located", "searched": "Active project docs, outputs and data/rating_packets_formal_v1; exact completed filename"}
            continue
        captured = [(p, p.read_bytes()) for p in matches]
        if len({sha(b) for _, b in captured}) != 1:
            returns[who] = {"receipt_status": "Multiple differing returns; selection required", "paths": [str(p.relative_to(ROOT)) for p, _ in captured]}
            continue
        path, data = captured[0]
        book = load_workbook(io.BytesIO(data))
        with ZipFile(BASE / f"Wording_boundary_confirmation_{who}.zip") as z:
            name = f"Wording_boundary_confirmation_{who}.xlsx"
            template_bytes = z.read(name)
            assert sha(template_bytes) == build["packet_members_sha256"][who][name]
            template = load_workbook(io.BytesIO(template_bytes))
        problems = []
        if book.sheetnames != template.sheetnames:
            problems.append("Sheet names differ from template")
        for sh in template:
            if sh.title not in book:
                continue
            actual = book[sh.title]
            for row in range(1, max(sh.max_row, actual.max_row) + 1):
                for col in range(1, max(sh.max_column, actual.max_column) + 1):
                    cell = actual.cell(row, col)
                    if cell.value != sh.cell(row, col).value and not allowed(sh.title, row, col):
                        problems.append(f"Static change: {sh.title}!{cell.coordinate}")
                    if cell.data_type in ("f", "e"):
                        problems.append(f"Formula/error cell: {sh.title}!{cell.coordinate}")
                    if isinstance(cell.value, str) and re.search(r"[\u4e00-\u9fff]", cell.value):
                        problems.append(f"Non-English content: {sh.title}!{cell.coordinate}")
        decisions = {}
        for row in range(2, 10):
            values = [book["Decisions"].cell(row, c).value for c in range(1, 10)]
            gid, rid, cid = values[:3]
            if gid != item_ids[row-2] or rid != frozen_groups[gid]["report_id"] or cid != frozen_groups[gid]["case_id"]:
                problems.append(f"Identity mismatch at Decisions row {row}")
            decision, reason, tags, reservation = values[5:]
            if decision not in ("Error", "Acceptable", "Pending adjudication") or not reason:
                problems.append(f"Incomplete/invalid decision or reason: {gid}")
            if decision == "Error" and (not tags or not all(re.fullmatch(r"E0[1-9]", c.strip()) for c in str(tags).split(";"))):
                problems.append(f"Missing/invalid Error categories: {gid}")
            if decision != "Error" and tags:
                problems.append(f"Category field filled for non-Error: {gid}")
            decisions[gid] = {"decision": decision, "reason": reason, "categories": tags, "reservation": reservation,
                              "frozen_individual_decision": frozen_groups[gid]["individual_records"][who]["Current decision"]}
        annotation = {"item": "AG023", "flag": book["Control annotation"]["D2"].value, "reason": book["Control annotation"]["E2"].value}
        if annotation["flag"] not in ("Yes", "No", "Uncertain") or not annotation["reason"]:
            problems.append("Incomplete control annotation")
        completion = {book["Completion"].cell(r, 1).value: book["Completion"].cell(r, 2).value for r in range(2, 11)}
        if any(v is None or not str(v).strip() for v in completion.values()):
            problems.append("Incomplete Completion fields")
        human_confirmed = who in confirmation.get("confirmed_current_return_roles", [])
        returns[who] = {
            "receipt_status": "Read", "source": str(path.relative_to(ROOT)), "sha256": sha(data),
            "identical_copies": [str(p.relative_to(ROOT)) for p, _ in captured[1:]],
            "technical_problems": problems, "form_complete_and_template_intact": not problems,
            "decision_counts": dict(Counter(r["decision"] for r in decisions.values())),
            "decisions": decisions, "control_annotation": annotation, "completion_verbatim": completion,
            "current_return_attribution_needs_confirmation": not human_confirmed,
            "human_review_and_adoption_confirmed": human_confirmed,
            "attribution_note": "The reviewer is a human expert. Original ratings were independently made by the reviewer, as confirmed by the study lead. This targeted return records the reviewer's own subsequent judgment; it is not a new initial independent-rating round." if human_confirmed else "Reviewer identity confirmation is not recorded.",
        }
    comparison = []
    for gid in item_ids:
        g = frozen_groups[gid]
        row = {"Item": gid, "Report": g["report_id"], "Case": g["case_id"]}
        labels = []
        for who in returns:
            position = returns[who].get("decisions", {}).get(gid)
            row[who] = position["decision"] if position else "Not received/selected"
            if position:
                labels.append(position["decision"])
        row["Receipt comparison"] = "Incomplete receipt" if len(labels) < 3 else "Matching submitted labels" if len(set(labels)) == 1 else "Divergent submitted labels"
        comparison.append(row)
    out = BASE / "return_review"
    out.mkdir(exist_ok=True)
    record = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Receipt and personal-position review; no new consensus or score import",
        "frozen_sha256": sha(frozen_bytes), "returns": returns, "comparison": comparison,
        "source_returns_modified": False, "frozen_outcomes_modified": False, "model_results_modified": False,
        "human_adoption_inferred": False,
        "human_review_confirmation": confirmation,
    }
    w = Workbook()
    sh = w.active
    sh.title = "Submitted positions"
    sh.append(list(comparison[0]))
    for row in comparison:
        sh.append(list(row.values()))
    details = w.create_sheet("Personal reasons")
    details.append(["Assigned role", "Item", "Decision", "Reason", "Categories", "Reservation", "Change from frozen individual label", "Source"])
    completion_sheet = w.create_sheet("Receipt and completion")
    completion_sheet.append(["Assigned role", "Field", "Recorded value"])
    for who, r in returns.items():
        completion_sheet.append([who, "Receipt status", r["receipt_status"]])
        if "decisions" not in r:
            continue
        for gid, d in r["decisions"].items():
            details.append([who, gid, d["decision"], d["reason"], d["categories"], d["reservation"], f"{d['frozen_individual_decision']} -> {d['decision']}", r["source"]])
        for key, value in r["completion_verbatim"].items():
            completion_sheet.append([who, key, value])
        completion_sheet.append([who, "AG023 flag", r["control_annotation"]["flag"]])
        completion_sheet.append([who, "AG023 annotation reason", r["control_annotation"]["reason"]])
        completion_sheet.append([who, "Current-return attribution", r["attribution_note"]])
    for sheet in w:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="23475A")
        for col in "ABCDEFGH":
            sheet.column_dimensions[col].width = 30
        for row in sheet:
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if isinstance(cell.value, str):
                    cell.data_type = "s"
        for n in range(2, sheet.max_row+1):
            sheet.row_dimensions[n].height = 85
    details.column_dimensions["D"].width = 100
    details.column_dimensions["F"].width = 65
    completion_sheet.column_dimensions["B"].width = 65
    completion_sheet.column_dimensions["C"].width = 110
    xp = out / "Submitted_positions.xlsx"
    w.save(xp)
    md = "# Targeted return receipt check\n\nThese are submitted personal positions, not a new consensus, a fresh independent rating round, or an import into frozen results. This receipt script does not modify submitted workbooks. Authorized reviewer-name corrections are recorded separately in IDENTITY_CORRECTION_RECORD.json; all judgments and exposure declarations are preserved.\n\n"
    md += "| Item | rater1 | rater2 | rater3 |\n|---|---|---|---|\n"
    for r in comparison:
        md += f"| {r['Item']} | {r['rater1']} | {r['rater2']} | {r['rater3']} |\n"
    md += "\n## Receipt and attribution\n\n"
    for who, r in returns.items():
        md += f"- **{who}:** {r['receipt_status']}. "
        if "source" in r:
            md += f"File: `{r['source']}`. Form complete and static template intact: {r['form_complete_and_template_intact']}. Counts: {r['decision_counts']}. AG023 flag: {r['control_annotation']['flag']}.\n\n"
            md += f"  Completion reviewer field, verbatim: {r['completion_verbatim']['Reviewer name']}. {r['attribution_note']}\n\n"
        else:
            md += "No current eight-item return has been located; an older rating workbook or the unchanged blank ZIP is not a substitute.\n\n"
    md += "## Remaining differences\n\n"
    for label in ("Matching submitted labels", "Divergent submitted labels", "Incomplete receipt"):
        ids = [r["Item"] for r in comparison if r["Receipt comparison"] == label]
        if ids:
            md += f"- {label}: {', '.join(ids)}.\n"
    md += "- AG023 control pathology annotation: " + "; ".join(f"{who} = {r.get('control_annotation', {}).get('flag', 'Not received')}" for who, r in returns.items()) + ". This is separate from the Error decision and category tags.\n"
    md += "\n## Handling\n\nHuman review and adoption are recorded in HUMAN_REVIEW_CONFIRMATION.json. Do not convert disagreement into a majority decision, force alignment, or treat Pending as an error. Source-specific categories and annotations remain individual. Prior discussion exposure is preserved; these targeted follow-ups must not replace the original independent-rating baseline. No frozen dataset, existing category assignment, control endpoint or model result was changed.\n\nSee [submitted positions](Submitted_positions.xlsx) and [machine-readable receipt record](RETURN_CHECK.json).\n"
    mp = out / "README.md"
    mp.write_text(md)
    record["output_sha256"] = {p.name: sha(p.read_bytes()) for p in (xp, mp)}
    (out / "RETURN_CHECK.json").write_text(json.dumps(record, indent=2) + "\n")
    assert FROZEN.read_bytes() == frozen_bytes
    print(json.dumps({"output": str(out), "receipts": {k: v["receipt_status"] for k, v in returns.items()}}))


if __name__ == "__main__":
    main()
