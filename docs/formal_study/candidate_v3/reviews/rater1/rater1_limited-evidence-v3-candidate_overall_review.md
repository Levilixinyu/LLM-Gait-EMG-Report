Reviewer: rater1
Review date: 2026-09-17
Version: limited-evidence-v3-candidate

Overall decision: **Revisions required; please return the revised version for confirmation.**

The limited-evidence approach is clinically defensible for this task and preserves the important supplied findings. I agree with rules 1, 2 and 4. I request a more explicit prospective CCI wording boundary and the limited input clarifications below. This is not approval of the candidate as written.

1. EMG threshold interpretation

Decision: **Agree**

Comments or proposed wording:

The intervals and coverage describe the averaged envelope under the specified relative threshold and minimum-duration rule. They do not, by themselves, establish physiological onset, offset, activation prolongation, tonic contraction, or absence of activity. No exception is needed for any of these five cases.

The restriction must still permit useful algorithm-level descriptions: “above threshold for 79% of the cycle,” “a broad boundary-spanning detected interval,” “no below-threshold interval in the mean envelope,” and comparisons of reported coverage. Such descriptions should not be relabeled as physiological activation duration or lack of phasic modulation. If no interval is retained, say that none met the threshold-and-duration criteria; this does not imply that the envelope never crossed the threshold or that the muscle was inactive.

Optional clarifying wording: “You may describe the extent, segmentation and cycle-boundary continuity of the detected above-threshold intervals. Keep these descriptions at the mean-envelope/algorithm level; they do not establish the same pattern in every individual stride.”

2. Timing and gait-phase interpretation

Decision: **Agree**

Comments or proposed wording:

For this particular input package, reporting cycle percentages without assigning stance, swing, loading response or phase-specific muscle roles is appropriate. The inputs do not provide the events and timing references needed to support the proposed physiological interpretations. A conventional 60% boundary must not substitute for an individual event. This restriction does not remove a supported case-specific phase interpretation from the present summaries.

Retain relative numerical location, such as “at approximately 81% of the analysis cycle,” and continuity across 100% to 0%. Preserve the distinction between a maximum absolute z-score location and the time of the envelope amplitude peak; neither is a toe-off estimate.

This is a task-specific restriction, not a general statement that EMG timing can never be interpreted. In a future version, supplied individual gait events could support mechanical phase assignment; judgments of early, delayed or prolonged activation would additionally require a suitable operational timing measure and comparison reference. Those are separate evidence requirements. No exception should be inferred from the present expert-only plots.

Suggested explicit clarification: “The reported location of maximum |z| identifies the largest standardized difference from the reference; it is not necessarily the time of peak envelope amplitude or a gait event.”

3. CCI interpretation

Decision: **Revise**

Comments or proposed wording:

I agree with retaining empirical comparisons and prohibiting inferences about muscle function, stiffness or phase-specific control. For the prospective version, make explicit whether this also excludes calling physiological co-activation itself normal. The current prohibition of “normal muscle function” could still leave “normal co-activation levels” open to competing readings. A precise output convention will remove that ambiguity without banning useful comparison.

Proposed wording:

“Report the supplied CCI as a whole-cycle overlap index of the normalized EMG envelopes. You may state that it is within, below or above the supplied empirical reference interval, or above/below its median or near an endpoint. Limit the conclusion to this index under the stated processing method. Being within that interval does not establish physiologically normal co-activation or normal muscle function; being outside it does not by itself establish pathological co-activation, joint stiffness, impaired control or a diagnosis. Do not interpret CCI as the percentage of simultaneous activation time, as the amount of muscular force, or as evidence about a particular gait phase.”

This allows, for example, “RF–BF CCI is near the upper end of the supplied interval,” while prospectively avoiding “normal antagonist co-activation.” This proposed wording does not change Q055 or any historical decision.

4. Reference comparability

Decision: **Agree**

Comments or proposed wording:

The two substantive meanings are appropriate: identify a meaningful limitation of the comparison and explain why the observed differences cannot independently establish a disease effect or clinical diagnosis. One clear statement is sufficient, even when supporting information appears in different sections. Neither separate age/speed keywords nor repetition in every paragraph is needed. A pooled label or a list of speed limits alone is insufficient.

Keep factual comparisons available: values may be ranked within a case, compared descriptively with the supplied empirical background, and reported with their signed direction. These permissions do not establish matched normal limits, clinical severity or individual causes. A value within the overall speed span does not establish an available, appropriate speed-matched sample. For a control, unknown speed prevents assessment of speed comparability; it must not be converted into an assertion of disease or overall normality. Coverage and incorrect assertions remain separate records.

Cases reviewed:

- [x] Sub09
- [x] Sub05
- [x] Sub50
- [x] Sub47
- [x] Control Sub49

Common input and review-material concerns (recorded once)

**Required clarification A — normalization provenance.** The supplied verification establishes a participant-, **side-**, and muscle-specific shared denominator for the evaluable stroke channels. The candidate user text says “for each participant and recorded muscle” without explicitly stating side. Add the side-specific qualifier to the stroke description so “shared” cannot be read as a bilateral denominator. Suggested wording: “For the checked stroke release, each participant–side–muscle channel uses its maximum across the available strides as a common denominator before averaging; the denominator is not shared between sides.” Keep this distinct from the detector's 20%-of-mean-peak threshold. This is a textual correction, not a request to recompute metrics.

The normalization report states that all 614 evaluable stroke combinations passed, while 86 were not evaluable; it does not establish that all 700 were verified. It also explicitly limits numerical verification to stroke MAT data. I reviewed that evidence; I did not rerun the normalization audit. The published dataset methods describe a maximum across available strides per muscle, consistent with the broad correction from independent stride scaling, but the side-specific and audit-scope details here come from the supplied local verification. [Original dataset methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC10692332/).

**Required clarification B — speed-band labels.** The user inputs retain “household ambulator,” “limited community ambulator” and “full community ambulator.” Explicitly identify these as speed-band descriptors, not measured real-world independence, safety or community participation. Suggested common sentence: “Any ambulation category supplied alongside gait speed denotes the stated speed band only; it does not establish this participant's actual walking independence, safety or community mobility.” This preserves the numbers and useful speed context.

**Recommended clarification C — the meaning of reference direction.** Define “above/below reference” in an EMG row as above/below the phase-specific reference mean at the reported maximum-|z| location, not above/below a healthy percentile limit. Paired with the timing clarification in section 2, this prevents two recurring conceptual confusions without adding required findings.

**Draft checklist boundary.** The common guidance appropriately excludes unseen plots and supplementary percentiles from required model content. However, draft case prompts still ask reviewers to inspect curves and select “changes” or “activity intervals.” These are preparation questions only. Carry into any later reporting requirement only findings traceable to the actual model-visible summary, unless that future input is explicitly expanded. Prefer “detected above-threshold intervals” to “activity intervals” in these questions. Do not turn every numerical maximum or draft item into a mandatory clinically important finding. This review does not approve a final checklist or omission rubric.

Case-specific applicability and concerns

| Case | Important supplied findings remain reportable | Case-specific concern |
|---|---|---|
| Sub09 | Hip/knee GVS differences; shorter paretic successive-footfall step (−9.9%); ERS above-reference difference at 81% with max \|z\| 6.2; broad ST/VL threshold coverage. | No additional case-specific restriction is needed. The rules permit the main findings without labeling ERS “late swing” or inferring loss of modulation from 100% coverage. Exact expert-only VL/ST percentiles must not be required. |
| Sub05 | Very low speed and unmatched-reference context; knee-dominant GVS; GAS 13.3 above reference at 80%, ST 7.0 above at 35%, and VL 5.3 below at 5%; shorter paretic step (−23.1%). | TA's displayed 4.6 and the displayed 4.61 background endpoint support a displayed-number comparison, not a robust classification of the unrounded value. Keep any near-boundary interpretation qualified and do not require hidden precision. |
| Sub50 | Pelvis has the largest GVS despite small ROM; knee is also prominent; ST max \|z\| 4.7 above reference at 33%; near-zero successive-footfall asymmetry (−0.7%). | Its speed 0.83 m/s is near the lower end of the supplied range, without establishing matching. Draft C04 omits GAS from its muscle list even though the model input includes GAS; correct that preparation prompt or mark the list non-exhaustive. Do not infer a missing GAS channel. |
| Sub47 | Speed, step asymmetry (−15.4%) and hip/knee/ankle summary differences remain interpretable within their limits. | Section 2 must permit a brief “EMG unavailable; envelope timing, amplitude and CCI cannot be assessed” statement. The displayed healthy EMG curves are reference-only and cannot supply this participant's missing EMG. There should be no requirement to invent EMG content to fill the four-section format. |
| Control Sub49 | Healthy-control provenance; 137-person reference excluding Sub49; knee/ankle GVS ranking; RF max \|z\| 3.3 at 32%; measured CCI compared with the supplied empirical intervals. | State that the healthy stride-normalization/side-pooling provenance is documentary rather than numerically verified by the stroke audit. Do not transfer the stroke side-specific verification claim to this case. Unknown speed prevents assessing speed comparability; pooled GPS-like percentiles are not matched LOO diagnostic limits. The generic “fields existing in the source” sentence should not imply that time post-stroke or a non-paretic designation applies to a healthy participant; qualify such fields by group/applicability. |

The healthy-case provenance qualification and applicability correction are required textual clarifications. They do not require a new healthy MAT audit for this limited-evidence review and do not question the unchanged supplied numerical summaries.

Overall decision:

- [ ] Approve this version as written.
- [x] Revisions required; please return the revised version for confirmation.
- [ ] Unable to approve; reasons are provided above.

Please return the revised CCI instruction, normalization wording with appropriate group-specific verification limits, and the speed-band/applicability clarifications, together with the resulting five full model-input snapshots. The recommendations about max-|z| wording and draft checklist terminology should also be considered, but no new feature extraction is requested.

Scope of confirmation:

This review concerns the prospective report interpretation instructions.
It does not revise historical reports, ratings or adjudications, establish
a final scoring rubric, or authorize a formal generation batch.

Review record:

I read the version description and normalization evidence before reviewing the five cards, their saved system/user inputs, draft checklist questions, reference notes and plots. I checked that the HTML contains the complete saved prompts and that each model_messages.json agrees with its system/user text. This was a document and interpretation review, not an independent rerun of the array audit, a new rating of the 15 historical reports, or a review of another reviewer's current answers. These five development cases are not an untouched validation sample.

No page review form was submitted or saved in browser storage. This English document is the formal overall response; the accompanying JSON is a standalone record of this response and its material hashes, **not** a browser “Export review JSON” file and not item-level Accept/Modify/Delete approval.
