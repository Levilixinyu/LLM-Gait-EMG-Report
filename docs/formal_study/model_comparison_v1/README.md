# Model comparison: frozen three-rater outcomes

> **Later targeted review:** read these historical frozen results together with the [wording-boundary sensitivity supplement](../wording_sensitivity_v1/README.md). Four issue-label disagreements and one control pathology-annotation disagreement remain in the later personal returns. The supplement retains the original results and shows their sensitivity; it does not replace this freeze or create a new consensus.

The study lead authorized analysis after the blinded dataset was frozen. The protected identity mapping was verified against the delivery integrity record and joined to all 105 unchanged report slots. No report was regenerated and no expert rating was changed during analysis.

## Main findings in this dataset

The primary stroke analysis includes all 25 paired participants. Mean full coverage was 98.2% for the recorded `claude-opus-5` configuration, 97.0% for `gpt-6-astra`, and 81.8% for `gemini-3.1-pro-preview`. These are equally weighted participant coverage proportions, with G03 separate and no half-credit for partial coverage.

The family-adjusted 98.3333% paired BCa intervals were:

- Claude minus Gemini: +16.4 percentage points, 9.6 to 24.2.
- GPT minus Gemini: +15.2 percentage points, 9.0 to 22.0.
- Claude minus GPT: +1.2 percentage points, -1.6 to 6.2.

The first two contrasts are positive under the planned approximate family-adjusted interval procedure. The Claude-GPT interval includes zero; this does not establish either a coverage advantage or equivalence between them.

Confirmed-error stroke reports were 11/22 evaluable for Claude, 12/23 for Gemini, and 2/25 for GPT. Three Claude and two Gemini reports had unknown any-error status due to Pending without a confirmed error. On all 25 planned stroke reports per model, error-proportion missingness bounds are therefore 44%-56%, 48%-56%, and 8%-8%, respectively. These bounds address unresolved status and are not confidence intervals. Error comparisons are exploratory, not a new confirmatory superiority test.

The control supplement has 10 participants per configuration. Coverage was 90.0%, 73.3% and 86.7% for Claude, Gemini and GPT, respectively. Confirmed-error reports were 6/9 evaluable for Claude (one unknown), 8/10 for Gemini, and 0/10 for GPT. The pathology annotation occurred in one Gemini control report; all other model/semantic-flag combinations had zero events. Zero events among 10 controls still has a one-sided 95% upper bound of approximately 25.9%; these annotations are not diagnostic false-positive rates.

## Original independent sensitivity must accompany the post-feedback results

The original independent coverage results put Claude and GPT above Gemini for all three reviewers, although the magnitudes differ. Original error-detection results are less stable:

- Rater1 and rater2 independently recorded fewer confirmed-error stroke reports for GPT than for the other two configurations.
- Rater3 originally recorded no confirmed-error Claude stroke reports (0/25), one GPT report (1/25), and one Gemini report among only 10 evaluable Gemini reports, with 15 unknown. That initial pattern does not reproduce the final Claude-GPT error ordering.

Do not describe the final result as a conclusion reached identically by all three original independent reviewers. The frozen main outcome layer incorporates blinded clarification, targeted audits and discussion; report that process, original agreement and sensitivity results transparently. Do not select whichever reviewer or stage gives a preferred model ranking.

All final G03 judgments were Covered. Each original reviewer marked the four-section format as present in all 105 reports and recorded no incidental unblinding; those are reviewer declarations. Generation metadata records 105 captured outputs, normal stream completion, and no truncation. These checks do not establish factual correctness or clinical suitability.

## Files

- [Numerical results and methods](RESULTS.md)
- [Model comparison workbook](Model_comparison.xlsx): cohort summaries, paired contrasts, per-case outcomes, individual category views, control flags, original independent sensitivity, and generation capture.
- [Paired coverage figure, PNG](Paired_stroke_coverage.png) and [SVG](Paired_stroke_coverage.svg).
- [Authorization scope](AUTHORIZATION.json).

Protected reproducibility files are in `data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/`: unblinding time, verified mapping snapshot, complete estimates, category trace, original-independent sensitivities, exact 20,000-row resampling matrices, and source/output hashes. This location is not a rater packet.

The original hash-bound analysis module was preserved byte-for-byte. The additive frozen-metric entry point uses the same planned calculations and leaves common category counts unavailable rather than imposing shared labels. Thirty-three relevant tests passed, including parity with the original analysis path. The frozen dataset remains SHA-256 `9cf006f23d5660118f5ac4da9e631e68645fa17686a0742841e267e616ca9167`.

These are results for selected internal cases and one response per configuration. They do not establish general model superiority, diagnostic accuracy, clinical deployment safety, or repeated-generation reliability. No overall quality score or model ranking was constructed.
