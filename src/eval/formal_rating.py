"""Blinded formal-study packets and immutable independent-review snapshots.

The caller supplies the complete frozen roster, explicit terminal report slots,
and verified review assets. No historical report or private key is discovered by
glob. Package publication is staged; existing packages cannot be superseded.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import secrets
import shutil
import tempfile
from datetime import datetime, timezone

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

from src.eval.formal_analysis import Coverage, Issue, LABELS
from src.llm.formal_generation import digest, write_once

G03 = ("Express a meaningful limitation of reference comparability AND why the comparison "
       "cannot establish disease effects or clinical diagnosis; for controls it cannot establish "
       "disease or overall normality. One statement may also support a case requirement.")
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
REVIEW_HEADERS = ["report_id", "case_id", "material_status", "review_state", "issue_review_complete",
                  "four_section_format", "incidental_unblinding", "notes"]
COVERAGE_HEADERS = ["report_id", "case_id", "requirement_id", "required_wording", "components",
                    "decision", "adjudication_status", "evidence_and_reason"]
ISSUE_HEADERS = ["report_id", "issue_id", "decision", "categories", "exact_quote", "locations",
                 "reason", "pathology_flag", "normality_flag"]


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def spaced_order(case_reports, seed):
    """Three randomized waves; random within-case assignment hides model codes.

    Waves are an internal construction, not displayed delivery blocks. At a wave
    boundary, reject a permutation if the same case is fewer than three positions
    from its preceding report. Ordering never examines output content.
    """
    if len(case_reports) < 3 or any(len(ids) != 3 for ids in case_reports.values()):
        raise ValueError("Spacing requires at least three cases with three planned slots each")
    rng = random.Random(seed)
    queues = {case: list(ids) for case, ids in sorted(case_reports.items())}
    for ids in queues.values():
        rng.shuffle(ids)
    result, previous = [], []
    for wave in range(3):
        for _ in range(10000):
            cases = list(queues)
            rng.shuffle(cases)
            joined = previous + cases
            if all(joined[i] not in joined[max(0, i - 2):i] for i in range(len(joined))):
                break
        else:
            raise ValueError("Cannot construct the prespecified spacing")
        result.extend(queues[case][wave] for case in cases)
        previous = (previous + cases)[-2:]
    return result


def _dropdown(sheet, column, choices, last):
    validation = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
    validation.errorTitle = "Select a listed value"
    validation.error = "Use the dropdown; describe ambiguity in the reason column."
    validation.showErrorMessage = True
    validation.errorStyle = "stop"
    sheet.add_data_validation(validation)
    validation.add(f"{column}2:{column}{max(2, last)}")


def _literal_row(sheet, values):
    # Report quotations and free text must never become executable spreadsheet formulas.
    sheet.append(values)
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = "s"


def _workbook(path, rater, order, reports, requirements):
    book = Workbook()
    instructions = book.active
    instructions.title = "Instructions"
    for row in [
        ["Independent formal review", rater],
        ["Scope", "Use only this rater folder. Do not consult the other rater before both reviews are locked."],
        ["Order", "Follow Review rows in order across sessions. Same-case reports are separated."],
        ["Materials", "Read reports/<report_id>.txt and materials/<case_id>/. Use the approved rubric."],
        ["Captured text", "Rate short, refused, malformed and truncated text. These are not Cannot assess by themselves."],
        ["Unavailable", "Do not rate an invented empty report. Mark Unavailable and explain missing materials."],
        ["Coverage", "Choose a semantic category. Pending adjudication is separate; explain unresolved readings."],
        ["Issues", "One row per unique issue group; separate E tags by semicolons and give exact quotes and locations."],
        ["Control flags", "Controls only: Yes marks a qualifying Error or Pending adjudication issue; No otherwise."],
        ["Normality", "Do not infer overall normal timing/function from control membership or displayed reference comparisons."],
        ["Pathology", "Unsupported disease, pathological mechanism or impairment; assessment questions alone do not qualify."],
        ["Format", "Record four-section compliance separately from case errors."],
        ["Identity", "Report text is verbatim, including any self-identification. Record incidental unblinding; do not edit it."],
        ["Completion", "Complete Review, Coverage and Issues, enter your name/date/confirmation below, and save a separate completed copy. Keep the delivered template unchanged."],
        ["Reviewer name", ""], ["Completion date (ISO 8601)", ""],
        ["Independent review complete (Yes)", ""],
        ["Pending issues", "Independent completion can retain documented Pending adjudication for later discussion."],
    ]:
        _literal_row(instructions, row)
    review = book.create_sheet("Review")
    coverage = book.create_sheet("Coverage")
    issues = book.create_sheet("Issues")
    review.append(REVIEW_HEADERS)
    coverage.append(COVERAGE_HEADERS)
    issues.append(ISSUE_HEADERS)
    for rid in order:
        report = reports[rid]
        case = report["case_id"]
        _literal_row(review, [rid, case, report["material_status"], "Not started", "", "", "", ""])
        rows = requirements[case] + [{"requirement_id": "G03", "required_wording": G03, "components": "AND: comparability and inference limitations"}]
        for requirement in rows:
            _literal_row(coverage, [rid, case, requirement["requirement_id"], requirement["required_wording"],
                                    requirement["components"], "", "", ""])
    _dropdown(review, "D", ["Not started", "Completed", "Unavailable"], review.max_row)
    _dropdown(review, "E", ["Yes", "No"], review.max_row)
    _dropdown(review, "F", ["Yes", "No", "Cannot assess"], review.max_row)
    _dropdown(review, "G", ["Yes", "No"], review.max_row)
    _dropdown(coverage, "F", [*LABELS, "Cannot assess"], coverage.max_row)
    _dropdown(coverage, "G", ["Final", "Pending"], coverage.max_row)
    for column, choices in [("C", ["Error", "Acceptable", "Pending adjudication", "Outside case-error scope"]),
                            ("H", ["Yes", "No"]), ("I", ["Yes", "No"])]:
        _dropdown(issues, column, choices, 5000)
    for sheet in book:
        sheet.freeze_panes = "D2" if sheet.title == "Coverage" else "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cells in sheet.columns:
            sheet.column_dimensions[cells[0].column_letter].width = min(65, max(20, len(str(cells[0].value)) + 3))
    book.save(path)


def build_package(output, slots, requirements, case_assets, common_assets):
    """Publish a new package, retaining every planned slot and verbatim text.

    Slots contain slot_id, case_id, model_key, report_text (None for no report),
    terminal_status and source_sha256. Hash/source attribution is checked by the
    future frozen-run importer before calling this packaging component.
    Assets are explicit {safe filename: bytes} maps, never whole-folder copies.
    """
    output = Path(output)
    if output.exists():
        raise FileExistsError("An existing packet may not be replaced")
    if set(case_assets) != set(requirements) or not requirements:
        raise ValueError("Asset and requirement rosters differ")
    if any(not SAFE_NAME.fullmatch(c) or c in {".", ".."} for c in requirements):
        raise ValueError("Unsafe case ID")
    if len({s["slot_id"] for s in slots}) != len(slots):
        raise ValueError("Duplicate slot")
    model_keys = {s["model_key"] for s in slots}
    expected = {(c, m) for c in requirements for m in model_keys}
    if len(model_keys) != 3 or {(s["case_id"], s["model_key"]) for s in slots} != expected or len(slots) != len(expected):
        raise ValueError("Require all planned case/model slots, including no-report outcomes")
    for case, rows in requirements.items():
        ids = [r["requirement_id"] for r in rows]
        if not ids or len(set(ids)) != len(ids) or "G03" in ids:
            raise ValueError("Invalid case requirements")
    for assets in [common_assets, *case_assets.values()]:
        if any(not SAFE_NAME.fullmatch(name) or name in {".", ".."} or not isinstance(data, bytes)
               for name, data in assets.items()):
            raise ValueError("Unsafe asset name or non-byte content")
    for slot in slots:
        text = slot["report_text"]
        if slot["terminal_status"] not in {"captured", "empty", "technical_failure", "closed_no_report"}:
            raise ValueError("Nonterminal slot cannot be packaged")
        if (text is not None and (not isinstance(text, str) or not text.strip())) or (
            (text is not None) != (slot["terminal_status"] == "captured")
        ):
            raise ValueError("Captured text and terminal status disagree")
        if not re.fullmatch(r"[0-9a-f]{64}", slot["source_sha256"]):
            raise ValueError("Missing source evidence hash")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=output.name + ".", suffix=".building", dir=output.parent))
    try:
        private = staging / "private"
        private.mkdir(mode=0o700)
        public_reports, mapping, case_reports = {}, {}, {c: [] for c in requirements}
        for slot in slots:
            rid = "R" + secrets.token_hex(8).upper()
            if rid in mapping:
                raise RuntimeError("Random ID collision")
            public_reports[rid] = {"case_id": slot["case_id"],
                                   "material_status": "Available" if slot["report_text"] is not None else "Unavailable"}
            mapping[rid] = {k: v for k, v in slot.items() if k != "report_text"}
            mapping[rid]["report_sha256"] = sha_bytes(slot["report_text"].encode()) if slot["report_text"] is not None else None
            case_reports[slot["case_id"]].append(rid)
        slot_by_id = {s["slot_id"]: s for s in slots}
        seeds, orders = {}, {}
        for rater in ("rater1", "rater2"):
            seeds[rater] = secrets.randbits(128)
            orders[rater] = spaced_order(case_reports, seeds[rater])
        if orders["rater1"] == orders["rater2"]:
            raise RuntimeError("Independent order collision; create a fresh package")
        _save_json(private / "answer_key_DO_NOT_SHARE.json", {"mapping": mapping, "order_seeds": seeds, "orders": orders})
        for rater in ("rater1", "rater2"):
            folder = staging / "raters" / rater
            (folder / "reports").mkdir(parents=True)
            (folder / "materials").mkdir()
            for name, data in common_assets.items():
                (folder / "materials" / name).write_bytes(data)
            for case, assets in case_assets.items():
                destination = folder / "materials" / case
                destination.mkdir()
                for name, data in assets.items():
                    (destination / name).write_bytes(data)
            for rid in orders[rater]:
                report_text = slot_by_id[mapping[rid]["slot_id"]]["report_text"]
                if report_text is not None:
                    (folder / "reports" / f"{rid}.txt").write_bytes(report_text.encode())
            _save_json(folder / "reports.json", {"order": orders[rater], "reports": public_reports})
            _workbook(folder / "Independent_ratings.xlsx", rater, orders[rater], public_reports, requirements)
            (folder / "README.md").write_text(
                "# Independent formal review\n\nOpen Independent_ratings.xlsx and follow the Instructions sheet. "
                "Follow its fixed Review order. Report files are verbatim; no-report slots have no text file. "
                "Case-specific requirements are the frozen rows in Coverage; the five-case developmental annex "
                "is not the requirements list for this study. Do not share your ratings with the other rater "
                "until both independent reviews have been locked.\n")
        hashes = {str(p.relative_to(staging)): sha_bytes(p.read_bytes())
                  for p in sorted(staging.rglob("*")) if p.is_file()}
        _save_json(private / "package_integrity.json", {"files_sha256": hashes, "requirements": requirements})
        os.rename(staging, output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return {"report_slots": len(slots), "available_reports": sum(s["report_text"] is not None for s in slots),
            "coverage_rows_per_rater": sum(len(rows) + 1 for rows in requirements.values()) * 3}


def _read_rows(book, sheet, headers):
    rows = list(book[sheet].values)
    if list(rows[0]) != headers:
        raise ValueError(f"Changed {sheet} columns")
    return [dict(zip(headers, row)) for row in rows[1:] if any(v is not None for v in row)]


def validate_return(workbook, template, reports, report_texts):
    """Validate structural completion, not clinical correctness or expert identity."""
    book = load_workbook(workbook, data_only=False)
    original = load_workbook(template, data_only=False)
    for sheet in book:
        if any(cell.data_type == "f" for row in sheet for cell in row):
            raise ValueError("Formulas are not valid review evidence")
    confirmation = [book["Instructions"].cell(row, 2).value for row in (15, 16, 17)]
    if not all(isinstance(v, str) and v.strip() for v in confirmation) or confirmation[-1] != "Yes":
        raise ValueError("Reviewer name, completion date and explicit independent completion are required")
    try:
        datetime.fromisoformat(confirmation[1])
    except ValueError as exc:
        raise ValueError("Completion date must be ISO 8601") from exc
    review = _read_rows(book, "Review", REVIEW_HEADERS)
    baseline = _read_rows(original, "Review", REVIEW_HEADERS)
    if [[r[h] for h in REVIEW_HEADERS[:3]] for r in review] != [[r[h] for h in REVIEW_HEADERS[:3]] for r in baseline]:
        raise ValueError("Changed planned report roster or order")
    for row in review:
        if row["material_status"] == "Unavailable":
            if row["review_state"] != "Unavailable" or not row["notes"] or row["issue_review_complete"] == "Yes":
                raise ValueError("Unavailable slots need an explicit missing-material record")
        elif (row["review_state"] != "Completed" or row["issue_review_complete"] != "Yes"
              or row["four_section_format"] not in {"Yes", "No", "Cannot assess"}
              or row["incidental_unblinding"] not in {"Yes", "No"}):
            raise ValueError("Available report review is incomplete")
    coverage = _read_rows(book, "Coverage", COVERAGE_HEADERS)
    expected = _read_rows(original, "Coverage", COVERAGE_HEADERS)
    if [[r[h] for h in COVERAGE_HEADERS[:5]] for r in coverage] != [[r[h] for h in COVERAGE_HEADERS[:5]] for r in expected]:
        raise ValueError("Changed requirement wording, membership or order")
    for row in coverage:
        unavailable = reports[row["report_id"]]["material_status"] == "Unavailable"
        if unavailable:
            if row["decision"] not in {None, "Cannot assess"}:
                raise ValueError("Unavailable report cannot be scored as content")
            continue
        if row["adjudication_status"] not in {"Final", "Pending"}:
            raise ValueError("Missing coverage adjudication status")
        decision = Coverage(row["decision"], row["adjudication_status"] == "Pending")
        if not decision.final and not row["evidence_and_reason"]:
            raise ValueError("Unresolved coverage needs a reason")
        if row["decision"] is None and not decision.pending:
            raise ValueError("Blank final coverage label")
    issues = _read_rows(book, "Issues", ISSUE_HEADERS)
    seen = set()
    for row in issues:
        rid = row["report_id"]
        if rid not in reports or reports[rid]["material_status"] != "Available":
            raise ValueError("Issue references an unknown or unavailable report")
        key = (rid, row["issue_id"])
        if key in seen:
            raise ValueError("Duplicate issue group")
        seen.add(key)
        control = reports[rid]["case_id"].startswith("control_")
        allowed_flags = {"Yes", "No"} if control else {None, "No"}
        if row["pathology_flag"] not in allowed_flags or row["normality_flag"] not in allowed_flags:
            raise ValueError("Both control-flag fields require Yes or No")
        flags = tuple(flag for flag in ("pathology", "normality") if row[f"{flag}_flag"] == "Yes")
        if flags and not control:
            raise ValueError("Semantic flags apply only to controls")
        categories = tuple(t.strip() for t in (row["categories"] or "").split(";") if t.strip())
        Issue(row["issue_id"], row["decision"], categories, row["exact_quote"] or "", flags)
        if not row["reason"] or not row["locations"]:
            raise ValueError("An issue needs a reason and locations")
        if row["exact_quote"] and row["exact_quote"] not in report_texts[rid]:
            raise ValueError("Issue quote is not an exact substring of the saved report")
    return {"reviewer": confirmation[0], "completion_date": confirmation[1],
            "review": review, "coverage": coverage, "issues": issues}


def lock_independent_review(package, rater, returned_workbook):
    """Save a new byte-exact return and derived records without opening the key.

    A snapshot records the submitted name/attestation, not identity verification
    or a new signature. Do not use this to create an expert confirmation.
    """
    package = Path(package)
    if rater not in {"rater1", "rater2"}:
        raise ValueError("Unknown rater")
    folder = package / "raters" / rater
    integrity = json.loads((package / "private/package_integrity.json").read_text())
    prefix = f"raters/{rater}/"
    for name, expected in integrity["files_sha256"].items():
        if name.startswith(prefix) and sha_bytes((package / name).read_bytes()) != expected:
            raise ValueError("Delivered template or material changed; preserve and recover the correct copy")
    reports = json.loads((folder / "reports.json").read_text())["reports"]
    texts = {rid: (folder / "reports" / f"{rid}.txt").read_bytes().decode("utf-8") for rid, row in reports.items()
             if row["material_status"] == "Available"}
    raw = Path(returned_workbook).read_bytes()
    normalized = validate_return(io.BytesIO(raw), folder / "Independent_ratings.xlsx", reports, texts)
    destination = package / "private" / "independent_locks" / rater
    destination.mkdir(parents=True, exist_ok=False)
    try:
        (destination / "submitted.xlsx").write_bytes(raw)
        write_once(destination / "normalized.json", normalized)
        write_once(destination / "lock.json", {
            "rater": rater, "locked_utc": datetime.now(timezone.utc).isoformat(),
            "submitted_sha256": sha_bytes(raw), "normalized_sha256": digest(normalized),
            "attestation_scope": "Submitted independent completion; no agent-created human decision",
        })
    except BaseException:
        # Retain any partial snapshot for recovery; never silently overwrite it.
        raise
    return {"rater": rater, "locked": True, "submitted_sha256": sha_bytes(raw)}


def require_both_independent_locks(package):
    """Gate cross-review on intact original submissions from both raters."""
    records = {}
    for rater in ("rater1", "rater2"):
        root = Path(package) / "private" / "independent_locks" / rater
        if not (root / "lock.json").exists():
            raise ValueError("Both independent reviews must be locked before cross-review")
        lock = json.loads((root / "lock.json").read_text())
        normalized = json.loads((root / "normalized.json").read_text())
        if sha_bytes((root / "submitted.xlsx").read_bytes()) != lock["submitted_sha256"] or digest(normalized) != lock["normalized_sha256"]:
            raise ValueError("Independent snapshot was altered")
        records[rater] = normalized
    return records
