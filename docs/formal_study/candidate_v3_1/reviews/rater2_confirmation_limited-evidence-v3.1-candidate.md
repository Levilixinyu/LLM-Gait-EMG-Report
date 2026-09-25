# Reviewer confirmation of revised interpretation instructions

Reviewer: rater2
Review date: 2026-09-18
Version: limited-evidence-v3.1-candidate

## Materials reviewed

- [x] Response to reviewers, including cycle-boundary evidence and qualifications (RESPONSE_TO_REVIEWERS.md; cycle_boundary_evidence.json summary fields).
- [x] Revised system prompt and full user input for Sub09.
- [x] Revised system prompt and full user input for Sub05.
- [x] Revised system prompt and full user input for Sub50.
- [x] Revised system prompt and full user input for Sub47.
- [x] Revised system prompt and full user input for control Sub49.

Method: the five system prompts were compared byte-for-byte and are identical. Each user input was diffed against Sub09 so that every non-numeric difference (normalization provenance, cycle-boundary paragraph, field-applicability bullet, speed-band annotation, control-specific lines, absent-EMG statement) was read in full. Numerical summaries were not re-verified; the response states they are unchanged from v5/v6. The checklist drafts for Sub50 (C04) and Sub47 (C02, C03) were read for R11 and R12. The card review page was not used; no review JSON is attached.

## Required points

**CCI interpretation: Agree**
R01 and R10 are resolved. The rule now separates three things that the trial showed models conflate: membership of the supplied empirical interval, physiological normality or pathology, and mechanism (stiffness, impaired control, simultaneous activation time). Proximity to an endpoint or to a supplied median is explicitly allowed, which preserves the legitimate Sub09/Sub50 statement that RF–BF lies near the upper bound. The cross-method prohibition and the dependence on normalization/envelope methods are stated. No further wording needed.

**Stroke normalization and healthy verification scope: Agree**
R02 and R03 are clearly stated in both the model input and the reference notes: stroke denominators are participant-, side- and muscle-specific and were array-verified; healthy normalization and left/right pooling are documentary and were not numerically re-verified by the stroke audit. One non-blocking presentation note: the stroke user input now carries audit counts ("614 evaluable combinations, not all 700; 86 lacked valid nonzero paired samples"). These figures are not usable by the model for interpretation and may be echoed into reports as if they were case findings. I would keep the qualitative provenance sentence in the model input and move the counts to the reference notes and NORMALIZATION_EVIDENCE.md. This does not affect my decision.

**Stroke initial-contact boundary: Agree**
R06 (stroke) is resolved exactly as requested. The input states that the paretic-side cycle runs from initial contact of that limb at 0% to its next initial contact at 100%, that the boundary may be called initial contact, that the endpoints are successive occurrences rather than one instant, and that no intermediate event or phase boundary is supplied. The system prompt permits naming the boundary or describing numerical proximity to it while still prohibiting stance/swing, loading response, pre-swing, mid-stance or a conventional 60% split. This is the correct scope: it releases the one event the data actually contain and nothing else. The consistency check that the four reviewed stroke cases have no invalid event interval is noted; the Sub43 zero-duration record is outside these cases and is appropriately parked for eligibility review.

**Healthy pooled initial-contact boundary with documentary qualification: Agree**
R06 (control) is formulated correctly and separately. Because the healthy Excel release averages left and right strides, the boundary is an initial-contact-aligned pooled cycle rather than one limb's observed event trace, and the input says so together with the documentary qualification. "Initial contact of contributing strides" is the right phrase. I do not consider the documentary status a reason to withhold the anchor: it is the dataset's stated construction, and the model is told it is documentary.

**Anatomical actions versus gait-phase functions: Agree**
R07 is resolved: anatomical actions may be named; mapping an interval to clearance, push-off or weight acceptance remains prohibited. This removes the unintended restriction I raised without reopening phase inference.

**Speed-band labels and group-specific field applicability: Agree**
R04: the annotation on every gait-speed line ("denotes a speed band only, not measured walking independence, safety or real-world community mobility") is sufficient without removing the category. The rubric's existing C01 prohibition on inferring community or household function from the band should remain so that the annotation and the scoring rule point the same way.
R05: the field-applicability bullet no longer claims that every listed field exists for every participant and distinguishes not supplied, not applicable and documented absent recordings. Resolved.
R13: control Sub49 now carries "Gait speed: not provided", "Cadence: not provided" and "Step length symmetry index: not applicable (this task's paretic/non-paretic index; control has no paretic side)". The narrower statement, which does not deny that a general left/right symmetry measure could be defined, is the correct one. Resolved.

**Other revisions R08–R14: Agree**
R08: the permitted vocabulary (reported coverage, retained intervals, boundary continuity at the mean-envelope level) is what I asked for, and the two added limits are correct: a mean-envelope pattern does not imply the same pattern in every stride, and a rounded 100% coverage or a single retained interval does not by itself prove that no sub-3% below-threshold dip existed, because the minimum-duration rule discards such dips. This is a subtle point; the rubric should count "above threshold for 100% of the analysis cycle with one retained interval" as full coverage of the finding and should not expect the stronger "no below-threshold segment" claim.
R09: the max |z| bullet correctly separates the location of the largest standardized difference from the amplitude peak and from any gait event, and defines above/below as relative to the phase-specific reference mean rather than to a percentile limit. This closes the R006-type direction/limit confusion prospectively.
R11: the Sub50 preparation item now states that the listed channels are examples selected for multiple retained intervals or boundary continuity, that other channels (including GAS with its single non-wrapping interval) remain in the full input, and that missing data must not be inferred from the selection. No longer misleading.
R12: "If EMG is unavailable, section 2 may simply state that envelope timing, amplitude and CCI cannot be assessed" resolves the Sub47 concern; the rubric should treat that statement as complete coverage of section 2.
R14: descriptive comparisons with supplied values remain allowed; near-boundary rounded values may not be used to classify hidden unrounded values. Consistent with the trial adjudication of the rounding question.

## Unresolved items and proposed wording

None that require revision.

Two non-blocking notes for the rubric or a later input version, not for this confirmation:
1. Audit counts in the stroke user input (see normalization point above) could be moved to the reference notes.
2. The per-muscle max |z| reference is still supplied only as the 3.65–4.61 endpoint span, so muscles inside that span (e.g. VL and ST at 4.2 in Sub09) must be reported as indeterminate. This is unchanged from v3 and was not part of the requested revisions; the rubric should count a correctly stated indeterminate as coverage, and the study lead should decide separately whether the formal input supplies all seven per-muscle values.

## Overall decision

- [x] Approve this revised version as written.
- [ ] Revisions required; return the next version for confirmation.
- [ ] Unable to approve; reasons are provided above.

Scope: This confirmation concerns the prospective interpretation instructions only. It does not modify historical reports, ratings or adjudications, establish a final scoring rubric, or authorize a formal generation batch.
