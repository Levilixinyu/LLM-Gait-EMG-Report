# Reference notes: stroke_Sub47_P

**Draft. An empirical distribution is not a clinical diagnostic threshold.**

Actual reference: 138 participants, pooled; excluded: [].

## A. Information actually provided to the model

Please refer to the original text in model_user_prompt.txt: the definition of max|z|, the overall pooled p95 span of 3.65–4.61 (only the muscles at the endpoints), the reminder that LOO is higher, CCI ranges, pooled GPS-like background, and speed limitations. Complete LOO values were not provided for each muscle.

## B. Supplementary table solely for expert verification during preparation

**The exact values in the table below and the plots were not sent to the model; their omission must not automatically be counted as a model error. Before formal scoring, experts must decide whether to add these references to future standardized inputs or retain the current task, which permits indeterminate judgments.**

| Muscle | Valid reference n for this case | Calibration distribution n | pooled p95 | LOO p95 | Background column corresponding to this case's method |
|---|---:|---:|---:|---:|---|
| GAS | 109 | 109 | 3.936 | 4.275 | p95 |
| RF | 108 | 108 | 4.527 | 5.06 | p95 |
| VL | 109 | 109 | 4.0 | 4.354 | p95 |
| BF | 106 | 106 | 4.127 | 4.532 | p95 |
| ST | 108 | 108 | 3.912 | 4.246 | p95 |
| TA | 107 | 107 | 4.605 | 5.174 | p95 |
| ERS | 106 | 106 | 3.646 | 3.919 | p95 |

The LOO column is the empirical distribution for all valid healthy individuals, each with themselves excluded, not a diagnostic threshold recalibrated specifically for Sub49 using 137 individuals; the possibility that this case is included as a calibration observation should not be concealed either. The patient's pooled comparison likewise indicates only deviation relative to this group of healthy individuals walking at self-selected speeds.

The input provides empirical 2.5–97.5 percentiles for CCI: TA–GAS 0.24–0.59 and RF–BF 0.48–0.83; CCI does not depend on the z reference mean.
The input GPS-like median 5.1/p95 10.7 comes from the pooled background. GPS-like calculations for healthy cases use the LOO mean; the background p95 must not be directly passed off as a matched LOO diagnostic limit.

The mean±1 SD in the plots describes only the phase-wise distribution, not a 95% interval for individual curves or a clinical normal limit; a negative lower band boundary merely displays the mean minus SD and does not mean that negative EMG was observed.
The released EMG curves are ensemble-averaged envelopes. For each participant and recorded muscle, normalization uses a shared maximum across the available strides before averaging; individual strides are not independently rescaled to their own peaks. This pipeline uses the released mean curves without further amplitude normalization. Amplitudes are relative envelope values, not absolute neural activation, force, or strength. Do not rank muscles as stronger or weaker from these amplitudes, or infer stride-to-stride variability from an average curve. Separately, interval detection uses 20% of the supplied mean envelope's own peak; do not confuse the detection threshold with the amplitude-normalization denominator.
Individual toe-off was not provided, so precise stance/swing phases are not marked on the plots; the seven muscles do not represent all muscles.

Sources: original data https://doi.org/10.6084/m9.figshare.c.6503791.v1 ; methods https://www.nature.com/articles/s41597-023-02767-y ; local file data/normative_calibration_v2.json (see manifest for hash).
