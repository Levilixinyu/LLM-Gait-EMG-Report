# Main dataset suitability assessment

Subject: Van Criekinge et al., 2023, gait data from 138 healthy adults and 50 stroke subjects.
Date: 2026-09-16.

## Conclusion

**It can continue to serve as the main dataset for this project. Its most suitable use is to evaluate whether LLMs can faithfully describe validated kinematic and normalized EMG features, appropriately express uncertainty, and generate research reports for expert evaluation.**

By itself, it cannot provide a gold standard for all clinical interpretations, nor is it sufficient on its own to validate automated diagnosis, judgments about spasticity/muscle weakness mechanisms, treatment selection, treatment outcome prediction, or cross-hospital deployment capability. Abandoning this dataset because of the current code errors is not recommended; the methods of use need to be fixed and the research conclusions narrowed.

## Scope of verification and evidence

The methods and limitations of the main paper, official supplementary tables, variable-description Excel file, public file metadata, two local data Excel files, and stroke MAT files have been checked. Previous recalculations covered 138 controls and both sides of 50 stroke participants, validating 1100 stroke Excel/MAT curves and 100 published walking speeds.

Further checks in this review: the number of participants with actually usable EMG, correspondence between clinical tables and MAT files, assisted-walking records, walking-speed support ranges of the two groups, and stride-by-stride EMG completeness in MAT files. Not all continuous C3D signals were re-reviewed, and the complete healthy-participant MAT files were not downloaded; “mean curves are readable” cannot be described as all raw signals having passed quality review.

## 1. The data content is sufficient to support the current descriptive task

| Data level | What it can be used for | What should not be done on this basis |
|---|---|---|
| Two Excel files: 1001-point mean curves per participant | Describing mean waveforms for four sagittal-plane kinematic measures and normalized EMG from seven muscles | Reconstructing stride-to-stride fluctuations, raw noise, or physiological onset in the actual time domain |
| Downloaded stroke MAT files | Side-specific/stride-by-stride curves, individual events, clinical variables, and additional three-dimensional variables | Treating all existing fields as quality-validated or as clinical conclusions |
| Healthy-participant MAT files not yet downloaded | Further constructing side-specific, stride-by-stride healthy references using symmetric processing | Claiming that all healthy stride-level data have been validated before reading them |
| Released raw C3D files | Reviewing raw EMG, events, and force-plate contacts when necessary | Assuming raw signals have been reviewed merely because the files are public |
| Supplementary materials | Checking demographics, clinical scores, assisted-walking status, and walking speed | Replacing complete case histories, expert reports, or diagnostic gold standards |

Muscle names and laterality have explicit mappings; the main dataset does not have the same obstacle as the external CSV, where the muscles corresponding to EMG1–16 cannot be confirmed. The seven muscles cover some important walking muscle groups, but not all muscles in the body; the model must not invent functions of muscles that were not recorded.

## 2. EMG sample size should be described using the number of participants with actually usable data

The following concerns finite-value completeness in the currently processed Excel files, not certification that the raw signal-to-noise ratio is adequate:

| Sample | Total participants | All seven channels complete | Partial channels | No valid EMG |
|---|---:|---:|---:|---:|
| Healthy controls | 138 | 102 | 7 | 29 |
| Stroke affected side | 50 | 43 | 3 | 4 |
| Stroke unaffected side | 50 | 44 | 2 | 4 |

The number of healthy participants with valid data varies from 106–109 across muscles; not all EMG references can be reported as n=138. The current mean curves for all four kinematic measures are complete for all participants.

Cases with partial channels on the affected side: Sub37, Sub45, and Sub46 each have only 1 valid channel; no valid EMG: Sub08, Sub43, Sub47, and Sub48. These cases can be used for missing-information experiments or kinematic reports, but cannot be used to evaluate EMG interpretation capability without distinguishing them from complete cases.

The original paper recorded whether analog acquisition was performed, whereas the current statistics concern whether the released processed curves are usable; participant counts differ between these two levels, so it cannot be directly concluded that the files are corrupted or that all missing data were caused by electrode failures.

It is recommended that the primary analysis use predefined completeness rules, with a separate missing-information analysis. The 43 participants with complete affected-side data represent a candidate sample size and still require quality checks; this does not mean that 43 clinically fully interpretable cases have already been obtained.

## 3. The most important reference limitation: most patients walk more slowly than all healthy controls

Supplementary Table 5 was parsed independently, averaging the published walking speeds for both sides of each participant:

| Population | Minimum walking speed | Median | Maximum walking speed |
|---|---:|---:|---:|
| Healthy controls, n=138 | 0.8028 | 1.1842 | 1.7930 |
| Stroke, n=50 | 0.1116 | 0.4001 | 1.3464 |

Unit: m/s. **41/50 patients walk below the minimum walking speed of the healthy controls.**

Therefore:

- The current healthy reference represents “the performance of this group of healthy participants at their self-selected speeds.”
- For most patients, there are no speed-matched healthy participants within the data, and simple filtering cannot resolve this.
- Age matching does not simultaneously eliminate walking-speed differences.
- Fitting a regression over the normal walking-speed range and then extrapolating to 0.1–0.4 m/s does not automatically establish reliable slow-speed norms.
- The degree of deviation from the reference can be described, but not all differences can be attributed to stroke-specific abnormalities in neural control.

If the goal is to distinguish the contributions of “slow speed itself” and “stroke pathology,” suitable controlled slow-speed data from healthy participants or other independent evidence are needed. The project need not resolve this physiological attribution question at its current stage, but the prompts, expert scoring, and paper conclusions must respect this boundary.

## 4. Population and clinical labels need to be used cautiously

The local MAT files show: age of stroke participants 19–85 years, median 68.5 years; time since stroke 14–139 days, median 45.5 days. The main cohort cannot be described as a representative sample of chronic stroke. The released data come from a population with specific recruitment criteria who could complete laboratory walking, and do not represent all stroke patients.

The following inconsistency must be explicitly retained: the paper's methods describe excluding FAC≤2 and TIS≥20, but the supplementary tables/MAT files contain 18 participants with FAC=2 and records with TIS=20. The released values should be reported, noting that the recruitment description and records are not fully consistent; if an explanation is needed, it should be verified with the authors. Scores must not be arbitrarily changed, participants removed, or an explanation involving “changes in assessment dates” fabricated.

The supplementary materials record assisted walking for TVC48, TVC51, and TVC54, corresponding to project cases Sub41, Sub43, and Sub46. Assistance status should be included in the case descriptions, or a sensitivity analysis should be predefined; the entire cohort must not be described as walking fully independently without assistance.

The control group is a healthy population screened for the study, not a clinical gold standard in which every potential pathology has been definitively ruled out. Unsupported pathological interpretations can therefore be evaluated, but a model questioning the label cannot be judged to have discovered a real occult disease merely on that basis.

## 5. Usable kinematics/EMG does not mean kinetics can be added directly

The authors specifically caution that valid-contact and quality checks for kinetics in the stroke group were insufficient. The project must not directly infer insufficient propulsive force, compensatory mechanisms, or treatment recommendations merely because GRF, moments, and power are present in the MAT files. If kinetics are added, valid foot contacts, gait events, and outliers should be reviewed separately, returning to C3D when necessary.

EMG is normalized to each individual's muscle peak and is better suited to studying relative waveforms and timing. Normalized peaks do not represent absolute force and do not support direct comparisons of strength across muscles. The Excel data have already been averaged, masking stride-to-stride differences; when necessary, valid stride counts and variability should be provided from the MAT files.

The project's existing issues involving max|z|>2, single-interval activation, and uncalibrated CCI are defects in use/interpretation, not evidence that the original data are useless. These should be fixed before evaluating the models.

## 6. No ready-made clinical report ground truth is available; evaluation standards need to be developed

The currently released files provide measurements and some clinical variables, but no complete expert report for each participant, comprehensive mechanism diagnoses, or treatment outcome labels for direct comparison.

Three levels of evaluation should be separated:

1. **Numerical facts**: values, laterality, intervals, and rankings, which can be verified through independent calculations.
2. **Interpretive boundaries**: whether an inference exceeds the supplied evidence, requiring predefined scoring rules and expert judgment.
3. **Actual clinical conclusions**: whether a specific pathological mechanism exists and which treatment is effective, requiring additional case information and clinical validation.

Research at the first two levels can be completed, but should not be described as having validated the third level. FAC, TIS, and POMA are not answers to every statement either; if used as a prediction endpoint, a measure must not simultaneously be leaked to the model as input.

## 7. Recommended study design

- Treat the current 18 participants as development/pilot-stage cases; repeated use for prompt refinement must be disclosed, and the same group can no longer be treated as a completely unseen confirmatory test set.
- Establish a fixed quality table for all 50 participants and determine the primary-analysis and missing-data experiment samples according to predefined rules. Complete cases may be subject to selection bias, so the basic characteristics of included/excluded participants should be compared.
- Retain the four kinematic measures and use all EMG activation intervals, individual events, metric definitions, valid stride counts, and reference limitations.
- Use symmetric processing methods for patients and healthy references as far as possible. For formal comparisons of stride-to-stride variability or bilateral features, obtain the healthy-participant MAT files; the current experiment describing mean curves does not require immediate downloading of all raw C3D files for this purpose.
- Use an independent/leave-one-out reference to evaluate healthy participants; if thresholds need to be selected, distinguish development from final evaluation.
- Expert scoring should use the participant as the repeated-measures unit. Left and right sides, multiple gait cycles, and multiple model outputs must not be passed off as independent patients.
- Describe the work externally as a “single-dataset, retrospective, exploratory evaluation of LLM reports.” Leave cross-center reliability, treatment recommendations, and actual clinical deployment for subsequent validation.

## 8. Decision table

| Objective | Judgment | Prerequisite |
|---|---|---|
| Generate descriptive reports from validated features | Usable, suitable for the current project | Fix extraction and input specifications, and establish expert scoring |
| Compare models' faithfulness, over-inference, and handling of missing information | Usable | Fix tasks and scoring criteria, and avoid post hoc rankings |
| Joint analysis of mean EMG patterns and kinematics | Conditionally usable | Clearly state normalization, speed differences, and reference limitations |
| Precise validation of raw EMG onset | Current Excel files are insufficient | Continuous signals, processing pipeline, and event validation |
| Demonstrate spasticity, muscle weakness, or specific pathological mechanisms | These data alone are insufficient | Additional clinical ground truth and corresponding validation |
| Directly interpret stroke kinetics | Unchecked fields cannot be used directly | Independent review of valid contacts and signal quality |
| Predict treatment outcomes or demonstrate effective clinical deployment | Not supported by the current study | Corresponding longitudinal outcomes/independent clinical validation |

Basis: [original paper](https://www.nature.com/articles/s41597-023-02767-y), [official data collection](https://doi.org/10.6084/m9.figshare.c.6503791.v1), local official supplementary materials `sources/VanCriekinge_2023_supplement.pdf`, variable descriptions `../data/raw/MATdatafiles_description.xlsx`, and direct local recalculations.

New recalculation program: `assess_main_dataset.py`; outputs: `outputs/main_dataset_suitability.json`, `outputs/main_dataset_stride_emg_quality.csv`. See the previous review report for the remaining foundational evidence.

## Supplement: completed results of this stride-by-stride check

- Checked 50 participants×2 sides×7 muscles, totaling 700 MAT channel entries; nonempty channels had 2–17 valid strides, with a median of 8. No partially NaN strides were found, nor any channels with only 1 valid stride. Valid stride counts differ, so stride counts and variability should also be recorded when reporting means.
- 43 participants had complete data for all seven muscles bilaterally. Of these, 34 still had a bilateral mean walking speed below the minimum healthy reference value; excluding cases with missing data will not resolve insufficient speed-range support.
- Age, sex, time since stroke, lesion side, FAC, POMA, and TIS for all 50 participants in Supplementary Table 2 matched the corresponding MAT values. The FAC/TIS inconsistency is therefore an issue between the paper's inclusion description and the released clinical records, not an error in this MAT reading or participant ordering.
- The healthy-control 20–39-year age group contains 45 participants, only 23 of whom have all seven channels complete; the figures are 37/44 for ages 40–59, 29/34 for ages 60–79, and 13/15 for those over 80. The age composition of the EMG-complete sample differs from that of the full healthy population, so missingness cannot be assumed to be completely random.
- Previous event checks identified 1 stride with non-positive duration on the affected side of Sub43; the existing spatiotemporal parameter calculation excludes it. Subsequent stride-by-stride analyses must inherit a consistent quality mask and must not treat all array rows as usable gait cycles.
