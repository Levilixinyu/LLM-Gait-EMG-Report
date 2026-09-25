# Prospective scoring rubric draft

Version: `rubric-v1-draft-for-limited-evidence-v3.1`

Status: agent-prepared draft for expert confirmation. The interpretation instructions have been approved; this scoring rubric has not. Nothing here rescored the completed trial or authorized a generation batch.

## 1. Review only what the model received

Use the report's exact saved system/user input and the approved prompt version `limited-evidence-v3.1-candidate`. Confirm report completeness, input correspondence and version before rating. An incomplete or mismatched material package is an administrative problem: mark Cannot assess and obtain the correct package. Do not convert missing materials into report errors or assume a blank form means no errors.

Plots, precise supplementary percentiles, source arrays and clinical knowledge can help experts understand limits, but their absence from a text-only report is not an omission. These five cases are development-exposed illustrations. Their requirement list cannot be applied unchanged to other patients or treated as a held-out sample.

## 2. Two records, not one combined score

**Coverage** asks whether the report conveyed a required case finding or limitation. **Errors** ask whether it made a false or unsupported assertion. Assess both across the whole report, not by expected paragraph position or a keyword checklist.

A correctly described finding followed by an unsupported causal interpretation can have full coverage and an error. If a required direction is itself wrong or absent, that component is not correctly conveyed; record the incomplete coverage and the false assertion separately. These are separate outcomes, not two numerical deductions to be added together.

No severity weights, total score, 0.5 partial-credit rule or error-rate denominator is proposed as approved. The analysis plan must address these questions separately.

## 3. Coverage decisions

| Decision | Operational meaning |
|---|---|
| Covered | Every applicable core component is conveyed, using any clinically equivalent wording or the explicitly allowed alternative route. |
| Partially covered | A meaningful subset is conveyed, but at least one required component is missing or incorrectly conveyed. Identify it in the rationale. |
| Not covered | No required core meaning is conveyed; an unrelated statement or a generic caveat is insufficient. |
| Cannot assess | Administrative state: the necessary report/input materials are incomplete, mismatched or unreadable. Do not use this to represent appropriate clinical uncertainty in a valid report. |

**AND:** all specified components are needed. **OR:** one complete permitted route is enough. **Conditional:** require the additional statement only when its stated condition applies. A conditional branch that is not triggered does not create an omission. Blank remains unfinished.

For Sub09 C04, ST and VL are both required, but either muscle may be described through its numerical-deviation route or its broad boundary-spanning threshold-interval route. Do not require both routes or every segment. For control Sub49 C06, group provenance and self-exclusion are core; missing speed/cadence and index applicability need explicit handling if those domains are discussed, not as a compulsory inventory in every report.

## 4. Common requirement G03: review once, apply per report

Convey **both** a meaningful limitation of reference comparability **and** why that comparison cannot establish a disease effect or clinical diagnosis. For controls, the comparison must not establish disease or overall normality. Once per report is sufficient; the two meanings may be distributed across sections.

An explicit inability to separate slow-walking and stroke effects can communicate both meanings. Unknown control speed can establish inability to assess speed matching. Age and speed do not each have to appear as keywords. The words pooled, healthy reference or a list of speed limits alone do not establish the required meanings.

Proposed scope for these five reference-bearing tasks: G03 is a required report-level item. A report that avoids all comparisons does not gain an automatic exemption. Experts should explicitly confirm this applicability rule under P03.

C01 separately assesses the actual case speed and its relation to reference support. Do not copy a G03 judgment automatically into C01. One sentence can support both items; no repeated caveat is required, and the disease-attribution caveat is not given a second standalone omission penalty inside C01. This clarified division of requirements needs prospective confirmation.

## 5. Appropriate uncertainty and displayed precision

An appropriately qualified indeterminate conclusion is not an error or automatic partial coverage. When a requirement asks for a factual finding, however, report the supported finding as well. “ST and VL are above the reference mean, but their muscle-specific percentile classification is indeterminate from the supplied endpoints” can satisfy Sub09 C04. “Nothing can be determined” without those findings cannot.

The 3.65–4.61 span supplies endpoint information, not every muscle's exact percentile. A muscle whose max |z| falls between those endpoints may remain unclassified relative to its own percentile. Clinical normality is a separate question: even a supplied percentile comparison does not establish disease or normal function. Do not require the model to reproduce expert-only percentiles.

Descriptive comparisons with visible values remain allowed: Sub50 ST 4.7 is above the largest supplied endpoint 4.61. Sub05 TA 4.6 versus 4.61 supports only a displayed-number comparison, not a conclusion about hidden full precision or clinical normality. Control GPS-like comparisons must preserve the difference between the actual LOO reference and pooled background distributions.

Judge against the precision supplied to the model. Exact string copying is not required; faithful rounding, paraphrases and approximately stated locations are acceptable when they preserve the finding. No new universal numeric tolerance is silently introduced. If a discrepancy matters or its acceptability is uncertain, record the numbers and refer it for discussion.

## 6. Required versus optional content

The [case annex](CASE_REQUIREMENTS.md) contains 20 proposed case-specific requirements, plus common G03 applied once to each report: 25 report-by-requirement rows for one report per development case. This is a checklist structure, not a sample-size claim or 25 independent observations.

CCI comparisons, cadence, every interval, all formulas, audit counts and anatomical explanations are optional unless an explicit case item says otherwise. Omission has no separate penalty, but incorrect optional assertions are still checked. A 100% threshold-coverage finding is not universally mandatory merely because an expert used it as an example. Preserve the specific required-core/optional distinctions.

The four-section format is an output instruction, not four equally weighted content scores. Record an actual format failure separately. Sub47 can satisfy its EMG section with a concise unavailability statement; it need not invent findings to fill space. Clinical follow-up questions may be open questions rather than presupposed diagnoses.

## 7. Interpretation boundaries to check

Use the error-definition sheet and [examples](EXAMPLES.md). Tags are a draft organizational taxonomy, not a validated severity scale.

- Threshold intervals, coverage and amplitude describe the supplied mean envelope under its processing. They do not establish physiological onset/duration, strength, force or stride variability. The 3% criterion removes short above-threshold runs, not short below-threshold gaps. Rounded 100% coverage is not proof that every sample was above threshold.
- The initial-contact anchor supplied in v3.1 may be named. Stroke endpoints are successive contacts of the analyzed limb; the healthy curve is a documented pooled initial-contact-aligned cycle, not a named limb's event trace. Anatomical muscle actions are allowed. Toe-off, stance/swing boundaries and phase-specific muscle functions remain unsupported here.
- Maximum-|z| location is not necessarily the amplitude peak or an event. Above/below reference describes the phase-specific mean at that location, not a percentile boundary.
- CCI may be compared with its supplied empirical interval. It cannot establish physiological normal co-activation, pathology, stiffness, force or simultaneous activation time. No external-method threshold substitution. This prospective boundary does not reopen Q055.
- GVS, ROM and GPS-like do not by themselves establish unseen waveform direction, restricted movement, cause or whole-pattern normality. Speed-band labels do not establish actual independence, safety or community participation.
- Missing data do not mean normality or absence of activity. The paretic/non-paretic index is inapplicable to controls; general left/right symmetry remains a definable measurement.

## 8. Error unit, context and adjudication

Record the exact assertion, report location, supporting input location and a brief explanation. A clinically loaded word is not an automatic error without reading its sentence and context. Open questions do not become measured findings unless their wording presupposes one.

Use **Error**, **Acceptable**, **Pending adjudication**, or **Outside case-error scope** as distinct issue decisions. A candidate issue awaiting discussion is not a confirmed error. Keep the original independent decisions when adjudicating.

One claim repeated about the same case finding is one issue group with multiple locations. Multiple tags do not multiply it. Split a sentence only when it contains independently assessable factual/interpretive claims; link their shared source. Do not aggregate tags or duplicated rater records as independent events. Experts must confirm this proposed unit before it is used prospectively.

Under proposed P07, methodological/design guarantees are recorded as separate design concerns rather than included silently in case-error counts. Format failures are also separate. This follows the historical Q018 scope distinction without endorsing its guarantee. Experts may revise this scope explicitly before scoring; it is not assumed approved.

## 9. Workflow after rubric approval

1. Lock the rubric version and input hashes; prepare case-specific requirements for any new sample before inspecting its generated reports.
2. Deliver complete blinded report/input packages without model identities; record material receipt, version checks and review time.
3. Each rater independently completes coverage, issues and completion status. Record either completed with issues or completed with no issues, not a blank issue table alone.
4. Preserve initial ratings; collect explanations and discuss only after independent completion. Keep unresolved cases pending. Do not represent agent recommendations as independent human adjudication.
5. Use an approved analysis specification that handles paired cases, crossed raters, missing assessments and dependence. This draft supplies neither statistical weights nor a formal sample size.

## 10. What experts are asked to approve now

In `Expert_rubric_review.xlsx`, confirm P01–P08 once, then review the 20 case-specific rows. Common G03 is reviewed under P04, with its applicability under P03, rather than repeated five times. The CSV/JSON retain all 25 application rows for traceability. Read the error definitions and examples, and record any objections before completing the overall decision.

Prompt approval does not imply rubric approval. Any revision to model-visible inputs requires its own version and recorded review scope. No model reports were generated to prepare this draft.
