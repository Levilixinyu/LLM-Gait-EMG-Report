# Five-case proposed requirement annex

DRAFT: adapted from the historical confirmed checklist and clarified for approved v3.1 inputs. This annex has not received expert approval. All exact numbers below are model-visible anchors; the full required core is specified per row.

Common G03 is defined once in RUBRIC.md and applies once per report. CCI and other optional items are not silently promoted to required findings. The source IDs below refer to the historical checklist, not to the regenerated draft card IDs.

## stroke_Sub09_P

[Exact user input](../../expert_trial/data_cards_v7_candidate/stroke_Sub09_P/model_user_prompt.txt)

### C01 (historical source: C01)

Describe speed 0.62 m/s AND explain that it is below the reference speed floor of 0.80 m/s, so this dataset supplies no healthy reference at that speed.

**Logic:** AND; factual case-speed requirement is separate from G03
**Optional:** Cadence and speed-band label are optional. If used, the band is not actual independence, safety or community function.
**Partial-coverage example:** Speed is supplied, but its relation to reference support or matching limitation is missing.
**Clarification:** One sentence may satisfy both C01 and G03; no duplicate caveat is required. The disease-attribution limit is assessed under G03 rather than counted twice as a separate omission.

### C02 (historical source: C02)

Prioritize the hip AND knee as the main joint-curve differences.

**Logic:** AND for the named priorities; synonyms accepted
**Optional:** Hip/knee GVS 11.70/9.22 degrees and ROM may be described, without requiring every number.
**Partial-coverage example:** Only some required joints are discussed, or the stated relative priority is absent.
**Clarification:** No unseen curve direction, phase, exact plot-derived morphology or clinical severity is required.

### C03 (historical source: C03)

Identify ERS as a principal numerical EMG difference AND describe it as above the phase-specific reference mean at approximately 81% of the analysis cycle. Its reported max |z| is 6.2.

**Logic:** AND for muscle, above-mean direction, approximate cycle location and prominence; prominence may be conveyed by the supplied magnitude or a within-case ranking
**Optional:** Exact numerical repetition is unnecessary if the main finding and direction/location are clear. A supplied empirical endpoint comparison is optional; clinical normality need not be determined.
**Partial-coverage example:** Names the muscle and magnitude, but does not communicate the above-mean direction or cycle location.
**Clarification:** Direction relative to the mean is not percentile exceedance. Cycle location is not amplitude-peak timing or an inferred gait phase.

### C04 (historical source: C04)

In addition to ERS, describe meaningful ST AND VL findings: their above-mean numerical deviations OR their broad boundary-spanning detected above-threshold intervals.

**Logic:** For EACH of ST and VL, accept either numerical or interval route; mixed routes are allowed. Do not require both routes.
**Optional:** Numerical route: max |z| 4.2, ST above at 25%, VL above at 21%. Interval route: ST about 83% to 44%, VL about 88% to 48%, wrapping the boundary. Exact segment lists and muscle-specific p95 are not required.
**Partial-coverage example:** Only one of ST/VL is described; or both are merely named with no finding.
**Clarification:** A supported indeterminate percentile classification is compatible with full coverage when the ST/VL findings are conveyed. A generic inability statement alone does not replace the findings.

### SL01 (historical source: NEW-stroke_Sub09_P-01)

Report the supplied successive-footfall step-length index (-9.9%) AND convey the paretic step is shorter.

**Logic:** AND; no formula recitation required
**Optional:** May be combined with speed/cadence; spelling out the operational definition again is optional.
**Partial-coverage example:** Gives the index without its directional/near-zero meaning, or gives only a vague asymmetry statement without the supplied index.
**Clarification:** Preserves the four previously confirmed step-index requirements under a new prospective ID. The index is not the percentage shortening relative to the other side.


## stroke_Sub05_P

[Exact user input](../../expert_trial/data_cards_v7_candidate/stroke_Sub05_P/model_user_prompt.txt)

### C01 (historical source: C01)

Describe speed 0.14 m/s AND explain that it is below the reference speed floor of 0.80 m/s, so this dataset supplies no healthy reference at that speed.

**Logic:** AND; factual case-speed requirement is separate from G03
**Optional:** Cadence and speed-band label are optional. If used, the band is not actual independence, safety or community function.
**Partial-coverage example:** Speed is supplied, but its relation to reference support or matching limitation is missing.
**Clarification:** One sentence may satisfy both C01 and G03; no duplicate caveat is required. The disease-attribution limit is assessed under G03 rather than counted twice as a separate omission.

### C02 (historical source: C02)

Identify the knee as the largest joint-curve difference AND include the ankle and hip as the next prominent differences.

**Logic:** AND for the named priorities; synonyms accepted
**Optional:** GVS 22.24/12.53/12.32 degrees; ankle ROM 13.4 degrees is a measurement, not an established restriction. Exact ankle-versus-hip ordering need not be emphasized.
**Partial-coverage example:** Only some required joints are discussed, or the stated relative priority is absent.
**Clarification:** No unseen curve direction, phase, exact plot-derived morphology or clinical severity is required.

### C03 (historical source: C03)

Identify GAS as a principal numerical EMG difference AND describe it as above the phase-specific reference mean at approximately 80% of the analysis cycle. Its reported max |z| is 13.3.

**Logic:** AND for muscle, above-mean direction, approximate cycle location and prominence; prominence may be conveyed by the supplied magnitude or a within-case ranking
**Optional:** Exact numerical repetition is unnecessary if the main finding and direction/location are clear. A supplied empirical endpoint comparison is optional; clinical normality need not be determined.
**Partial-coverage example:** Names the muscle and magnitude, but does not communicate the above-mean direction or cycle location.
**Clarification:** Direction relative to the mean is not percentile exceedance. Cycle location is not amplitude-peak timing or an inferred gait phase.

### C04 (historical source: C04)

Describe ST above the reference mean at about 35% AND VL below the reference mean at about 5%. Their max |z| values are 7.0 and 5.3.

**Logic:** AND for both muscles and their respective directions/approximate locations
**Optional:** TA below at 0% and RF below at 6% are optional. No muscle-strength inference is required.
**Partial-coverage example:** Discusses only ST, or names both muscles but omits VL below-mean direction.
**Clarification:** Exceeding a percentile is not a substitute for identifying the signed mean-relative direction.

### SL01 (historical source: NEW-stroke_Sub05_P-01)

Report the supplied successive-footfall step-length index (-23.1%) AND convey the paretic step is shorter.

**Logic:** AND; no formula recitation required
**Optional:** May be combined with speed/cadence; spelling out the operational definition again is optional.
**Partial-coverage example:** Gives the index without its directional/near-zero meaning, or gives only a vague asymmetry statement without the supplied index.
**Clarification:** Preserves the four previously confirmed step-index requirements under a new prospective ID. The index is not the percentage shortening relative to the other side.


## stroke_Sub50_P

[Exact user input](../../expert_trial/data_cards_v7_candidate/stroke_Sub50_P/model_user_prompt.txt)

### C01 (historical source: C01)

Describe speed 0.83 m/s AND describe it as near the lower end of the supplied 0.80–1.79 m/s span AND make clear that the pooled comparison is not thereby speed-matched.

**Logic:** AND; factual case-speed requirement is separate from G03
**Optional:** Cadence and speed-band label are optional. If used, the band is not actual independence, safety or community function.
**Partial-coverage example:** Speed is supplied, but its relation to reference support or matching limitation is missing.
**Clarification:** One sentence may satisfy both C01 and G03; no duplicate caveat is required. The disease-attribution limit is assessed under G03 rather than counted twice as a separate omission.

### C02 (historical source: C02)

Identify pelvis as the largest GVS difference AND knee as another prominent difference; distinguish the large pelvic GVS from the small supplied pelvic ROM.

**Logic:** AND for the named priorities; synonyms accepted
**Optional:** Pelvis/knee GVS 9.56/7.75 degrees; pelvic ROM 3.8 degrees. No pelvic offset direction is required; it is not in the model input.
**Partial-coverage example:** Only some required joints are discussed, or the stated relative priority is absent.
**Clarification:** No unseen curve direction, phase, exact plot-derived morphology or clinical severity is required.

### C03 (historical source: C03)

Identify ST as a principal numerical EMG difference AND describe it as above the phase-specific reference mean at approximately 33% of the analysis cycle. Its reported max |z| is 4.7.

**Logic:** AND for muscle, above-mean direction, approximate cycle location and prominence; prominence may be conveyed by the supplied magnitude or a within-case ranking
**Optional:** Exact numerical repetition is unnecessary if the main finding and direction/location are clear. A supplied empirical endpoint comparison is optional; clinical normality need not be determined.
**Partial-coverage example:** Names the muscle and magnitude, but does not communicate the above-mean direction or cycle location.
**Clarification:** Direction relative to the mean is not percentile exceedance. Cycle location is not amplitude-peak timing or an inferred gait phase.

### SL01 (historical source: NEW-stroke_Sub50_P-01)

Report the supplied successive-footfall step-length index (-0.7%) AND convey the index is near zero, indicating a small difference under this step-length definition rather than proof of overall gait symmetry.

**Logic:** AND; no formula recitation required
**Optional:** May be combined with speed/cadence; spelling out the operational definition again is optional.
**Partial-coverage example:** Gives the index without its directional/near-zero meaning, or gives only a vague asymmetry statement without the supplied index.
**Clarification:** Preserves the four previously confirmed step-index requirements under a new prospective ID. The index is not the percentage shortening relative to the other side.


## stroke_Sub47_P

[Exact user input](../../expert_trial/data_cards_v7_candidate/stroke_Sub47_P/model_user_prompt.txt)

### C01 (historical source: C01)

Describe speed 0.54 m/s AND explain that it is below the reference speed floor of 0.80 m/s, so this dataset supplies no healthy reference at that speed.

**Logic:** AND; factual case-speed requirement is separate from G03
**Optional:** Cadence and speed-band label are optional. If used, the band is not actual independence, safety or community function.
**Partial-coverage example:** Speed is supplied, but its relation to reference support or matching limitation is missing.
**Clarification:** One sentence may satisfy both C01 and G03; no duplicate caveat is required. The disease-attribution limit is assessed under G03 rather than counted twice as a separate omission.

### C02 (historical source: C02)

Summarize the hip, knee AND ankle as the main available sagittal joint-curve differences.

**Logic:** AND for the named priorities; synonyms accepted
**Optional:** GVS 11.73/9.46/7.62 degrees; avoid compulsory listing of all values.
**Partial-coverage example:** Only some required joints are discussed, or the stated relative priority is absent.
**Clarification:** No unseen curve direction, phase, exact plot-derived morphology or clinical severity is required.

### C03 (historical source: C03)

State that participant EMG is unavailable AND that its envelope timing, amplitude and CCI cannot be assessed.

**Logic:** AND; a concise statement that all EMG-derived interpretation is unavailable satisfies the domains collectively
**Optional:** Available gait/kinematic findings remain reportable. A brief unavailable-EMG section is sufficient; no fabricated EMG text is required.
**Partial-coverage example:** States only that EMG is missing, without conveying that its derived timing, amplitude and CCI cannot be assessed.
**Clarification:** A clear unavailability statement can satisfy coverage even if a separate later claim is erroneous; record that assertion independently. Do not infer absence of muscle activity.

### SL01 (historical source: NEW-stroke_Sub47_P-01)

Report the supplied successive-footfall step-length index (-15.4%) AND convey the paretic step is shorter.

**Logic:** AND; no formula recitation required
**Optional:** May be combined with speed/cadence; spelling out the operational definition again is optional.
**Partial-coverage example:** Gives the index without its directional/near-zero meaning, or gives only a vague asymmetry statement without the supplied index.
**Clarification:** Preserves the four previously confirmed step-index requirements under a new prospective ID. The index is not the percentage shortening relative to the other side.


## control_Sub49_avg

[Exact user input](../../expert_trial/data_cards_v7_candidate/control_Sub49_avg/model_user_prompt.txt)

### C01 (historical source: C01)

Objectively identify knee AND ankle as the relatively larger joint-curve differences in this case.

**Logic:** AND for the named priorities; synonyms accepted
**Optional:** GVS 5.86/3.86 degrees; GPS-like 3.75 and supplied backgrounds may be compared descriptively without proving overall normality.
**Partial-coverage example:** Only some required joints are discussed, or the stated relative priority is absent.
**Clarification:** No unseen curve direction, phase, exact plot-derived morphology or clinical severity is required.

### C06 (historical source: C06)

Respect healthy-control provenance AND describe the self-excluded leave-one-out comparison. IF speed/cadence or step symmetry is discussed, accurately distinguish not supplied from not applicable.

**Logic:** AND for control provenance and self-exclusion; conditional missing/applicability statements only when those domains are discussed
**Optional:** 137 reference participants may be stated; verbatim count repetition is not required if self-exclusion is explicit. No obligation to enumerate every unavailable variable when not discussed.
**Partial-coverage example:** Identifies the control group but omits self-exclusion; or addresses speed/cadence as measured or the paretic index as simply a missing control measurement.
**Clarification:** Updated to approved v3.1: the task-specific paretic/non-paretic index is not applicable. General left/right symmetry remains definable. Pooled calibration is not a matched LOO normal limit.

