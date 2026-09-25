# Revised candidate returned for expert confirmation

Version: **limited-evidence-v3.1-candidate**

Status: revised following both expert submissions; confirmation pending. No model calls, new reports or expert approvals were produced.

## Expert reading order

1. Read [Response to reviewers](RESPONSE_TO_REVIEWERS.md), which maps all requests to the implemented wording and identifies what requires confirmation.
2. Open the [five revised data cards](../../expert_trial/data_cards_v7_candidate/index.html). Expand **View full model input (system + user)** in each case. The complete text matches the saved messages.
3. Return a separately completed copy of the [confirmation template](CONFIRMATION_TEMPLATE.md). Reviewers should use their own identity and record unresolved requests; agreement is not prefilled. Browser exports are optional and do not replace overall version confirmation.

## Exact saved model inputs

| Case | System instruction | User input | Complete messages |
|---|---|---|---|
| Sub09 | [System](../../expert_trial/data_cards_v7_candidate/stroke_Sub09_P/model_system_prompt.txt) | [User](../../expert_trial/data_cards_v7_candidate/stroke_Sub09_P/model_user_prompt.txt) | [JSON](../../expert_trial/data_cards_v7_candidate/stroke_Sub09_P/model_messages.json) |
| Sub05 | [System](../../expert_trial/data_cards_v7_candidate/stroke_Sub05_P/model_system_prompt.txt) | [User](../../expert_trial/data_cards_v7_candidate/stroke_Sub05_P/model_user_prompt.txt) | [JSON](../../expert_trial/data_cards_v7_candidate/stroke_Sub05_P/model_messages.json) |
| Sub50 | [System](../../expert_trial/data_cards_v7_candidate/stroke_Sub50_P/model_system_prompt.txt) | [User](../../expert_trial/data_cards_v7_candidate/stroke_Sub50_P/model_user_prompt.txt) | [JSON](../../expert_trial/data_cards_v7_candidate/stroke_Sub50_P/model_messages.json) |
| Sub47 | [System](../../expert_trial/data_cards_v7_candidate/stroke_Sub47_P/model_system_prompt.txt) | [User](../../expert_trial/data_cards_v7_candidate/stroke_Sub47_P/model_user_prompt.txt) | [JSON](../../expert_trial/data_cards_v7_candidate/stroke_Sub47_P/model_messages.json) |
| Control Sub49 | [System](../../expert_trial/data_cards_v7_candidate/control_Sub49_avg/model_system_prompt.txt) | [User](../../expert_trial/data_cards_v7_candidate/control_Sub49_avg/model_user_prompt.txt) | [JSON](../../expert_trial/data_cards_v7_candidate/control_Sub49_avg/model_messages.json) |

## Provenance and scope

The [previous candidate](../candidate_v3/README.md), its reviewed cards and both original submissions remain unchanged. Their approval status remains revisions required. This revision updates wording and task definitions only; five-case numerical summaries are unchanged. The four-section format allows a short unavailable-EMG statement for Sub47.

The initial-contact anchor comes from the release dictionary and Excel Readme. Stroke event-array consistency checks and the out-of-sample Sub43 zero-duration flag are in [cycle boundary evidence](cycle_boundary_evidence.json). Healthy pooling and event alignment remain documentary, not a new healthy MAT validation.

See [validation](validation.json) for checks and hashes. Neither this candidate nor its draft preparation questions are a final scoring rubric. Pending expert confirmation, subsequent work remains the prospective rubric, exposure-aware sample selection, analysis specification and generation authorization.

## Reproduction

Use fresh output directories:

```sh
python -m pytest tests -q
python scripts/verify_release_cycle_boundary.py --out /tmp/gait-cycle-evidence-new.json
python scripts/build_expert_trial_package.py --verified-cache --prompt-version limited-evidence-v3.1-candidate --out /tmp/gait-cards-v31-new
python scripts/verify_card_review_ui.py --base /tmp/gait-cards-v31-new --out /tmp/gait-browser-v31-new
```
