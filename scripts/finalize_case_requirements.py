"""Materialize expert-confirmed case requirements without altering review evidence."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/formal_study/case_review_reconciliation_v1"
DEST = ROOT / "docs/formal_study/case_requirements_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def records(sheet):
    values = list(sheet.values)
    return [dict(zip(values[0], row)) for row in values[1:]]


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build():
    if DEST.exists():
        raise FileExistsError("Never overwrite a finalized version; use an explicitly revised version.")
    names = [
        "Case_requirements_reconciliation_consensus.xlsx",
        "Case_requirements_reconciliation_rater1_reply.xlsx",
        "Case_requirements_reconciliation_rater2_reply.xlsx",
        "CONSENSUS_RETURN_AUDIT.json",
        "RATER1_REMAINING_REQUIREMENTS_CONFIRMATION.md",
        "RATER1_REMAINING_REQUIREMENTS_CONFIRMATION.json",
        "RATER2_R099_CONFIRMATION.md",
    ]
    protected = {str((SOURCE / name).relative_to(ROOT)): sha(SOURCE / name) for name in names}
    r1 = read_json(SOURCE / names[5])
    audit = read_json(SOURCE / names[3])
    r1_text = (SOURCE / names[4]).read_text()
    r2_text = (SOURCE / names[6]).read_text()
    source_hash = sha(SOURCE / names[0])
    assert source_hash == r1["source_sha256"] == audit["source_sha256"][names[0]]
    assert source_hash in r2_text and sha(SOURCE / names[4]) in r2_text
    assert "**Accepted as written.**" in r2_text
    assert sha(SOURCE / names[6]) == "14a3512a27131d3d2f398ee7bbb5602e0772f1f1ba98b7b84514305ef450b03e"
    for name in names[1:3]:
        assert sha(SOURCE / name) == audit["source_sha256"][name]

    wb = load_workbook(SOURCE / names[0])
    originals = records(wb["Full comparison"])
    additions = records(wb["Additions"])
    topics = records(wb["Shared questions"])
    assert len(originals) == 200 and len(additions) == 13 and len(topics) == 8
    by_id = {row["comparison_id"]: row for row in originals}
    accepted = set(r1["accepted_comparison_ids"])
    prior = set(audit["confirmed_original_ids"])
    assert len(accepted) == 176 and len(prior) == 23 and not accepted & prior
    assert accepted | prior | {"R099"} == set(by_id)
    assert {row["comparison_id"] for row in r1["accepted_rows"]} == accepted
    assert len(r1["accepted_rows"]) == 176
    for row in r1["accepted_rows"]:
        src = by_id[row["comparison_id"]]
        for left, right in [("case_id", "case_id"), ("item_id", "item_id"),
                            ("final_decision", "final_decision"),
                            ("final_wording", "final_required_wording"),
                            ("final_required_components", "final_components_and_optional_content")]:
            assert row[left] == src[right], (row["comparison_id"], left)
    assert len(r1["exceptions"]) == 1
    exception = r1["exceptions"][0]
    assert exception["comparison_id"] == "R099"
    for key in ["proposed_final_wording", "proposed_final_required_components"]:
        assert exception[key] in r1_text and exception[key] in r2_text
    input_path = ROOT / "docs/formal_study" / r1["exception_input_evidence"]["path"]
    assert sha(input_path) == r1["exception_input_evidence"]["sha256"]
    assert all(line in input_path.read_text() for line in r1["exception_input_evidence"]["lines"])
    protected[str(input_path.relative_to(ROOT))] = sha(input_path)

    # Check the explicit reply chain instead of inferring confirmation from filled cells.
    first = load_workbook(SOURCE / names[1])
    second = load_workbook(SOURCE / names[2])
    for sheet, key in [("Shared questions", "topic_id"), ("Full comparison", "comparison_id"), ("Additions", "addition_id")]:
        for a, b, final in zip(records(first[sheet]), records(second[sheet]), records(wb[sheet])):
            assert all(b.get(k) == v for k, v in a.items())
            if sheet == "Full comparison" and final[key] not in prior:
                continue
            assert a.get("rater1_response_status") and b.get("rater2_response_status")
            if sheet == "Shared questions":
                assert b["rater2_response"] == final["agreed_rule"]
            elif final["final_decision"] != "Omit":
                for src, dest in [("rater1_proposed_complete_wording", "final_required_wording"),
                                  ("rater1_proposed_components", "final_components_and_optional_content")]:
                    assert (a.get(src) or a[dest]) == final[dest]

    final_rows = []
    for kind, rows, key in [("Original", originals, "comparison_id"), ("Addition", additions, "addition_id")]:
        for source in rows:
            item = source[key]
            decision = source["final_decision"]
            wording = source["final_required_wording"] or ""
            components = source["final_components_and_optional_content"] or ""
            evidence = "Case_requirements_reconciliation_rater1_reply.xlsx; Case_requirements_reconciliation_rater2_reply.xlsx"
            if item in accepted:
                evidence = "Case_requirements_reconciliation_consensus.xlsx; RATER1_REMAINING_REQUIREMENTS_CONFIRMATION.md"
            if item == "R099":
                decision = exception["proposed_final_decision"]
                wording = exception["proposed_final_wording"]
                components = exception["proposed_final_required_components"]
                evidence = "RATER1_REMAINING_REQUIREMENTS_CONFIRMATION.md; RATER2_R099_CONFIRMATION.md"
            assert decision in {"Retain", "Modify", "Omit"}
            assert decision == "Omit" or (wording and components)
            final_rows.append(dict(
                record_id=item, record_type=kind, case_id=source["case_id"],
                source_item_id=source.get("item_id") or item, decision=decision,
                included="Yes" if decision != "Omit" else "No",
                required_wording=wording, required_components_and_optional_content=components,
                confirmation_status="Confirmed by both reviewers",
                confirmation_date="2026-09-18", evidence_files=evidence,
            ))
    included = [row for row in final_rows if row["included"] == "Yes"]
    omitted = [row for row in final_rows if row["included"] == "No"]
    assert len(included) == 149 and len(omitted) == 64
    cases = sorted({row["case_id"] for row in final_rows})
    assert len(cases) == 35
    case_summary = [dict(case_id=case, included_requirements=sum(r["case_id"] == case for r in included),
                         omitted_candidates=sum(r["case_id"] == case for r in omitted)) for case in cases]
    final_topics = [dict(topic_id=r["topic_id"], topic=r["topic"], agreed_rule=r["agreed_rule"],
                         confirmation_status="Confirmed by both reviewers", confirmation_date="2026-09-18",
                         evidence_files="Case_requirements_reconciliation_rater1_reply.xlsx; Case_requirements_reconciliation_rater2_reply.xlsx") for r in topics]
    instructions = [
        dict(topic="Version", instruction="case-requirements-v1; expert-confirmed prospective case requirements for 25 stroke cases and 10 controls."),
        dict(topic="Use", instruction="Use Included requirements for case-specific coverage and Shared rules for agreed component interpretation. AND/OR wording and optional anchors must be respected. Apply the approved rubric v2 and its common requirements separately; this file does not replace them."),
        dict(topic="Omissions", instruction="Omitted candidates carry no coverage requirement. Assertions about optional findings remain subject to correctness review."),
        dict(topic="Evidence", instruction="Evidence filenames refer to ../case_review_reconciliation_v1/. Source hashes and the exact R099 change are recorded in the manifest and change log. This is an administrative compilation of expert confirmations, not a new signature."),
        dict(topic="Counting", instruction="149 included requirements and 64 omitted candidates across 35 cases. These counts do not define weights, outcomes or the statistical analysis; cases have different numbers of included requirements."),
        dict(topic="Scope", instruction="No historical rating changes or report-generation authorization. Exposure checks, outcome/analysis decisions and generation/retry/failure rules remain separate work."),
    ]
    DEST.mkdir()
    write_csv(DEST / "case_requirements.csv", final_rows)
    write_csv(DEST / "shared_rules.csv", final_topics)
    write_csv(DEST / "case_summary.csv", case_summary)
    final = Workbook()
    final.remove(final.active)
    sheets = [("Read first", instructions), ("Shared rules", final_topics), ("Case summary", case_summary),
              ("Included requirements", included), ("Omitted candidates", omitted)]
    for name, rows in sheets:
        ws = final.create_sheet(name)
        ws.append(list(rows[0]))
        for row in rows:
            ws.append(list(row.values()))
        ws.freeze_panes = "D2" if name in {"Included requirements", "Omitted candidates"} else "B2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="24476B")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(70, max(18, max(len(str(c.value or "")) for c in col) + 2))
            for cell in col:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        for row in range(2, ws.max_row + 1):
            ws.row_dimensions[row].height = 150 if name != "Case summary" else 30
    final.save(DEST / "Final_case_requirements_v1.xlsx")
    changed = [dict(record_id="R099", field=field, source_text=by_id["R099"][original], final_text=exception[replacement])
               for field, original, replacement in [
                   ("required_wording", "final_required_wording", "proposed_final_wording"),
                   ("required_components_and_optional_content", "final_components_and_optional_content", "proposed_final_required_components")]]
    write_json(DEST / "change_log.json", dict(substantive_changes=changed,
        administrative_changes="Clean presentation, explicit included/omitted separation and evidence-based confirmation status. No other requirement decisions, wording or component fields changed."))
    summary = dict(version="case-requirements-v1", status="Finalized from bilateral expert confirmations",
                   original_rows=200, addition_rows=13, shared_topics=8, participants=35,
                   included_requirements=149, omitted_candidates=64, unresolved_items=0,
                   counts_by_decision=dict(Counter(r["decision"] for r in final_rows)),
                   requirements_frozen=True, generation_authorized=False, model_calls=0,
                   external_exposure_confirmation="Pending",
                   scope="Prospective case-specific requirements only; weights, outcomes, analysis and generation/failure policy are not approved by these confirmations.")
    write_json(DEST / "summary.json", summary)

    # Verify the saved artifacts against the actual source fields, not just counts.
    output_wb = load_workbook(DEST / "Final_case_requirements_v1.xlsx")
    saved = records(output_wb["Included requirements"]) + records(output_wb["Omitted candidates"])
    normalized = lambda r: {k: "" if v is None else str(v) for k, v in r.items()}
    assert {r["record_id"]: normalized(r) for r in saved} == {r["record_id"]: normalized(r) for r in final_rows}
    for row in final_rows:
        if row["record_id"] == "R099":
            continue
        src = by_id[row["record_id"]] if row["record_type"] == "Original" else next(r for r in additions if r["addition_id"] == row["record_id"])
        assert row["decision"] == src["final_decision"]
        assert row["required_wording"] == (src["final_required_wording"] or "")
        assert row["required_components_and_optional_content"] == (src["final_components_and_optional_content"] or "")
    for sheet in output_wb:
        for row in sheet:
            for cell in row:
                assert cell.data_type != "f"
                if isinstance(cell.value, str):
                    assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", cell.value)
    assert all(sha(ROOT / rel) == value for rel, value in protected.items())
    write_json(DEST / "validation.json", dict(status="Passed", source_hashes_verified=len(protected),
        accepted_176_rows_match=True, rater2_accepts_exact_R099_replacement=True,
        reply_chain_verified=True, original_sources_unchanged=True,
        other_212_rows_unchanged=True, workbook_matches_csv_rows=True, english_only=True,
        substantive_changed_rows=["R099"], unresolved_items=0))
    write_json(DEST / "manifest.json", dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        script_sha256=sha(Path(__file__)), source_sha256=protected,
        output_sha256={p.name: sha(p) for p in DEST.iterdir() if p.is_file()}))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    build()
