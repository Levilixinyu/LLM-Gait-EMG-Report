# Completeness and evidence fidelity of large language model gait reports: a paired evaluation of 25 stroke cases with a 10-control supplement

Working manuscript draft for author review. Numerical results are drawn from preserved analysis records. Bracketed author-confirmation fields must be completed before submission. This document does not assert prospective registration, institutional ethical exemption, unconfirmed reviewer credentials or a new expert consensus.

## Abstract

**Objective:** Compare required-content coverage and evidence fidelity of three language-model configurations interpreting structured stroke gait summaries, with a separate healthy-control supplement.

**Methods:** Twenty-five stroke participants and 10 controls from a public motion-capture/EMG dataset each contributed one report per configuration, giving 105 saved reports. Three human experts independently rated original reports; later clarifications, personal rechecks and discussion were retained as separate stages. The principal analysis used the frozen post-feedback layer. Full coverage was the participant-weighted proportion of case requirements marked Covered. Paired stroke contrasts used 20,000 BCa resamples. Confirmed errors, Pending states, original agreement and later targeted sensitivity were reported separately.

**Results:** Stroke full coverage was 98.2% for Claude, 97.0% for GPT and 81.8% for Gemini. Family-adjusted intervals excluded zero for Claude-Gemini and GPT-Gemini, but not Claude-GPT. Confirmed errors occurred in 11/22, 2/25 and 12/23 evaluable stroke reports, respectively; remaining reports retained unknown status. Original ratings differed from the frozen layer, particularly for error judgments and Gemini coverage. Control error counts were 6/9, 0/10 and 8/10; a later pathology annotation remained disputed. Targeted wording overlays changed Gemini stroke error counts to 10-12 of 25 planned reports without changing coverage.

**Conclusion:** Coverage and fidelity were distinct in this selected interpretation task. Findings depend on saved outputs and the rating stage, and do not establish diagnostic performance, clinical benefit, equivalence or general model superiority.

## Introduction

The public gait dataset used here combines kinematics and surface EMG collected under a common protocol in able-bodied adults and stroke survivors. Its authors emphasize age and sex comparability and the limitation of recordings collected only at self-selected speeds. These constraints matter when converting numerical departures from a pooled reference into prose: a measured difference does not by itself establish its cause or functional significance. [Dataset publication](https://www.nature.com/articles/s41597-023-02767-y).

For this study, the intended role of a language model was to organize supplied findings into a reviewable narrative. We treated inclusion of required findings and avoidance of unsupported claims as separate properties. A fluent report might omit a principal difference, while a comprehensive report might introduce an incorrect comparison or an unsupported explanation. The evaluation therefore needed explicit case requirements, source-linked error records and a way to retain unresolved interpretations.

Reporting guidance such as CHART addresses model identification, prompts, query strategy, performance evaluation and analysis in studies of chatbot-generated clinical evidence or advice. Its emphasis on transparency informs the present description of saved configurations, review procedures and workflow amendments; no completed reporting-checklist compliance claim is made here. [CHART explanation and elaboration](https://www.bmj.com/content/390/bmj-2024-083305).

We compared three saved configurations on the same participant inputs, with stroke coverage as the primary endpoint. A smaller control supplement examined evidence fidelity when cohort membership was disclosed. Original independent judgments, subsequent review and post-unblinding sensitivity were retained separately to show how interpretation choices affected the results.

## Methods

### Study design and data source

We conducted a within-participant comparison of three saved model configurations on a constrained gait-report interpretation task. The principal cohort comprised 25 stroke participants; 10 healthy controls formed a separate exploratory supplement. The task was to describe the supplied evidence faithfully and express its limits, rather than diagnose disease, recommend treatment or interpret raw recordings independently. Each participant contributed one report per configuration, yielding 105 reports. Model outputs and repeated ratings did not increase the independent participant count.

Data originated from the public dataset of Van Criekinge and colleagues, which includes 50 stroke survivors and 138 able-bodied adults and provides motion-capture and surface EMG data in source and postprocessed forms. We used released participant-average curves and verified derived features. The original data-collection study reported informed consent and ethics approvals. The determination applicable to the present secondary analysis remains **[AUTHOR CONFIRMATION REQUIRED: institution, review or exemption determination, and reference number if applicable]**. [Dataset publication](https://www.nature.com/articles/s41597-023-02767-y).

### Case selection and sample size

The stroke cohort was the entire conservative internal eligibility pool of 25 participants. The local inventory began with 50 stroke participants, identified 43 with complete bilateral data, retained 27 with complete data and no prior report in the checked inventory, and excluded two additional individually audited cases. The controls were selected by a single recorded seeded pseudorandom ordering of 98 locally eligible participants, retaining the first 10. Controls were not age- or speed-matched to the stroke cohort. The study lead subsequently confirmed no additional known use outside the recorded project history for the selected participants. This attestation is not an exhaustive audit of all external systems.

Sample size was resource-defined; no power claim for model superiority or equivalence is made. Case-specific requirements for the selected participants were reviewed before formal generation. These were prospectively specified evaluation cases, not untouched external test cases. The controls had contributed to reference or calibration construction; leave-one-out calculations for individual comparisons did not make the control cohort independent external validation. Table 1 describes the retained sample. Age and published bilateral speed are administrative metadata, not additional model inputs; control speed was not supplied to the models. The published bilateral speed is distinct from the analyzed-side speed supplied in stroke prompts.

### Model-visible information and feature definitions

All three configurations received the same saved system/user input pair for a given participant. Stroke inputs described the paretic side; control inputs described the released left/right pooled average. Inputs identified cohort membership. Seven EMG channels and sagittal pelvis, hip, knee and ankle curves were represented on a 1,001-point cycle. Released normalized ensemble-average EMG curves were used without further amplitude normalization. Stroke normalization provenance was checked numerically where evaluable; healthy-side pooling and normalization relied on release documentation and were not numerically revalidated to the same extent.

The summary included relative envelope amplitudes, retained above-threshold intervals, threshold coverage, boundary continuity, maximum absolute phasewise standardized deviation, two whole-cycle overlap indices, sagittal range of motion and reference-deviation scores. Stroke summaries also provided speed, cadence and a successive-footfall step-length index, defined as 200(P-N)/(P+N), where P and N denote paretic and non-paretic step lengths. This index is not the ordinary percentage shortening relative to the other step. Control prompts marked that paretic/non-paretic index as inapplicable and speed/cadence as not supplied.

The EMG threshold was 20% of each supplied mean curve's own peak. A sample was above threshold only when its value exceeded this threshold. Coverage was the proportion of above-threshold samples before interval filtering. Circular above-threshold runs were retained when their sample count met the 3% minimum; on the 1,001-point grid the integer threshold was 30 samples. This filter removes short above-threshold runs, not below-threshold gaps. Wrapped intervals could cross the cycle boundary. Display rounding could obscure small discontinuities; neither rounded 100% coverage nor a displayed 0%-100% retained interval established full-precision continuous exceedance or physiological continuous contraction.

The overlap index was computed as twice the summed pointwise minimum of two normalized envelopes divided by their summed amplitudes over the cycle, for TA/GAS and RF/BF. It was not simultaneous activation duration. Per-channel kinematic deviation was the root-mean-square difference from the reference mean curve; the composite was the root mean square of the four sagittal channel scores and was explicitly labeled GPS-like rather than the validated nine-variable GPS. Maximum absolute z was the maximum across 1,001 phasewise comparisons, not a single-observation z statistic or a clinical abnormality test.

The reference was pooled rather than individually age- or speed-matched. Stroke comparisons used the healthy reference; each control was excluded from its own mean/SD comparison. Pooled calibration summaries remained distinct from leave-one-out individual references. The full reference included 138 participants for kinematics, with effective EMG availability varying by muscle (106-109 before self-exclusion). Supplied empirical percentiles were descriptive and did not establish diagnostic or normality cutoffs. In particular, the supplied span of muscle-specific maximum-|z| percentiles did not reveal every muscle's individual cutoff.

The instructions permitted naming the documented initial-contact boundary, anatomical muscle actions and genuine clinical follow-up questions. They prohibited assigning intermediate gait phases from cycle percentages without events, converting summary metrics into unsupported deficits or diagnoses, or treating an open question as permission to assert an unsupported observed finding. Individual toe-off, matched muscle timing, raw-signal quality and stride variability were outside the input. Models received no plots, expert checklist, reference answers, retrieval tools or prior conversation. Experts could consult the supplied curves and reference materials while respecting this model-visible information boundary.

### Model configuration and generation

We evaluated the recorded identifiers `claude-opus-5`, `gpt-6-astra` and `gemini-3.1-pro-preview`. These identify the saved configurations, not claims about current services or permanently pinned versions. Each had a 16,000-token output allowance with its recorded high/adaptive reasoning configuration (Supplementary Table S1). The allowance and effort labels did not establish equal computational expenditure across providers. Sampling parameters not sent by the adapter remained provider-managed; deterministic generation is not claimed.

Generation used a frozen task manifest, recorded case ordering and balanced provider ordering within case blocks. The batch was executed in three operational stages: 10 stroke participants, another 10 stroke participants, then five stroke participants plus 10 controls. Inputs and settings were unchanged across stages. One retained response was planned per case and model; retries were restricted to specified transport failures without a usable captured report, never poor content. All 105 formal slots completed on 19 September 2026 UTC with no retry, refusal or token-limit finish. Preliminary technical probes were outside the formal 105-report analysis. Responses were retained with generation metadata and verified against captured stream evidence.

### Expert assessment and workflow changes

Three human reviewers independently scored all 105 reports in the original rating round. All three were PhD students at The University of Texas at Austin with at least five years of experience in EMG analysis and neuromuscular control research, as confirmed by the study lead. All scoring judgments were made by the human reviewers themselves. Rater1 and rater2 participated in criteria development; rater3 joined at scoring and did not develop the criteria. Each complete stage comprised 315 report-review assignments and 1,656 coverage judgments, not 315 participants.

The original plan specified two independent reviewers and a third reviewer for unresolved adjudication. The implemented workflow instead added a third complete independent review after the first two submissions and their administrative inspection, while model identities remained concealed. Some blinded outcome counts had already been seen at that decision. This was a documented change after access to outcome-related information, not an original prospective three-rater design. The third reviewer was not treated as a privileged tie-breaker; no coordinator or fourth-reviewer adjudication is asserted.

Review packets used opaque report identifiers, concealed provider metadata, separately randomized reading orders and separated same-case reports. Original prose was preserved rather than paraphrased to conceal style. Reviewers recorded incidental unblinding. Independent submissions were preserved separately from later targeted corrections, discussion and source-linked post-feedback decisions. Administrative material preparation and quotation checks were separate from the experts' scoring. Later discussion and personal rechecks could affect interpretation and were not treated as fresh independent reviews.

Case-specific requirements were fixed before generation: 119 across stroke cases and 30 across controls. Each report had 4-6 stroke requirements or three control requirements. Reviewers used Covered, Partially covered or Not covered, with missing or unresolved assessments recorded separately. A core finding required its specified explanatory content, not only a numerical list. G03 separately assessed meaningful reference-comparability limitations and their implications for disease attribution or diagnosis; one statement could satisfy overlapping requirements without repetition.

Correctness was assessed through distinct report-scoped issue groups under nine categories: misreported facts; unsupported clinical/function inference; threshold/amplitude overinterpretation; unsupported events/phases/functions; invalid reference classification; overlap-index overinterpretation; kinematic-summary overinterpretation; missingness/applicability errors; and unsupported matching/disease attribution. Multiple tags or repeated locations did not multiply a group. Coverage and error judgments remained separate. Interpretive uncertainty could remain Pending; it was neither forced to Error nor cleared by default.

The source-linked blinded outcome dataset was frozen on 23 September 2026 before the authorized model-mapping join. It contained matching coverage judgments, 52 confirmed issue groups and 16 administratively closed but substantively unresolved Pending groups. Different personal category proposals were preserved, without a majority or union category assignment. The protocol's earlier requirement for an E02 co-tag on one form of pathological presupposition was clarified after rating: an explicit qualifying human annotation and confirmed in-scope issue were required, but a simultaneous E02 label was not. This change is reported as post-rating clarification.

The D01-D03 clarification was issued after the original independent submissions. It required interpretation beyond numerical or magnitude-sorted lists and clarified that genuine clinical questions propose possibilities, while wrong facts or explicit unsupported observed premises remain reviewable. These rules were applied in personal rechecks and subsequent discussion. Supplementary Table S4 distinguishes the sequence and the dated records; undated steps are not assigned invented dates. The frozen results are post-feedback outcomes, not unchanged scores from the original independent round.

### Outcomes and analysis

The primary outcome was full coverage of included case requirements: C_im = Covered_im / K_i. Participants were equally weighted, K_i remained fixed across models, partial coverage received no half-credit, and G03 was excluded from K_i. The primary comparison used the same 25 stroke participants with all three coverage scores available. For each model pair, we calculated participant-level percentage-point differences and their mean. We used 20,000 paired BCa resamples, the same saved participant-index matrix for all contrasts and seed 20260918. Descriptive 95% and approximate Bonferroni-adjusted 98.3333% intervals were reported for the three primary contrasts. The implementation preserved paired sampling and reported unavailable intervals without switching methods; these are approximate intervals rather than guaranteed finite-sample bounds. [Paired bootstrap and BCa documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).

Secondary outcomes included any confirmed case error, unique confirmed issue counts, G03 coverage, technical completion and an operational joint-success measure requiring all case requirements and G03 Covered with no confirmed or Pending error after complete review. These were not clinical safety or usefulness endpoints. Any-error was positive if at least one confirmed error existed; otherwise it was negative only after complete review with no Pending issue, and unknown otherwise. Evaluable denominators and all-planned bounds were shown together. Bounds counted unknown states as zero or one and were not confidence intervals. Joint-success point estimates retained the protocol's complete-review denominator, separately from all-planned known/unknown status.

Binary outcomes used exact two-sided 95% binomial intervals on the stated evaluable denominators; their assumptions are limited by selected cases and shared references. The zero-event control result also has a one-sided 95% upper limit of 1-0.05^(1/10), approximately 25.9%. Secondary and control comparisons were exploratory, without additional confirmatory tests or an overall quality ranking. [Exact binomial limits](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).

Original independent agreement was evaluated separately by cohort and domain using raw agreement, three-category coverage cross-tabulations and unweighted Cohen's kappa; report-level any-error used binary states. Pairwise unknown/incomplete observations were excluded with counts disclosed. Rater1-rater2 was the originally planned comparison; the other pairs were supplementary. Kappas were not averaged into a three-rater coefficient. No confidence interval treating all item rows as independent was used. Original independent model-specific outcomes were retained as a sensitivity analysis distinct from post-feedback outcomes.

### Separate healthy-control analysis and later sensitivity

All 30 control reports were analyzed separately. Two nonexclusive annotations captured unsupported pathological/clinical-impairment assertions and unsupported overall-normality/function assertions. Cohort membership, numerical deviation or a genuine clinical question alone did not qualify. Each annotation required its own explicit judgment and a confirmed in-scope issue for a positive endpoint. The annotations were not diagnostic classifications, sensitivity, specificity or clinical false-positive rates. The 30 reports represented 10 correlated case sets, not 30 independent controls.

After analysis-team unblinding, eight wording-sensitive groups underwent targeted personal review. Packets omitted identities, model results and peer positions; all three reviewers declared no model-identity or comparison-result exposure, while earlier discussion exposure remained recorded. Four labels matched as Error, four remained divergent, and one control pathology annotation differed. We preserved the frozen primary results and performed exploratory hybrid overlays substituting only each reviewer's eight latest decisions and one annotation into the shared baseline. Additional scenarios treated the four divergent claims as Pending, Acceptable or Error, with the disputed annotation unknown, negative or positive. Previously Pending groups remained Pending. These scenarios were neither new expert consensus nor full independent-rater estimates.

## Results

### Sample and report completion

The retained sample comprised 25 stroke participants and 10 controls (Table 1). The age distributions differed, with medians of 65.0 and 75.5 years, respectively. Twenty-two selected stroke participants had published bilateral speed below 0.80 m/s; this descriptive count uses administrative source metadata and is not a count derived from rounded prompt values. All 105 reports were captured. Generation records showed normal stream completion for every report, with zero retries, refusals and token-limit finishes. Reviewers recorded all reports as having the requested four-section format and reported no incidental unblinding during the original review; these are declarations and technical observations, not proof of factual correctness.

### Table 1. Retained participant characteristics

| Cohort | Participants | Reports | Age, median (IQR), years | Published bilateral speed, median (IQR), m/s | Published speed below 0.80 m/s |
| --- | --- | --- | --- | --- | --- |
| Stroke | 25 | 75 | 65.0 (58.0-72.0) | 0.348 (0.239-0.566) | 22 |
| Control | 10 | 30 | 75.5 (56.0-82.0) | 1.160 (1.095-1.216) | 0 |

IQR uses the 25th and 75th percentiles with linear interpolation. Administrative age and published bilateral speed were summarized after checking membership against the frozen roster; they were not added to model inputs. Historical planning-status fields in the source metadata were not interpreted as current eligibility or generation status.

### Primary stroke coverage

Mean full coverage was 98.2% for Claude, 97.0% for GPT and 81.8% for Gemini. Claude-Gemini and GPT-Gemini contrasts were positive under the planned family-adjusted interval procedure. The Claude-GPT interval included zero and did not establish either superiority or equivalence (Table 3). No participant was excluded from the complete paired coverage analysis. All G03 judgments in the frozen post-feedback layer were Covered. The denominator comprised case-specific requirements rather than all possible factual assertions.

### Table 2. Frozen coverage and report-level errors, by cohort

| Cohort | Model | Mean full coverage, % | Error reports / evaluable | Unknown | Exact 95% CI, % | All-planned bounds, % | Confirmed groups |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 98.2 | 11/22 | 3 | 28.2 to 71.8 | 44.0 to 56.0 | 17 |
| Stroke | GPT-6-astra | 97.0 | 2/25 | 0 | 1.0 to 26.0 | 8.0 to 8.0 | 2 |
| Stroke | Gemini 3.1 Pro preview | 81.8 | 12/23 | 2 | 30.6 to 73.2 | 48.0 to 56.0 | 13 |
| Control | Claude Opus 5 | 90.0 | 6/9 | 1 | 29.9 to 92.5 | 60.0 to 70.0 | 9 |
| Control | GPT-6-astra | 86.7 | 0/10 | 0 | 0.0 to 30.8 | 0.0 to 0.0 | 0 |
| Control | Gemini 3.1 Pro preview | 73.3 | 8/10 | 0 | 44.4 to 97.5 | 80.0 to 80.0 | 11 |

Coverage is the equally weighted participant mean. Error proportions use the displayed evaluable denominator; unknown reports remain in the all-planned bounds. Confirmed groups are not severity-weighted and are not the number of erroneous reports. Later wording-review alternatives are reported below; this table preserves the historical frozen layer.

### Table 3. Paired stroke coverage contrasts

| Contrast | Difference, percentage points | Descriptive 95% BCa | Family-adjusted 98.3333% BCa |
| --- | --- | --- | --- |
| Claude Opus 5 minus Gemini 3.1 Pro preview | 16.4 | 10.8 to 22.8 | 9.6 to 24.2 |
| Claude Opus 5 minus GPT-6-astra | 1.2 | -1.4 to 5.2 | -1.6 to 6.2 |
| Gemini 3.1 Pro preview minus GPT-6-astra | -15.2 | -20.8 to -10.0 | -22.0 to -9.0 |

All intervals are in percentage points; n=25 paired participants. Gemini minus GPT is the negative form of GPT minus Gemini.

### Stroke errors and joint outcome

In the frozen layer, Claude had confirmed errors in 11/22 evaluable stroke reports, Gemini in 12/23 and GPT in 2/25; three Claude and two Gemini reports were unknown because a Pending issue remained without a confirmed error. The all-planned bounds were 44%-56%, 48%-56% and 8%-8%, respectively. Confirmed issue groups numbered 17, 13 and two. This descriptive pattern was not subjected to a new confirmatory superiority test. Full coverage could coexist with a factual or interpretive error. Supplementary Table S2 reports the joint outcome with its complete-review denominator, which differs from the any-error denominator when a known failure also has unresolved issues.

### Healthy-control reports

The 10 controls contributed all 30 planned reports. Mean full coverage was 90.0% for Claude, 86.7% for GPT and 73.3% for Gemini. Confirmed-error reports numbered 6/9 evaluable for Claude, 0/10 for GPT and 8/10 for Gemini; one Claude report remained unknown. These counts include factual, metric and evidence-boundary violations, not only pathological assertions or diagnoses. No control normality annotation was positive in the frozen data. One Gemini control pathology annotation was positive at freeze, but later personal review produced Yes/No/Yes rather than a matching judgment (Table 4). The other models had no positive pathology annotation. Zero events among 10 controls did not establish absence of risk; the one-sided 95% upper limit was 25.9% under the binomial assumptions.

### Table 4. Control semantic annotations and later disagreement

| Model | Flag | Frozen events / evaluable | Unknown | Exact 95% CI, % | Later review |
| --- | --- | --- | --- | --- | --- |
| Claude Opus 5 | normality | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| Claude Opus 5 | pathology | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| GPT-6-astra | normality | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| GPT-6-astra | pathology | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| Gemini 3.1 Pro preview | normality | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| Gemini 3.1 Pro preview | pathology | 1/10 | 0 | 0.3 to 44.5 | Disputed: Yes / No / Yes; unknown scenario 0/9 with 1 unknown |

For the disputed Gemini pathology annotation, preserving disagreement as unknown gives zero known-positive reports among nine evaluable reports and one unknown, with all-planned bounds 0%-10%. This is not equivalent to 0/10 negative or to a new unanimous positive. Control any-error status remains unchanged in all targeted scenarios because other confirmed errors remain in the affected reports.

### Descriptive report length

Saved blinded report texts were counted by whitespace splitting, including headings and table markup. This post-hoc descriptive measure is not linguistic word segmentation, billable tokens, reasoning length or a measure of quality. Stroke median counts were 2,049 for Claude, 818 for GPT and 761 for Gemini; control medians were 1,992, 803.5 and 712.5 (Supplementary Table S6). No length adjustment or additional significance test was introduced.

### Original independent agreement and stage sensitivity

Original case-requirement agreement for stroke was 95.5%, 94.4% and 95.0% for rater1-rater2, rater1-rater3 and rater2-rater3, respectively; kappas were 0.550, 0.305 and 0.559. Report-level error agreement was less consistent and used different assessable subsets. Controls also showed differences between high raw coverage agreement and modest or variable kappa (Table 5). G03 kappa was often undefined because the included ratings had no category variation. Neither agreement nor kappa established correctness or reviewer quality.

### Table 5. Original independent agreement

| Pair | Cohort | Domain | Assessed / planned | Excluded | Raw agreement, % | Unweighted kappa |
| --- | --- | --- | --- | --- | --- | --- |
| rater1 / rater2 | Stroke | case_requirements | 357/357 | 0 | 95.5 | 0.550 |
| rater1 / rater2 | Stroke | G03 | 75/75 | 0 | 100.0 | Undefined |
| rater1 / rater2 | Stroke | any_error | 65/75 | 10 | 81.5 | 0.600 |
| rater1 / rater2 | Control | case_requirements | 90/90 | 0 | 86.7 | 0.309 |
| rater1 / rater2 | Control | G03 | 29/30 | 1 | 100.0 | Undefined |
| rater1 / rater2 | Control | any_error | 29/30 | 1 | 62.1 | 0.290 |
| rater1 / rater3 | Stroke | case_requirements | 357/357 | 0 | 94.4 | 0.305 |
| rater1 / rater3 | Stroke | G03 | 75/75 | 0 | 100.0 | Undefined |
| rater1 / rater3 | Stroke | any_error | 54/75 | 21 | 68.5 | 0.132 |
| rater1 / rater3 | Control | case_requirements | 90/90 | 0 | 87.8 | 0.200 |
| rater1 / rater3 | Control | G03 | 29/30 | 1 | 100.0 | Undefined |
| rater1 / rater3 | Control | any_error | 29/30 | 1 | 55.2 | 0.171 |
| rater2 / rater3 | Stroke | case_requirements | 357/357 | 0 | 95.0 | 0.559 |
| rater2 / rater3 | Stroke | G03 | 75/75 | 0 | 100.0 | Undefined |
| rater2 / rater3 | Stroke | any_error | 60/75 | 15 | 81.7 | 0.222 |
| rater2 / rater3 | Control | case_requirements | 90/90 | 0 | 92.2 | 0.614 |
| rater2 / rater3 | Control | G03 | 30/30 | 0 | 96.7 | 0.000 |
| rater2 / rater3 | Control | any_error | 30/30 | 0 | 80.0 | 0.143 |

These are descriptive item/report comparisons with within-participant dependence; pair-specific exclusions prevent treating all pairs as if they assessed the same reports. The full original independent outcome table is Supplementary Table S3. Rater1 and rater2 originally recorded fewer confirmed-error stroke reports for GPT than for the other models. Rater3 originally recorded 0/25 for Claude, 1/25 for GPT and 1/10 for Gemini with 15 unknown Gemini reports. Thus the later Claude-GPT error ordering was not reproduced by every original reviewer. Original coverage results consistently placed Claude and GPT above Gemini in mean full coverage, with different effect magnitudes.

Supplementary Table S5 directly compares coverage stages. Gemini stroke coverage was 93.8%, 86.0% and 86.5% in the three original reviews, versus 81.8% in the shared frozen layer. Claude and GPT changed less. These differences combine clarification, personal reconsideration and discussion; they cannot be attributed causally to D01 or D02 alone. Model separation in the frozen layer must not be presented as the magnitude found independently by all original reviewers.

### Post-unblinding targeted sensitivity

The eight-item follow-up did not alter coverage scores. Claude retained 11 confirmed-error stroke reports and GPT retained two. Gemini varied from 10 to 12 confirmed-error reports across the 25 planned slots, with an overall unknown-status envelope of 40%-56% (Table 6). Only two report-level any-error statuses could change; other changed claim labels left a separate confirmed error. The description of fewer flagged stroke reports for GPT persisted within this targeted sensitivity, while the Claude-Gemini ordering was not stable. These classification bounds are not sampling intervals or evidence of general superiority. The control pathology disagreement remained separately visible.

### Table 6. Gemini stroke sensitivity to targeted interpretations

| Scenario | Gemini error / evaluable | Unknown | All-planned bounds, % |
| --- | --- | --- | --- |
| Frozen baseline | 12/23 | 2 | 48.0 to 56.0 |
| rater1 targeted overlay | 11/22 | 3 | 44.0 to 56.0 |
| rater2 targeted overlay | 12/23 | 2 | 48.0 to 56.0 |
| rater3 targeted overlay | 11/22 | 3 | 44.0 to 56.0 |
| Disagreements kept unknown | 10/21 | 4 | 40.0 to 56.0 |
| Disputed claims cleared | 10/22 | 3 | 40.0 to 52.0 |
| Disputed claims counted | 12/23 | 2 | 48.0 to 56.0 |

Named-reviewer overlays replace only the eight targeted decisions and one annotation. All other judgments retain the shared frozen baseline; these rows must not be labeled complete independent-rater analyses. Disputed-claim scenarios are analyst-defined, not votes or additional expert judgments.

## Discussion

The study separates two questions: whether a report conveys the required findings and whether its claims stay within the supplied evidence. High coverage did not guarantee fidelity. In the frozen layer, Claude and GPT covered more required content than Gemini, while GPT had fewer confirmed-error stroke reports. The Claude-GPT coverage interval included zero; the error comparison was descriptive. These findings support reporting separate endpoints rather than collapsing them into an unvalidated overall score.

The review-stage comparison is central to interpretation. All original reviewers placed Claude and GPT above Gemini on mean stroke coverage, but the magnitude of separation changed after feedback. Original error judgments were less consistent, and one reviewer did not reproduce the later Claude-GPT pattern. A common framework can make disagreements explicit without establishing an objective clinical truth. Preserving the independent stage and unresolved claims makes the dependence on that framework visible.

Report length provides another potential explanation to investigate, rather than a correction that can be imposed retrospectively. Longer reports have more space for required explanations and more opportunities to make unsupported claims. The present data do not separate length from model, style or reasoning configuration, and no causal effect of length is estimated. Future work could prospectively compare matched output-length constraints and repeated generations while retaining participant pairing.

The control supplement addresses how disclosed healthy status is handled, not whether a model can identify an undisclosed diagnosis. Any-error includes incorrect numerical comparisons and evidence-boundary violations; it is broader than a pathological assertion. The disputed pathology annotation and the small control denominator preclude a robust estimate of rare harmful assertions. Shared reference participation further limits generalization.

The preserved prompts, source-linked judgments and offline numerical replay address transparency concerns emphasized by CHART. They do not remedy case selection, reviewer involvement in rule development or later amendments. Further testing would need independent cases, prospectively specified handling of ambiguous language, repeated model outputs and assessment of whether clinicians find the reports useful. This study did not measure workflow time, management decisions or patient outcomes. [CHART explanation and elaboration](https://www.bmj.com/content/390/bmj-2024-083305).

## Limitations

First, this was a resource-defined, selected internal sample of 25 stroke participants and 10 controls. It was not a random clinical population sample, a powered equivalence study or external validation. The available stroke cohort and the selected subset do not represent all stroke stages or ambulatory abilities. Controls were relatively old, not matched to stroke cases, and had contributed to reference/calibration construction. Age and speed differences, shared reference estimates and missing muscle data limit physiological comparability. Leave-one-out self-exclusion does not remove all shared-data dependence.

Second, the task tested constrained interpretation of supplied summaries. Models knew cohort membership and did not inspect raw EMG, individual strides or clinical examinations. High rubric coverage therefore does not establish diagnostic accuracy, patient benefit or readiness for clinical use. Correctly expressing uncertainty can be appropriate, while a true but unsupplied detail can violate the task's evidence boundary. The endpoints combine different types of error without a validated severity weighting. The four-channel GPS-like composite and threshold-derived envelope summaries are not clinical diagnostic tests.

Third, the reference standard was an expert-defined interpretation framework rather than independent clinical ground truth. Two raters helped develop the rules, while the third joined after the first submissions. Review and discussion clarified ambiguous wording and sometimes changed labels. Blinding to model identity reduced one source of bias but did not remove stylistic clues, prior beliefs, development involvement or later exposure to peer views. The frozen post-feedback results must be read alongside the original independent agreement and outcome analyses; original rater3 error judgments did not reproduce every later model ordering.

Fourth, the source audit and eight-item follow-up occurred after analysis-team unblinding. Their purposive scope and analyst-defined scenarios make the supplement exploratory. Unchanged coverage follows from the fact that coverage was not reassessed; it is not an independent validation. Retaining four divergent issue judgments and one disputed pathology annotation is more faithful than implying new unanimity. The targeted sensitivity does not establish robustness to all possible errors, alternative rubrics or selection of a different reference standard.

Fifth, only one response was generated per case and configuration. The study cannot estimate within-model stochastic reliability or performance across prompt variants. Recorded effort labels, token allowances and provider-managed sampling settings do not establish equal compute. Saved identifiers may be service aliases, and operational staging introduces time/batch context despite unchanged settings. Results apply to these saved configurations and responses.

Finally, item and report counts exceed the number of independent participants. Pairwise agreement denominators differ, and naive item-level precision would be misleading. Exact binomial intervals do not remedy selected sampling or shared references; bootstrap intervals remain approximate. Ten controls provide limited precision, particularly for rare semantic flags. No overall winner, clinical false-positive rate or proof of safety should be inferred from these results.

## Conclusion

Within this selected task, Claude and GPT covered more required content than Gemini, while the post-feedback outcomes and targeted sensitivity recorded fewer error-positive stroke reports for GPT. Completeness and fidelity should be reported separately. Reviewer-stage differences and the disputed control pathology annotation limit stronger conclusions. Further evaluation would require new cases, an independently applied reference standard and repeated outputs; those extensions were not performed in this study.

## Supplementary tables

### Supplementary Table S1. Recorded generation configurations

| Model identifier | Recorded API route | Recorded SDK | Reasoning setting | Output-token allowance |
| --- | --- | --- | --- | --- |
| claude-opus-5 | Messages API, streamed | anthropic 1.6.0 | {"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}} | 16000 |
| gpt-6-astra | Chat Completions API, streamed with usage | openai 3.14.1 | {"reasoning_effort": "high"} | 16000 |
| gemini-3.1-pro-preview | Generate Content API, generate_content_stream | google-genai 2.23.0 | {"thinking_config": {"thinking_level": "HIGH", "include_thoughts": false}} | 16000 |

Client retries were disabled; allowed retry behavior was controlled by the study runner and no formal retry occurred. Stored SDK versions and model identifiers are historical generation records. Sampling parameters not explicitly passed were provider-managed; equal effort labels are not evidence of equal compute. Generation ran from 2026-09-19T00:09:00.114889+00:00 to 2026-09-19T01:47:15.801637+00:00.

### Supplementary Table S2. Joint-success outcomes in the frozen layer

| Cohort | Model | Success / complete reviews | Unknown status | Excluded from point estimate | Exact 95% CI, % | All-planned bounds, % |
| --- | --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 10/21 | 3 | 4 | 25.7 to 70.2 | 40.0 to 52.0 |
| Stroke | GPT-6-astra | 20/25 | 0 | 0 | 59.3 to 93.2 | 80.0 to 80.0 |
| Stroke | Gemini 3.1 Pro preview | 2/18 | 2 | 7 | 1.4 to 34.7 | 8.0 to 16.0 |
| Control | Claude Opus 5 | 1/7 | 1 | 3 | 0.4 to 57.9 | 10.0 to 20.0 |
| Control | GPT-6-astra | 6/10 | 0 | 0 | 26.2 to 87.8 | 60.0 to 60.0 |
| Control | Gemini 3.1 Pro preview | 1/10 | 0 | 0 | 0.3 to 44.5 | 10.0 to 10.0 |

A known joint failure with unresolved issues can be outside the complete-review denominator while still constraining all-planned bounds. The joint measure is operational, not clinical usability certification.

### Supplementary Table S3. Original independent outcomes

| Reviewer | Cohort | Model | Mean full coverage, % | Error reports / evaluable | Unknown | All-planned bounds, % |
| --- | --- | --- | --- | --- | --- | --- |
| rater1 | Stroke | Claude Opus 5 | 98.0 | 13/22 | 3 | 52.0 to 64.0 |
| rater1 | Stroke | GPT-6-astra | 97.0 | 2/25 | 0 | 8.0 to 8.0 |
| rater1 | Stroke | Gemini 3.1 Pro preview | 93.8 | 11/18 | 7 | 44.0 to 72.0 |
| rater1 | Control | Claude Opus 5 | 96.7 | 7/9 | 1 | 70.0 to 80.0 |
| rater1 | Control | GPT-6-astra | 90.0 | 1/10 | 0 | 10.0 to 10.0 |
| rater1 | Control | Gemini 3.1 Pro preview | 90.0 | 8/10 | 0 | 80.0 to 80.0 |
| rater2 | Stroke | Claude Opus 5 | 96.4 | 5/25 | 0 | 20.0 to 20.0 |
| rater2 | Stroke | GPT-6-astra | 95.2 | 2/25 | 0 | 8.0 to 8.0 |
| rater2 | Stroke | Gemini 3.1 Pro preview | 86.0 | 18/25 | 0 | 72.0 to 72.0 |
| rater2 | Control | Claude Opus 5 | 93.3 | 1/10 | 0 | 10.0 to 10.0 |
| rater2 | Control | GPT-6-astra | 90.0 | 0/10 | 0 | 0.0 to 0.0 |
| rater2 | Control | Gemini 3.1 Pro preview | 76.7 | 4/10 | 0 | 40.0 to 40.0 |
| rater3 | Stroke | Claude Opus 5 | 99.2 | 0/25 | 0 | 0.0 to 0.0 |
| rater3 | Stroke | GPT-6-astra | 99.2 | 1/25 | 0 | 4.0 to 4.0 |
| rater3 | Stroke | Gemini 3.1 Pro preview | 86.5 | 1/10 | 15 | 4.0 to 64.0 |
| rater3 | Control | Claude Opus 5 | 96.7 | 2/10 | 0 | 20.0 to 20.0 |
| rater3 | Control | GPT-6-astra | 96.7 | 0/10 | 0 | 0.0 to 0.0 |
| rater3 | Control | Gemini 3.1 Pro preview | 80.0 | 1/10 | 0 | 10.0 to 10.0 |

These are the preserved original independent stage, unlike the targeted hybrid overlays in Table 6. They must not be substituted selectively to obtain a preferred model ordering.

### Supplementary Table S4. Review and amendment timeline

| Recorded timing | Stage | Interpretation |
| --- | --- | --- |
| Before formal generation | Two-reviewer protocol and fixed case requirements | 119 stroke and 30 control requirements; third reviewer originally reserved for unresolved adjudication. |
| 2026-09-19T00:09:00.114889+00:00 to 2026-09-19T01:47:15.801637+00:00 | Formal generation | 105 saved reports; operational stages did not change inputs or settings. |
| 2026-09-19 UTC | Third full independent reviewer added | After the first two returns and administrative outcome counts; identities still concealed. Change from the original plan. |
| After generation; before D01-D03 | Original independent submissions | All three reviewed 105 reports independently. Original workbook hashes are retained; later personal changes do not replace this stage. |
| 2026-09-19 (recorded date; no time zone supplied) | D01-D03 post-independent clarification | Required explanation beyond numerical lists; ordered lists still require interpretation; genuine clinical questions are permitted subject to factual/presupposition exceptions. |
| After D01-D03; before the blinded freeze | Personal rechecks and shared discussion | Source-linked personal changes and unresolved interpretations retained. This is not a new independent review; no exact discussion timestamp is inferred. |
| 2026-09-23T16:57:14.416061+00:00 | Semantic-flag clarification | Explicit qualifying human pathology annotation does not require a simultaneous E02 tag. |
| 2026-09-23T18:23:29.970501+00:00 | Blinded post-feedback freeze | 52 confirmed groups and 16 unresolved Pending groups; original ratings remain separate. |
| 2026-09-23T19:36:30.271641+00:00 | Authorized analysis-team unblinding | Mapping joined after freeze, outside reviewer materials. |
| 2026-09-25T02:38:04.496626+00:00 | Targeted wording-return receipt check | Eight personal claim reviews after analysis-team unblinding; exploratory overlays preserve disagreements and the frozen baseline. |

Full timestamps are copied from recorded UTC events. Date-only records retain their documented precision and time-zone limits. The final row dates the administrative receipt check, not every reviewer action. Sequential descriptions are used where an exact timestamp was not established. Historical protocols were not rewritten to imply prospective three-rater planning or pre-rating clarification.

### Supplementary Table S5. Coverage before and after review

| Cohort | Model | rater1 original, % | rater2 original, % | rater3 original, % | Frozen post-feedback, % |
| --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 98.0 | 96.4 | 99.2 | 98.2 |
| Stroke | GPT-6-astra | 97.0 | 95.2 | 99.2 | 97.0 |
| Stroke | Gemini 3.1 Pro preview | 93.8 | 86.0 | 86.5 | 81.8 |
| Control | Claude Opus 5 | 96.7 | 93.3 | 96.7 | 90.0 |
| Control | GPT-6-astra | 90.0 | 90.0 | 96.7 | 86.7 |
| Control | Gemini 3.1 Pro preview | 90.0 | 76.7 | 80.0 | 73.3 |

The frozen column is one shared post-feedback layer, not a fourth independent reviewer. All columns use the fixed case denominators and equal participant weighting. Differences are descriptive stage sensitivity, not an estimated causal effect of one clarification.

### Supplementary Table S6. Saved report length

| Cohort | Model | Reports | Median whitespace units | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 25 | 2049.0 | 1909 | 2419 |
| Stroke | GPT-6-astra | 25 | 818.0 | 765 | 910 |
| Stroke | Gemini 3.1 Pro preview | 25 | 761.0 | 657 | 936 |
| Control | Claude Opus 5 | 10 | 1992.0 | 1881 | 2265 |
| Control | GPT-6-astra | 10 | 803.5 | 759 | 810 |
| Control | Gemini 3.1 Pro preview | 10 | 712.5 | 696 | 867 |

Counts use Python str.split() on the hash-verified blinded report text, including Markdown. They are neither provider tokens nor a validated measure of verbosity or quality. This analysis was added after unblinding; no length-adjusted outcome or new inferential test was specified.

## References

- Van Criekinge T, et al. A full-body motion capture gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors. Scientific Data. 2023;10:852. [doi:10.1038/s41597-023-02767-y](https://doi.org/10.1038/s41597-023-02767-y).
- The CHART Collaborative. Reporting guidelines for chatbot health advice studies: explanation and elaboration for the Chatbot Assessment Reporting Tool (CHART). BMJ. 2025;390:e083305. [doi:10.1136/bmj-2024-083305](https://doi.org/10.1136/bmj-2024-083305).
- SciPy documentation. Bootstrap confidence intervals, including paired resampling and BCa. [Documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). Used for methodological context; local code produced this study's saved estimates.
- NIST Dataplot reference manual. Exact binomial confidence limits. [Documentation](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).

## Declarations requiring author completion

The institutional ethics determination for this secondary analysis, author affiliations and contributions, funding, competing interests, and the final data/code release statement remain to be supplied by the authors. The original dataset's approvals do not constitute an approval or exemption for this project. The recorded human expert judgments must not be described as newly signed through manuscript preparation. The role of AI-assisted drafting, software development and source auditing should be described accurately in the journal's required disclosure, without assigning such tools authorship or decision authority. See AUTHOR_CONFIRMATION.md.
