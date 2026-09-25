# Manuscript source map

| Content | Authoritative local source |
| --- | --- |
| Frozen numerical outcomes and paired intervals | `data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/final_outcomes.json` |
| Current reviewer background | `docs/formal_study/REVIEWER_BACKGROUND_CONFIRMATION.json`; study-lead confirmation, not a new expert signature |
| Original independent outcomes and coverage stage comparison | Same protected directory, `independent_sensitivity.json` |
| Review timeline | D01-D03 recheck instructions, freeze record, unblinding record, semantic-flag confirmation and targeted return check |
| Descriptive length | 105 hash-verified blinded report texts in `rating_delivery_v1/rater2/reports`; whitespace splitting including Markdown |
| Original agreement and exclusions | `docs/formal_study/three_rater_analysis_v1/INDEPENDENT_AGREEMENT.json` |
| Targeted sensitivity | `data/rating_packets_formal_v1/private/wording_sensitivity_v1/ANALYSIS.json` |
| Sample characteristics | `docs/formal_study/control_supplement_v2/selected_study_cases.csv`, membership checked against the frozen roster; old status fields excluded |
| Eligibility and exposure history | `sample_eligibility_v1/README.md`, `execution_analysis_v1_draft/exposure_confirmation.json` |
| Original plan versus implemented review | `execution_analysis_v3_draft/PROTOCOL.md`, `rating_delivery_rater3_v1/REVIEWER_ADDITION_RECORD.md`, `three_rater_analysis_v1/ANALYSIS_ADDENDUM_DRAFT.md` and later authorization records |
| Semantic flag clarification | `three_rater_analysis_v1/SEMANTIC_FLAG_CONFIRMATION.json` |
| Generation settings and dates | `formal_execution_v2_candidate/plan.json`, `provider_configuration.json`, `formal_stages_v1/GENERATION_COMPLETION.json`, stage result rows |
| Feature definitions | Saved model prompts; `src/features/emg_signal.py`, `src/features/kinematic.py` |

Only later, scoped completion/authorization records supersede historical pending-status statements. Historical protocol text was not edited or represented as if it originally specified three independent raters or the later semantic clarification. The manuscript preserves this chronology.

External references verified while preparing this draft: the [dataset publication](https://www.nature.com/articles/s41597-023-02767-y), [SciPy paired-bootstrap/BCa documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), and [NIST exact binomial limits](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm). These support dataset context and calculation concepts, not the project's selection, ethical determination or empirical results. The project's BCa implementation is local code; the manuscript does not claim that scipy.stats.bootstrap directly produced the saved estimates.

This is a full working manuscript with a focused background, not a systematic literature review. CHART is cited for reporting context, not as evidence of completed checklist compliance. No journal-specific reporting-compliance claim is made. Per-report model identities remain outside reviewer packets.
