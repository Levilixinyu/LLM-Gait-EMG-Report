# Repeated-generation supplement: all 25 stroke cases

Status: prepared before new outputs, after the original study results were known. The study lead selected all 25 original stroke cases and three additional responses per case and model. Expert capacity, prospective application of the review instructions, and technical/budget release remain to be confirmed. This file does not claim an expert signature, model access check or completed experiment.

## Question and scope

How much do required-content coverage and evidence-fidelity judgments vary across repeated responses to the same gait summary under the same recorded configuration? Include every original stroke case, with no selection based on model performance. Generate 25 x 3 models x 3 new responses = 225 reports. Each model contributes 75 new reports. The original 75 stroke and 30 control reports remain historical evidence. If every new slot yields a report, the project contains 330 reports, including 300 stroke reports, but still only 25 independent stroke participants. No new control generation is planned.

The supplement is exploratory and was designed after seeing the original results. It is not a new external validation set or a remedy for an unvalidated clinical reference. It estimates variability on the existing selected cases. Do not claim a powered sample size, adequate precision for rare errors or population-wide rankings.

## Input and generation

Use the exact original system/user bytes and recorded high/adaptive 16,000-token configuration for each provider. Do not add length constraints, examples, prior reports, expert feedback, case requirements, retrieval or conversational memory. Start each call independently. Temperature and other omitted sampling settings remain omitted; do not introduce a fixed seed that artificially repeats one draw. Record any available returned model version, request identifier, time, usage, finish reason and stream evidence.

PLAN.json specifies every slot, prompt hash and original task. Dispatch three complete waves, each containing one response from each model for all 25 participants. Case ordering is seeded and provider positions rotate, so each provider occupies each position once per participant across the three waves. Operational pauses are allowed and logged; order and output selection cannot depend on report quality.

Verify available model identifiers, installed SDKs and effective requests before release. The original API identifier alone does not establish an unchanged backend snapshot. No silent model substitution is allowed. The primary supplement compares the three new responses with one another. Compare original versus new responses separately and label possible temporal/service drift. Even the new waves can span provider updates; preserve returned metadata and disclose unobservable changes.

Do not reuse the original live runner, authorization or report directory. The planned directory is data/reports_repeatability_v1. New task IDs cannot collide with historical IDs. A dedicated runner must preserve streams durably, validate source/configuration identity on resume, and retain every first usable response. Poor, cautious, malformed, refused or truncated text is not a reason to regenerate. Retries are limited to the original transient transport policy, at most three attempts per slot, with 600-second attempt deadlines. Interrupted ambiguous requests pause for review. No extra clinical-input probe outside the registered slots is included.

## Human scoring

The proposed design uses all three human reviewers independently for all 225 new reports: 675 report-review assignments. Each reviewer has 1,071 case-requirement judgments and 225 separate reference-limit judgments, plus error review. Confirm capacity before generating this workload.

Use the existing 119 stroke requirements, the approved rubric and the substantive D01-D03 clarifications from the outset. Prepare a concise prospective instruction pack before scoring; distinguish agreed general rules from unresolved historical case interpretations. Do not convert any reviewer's preferred reading, later individual decision or historical consensus into an automatic answer key for a new report. Pending remains available. Existing historical case labels are not shown in the new packets.

Use opaque report IDs, concealed provider/repetition metadata and separately randomized reading orders. Separate reports from the same case as far as feasible; distribute manageable batches without showing peer judgments. Collect current model-identity/results exposure and case-familiarity declarations. Prior experience with the cases and rules is expected, so these are new independent judgments on new reports, not ratings by naive reviewers. Do not promise blinding if a reviewer has already seen the identities/results.

Each reviewer retains an independent coverage and error dataset. New first-pass judgments are the primary rating basis for this supplement, reported separately for each reviewer. Later discussion, if undertaken, is secondary and does not overwrite those results or force agreement. No new wording rule may be presented as having preceded scoring if it was created after outputs were inspected.

## Analysis specified before new outputs

For participant i, model m, repeat r and reviewer h, compute full coverage C_imrh as the number of case requirements marked Covered divided by the fixed case-specific K_i. Partially covered receives no fractional credit. Reference-limit coverage remains separate. Report category frequencies as well as binary full coverage. An unassessed or unresolved item is unknown, not a model omission.

The principal repeatability statistic is the participant mean of the absolute difference between each of the three new-response pairs: V_imh = (abs(C_im1h-C_im2h) + abs(C_im1h-C_im3h) + abs(C_im2h-C_im3h))/3. Average V_imh equally across participants within each model and reviewer and express it in percentage points. Also report each participant's three observed scores, range and mean coverage. Zero variability can mean consistently poor reports; always interpret variation with the coverage level.

For each reviewer, report known positive, known negative and unknown any-error status for every new report. Positive means at least one judged in-scope Error; negative requires completed issue review with no Error or Pending; otherwise unknown. Do not call an individual reviewer's Error a unanimous confirmed error. Show error status patterns across the three repeats and the participant-level proportion of discordant response pairs, averaging cases equally. Use complete three-response blocks for observed repeatability summaries, disclose exclusions and retain unknowns in bounds. Never combine positive and Pending states.

Report per-reviewer results side by side; do not average away disagreement or pool 675 assignments as independent observations. Human agreement is a separate endpoint using raw agreement, cross-tabulations and the original pairwise nominal kappa conventions. AC1 may be reported as a predeclared supplementary coefficient for this new stage, alongside kappa and category marginals. Agreement is not correctness.

For each complete-block repeatability statistic use 20,000 percentile bootstrap samples of participants within this stroke cohort, seed 20260925, retaining all models, repeats, items and reviewer labels within each sampled participant. Keep the analysis draws and category definitions fixed. Report 95% intervals as descriptive uncertainty, without confirmatory p-values or superiority/equivalence claims. These cluster intervals describe participant-sample variation conditional on the observed three responses; they do not precisely estimate the full stochastic distribution of future outputs. With fewer than two complete participant blocks, no interval is reported. Constant bootstrap values are identified rather than presented as proof of zero uncertainty.

Report every model's available complete blocks and denominators. Any secondary between-model contrast uses the same participants with complete three-response coverage for both compared models, with equal participant weighting; show all planned-case bounds as a missingness sensitivity. Do not substitute the old response to complete a missing new block. For unknown coverage items, report report-level bounds [known Covered/K_i, (known Covered + unknown)/K_i] and case/model mean bounds across all three planned repeats. For any-error rates, count unknown report states as zero and one for bounds across all 75 new slots per model and reviewer. For repeat-pair discordance, known differing binary states contribute one, known equal states zero, and any pair with an unknown state contributes [0,1]; average all three pair bounds per case and then all 25 cases. Such bounds are not confidence intervals. Coverage-variability bounds need not be inferred from coverage-mean bounds; leave that variability estimate unavailable for incomplete blocks.

Do not calculate ordinary independent-binomial intervals using 75 reports as 75 independent participants. Error-group counts remain report-scoped and unweighted. Report lengths are descriptive, using the existing whitespace-count rule; no per-word correction is claimed to remove length confounding. No new severity scale, composite ranking, subgroup search or best-of-three response selection is introduced.

## Remaining steps before live release

1. Confirm the human scoring arrangement and workload; assemble and review the prospective instructions without new model outputs.
2. Implement a separate bounded runner and verify interruption/resume, first-response retention, transient retry accounting and exact prompt/configuration capture offline.
3. Check current provider access and version information, determine a concrete spending limit and record any service differences. Synthetic checks, if needed, require their own bounded scope; do not spend extra clinical calls outside these 225 slots.
4. Fix the dated supplement and exact execution manifest before dispatch. Record the study lead's concrete execution decision; do not reuse the original batch authorization. The choice of 25 cases has been accepted, but this offline planning file is not a transmitted-call authorization.
5. Generate, blind, independently rate, then analyze with the above definitions. Report deviations and missing outputs without replacing cases or selectively discarding responses.
