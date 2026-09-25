# Prospective rubric draft for expert review

Version: `rubric-v1-draft-for-limited-evidence-v3.1`

Status: **DRAFT — expert confirmation pending.** The underlying v3.1 interpretation instructions were approved by both experts; this does not approve the scoring rules proposed here. No model calls or new report ratings were made.

## Send these materials to each expert

1. [RUBRIC.md](RUBRIC.md): common rules, coverage categories, uncertainty, error handling and review scope.
2. [CASE_REQUIREMENTS.md](CASE_REQUIREMENTS.md): 20 case-specific proposed requirements; common G03 is reviewed once in the rubric.
3. [EXAMPLES.md](EXAMPLES.md): 24 newly authored teaching examples, not actual model outputs or new expert decisions.
4. [Expert_rubric_review.xlsx](Expert_rubric_review.xlsx): editable confirmation workbook with dropdowns and comment fields. Each expert returns a separately named copy.

The workbook contains eight policy decisions, the 20 case-specific rows, nine candidate error categories, the examples and proposed fields for later independent rating. Fill reviewer/date and overall decision on Read first. Review P01–P08 before the case rows. Choose Accept, Revise or Unable to confirm; explain revisions. Do not enter report ratings here. Approval fields are intentionally blank.

The common G03 item applies once per report. Together with the 20 case-specific requirements, it yields 25 application rows for one report per each of the five development cases. These counts are not a formal sample size, and repeated reports/items are not independent subjects.

## Choices needing explicit confirmation

- Retain the existing required-versus-optional distinction, especially optional CCI and non-compulsory audit/method counts.
- Confirm the proposed minimum semantic core, AND/OR routes and conditional Sub49 missing-information statements. Exact reproduction of every number is not required.
- Apply the substantive G03 rule to these five reference-bearing tasks and keep case-specific C01 separate without a repeated disease-attribution omission penalty.
- Credit supported indeterminate conclusions while still requiring available case findings.
- Keep coverage separate from correctness, with no implicit combined deduction or partial-credit weight.
- Confirm issue grouping and the proposed separation of case assertions from methodology/design and format concerns. This scope is a proposal, not a silent carry-over of approval.

## Sources and version boundaries

Historical required-core candidates were traced to `docs/expert_trial/expert_rate/trial_2026-09-17_v1/frozen/confirmed_checklist.xlsx`, sheet Scoring tiers and traceability, plus the final trial summary and agreed G03 interpretation. Original checklist source IDs are retained; they are not the similarly named machine-draft items in the regenerated cards.

Current interpretation boundaries come from [the approved v3.1 record](../candidate_v3_1/APPROVAL_STATUS.md) and [the exact five-case inputs](../../expert_trial/data_cards_v7_candidate/index.html). No expert-only quantitative reference was promoted into mandatory model content. New scoring semantics in this draft require expert review even where the historical core was already agreed.

The machine-readable `rubric.json` and `case_requirements.csv` carry the same draft content; they are not expert submissions. Source and output hashes, consistency checks and preservation results are in [manifest.json](manifest.json). The earlier inputs, expert submissions and historical ratings remain unchanged.

## Next after confirmation

Resolve any returned wording disagreements in a new rubric version, obtain confirmation and freeze it. Prepare the exposure-aware sample and its case requirements before inspecting new model outputs. The Sub43 event flag remains a separate eligibility check. Approve the analysis, blinding and generation plan before any formal batch. This package neither sets outcome weights nor chooses a formal sample size.
