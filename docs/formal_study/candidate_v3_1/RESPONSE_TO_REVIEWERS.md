# Response to reviewer requests

Revised version: `limited-evidence-v3.1-candidate`

Status: revisions implemented and returned for confirmation. Neither reviewer has approved this revised version yet. This response is agent-authored; it is not a new expert statement or signature.

Original submissions remain unchanged under [candidate v3 reviews](../candidate_v3/reviews/). Both reviewers requested revisions. Their agreement with some original rules is not treated as approval of the new package.

| ID | Reviewer request | Action in v3.1 | Confirmation sought |
|---|---|---|---|
| R01 | Rater1: explicitly exclude physiological normal co-activation, not only normal muscle function. | CCI rule now distinguishes empirical interval membership from physiological normality, pathology, stiffness, impaired control and diagnosis. Supplied median/endpoint comparisons remain allowed; unavailable medians cannot be invented. | Does the revised wording resolve the ambiguity? |
| R02 | Rater1: specify side-dependent stroke normalization and audit scope. | Stroke user input and reference notes state participant-, side- and muscle-specific denominators, not bilateral sharing; 614 evaluable combinations verified and 86 not evaluable. | Is the provenance statement sufficiently clear? |
| R03 | Rater1: distinguish healthy documentary provenance from stroke array verification. | Healthy user input and reference notes explicitly say that healthy normalization and pooling are documented, not numerically verified by the stroke audit. | Is the documentary qualification acceptable? |
| R04 | Both: clarify speed-band labels. | Each supplied gait-speed line retains its value and category but states that the label denotes a speed band, not measured independence, safety or real-world community mobility. | Is the annotation sufficient without removing the category? |
| R05 | Rater1: qualify source fields by group. | Removed the blanket claim that all listed fields exist for every participant; stroke-specific history, scores and non-paretic designation are qualified by applicability. | Is the healthy-case ambiguity resolved? |
| R06 | Rater2: allow the actual initial-contact boundary. | Added a source-qualified event anchor. Stroke cycles use successive initial contacts of the analyzed limb. Healthy averaged curves use the initial-contact boundary of contributing left/right strides, not one named limb's event trace. No intermediate phase boundaries are added. See cycle evidence below. | Confirm the stroke and pooled-control formulations separately. |
| R07 | Rater2: distinguish anatomy from gait-phase function. | Anatomical muscle actions may be named. Mapping intervals to clearance, push-off or weight acceptance remains prohibited without supporting phase evidence. | Does this remove the unintended restriction? |
| R08 | Both: explicitly allow descriptive threshold vocabulary. | Permits reported coverage, retained intervals and boundary continuity at the mean-envelope level. No inference about every stride; rounded coverage or no retained interval cannot alone prove absence of a below-threshold segment. | Are useful descriptions retained with adequate evidence limits? |
| R09 | Both: clarify maximum-z location and direction. | System prompt distinguishes maximum standardized difference from amplitude peak or a gait event; above/below reference means the phase-specific mean at that location, not a healthy percentile cutoff. | Is this distinction clear? |
| R10 | Rater2: avoid CCI cross-method thresholds. | Explicit prohibition of importing values/thresholds from other studies or algorithms; normalization/envelope dependence stated. | Confirm. |
| R11 | Rater1: Sub50 interval list omits GAS. | Marked the preparation list as non-exhaustive, explained its selection criteria, and stated that other measured channels remain available. Retained detected-interval terminology. No channel was added or removed. | Is the preparation question no longer misleading? |
| R12 | Both: Sub47 should not need invented section content. | Section 2 may simply state that EMG envelope timing, amplitude and CCI cannot be assessed; reference-only plots do not supply patient EMG. | Confirm. |
| R13 | Rater2: control cadence and symmetry applicability. | Added cadence not provided and the task's paretic/non-paretic index not applicable. Explicitly avoided claiming that general left/right symmetry cannot be measured in controls. | Confirm the narrower applicability statement. |
| R14 | Both: retain supported numerical comparisons without hidden precision or unseen plots. | Preserved numerical findings; allowed descriptive comparisons with supplied values, qualified rounded near-boundary classifications, and made draft questions refer to model-visible summaries. | Confirm; final scoring examples remain separate work. |

## Cycle-boundary evidence and one unrelated data flag

The release dictionary `data/raw/MATdatafiles_description.xlsx`, sheet `MAT data Struct`, rows 24–26 and 36 defines initial contact at the start and end of the ipsilateral stride and explains side-based segmentation. The healthy Excel Readme states that left/right strides are averaged. Together these support a pooled initial-contact-aligned cycle for the healthy summary, with documentary provenance explicitly retained. The original publication describes the release's event processing and participant summaries: https://www.nature.com/articles/s41597-023-02767-y.

The [event consistency record](cycle_boundary_evidence.json) additionally compares stroke event counts with the same-side hip-angle stride arrays. These are consistency checks, not independent event detection. One Sub43 paretic record has start and stop both zero (zero-based stride index 3). This participant is outside the five development cases. It is recorded for later data eligibility review; no automatic exclusion, data repair or feature change was made. The four reviewed stroke cases do not have this flag. The healthy MAT was not audited.

0% and 100% denote successive initial contacts of a stride-defining limb. They occupy the same position in a periodic representation but are not the same physical instant. Neither the known boundary nor the anatomical permission establishes stance/swing boundaries or physiological onset/offset from threshold intervals.

## What this return does not request

Do not re-score the 15 historical reports or reopen Q055. No healthy MAT reanalysis, new clinical findings, final omission checklist, scoring weights, formal sample size or model batch is being approved through this confirmation. Five-case numerical summaries and the original submissions are unchanged.

Please use [the confirmation template](CONFIRMATION_TEMPLATE.md) and identify any unresolved item by its R01–R14 ID. Required revisions remain pending until the revised wording and complete five-case inputs have been confirmed.
