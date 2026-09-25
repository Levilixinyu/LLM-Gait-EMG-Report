# EMG normalization evidence

## Documentary source

The [original dataset paper](https://www.nature.com/articles/s41597-023-02767-y) describes per-muscle normalization using the maximum across available strides, followed by time normalization and participant summary data. This supports a common across-stride denominator rather than independent normalization of each stride to its own peak. The paper alone does not settle all implementation details; the local array checks below provide the stroke-specific evidence.

The local release dictionary `data/raw/MATdatafiles_description.xlsx`, sheet `Stride normalized data`, cell C119 describes GAS normalization across the subject's strides. Rows 120, 121, 122 and 124 describe normalized RF, VL, BF and TA. STnorm and ERSnorm descriptions at rows 123 and 125 instead say "as measured". This documentation inconsistency is resolved for the checked stroke arrays by verifying those channels directly, rather than assuming that the labels alone prove their processing.

## Array-level verification

`verify_release_emg_normalization.py` checks 50 stroke participants, both sides and seven muscles, using each side's own segmentation. For each usable channel it compares the paired unnormalized and normalized arrays, estimates a common denominator, tests that it equals the raw array maximum, and compares the mean normalized curve against the released Excel curve. File hashes before and after the run confirm stable source bytes.

Of 700 combinations, 614 were evaluable and all passed; 86 had no valid nonzero paired samples. The maximum relative scaling residual was approximately 1.11e-16. Every checked Excel mean matched `nanmean(normalized_strides, axis=0)` exactly. All 614 combinations included at least one stride with a peak below one, inconsistent with independently rescaling every stride to its own peak.

All 304 muscle pairs with valid data on both sides had different denominators. Each denominator matched the corresponding side-muscle maximum. For the checked stroke release, the denominator is therefore participant-, side- and muscle-specific, shared across available strides. It is not a common bilateral denominator.

The numerical operation supported by these arrays is:

`normalized_stride = unnormalized_stride / maximum_over_available_strides_for_that_side_and_muscle`

`released_mean_curve = nanmean(normalized_strides, axis=strides)`

Separately, the project's threshold detector uses 20% of the supplied mean curve's own peak. That threshold is not the normalization denominator and is not established here as a clinical abnormality cutoff.

## Distinct project processing paths

The release loader supplies the published mean curves without further amplitude scaling. In contrast, the separate raw-signal pipeline extracts envelopes, time-normalizes cycles, averages them, then divides each mean curve by its own peak. The candidate records this distinction; neither numerical path was changed.

All 2,618 curve arrays used by the audited cache matched the current stroke and healthy Excel arrays exactly, including NaN positions. Thus the five-case candidate retains the existing numerical inputs while correcting processing descriptions and interpretation instructions.

## Limits

The healthy-cohort MAT was not checked, so healthy stride aggregation and side-pooling provenance remain documentary rather than numerically reproduced here. The complete filtering/acquisition pipeline, cross-side segmentation and author preprocessing code were not audited. These checks establish internal scaling and averaging consistency, not clinical validity, diagnostic thresholds or matched normal muscle timing. Source hashes, channel-level results, exclusions and bilateral denominators are recorded in `normalization_verification.json`.
