# Expert confirmation of prospective interpretation rules

Reviewer: rater2
Review date: 2026-09-17
Version: limited-evidence-v3-candidate
Materials reviewed: candidate_v3/README.md, NORMALIZATION_EVIDENCE.md, src/llm/candidate_prompts.py (system prompt), the full model input (system + user) for all five candidate cards, reference_card.md and checklist_DRAFT.md for each case, and the expert-only EMG/kinematic plots. The card review page was not used; no review JSON is attached. Historical reports, ratings and adjudications were not re-examined.

---

## 1. EMG threshold interpretation

Decision: **Agree** (with two optional additions)

Comments or proposed wording:

The statement is physiologically sound. A 20%-of-own-peak rule applied to an ensemble-averaged envelope yields a description of that curve, not of motor-unit recruitment. Coverage near 100% can arise from a flat envelope with low peak-to-baseline contrast, from genuinely sustained activity, or from averaging strides with variable burst timing; the summary cannot separate these. Likewise, "no interval detected" only means the criteria were not met. The candidate wording (system prompt rule 2 and the "Above-threshold intervals" definition) captures this correctly, and the healthy control Sub49 (RF above threshold for 100% of the cycle) is a useful in-sample demonstration that high coverage is not itself abnormal.

Two additions would make the rule easier to apply without loosening it:

a) State what the report *may* say, not only what it may not. Suggested permitted vocabulary: "above threshold for X% of the analysis cycle", "broad/narrow coverage", "remains above threshold across the cycle boundary", "no below-threshold segment was detected", "coverage depends on the envelope's shape relative to its own peak". Without an allowed list, models tend to over-hedge and drop findings that the rubric still expects (e.g. the 100% coverage of RF/BF/ERS in Sub09), which will show up as coverage loss rather than as safer reports.

b) Add one sentence on the max |z| phase: "The phase at which max |z| occurs is the location of the largest standardized difference from the reference; it is not the amplitude peak of the subject's curve." This was a listed prohibited inference in the completed trial (old G04) and is not stated explicitly in the candidate prompt.

No exception is needed for the 0%/100% boundary; the current text handles it.

## 2. Timing and gait-phase interpretation

Decision: **Revise** (the restriction is appropriate; two clarifications are needed so that it does not exclude the one phase anchor that is actually supplied, and so that anatomical muscle actions are not caught by the ban)

Comments or proposed wording:

The restriction is clinically justified for this task. Population toe-off (~60%) is a reasonable anchor only for healthy adults at self-selected speed. For the stroke cases here (0.14–0.83 m/s) stance fraction on the analysed side is unknown and can differ substantially from 60%, so any stance/swing split assigned from cycle percentage alone is a guess, and in the completed trial this guess was the single most frequent error class (7 of 15 reports). Prohibiting phase labels, and the "normal / early / delayed / prolonged" judgements that depend on them, removes that error source without removing any finding that the supplied data can support: percent-of-cycle intervals, the phase and direction of max |z|, and the comparison of max |z| with the supplied per-muscle 95th-percentile endpoints all remain reportable.

Two points where the current wording is stricter than the evidence requires:

a) The cycle-defining event is not named anywhere in the model input, yet it is the one gait event the data do contain. If, as in the source dataset, 0%/100% is initial contact of the analysed limb, the input should say so, e.g. "0% and 100% of the cycle are the initial contact of the analysed (paretic) limb." The report may then say "above threshold across initial contact" or "the largest difference occurs shortly before initial contact" without inferring stance/swing. Proposed rule wording: "Use percentages of the analysis cycle. The cycle boundary (0%/100%) is the initial contact of the analysed limb and may be named as such; no other gait event or phase (stance, swing, loading response, pre-swing, mid-stance) may be assigned to any percentage."

b) "Textbook muscle roles" should be narrowed to gait-phase functional roles. Naming a muscle's anatomical action (tibialis anterior as a dorsiflexor, gastrocnemius as a plantarflexor) is factual and harmless; mapping an interval to a functional role in the gait cycle ("swing-phase clearance", "push-off", "weight-acceptance control") is the inference that must be prohibited. Proposed wording: "Anatomical muscle actions may be named. Do not map any interval to a gait-phase function (e.g. foot clearance, push-off, loading), because the phase itself is not established."

I do not consider the rule excessive with regard to healthy Sub49. Although toe-off is more predictable in healthy adults, the task is defined as limited-evidence interpretation for all cases and the same restriction should apply; otherwise raters will need a case-dependent standard.

## 3. CCI interpretation

Decision: **Agree** (with one wording addition)

Comments or proposed wording:

The Falconer–Winter index is a whole-cycle envelope-overlap ratio computed on within-muscle normalised curves. It does not localise to a phase, is not a percentage of co-activation time, and is not a measure of joint stiffness. Values inside an empirical 2.5th–97.5th percentile band of a non-matched cohort say only that the ratio is not unusual for that cohort. The candidate rule ("within, below, or above that range; do not infer normal muscle function, co-activation time, stiffness, or phase-specific control") is the right boundary and is consistent with the substantive position I took in the completed trial. I understand it is prospective only and does not reopen Q055.

Addition: "CCI values depend on the normalisation and envelope method; do not compare them with CCI values or thresholds from other studies or algorithms." The completed-trial checklist carried this prohibition (applying thresholds across algorithms); the candidate prompt does not.

Suggested reportable phrasing for the rubric: "The RF–BF CCI (0.82) lies within the supplied empirical range (0.48–0.83), near its upper bound." Suggested prohibited phrasing: "normal co-activation", "no abnormal co-contraction", "elevated antagonist co-contraction indicating stiffness".

## 4. Reference comparability

Decision: **Agree**

Comments or proposed wording:

The candidate implements the agreed substantive G03 approach: both elements (limited comparability; no disease-effect or diagnostic inference) must be conveyed, once per report is enough, and age and speed need not appear as separate keywords. The added sentence "A speed inside an overall range does not prove that an appropriate matched reference exists" closes the Sub50-type loophole. "Gait speed: not provided" in the Sub49 input and "Apply these limits to controls as well" close the control-case gap. Case-specific speed content (C01) remaining a separate requirement is correct.

One residual risk that is not a rule problem but an input problem: the speed-band labels in the subject line ("limited community ambulator (0.4–0.8 m/s)", "full community ambulator (>0.8 m/s)", "household ambulator (<0.4 m/s)") are functional-classification terms from external literature, not measurements of this participant. In the completed trial they invited functional and attribution claims. I recommend either removing the label from the subject line or annotating it: "(speed band from published classification; not a functional assessment of this participant)". If retained without annotation, the rubric should keep the existing C01 prohibition on inferring community/household function from the band.

---

## Cases reviewed

- [x] Sub09
- [x] Sub05
- [x] Sub50
- [x] Sub47
- [x] Control Sub49

I browsed all five cards, read each complete model input, and used the plots only to check that the rules do not suppress a finding the data card actually supports. I did not re-verify individual interval values or thresholds; the package verification report states they are unchanged from v5.

## Case-specific concerns

Common observations are stated once above (permitted vocabulary; naming of the cycle-defining event; anatomical action vs phase role; max |z| phase ≠ amplitude peak; CCI cross-method comparison; speed-band labels). Case notes below add only what is specific to each card.

**Sub09** — None beyond the common items. Under the new rules the essential findings remain reportable: ERS max |z| 6.2 at 81% above reference, which exceeds the supplied ERS-specific 95th percentile (3.65); hip and knee as the largest GVS; RF/BF/ERS above threshold for 100% of the cycle as an envelope property; step-length index −9.9% with the paretic step shorter. VL and ST at 4.2 fall inside the 3.65–4.61 span of supplied endpoints and must be reported as indeterminate; the rubric should count a correctly stated "indeterminate" as coverage for such items rather than as an omission.

**Sub05** — (i) Ankle ROM 13.4° cannot be called restricted under the rules because no ROM reference is supplied. The restriction is correct for this version, but this is a real finding that a small addition to the input (cohort ROM mean ± SD per joint) would make legitimately reportable in a future version. (ii) TA max |z| occurs "at 0% of cycle"; the report should be allowed to note that this is at the cycle boundary, which is the same point as 100%. (iii) Five muscles at ≥95% coverage together with low mean-envelope peaks (0.24–0.50 under the shared-stride-maximum normalisation) will tempt models to infer stride-to-stride variability; the prompt already prohibits this. No change needed.

**Sub50** — (i) The pelvis GVS 9.56 with ROM 3.8° is, on the expert plot, a clear offset below the reference band, but the model cannot see the plot and the rules correctly stop it from asserting an offset direction from GVS+ROM. The rubric must not expect the offset. (ii) ST max |z| 4.7 exceeds 4.61, the highest supplied per-muscle 95th percentile, so the report may state that it exceeds every supplied endpoint; this should remain permitted. (iii) The "full community ambulator (>0.8 m/s)" label is the specific trigger for the over-attribution error seen in the trial; see the recommendation under rule 4.

**Sub47** — None. The input states the absence of EMG acquisition clearly. Section 2 of the four-section format will necessarily be a statement of non-availability; the rubric should treat that as full coverage of the EMG section and not require any further content there.

**Control Sub49** — (i) "Gait speed: not provided" is now explicit; good. Cadence and step-length symmetry are absent without a statement. For a control there is no paretic/non-paretic pair, so the symmetry index is not applicable rather than not provided. Suggest adding "Step length symmetry index: not applicable (control, no paretic side)" and "Cadence: not provided" so that the report neither invents them nor asks for a value that cannot exist. (ii) The deviation reference is leave-one-out (137) while the CCI and GPS-like background percentiles are pooled; the prompt's "Do not treat pooled calibration percentiles as matched leave-one-out normal limits" covers this. (iii) RF at 100% coverage in a healthy participant is the right in-sample check for rule 1.

## Overall decision

- [ ] Approve this version as written.
- [x] Revisions required; please return the revised version for confirmation.
- [ ] Unable to approve; reasons are provided above.

The required revisions are limited to rule 2 (name the cycle-defining event and permit it as the only nameable event; narrow "textbook muscle roles" to gait-phase functional roles). The other comments (permitted vocabulary, max |z| phase note, CCI cross-method sentence, speed-band label annotation, control-case "not applicable" lines) are recommended but I would not withhold approval over them if the study lead prefers to defer them to the rubric or to a later input version. I will confirm the revised wording when returned.

## Scope of confirmation

This review concerns the prospective report interpretation instructions. It does not revise historical reports, ratings or adjudications, establish a final scoring rubric, or authorize a formal generation batch.
