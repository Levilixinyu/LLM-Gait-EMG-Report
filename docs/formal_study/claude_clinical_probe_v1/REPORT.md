# Gait Report Interpretation — Sub09_P

**Interpretation version:** limited-evidence-v3.1-candidate
**Scope:** Research-level interpretation of a supplied quantitative summary. Not a diagnosis, not a treatment recommendation, and not a substitute for clinical examination.

---

## 1. Objective Findings

**Participant and side.** Sub09_P is documented in the stroke group; the analyzed limb is the **paretic** side. The released cycle for this limb runs from one initial contact of that limb (0%) to the next initial contact (100%); these are two successive occurrences of the same event, not a single instant. No intermediate gait event (including individual toe-off) is supplied, so all timing below is expressed purely as a percentage of the analysis cycle.

**Spatiotemporal values as supplied.**
- Gait speed **0.62 m/s**, falling in the 0.4–0.8 m/s band labelled "limited community ambulator." This label denotes a speed band only; it does not measure walking independence, safety, or real-world community mobility.
- Cadence **79.0 steps/min**.
- Step length symmetry index **−9.9%** using the **successive-footfall** definition (each heel at its own initial contact). By the stated sign convention, the negative value means the **paretic step is the shorter** of the two. The alternative instantaneous definition can yield a different value for some subjects, so this figure should be read as definition-specific.

**Reference comparability (applies to every comparison in this report).** The deviation reference actually used is a **pooled cohort of 138 healthy subjects**, 1001 phase points, from `main_cohort_excel`; it pools both body sides and all ages and is **not age- or speed-matched** to this participant. This participant's speed of 0.62 m/s lies **below the 0.80 m/s floor** of the healthy cohort's self-selected speeds, so **no speed-matched healthy reference exists in this dataset**. Any difference from the reference therefore conflates slow-walking effects with stroke-related control changes, and these data cannot separate the two. Differences from an empirical reference do not, on their own, establish a disease effect, a clinical diagnosis, or a severity grade.

**Channels available and not available.** Sagittal-plane kinematics for ankle, knee, hip and pelvis are provided; **coronal and transverse plane data are not included**. Seven EMG envelope channels (GAS, RF, VL, BF, ST, TA, ERS) and two co-contraction indices are provided. Not supplied in this input: individual toe-off and other phase boundaries, matched muscle-specific normal timing references, stride-level variability, raw-signal quality checks, and expert plots. Age, sex, time post-stroke, stroke clinical scores and non-paretic-side data are outside this input; their absence here does not mean they are absent from the source release.

---

## 2. EMG Envelope and Threshold Findings

**How these numbers must be read.** All EMG values derive from **ensemble-averaged envelopes**, normalized with a shared participant-, side-, and muscle-specific maximum across available strides before averaging (the denominator is not shared between sides). Amplitudes are therefore **relative envelope values** — not neural drive, force, or strength — and muscles cannot be ranked as stronger or weaker from them. Detected intervals are properties of the **mean envelope under a 20%-of-own-peak threshold with a 3%-of-cycle minimum retained duration**; they are not physiological onsets, offsets, contraction durations, or proof of inactivity outside the listed intervals. An average curve cannot show stride-to-stride variability, and a pattern seen in the mean does not establish that every individual stride behaved the same way. Anatomical actions may be named, but no interval is assigned here to a gait-phase function.

| Muscle | Retained interval(s) (% cycle) | Coverage | Peak norm. amplitude | Max \|z\| (location) |
|---|---|---|---|---|
| GAS | 8–12; 14–20; 23–56 | 43% | 0.59 | 3.1 above ref. @ 52% |
| RF | 0–100 | 100% | 0.54 | 3.5 above ref. @ 21% |
| VL | 69–85; 88–48 (wraps) | 78% | 0.51 | 4.2 above ref. @ 21% |
| BF | 0–100 | 100% | 0.50 | 2.6 above ref. @ 10% |
| ST | 54–58; 67–80; 83–44 (wraps) | 79% | 0.67 | 4.2 above ref. @ 25% |
| TA | 36–40; 63–25 (wraps) | 70% | 0.65 | 2.1 above ref. @ 86% |
| ERS | 0–100 | 100% | 0.62 | 6.2 above ref. @ 81% |

**Boundary continuity.** For RF, VL, BF, ST, TA and ERS the mean envelope remained above threshold **across the cycle-defining initial-contact boundary** (VL, ST and TA via explicitly wrapping intervals; RF, BF and ERS as a single 0–100% span). For RF, BF and ERS an onset written as 0% is the **analysis-window boundary**, not an identified physiological onset. Coverage reported as 100% for these three means no below-threshold region was retained by the algorithm; brief dips shorter than the 3% retention rule, or lost in the rounding of the coverage figure, cannot be excluded from this summary alone. GAS is the one channel with clearly segmented above-threshold regions and the lowest coverage (43%); the gaps between its retained intervals indicate regions of the **mean envelope** below the 20% threshold, not muscle silence in every stride.

**Timing.** Because no toe-off, phase boundary or matched muscle-specific timing reference is supplied, none of these intervals can be called normal, early, delayed or prolonged, and none can be assigned to stance, swing, loading response, pre-swing or mid-stance. Only proximity to the named initial-contact boundary can be described, as above.

**Max |z| interpretation.** Max |z| is an **extreme-value statistic** — the single largest standardized difference across all 1001 phase points — not a single-observation z-score, and its location marks the largest standardized difference from the phase-specific reference mean, **not** necessarily the peak of the envelope or any gait event. "Above reference" means above the reference mean at that phase point. The conventional 2-SD rule does not apply: in this dataset every one of 109 healthy controls exceeds |z| = 2 on at least one muscle, and per-muscle healthy 95th percentiles for this statistic run from 3.65 (ERS) to 4.61 (TA), higher still under leave-one-out. Against that framing:
- **ERS 6.2** exceeds the stated ERS 95th percentile (3.65) and also the top of the whole per-muscle range (4.61) — the largest standardized difference in this set, at 81% of the cycle.
- **TA 2.1** is below the TA 95th percentile of 4.61. **GAS 3.1**, **BF 2.6** and **RF 3.5** all fall below 3.65, the lowest of the listed per-muscle 95th percentiles, and are therefore below their own muscle's percentile as well.
- **VL 4.2** and **ST 4.2** fall inside the 3.65–4.61 span; their individual muscle-specific percentiles are not supplied here, so these two cannot be classified either way from this input.

None of these values, in isolation or together, establishes abnormal physiology, and the unmatched, non-speed-matched reference (see Section 1) further limits what they can support.

**Co-contraction indices.** CCI here is the Falconer–Winter index (2 × common area / summed areas) computed over the **full continuous envelopes across the whole cycle**. It is a whole-cycle overlap index of normalized envelopes — not simultaneous activation time, not muscular force, not a phase-specific result — and it can be non-zero even where the detected burst intervals of the pair do not overlap, because sub-threshold envelope area contributes. It is method-dependent (normalization and envelope processing), so values and thresholds from other studies or algorithms do not transfer.
- **TA vs GAS = 0.38**, just below the healthy median of 0.39 and within the supplied 2.5th–97.5th percentile interval of 0.24–0.59.
- **RF vs BF = 0.82**, above the healthy median of 0.68 and within the supplied interval of 0.48–0.83, sitting **close to the upper endpoint**.

Lying within the supplied interval does not establish physiologically normal co-activation or normal muscle function; lying near or outside an endpoint would not establish pathological co-activation, stiffness, impaired motor control, or any diagnosis. The same speed and matching limits described in Section 1 apply to these percentile intervals.

---

## 3. Kinematic and Reference Comparisons

All kinematic values are **sagittal plane only**.

| Joint | Sagittal ROM (deg) | Gait Variable Score |
|---|---|---|
| Ankle | 19.5 | 3.80 |
| Knee | 51.5 | 9.22 |
| Hip | 47.0 | 11.70 |
| Pelvis | 3.5 | 4.69 |

**Composite deviation ("GPS-like") = 8.04**, the RMS of the per-joint GVS values over the supplied sagittal channels. This is not the validated 9-variable GPS, so published GPS cut-offs and severity bands do not apply. Against the supplied composite reference (median 5.1, 95th percentile 10.7), this participant's value is **above the median and below the 95th percentile**. Note that these are **pooled calibration percentiles**, not matched leave-one-out normal limits, and the reference is not speed- or age-matched to a 0.62 m/s walker.

Within the supplied set, the largest per-joint GVS values are at the **hip (11.70)** and **knee (9.22)**, with ankle (3.80) and pelvis (4.69) lower. No per-joint GVS reference values are supplied, so these joints cannot be individually classified as within or outside normal limits — only ordered relative to one another within this subject.

GVS and the composite score are **summary magnitude differences** from the stated reference across the cycle. Neither identifies the direction of the waveform difference (e.g. more flexion vs more extension), nor the phase at which it occurs, nor a mechanism. ROM values alone do not establish a clinical restriction in the absence of an appropriate matched comparison; the small pelvic sagittal ROM (3.5 deg) is reported here as a measured value without such a comparison. As throughout, differences from this pooled reference at a speed below the reference cohort's floor cannot be attributed wholly to stroke pathology and do not by themselves establish a disease effect or diagnosis.

---

## 4. Questions for Further Clinical Assessment

The following are open questions for the treating clinician, posed without presupposing that any of the mechanisms or measurement issues named has already been observed in this participant. No treatment is recommended here.

1. **Event and phase resolution.** Can individual toe-off and other gait-event timings for this limb be retrieved from the release, so that the reported envelope intervals and the max-|z| locations (notably ERS at 81% and TA at 86%) could be examined relative to actual phase boundaries rather than to cycle percentage alone?
2. **Speed-related confounding.** Is a slow-speed healthy comparison set (at or near 0.62 m/s) available from another source? Without one, the direction and size of the observed deviations cannot be separated from speed effects.
3. **Stride-level behaviour.** Do the underlying individual strides show the same near-continuous above-threshold behaviour seen in the mean envelopes for RF, BF and ERS, or does the averaging contribute to it? Stride-level curves and variability metrics would be needed to address this.
4. **Signal quality.** Have raw-signal quality checks (e.g. baseline, crosstalk, electrode integrity, ECG or movement artefact — particularly relevant for the trunk channel with the largest standardized difference, ERS) been performed for this recording? These checks are not part of the supplied summary.
5. **Normalization denominator.** Given that the normalization maximum is participant-, side- and muscle-specific, is the non-paretic-side recording available and separately normalized, and is a between-side comparison appropriate under that pipeline?
6. **Muscle-specific reference percentiles.** Can the individual healthy 95th-percentile max-|z| values for VL and ST be obtained, so that those two channels (both 4.2, inside the unresolved 3.65–4.61 span) can be placed relative to their own muscle-specific reference?
7. **Out-of-plane motion.** Would coronal- and transverse-plane kinematics be worth acquiring, given that the supplied analysis and the composite score cover sagittal channels only?
8. **Step-length definition.** Would the instantaneous step-length definition change the −9.9% symmetry value for this participant, and which definition is preferred for the intended clinical or research comparison?
9. **Clinical context.** What do the examination findings, time post-stroke, and available clinical scores show, and how do they correspond to the patterns summarized above? None of these fields is supplied in this input, and the quantitative summary alone cannot support inferences about them.