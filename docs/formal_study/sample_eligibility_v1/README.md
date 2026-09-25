# Prospective sample exposure and eligibility ledger

Prepared: 2026-09-18. Status: **decision support; no formal sample selected**.

The v3.1 interpretation instructions and rubric v2 have expert approval within their recorded scopes. This ledger implements the next administrative and technical step: identify prior case use and check the available data before choosing a new sample. It does not authorize report generation or approve a statistical design.

## Start here

Open [Sample_eligibility_and_decisions.xlsx](Sample_eligibility_and_decisions.xlsx). Read `Read first`, filter `Participants`, and use `Decision record` to record the study lead's decisions in a separately saved review copy. Decision, reviewer, date and comment cells are intentionally blank. All participant selections and external-exposure attestations remain pending.

The recommended starting point for planning is the **25-case conservative stroke pool**, subject to checking unrecorded exposure and deciding the scientific sampling strategy. This is a pool of available cases, not a required sample size or an approved held-out test set. The approved five-case annex cannot simply be reused as the case-specific reference standard for these new cases.

## Verified counts

| Cohort | Participants | Complete primary-side EMG | Partial EMG | No EMG | Participants with prior pilot/spot-check reports |
|---|---:|---:|---:|---:|---:|
| Stroke | 50 | 43 | 3 | 4 | 18 |
| Control | 138 | 102 | 7 | 29 | 4 |

All 238 available side records have four complete sagittal kinematic mean curves. Stroke records include P and N; control records use the released pooled `avg` curves. Both stroke sides have all seven EMG means in 43 participants. There are 44 complete N-side records, but N is not a second independent participant or an unexposed substitute for a previously used P side.

The report inventory contains 54 pilot reports for 18 stroke participants and 12 spot-check reports for 4 controls. The separate 15-report expert trial used five participants already among those 22; it adds report outputs, not new participants. Consequently, the number 66 is specifically the pilot/spot-check file count, not the total number of reports ever generated in this project.

| Planning filter | Remaining stroke participants |
|---|---:|
| Complete P-side EMG and kinematics, with valid current spatiotemporal data | 43 |
| Exclude the 16 complete cases already used for pilot reports | 27 |
| Additionally exclude individually audited Sub03 and Sub41 | 25 |

Sub03 was used to examine step-length definition sensitivity. Sub41 was explicitly identified in the assistance audit and has documented human assistance. These are distinct reasons for caution, not evidence that a report was generated for either participant. Other individually audited cases are already report-exposed or have incomplete EMG.

The 25 cases under this filter are **stroke** Sub01, Sub02, Sub07, Sub10, Sub13, Sub15, Sub16, Sub18, Sub19, Sub21, Sub22, Sub24, Sub25, Sub26, Sub27, Sub28, Sub29, Sub30, Sub33, Sub34, Sub35, Sub36, Sub38, Sub40 and Sub49. The group prefix is essential: stroke Sub49 is different from the control Sub49 used in the expert trial; the same distinction applies to Sub10.

Among controls, 98 complete-EMG participants have no pilot/spot-check report in the inventory. However, the healthy cohort has already supplied reference curves and calibration distributions wherever channels were available. These participants therefore support an internal reference-used challenge evaluation, not a claim of an untouched independent reference-validation cohort. Excluding a participant from their own mean reference by leave-one-out does not remove their previous contribution to cohort calibration or method development.

## What exposure means here

The ledger keeps distinct evidence types:

- **Prior report generation:** subject identifiers extracted from the two pilot/spot-check filename inventories. Report narratives and blinded identity keys were not read. Generation alone does not prove that a human read every report; exclusion from a new report-development holdout is the conservative planning choice.
- **Pilot and expert development:** the 18-case pilot list and five frozen trial case directories. The five cases also informed later candidate instructions and the rubric.
- **Targeted method or quality audit:** individually discussed cases in the original project audit and main-dataset suitability review. These are recorded separately from generated reports.
- **Cohort processing:** feature extraction and quality checks across the dataset. This is a known shared development exposure, but does not establish individual human report review.
- **Reference/calibration use:** the control cohort's role in the current empirical references. A missing channel did not contribute an available EMG curve for that channel.

The machine-readable [exposure evidence](exposure_evidence.csv) contains the source and locator for each recorded item. This is an evidence inventory, not a complete reconstruction of all past terminal sessions, external conversations or unregistered work. Before calling any selected cases prospective, the study lead must check additional exposure and document the operational definition of the holdout. Even the 25-case pool is not independent of all prior dataset-level method development.

Synthetic packaging tests mention Sub01 and Sub02 in `audit/review5/packaging_probes.py`, whose module explicitly describes synthetic reports in temporary directories. Those mentions alone do not establish exposure to the real dataset participants. Do not treat a bare subject string in every source file as proof of real-case use.

## Data checks and their limits

The builder compared all **2,618 current Excel curves** with the hash-verified audit cache, checked the recorded missing/finite sample counts, recomputed all **700 stroke muscle-side stride availability records**, and recomputed **100 stroke side-level spatiotemporal summaries**. They matched the existing evidence. The current stroke MAT and Excel hashes also match the prior normalization verification. Fifty original subject-ID mappings were checked against the published clinical table and audited clinical metadata.

For this ledger, technical completeness means seven entirely finite, 1,001-point EMG mean curves and four entirely finite sagittal kinematic means. Stroke cases also require available current spatiotemporal results from positive-duration strides. Effective EMG stride counts are recorded; no new minimum-stride cutoff or clinical-validity threshold has been imposed. Availability is not proof of acquisition quality, clinical normality or diagnostic validity. Raw C3D processing and healthy MAT normalization were not newly audited.

Age and published bilateral speed are administrative design metadata. They have not been added to model inputs. The stroke P-side speed is separately labelled and must not be confused with the published bilateral mean. Under the latter definition, 41/50 stroke participants are below the minimum control speed; being inside that range does not establish speed matching.

The published article (`reference/tamaya, 2023.pdf`, page 5) identifies TVC48, TVC51 and TVC54 as requiring minimal physical support through the non-hemiplegic hand. The verified project mapping is Sub41, Sub43 and Sub46. This is **hands-on human assistance**, not evidence of assistive-device use. The ledger says the other stroke cases are not among these three documented cases; it does not automatically certify independent walking for every other participant.

### Sub43: existing event issue verified, no new repair needed

The affected-side fourth array row (zero-based index 3) has ICstart = ICstop = 0. This was already documented in the earlier main-dataset audit. The current spatiotemporal code excludes it and retains five valid strides, giving P-side speed 0.2240079266 m/s, unchanged from the earlier audit.

In each of the four sagittal kinematic channels, this same row is entirely NaN. The released mean agrees with the MAT NaN-aware mean; removing the row explicitly changes the mean by exactly zero. Thus it is not a finite malformed row contaminating the released sagittal mean curves. See [the numerical verification](sub43_verification.json).

Sub43 still has no EMG and documented assistance. It is outside the complete-EMG pool for those reasons. Any later stride-level analysis must preserve appropriate event and signal-quality masks rather than assuming every row is a valid stride. No raw data, mean curve or historical report was edited.

## Decisions needed before a formal batch

1. Define exposure exclusions and check external case-use history. Decide whether the stricter 25-case pool is appropriate for the research claim.
2. Set the primary sample, sampling/stratification strategy and side policy; specify whether missing-EMG and assisted cases form separate challenge or sensitivity sets.
3. Decide the role of healthy controls and how reference/calibration dependence will be described or addressed.
4. Specify outcomes, weighting if any, uncertainty analysis, and technical-failure/retry handling. Derive a sample size appropriate to those decisions; the candidate count alone is not a power calculation.
5. Prepare and obtain the appropriate expert confirmation of new-case requirements, then freeze the generation inputs and rating materials. Preserve the approved interpretation/rubric scope and historical trial records.

These choices are captured as D01-D07 in the workbook. This package does not request a new review of already approved interpretation wording and does not record approval on anyone's behalf.

## Files and reproduction

- [Participant eligibility](participant_eligibility.csv): 188 group-qualified participants, exposure flags, data availability and pending selection fields.
- [Side data quality](side_data_quality.csv): 238 side records, missing channels, effective stride counts and side-level event flags.
- [Exposure evidence](exposure_evidence.csv): sources and explanations for recorded prior use.
- [Summary](summary.json): verified counts and the proposed conservative pool.
- [Verification and source hashes](verification.json): current-source hashes, checks and preserved prior-file hashes. Historical original-language evidence hashes remain in the existing conversion provenance records.
- [Report inventory](report_file_inventory.json): administrative provenance for the pilot/spot-check files. Filenames contain model/provider names; this is not a blinded rating packet and should not be distributed as one.
- [Manifest](manifest.json): hashes for this completed package, excluding the manifest itself.

Rebuild the machine-generated ledger into a **new** directory from the project root:

```sh
/Users/lixinyu/.venvs/gait-emg/bin/python scripts/build_sample_eligibility_ledger.py --out /private/tmp/gait-sample-eligibility-recheck
```

The script refuses an existing output directory and performs no model calls. It creates the workbook, CSVs and numerical/provenance JSON files; this explanatory README and package manifest document the reviewed package separately. Expected counts intentionally guard this dataset snapshot: investigate changed evidence rather than weakening assertions to reuse the same version.

The approved prompt package, reviewed rubric workbooks and historical trial files were preserved. No archived originals, private identity maps or answer keys were used. No formal participants have been selected and no new reports have been generated.
