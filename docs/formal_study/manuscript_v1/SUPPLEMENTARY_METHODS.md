# Supplementary methods

## Generation and retained evidence

Generation followed a fixed task manifest and case order, with balanced provider order within case blocks. The three batches comprised 10 stroke cases, another 10 stroke cases, and five stroke cases plus 10 controls. Inputs and settings were unchanged. Only transport failures without a usable captured report could trigger a retry; poor content could not. No formal retry occurred. Preliminary technical probes were excluded from the 105-report analysis. Responses and metadata were checked against captured stream evidence. Supplementary Table S1 gives identifiers, settings and generation timestamps.

## Rating records

The blinded outcome dataset was finalized on September 23, 2026 before joining the model-identity mapping. Original independent submissions, personal rechecks and final decisions remain distinct. The final ratings contain 52 confirmed issue groups and 16 unresolved groups. Repeated locations and multiple category tags do not multiply a report-scoped group. The original two-reviewer plan, later third full review, post-rating clarifications and post-unblinding sensitivity review are described in the main Methods because they affect interpretation.

## Inputs, prompts and intended use

The study uses English instructions, numerical summaries and English report outputs. Prompt development included a five-case trial using stroke Sub09, Sub05, Sub50 and Sub47, and control Sub49. The limited-evidence-v3.1-candidate instructions were reviewed before the formal batch; the current confirmation records are in `docs/formal_study/candidate_v3_1/APPROVAL_RECORD.json`. This work did not train or fine-tune the commercial models. The development cases must not be described as external validation. Exact formal system/user prompts and reviewer reference materials are retained in `docs/formal_study/rating_delivery_v1/rater2/materials/`; rubric instructions and worked examples are in `docs/formal_study/rubric_v2_draft/`, with the formal case requirements in `docs/formal_study/case_requirements_v1/`. Post-rating clarifications remain separate from those pre-generation materials.

Provider training corpora, their date ranges and final training dates are not established by the retained study records. A release date or API alias is not a training cutoff, and prior provider exposure to the public dataset cannot be excluded. The original gait measurements were collected at the Multidisciplinary Motor Centre Antwerp (M2OCEAN), Belgium, as described by Van Criekinge et al. (manuscript reference 2). Participant-level collection-date ranges were not reconstructed in this analysis. Token allowances and wall-clock batch dates are recorded, but provider hardware, total compute and comparable inference cost were not measured.

Candidate users are researchers and gait professionals reviewing a numerical summary. The tested workflow was offline expert evaluation, with no autonomous clinical decision or patient-facing use. A clinical input-quality policy, required user training, integration into care, and effects on clinical decisions have not been validated. The study does not estimate demographic fairness or subgroup performance. Missing channels and inapplicable metrics are identified in the supplied materials rather than imputed by the models; source availability limits and reference construction are described in the main Methods.

## Additional agreement analysis

Gwet AC1 was added after unblinding as a sensitivity description of the preserved original independent ratings. It did not replace kappa, select a preferred reviewer or change the final outcomes. The analysis reproduces all 18 original pair/cohort/domain cross-tabulations and retains their exclusions. The categories are fixed at three for case requirements and reference-limit coverage, and two for report-level any-error. No ordinal weights are used and unobserved categories are not dropped.

For q categories, let p_k be the average of the two reviewers' marginal proportions for category k. With observed agreement P_a, P_e = sum_k p_k(1-p_k)/(q-1), and AC1 = (P_a-P_e)/(1-P_e). This comparator differs from Cohen kappa. Identical ratings confined to one category give AC1=1; that result does not show that reviewers distinguish categories correctly. Kappa interpretation bands are not applied to AC1.

We sampled participants with replacement within each cohort, preserving every included report and requirement of each sampled participant and retaining the original pairwise exclusions. We used 20,000 samples, seed 20260925, and shared draws across reviewer pairs and domains. Percentile 95% intervals use NumPy linear quantiles. Point estimates retain the original item/report weighting. Empty replicate tables would be counted as undefined and excluded from interval quantiles; the output records valid and undefined replicate counts. No new ratings were imputed. These intervals do not remove dependence from shared reference construction or make the selected cases a population sample.

The source registry, per-participant contingency tables and summary are in `docs/formal_study/agreement_sensitivity_v1/`. Point estimates were separately checked with exact rational arithmetic. The offline reproduction pipeline independently rebuilds these estimates from reduced exports of the original submissions, alongside the main outcomes. Gwet (2008) defines AC1; Vach and Gerke (2023) explain why it should not be treated as interchangeable with kappa. Full citations appear in the manuscript.

## Reporting scope

The populated TRIPOD-LLM checklist applies the published 2025 evaluation and document-generation items. It maps claims to manuscript sections and supporting materials, identifies missing author declarations, and explains non-applicable development and live-deployment items. It is not a claim of complete guideline compliance. Public data provenance does not by itself establish this study's institutional ethics determination or permission to publish all expert records.
