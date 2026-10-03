# Completeness and evidence fidelity of large language model gait reports

Working manuscript draft for author review. Numerical results are drawn from preserved analysis records. Bracketed author-confirmation fields must be completed before submission. This document does not assert prospective registration, institutional ethical exemption, unconfirmed reviewer credentials or a new expert consensus.

## Abstract

**Objective:** Fluent gait reports can omit findings or overstate evidence. We evaluated a framework for assessing completeness and evidence fidelity in large language model gait reports, using a paired comparison with a separate healthy-control analysis.

**Methods:** We generated one report with each of `claude-opus-5`, `gpt-6-astra` and `gemini-3.1-pro-preview` for 25 selected stroke participants and 10 controls from a public motion-capture/EMG dataset (105 reports). Three EMG researchers independently rated the reports, then reviewed their judgments after scoring-rule clarification. The primary analysis used the ratings finalized after review; original independent ratings were analyzed separately. Full coverage was the mean proportion of case requirements rated Covered, with equal participant weighting. Paired stroke comparisons used 20,000 bias-corrected and accelerated bootstrap resamples. We assessed confirmed errors separately from unresolved judgments and examined sensitivity to disputed wording.

**Results:** Mean full coverage in stroke reports was 98.2% for Claude, 97.0% for GPT and 81.8% for Gemini. Confidence intervals adjusted for the three comparisons excluded zero for Claude-Gemini and GPT-Gemini, but not Claude-GPT. Confirmed errors occurred in 11/22, 2/25 and 12/23 evaluable stroke reports, respectively; error status remained unknown for the other reports. Original error kappa ranged from 0.132 to 0.600; one reviewer initially identified no Claude stroke errors. Error comparisons were exploratory. Corresponding control error counts were 6/9, 0/10 and 8/10. One control pathology annotation remained disputed. Alternative interpretations of selected wording yielded 10-12 confirmed-error Gemini stroke reports among 25 planned reports, with coverage unchanged.

**Conclusion:** Reports with high content coverage could still contain unsupported or incorrect claims. Completeness and evidence fidelity should be evaluated separately. The findings apply to the outputs and scoring procedures studied here; clinical benefit and broader model performance require further evaluation.

## Introduction

Interpreting a gait summary requires more than restating its measurements. A report must identify the principal findings and distinguish numerical differences from explanations that the data cannot establish. Comparisons of post-stroke muscle activity with healthy references depend on walking speed, gait-event alignment and variability within the reference population. Srivastava and colleagues addressed these factors in their altered muscle activation patterns (AMAP) method, using speed-matched comparisons and corresponding gait sub-phases. [1](https://doi.org/10.1186/s12984-019-0487-y) The public dataset used here provides kinematics and surface electromyography (EMG) from able-bodied adults and stroke survivors recorded at self-selected speeds. Its authors describe demographic and speed-related constraints on comparisons between groups. [2](https://doi.org/10.1038/s41597-023-02767-y)

Large language model (LLM) evaluations in medicine have assessed more than factual recall. Singhal and colleagues evaluated medical answers for factuality, reasoning and potential harm, among other dimensions. [3](https://doi.org/10.1038/s41586-023-06291-2) In clinical text summarization, Van Veen and colleagues used physician review to assess completeness, correctness and conciseness. [4](https://doi.org/10.1038/s41591-024-02855-5) The Clinical Large Language Model Evaluation by Expert Review (CLEVER) framework similarly uses blinded expert comparisons across factuality, clinical relevance and conciseness. [5](https://doi.org/10.2196/72153) These studies support evaluating distinct aspects of report quality, but their findings do not establish performance on numerical gait summaries.

Gait report generation is also an emerging application. OGA-AID combines movement recordings, kinematic trajectories and clinical profiles in a multimodal system for post-stroke report drafting, with evaluation by physiotherapists. [6](https://arxiv.org/abs/2604.05360v2) Our study addresses a narrower task: interpreting a fixed numerical summary without access to videos, raw recordings or clinician notes. This design allows comparison of how three model configurations handle the same supplied findings and their stated limits.

We assessed completeness and evidence fidelity separately. Completeness concerns whether a report explains the required findings; evidence fidelity concerns whether its claims are supported by the input. A report can omit an important difference despite fluent prose, or describe the required findings while adding an incorrect comparison or unsupported explanation. Case-specific requirements and checks against the source input allow these problems to be recorded separately, while ambiguous claims can remain unresolved.

We compared three model configurations using identical inputs for 25 stroke participants, with required-content coverage as the primary outcome. A separate analysis of 10 healthy controls examined how reports interpreted deviations when healthy cohort membership was known. Three human experts assessed the reports. We compared their original independent ratings with ratings finalized after clarification and discussion, and examined the effect of unresolved interpretations on the findings.

## Methods

### Study design and data source

We conducted a methodological evaluation of structured gait-report assessment using a within-participant comparison of three saved model configurations. The principal cohort comprised 25 stroke participants; 10 healthy controls formed a separate exploratory supplement. The task was to describe the supplied evidence faithfully and express its limits, rather than diagnose disease, recommend treatment or interpret raw recordings independently. Each participant contributed one report per configuration, yielding 105 reports. Model outputs and repeated ratings did not increase the independent participant count.

Data originated from the public dataset of Van Criekinge and colleagues, which includes 50 stroke survivors and 138 able-bodied adults and provides motion-capture and surface EMG data in source and postprocessed forms. We used released participant-average curves and verified derived features. The original data-collection study reported informed consent and ethics approvals. The determination applicable to the present secondary analysis remains **[AUTHOR CONFIRMATION REQUIRED: institution, review or exemption determination, and reference number if applicable]**. [2](https://doi.org/10.1038/s41597-023-02767-y).

### Case selection and sample size

The stroke cohort was the entire conservative internal eligibility pool of 25 participants. The local inventory began with 50 stroke participants, identified 43 with complete bilateral data, retained 27 with complete data and no prior report in the checked inventory, and excluded two additional individually audited cases. The controls were selected by a single recorded seeded pseudorandom ordering of 98 locally eligible participants, retaining the first 10. Controls were not age- or speed-matched to the stroke cohort. The study lead subsequently confirmed no additional known use outside the recorded project history for the selected participants. This attestation is not an exhaustive audit of all external systems.

Sample size was resource-defined; no power claim for model superiority or equivalence is made. Case-specific requirements for the selected participants were reviewed before formal generation. These were prospectively specified evaluation cases, not untouched external test cases. The controls had contributed to reference or calibration construction; leave-one-out calculations for individual comparisons did not make the control cohort independent external validation. Table 1 describes the retained sample. Age and published bilateral speed are administrative metadata, not additional model inputs; control speed was not supplied to the models. The published bilateral speed is distinct from the analyzed-side speed supplied in stroke prompts.

### Model-visible information and feature definitions

All three configurations received the same saved system/user input pair for a given participant. Stroke inputs described the paretic side; control inputs described the released left/right pooled average. Inputs identified cohort membership. Seven EMG channels and sagittal pelvis, hip, knee and ankle curves were represented on a 1,001-point cycle. Released normalized ensemble-average EMG curves were used without further amplitude normalization. Stroke normalization provenance was checked numerically where evaluable; healthy-side pooling and normalization relied on release documentation and were not numerically revalidated to the same extent.

The summary included relative envelope amplitudes, retained above-threshold intervals, threshold coverage, boundary continuity, maximum absolute phasewise standardized deviation, two whole-cycle overlap indices, sagittal range of motion and reference-deviation scores. Stroke summaries also provided speed, cadence and a successive-footfall step-length index, defined as 200(P-N)/(P+N), where P and N denote paretic and non-paretic step lengths. This index is not the ordinary percentage shortening relative to the other step. Control prompts marked that paretic/non-paretic index as inapplicable and speed/cadence as not supplied.

The EMG threshold was 20% of each supplied mean curve's own peak. A sample was above threshold only when its value exceeded this threshold. Coverage was the proportion of above-threshold samples before interval filtering. Circular above-threshold runs were retained when their sample count met the 3% minimum; on the 1,001-point grid the integer threshold was 30 samples. This filter removes short above-threshold runs, not below-threshold gaps. Wrapped intervals could cross the cycle boundary. Display rounding could obscure small discontinuities; neither rounded 100% coverage nor a displayed 0%-100% retained interval established full-precision continuous exceedance or physiological continuous contraction. EMG onset estimates depend on the detection method and its parameters. [7](https://pubmed.ncbi.nlm.nih.gov/9020824/) The present 20% threshold and 3% run-length rule were study-specific descriptive choices; the cited onset-detection work does not validate them as physiological onset measures or clinical cutoffs.

The overlap index was computed as twice the summed pointwise minimum of two normalized envelopes divided by their summed amplitudes over the cycle, for TA/GAS and RF/BF. It was not simultaneous activation duration. Per-channel kinematic deviation was the root-mean-square difference from the reference mean curve; the composite was the root mean square of the four sagittal channel scores and was explicitly labeled GPS-like rather than the original nine-variable Gait Profile Score (GPS). [8](https://doi.org/10.1016/j.gaitpost.2009.05.020) Validation of the original GPS does not establish validity of this four-channel composite. Maximum absolute z was the maximum across 1,001 phasewise comparisons, not a single-observation z statistic or a clinical abnormality test.

The reference was pooled rather than individually age- or speed-matched. Stroke comparisons used the healthy reference; each control was excluded from its own mean/SD comparison. Pooled calibration summaries remained distinct from leave-one-out individual references. The full reference included 138 participants for kinematics, with effective EMG availability varying by muscle (106-109 before self-exclusion). Supplied empirical percentiles were descriptive and did not establish diagnostic or normality cutoffs. In particular, the supplied span of muscle-specific maximum-|z| percentiles did not reveal every muscle's individual cutoff.

The instructions permitted naming the documented initial-contact boundary, anatomical muscle actions and genuine clinical follow-up questions. They prohibited assigning intermediate gait phases from cycle percentages without events, converting summary metrics into unsupported deficits or diagnoses, or treating an open question as permission to assert an unsupported observed finding. Individual toe-off, matched muscle timing, raw-signal quality and stride variability were outside the input. Models received no plots, expert checklist, reference answers, retrieval tools or prior conversation. Experts could consult the supplied curves and reference materials while respecting this model-visible information boundary.

### Model configuration and generation

We evaluated the recorded identifiers `claude-opus-5`, `gpt-6-astra` and `gemini-3.1-pro-preview`. These identify the saved configurations, not claims about current services or permanently pinned versions. Each had a 16,000-token output allowance with its recorded high/adaptive reasoning configuration (Supplementary Table S1). The allowance and effort labels did not establish equal computational expenditure across providers. Sampling parameters not sent by the adapter remained provider-managed; deterministic generation is not claimed.

All 105 reports were generated on 19 September 2026 UTC with identical case inputs across models, balanced provider ordering and unchanged settings across three batches. Each case-model pair contributed one response, with no retry, refusal or token-limit finish. Technical probes were excluded. Supplementary methods describe execution and retained records.

### Expert assessment and workflow changes

Three human reviewers independently scored all 105 reports in the original rating round. All three were PhD students at The University of Texas at Austin with at least five years of experience in EMG analysis and neuromuscular control research, as confirmed by the study lead. Rater1 and rater2 participated in criteria development; rater3 joined at scoring and did not develop the criteria. Together they completed 315 report reviews and 1,656 coverage judgments per complete stage.

The study was not preregistered. The internal plan specified two independent reviewers and a third for unresolved adjudication. A third complete independent review was added after the first two submissions and inspection of some blinded outcome counts. Model identities remained concealed. The third reviewer had no tie-breaking authority.

Packets concealed provider metadata and used opaque identifiers, independently randomized reading orders and separated same-case reports. Original prose was preserved, leaving stylistic clues possible. Reviewers recorded incidental unblinding. Independent submissions were preserved separately from subsequent corrections and discussion; later reviews were not independent repetitions.

Case-specific requirements were fixed before generation: 119 across stroke cases and 30 across controls. Each report had 4-6 stroke requirements or three control requirements. Reviewers used Covered, Partially covered or Not covered, with missing or unresolved assessments recorded separately. A core finding required its specified explanatory content, not only a numerical list. G03 separately assessed meaningful reference-comparability limitations and their implications for disease attribution or diagnosis; one statement could satisfy overlapping requirements without repetition.

Correctness was assessed through distinct report-scoped issue groups under nine categories: misreported facts; unsupported clinical/function inference; threshold/amplitude overinterpretation; unsupported events/phases/functions; invalid reference classification; overlap-index overinterpretation; kinematic-summary overinterpretation; missingness/applicability errors; and unsupported matching/disease attribution. Multiple tags or repeated locations did not multiply a group. Coverage and error judgments remained separate. Interpretive uncertainty could remain Pending; it was neither forced to Error nor cleared by default.

Ratings were finalized before model identities were linked to the analysis, with matching coverage judgments, 52 confirmed issue groups and 16 unresolved groups. Individual category differences were retained. A post-rating clarification removed the requirement for a simultaneous clinical-inference error tag on pathological presuppositions; an explicit qualifying annotation and confirmed in-scope error were still required.

After independent submission, scoring instructions were clarified to require interpretation beyond numerical or ranked lists and to distinguish open clinical questions from incorrect facts or unsupported premises. Reviewers applied these clarifications during personal rechecks and discussion. Primary results use the resulting final ratings; original independent results are reported separately.

### Outcomes and analysis

The primary outcome was full coverage of included case requirements: C_im = Covered_im / K_i. Participants were equally weighted, K_i remained fixed across models, partial coverage received no half-credit, and G03 was excluded from K_i. The primary comparison used the same 25 stroke participants with all three coverage scores available. For each model pair, we calculated participant-level percentage-point differences and their mean. We used 20,000 paired BCa resamples, the same saved participant-index matrix for all contrasts and seed 20260918. Descriptive 95% and approximate Bonferroni-adjusted 98.3333% intervals were reported for the three primary contrasts. The implementation preserved paired sampling and reported unavailable intervals without switching methods; these are approximate intervals rather than guaranteed finite-sample bounds. [9](https://doi.org/10.1080/01621459.1987.10478410) [10](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).

Secondary outcomes included any confirmed case error, unique confirmed issue counts, G03 coverage, technical completion and an operational joint-success measure requiring all case requirements and G03 Covered with no confirmed or Pending error after complete review. These were not clinical safety or usefulness endpoints. Any-error was positive if at least one confirmed error existed; otherwise it was negative only after complete review with no Pending issue, and unknown otherwise. Evaluable denominators and bounds across all planned reports were shown together. Bounds counted unknown states as zero or one and were not confidence intervals. Joint-success point estimates retained the protocol's complete-review denominator, separately from all-planned known/unknown status.

Binary outcomes used exact two-sided 95% binomial intervals on the stated evaluable denominators; their assumptions are limited by selected cases and shared references. The zero-event control result also has a one-sided 95% upper limit of 1-0.05^(1/10), approximately 25.9%. Secondary and control comparisons were exploratory, without additional confirmatory tests or an overall quality ranking. [11](https://doi.org/10.1093/biomet/26.4.404) [12](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).

Original independent agreement was evaluated separately by cohort and domain using raw agreement, three-category coverage cross-tabulations and unweighted Cohen's kappa; report-level any-error used binary states. [13](https://doi.org/10.1177/001316446002000104) Pairwise unknown/incomplete observations were excluded with counts disclosed. Rater1-rater2 was the originally planned comparison; the other pairs were supplementary. Kappas were not averaged into a three-rater coefficient. We reported raw agreement alongside kappa because kappa depends on the marginal distributions of ratings. [14](https://pubmed.ncbi.nlm.nih.gov/2348207/) No confidence interval treating all item rows as independent was used. Original independent model-specific outcomes were retained as a sensitivity analysis distinct from post-feedback outcomes. We added a post-hoc nominal Gwet AC1 analysis using the same original ratings, categories and exclusions. [15](https://doi.org/10.1348/000711006X126600) Confidence intervals used 20,000 participant-cluster bootstrap samples, retaining all reports and items within each sampled participant. AC1 uses a different agreement comparator from kappa and was not treated as its replacement or as evidence of correct judgments. [16](https://doi.org/10.1016/j.mex.2023.102212) Calculation details appear in the supplementary methods.

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

Mean full coverage was 98.2% for Claude, 97.0% for GPT and 81.8% for Gemini. Claude-Gemini and GPT-Gemini contrasts were positive under the planned family-adjusted interval procedure. The Claude-GPT interval included zero and did not establish either superiority or equivalence (Table 3). No participant was excluded from the complete paired coverage analysis. All reference-limit judgments were Covered in the final ratings. The denominator comprised case-specific requirements rather than all possible factual assertions.

### Table 2. Final coverage and report-level errors, by cohort

| Cohort | Model | Mean full coverage, % | Error reports / evaluable | Unknown | Exact 95% CI, % | All-planned bounds, % | Confirmed groups |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 98.2 | 11/22 | 3 | 28.2 to 71.8 | 44.0 to 56.0 | 17 |
| Stroke | GPT-6-astra | 97.0 | 2/25 | 0 | 1.0 to 26.0 | 8.0 to 8.0 | 2 |
| Stroke | Gemini 3.1 Pro preview | 81.8 | 12/23 | 2 | 30.6 to 73.2 | 48.0 to 56.0 | 13 |
| Control | Claude Opus 5 | 90.0 | 6/9 | 1 | 29.9 to 92.5 | 60.0 to 70.0 | 9 |
| Control | GPT-6-astra | 86.7 | 0/10 | 0 | 0.0 to 30.8 | 0.0 to 0.0 | 0 |
| Control | Gemini 3.1 Pro preview | 73.3 | 8/10 | 0 | 44.4 to 97.5 | 80.0 to 80.0 | 11 |

Coverage is the equally weighted participant mean. Error proportions use the displayed evaluable denominator; unknown reports remain in the bounds across all planned reports. Confirmed groups are not severity-weighted and are not the number of erroneous reports. Later wording-review alternatives are reported below; this table preserves the preserved final ratings.

### Table 3. Paired stroke coverage contrasts

| Contrast | Difference, percentage points | Descriptive 95% BCa | Family-adjusted 98.3333% BCa |
| --- | --- | --- | --- |
| Claude Opus 5 minus Gemini 3.1 Pro preview | 16.4 | 10.8 to 22.8 | 9.6 to 24.2 |
| Claude Opus 5 minus GPT-6-astra | 1.2 | -1.4 to 5.2 | -1.6 to 6.2 |
| Gemini 3.1 Pro preview minus GPT-6-astra | -15.2 | -20.8 to -10.0 | -22.0 to -9.0 |

All intervals are in percentage points; n=25 paired participants. Gemini minus GPT is the negative form of GPT minus Gemini.

### Stroke errors and joint outcome

In the final ratings, Claude had confirmed errors in 11/22 evaluable stroke reports, Gemini in 12/23 and GPT in 2/25; three Claude and two Gemini reports were unknown because a Pending issue remained without a confirmed error. The bounds across all planned reports were 44%-56%, 48%-56% and 8%-8%, respectively. Confirmed issue groups numbered 17, 13 and two. This descriptive pattern was not subjected to a new confirmatory superiority test. Full coverage could coexist with a factual or interpretive error. Supplementary Table S2 reports the joint outcome with its complete-review denominator, which differs from the any-error denominator when a known failure also has unresolved issues.

### Healthy-control reports

The 10 controls contributed all 30 planned reports. Mean full coverage was 90.0% for Claude, 86.7% for GPT and 73.3% for Gemini. Confirmed-error reports numbered 6/9 evaluable for Claude, 0/10 for GPT and 8/10 for Gemini; one Claude report remained unknown. These counts include factual, metric and evidence-boundary violations, not only pathological assertions or diagnoses. No control normality annotation was positive in the final ratings. One Gemini control pathology annotation was positive when ratings were finalized, but later personal review produced Yes/No/Yes rather than a matching judgment (Table 4). The other models had no positive pathology annotation. Zero events among 10 controls did not establish absence of risk; the one-sided 95% upper limit was 25.9% under the binomial assumptions.

### Table 4. Control semantic annotations and later disagreement

| Model | Flag | Frozen events / evaluable | Unknown | Exact 95% CI, % | Later review |
| --- | --- | --- | --- | --- | --- |
| Claude Opus 5 | normality | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| Claude Opus 5 | pathology | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| GPT-6-astra | normality | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| GPT-6-astra | pathology | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| Gemini 3.1 Pro preview | normality | 0/10 | 0 | 0.0 to 30.8 | Unchanged |
| Gemini 3.1 Pro preview | pathology | 1/10 | 0 | 0.3 to 44.5 | Disputed: Yes / No / Yes; unknown scenario 0/9 with 1 unknown |

For the disputed Gemini pathology annotation, preserving disagreement as unknown gives zero known-positive reports among nine evaluable reports and one unknown, with bounds across all planned reports 0%-10%. This is not equivalent to 0/10 negative or to a new unanimous positive. Control any-error status remains unchanged in all targeted scenarios because other confirmed errors remain in the affected reports.

### Descriptive report length

Saved blinded report texts were counted by whitespace splitting, including headings and table markup. This post-hoc descriptive measure is not linguistic word segmentation, billable tokens, reasoning length or a measure of quality. Stroke median counts were 2,049 for Claude, 818 for GPT and 761 for Gemini; control medians were 1,992, 803.5 and 712.5 (Supplementary Table S5). No length adjustment or additional significance test was introduced.

### Original independent agreement and stage sensitivity

Original case-requirement agreement for stroke was 95.5%, 94.4% and 95.0% for rater1-rater2, rater1-rater3 and rater2-rater3, respectively; kappas were 0.550, 0.305 and 0.559. Report-level error agreement was less consistent and used different assessable subsets. Controls also showed differences between high raw coverage agreement and modest or variable kappa (Table 5). G03 kappa was often undefined because the included ratings had no category variation. Neither agreement nor kappa established correctness or reviewer quality. Post-hoc stroke coverage AC1 values were 0.942-0.953; stroke error values were 0.542-0.765. Control error AC1 was 0.295, 0.199 and 0.740 for the three pairs, with intervals crossing zero for the first two (Supplementary Table S6).

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

Supplementary Table S4 directly compares coverage stages. Gemini stroke coverage was 93.8%, 86.0% and 86.5% in the three original reviews, versus 81.8% in the shared final ratings. Claude and GPT changed less. These differences combine clarification, personal reconsideration and discussion; they cannot be attributed causally to D01 or D02 alone. Model separation in the final ratings must not be presented as the magnitude found independently by all original reviewers.

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

Named-reviewer overlays replace only the eight targeted decisions and one annotation. All other judgments retain the shared final ratings; these rows must not be labeled complete independent-rater analyses. Disputed-claim scenarios are analyst-defined, not votes or additional expert judgments.

## Discussion

High content coverage did not ensure evidence fidelity. Claude and GPT included more required content than Gemini in the final stroke ratings, but Claude reports also contained confirmed errors in 11 of 22 evaluable cases. GPT had fewer reports with confirmed errors, although this comparison was descriptive. The coverage difference between Claude and GPT remained uncertain; the error comparison was sensitive to how reviewers applied the criteria. These findings favor assessing completeness and errors separately: combining them into a single score would obscure differences that matter when reviewing a report. This distinction is consistent with the separate completeness and correctness judgments used by Van Veen and colleagues and the factuality dimension in CLEVER. [4](https://doi.org/10.1038/s41591-024-02855-5) [5](https://doi.org/10.2196/72153) Their tasks, models and evaluation criteria differed, so their results do not provide a direct benchmark for the error proportions reported here.

The coverage pattern was consistent across the original reviewers, each of whom rated Claude and GPT above Gemini on average. Its magnitude changed after clarification and discussion. Error judgments varied more, and one reviewer's original ratings did not show the later Claude-GPT ordering. The final ratings therefore reflect both the reports and how the experts applied the evaluation criteria. High raw agreement accompanied by a lower kappa also needs care: imbalanced rating distributions can produce this pattern, as Feinstein and Cicchetti demonstrated. [14](https://pubmed.ncbi.nlm.nih.gov/2348207/) The supplementary AC1 estimates describe agreement under a different comparator; substantial error disagreement remains, particularly in controls. Neither coefficient establishes which judgments are correct. Reporting the original ratings alongside the final results shows this dependence and preserves disagreements that the review did not resolve.

Report length may help explain the observed pattern, but the present design cannot isolate its contribution. Longer reports have more space to explain required findings and more opportunities to introduce unsupported claims. Length varied with model, writing style and reasoning configuration. A study that specifies comparable length limits and obtains repeated responses for each case could examine these relationships directly. Conciseness was a separate evaluation dimension in both the clinical summarization study and CLEVER; we did not score conciseness here. [4](https://doi.org/10.1038/s41591-024-02855-5) [5](https://doi.org/10.2196/72153)

Healthy-control reports provided a separate test of how models handled deviations in participants explicitly identified as healthy. The any-error outcome included incorrect numerical comparisons as well as unsupported interpretations, so it cannot be read as a rate of pathological diagnoses. Only 10 controls were included, and one pathology annotation remained disputed. These findings describe errors in the sampled reports but offer limited evidence about rare harmful assertions or performance in new populations.

Preserved prompts, judgments linked to the source reports and reproducible analyses allow readers to examine the basis of these findings. These practices follow the transparency principles of the Chatbot Assessment Reporting Tool (CHART). [17](https://doi.org/10.1136/bmj-2024-083305). A populated TRIPOD-LLM checklist identifies reported information and outstanding items. [18](https://doi.org/10.1038/s41591-024-03425-5) The next evaluation should use independent cases, prespecified wording rules and repeated outputs. Clinical usefulness also remains to be tested: this study did not measure review time, changes in management or patient outcomes. DECIDE-AI addresses reporting of early live clinical evaluations, including the interaction between users and decision-support systems. [19](https://doi.org/10.1038/s41591-022-01772-9) Such an evaluation would be a separate step beyond the present offline report comparison.

## Limitations

This was a resource-defined, selected internal sample of 25 stroke participants and 10 controls. It was not a random clinical population sample, a powered equivalence study or external validation. The available stroke cohort and the selected subset do not represent all stroke stages or ambulatory abilities. Controls were relatively old, not matched to stroke cases, and had contributed to reference/calibration construction. Age and speed differences, shared reference estimates and missing muscle data limit physiological comparability. Leave-one-out self-exclusion does not remove all shared-data dependence.

The task tested constrained interpretation of supplied summaries. Models knew cohort membership and did not inspect raw EMG, individual strides or clinical examinations. High rubric coverage therefore does not establish diagnostic accuracy, patient benefit or readiness for clinical use. Correctly expressing uncertainty can be appropriate, while a true but unsupplied detail can violate the task's evidence boundary. The endpoints combine different types of error without a validated severity weighting. The four-channel GPS-like composite and threshold-derived envelope summaries are not clinical diagnostic tests.

The reference standard was defined by EMG researchers and was not clinical ground truth. Reviewer expertise supports evaluation of signal interpretation, but physician or clinical gait-assessment credentials were not established. Two raters helped develop the rules, while the third joined after the first submissions. Review and discussion clarified ambiguous wording and sometimes changed labels. Blinding to model identity reduced one source of bias but did not remove stylistic clues, prior beliefs, development involvement or later exposure to peer views. The final ratings must be read alongside the original independent agreement and outcome analyses; original rater3 error judgments did not reproduce every later model ordering.

The source audit and eight-item follow-up occurred after analysis-team unblinding. Their purposive scope and analyst-defined scenarios make the supplement exploratory. Coverage was unchanged because the follow-up did not reassess it; this provides no independent validation of coverage. Retaining four divergent issue judgments and one disputed pathology annotation is more faithful than implying new unanimity. The targeted sensitivity does not establish robustness to all possible errors, alternative rubrics or selection of a different reference standard.

Only one response was generated per case and configuration. The study cannot estimate within-model stochastic reliability or performance across prompt variants. Provider settings do not establish equal compute. Version drift and operational timing limit transfer to later services. The conclusions concern the recorded configurations and responses.

Item and report counts exceed the number of independent participants. Pairwise agreement denominators differ, and naive item-level precision would be misleading. Exact binomial intervals do not remedy selected sampling or shared references; bootstrap intervals remain approximate. Ten controls provide limited precision, particularly for rare semantic flags. No overall winner, clinical false-positive rate or proof of safety should be inferred from these results.

## Conclusion

Separate assessment of completeness and evidence fidelity identified omissions, unsupported claims and unresolved interpretations in gait reports. Claude and GPT achieved higher coverage than Gemini in this sample, while error comparisons depended more strongly on the rating process. These findings support further evaluation of the assessment framework with independent cases, repeated outputs and a prospectively specified reference standard.

## Supplementary tables

### Supplementary Table S1. Recorded generation configurations

| Model identifier | Recorded API route | Recorded SDK | Reasoning setting | Output-token allowance |
| --- | --- | --- | --- | --- |
| claude-opus-5 | Messages API, streamed | anthropic 1.6.0 | {"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}} | 16000 |
| gpt-6-astra | Chat Completions API, streamed with usage | openai 3.14.1 | {"reasoning_effort": "high"} | 16000 |
| gemini-3.1-pro-preview | Generate Content API, generate_content_stream | google-genai 2.23.0 | {"thinking_config": {"thinking_level": "HIGH", "include_thoughts": false}} | 16000 |

Client retries were disabled; allowed retry behavior was controlled by the study runner and no formal retry occurred. Stored SDK versions and model identifiers are historical generation records. Sampling parameters not explicitly passed were provider-managed; equal effort labels are not evidence of equal compute. Generation ran from 2026-09-19T00:09:00.114889+00:00 to 2026-09-19T01:47:15.801637+00:00.

### Supplementary Table S2. Joint-success outcomes in the final ratings

| Cohort | Model | Success / complete reviews | Unknown status | Excluded from point estimate | Exact 95% CI, % | All-planned bounds, % |
| --- | --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 10/21 | 3 | 4 | 25.7 to 70.2 | 40.0 to 52.0 |
| Stroke | GPT-6-astra | 20/25 | 0 | 0 | 59.3 to 93.2 | 80.0 to 80.0 |
| Stroke | Gemini 3.1 Pro preview | 2/18 | 2 | 7 | 1.4 to 34.7 | 8.0 to 16.0 |
| Control | Claude Opus 5 | 1/7 | 1 | 3 | 0.4 to 57.9 | 10.0 to 20.0 |
| Control | GPT-6-astra | 6/10 | 0 | 0 | 26.2 to 87.8 | 60.0 to 60.0 |
| Control | Gemini 3.1 Pro preview | 1/10 | 0 | 0 | 0.3 to 44.5 | 10.0 to 10.0 |

A known joint failure with unresolved issues can be outside the complete-review denominator while still constraining bounds across all planned reports. The joint measure is operational, not clinical usability certification.

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

### Supplementary Table S4. Coverage before and after review

| Cohort | Model | rater1 original, % | rater2 original, % | rater3 original, % | Frozen post-feedback, % |
| --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 98.0 | 96.4 | 99.2 | 98.2 |
| Stroke | GPT-6-astra | 97.0 | 95.2 | 99.2 | 97.0 |
| Stroke | Gemini 3.1 Pro preview | 93.8 | 86.0 | 86.5 | 81.8 |
| Control | Claude Opus 5 | 96.7 | 93.3 | 96.7 | 90.0 |
| Control | GPT-6-astra | 90.0 | 90.0 | 96.7 | 86.7 |
| Control | Gemini 3.1 Pro preview | 90.0 | 76.7 | 80.0 | 73.3 |

The final column is one shared post-feedback layer, not a fourth independent reviewer. All columns use the fixed case denominators and equal participant weighting. Differences are descriptive stage sensitivity, not an estimated causal effect of one clarification.

### Supplementary Table S5. Saved report length

| Cohort | Model | Reports | Median whitespace units | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- |
| Stroke | Claude Opus 5 | 25 | 2049.0 | 1909 | 2419 |
| Stroke | GPT-6-astra | 25 | 818.0 | 765 | 910 |
| Stroke | Gemini 3.1 Pro preview | 25 | 761.0 | 657 | 936 |
| Control | Claude Opus 5 | 10 | 1992.0 | 1881 | 2265 |
| Control | GPT-6-astra | 10 | 803.5 | 759 | 810 |
| Control | Gemini 3.1 Pro preview | 10 | 712.5 | 696 | 867 |

Counts use Python str.split() on the hash-verified blinded report text, including Markdown. They are neither provider tokens nor a validated measure of verbosity or quality. This analysis was added after unblinding; no length-adjusted outcome or new inferential test was specified.

### Supplementary Table S6. Post-hoc AC1 from original independent ratings

| Pair | Cohort | Domain | Assessed / planned | AC1 | Participant-bootstrap 95% CI | Constant observed label |
| --- | --- | --- | --- | --- | --- | --- |
| rater1 / rater2 | Stroke | case_requirements | 357/357 | 0.953 | 0.930 to 0.972 | No |
| rater1 / rater2 | Stroke | G03 | 75/75 | 1.000 | 1.000 to 1.000 | Yes |
| rater1 / rater2 | Stroke | any_error | 65/75 | 0.660 | 0.492 to 0.817 | No |
| rater1 / rater2 | Control | case_requirements | 90/90 | 0.853 | 0.773 to 0.927 | No |
| rater1 / rater2 | Control | G03 | 29/30 | 1.000 | 1.000 to 1.000 | Yes |
| rater1 / rater2 | Control | any_error | 29/30 | 0.295 | -0.030 to 0.647 | No |
| rater1 / rater3 | Stroke | case_requirements | 357/357 | 0.942 | 0.913 to 0.965 | No |
| rater1 / rater3 | Stroke | G03 | 75/75 | 1.000 | 1.000 to 1.000 | Yes |
| rater1 / rater3 | Stroke | any_error | 54/75 | 0.542 | 0.329 to 0.729 | No |
| rater1 / rater3 | Control | case_requirements | 90/90 | 0.868 | 0.812 to 0.919 | No |
| rater1 / rater3 | Control | G03 | 29/30 | 1.000 | 1.000 to 1.000 | Yes |
| rater1 / rater3 | Control | any_error | 29/30 | 0.199 | -0.206 to 0.608 | No |
| rater2 / rater3 | Stroke | case_requirements | 357/357 | 0.947 | 0.914 to 0.974 | No |
| rater2 / rater3 | Stroke | G03 | 75/75 | 1.000 | 1.000 to 1.000 | Yes |
| rater2 / rater3 | Stroke | any_error | 60/75 | 0.765 | 0.614 to 0.886 | No |
| rater2 / rater3 | Control | case_requirements | 90/90 | 0.914 | 0.863 to 0.963 | No |
| rater2 / rater3 | Control | G03 | 30/30 | 0.966 | 0.895 to 1.000 | No |
| rater2 / rater3 | Control | any_error | 30/30 | 0.740 | 0.597 to 0.882 | No |

Coverage retains three nominal categories; error status retains two. Intervals resample participants, not individual ratings. A constant observed label produces AC1=1 and a degenerate interval, which cannot establish discrimination between categories. These estimates complement Table 5 without changing exclusions or judgments.

See [Supplementary methods](SUPPLEMENTARY_METHODS.md) and the [TRIPOD-LLM reporting checklist](../reporting_checklist_v1/TRIPOD_LLM_CHECKLIST.md). The checklist includes unresolved author declarations and does not assert complete compliance.

## References

- [1](https://doi.org/10.1186/s12984-019-0487-y) Srivastava S, Patten C, Kautz SA. Altered muscle activation patterns (AMAP): an analytical tool to compare muscle activity patterns of hemiparetic gait with a normative profile. Journal of NeuroEngineering and Rehabilitation. 2019;16:21.
- [2](https://doi.org/10.1038/s41597-023-02767-y) Van Criekinge T, et al. A full-body motion capture gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors. Scientific Data. 2023;10:852.
- [3](https://doi.org/10.1038/s41586-023-06291-2) Singhal K, et al. Large language models encode clinical knowledge. Nature. 2023;620:172-180.
- [4](https://doi.org/10.1038/s41591-024-02855-5) Van Veen D, et al. Adapted large language models can outperform medical experts in clinical text summarization. Nature Medicine. 2024;30:1134-1142.
- [5](https://doi.org/10.2196/72153) Kocaman V, Kaya MA, Feier AM, Talby D. Clinical Large Language Model Evaluation by Expert Review (CLEVER): Framework Development and Validation. JMIR AI. 2025;4:e72153.
- [6](https://arxiv.org/abs/2604.05360v2) Nguyen KTN, et al. OGA-AID: Clinician-in-the-loop AI Report Drafting Assistant for Multimodal Observational Gait Analysis in Post-Stroke Rehabilitation. 2026. arXiv:2604.05360v2. Cited arXiv version; the record identifies the work with the 2026 CV4Clinic CVPR Workshop Proceedings.
- [7](https://pubmed.ncbi.nlm.nih.gov/9020824/) Hodges PW, Bui BH. A comparison of computer-based methods for the determination of onset of muscle contraction using electromyography. Electroencephalography and Clinical Neurophysiology. 1996;101(6):511-519. PMID:9020824.
- [8](https://doi.org/10.1016/j.gaitpost.2009.05.020) Baker R, et al. The gait profile score and movement analysis profile. Gait & Posture. 2009;30(3):265-269.
- [9](https://doi.org/10.1080/01621459.1987.10478410) Efron B. Better Bootstrap Confidence Intervals. Journal of the American Statistical Association. 1987;82(397):171-185.
- [10](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) SciPy. Bootstrap confidence intervals, including paired resampling and BCa. Technical documentation. Accessed September 25, 2026. Cited for methodological context; local code produced the saved estimates.
- [11](https://doi.org/10.1093/biomet/26.4.404) Clopper CJ, Pearson ES. The use of confidence or fiducial limits illustrated in the case of the binomial. Biometrika. 1934;26(4):404-413.
- [12](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm) National Institute of Standards and Technology. Exact binomial confidence limits. Dataplot Reference Manual. Accessed September 25, 2026.
- [13](https://doi.org/10.1177/001316446002000104) Cohen J. A coefficient of agreement for nominal scales. Educational and Psychological Measurement. 1960;20(1):37-46.
- [14](https://pubmed.ncbi.nlm.nih.gov/2348207/) Feinstein AR, Cicchetti DV. High agreement but low kappa: I. The problems of two paradoxes. Journal of Clinical Epidemiology. 1990;43(6):543-549. doi:10.1016/0895-4356(90)90158-L.
- [15](https://doi.org/10.1348/000711006X126600) Gwet KL. Computing inter-rater reliability and its variance in the presence of high agreement. British Journal of Mathematical and Statistical Psychology. 2008;61(Pt 1):29-48.
- [16](https://doi.org/10.1016/j.mex.2023.102212) Vach W, Gerke O. Gwet's AC1 is not a substitute for Cohen's kappa: A comparison of basic properties. MethodsX. 2023;10:102212.
- [17](https://doi.org/10.1136/bmj-2024-083305) The CHART Collaborative. Reporting guidelines for chatbot health advice studies: explanation and elaboration for the Chatbot Assessment Reporting Tool (CHART). BMJ. 2025;390:e083305.
- [18](https://doi.org/10.1038/s41591-024-03425-5) Gallifant J, et al. The TRIPOD-LLM reporting guideline for studies using large language models. Nature Medicine. 2025;31:60-69.
- [19](https://doi.org/10.1038/s41591-022-01772-9) Vasey B, et al. Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI. Nature Medicine. 2022;28:924-933.

## Declarations requiring author completion

The institutional ethics determination for this secondary analysis, author affiliations and contributions, funding, competing interests, and the final data/code release statement remain to be supplied by the authors. The original dataset's approvals do not constitute an approval or exemption for this project. The recorded human expert judgments must not be described as newly signed through manuscript preparation. The role of AI-assisted drafting, software development and source auditing should be described accurately in the journal's required disclosure, without assigning such tools authorship or decision authority. See AUTHOR_CONFIRMATION.md.
