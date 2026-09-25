# Concrete formal batch awaiting study-lead authorization

Preparation is complete. No further routine paid test is proposed. The formal batch has not started.

- Participants: 25 stroke cases and 10 controls.
- Workload: 35 cases x 3 models = 105 fixed report slots. Some slots may yield no report; all outcomes are retained.
- Models: claude-opus-5, gpt-6-astra and gemini-3.1-pro-preview; 16,000-token cap and high reasoning for every model.
- Inputs: 70 exact reviewed prompt files; case selection and scoring rules unchanged.
- Budget: proposed $120 local cumulative reservation limit. One attempt across all slots reserves $59.64 using registered rates and assumed input size. The theoretical three-attempt reservation is $178.92, so the runner pauses before exceeding the $120 reservation limit. This is not a hard provider billing ceiling or an invoice estimate. Raising the limit requires a separate decision.
- Attempts: at most three per slot for eligible operational failures, never to replace an unsatisfactory report; no automatic model fallback.
- Evidence: [technical review](TECHNICAL_EVIDENCE_REVIEW.md), [effective parameters](EFFECTIVE_PARAMETERS.md), [offline evidence](OFFLINE_EVIDENCE.json).
- Limitation needing acceptance: Gemini has not been retested at 16K after its 8K truncation; Claude's real clinical probe succeeded, while the synthetic refusals remain unexplained. No model's success across all cases is guaranteed.

Plan canonical SHA-256: `726dbda2ef559cdfa33ecf7c851935a6bd7274ee85b8a27f31d15447352c6aa4`.
Plan: `../plan.json`.
Authorization draft: `authorization_READY_FOR_APPROVAL.json` (`approved: false`).

The earlier approvals covered study policy, a token-cap change and specific technical calls. They did not approve this concrete 105-slot plan and $120 reservation limit. The latest instruction to proceed is recorded as authorization to prepare this next step; no signature or acceptance of the above limitations has been inferred. The final decision is whether to start this exact batch under these terms without another paid check.

After explicit acceptance, record the study lead's instruction against this plan and execute the guarded formal runner. Do not change the plan or repeat completed technical checks. Once all slots have terminal outcomes, prepare the two independent blinded rating packages under the existing protocol.
