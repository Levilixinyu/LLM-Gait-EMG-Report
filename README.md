# LLM-Gait-EMG-Report

Can an LLM draft a clinically usable interpretive summary of surface
EMG + kinematic gait-analysis findings for post-stroke gait, validated against
blinded expert ratings across multiple models (Claude / GPT / Gemini)?

**Research scope (frozen per audit handoff v2 §8.1):** an evaluation of whether LLMs can *faithfully describe*
verified kinematic/EMG features, express uncertainty appropriately, and produce
reports suitable for expert review. Explicitly OUT of scope: automated diagnosis,
confirming pathophysiological mechanisms (spasticity/weakness), treatment selection,
outcome prediction, and claims of clinical deployment readiness.

Dataset: Van Criekinge et al., 2023, *Scientific Data* — "A full-body motion capture
gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors."
https://doi.org/10.6084/m9.figshare.c.6503791.v1 (journal paper DOI:
10.1038/s41597-023-02767-y). Same protocol for stroke and healthy-control cohorts,
which is what makes the normative-reference step below straightforward. **Downloaded
and integrated** -- see Data section below. Key reference limits: subacute cohort
(14-139 days post-stroke); healthy speeds span 0.80-1.79 m/s while 41/50 stroke
subjects walk slower than that floor (no speed-matched reference for most patients);
effective EMG reference n = 106-109 per muscle, not 138.

## Project structure

```
data/raw/                    # downloaded post-processed Excel files (see Data section)
data/pilot_subset.json       # 18-subject pilot list (see Pilot subset selection)
data/reports/                # generated LLM reports, one JSON per subject x provider
scripts/
  select_pilot_subset.py      # -> data/pilot_subset.json
  generate_pilot_reports.py   # -> data/reports/*.json
src/
  features/
    data_types.py         # RawTrialData / NormalizedTrialData, PatientFeatureSummary, MuscleFinding, JointFinding
    emg_signal.py           # filtering, envelope, onset/offset, amplitude norm, CCI, z-score vs normative
    kinematic.py              # gait-cycle resampling, ROM, Gait Variable/Profile Score (simplified)
    spatiotemporal.py        # symmetry index, cadence helpers
    figshare_loader.py        # REAL loader for the Van Criekinge et al. Excel files -> NormalizedTrialData
    mat_spatiotemporal.py     # REAL loader for the raw stroke .mat (HDF5): gait speed/cadence/step-length symmetry
    data_loader.py             # generic RawTrialData/CSV adapter template (for a hypothetical raw-signal dataset)
    pipeline.py                 # orchestration -- two parallel paths, see "Two extraction paths" below
  llm/
    prompt_templates.py  # system prompt (4-section report structure) + user prompt builder
    providers.py           # AnthropicProvider / OpenAIProvider / GeminiProvider (+ LocalOllamaProvider, unused for now)
    report_generator.py    # batch-generates reports across subjects x providers, saves JSON
  eval/
    rubric.py               # 4-dimension blinded rating rubric (accuracy/completeness/hallucination/usefulness)
    blinding.py              # de-identifies + randomizes reports into rater packets + answer key
tests/
  synthetic_data.py         # fake raw-signal trial generator (RawTrialData path, no real data needed)
  test_pipeline.py          # end-to-end sanity check on synthetic data
```

## Data

Downloaded from the Figshare collection (`data/raw/`, gitignore this if you init git --
the two `.xlsx` data files total ~50MB):

| File | Content | Size |
|---|---|---|
| `PostStrokeAdults.xlsx` | 50 stroke subjects, 1 sheet each (`Sub01`..`Sub50`), `Pside_`/`Nside_` (paretic/non-paretic) prefixed columns | 14 MB |
| `AbleBodiedAdults.xlsx` | 138 healthy controls, 1 sheet each, unprefixed columns (symmetric gait, plus moments/powers/GRF not in the stroke file) | 36 MB |
| `MATdatafiles_description.xlsx` | variable/column documentation | 18 KB |
| `NrStrides.xlsx` | stride-count descriptive stats by age decade (not a per-subject QC mask) | 14 KB |
| `MAT_normalizedData_PostStrokeAdults.mat` | raw MATLAB v7.3 (HDF5) release, stroke cohort only -- gait events + full marker/kinematic/kinetic/EMG data | 2.7 GB |

Each Excel subject sheet has 1001 rows = one full gait cycle already stride-time-normalized
(0-100%) and averaged over that subject's strides; EMG columns (`GASnorm`, `RFnorm`,
`VLnorm`, `BFnorm`, `STnorm`, `TAnorm`, `ERSnorm`) are already normalized to that
subject's own peak muscle activity. Kinematic columns cover sagittal ankle/knee/hip/
pelvis angles. **The Excel files are pre-processed, not raw** -- no raw time series,
events, or spatiotemporal (speed/cadence/step length) columns.

Spatiotemporal parameters are derived in `mat_spatiotemporal.py` from the stroke
`.mat` file's gait events (`ICstart`/`ICstop`/`IC_cnt`, absolute video-frame indices,
100 Hz) and the `HEE` marker's stride-normalized trajectory. **Correction (audit
P1-6): the original paper's Supplementary Table 5 DOES publish per-side gait speeds**
-- an earlier version of this section claimed no precomputed spatiotemporal values
existed anywhere, which was wrong. The silver lining: our computed speeds match all
100 published side-values to their 4-decimal precision (max abs diff 0.00005 m/s),
which is the independent external validation of the speed computation. The able-bodied
`.mat` (6+ GB) was **not** downloaded -- the normative reference comes from the Excel
EMG/kinematic data. Note the `.mat` is *processed, stride-normalized* data, not raw
continuous EMG; genuinely raw time series live only in the `.c3d` releases (also not
downloaded).

**Correctness pitfall already hit and fixed, worth knowing before touching this code:**
step length is NOT the stride-defining leg's own marker displacement over its stride --
that foot is planted/stationary in stance for most of that window, so this silently
produces near-zero garbage (caught via a physically-impossible ~1-13mm "step length").
The correct computation needs the *contralateral* leg's marker position (a separate MAT
field, e.g. `PsideSegm_NsideData`). **Definition caveat (audit P1-3): two operational
step-length definitions exist** -- successive-footfall (contralateral heel at its IC
minus stride-side heel at stride start; the default here) vs. same-instant two-heel
distance at contralateral IC. Both are implemented (`step_length_definition` parameter);
switching moves some subjects' symmetry index materially (Sub45: +5.8% -> -0.3%), so
the choice is stated explicitly rather than assumed. The stride≈step+step check is
*internal consistency only*, not ground-truth validation; the independent external
check is the speed match against published Supplementary Table 5 (which doesn't depend
on the step definition). See the docstring in `load_stroke_spatiotemporal()` for the
side-labeling gotcha (a "P"-side stride entry's step_length_m is the *non-paretic*
leg's step, and vice versa -- easy to get backwards).

**Known data-quality issue, already handled:** ~20-30% of control subjects and ~12% of
stroke subject-muscle combinations have the EMG channel entirely `NaN` for a given
muscle. **The specific cause per subject is not recorded in the public release** -- the
source study notes some participants simply had no analog signals captured, so
all-NaN does not automatically mean "dropped electrode / bad signal quality" (audit
P1-6; an earlier version of this section over-asserted the cause). `figshare_loader.py`
loads these as-is; `pipeline.py` uses `nanmean`/`nanstd` when building the normative
reference and skips a muscle entirely for a given subject when its curve is all-`NaN`
(verified: no partial-`NaN` curves in this dataset, only fully-missing ones).

## Pilot subset selection

`scripts/select_pilot_subset.py` -> `data/pilot_subset.json`. 18 paretic-side stroke
subjects, stratified 6/6/6 across the 3 Perry (1995) ambulation categories (household /
limited-community / full-community, see `classify_ambulation()`), so the pilot spans
the full severity range rather than clustering at one end. Within each category,
subjects with complete 7-muscle EMG data are preferred, but one incomplete-EMG subject
per category is deliberately included as an edge case (Sub46: 1/7 muscles valid, Sub47:
0/7) to check the pipeline/LLM handle missing data gracefully rather than only ever
seeing clean inputs. Fixed seed (42) for reproducibility -- re-running the script
reproduces the exact same 18 subjects (verified byte-identical against the file actually
used for the pilot's report generation).

Post-audit annotations on this subset (handoff v2 §8):
- **Sub46 walked with hands-on assistance from a physical therapist** (supplement id
  TVC54; likewise Sub41/Sub43 = TVC48/TVC51, neither in the pilot). NOT an assistive
  device -- an earlier version of this note said "assistive device", which the source
  material does not support (audit round 2, R3). Case documentation and any
  sensitivity analysis must carry the assisted-walking status; reports shouldn't
  presume unaided walking.
- These 18 have been used repeatedly for prompt/pipeline development. **They are
  development cases now** -- any confirmatory evaluation needs to disclose that, or
  draw fresh subjects from the remaining pool under prespecified inclusion rules
  (43 stroke subjects have complete bilateral 7-muscle EMG as main-analysis candidates).
- The cohort is subacute (TPS 14-139 days). Known dataset-level inconsistency, kept
  as-published: the paper's methods describe excluding FAC<=2 / TIS>=20, but the
  released records include 18 subjects with FAC=2 and one TIS=20 -- note it, don't
  "fix" the data or invent a reason (author clarification would need user
  authorization).

## Model roster: Claude / GPT / Gemini (not open-source)

Decided against a local open-source arm (disk had ~11GB free after the dataset
downloads -- no room for a large local model) in favor of three commercial flagships,
following precedent from cardiology-LLM comparison work using the same three-way
design -- ChatGPT vs Claude vs Gemini, no open-source arm (2025, *Hearts*/MDPI,
https://www.mdpi.com/2673-3846/6/3/19 -- author names not independently confirmed, cite
via DOI/journal rather than by name until verified). The alternative design --
open-source/self-hostable models only, no commercial APIs -- is also well precedented
(brain-MRI diagnostic-impression benchmark, 2026, *npj Digital Medicine*,
doi:10.1038/s41746-026-02380-4: 10 models, all open-weight, GPT-4/Claude/Gemini
deliberately excluded) and is the more reproducibility-friendly choice; **state this
tradeoff explicitly in limitations** -- commercial API model versions get deprecated/
renamed over time in a way open weights don't, so exact reproduction of this pilot years
later isn't guaranteed the way it would be with self-hosted open weights.

Model ids as of 2026-09-16, each confirmed by a live API call that echoed the model id
back (not just docs -- these move fast, re-check before running anything that needs to
stay reproducible):
- Claude: `claude-opus-5` (Claude 5 family: Opus 5 / Sonnet 5 / Fable 5, plus Haiku 4.5.
  First attempt defaulted to `claude-opus-4-6` from a stale ~7-month-old cached skill
  reference and wasn't re-checked the way GPT/Gemini were -- caught only because a
  session question ("why not Fable?") prompted a re-check. Fable 5 is a separate named
  tier in the same family, not the flagship-reasoning one this comparison wants.)
- OpenAI: `gpt-6-astra` (current flagship per developers.openai.com/api/docs/models;
  gpt-4o is a superseded 2024 model, don't default to it)
- Gemini: `gemini-3.1-pro-preview` (current flagship reasoning model per
  ai.google.dev/gemini-api/docs/models; note the "-preview" suffix. SDK calls to this
  model routinely took 1-4 minutes even for a one-word test reply in this session,
  apparently normal for its default extended-thinking behavior, not a bug -- budget
  batch-generation time accordingly.)

## Two extraction paths in `pipeline.py`

1. **`extract_summary_from_normalized()` + `build_normative_reference_from_normalized()`**
   -- the one actually in use. Takes `NormalizedTrialData` (already stride-normalized,
   already amplitude-normalized) from `figshare_loader.py`. No filtering/resampling
   needed since the dataset authors already did it.
2. **`extract_patient_summary()` + `build_normative_reference()`** -- a more general
   path that takes `RawTrialData` (continuous raw EMG + joint angle time series + event
   timestamps) and does the filtering/envelope/resampling itself. Kept in case you later
   pull the raw `.c3d` releases for a method that needs true onset timing instead of a
   threshold on the ensemble-averaged curve. `data_loader.py` is a placeholder adapter
   for this path -- not needed for the Excel-based workflow above.

## Status

- Real dataset: **downloaded and loading correctly** -- all 100 stroke trials (50
  subjects x 2 sides) and 138 controls extract with no errors and no `NaN` leakage
  (verified with a full-dataset sweep).
- Feature-extraction pipeline: **implemented; v1 had real defects found by external
  audit (2026-09-16), fixed post-audit** -- v1 dropped all EMG activation intervals
  after the first and mishandled the cycle boundary (audit P0-1; fixed by
  `analyze_activation()`); the raw path compared unnormalized envelopes against a
  normalized reference so z scaled with signal amplitude (P1-2; fixed + regression
  test); the Excel path applied an absolute threshold where fraction-of-peak was
  intended (P0-2; primary definition now frozen as fraction-of-peak, with the change
  documented). "Runs without errors on all subjects" is the accurate claim for what
  the full-dataset sweep showed -- it is not clinical validation.
- Spatiotemporal parameters (gait speed, cadence, step-length symmetry): **implemented;
  speed independently validated** -- computed speeds match the original paper's
  Supplementary Table 5 for all 100 published side-values to 4-decimal precision.
  Population mean gait speed 0.49 m/s (range 0.11-1.36), cadence 79.5 steps/min
  (range 33.6-117.7). Note this is a **subacute** cohort (time post-stroke 14-139 days
  in the MAT's TPS field; the study recruited within 5 months post-stroke) -- an
  earlier version of this section wrongly called it chronic. Step-length symmetry
  carries a definitional caveat (see Data section). Wired into `to_prompt_text()` with
  an automatic Perry (1995) ambulation-category label.
- Prompt templates: **implemented** -- see example output below, now with real
  spatiotemporal values instead of placeholders.
- Multi-model report generation: **done for the pilot subset, verified clean**. All 54
  calls (18 subjects x 3 providers) succeeded on the second run, 0 failures, **0
  truncated** (18/18/18 clean `end_turn`/`STOP`/`stop` per provider -- checked via the
  `stop_reason`/`truncated` fields every record now carries). Reports in
  `data/reports/`, one JSON per subject x provider (see
  `scripts/generate_pilot_reports.py`). Generation is idempotent -- re-running skips
  files that already exist.

  **First run silently truncated at least one report** (`max_tokens=4000` was too low --
  a spot-read of one output ended mid-word; `GenerationResult` didn't capture
  `stop_reason` at all, so this wasn't otherwise detectable). Fixed by raising
  `max_tokens` to 8000 across all three providers and adding `stop_reason`/`truncated`
  capture to `GenerationResult` (see `providers.py`) and to the saved JSON records (see
  `report_generator.py` and `generate_pilot_reports.py`) so future truncation is loud,
  not silent. All 54 reports were deleted and regenerated after the fix -- don't trust
  reports from before this fix if you find any lying around.

  **v1 report status after the external audit (2026-09-16): exploratory only.** The
  v1 inputs carried the P0-1/P0-2 extraction defects (missing second activation
  intervals -- e.g. Sub50 TA's swing burst and Sub05 GAS's max-deviation burst never
  reached the models -- and the absolute-vs-fraction threshold mix-up), plus
  uncalibrated max-|z| framing (P0-3). v1 outputs are frozen in `v1_freeze/` and
  `data/reports/` as a record of what was generated under those inputs; they must not
  be used for model comparison or expert rating. `generate_pilot_reports.py` now
  targets `data/reports_v2/` with prompt_version=v2, embeds the full prompts + a
  config hash in every record, and validates existing files before skipping (bare
  file-existence no longer suppresses regeneration). Running it calls paid APIs --
  needs explicit user go-ahead.
- Blinding / rating packet generation: **done**. `data/rating_packets/` -- 18 packets
  (one per subject, 3 blinded/shuffled reports each), `answer_key_DO_NOT_SHARE.csv`,
  `rubric.json` (Likert dimensions + safety-critical checks, see below). Rubric now
  includes two Pass/Fail safety-critical checks (side inversion, normal/abnormal
  inversion) alongside the 4 Likert dimensions -- precedent from a hybrid rule+LLM
  electrodiagnostic-reporting system (PMC, two-center eval) that tracks these as a
  separate binary flag rather than folding them into a continuous accuracy score, since
  a single side-flip is severe enough that averaging hides it. See `eval/rubric.py`.

  **De-identification regex was stale and silently under-covering, fixed.**
  `STRIP_PATTERNS` in `blinding.py` was written for the original gpt-4o/claude-opus-4-6
  roster and never updated after the roster moved to gpt-6-astra/claude-opus-5/
  gemini-3.1-pro-preview -- it didn't even contain "gemini" at all. Checked all 54
  report texts (not just the JSON metadata, which trivially contains the model name and
  isn't what gets shared with raters): none actually self-referenced their model name,
  so this run's blinding wasn't compromised in practice, but the safety net wasn't
  actually there for future runs. Replaced the hardcoded list with
  `_build_strip_patterns()`, which derives exact-match patterns from whatever
  provider/model values are actually present in the reports being processed, plus a
  generic vendor-stem backstop (claude/gpt/gemini/opus/sonnet/... family names) --
  correct automatically no matter what models get used next time, not another
  hardcoded list to forget to update.

## Setup

```bash
cd ~/Desktop/LLM-Gait-EMG-Report
source .venv/bin/activate   # venv already has numpy/scipy/pandas/openpyxl
pip install -r requirements.txt   # adds anthropic/openai/requests/pytest when ready to generate reports
cp .env.example .env               # fill in ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY
```

## Run on the real data (no API keys needed yet)

```bash
python3 -c "
from src.features.figshare_loader import load_stroke_excel, load_control_excel
from src.features.mat_spatiotemporal import load_stroke_spatiotemporal, build_spatiotemporal_lookup
from src.features.pipeline import build_normative_reference_from_normalized, extract_summary_from_normalized
from src.llm.prompt_templates import build_user_prompt

controls = load_control_excel('data/raw/AbleBodiedAdults.xlsx')
stroke = load_stroke_excel('data/raw/PostStrokeAdults.xlsx')
normative = build_normative_reference_from_normalized(controls)

st_lookup = build_spatiotemporal_lookup(load_stroke_spatiotemporal('data/raw/MAT_normalizedData_PostStrokeAdults.mat'))

demo = next(t for t in stroke if t.subject_id == 'Sub03' and t.side == 'P')
st = st_lookup.get(('Sub03', 'P'), {})
summary = extract_summary_from_normalized(demo, normative=normative, **st)
print(build_user_prompt(summary))
"
```

## Run the synthetic-data sanity check (RawTrialData path)

```bash
python3 -m tests.test_pipeline
```

## Next steps (rewritten per audit handoff v3 §8.7/§9.3 -- supersedes the old flow)

**Do NOT distribute the existing `data/rating_packets/` -- they were built from v1
reports and are deprecated** (see `data/rating_packets/DEPRECATED_v1_README.txt`).
The old plan (experts write full gold-standard reports for all 18, distribute v1
packets) is withdrawn. Current sequence:

1. **Freeze evaluation groundwork first** (before any paid generation): a data card /
   reference checklist per case (which curves, features, definitions and calibration
   the raters see), and rating rules built on `eval/rubric.py`'s three-layer split --
   numeric facts (machine-checkable), interpretation boundaries (expert judgment
   against the supplied references, with an explicit INDETERMINATE option), and
   actual clinical mechanisms (out of scope -- expert reading a report cannot
   confirm spasticity etc.). Expert opinion is a REFERENCE STANDARD, not absolute
   truth. Instead of full gold-standard reports, build per-case checklists:
   must-mention findings / allowed interpretations / inferences the data cannot
   support.
2. **Trial-rate 3-5 development cases** (mix of complete, missing-EMG, and healthy
   LOO cases) with >=2 raters working independently and model-blinded, then
   adjudicate -- primarily to test whether the rating materials suffice and how long
   rating takes. Raters should see necessary curves + verified features, not judge
   from report style alone.
3. **Freeze inputs, prompts, rating rules, sample and analysis plan** based on the
   trial round. Disclose that the 18-subject pilot has been reused for development;
   confirmatory claims need fresh subjects under prespecified inclusion rules
   (43 complete-bilateral candidates).
4. **Generate the formal v2 batch** (user authorization required -- paid APIs) via
   `scripts/generate_pilot_reports.py` / `generate_control_spotcheck.py` (both now on
   the generation_cache task-identity system), then rebuild blinded packets with the
   fixed `blinding.py`.
5. **Independent expert rating, then adjudication; analysis** with subject as the
   repeated-measures unit (18 subjects are not 54 independent samples; raters are
   crossed, not independent) -- report effects with uncertainty, no winner-by-anecdote.

## Healthy-control spot-check (v1): what it was and was not

`data/reports_control_spotcheck/` holds 12 reports (4 complete-EMG controls x 3
models), generated with `Group: control` **stated in the input**. Post-audit framing
corrections (P0-4):

- This was a **label-known interpretation task** ("how does the model discuss
  deviations when told the subject is healthy"), NOT a hidden-label normal-vs-abnormal
  identification test, and 4 subjects x 3 models is not 12 independent cases. No
  false-positive *rate* can be claimed from it.
- The interim conclusions drawn in-session ("no fabricated pathology = check passed";
  "Claude questioning Sub10's control label shows superior critical reasoning";
  "Claude clearly stronger overall") are **withdrawn as unsupported** and demoted to
  hypotheses for the real rated evaluation. Counter-evidence from the audit: Sub10
  (age 81) sits at the ~81st percentile of the 138-control GPS-like distribution
  (95th pct = 10.71), so its label was not statistically suspect; Claude's Sub50
  report contains a plain arithmetic error ("6.86 is lower than three of the four
  GVS" -- only two exceed it) that was praised in-session as insightful; Claude and
  Gemini both called a healthy-range CCI of 0.63 "high/elevated" (healthy RF-BF
  median is 0.68, 2.5-97.5 pct 0.48-0.83) -- pathologizing language without a
  reference basis, just without a disease name attached. GPT's refusals to interpret
  were partly the correct response to inputs that genuinely lacked definitions and
  reference ranges (now fixed in the v2 input spec).
- Any model comparison must come from blinded expert rating with predefined error
  categories, per-subject repeated-measures analysis, and all three models' errors
  logged symmetrically -- not from post-hoc case-picking by the same model being
  compared (which is what happened in-session).

## Parked: external-validation dataset (Chatpun et al. 2024, PeerJ)

Investigated as a second, independent stroke-gait sEMG cohort for an external-validation
arm: 16 chronic stroke + 16 healthy, raw 1000 Hz signals, publicly on Figshare
(https://doi.org/10.6084/m9.figshare.26065414.v1, ~1.7 GB / 32 CSV files). Shares 4
muscles with the Van Criekinge cohort (RF, BF, MG≈GAS, TA) plus GM and PL.

**Blocked on:** the raw CSV's 16 EMG columns (`EMG1`..`EMG16`) are not mapped to
muscle/side anywhere public -- checked the paper's full Methods text (verbatim), Data
Availability statement, and Figshare item metadata/description; none specify channel
order, and there's no supplementary file. Confirmed by full-text re-read, not just an
abstract skim.

Explored recovering the mapping from signal timing alone (classic literature EMG
patterns -- TA is biphasic around heel-strike + swing, hamstrings burst late-swing/
early-stance, etc. -- are usually distinctive enough to fingerprint a channel). Requires
reliable per-trial gait-event timing first. Checked one file (`N2_Trial01.csv`,
healthy subject): the `FootSwitch1`/`FootSwitch2` analog channels look unused (±0.15V,
not switch-like -- the paper actually used a separate Pedar-X insole system not present
in this export), and none of the 3 force plates registered a clean footstrike in this
particular trial (Fz peaked at 20-60N vs the several-hundred-N expected for a real
stance phase -- plausible given a 10 m walkway with only 3 small plates). Not a dead
end -- a per-trial sweep to find files with clean plate contacts, or an autocorrelation-
based cycle alignment without absolute event timing, would likely get there -- just more
work than a quick check. Parked; revisit if the pilot needs a second cohort for
generalizability, or email the corresponding author for the channel order directly
(faster than the signal-analysis route).

## Known simplifications to flag in the methods section

- Activation detection (v2: `analyze_activation()`) reports every above-threshold
  interval on the ensemble-averaged, gait-cycle-normalized envelope, with circular
  boundary handling. **Frozen primary threshold definition: 20% of that curve's own
  peak, minimum interval 3% of cycle.** This is not Hodges & Bui with a
  static/quiet-standing baseline (not available in this release), and averaged-envelope
  intervals are not per-stride physiological onsets.

  **v1's version of this had two audit-confirmed defects (P0-1, P0-2), both of which
  contaminated the v1 report inputs:** (a) it returned only the FIRST interval --
  e.g. Sub50 paretic TA's swing burst (~57-100%) and Sub05 paretic GAS's late burst
  (~75-87%, containing that subject's max |z|) never reached the models, and one
  model then built a "no swing-phase TA activity / foot drop?" discussion on the
  omission; (b) the Excel path applied 0.2 as an ABSOLUTE threshold while the
  docstring (and the raw path, and the README stats below as originally computed)
  used fraction-of-peak -- two different statistics presented as one.

  **Definition sensitivity is large, not cosmetic** (audit-reproduced counts of
  subjects with >=95% of cycle above threshold):

  | Muscle/cohort | fraction-of-peak (0.2x own peak) | absolute 0.2 |
  |---|---:|---:|
  | ERS stroke-P | 32/46 | 12/46 |
  | ERS controls | 37/106 | 3/106 |
  | GAS stroke-P | 9/43 | 1/43 |
  | GAS controls | 0/109 | 0/109 |
  | BF stroke-P | 15/43 | 2/43 |
  | BF controls | 7/106 | 3/106 |

  Under the now-frozen fraction-of-peak definition, the earlier biological reading
  still holds directionally (ERS "always-on" is common in healthy subjects too --
  tonic postural muscle, wrong tool for it; GAS "always-on" is stroke-only), but any
  such statement must name the definition it was computed under. Also note ">=95% of
  samples above threshold" is not the same claim as "the detector returns a single
  0-100% interval". (Origin: a Claude pilot report flagged the ERS finding as a
  possible artifact; the external audit then found the definition mismatch.)
- `gait_profile_score()` is a composite RMS-deviation score over the 4 available sagittal
  kinematic channels (ankle/knee/hip/pelvis), not the validated 9-variable GPS (Baker et
  al., 2009), which also needs coronal/transverse-plane and foot-progression variables
  not in this post-processed export. Report it as "GPS-like" / "composite kinematic
  deviation score", not as GPS.
- `deviation_z_peak` is the max |z| across all 1001 phase points -- an extreme-value
  statistic, NOT a single-observation z-score, and **the conventional 2-SD abnormality
  rule does not apply to it** (audit P0-3): all 109 healthy controls with EMG exceed
  |z|>2 on at least one muscle, and the healthy per-muscle 95th percentiles for this
  statistic are 3.65 (ERS) to 4.61 (TA) -- higher under leave-one-out (controls
  currently contribute to their own reference; a LOO or held-out reference is required
  before any formal healthy-vs-stroke evaluation). v2 now also records the SIGN and
  PHASE of the max deviation, and `to_prompt_text` ships the calibration context with
  the number. **Retraction of an earlier claim:** a previous version of this section
  called large peak-z values (e.g. Sub05 GAS 13.3) a "z-amplification artifact at
  near-zero-variance points". Audit-checked: at that subject's max-|z| phase (80.3%),
  the healthy SD is 0.023 -- not near zero -- and the value sits inside a real second
  activation burst that v1's detector dropped. The claim was made without checking the
  actual curve and is withdrawn; each large deviation needs its denominator and phase
  inspected, not a blanket artifact label.
- `DEFAULT_ANTAGONIST_PAIRS_SHORT = [("TA","GAS"), ("RF","BF")]` (ankle and knee
  antagonist pairs) is a standard clinical choice but not the only reasonable one --
  `VL` and `ST` are also available if you want additional pairs (e.g. knee flexor/extensor
  via `ST` instead of `BF`).
- `classify_ambulation()` uses the household/limited-community/full-community speed
  cutoffs conventionally attributed to Perry et al. (1995, *Stroke* 26(6):982-9) --
  the paper itself is confirmed real (PubMed/NCBI eutils: authors/journal/year/volume
  all check out), but its abstract describes a more granular 6-category scale, not these
  exact three bands with these exact 0.4/0.8 m/s numbers; the 3-tier framing is the
  standard citation-chain simplification (independently corroborated by Bansal et al.
  2024 using the same 3 categories without disputing the cutoffs), not something
  verified character-for-character against Perry et al.'s full text. Computed by the
  pipeline rather than left for the LLM to recall (see its docstring for why). Cite
  Bansal et al. (2024, *Neurorehabil Neural Repair* 38(8):582-594) in the limitations:
  they found this scheme separates household from community ambulators reliably, but
  doesn't reliably distinguish "limited" from "full" community ambulation against
  real-world (GPS/accelerometer) daily step counts --
  don't let generated report text extrapolate real-world function from gait speed alone.

## 专家数据卡

当前使用[五例临床简版数据卡](docs/expert_trial/data_cards_v5/index.html)，填写和交回方式见[审核指南](docs/expert_trial/DATA_CARD_REVIEW_GUIDE.md)。旧数据卡已清理；当前版本可用于专家审核，内容尚待专家定稿。
