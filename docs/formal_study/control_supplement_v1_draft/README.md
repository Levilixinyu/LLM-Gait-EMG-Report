# Healthy-control supplementary evaluation: design proposal

Prepared: 2026-09-18. Status: **draft design extension**.

The user agreed to including healthy controls as a separately reported supplementary evaluation. In response to the subsequent question about rigor, the recommendation is **40 control participants**, alongside the existing **25-participant stroke planning pool**. This is an agent recommendation for review, not a recorded sample-size approval, expert signature, final selection or batch authorization.

Open [Control_supplement_design_review.xlsx](Control_supplement_design_review.xlsx) to compare options and record decisions. No review decisions are prefilled. The already approved v3.1 interpretation instructions, rubric v2 and historical trial records remain unchanged.

## Why propose 40 controls?

The proposed planning objective is a roughly 15-percentage-point maximum half-width for a single model's binary control-report outcome at 95% confidence. This tolerance is a proposed practical tradeoff, not a clinical standard or an expert-approved acceptable error rate. The unknown event proportion is conservatively set to 0.5 for planning.

Under the Wilson calculation, the half-width at p = 0.5 is `z / (2 * sqrt(n + z^2))`, where z = 1.9599639845. The smallest integer n reaching 0.15 is 39; 40 is the rounded planning recommendation. These calculations assume independent equal-probability Bernoulli outcomes. They are approximate planning illustrations for this internal case evaluation, not a paired-model power calculation or a design-based finite-population analysis. Method: [NIST proportion confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

| Controls | Approximate maximum 95% Wilson half-width | Added reports per model | Added reviews per rater | Total reviews per rater, including 25 stroke cases |
|---|---:|---:|---:|---:|
| 20 | 20.1 percentage points | 20 | 60 | 135 |
| 30 | 16.8 percentage points | 30 | 90 | 165 |
| **40 (recommended)** | **14.8 percentage points** | **40** | **120** | **195** |
| 50 | 13.4 percentage points | 50 | 150 | 225 |
| 98 (entire current candidate pool) | 9.7 percentage points | 98 | 294 | 369 |

Forty controls plus 25 stroke cases would produce 195 reports for three models and one response per case-model, with 390 independent rating assignments across two raters. The 390 assignments are not 390 independent participants. At an illustrative 15-30 minutes per report, the control component alone adds 30-60 hours per rater. This excludes case-card preparation, training and reconciliation; no actual reading-time estimate has been measured here.

Thirty controls are a possible resource-constrained alternative, but their broader uncertainty must be accepted explicitly. Increasing to 50 provides a smaller precision gain than increasing from 20 to 40. Neither 40 nor 50 guarantees adequate power for small differences between models. The study should report the resource constraint and the precision it permits, rather than call an available count automatically sufficient. See [Lakens, Sample Size Justification (2022)](https://doi.org/10.1525/collabra.33267).

The workbook also gives an exact one-sided 95% upper bound if zero events are observed: `1 - 0.05^(1/n)`. For 40 independent observations this is approximately 7.2%. Zero observed errors therefore would not prove absence of errors, and this scenario is neither a pass criterion nor a reason to stop early. See [NIST exact binomial limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).

The interval examples concern a hypothetical broader case-generating process. Random sampling without replacement from the 98-case pool is a finite-population design; estimating that pool's fixed outcomes would require its own design-based uncertainty calculation. Neither approach removes reference reuse, cohort-selection limits or model-generation uncertainty. Using every available control would still not create external clinical validation.

## Cohort roles and scope

| Component | Proposed role | Important limit |
|---|---|---|
| Stroke planning pool | Main evaluation of faithful description, coverage and unsupported interpretation | 25 complete-EMG P-side cases; external exposure history and final selection remain pending |
| Healthy controls | Supplementary evaluation of unsupported pathological and normal-function inferences | Internal reference-used, complete-EMG, pooled-side cases; not an independent external validation cohort |
| Previously used controls | Development and historical evidence | Control Sub10, Sub49, Sub93 and Sub98 are excluded from the new candidate pool |
| Missing-EMG or deliberately extreme cases | Optional separately labelled challenge studies | Not silently added to the randomly selected complete-EMG control group |

The approved inputs explicitly disclose the participant group. This is interpretation given known group information, not a blinded disease-detection task. Sensitivity and diagnostic specificity are not proposed endpoints. Healthy-group membership does not prove every measurement or function is normal. Stroke and control results will be reported separately; do not inflate the apparent stroke sample size or present a pooled headline rate whose value depends on an arbitrary group mixture.

## Proposed endpoints and coding boundaries

The proposed **main stroke endpoint** remains the per-model proportion of assessable reports containing at least one confirmed case error under rubric v2. It is a proposal, not an already approved outcome definition. The **primary supplementary control endpoint** is narrower: the proportion containing at least one confirmed unsupported pathological inference OR unsupported normal-physiology/function inference. The denominator is the assessable report count for that model in the respective cohort, with technical failures, missing ratings and unresolved adjudications accounted for separately.

Two semantic flags would be added to confirmed control issues:

- `unsupported_pathological_inference`: asserting disease, pathology, clinical dysfunction, mechanism or clinical severity beyond the supplied evidence.
- `unsupported_normal_function_inference`: asserting normal physiological timing, function or overall gait based only on group membership or descriptive reference comparisons.

These flags supplement existing error categories; they do not replace rubric decisions or create severity weights. An E02, E04, E05, E06 or E07 tag alone is not sufficient to assign either flag: the actual quoted assertion must meet the definition. Experts must confirm these additional coding rules before reviewing new model outputs. Repeated claims use the existing issue-group rules; a report containing both flag types counts once in their union and once in each separate component. Component percentages therefore need not add to the union percentage.

| Synthetic assertion | Proposed treatment |
|---|---|
| The participant belongs to the control cohort. | Supported group description, not proof of normal physiology |
| The supplied GPS-like score is below the stated pooled p95. | May be a supported descriptive comparison if the supplied numbers establish it; not itself a normality claim |
| These deviations establish pathological muscle dysfunction. | Pathological-inference flag if unsupported by the available evidence |
| The supplied envelope deviations establish moderate spasticity. | Pathological-inference flag for an unsupported clinical severity/mechanism claim |
| The CCI lies within the empirical interval, proving normal co-activation. | Normal-function-inference flag; separate the supported comparison from the unsupported conclusion |
| Muscle activation timing is physiologically normal. | Normal-function-inference flag when matching timing evidence is unavailable |
| The deviation cannot establish pathology or overall normality. | Appropriate limitation, but does not replace required factual findings |
| Could additional history or measurement review explain this difference? | A non-presupposing question is not automatically an error |

These examples do not reopen the approved X32 degree-word rule or historical adjudications. Merely describing a difference in a control is not an error. Conversely, a generic cautious report may avoid unsupported inferences while omitting important findings. Report the following secondary outcomes alongside the primary supplementary endpoint:

- Each semantic flag separately, and the broader proportion with any confirmed rubric case error.
- Required-item coverage, keeping Covered / Partially covered / Not covered distinct; do not assign an unapproved 0.5 score to partial coverage.
- Confirmed issue-group counts per report, with no duplicated counting for multiple tags on the same claim.
- Reference-limitation coverage, unresolved assessments, technical failures and independent-rater disagreement.

Final coverage aggregation across cases, uncertainty intervals and model comparisons belong in the prospective analysis specification. Both-rater independent records must be retained; final consensus is not evidence of initial inter-rater agreement. The same participants must be used for all models and comparisons must preserve pairing. Repeated model runs, if later added, do not add new participants.

## Candidate pool and sampling proposal

The [candidate inventory](control_candidate_pool.csv) contains 98 controls with seven complete EMG means, four complete sagittal kinematic means, and no pilot/spot-check report in the current inventory. Their previous participation in reference/calibration construction is explicitly recorded. External case-use history remains unconfirmed. This inventory does not represent a final list of selected controls.

The proposed sampling procedure is:

1. Complete external exposure checks using objective recorded criteria, without viewing new model responses. Document exclusions and freeze the remaining candidate file and its hash.
2. Agree the sample size and uncertainty/resource rationale before sampling. If the eligible pool shrinks below the agreed size, revise the design transparently rather than silently substitute ineligible cases.
3. Sort group-qualified participant identifiers, register a random seed and the sampling implementation/version, and draw a simple random sample without replacement. Archive the draw, pool hash, ordered reserve list and all exclusion/replacement reasons. No draw or seed has been registered in this draft.
4. Do not select or reject subjects because of model performance, a preferred physiological pattern or observed error rates. Technical ineligibility discovered later follows the prespecified replacement rule; difficult valid cases remain included.
5. Describe the selected sample's age and published-speed distribution without claiming clinical matching. Do not repeatedly redraw until the sample looks favorable. If age-stratified sampling is scientifically preferred, define the strata, allocation and weighting before the draw instead of changing the procedure afterwards.

Administrative age and published bilateral speed have not been added to model inputs. The approved control contract still determines what the model sees. Control `avg` curves pool contributing sides and do not establish a paretic side or permit stroke-specific asymmetry requirements. Reviewers must not demand facts only visible in administrative metadata or reference-only plots.

## Reference use and release checks

Retain the approved v3.1 interpretation contract. Before freezing each selected control input, verify that its own curves are excluded from its mean/SD reference under the intended leave-one-out implementation, record effective reference counts and distinguish those reference curves from pooled calibration distributions. The calibration distributions have previous cohort contributions and are not independent matched limits. This proposal has not created or verified any new case inputs.

Do not silently recompute a different calibration/reference system under the same approved input version. A fully separate reference/evaluation split would be a different design requiring refreshed derived inputs, interpretation checks and case requirements; splitting now would not erase previous development exposure. The present proposal accepts and reports the internal reference-use limitation.

## Steps before generation

1. Confirm the recommended size or a justified alternative with study leadership and rater capacity. Forty controls is proposed, not selected.
2. Confirm the new endpoint flags and finalize participant-level analysis, adjudication and technical-failure/retry rules. Failed or unresolved outcomes must not be silently treated as error-free or dropped until the desired count is reached. A faithfully captured poor or incomplete response remains assessable under the approved rubric when its materials are valid.
3. Freeze eligibility, draw the sample, prepare model-visible inputs and new case-specific requirements, and obtain the appropriate expert confirmation. Do not copy control Sub49's numerical checklist into new controls.
4. Freeze the generation and rating packages, preserving model blinding for raters while keeping the known cohort information in the approved input. Only then proceed to a separately authorized batch.

The linked [rubric approval record](../rubric_v2_draft/APPROVAL_STATUS.md) explicitly limits its approval to the rubric and five-case annex; it does not approve new samples, endpoints, statistical analysis or batch generation. The new workbook records proposed decisions without changing that approval scope.

## Reproduction and evidence

- [Review workbook](Control_supplement_design_review.xlsx): eight role-labelled design decisions, sample-size options and the candidate inventory.
- [Sample-size calculations](sample_size_options.csv): reproducible reference calculations, workload scenarios and pending decisions.
- [Design record](design_record.json): source hashes, calculation assumptions and no-selection status.
- [Manifest](manifest.json): hashes and validation for this package.

The script creates the workbook, CSVs and design record in a new directory; this explanatory README and final package manifest are maintained separately:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/prepare_control_supplement_design.py --out /private/tmp/gait-control-design-recheck
```

The builder refuses an existing output directory, reads no private model mappings or archived originals, and calls no model APIs. Existing candidate, rubric and sample-ledger files are hash-checked and preserved. All newly written project material is English.
