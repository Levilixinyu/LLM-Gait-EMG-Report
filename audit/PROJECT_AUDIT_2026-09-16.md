# LLM-Gait-EMG-Report Project Review

Review date: 2026-09-16. Review scope: the current local project, corresponding Claude conversation records, original public data files, and supplementary materials. This review only added review materials under `audit/`; it did not modify production source code, README, original data, or generated reports, and did not call paid models to regenerate reports.

## Conclusion and scope

The project has completed a runnable exploratory prototype: loading data, extracting features, selecting 18 stroke subjects, generating 54 reports from three models and 18 rating packets, and additionally generating 12 reports for 4 healthy controls. These engineering outputs genuinely exist; however, “feature extraction has been validated,” “the healthy-control false-positive check passed,” and “Claude is clearly superior to the other models” go beyond the available evidence.

The most important obstacles concern feature input and evaluation design: the extraction program outputs only the first EMG activation interval, README threshold statistics are inconsistent with the production program, and peak absolute z scores have not been calibrated as clinical abnormality thresholds. These directly affect report content and comparisons between models. Inputs should be fixed and frozen before formal blinded expert rating.

This review read the text records of the corresponding Claude conversation, inspected the project implementation and the structure/termination information of all 66 reports and 54 rating-packet correspondences; recalculated bilateral features for all 138 healthy controls and 50 stroke subjects; compared 1100 stroke Excel/MAT curves, and checked 100 bilateral walking-speed values in the supplementary materials. Report content was examined through case tracing and focused paragraph-by-paragraph review, **without pretending to have completed independent clinical expert ratings of 66 reports**. Not all original continuous C3D data were reviewed, nor were subjects' actual medical histories recollected or verified.

## 1. Components confirmed to be correct

- The MD5 values of the five main downloaded files all match the official Figshare records; no download truncation or file mismatch was found.
- The 1100 stroke Excel curves match the corresponding gait-cycle averages in MAT; subject order, bilateral correspondence, and sagittal-plane selection are valid. Scanning 2618 curves found no partial NaN values or infinities; entire curves are missing in some cases and require different handling.
- Features can be extracted for all 138 controls and 100 stroke sides; the 18-person trial subset with seed=42 is reproducible, with 6 people in each of the three speed strata.
- Calculated walking speeds match the 100 published values in the original paper's Supplementary Table 5 to their four-decimal-place precision, with a maximum absolute difference of 0.00004972 m/s. This is validation independent of “appearing to fall within a clinical range.”
- All 66 reports are nonempty, all saved termination statuses are normal, and none has a truncation flag; the 54 rating-packet texts match their source reports. “Normal completion” cannot be further interpreted as “correct clinical content.”
- No model self-identification by name was found in the current reports, so the anonymization code defect described below has not yet caused actual name leakage in this batch of reports.
- Claude did fix truncation tracking, API parameters, environment-variable loading, and the early near-zero step-length issue. The mathematical implementation of GPS-like as the RMS deviation of four sagittal-plane variables is largely valid, and it has already been stated that this is not the complete standard GPS.

Checksums of the main files:

| File | MD5 |
|---|---|
| AbleBodiedAdults.xlsx | 7d6585bb1bfd61f53840aa3a0eb288de |
| PostStrokeAdults.xlsx | d79ec047d50f5a957d164a25bffabf32 |
| MAT_normalizedData_PostStrokeAdults.mat | b866f174a3e7cd17aa5652f5383a5d4c |
| MATdatafiles_description.xlsx | 91e19f0c0bbac2cabab087bf17cbbc65 |
| NrStrides.xlsx | d66c33d1b460dfd7dec38767453b484e |

## 2. High priority: retaining only the first activation interval has already affected actual reports

Location: `onset_offset_pct_from_cycle()` in `src/features/emg_signal.py`. It returns as soon as it finds the first interval meeting the threshold and minimum-duration requirements, discarding all subsequent intervals; continuous activation crossing the 0/100% cycle boundary is also not handled circularly. The input text does not explicitly state “this is only the first interval.”

The 18-person trial subset contains 113 valid EMG curves, of which 92 contain multiple qualifying linear intervals and 79 are above threshold at both ends of the cycle. Here, “multiple linear intervals” does not mean multiple independent physiological bursts; the two ends of the cycle may belong to the same continuous activation.

- **Sub50 affected-side TA**: under the production threshold, there are two intervals, 0–7.09% and 56.74–100%; the model received only 0–7%. Gemini's report used “Absence of Swing-Phase TA Activation” as an issue heading and raised follow-up questions about foot drop/proximal compensation. The signal in the latter half of the cycle clearly exists; it was omitted by the program. This is overinterpretation induced by an input defect and cannot be attributed entirely to the model's own capabilities.
- **Sub05 affected-side GAS**: there are two intervals, 24.98–37.76% and 74.53–86.61%, but the model received only the first; the maximum absolute z=13.33 occurs at 80.3%, in the omitted later interval. At this point, the patient value is 0.3495, the control mean is 0.0419, and SD=0.0231. This large deviation cannot be categorically described as “an artifact caused by near-zero SD” without examination. Phase percentages alone should also not replace individual toe-off in determining the specific stance/swing phase.
- “not detected” only means that no interval met the specified threshold and minimum-duration requirements; it does not mean no muscle activity or loss of muscle function.

Fix: output all retained intervals, total duration proportion, and cycle-boundary status; specify the threshold and minimum duration. Incorporate the available individual gait events. If the mean envelope continues to be used, call these “above-threshold intervals of the mean envelope,” rather than claiming to have obtained original step-by-step physiological onsets.

## 3. High priority: README threshold statistics are not the production pipeline statistics

The original data were normalized by the maximum across available gait cycles for each muscle of each person and then averaged, so the mean curve's peak need not equal 1. The production program compares `curve > 0.2`; Claude's diagnostic statistics compare `curve > 0.2 * curve.max()`. These are different.

Recalculation using the same data of “at least 95% of sampled points above threshold”:

| Muscle/population | 0.2×mean curve peak used in README | Fixed 0.2 in production program |
|---|---:|---:|
| ERS stroke affected side | 32/46 | 12/46 |
| ERS healthy controls | 37/106 | 3/106 |
| GAS stroke affected side | 9/43 | 1/43 |
| GAS healthy controls | 0/109 | 0/109 |
| BF stroke affected side | 15/43 | 2/43 |
| BF healthy controls | 7/106 | 3/106 |

The source of the README numbers has been reproduced exactly. The table itself was not fabricated, but it was used to explain a different algorithm; the conclusion that “35% of healthy ERS shows full-cycle activation” cannot be applied to the current input. Another definitional issue is that “≥95% of points above threshold” does not mean “no off points at all” or that the program returns a complete continuous 0–100% interval.

The intended threshold definition should be selected and explained, sensitivity analysis performed, and the table and interpretation then rewritten; merely changing the wording to make the numbers appear consistent is not sufficient.

## 4. High priority: the healthy-control check has not established a valid abnormality criterion

The current `deviation_z_peak` is the maximum absolute z value among 1001 phase points, losing direction and the phase of occurrence. It does not have the interpretation of a z score for a single fixed observation, and “>2 SD” cannot be directly used as a clinical abnormality threshold for the entire curve/individual.

Recalculated results: **109 healthy controls with EMG, and 109 with max|z|>2 in at least one muscle**. For example, RF was 58/108 and TA was 58/107. For each muscle, the 95th percentile of this statistic in the healthy sample was approximately 3.65–4.61, not 2. Here, healthy participants also contributed to the calculation of their own reference mean and SD; leave-one-out calculations generally increase their scores further. The percentages above reflect the behavior of the statistic, **not that 109 healthy people have a disease, nor that the LLM diagnostic false-positive rate is 100%**.

Similarly, the healthy-control RF–BF CCI median was 0.676, with sample 2.5–97.5 percentiles of 0.483–0.825. Directly calling 0.63 or 0.65 “abnormally elevated” is not supported by this cohort. These percentiles serve only to illustrate internal calibration and do not constitute a clinical diagnostic reference interval.

GPS-like values for the four spot-check controls:

| Participant | Age | GPS-like | Empirical percentile among 138 controls |
|---|---:|---:|---:|
| Sub10 | 81 | 7.19 | 81.16 |
| Sub49 | 60 | 3.72 | 22.46 |
| Sub93 | 39 | 4.40 | 37.68 |
| Sub98 | 36 | 4.05 | 27.54 |

The 95th percentile of GPS-like across all controls was 10.71. Sub10 is not an extreme kinematic outlier in this cohort; questioning the healthy label is not inherently a higher-order form of correct reasoning. Using another 22 controls aged ≥75 as an exploratory reference changed the score to 6.05, but this is insufficient to establish that age explains all the differences.

In addition, the input explicitly stated `Group: control`. This experiment can investigate “how deviations are explained when the label is known,” but cannot be called a normal/abnormal identification experiment with unknown labels. The 12 calls for 4 participants×3 models are not 12 independent cases either.

## 5. Claude's work and conclusions: retain the contributions, withdraw the ranking

Reasonable aspects: In several reports, Claude did point out cycle boundaries, the possible omission of a second activation segment, and possible nonpathological explanations for EMG/kinematic differences; this is more cautious than directly treating what was not reported as nonexistent.

Aspects that are unsupported or require revision:

1. “No specific disease name was given” does not mean “there was no unsupported pathological interpretation.” The Gemini report for Sub49 called CCI=0.63 elevated and proposed a stiffness/restriction interpretation for the 1.6° pelvic ROM; its plane and reference range had not been passed to the model in the first place. Claude also called CCI=0.63 high in the same case and treated >2 SD as evidence of internal inconsistency. These should all be scored against predefined criteria.
2. For Sub50, Claude wrote “6.86 is lower than three of the four GVS values,” with 5.41 among the listed values; in fact, only 9.56 and 7.75 are higher than 6.86. This is a clear arithmetic error; the agent's subsequent description of this discussion as excellent analysis was insufficiently cautious.
3. The Sub10 report interpreted some deviations as increased amplitude, whereas the input contained only nondirectional max|z|, which cannot determine an increase versus a decrease, or amplitude differences versus temporal misalignment.
4. “Claude is clearly stronger” was based on a small number of unblinded, post hoc selected cases, without independent expert scoring or uncertainty estimates. At most, this can generate a qualitative hypothesis to be tested.
5. GPT's caution cannot simply be dismissed as boilerplate: the input genuinely lacked the plane, reference intervals, normalization, and metric definitions. Factual accuracy, the ability to explicitly identify supportable conclusions, and report utility should all be evaluated; making more inferences cannot automatically be judged better.

Nor can GPT or Gemini be declared better in the opposite direction at this stage. This audit has not completed a model ranking.

## 6. The model input omitted information that was already available

`to_prompt_text()` in `src/features/pipeline.py` should explicitly specify: the sagittal plane, units, mean-envelope normalization method, CCI formula, max|z| definition and its sign/phase, GPS-like components, and the formulas and directionality of symmetry metrics. Where necessary, include the corresponding reference distributions, phase-interval summaries, or traceable curves.

The MAT files already contain age, sex, time since stroke, clinical scores, bilateral information, and gait events; the supplementary materials also contain healthy-participant demographics and walking speed. These have not currently been passed to the model, and explanations should not broadly state that this information does not exist in the dataset. The mean toe-off phase on the affected side varies substantially across participants; a fixed percentage from healthy people cannot be used to define everyone's swing phase.

Peak-normalized EMG is not absolute force or activation intensity, and should not be used to directly compare “weaker” activity across muscles. Control curves pool both sides, whereas stroke curves are separated by side, and factors such as age/walking speed were not strictly matched; “the same study protocol” does not mean a clinically matched reference.

## 7. Dataset and literature descriptions

- The stroke inclusion criterion for the main Van Criekinge 2023 dataset was within 5 months of onset; TPS in the MAT files was 14–139 days. Describing it as a chronic stroke cohort on line 163 of the README is inaccurate. Do not confuse it with another chronic stroke dataset.
- The statement on line 66 of the README that there are no precomputed spatiotemporal parameters is overstated: Supplementary Table 5 published walking speeds, which were successfully aligned in this audit. The MAT files remain valuable for calculating other parameters and conducting consistency checks.
- The MAT files are a processed, cycle-normalized release, not raw continuous EMG; genuine raw onset validation requires continuous signals and reliable events.
- Missing all channels does not automatically indicate electrode failure or exclusion for data quality; the original study documented that analog signals were not collected for some participants. The actual reason for missingness should be recorded, and explicitly marked unknown when unknown.
- The external dataset from Hohsoh et al. 2024 (called the Chatpun study in the README) does exist. `N2_Trial01.csv` (19,104,899 bytes), which Claude had used, was downloaded again: the unit of Fz is indeed N, with maxima across the three platforms of approximately 19.93, 60.10, and 0; the FootSwitch channels are approximately ±0.2V. Thus, Claude's observation of a lack of clear foot-ground contact in this **one file** is largely reproducible, rather than a misinterpretation of voltage as newtons. The paper/public metadata did not provide a directly usable EMG1–16 muscle-and-side mapping; a mapping guessed from typical waveforms cannot then be treated as external ground truth. Not all 32 CSV files were downloaded again/reviewed, so it cannot be asserted that all trials are unusable.
- The relevant 2026 papers are retrievable and cannot be judged fictitious based on the year or model names. The tasks, abnormal-case selection, and input rules in needle EMG/electrodiagnostic report studies differ from those in this project; their performance conclusions or normal/abnormal classification criteria cannot be transferred directly.

Sources: [Main data paper](https://www.nature.com/articles/s41597-023-02767-y), [Official data collection](https://doi.org/10.6084/m9.figshare.c.6503791.v1), [Original paper supplementary materials](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41597-023-02767-y/MediaObjects/41597_2023_2767_MOESM1_ESM.pdf), [External study](https://pubmed.ncbi.nlm.nih.gov/39553714/), [External dataset](https://doi.org/10.6084/m9.figshare.26065414.v1), [Related gait study](https://www.frontiersin.org/journals/medical-technology/articles/10.3389/fmedt.2026.1863908/full), [Electrodiagnostic report study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13332575/).

## 8. Other implementation defects and unresolved issues

**There is a normalization comparison error in the RawTrialData path.** In `pipeline.py`, unnormalized `mean_cycle` is compared with the normalized healthy reference, while other outputs for the same muscle use `norm_cycle`. When the same synthetic signal was amplified 10-fold, with the normalized waveform unchanged, TA z changed from 370.58 to 967.72. This defect does not affect the 54 reports from the current Excel path, but invalidates the statement that “both paths have been validated.” Although `detect_onset_offset()` is implemented, it has not been integrated into the current raw feature-extraction path. There is only 1 existing test, which passed in the audit environment, indicating that it is insufficient to catch these issues.

**The step-length definition must be clarified; this is not yet judged a confirmed algorithmic error.** The documentation says “the distance between the feet at the instant of contralateral foot contact,” while the code subtracts the previous ipsilateral contact position from the contralateral contact position. The distance between successive foot placements and the distance between markers at the same instant are different operational definitions; neither can be declared ground truth without confirming the protocol. In sensitivity results calculated using the positions of both feet at the same instant instead, the Sub45 symmetry index changed from +5.80% to −0.27%, and Sub03 from −81.35% to −89.93%. The existing “sum of step lengths≈stride length” is internal consistency and is insufficient on its own to be called ground-truth validation. The independent speed cross-check passed and is unaffected by this dispute.

**Potential anonymization defect.** `src/eval/blinding.py` replaces vendor terms before replacing full model IDs, causing full matches to fail: `gemini-3.1-pro-preview` becomes `[model]-3.1-pro-preview`, leaving the version identifiable. The current reports contain no such self-identifications, so no actual leakage was found in this instance. Full IDs should be replaced first. File enumeration is unsorted, and the order for reconstruction across environments still needs to be fixed; a local test with reversed file-creation order produced the same order, so it cannot be claimed that randomization inconsistency has already been observed empirically.

**The scoring scheme is still incomplete.** The scoring package contains only anonymous IDs and report text, without fact-checking inputs, formal scoring forms, or adjudicated reference answers. Report lengths differ markedly across the three models (22 reports/model, median character counts Claude9977, GPT3944, Gemini4734), which may affect preference judgments; this is not confirmed unblinding. It should be specified which data clinical raters receive and how to distinguish insufficient input from model errors, and length/format factors should be evaluated.

**Insufficient reproducibility.** Saved records include the requested model name, version string, and termination information, but do not fully preserve the input and system prompt used for that call, source-code/data hashes, actual responding model version, parameters, usage, request ID, etc. The currently reconstructed `pilot_inputs.txt` was rebuilt from the current code, not archived from the original requests at the time. Dependencies are not locked; batch processing skips files solely based on their existence, so corrupted/truncated files may also be skipped. Tasks should be defined by input and configuration hashes, and existing artifacts should be validated before being skipped.

**Judgments about the runtime environment should be restrained.** Some local files had macOS dataless/cloud-placeholder status, causing long waits when reading files; it has not been established that “94% disk usage” was the root cause of the stalls.

## 9. Recommended next-step sequence

1. Retain existing outputs as v1 exploratory results and avoid overwriting the history.
2. Fix handling of multiple intervals and cycle boundaries, and standardize normalization/thresholds; clarify the step-length definition, and fix the raw path and anonymization.
3. Freeze the complete feature-input specification, adding the known plane, metric formulas, individual events, and reference calibration; validate the curve→feature→text chain for each representative case.
4. Use independent/held-out references or an explicit leave-one-out reference, and predefine the healthy-control experiment and error types; separate the “interpretation task with known labels” from the “identification task with hidden labels.”
5. Establish expert references and scoring forms, then generate v2 reports from the three models. Retain the same cases, fix parameters, and record all request/response metadata.
6. For the formal comparison, use participants as the repeated-measures units and account for the crossed structure of models, participants, and raters; 18 patients constitute an exploratory sample, not 54 independent samples. Report effects and uncertainty first, then consider conclusions about model superiority.

## 10. Audit evidence and recalculation

- `recompute.py`: full-data recalculation, MAT/Excel comparison, activation intervals and z-scores, and spatiotemporal parameter sensitivity.
- `validate_artifacts.py`: 66 reports, 54 scoring-package entries, anonymization and raw-path scaling tests.
- `postprocess.py`: supplementary-table walking-speed verification, threshold-table reproduction, control distributions and plots.
- `outputs/audit_evidence.png` / `.pdf`: omitted curves from two cases and healthy-control distributions.
- `outputs/audit_facts.json`, `artifact_checks.json`, `supplement_and_control_checks.json`: main statistics.
- `outputs/activation_windows.csv`, `z_scores.csv`, `mat_excel_comparison.csv`, `published_speed_comparison.csv`: item-by-item evidence.
- `outputs/external_sample_check.json`: summary of the external CSV; the original download is retained in a temporary directory, without altering the project's formal dataset.
- `sources/`: public supplementary materials, official Figshare metadata, and text extracted from external papers.

A separate temporary environment, `/private/tmp/gait-audit-venv`, was used, without patching the project's original virtual environment; see `audit_environment.txt` for the dependency list. Running the three scripts above in sequence from the project root directory recalculates the main results, provided that the original data and audit supplementary materials are readable. The scripts generate only audit artifacts and do not make model API requests.
