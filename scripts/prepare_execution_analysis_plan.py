"""Build the prospective plan review package; never call model APIs."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/formal_study/execution_analysis_v1_draft"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def build():
    if (OUT / "plan.json").exists():
        raise FileExistsError("Preserve the existing review package; create a documented new version.")
    selected_path = ROOT / "docs/formal_study/control_supplement_v2/selected_study_cases.csv"
    requirements_path = ROOT / "docs/formal_study/case_requirements_v1/case_requirements.csv"
    reviewed_manifest_path = ROOT / "docs/formal_study/case_review_v1/manifest.json"
    selected = list(csv.DictReader(selected_path.open()))
    req = list(csv.DictReader(requirements_path.open()))
    included = [r for r in req if r["included"] == "Yes"]
    counts = Counter(r["case_id"] for r in included)
    assert len(selected) == 35 and len(included) == 149 and len(req) == 213
    cases = read_json(reviewed_manifest_path)["cases"]
    selected_cases = {f"{r['group']}_{r['subject']}_{r['side']}" for r in selected}
    assert selected_cases == set(counts) == {r["case_id"] for r in cases}
    assert Counter(r["group"] for r in selected) == {"stroke": 25, "control": 10}
    sources = [selected_path, requirements_path, reviewed_manifest_path,
               ROOT / "docs/formal_study/case_requirements_v1/manifest.json",
               ROOT / "docs/formal_study/case_requirements_v1/summary.json",
               ROOT / "docs/formal_study/rubric_v2_draft/rubric.json",
               ROOT / "docs/formal_study/rubric_v2_draft/APPROVAL_RECORD.json",
               ROOT / "docs/formal_study/candidate_v3_1/APPROVAL_RECORD.json",
               ROOT / "scripts/run_five_case_trial.py", ROOT / "src/llm/providers.py",
               ROOT / "src/llm/generation_runner.py"]
    protected = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    registry = []
    for case in cases:
        folder = ROOT / "docs/formal_study/case_review_v1" / case["case_id"]
        checked = []
        for filename in ["model_system_prompt.txt", "model_user_prompt.txt"]:
            p = folder / filename
            expected = case["files_sha256"][filename]
            if p.stat().st_flags & 0x40000000:
                checked.append("Prior reviewed manifest only; local iCloud placeholder")
            else:
                assert sha(p) == expected, str(p)
                checked.append("Current bytes match reviewed manifest")
                protected[str(p.relative_to(ROOT))] = expected
        registry.append(dict(case_id=case["case_id"], group=case["group"], subject_id=case["subject_id"],
            side=case["side"], included_case_requirements=counts[case["case_id"]],
            proposed_G03_rows_per_report=1, planned_model_reports=3,
            model_input_directory=str(folder.relative_to(ROOT)),
            system_sha256=case["files_sha256"]["model_system_prompt.txt"],
            user_sha256=case["files_sha256"]["model_user_prompt.txt"],
            system_verification=checked[0], user_verification=checked[1],
            additional_external_use="No additional use known; user attestation 2026-09-18",
            reference_status="Internal pooled reference" if case["group"] == "stroke" else "Internal reference-used control; leave-one-out comparison"))
    with (OUT / "input_registry.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(registry[0]))
        writer.writeheader(); writer.writerows(registry)
    roster = None
    for node in ast.parse((ROOT / "scripts/run_five_case_trial.py").read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MODELS" for t in node.targets):
            roster = ast.literal_eval(node.value)
    assert roster and len(roster) == 3

    decisions = [
        ("D01", "Study lead", "Primary outcome", "Mean case-specific full-coverage proportion in stroke cases; equal participant weight; no 0.5 partial credit or combined coverage/error score.", "4"),
        ("D02", "Both experts; study lead", "Common G03", "Apply G03 once to all 35 reference-bearing tasks; report it separately from the primary denominator; permit shared evidence with case requirements.", "4"),
        ("D03", "Study lead", "Correctness and other outcomes", "Any confirmed E01-E09 case error and unique issue counts; preserve contradictions; format/design concerns separate; joint fully-covered/G03/error-free outcome secondary only.", "5"),
        ("D04", "Both experts; study lead", "Control semantic flags", "Approve the exact unsupported-pathology and unsupported-overall-normality definitions; flag only confirmed in-scope issues, never group membership or a descriptive deviation alone.", "6"),
        ("D05", "Study lead; statistical reviewer if appointed", "Paired analysis and multiplicity", "Complete three-model stroke case sets; equal-case means and paired differences; 20000 BCa case resamples; descriptive 95% and approximate Bonferroni 98.3333% primary-pair intervals; no confirmatory secondary tests.", "8"),
        ("D06", "Study lead", "Missingness", "Recover administrative material first; no unknown-to-zero conversion or denominator shrinkage; complete-triad analysis plus all-planned-case bounds and explicit delivery accounting.", "9"),
        ("D07", "Both experts; study lead", "Review and adjudication", "Independent blinded reviews, original labels preserved, human resolution of remaining disputes; descriptive agreement from independent labels only.", "7"),
        ("D08", "Study lead; technical operator", "Generation and retries", "One intended response; at most three transient-failure attempts, first usable output retained, no quality/truncation regeneration; persistent attempt ledger, 600-second deadline and controlled backoff.", "10"),
        ("D09", "Study lead; technical operator", "Provider settings", "Review historical local candidate roster and proposed 8000-token budget; verify exact available identifiers and effective settings before freeze. No provider substitution or equal-compute claim.", "10"),
        ("D10", "Both experts", "Capacity", "Each rater reviews up to 105 reports and 552 coverage rows, plus issue review and reconciliation; confirm capacity and enter a realistic schedule.", "3"),
        ("D11", "Study lead; technical operator", "Readiness and release", "Implement offline tested formal runner, exact input hashes, private blinding, persisted retries and analysis checks before the separate batch-generation authorization.", "11-12"),
    ]
    blank_decisions = [dict(decision_id=i, responsible_role=role, topic=topic, proposed_decision=proposal,
                            protocol_section=section, reviewer_decision="", comments_or_revision="",
                            reviewer="", date="") for i, role, topic, proposal, section in decisions]
    exposure = dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(), review_date="2026-09-18",
        source="User response in the active conversation to the explicit 25-stroke/10-control external-use question",
        attestation_english="I have checked; there was no additional use.",
        language_provenance="English translation of the user's Chinese response. The original remains in the conversation; this record is not a new signature or a separately authenticated source document.",
        applies_to_cases=sorted(selected_cases), selected_case_file_sha256=sha(selected_path),
        interpretation="No additional known use outside the registered project history. Existing reference/calibration use and current case-card/requirement development remain disclosed.",
        limitations="User attestation of known history, not independent exhaustive verification. Does not approve this protocol or authorize generation.",
        membership_change=False, exclusions=[], replacements=[])
    write_json(OUT / "exposure_confirmation.json", exposure)
    plan = dict(version="execution-analysis-v1-draft", status="Pending prospective plan review",
        cases=35, stroke_cases=25, control_cases=10, planned_report_slots=105,
        raters=2, report_assignments=210, included_case_requirements=149,
        proposed_G03_applications=35, coverage_rows_per_rater=552, coverage_rows_total=1104,
        primary=dict(name="Stroke case-specific full-coverage proportion", participant_equal_weight=True,
                     denominator="All included case requirements for that participant; common G03 separate",
                     partial_credit=None, contrast="Mean within-case difference", missing="Complete triads plus all-planned-case bounds"),
        analysis=dict(method="Paired participant BCa bootstrap", resamples=20000, seed=20260918,
                      primary_pairwise_contrasts=3, descriptive_confidence=0.95,
                      adjusted_primary_confidence=1-0.05/3, secondary_inference="Exploratory",
                      binary_interval="Clopper-Pearson, 95% two-sided; zero-control-event bound also 95% one-sided"),
        generation=dict(candidate_models=[dict(provider=p, model=m, verification="Historical local configuration only; runtime availability/settings pending") for p,m in roster],
                        proposed_output_token_budget=8000, max_transmitted_attempts=3,
                        attempt_deadline_seconds=600, backoff_seconds=[5,30], retry_after_pause_threshold_seconds=300,
                        allow_content_regeneration=False, allow_truncation_regeneration=False,
                        sdk_retry_policy="Disable or make every hidden request visible in the shared attempt budget"),
        exposure_status="User confirmed no additional known use for all 35 selected cases",
        plan_approved=False, clinical_operational_items_approved=False,
        provider_configuration_frozen=False, generation_authorized=False, model_calls=0,
        decisions=blank_decisions)
    write_json(OUT / "plan.json", plan)
    book = Workbook(); book.remove(book.active)
    instructions = [dict(topic="Status", instruction="Review of a proposed execution/analysis plan; no API generation. Finalized case requirements and prior reviews remain unchanged."),
                    dict(topic="Complete", instruction="Read PROTOCOL.md. Complete only decisions within your role and identify the reviewer. Save a separate copy per reviewer. Do not sign for another person."),
                    dict(topic="Expert focus", instruction="Experts focus on D02, D04, D07 and D10; the study lead owns statistical/operational choices and can request statistical review."),
                    dict(topic="Overall", instruction="Complete Overall review and capacity if applicable. Accepting the plan is not the later concrete batch authorization."),
                    dict(topic="Exposure", instruction="The Exposure review sheet records the user's known-history attestation for all 35 cases; it is not an expert signature or an external-validation claim.")]
    capacities = [dict(reviewer=r, report_assignments=105, coverage_judgments=552, capacity_confirmed="", planned_start="", planned_completion="", comments="") for r in ["rater1","rater2"]]
    exposure_rows = [dict(case_id=case, history_status="No additional use known", recorded_from="User confirmation in conversation", date="2026-09-18", additional_details="Registered case-card/review and reference-calibration uses remain disclosed.") for case in sorted(selected_cases)]
    overall = [dict(reviewer_role=role, reviewer="", overall_decision="", scope_approved_or_exceptions="", date="") for role in ["Study lead", "rater1", "rater2"]]
    for title, rows in [("Read first",instructions),("Plan decisions",blank_decisions),("Capacity",capacities),("Exposure review",exposure_rows),("Overall review",overall)]:
        ws=book.create_sheet(title); ws.append(list(rows[0]))
        for row in rows:ws.append(list(row.values()))
        ws.freeze_panes="C2";ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color="FFFFFF");c.fill=PatternFill("solid",fgColor="24476B")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(70,max(18,max(len(str(c.value or "")) for c in col)+2))
            for c in col:c.alignment=Alignment(wrap_text=True,vertical="top")
        for row in range(2,ws.max_row+1):ws.row_dimensions[row].height=115 if title!="Exposure review" else 55
        if title=="Plan decisions":
            dv=DataValidation(type="list",formula1='"Accept,Revise,Outside my review scope"',allow_blank=True);dv.showErrorMessage=True;ws.add_data_validation(dv);dv.add(f"F2:F{ws.max_row}")
            for row in ws.iter_rows(min_row=2,min_col=6):
                for c in row:c.fill=PatternFill("solid",fgColor="E8F1FA")
    book.save(OUT/"Study_plan_review.xlsx")
    assert all(sha(ROOT/rel)==h for rel,h in protected.items())
    write_json(OUT/"manifest.json",dict(created_at_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__)),
        source_sha256=protected,output_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!="manifest.json"}))
    print(json.dumps({k:v for k,v in plan.items() if k not in ["decisions","primary","analysis","generation"]},indent=2))


if __name__=="__main__":
    build()
