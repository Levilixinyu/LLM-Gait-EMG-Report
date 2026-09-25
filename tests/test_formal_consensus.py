"""Human provenance schema checks with explicitly synthetic evidence only."""
import copy
import json

import pytest

from src.eval.formal_consensus import import_final_consensus
from src.eval.formal_rating import lock_independent_review, require_both_independent_locks, sha_bytes
from src.llm.formal_generation import IntegrityError, digest
from tests.test_formal_rating import package, completed_return


def setup_submission(tmp_path):
    root = package(tmp_path)
    for rater in ("rater1", "rater2"):
        returned = completed_return(root, rater, tmp_path / f"{rater}.xlsx")
        lock_independent_review(root, rater, returned)
    locked = require_both_independent_locks(root)
    final = copy.deepcopy(locked["rater1"])
    for row in final["coverage"]:
        if row["decision"] == "Cannot assess":
            row["evidence_and_reason"] = "SYNTHETIC missing-output fixture"
    evidence = tmp_path / "SYNTHETIC_confirmation.txt"
    evidence.write_text("SYNTHETIC automated test fixture. No human has reviewed or signed this test.")
    confirmations = [{"role": r, "name": locked[r]["reviewer"], "confirmed_at": "2026-09-18",
                      "human_confirmation": True, "confirmation_source": "SYNTHETIC software fixture only",
                      "evidence_file": evidence.name, "evidence_sha256": sha_bytes(evidence.read_bytes())}
                     for r in ("rater1", "rater2")]
    data = {"independent_submission_sha256": {
        r: json.loads((root / "private/independent_locks" / r / "lock.json").read_text())["submitted_sha256"]
        for r in locked}, "final_review": final,
        "authorities": [{"kind": "two_rater_consensus", "report_ids": [r["report_id"] for r in final["review"]],
                         "final_review_sha256": digest(final), "confirmations": confirmations}]}
    path = tmp_path / "final_SYNTHETIC.json"
    path.write_text(json.dumps(data))
    return root, path, data


def test_supplied_final_dataset_preserves_originals_and_stores_resampling(tmp_path):
    root, path, data = setup_submission(tmp_path)
    original = (root / "private/independent_locks/rater1/submitted.xlsx").read_bytes()
    result = import_final_consensus(root, path)
    assert result["reports"] == 12 and result["automatic_adjudications_created"] == 0
    assert (root / "private/independent_locks/rater1/submitted.xlsx").read_bytes() == original
    final = root / "private/final_consensus"
    assert (final / "final_resample_indices.npy").exists()
    assert (final / "rater2_sensitivity.json").exists()
    assert (final / "independent_agreement.json").exists()
    with pytest.raises(FileExistsError):
        import_final_consensus(root, path)


@pytest.mark.parametrize("mutation,match", [
    ("agent", "Agent proposals"), ("one_rater", "both named"),
    ("hash", "exact final dataset"), ("scope", "no documented"),
    ("independent", "different independent"), ("membership", "membership"),
    ("evidence", "evidence hash"),
])
def test_missing_or_changed_human_provenance_rejected(tmp_path, mutation, match):
    root, path, data = setup_submission(tmp_path)
    authority = data["authorities"][0]
    if mutation == "agent": authority["kind"] = "agent_suggestion"
    elif mutation == "one_rater": authority["confirmations"].pop()
    elif mutation == "hash": authority["final_review_sha256"] = "0" * 64
    elif mutation == "scope": authority["report_ids"].pop()
    elif mutation == "independent": data["independent_submission_sha256"]["rater1"] = "0" * 64
    elif mutation == "membership": data["final_review"]["coverage"].pop()
    elif mutation == "evidence": authority["confirmations"][0]["evidence_sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(IntegrityError, match=match):
        import_final_consensus(root, path)
    assert not (root / "private/final_consensus").exists()


def test_named_third_human_requires_prior_discussion(tmp_path):
    root, path, data = setup_submission(tmp_path)
    authority = data["authorities"][0]
    authority["kind"] = "third_human_adjudication"
    authority["confirmations"] = [dict(authority["confirmations"][0], role="third_reviewer", name="SYNTHETIC third reviewer")]
    authority["prior_discussion"] = {"evidence_file": "SYNTHETIC_confirmation.txt", "evidence_sha256": "bad"}
    path.write_text(json.dumps(data))
    with pytest.raises(IntegrityError, match="evidence hash"):
        import_final_consensus(root, path)
    authority["prior_discussion"]["evidence_sha256"] = authority["confirmations"][0]["evidence_sha256"]
    path.write_text(json.dumps(data))
    assert import_final_consensus(root, path)["reports"] == 12
