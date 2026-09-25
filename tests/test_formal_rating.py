"""No real reports, identities, or external model calls are used here."""
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook
from src.eval.formal_analysis import assessments_from_review

from src.eval.formal_rating import (
    build_package, lock_independent_review, require_both_independent_locks,
    sha_bytes, spaced_order,
)


def inputs(n=4):
    requirements, assets, slots = {}, {}, []
    for i in range(n):
        case = f"stroke_Synthetic{i:02d}_P"
        requirements[case] = [{"requirement_id": f"Q{i}", "required_wording": "Describe the displayed synthetic finding.",
                               "components": "AND: direction and reference scope"}]
        assets[case] = {"model_system_prompt.txt": b"SYNTHETIC ONLY", "model_user_prompt.txt": b"SYNTHETIC ONLY"}
        for model in ("SecretModelA", "SecretModelB", "SecretModelC"):
            text = "=Not a formula.\nSynthetic response.\n"
            if i == 0 and model == "SecretModelA":
                text = "As SecretModelA, I cannot complete this request."
            if i == 0 and model == "SecretModelB":
                text = None
            if i == 0 and model == "SecretModelC":
                text = "Truncated synthetic response ending in"
            slots.append({"slot_id": f"{case}_{model}", "case_id": case, "model_key": model,
                          "report_text": text, "terminal_status": "captured" if text else "empty",
                          "source_sha256": sha_bytes(str((case, model, text)).encode())})
    return slots, requirements, assets, {"RUBRIC.md": b"SYNTHETIC test rubric"}


def package(tmp_path):
    root = tmp_path / "packet"
    build_package(root, *inputs())
    return root


def completed_return(root, rater, destination):
    book = load_workbook(root / "raters" / rater / "Independent_ratings.xlsx")
    book["Instructions"].cell(15, 2, "SYNTHETIC reviewer fixture")
    book["Instructions"].cell(16, 2, "2026-09-18")
    book["Instructions"].cell(17, 2, "Yes")
    unavailable = set()
    for row in book["Review"].iter_rows(min_row=2):
        if row[2].value == "Unavailable":
            unavailable.add(row[0].value)
            row[3].value, row[4].value, row[7].value = "Unavailable", "No", "No text was returned."
        else:
            row[3].value, row[4].value, row[5].value, row[6].value = "Completed", "Yes", "No", "No"
    for row in book["Coverage"].iter_rows(min_row=2):
        row[5].value = "Cannot assess" if row[0].value in unavailable else "Covered"
        row[6].value = "Final"
    book.save(destination)
    return destination


def test_all_slots_verbatim_including_partial_refusal_and_no_report(tmp_path):
    root = package(tmp_path)
    key = json.loads((root / "private/answer_key_DO_NOT_SHARE.json").read_text())
    slot_map = {s["slot_id"]: s for s in inputs()[0]}
    assert len(key["mapping"]) == 12
    for rid, source in key["mapping"].items():
        original = slot_map[source["slot_id"]]["report_text"]
        for rater in ("rater1", "rater2"):
            path = root / "raters" / rater / "reports" / f"{rid}.txt"
            assert path.read_bytes() == original.encode() if original else not path.exists()
    with pytest.raises(FileExistsError):
        build_package(root, *inputs())


def test_independent_orders_spacing_and_public_metadata(tmp_path):
    root = package(tmp_path)
    manifests = [json.loads((root / "raters" / r / "reports.json").read_text()) for r in ("rater1", "rater2")]
    assert manifests[0]["order"] != manifests[1]["order"]
    for manifest in manifests:
        assert len(set(manifest["order"])) == 12
        cases = [manifest["reports"][rid]["case_id"] for rid in manifest["order"]]
        assert all(case not in cases[max(0, i - 2):i] for i, case in enumerate(cases))
        assert set(manifest) == {"reports", "order"}
        assert all(set(r) == {"case_id", "material_status"} for r in manifest["reports"].values())
        assert "SecretModel" not in json.dumps(manifest)
    assert not list((root / "raters").rglob("*key*"))
    assert not list((root / "raters").rglob("*private*"))


@pytest.mark.parametrize("n", [3, 4, 35])
def test_spacing_many_seeds(n):
    cases = {str(i): [f"{i}-{j}" for j in range(3)] for i in range(n)}
    for seed in range(25):
        order = spaced_order(cases, seed)
        labels = [rid.split("-")[0] for rid in order]
        assert len(set(order)) == 3 * n
        assert all(label not in labels[max(0, i - 2):i] for i, label in enumerate(labels))
        assert order == spaced_order(cases, seed)


def test_slots_and_assets_fail_closed(tmp_path):
    slots, requirements, assets, common = inputs()
    with pytest.raises(ValueError, match="planned"):
        build_package(tmp_path / "bad", slots[:-1], requirements, assets, common)
    slots[0]["terminal_status"] = "paused"
    with pytest.raises(ValueError, match="Nonterminal"):
        build_package(tmp_path / "bad", slots, requirements, assets, common)
    slots[0]["terminal_status"] = "captured"
    with pytest.raises(ValueError, match="Unsafe"):
        build_package(tmp_path / "bad", slots, requirements, assets, {"../leak": b"x"})


def test_blank_template_cannot_be_registered_as_completed(tmp_path):
    root = package(tmp_path)
    with pytest.raises(ValueError, match="Reviewer"):
        lock_independent_review(root, "rater1", root / "raters/rater1/Independent_ratings.xlsx")


def test_two_original_reviews_required_and_cannot_overwrite(tmp_path):
    root = package(tmp_path)
    first = completed_return(root, "rater1", tmp_path / "return1.xlsx")
    second = completed_return(root, "rater2", tmp_path / "return2.xlsx")
    lock_independent_review(root, "rater1", first)
    with pytest.raises(ValueError, match="Both independent"):
        require_both_independent_locks(root)
    with pytest.raises(FileExistsError):
        lock_independent_review(root, "rater1", first)
    lock_independent_review(root, "rater2", second)
    locked = require_both_independent_locks(root)
    assert set(locked) == {"rater1", "rater2"}
    # Only the newly created synthetic key is opened, after both fixture locks.
    mapping = json.loads((root / "private/answer_key_DO_NOT_SHARE.json").read_text())["mapping"]
    requirements = inputs()[1]
    roster = {c: {"group": "stroke", "required_ids": [r["requirement_id"] for r in rows]}
              for c, rows in requirements.items()}
    converted = assessments_from_review(locked["rater1"], mapping, roster)
    assert len(converted) == 12 and sum(r.available for r in converted) == 11
    assert all(r.g03.label == "Covered" for r in converted if r.available)
    path = root / "private/independent_locks/rater1/submitted.xlsx"
    path.write_bytes(path.read_bytes() + b"altered")
    with pytest.raises(ValueError, match="altered"):
        require_both_independent_locks(root)


def test_changed_requirement_rejected(tmp_path):
    root = package(tmp_path)
    file = completed_return(root, "rater1", tmp_path / "changed.xlsx")
    book = load_workbook(file)
    book["Coverage"].cell(2, 4, "A new post hoc requirement")
    book.save(file)
    with pytest.raises(ValueError, match="requirement"):
        lock_independent_review(root, "rater1", file)


def test_pending_return_preserved_and_false_quote_rejected(tmp_path):
    root = package(tmp_path)
    file = completed_return(root, "rater1", tmp_path / "pending.xlsx")
    book = load_workbook(file)
    rid = next(row[0].value for row in book["Review"].iter_rows(min_row=2) if row[2].value == "Available")
    quote = (root / "raters/rater1/reports" / f"{rid}.txt").read_text()
    book["Issues"].append([rid, "I001", "Pending adjudication", "E02", quote, "Report body",
                           "Synthetic competing readings", "No", "No"])
    # Quotes beginning with '=' remain literal text.
    book["Issues"].cell(2, 5).data_type = "s"
    book.save(file)
    lock_independent_review(root, "rater1", file)
    normalized = json.loads((root / "private/independent_locks/rater1/normalized.json").read_text())
    assert normalized["issues"][0]["decision"] == "Pending adjudication"
    file2 = completed_return(root, "rater2", tmp_path / "false_quote.xlsx")
    book = load_workbook(file2)
    book["Issues"].append([rid, "I001", "Error", "E02", "A fabricated quote", "Report body", "Reason", "No", "No"])
    book.save(file2)
    with pytest.raises(ValueError, match="exact substring"):
        lock_independent_review(root, "rater2", file2)


def test_metadata_or_formula_corruption_cannot_lock(tmp_path):
    root = package(tmp_path)
    file = completed_return(root, "rater1", tmp_path / "formula.xlsx")
    book = load_workbook(file)
    book["Review"].cell(2, 8, "=1+1")
    book.save(file)
    with pytest.raises(ValueError, match="Formulas"):
        lock_independent_review(root, "rater1", file)
