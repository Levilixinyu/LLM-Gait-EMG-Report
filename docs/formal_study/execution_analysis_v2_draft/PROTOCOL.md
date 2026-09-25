# Execution and analysis plan v2 — proposal for confirmation

Status: **Targeted revision awaiting confirmation; no formal API generation authorized or performed.** Both experts accepted D02 and D07 in v1. Section 6 below incorporates rater1's exact D04 correction and rater2's relevant examples for both experts to confirm. Rater1 capacity remains pending; rater2's schedule is conditional. Study-lead decisions remain pending. No finalized case requirement has changed.

## 1. Study question and fixed material

Compare how completely and correctly three model configurations describe supplied gait/EMG evidence in 25 stroke cases. Ten healthy controls form a separate exploratory supplement. This is a within-participant comparison of reports, not a diagnostic accuracy or clinical deployment study.

The user selected the 25+10 allocation and on 2026-09-18 confirmed, after checking, that there was no additional use outside the registered project history for all 35 selected participants. No membership change is indicated by that attestation; see `../execution_analysis_v1_draft/exposure_confirmation.json`. The stroke pool is a conservatively selected internal pool, not a random population sample. Controls were drawn using the registered seed/order and have contributed to reference/calibration construction. Leave-one-out reference calculation does not make them an external validation cohort. All 35 cases have now been inspected for case-specific requirements; call them prospectively specified evaluation cases, not untouched cases.

Use the exact saved system/user inputs from `case_review_v1`, interpretation version `limited-evidence-v3.1-candidate`, the approved rubric in `rubric_v2_draft` with its approval record, and `case_requirements_v1`. The old five-case rubric annex is developmental and must not be copied into these new cases. No plots, expert answers, requirements or review comments are supplied to the models.

## 2. Sample exposure and membership

Record known additional participant use outside the local inventory: report generation, case-specific prompt tuning, rubric development or individually targeted analysis. The current registered case-card and requirement-review work is disclosed development of the evaluation instrument, not an undisclosed extra exposure.

The study lead may provide one explicit, dated attestation covering all 35 listed participants if it accurately reflects known history. Alternatively complete the Exposure review sheet. A blank response remains unknown. An attestation of no additional known use is not a claim of an exhaustive search of every possible external system.

If additional use is disclosed, record its date, purpose and whether outputs influenced prompt/rubric decisions. Apply the existing eligibility policy before generation. A control replacement must be the next eligible participant in the existing registered order; do not redraw. Any replacement needs its own exact input and expert requirements before generation. Stroke exclusions require a documented design amendment; do not silently recruit previously exposed cases. No substitution is allowed because a valid output is poor.

## 3. Unit, volume and rating burden

Plan one response per case and model: 35 x 3 = **105 report slots**, consisting of 75 stroke and 30 control reports. Each of two raters independently reviews every available report: up to **210 report-rating assignments**. One response per configuration cannot estimate within-model generation variability.

There are 119 included stroke case requirements and 30 included control requirements. Across three models that gives 447 case-coverage rows per rater. The proposed application of common G03 once per report adds 105 rows, for **552 coverage judgments per rater, 1,104 across both raters**, plus issue review, format checks and reconciliation. Expert capacity must be confirmed against this workload; 210 assignments are not 210 independent participants.

## 4. Primary outcome: full coverage of case-specific requirements

For participant i and model m, let K_i be the number of included case-specific requirements in the frozen list. Define C_im = number finally labeled Covered / K_i. Report it as a percentage. K_i is fixed across models: 4–6 in the current stroke sample and 3 for every selected control. An OR requirement remains one requirement; components are not extra denominator items.

The primary estimand is the mean C_im across stroke participants, with every participant weighted equally. Compare models using within-participant differences in C_im. This is a full-coverage proportion, not an overall quality score or a clinical usefulness score.

Covered, Partially covered and Not covered remain separate labels in the data. Only Covered enters the full-coverage numerator; partial coverage is not converted to 0.5. Also show all three category frequencies and report-level proportions, so meaningful partial content is visible. Omitted candidates are not in K_i. No additional error deductions or importance weights are added.

Common G03 is a separate outcome, not an extra item in the primary denominator. It requires a meaningful comparability limitation AND its inference limitation. Propose applying it once to each of the 35 reference-bearing tasks, consistent with the common rule and the confirmed control requirements. The same sentence can support both a case speed item and G03; no repeated disclaimer is needed. Confirm this extension explicitly in review item D02.

## 5. Correctness and other secondary outcomes

For each report, record the presence of at least one finally confirmed in-scope case error under E01–E09 and the number of unique confirmed issue groups. Multiple tags and repeated locations do not multiply a group. Optional statements can be wrong even when their absence carries no coverage penalty. Pure design concerns and format problems stay separate. A contradiction can coexist with correct coverage, as specified by the approved rubric.

Report the fraction of evaluable reports with any confirmed case error, the issue-count distribution, categories and exact denominators. Do not call this a per-assertion error rate: the number of assertions has not been systematically enumerated. Do not give an issue more weight because it has more category tags. Pending issues are not confirmed errors, and no severity-weighted score is proposed.

Also report G03 coverage, the partial/not-covered distributions, four-section format compliance, truncation/refusal flags and technical delivery. As an explicitly secondary joint measure, report the fraction with every case requirement Covered AND G03 Covered AND no confirmed case error, only when all reviews are complete. This is an operational description, not a clinical usability or safety certification. No new subjective usefulness scale is introduced.

## 6. Healthy-control supplement

Analyze the ten controls separately using the same coverage and error rules. Additionally propose two nonexclusive semantic flags, each requiring a confirmed in-scope issue and an exact quote:

- **Unsupported pathological inference:** the report asserts a disease, pathological deficit/mechanism or clinical impairment unsupported by the supplied evidence. A mean-relative deviation, threshold statistic or qualified assessment question alone does not trigger the flag.
- **Unsupported overall normality/function inference:** the report asserts normal physiology, normal timing/function or overall normal gait from insufficient evidence. Healthy-group membership, an in-range CCI or a low composite value alone does not establish these conclusions. Correctly stating membership or a displayed comparison does not trigger the flag.

The flags add descriptive labels to existing confirmed issue groups, not new errors or extra penalties. One report may trigger both.

Determine each semantic flag separately. A flag is positive once at least one confirmed in-scope issue satisfies its definition, even if another potentially qualifying issue remains pending. A flag is negative only after a complete issue review finds no confirmed or pending issue qualifying for that flag. Otherwise it is indeterminate. A pending issue relevant only to the other flag does not make this flag indeterminate once this flag has been fully assessed.

A control EMG route-C statement that all seven displayed max |z| values are below the supplied 3.65 endpoint is a displayed-value comparison and does not itself trigger the normality flag. A question presupposing an unsupported clinical deficit is assessed as an assertion under the existing rubric; the pathology flag for that presupposition requires a confirmed E02 issue, not question syntax alone. Other flag-qualifying assertions remain assessed under their applicable existing error categories. No new mandatory report content, error category or penalty is introduced.

Both experts must confirm this revised operational wording before use. Rater2's v1 approval is not approval of the changed wording. Do not label their proportions diagnostic false-positive rates, sensitivity or specificity.

## 7. Independent review, disagreements and blinding

Use the two original independent reviews to describe agreement; use a separately documented final adjudicated set for outcome estimates. Preserve all original labels, quotes and timestamps. Raters cannot see each other's responses until independent completion. If discussion cannot resolve a content judgment, a named human third reviewer adjudicates while blinded to model identity. Agent suggestions do not create human decisions.

Blind provider identity, model identifier, request metadata, timing and generation order in reviewer packets. Assign a separate opaque ID per report; do not use a shared visible model code that links one model's reports. Case data must remain accessible to assess factual support. Do not paraphrase outputs to hide style or remove self-identifying prose; record incidental unblinding if it occurs.

Generate and save the private mapping and independent rater order seeds only at packaging time, before ratings, in the established ignored private location. Do not expose mappings in this plan, its public manifests or rater packets. Separate the three reports for the same case by at least two other reports in each rater's order; preserve the precomputed order across sessions. No output-content-based ordering is permitted. Log administrative replacements of corrupted files without changing report content.

Coverage agreement: provide a three-category cross-tabulation, raw agreement and unweighted Cohen's kappa for jointly assessable, non-pending item rows, separately for case requirements and G03 and separately by cohort. Cannot assess and Pending are accounted for outside this agreement denominator. Kappa is undefined if its denominator is zero; report it as such. These are descriptive item-level agreement summaries, not an independent item sample. For error detection, compare each rater's completed report-level any-error flag. Do not compute issue-level kappa over an artificially expanded universe of errors that neither rater identified. No agreement claim is based on the reconciled set.

## 8. Analysis and uncertainty

The primary analysis uses the same stroke participants with complete final case-coverage assessment for all three model reports. If all material is available, n=25. Publish the exact included case list and exclusions. Never use different model-specific subsets to present an apparently paired comparison. Show all available per-model results separately as supplementary descriptions.

For each of the three model pairs, form each participant's full-coverage difference and estimate its mean in percentage points. Resample participants with replacement, keeping all model observations and item structure together. Proposed implementation: 20,000 BCa bootstrap resamples, paired by participant, deterministic analysis seed 20260918 and sorted group-qualified case order. Use the same stored resample-index matrix for all three contrasts. If fewer than two paired participants are available, do not compute an interval. If the BCa interval is undefined/degenerate, report it as unavailable with the observed data; do not change interval methods after seeing a favorable result.

Show descriptive 95% intervals and, for the family of three primary pairwise comparisons, approximate Bonferroni-adjusted intervals with confidence level 1 - 0.05/3 = 98.3333% per contrast. These are approximate bootstrap intervals, not guaranteed finite-sample bounds. Do not select a winner from unadjusted intervals, search across endpoints for significance or claim equivalence from overlap. No omnibus/pairwise hypothesis-test sequence or additional p-values is proposed. With resource-defined, selected cases, emphasize effect estimates and uncertainty rather than population-wide superiority claims. A coverage advantage alone does not imply better overall interpretation quality if errors are more frequent.

For report-level binary outcomes, provide counts and two-sided 95% Clopper–Pearson intervals within each cohort/model. State the binomial independent-case assumptions and the limits of applying them to this selected internal sample and shared references. For controls with zero qualifying events among ten fully assessed cases, also show the one-sided 95% upper bound, 1 - 0.05^(1/10), about 25.9%. Never pool the 30 correlated control reports to claim n=30 independent controls. Do not bootstrap a zero-event sample and interpret a zero-width interval as certainty. Pairwise binary comparisons are descriptive matched counts/differences without confirmatory testing in this small study.

All secondary outcomes and control results are exploratory; no claims of controlled familywise inference across them. No subgroup analyses by speed, age or muscle, or post hoc power claims, are prespecified. Display per-case observations for transparency without treating their within-case rows as independent replicates. Uncertainty describes variation across cases under the specified assumptions, not model stochastic variability or independently sampled raters.

## 9. Missing material, pending assessments and sensitivity analyses

Administrative missingness is not a model omission. First try to recover the correct saved material without a new generation. Score faithfully captured short, refusal, malformed or truncated text under the rubric, including omissions; do not mark it Cannot assess merely for poor content. An explicit refusal with captured readable text is an output to assess. A response with no report text at all is an operational no-report outcome, not an invented empty expert-rated report.

Unresolved coverage labels or lost output make the report's primary complete score unavailable. Do not reduce K_i to the number of assessed items or recode unknowns as Not covered. Exclude that participant's entire three-model set from the primary complete-triad comparison, disclose the missingness and retain all slots in the generation accounting. This conditional content analysis may be biased when outputs are missing; it must be accompanied by the following all-planned-case sensitivity analysis.

For every planned report, bound full coverage by [known Covered / K_i, (known Covered + unresolved items) / K_i]; an entirely unavailable report has [0,1]. Average bounds over all 25 planned stroke participants. For pair A-B, average the per-case lower_A - upper_B and upper_A - lower_B bounds. These are missingness bounds, not confidence intervals. If unresolved content remains, do not present an all-planned-case point estimate as fully observed.

An any-error flag is known positive once a confirmed error exists, even if another issue remains pending. It is known negative only after a complete issue review with no confirmed or pending in-scope error. Otherwise it is unknown. Report lower/upper proportions counting unknown flags as 0/1 over all planned slots, alongside evaluable denominators. Apply analogous accounting to the two control flags and the secondary joint measure. A delivery failure is neither an error-free report nor a confirmed clinical error.

Show each rater's independent full-coverage results and error flags as a sensitivity description, using the same explicit missingness policy. Do not change the accepted rubric, case requirements or endpoints in response to model output.

## 10. Generation configuration and retry policy

The model strings copied into `plan.json` are **local historical configuration candidates only**, not assertions of current availability, access or immutable model versions. Before freezing the batch, verify the intended provider/model identifiers, account access, exact output limits, timeout behavior, SDK versions and all effective inference settings. Pin snapshots where supported; otherwise disclose alias drift and record returned model identifiers. Never silently substitute a cheaper, newer or differently configured model.

Proposal: retain the existing 8,000-token output-budget setting per provider adapter, with optional sampling/reasoning settings omitted unless an explicitly documented provider requirement dictates otherwise. Equal numeric caps do not guarantee equal visible-output or reasoning budgets. Record each actual request field and whether omitted settings use provider defaults. Any decision to change a cap or reasoning setting must precede formal outputs, have a documented rationale, and be incorporated into a new configuration hash.

Use the exact reviewed system/user pair as the only clinical input; no previous conversation, retrieval, tools, images, expert checklist or feedback. Each slot has one intended generation. Generate in case blocks with a recorded randomized case order and balanced provider ordering, independent of output content. Write the 105-slot manifest, source hashes and schedule before calls. Per-task hard deadline proposal: 600 seconds per attempt, enforced by the adapter. Set or disable hidden SDK retries so the attempt ledger captures all actual requests.

Allow at most three transmitted attempts per slot, and only for transient transport failures, timeouts, HTTP 408/429 or server 5xx responses with no usable captured report. Record each attempt, request identifier if available, error, timestamps and delay. Proposed backoff: 5 seconds then 30 seconds, honoring a longer server Retry-After up to 300 seconds. If a server asks for longer, pause the batch rather than bypass its limit. Authentication, invalid model, malformed request, unsupported parameter or quota/billing configuration errors stop the batch for administrative correction; do not cycle retries. Resolve local validation failures before transmission and do not count them as model responses.

Retain the first usable response, even if clinically poor, cautious, structurally invalid or truncated. Do not continue a truncated response, raise its cap, ask for corrections or choose a preferred response. A successfully completed empty/filtered response is retained as a no-report outcome, not automatically retried for content. If a timeout might have completed remotely, try provider-supported retrieval first; any unresolved retry is labeled a possible duplicate and the first received usable text is retained under the frozen rule.

After allowed transient attempts are exhausted, record technical failure and do not substitute a new participant. Batch resume does not reset attempt counts. Each saved response and attempt is immutable; resumability uses exact task hashes, not filenames alone. Record response model, finish reason, truncation, usage, latency and SDK/request metadata available, excluding secrets. Save all returned text blocks in order and fail validation if extraction would silently discard them.

No live test on these 35 cases is permitted outside the registered slots. Provider-compatibility testing, if later authorized, uses clearly separate synthetic material and does not count as a study report. A live smoke test and the formal batch still require their own concrete authorization.

## 11. Implementation gaps before generation

The existing `call_with_retry` catches all exceptions and lacks an attempt ledger. The current shared runner writes its task manifest after processing and can supersede prior records. The Anthropic adapter extracts only the first text block. These are source-code observations, not new experimental failures. The formal runner must implement the prospective rules above, verify all text extraction, and pass offline tests with simulated failures before use. Do not repurpose the historical five-case runner directly for the new batch.

Other required checks: verify all exact prompt bytes and hashes against the reviewed inputs; source-reference policies and cohort-qualified IDs; 105 unique case/model slots; approved case requirement membership; frozen effective provider configuration; attempt persistence; first-response retention; missing-output accounting; private mapping exclusion from public/rater artifacts; 105 reports or explicit failure slots; and deterministic analysis on synthetic data. No historical output is regenerated for these checks.

## 12. Decision and release sequence

1. Exposure checkpoint completed: the user confirmed no additional known use for all 35 selected participants on 2026-09-18. Preserve the registered membership/draw; any later contrary evidence requires a documented amendment before proceeding.
2. Study lead approves or revises the outcome/aggregation, paired analysis, missingness and retry proposals. A statistical reviewer may be consulted; this draft is not a claim that such a review occurred.
3. Both experts confirm G03 application, the two supplementary semantic flags and their review capacity. They need not repeat the finalized 200-row requirement review.
4. Resolve provider configuration and implement/test the formal runner and review forms offline. Freeze the dated plan, source hashes, task manifest and data dictionary. Unanswered choices remain pending, not default approvals.
5. Present the concrete 105-slot batch configuration, access/cost information available and readiness checks for generation authorization. Then generate, blind, independently rate, reconcile and analyze in that order.

## Method references

The paired-resampling implementation must preserve the same subject indices across model arrays; BCa support and degenerate-data limitations are documented in the [SciPy bootstrap reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). The particular endpoint, resample count and multiplicity family above are study-design proposals, not requirements imposed by that reference.

The binomial calculations follow [NIST exact binomial limits](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm). Those formulas do not remedy nonrandom sampling, reference reuse or unknown exposure. All method choices must be fixed before viewing formal outputs.
