"""Validate and retain explicitly submitted human final decisions.

No consensus label or signature is generated here. The importer checks recorded
provenance and scope, not the authenticity of a person's identity or signature.
Both original independent reviews must already be locked.
"""
from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path

import numpy as np

from .formal_analysis import Coverage, Issue, analyze, assessments_from_review, independent_agreement
from .formal_rating import require_both_independent_locks
from src.llm.formal_generation import IntegrityError, digest, write_once


def import_final_consensus(package, submission_file):
    """Final JSON: independent_submission_sha256, final_review, authorities.

    Each authority binds the exact final_review hash and an explicit report-ID
    scope. It contains either both raters' confirmations or a named third human
    adjudicator plus documented prior discussion. Every report needs one such
    authority. Pending labels remain pending even in a finalized release.
    """
    package, submission_file = Path(package), Path(submission_file).resolve()
    locked = require_both_independent_locks(package)
    integrity = json.loads((package / "private/package_integrity.json").read_text())
    for name, expected in integrity["files_sha256"].items():
        if name.startswith("raters/") and hashlib.sha256((package / name).read_bytes()).hexdigest() != expected:
            raise IntegrityError("Delivered source materials changed")
    raw = submission_file.read_bytes()
    submission = json.loads(raw)
    for rater in ("rater1", "rater2"):
        lock = json.loads((package / "private/independent_locks" / rater / "lock.json").read_text())
        if submission["independent_submission_sha256"].get(rater) != lock["submitted_sha256"]:
            raise IntegrityError("Final decisions refer to different independent submissions")
    final = submission["final_review"]
    original = locked["rater1"]
    report_rows = {r["report_id"]: r for r in final["review"]}
    originals = {r["report_id"]: r for r in original["review"]}
    if len(report_rows) != len(final["review"]) or set(report_rows) != set(originals):
        raise IntegrityError("Final report roster changed")
    expected_coverage = {(r["report_id"], r["requirement_id"]): r for r in original["coverage"]}
    final_coverage = {(r["report_id"], r["requirement_id"]): r for r in final["coverage"]}
    if len(final_coverage) != len(final["coverage"]) or set(final_coverage) != set(expected_coverage):
        raise IntegrityError("Final requirement membership changed")
    for key, row in final_coverage.items():
        expected = expected_coverage[key]
        if any(row[field] != expected[field] for field in ("report_id", "case_id", "requirement_id", "required_wording", "components")):
            raise IntegrityError("Final requirement identity or wording changed")
        if row["adjudication_status"] not in {"Final", "Pending"}:
            raise IntegrityError("Missing final coverage status")
        assessment = Coverage(row["decision"], row["adjudication_status"] == "Pending")
        if row["decision"] is None and not assessment.pending:
            raise IntegrityError("Blank final label is not a resolved decision")
        if not assessment.final and not row.get("evidence_and_reason"):
            raise IntegrityError("Unknown final coverage requires a reason")
    for rid, row in report_rows.items():
        if any(row[field] != originals[rid][field] for field in ("case_id", "material_status")):
            raise IntegrityError("Final material identity changed")
        expected_state = "Completed" if row["material_status"] == "Available" else "Unavailable"
        if row["review_state"] != expected_state:
            raise IntegrityError("Incomplete final review record")
        if row["material_status"] == "Available" and (
            row["issue_review_complete"] != "Yes" or row["four_section_format"] not in {"Yes", "No", "Cannot assess"}
            or row["incidental_unblinding"] not in {"Yes", "No"}
        ):
            raise IntegrityError("Final report review fields incomplete")
        if row["material_status"] == "Unavailable" and row["issue_review_complete"] == "Yes":
            raise IntegrityError("No-report slot cannot be declared error-free")
    seen = set()
    for row in final["issues"]:
        rid = row["report_id"]
        if rid not in report_rows or report_rows[rid]["material_status"] != "Available":
            raise IntegrityError("Final issue has no available source report")
        key = (rid, row["issue_id"])
        if key in seen:
            raise IntegrityError("Repeated final issue group")
        seen.add(key)
        text = (package / "raters/rater1/reports" / f"{rid}.txt").read_bytes().decode("utf-8")
        quote = row["exact_quote"] or ""
        if not row.get("reason") or not row.get("locations") or (quote and quote not in text):
            raise IntegrityError("Final issue needs a supported exact quote, locations and reason")
        control = report_rows[rid]["case_id"].startswith("control_")
        allowed_flags = {"Yes", "No"} if control else {None, "No"}
        if any(row.get(f"{flag}_flag") not in allowed_flags for flag in ("pathology", "normality")):
            raise IntegrityError("Invalid final control-flag scope")
        Issue(row["issue_id"], row["decision"],
              tuple(x.strip() for x in (row["categories"] or "").split(";") if x.strip()), quote,
              tuple(f for f in ("pathology", "normality") if row.get(f"{f}_flag") == "Yes"))
    covered = set()
    evidence = []
    dataset_hash = digest(final)

    def verify_evidence(record):
        path = (submission_file.parent / record["evidence_file"]).resolve()
        if not path.is_relative_to(submission_file.parent) or not path.is_file():
            raise IntegrityError("Human evidence must be inside the submitted evidence folder")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != record["evidence_sha256"]:
            raise IntegrityError("Human evidence hash mismatch")
        evidence.append((str(path.relative_to(submission_file.parent)), content))

    for authority in submission["authorities"]:
        scope = authority["report_ids"]
        if len(set(scope)) != len(scope) or not scope or set(scope) - set(report_rows) or covered.intersection(scope):
            raise IntegrityError("Authority scopes must cover each report exactly once")
        if authority["final_review_sha256"] != dataset_hash:
            raise IntegrityError("Human confirmation does not identify this exact final dataset")
        reviewers = authority["confirmations"]
        kind = authority["kind"]
        if kind == "two_rater_consensus":
            if len(reviewers) != 2 or {r["role"] for r in reviewers} != {"rater1", "rater2"}:
                raise IntegrityError("Consensus requires both named independent raters")
            if any(r["name"] != locked[r["role"]]["reviewer"] for r in reviewers):
                raise IntegrityError("Consensus reviewer identity differs from the locked record")
        elif kind == "third_human_adjudication":
            if len(reviewers) != 1 or reviewers[0]["role"] != "third_reviewer" or not reviewers[0]["name"].strip():
                raise IntegrityError("Named third human adjudicator required")
            if reviewers[0]["name"] in {r["reviewer"] for r in locked.values()}:
                raise IntegrityError("Third reviewer cannot be either independent rater")
            verify_evidence(authority["prior_discussion"])
        else:
            raise IntegrityError("Agent proposals are not human final decisions")
        for reviewer in reviewers:
            if reviewer.get("human_confirmation") is not True or not reviewer.get("confirmation_source"):
                raise IntegrityError("Explicit recorded human confirmation required")
            datetime.fromisoformat(reviewer["confirmed_at"])
            verify_evidence(reviewer)
        covered.update(scope)
    if covered != set(report_rows):
        raise IntegrityError("Some final reports have no documented human authority")
    # Opening this key occurs only after both independent locks and the supplied
    # final human provenance have passed. No model identity is printed.
    key_path = package / "private/answer_key_DO_NOT_SHARE.json"
    if hashlib.sha256(key_path.read_bytes()).hexdigest() != integrity["files_sha256"]["private/answer_key_DO_NOT_SHARE.json"]:
        raise IntegrityError("Private mapping changed")
    mapping = json.loads(key_path.read_text())["mapping"]
    roster = {case: {"group": "control" if case.startswith("control_") else "stroke",
                     "required_ids": [r["requirement_id"] for r in rows]}
              for case, rows in integrity["requirements"].items()}
    models = sorted({m["model_key"] for m in mapping.values()})
    final_rows = assessments_from_review(copy.deepcopy(final), mapping, roster)
    estimates, indices = analyze(roster, models, final_rows)
    independent = {r: assessments_from_review(copy.deepcopy(locked[r]), mapping, roster) for r in locked}
    agreement = independent_agreement(roster, models, independent["rater1"], independent["rater2"])
    sensitivity = {r: analyze(roster, models, rows) for r, rows in independent.items()}
    destination = package / "private/final_consensus"
    destination.mkdir(exist_ok=False)
    (destination / "submitted.json").write_bytes(raw)
    evidence_index = []
    for number, (name, content) in enumerate(evidence):
        filename = f"human_evidence_{number:03d}.bin"
        (destination / filename).write_bytes(content)
        evidence_index.append({"original_relative_path": name, "snapshot_file": filename,
                               "sha256": hashlib.sha256(content).hexdigest()})
    write_once(destination / "final_outcomes.json", estimates)
    write_once(destination / "independent_agreement.json", agreement)
    np.save(destination / "final_resample_indices.npy", indices, allow_pickle=False)
    for rater, (results, matrix) in sensitivity.items():
        write_once(destination / f"{rater}_sensitivity.json", results)
        np.save(destination / f"{rater}_resample_indices.npy", matrix, allow_pickle=False)
    write_once(destination / "review_operations.json", {"final_review": final["review"],
               "independent_review": {r: locked[r]["review"] for r in locked},
               "generation_metadata": mapping,
               "scope": "Restricted export: includes model mapping; never deliver to independent raters"})
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.is_file()}
    write_once(destination / "manifest.json", {"final_review_sha256": dataset_hash, "files_sha256": hashes,
               "human_evidence": evidence_index, "identity_authentication": "Not independently verified by software",
               "automatic_adjudications_created": 0})
    return {"status": "Supplied human final decisions imported", "reports": len(report_rows),
            "final_review_sha256": dataset_hash, "automatic_adjudications_created": 0}
