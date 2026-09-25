"""Three independent human reviews keyed by opaque report IDs, never model keys.

This additive preparation interface does not import the old adjudicator workflow,
open an identity mapping, or turn matching post-feedback labels into consensus.
"""
from itertools import combinations

from .formal_analysis import Assessment, Coverage, Issue, binary_agreement, coverage_agreement, report_metrics

RATERS = ("rater1", "rater2", "rater3")
STAGES = {"original_independent", "post_feedback_individual"}


def validate_review(review, roster):
    if any(r["group"] not in {"stroke", "control"} or not r["required_ids"]
           or len(set(r["required_ids"])) != len(r["required_ids"]) or 'G03' in r["required_ids"]
           for r in roster.values()):
        raise ValueError("Invalid frozen requirement roster")
    if review["rater"] not in RATERS or review["stage"] not in STAGES:
        raise ValueError("Invalid rater or review stage")
    reports = {r["report_id"]: r for r in review["review"]}
    if len(reports) != len(review["review"]) or not reports:
        raise ValueError("Duplicate or empty report roster")
    if any(r["case_id"] not in roster for r in reports.values()):
        raise ValueError("Unknown case")
    if any(r["material_status"] not in {"Available", "Unavailable"}
           or r["issue_review_complete"] not in {"Yes", "No", None} for r in reports.values()):
        raise ValueError("Invalid review completion or availability")
    coverage = {}
    for row in review["coverage"]:
        rid, req = row["report_id"], row["requirement_id"]
        if rid not in reports or row["case_id"] != reports[rid]["case_id"] or (rid, req) in coverage:
            raise ValueError("Coverage identity mismatch or duplicate")
        if row["adjudication_status"] not in {"Final", "Pending", None}:
            raise ValueError("Unknown coverage status")
        coverage[rid, req] = Coverage(row["decision"], row["adjudication_status"] != "Final")
    expected = {(rid, req) for rid, r in reports.items()
                for req in (*roster[r["case_id"]]["required_ids"], "G03")}
    if set(coverage) != expected:
        raise ValueError("Frozen coverage membership mismatch")
    issues = {rid: [] for rid in reports}
    seen = set()
    for row in review["issues"]:
        rid, iid = row["report_id"], row["issue_id"]
        if rid not in reports or (rid, iid) in seen:
            raise ValueError("Duplicate or unregistered issue")
        seen.add((rid, iid))
        cohort = roster[reports[rid]["case_id"]]["group"]
        flags = [row.get(f"{flag}_flag") for flag in ("pathology", "normality")]
        if any(v not in {"Yes", "No", None} for v in flags):
            raise ValueError("Invalid control annotation")
        if cohort != "control" and "Yes" in flags:
            raise ValueError("Control flag applied to stroke")
        item = Issue(iid, row["decision"],
                     tuple(v.strip() for v in (row["categories"] or "").split(";") if v.strip()),
                     row["exact_quote"] or "",
                     tuple(f for f in ("pathology", "normality") if row.get(f"{f}_flag") == "Yes"))
        issues[rid].append(item)
    return reports, coverage, issues


def blinded_report_metrics(review, roster):
    """Per-reviewer metrics; retain unknown annotations instead of converting to No."""
    reports, coverage, issues = validate_review(review, roster)
    output = {}
    for rid, r in reports.items():
        case = r["case_id"]
        info = roster[case]
        if info["group"] not in {"stroke", "control"}:
            raise ValueError("Unknown cohort")
        available = r["material_status"] == "Available"
        if not available:
            if issues[rid] or any(coverage[rid, req].final for req in (*info["required_ids"], "G03")):
                raise ValueError("Unavailable report has content ratings")
            assessment = Assessment(case, rid, False)
        else:
            assessment = Assessment(case, rid, True,
                                    {req: coverage[rid, req] for req in info["required_ids"]},
                                    coverage[rid, "G03"], r["issue_review_complete"] == "Yes",
                                    tuple(issues[rid]))
        result = report_metrics(assessment, info["required_ids"], info["group"])
        if info["group"] == "control":
            rows = [i for i in review["issues"] if i["report_id"] == rid
                    and i["decision"] in {"Error", "Pending adjudication"}]
            for flag in ("pathology", "normality"):
                key = flag + "_flag"
                positive = any(i["decision"] == "Error" and i.get(key) == "Yes" for i in rows)
                uncertain = any(i.get(key) is None or
                                (i["decision"] == "Pending adjudication" and i.get(key) == "Yes")
                                for i in rows)
                result["control_flags"][flag] = True if positive else (
                    False if available and assessment.issue_review_complete and not uncertain else None)
        output[rid] = {"case_id": case, "cohort": info["group"], **result}
    return output


def pairwise_blinded_agreement(reviews, roster):
    """Original R1/R2 analysis plus separately labeled R1/R3 and R2/R3 summaries.

    Uses exact report IDs, with no linkage of reports to common model identities.
    The additional pairs are descriptive proposals, not a new inferential family.
    """
    if set(reviews) != set(RATERS):
        raise ValueError("Require exactly three independent raters")
    parsed, metrics = {}, {}
    for who, review in reviews.items():
        if review["rater"] != who or review["stage"] != "original_independent":
            raise ValueError("Agreement requires original independent reviews")
        parsed[who] = validate_review(review, roster)
        metrics[who] = blinded_report_metrics(review, roster)
    reference = {rid: r["case_id"] for rid, r in parsed['rater1'][0].items()}
    if any({rid: r["case_id"] for rid, r in parsed[who][0].items()} != reference for who in RATERS):
        raise ValueError("Independent report rosters differ")
    results = {}
    for left, right in combinations(RATERS, 2):
        pair = {}
        for cohort in ("stroke", "control"):
            ids = {rid for rid, case in reference.items() if roster[case]["group"] == cohort}
            domain_rows = {"case_requirements": [], "G03": [], "any_error": []}
            for who in (left, right):
                reports, coverage, _ = parsed[who]
                domain_rows['case_requirements'].append({key: value for key, value in coverage.items()
                                                         if key[0] in ids and key[1] != 'G03'})
                domain_rows['G03'].append({key: value for key, value in coverage.items()
                                          if key[0] in ids and key[1] == 'G03'})
                domain_rows['any_error'].append({rid: metrics[who][rid]['any_error']
                                                if reports[rid]['issue_review_complete'] == 'Yes' else None
                                                for rid in ids})
            pair[cohort] = {"case_requirements": coverage_agreement(*domain_rows['case_requirements']),
                            "G03": coverage_agreement(*domain_rows['G03']),
                            "any_error": binary_agreement(*domain_rows['any_error'])}
        results[f'{left}__{right}'] = {"role": "originally_planned" if (left, right) == RATERS[:2]
                                     else "supplementary_proposal", "cohorts": pair}
    return results
