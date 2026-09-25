# Project maturity review

Implementation update: the subsequent [follow-up](IMPLEMENTATION_FOLLOWUP.md) records the completed fixture repair, clean-environment numerical replay and manuscript additions. The findings below describe the original audit state and remain preserved.

## Overall judgment

This is a technically substantial, traceable internal comparative study that is ready for manuscript completion. It is not yet a publication-ready reproducibility release, and its evidence does not establish clinical effectiveness or general model superiority. Within the audited computational chain, no discrepancy was found that requires discarding the completed experiment or regenerating reports.

The strongest contribution is a case-specific evaluation of completeness and evidence fidelity under explicitly limited inputs. The most consequential remaining work concerns transparent reporting of the rating stages, packaging for independent reproduction, and author-owned submission information. More files or repeated requests for expert agreement would not address those needs.

All three raters are human experts and made their original judgments independently, as confirmed by the study lead. This audit did not rescore reports, alter individual interpretations or create new human decisions.

## Scope and verified evidence

| Check | Observed result | Boundary |
| --- | --- | --- |
| Source structure | 112 Python files parsed without syntax errors; core feature, generation, rating, analysis and manuscript paths inspected | Not a line-by-line certification of every historical script |
| Offline tests | 259 passed; three legacy single-attempt tests failed | Full suite completed; no clean-environment installation or live API evaluation |
| Feature reproduction | All 35 selected cases and 3,302 saved numeric fields matched recomputation | Uses the SHA-verified released-curve/event cache |
| Direct source comparison | 100 stroke side-trials, 1,100 arrays matched the released stroke Excel | Control Excel and processed MAT were not freshly reloaded in this audit |
| Frozen rating layer | 105 reports, 35 participants, 552 coverage rows and 68 issue groups verified | Checks administrative and arithmetic consistency, not clinical truth |
| Quoted evidence | Every frozen group anchor and its per-rater quotations matched the saved report | Matching a quote does not settle an ambiguous interpretation |
| Main analysis | Recomputed estimates matched the saved results exactly | Same defined estimands and computational modules; separate integer/count checks were also performed |
| Original-stage sensitivity | All three original independent analyses matched the saved results exactly | Kept distinct from later discussion and targeted overlays |
| Model-visible input | All 35 saved prompt pairs matched the formal plan; three models shared each case's exact input | No new generation |
| Registered source checks | 128 freeze references, 119 consolidation references, 33 manuscript source/output references and 16 sensitivity references matched | Counts include repeated references across records |

The source Excel hash was `905512c4deb0f90d54d01032f577446886280d6a6f8b6ead9c7096aab1ad16dd`. The frozen outcome SHA-256 remains `9cf006f23d5660118f5ac4da9e631e68645fa17686a0742841e267e616ca9167`.

The 52 confirmed groups and 16 Pending groups reproduce the report-level accounting. Pending was not silently scored as either correct or erroneous. Shared category labels were not invented where personal tag proposals differed.

The three stage records retain 30, 30 and 45 reports, respectively: 105 dispatches, no retries, no refusals and no token-limit finishes. This audit inspected stage records and report hashes, not every low-level historical streaming event.

## Findings that should be addressed before submission

### P1 — Make the interpretation-rule timeline and its effect on coverage explicit

The primary outcome is based on the post-feedback layer. [D01-D03](../three_rater_review_v1/DISCUSSION_RULES_LOG.json) were recorded after the original independent submissions. They concern substantive versus numerical coverage, ordered lists, and clinical questions. The [manuscript](../manuscript_v1/MANUSCRIPT.md) already discloses later clarification in general, but its coverage-definition paragraph can be read as a single uniformly fixed rule applied throughout.

The distinction matters empirically. Stroke full coverage for Gemini was 93.8% for original rater1, 86.0% for original rater2 and 86.53% for original rater3; the frozen post-feedback estimate is 81.8%. The corresponding original-to-frozen Claude values were 98.0%/96.4%/99.2% to 98.2%, and GPT 97.0%/95.2%/99.2% to 97.0%. These comparisons do not isolate the causal effect of one clarification: they include the full subsequent review process.

Across both cohorts, rater1's Gemini case-coverage records include 19 Covered-to-Partially-covered transitions. This does not prove biased or invalid scoring. It shows that scoring-stage effects are material and should be easy for readers to see. All original reviewers still placed Claude and GPT above Gemini in mean stroke coverage, but the size of the difference depends on the stage.

**Action:** add one compact, dated workflow/amendment table covering the initial rubric, initial independent ratings, D01-D03 clarification and personal rechecks, discussion, blinded freeze, unblinding, and later targeted review. State which boundaries were clarified when and display original versus frozen coverage alongside the error sensitivity. Preserve the original labels and the pre-unblinding primary layer. Do not seek artificial unanimity or relabel the later reviews as fresh independence.

**Completion criterion:** a reader can identify the applicable rule version, exposure stage and outcome layer without reconstructing several folders.

### P1 — Package a usable offline reproduction route

The code and saved results are internally reproducible in this workspace, as the numerical replay above demonstrates. A repository clone alone is not the complete analysis package. The [repository description](../../REPOSITORY_CONTENTS.md) states this; `.gitignore` excludes `data/rating_packets*/`, while the manuscript generator reads four sources under that ignored tree. The model-analysis entry point also refuses to overwrite an existing analysis and has no separate output-directory argument. That overwrite protection is appropriate, but a documented isolated replay route is still needed.

Cloud-only files caused real execution blocks. A first multiprocessing test run waited on dataless Python bytecode and reached a timeout; using `PYTHONPYCACHEPREFIX=/private/tmp/gait_maturity_pycache` made the cache setting available to child processes. Integration tests then waited on dataless plot assets. This audit restored 52 such PNG files from the existing self-contained reviewer ZIP, each verified against its frozen plan SHA-256 before atomic replacement. No image was regenerated or changed. The complete suite subsequently finished with 259 passes and three reproducible legacy-plan test failures described below. The unavailable control Excel was not represented as freshly verified.

**Action:** prepare a versioned analysis-only release containing the allowed inputs, frozen outcomes, required identity join for a post-unblinding researcher release, original-stage outcomes or permitted deidentified ratings, dependency specifications and a command that writes to a new directory. Keep the existing research record immutable. Exclude credentials and distribute reviewer packets separately. Test this release in a clean environment without API calls and compare its output tables with the saved values. Provide explicit source-data retrieval and hash instructions for reproducing feature extraction.

**Completion criterion:** a second machine can reproduce the manuscript tables from documented inputs, without the original Desktop path, cloud placeholders, credentials or regenerating reports. Final release/license and expert-record sharing scope remain author decisions.

### P1 — Resolve the legacy test fixture versus immutable-plan mismatch

The full suite completed in 61.16 seconds with **259 passing tests and three failures**, all in `tests/test_full_length_once.py`. The failures are both parameterizations of `test_only_one_call_per_provider_even_after_failure_and_resume` and `test_unsigned_run_never_loads_credentials`.

`scripts/run_full_length_once.py:26` compares the saved historical parent plan with a freshly constructed plan. Comparing the two objects shows one differing field: the SHA-256 for `src/llm/formal_release.py` changed from `f4145b5287641faf7bef546484e050732ed17e85c3e040471ae749574160ef15` to `9b1b5e25c3376ebf0896f983f835b42fd1e27b02a01ad0ffac3871c747ed9562`. The current source is incompatible with the earlier immutable execution identity, so the live-protection guard correctly refuses to continue. The unit tests are coupled to that old on-disk artifact and fail before reaching their intended mocked behaviors. There is no evidence here that requests were repeated or credentials accessed.

**Action:** isolate the offline unit fixtures from the historical live plan, and add or retain a separate assertion that changed live-source identity is rejected. Keep the historical plan, source hashes and authorization unchanged. Do not make the suite pass by weakening the guard, rewriting the old hashes or rerunning a paid check. Re-run the affected tests and then the full suite after the fixture change.

**Completion criterion:** all 262 existing tests pass under the supported environment and a changed historical source still fails closed. This audit records the failure; it does not modify source or test logic.

### P2 — Correct the documented setup and distinguish current from historical instructions

The root README still activates a presumed `.venv`, installs loose `requirements.txt` constraints and illustrates the legacy prompt route. Its later "Next steps" section still describes pilot preparation and future formal generation. Those passages do not reflect the completed study, even though the new top-level index does.

The separate repository instructions recommend `requirements.lock.txt` followed by the full test suite. However, tests import `scripts/build_expert_trial_package.py` and `scripts/build_formal_case_review.py`, which import matplotlib; matplotlib is pinned only in `requirements-cards.txt`. A clean installation of the documented base lock does not supply this required test dependency. No fresh-install test was attempted here, so this is a dependency-contract finding, not a claimed observed pip failure.

**Action:** make one supported setup path with an explicit Python version and all test/figure dependencies; label legacy examples and old phase instructions as historical. Add an analysis replay command that is safe to run repeatedly. A continuous-integration workflow would help maintain this, but its absence alone does not invalidate research results.

**Completion criterion:** setup documentation and automated checks refer to the same supported environment and current analysis entry points.

### P2 — Report output length and explain the scope of the error endpoint

An exploratory audit count of whitespace-separated units in the blinded saved reports found:

| Cohort | Claude median (range) | GPT median (range) | Gemini median (range) |
| --- | --- | --- | --- |
| Stroke | 2,049 (1,909-2,419) | 818 (765-910) | 761 (657-936) |
| Control | 1,992 (1,881-2,265) | 803.5 (759-810) | 712.5 (696-867) |

These are descriptive length proxies, not billing tokens, a prespecified endpoint, or evidence that length caused any error. The primary task allowed different output lengths. More text may provide more required explanation and more opportunities for optional unsupported assertions. This tradeoff matters when discussing report quality and clinician reading burden.

**Action:** report length descriptively and discuss that any-error is a report-level endpoint, not an error-per-assertion rate, a harm-severity scale, or a measure of clinical usefulness. The manuscript already states some of these limits; connect them explicitly to output length. Do not retrospectively replace the registered endpoint with errors per word or introduce a post hoc length cap.

**Completion criterion:** readers can distinguish completeness, factual fidelity, verbosity and clinical consequences.

### P1 — Complete the paper and author-owned facts

The current manuscript is explicitly a Methods/Results/Limitations draft. It still needs a research rationale tied to relevant literature, an abstract, a full discussion, a finalized reference list and journal-specific presentation. [Author confirmation](../manuscript_v1/AUTHOR_CONFIRMATION.md) still requests reviewer specialty/qualifications/experience, the actual institutional determination for this secondary analysis, authorship/contributions, funding/conflicts and the data/code release scope. Human reviewer status is already confirmed; it does not substitute for a description of expertise.

**Action:** complete these facts without inventing approvals or dates, select the intended article type, and map the manuscript to an appropriate reporting checklist. [CHART](https://www.bmj.com/content/390/bmj-2024-083305) is a useful reporting framework to adapt to this constrained report-generation study: model identification, prompts, query strategy, evaluation, sample size, analysis and availability need clear reporting. It is not a certificate of methodological validity.

**Completion criterion:** no unresolved author fields; the paper and release explicitly identify what was evaluated and what can be reproduced.

## Design limits that do not require reopening the completed experiment

- **Internal sample:** 25 selected stroke participants and 10 controls support a bounded, exploratory internal evaluation. There is no retrospective power justification or claim of broad representativeness. An external cohort would strengthen a subsequent study, but is not a mandatory repair of the current descriptive research question.
- **One response per configuration/case:** generation stability across repeated outputs and prompts was not measured. State this; do not silently add favorable repeat generations to the current dataset.
- **Reference dependence:** controls contributed to reference/calibration construction, despite self-exclusion in individual comparisons. They are not independent external validation. The [source dataset](https://www.nature.com/articles/s41597-023-02767-y) is appropriate for released gait-feature research; its availability does not make the derived threshold, GPS-like score or pooled comparisons diagnostic tests.
- **Reference standard:** experts assess fidelity to the supplied evidence and task rules. They do not supply independent clinical mechanism ground truth. Two raters helped develop the rules, and the third joined later; both facts are already documented.
- **Uncertainty and ceiling:** near-ceiling coverage for Claude and GPT limits discrimination. Their interval including zero is neither proof of equivalence nor evidence of a difference. Error rankings are more sensitive to reviewer stage than coverage ordering.
- **Joint-success denominator:** the complete-review denominator is prespecified and consistently implemented. Some known failures with other unresolved issues are outside its point-estimate denominator. A supplementary excluded-from-point-estimate count would improve readability; the existing planned-slot bounds should remain.
- **Healthy controls:** the supplement tests interpretation boundaries when group membership is known. Its semantic annotations are not a blinded disease-detection test or clinical false-positive rate. Ten participants leave wide uncertainty.

No additional mandatory rater count is established by this audit. Three independent human raters provide a meaningful design; further raters would not automatically solve rule ambiguity or convert post-discussion agreement into independent reliability.

## Recommended next sequence

1. Freeze the present analytical outcomes and retain all existing disagreements. No new forced full re-rating or report generation is indicated by these checks.
2. Complete the rule-stage timeline and add the concise original-versus-frozen comparison plus descriptive length reporting, with post hoc additions labeled.
3. Repair the legacy offline test fixtures without changing live guards; assemble and test the offline reproducibility package and align setup instructions.
4. Obtain the outstanding author information and complete the manuscript and reporting checklist.
5. Consider new cases, repeated generations or an external validation study only as separately specified future work if broader claims are desired.

## Audit limits

This was a review of the full research chain and its key active artifacts, not a new clinical assessment of all 105 reports, a full raw-signal acquisition audit, a clean-system installation or a forensic review of every archived stream event. Original-language archives were not searched. No live model requests, model substitutions, score changes or numerical-analysis overwrites were made. Existing manuscript artifacts were left unchanged. Git publication was not performed; the local Git index was cloud-only during inspection.

Machine-readable evidence, including the exact image restoration list and registered integrity checks, is in [EVIDENCE.json](EVIDENCE.json).
