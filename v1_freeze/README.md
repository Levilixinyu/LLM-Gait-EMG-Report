# LLM-Gait-EMG-Report

Pilot study: can an LLM draft a clinically usable interpretive summary of surface
EMG + kinematic gait-analysis findings for post-stroke gait, validated against
blinded expert (PT / physiatrist) ratings across multiple models (Claude / GPT-4o /
an open-source model)?

Dataset: Van Criekinge et al., 2023, *Scientific Data* — "A full-body motion capture
gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors."
https://doi.org/10.6084/m9.figshare.c.6503791.v1 (journal paper DOI:
10.1038/s41597-023-02767-y). Same protocol for stroke and healthy-control cohorts,
which is what makes the normative-reference step below straightforward. **Downloaded
and integrated** -- see Data section below.

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

Spatiotemporal parameters aren't published as precomputed columns anywhere for this
dataset -- they're derived in `mat_spatiotemporal.py` from the stroke `.mat` file's gait
events (`ICstart`/`ICstop`/`IC_cnt`, absolute video-frame indices, 100 Hz) and the `HEE`
marker's stride-normalized trajectory. The able-bodied `.mat` (6+ GB) was **not**
downloaded -- not needed, since the normative reference already comes from the Excel
EMG/kinematic data and gait speed doesn't need a cohort-specific "normal" comparison to
be clinically interpretable (see `classify_ambulation()` in `spatiotemporal.py`). If you
ever need raw EMG/marker *time series* (not stride-averaged) for a custom onset-detection
method, the `.c3d` releases are the ones not downloaded, not this `.mat` file.

**Correctness pitfall already hit and fixed, worth knowing before touching this code:**
step length is NOT the stride-defining leg's own marker displacement over its stride --
that foot is planted/stationary in stance for most of that window, so this silently
produces near-zero garbage (caught via a physically-impossible ~1-13mm "step length").
The correct computation needs the *contralateral* leg's marker position (a separate MAT
field, e.g. `PsideSegm_NsideData`) at the moment it heel-strikes (`IC_cnt`) relative to
the stance leg. Verified via an internal-consistency check: a stride's own stride_length
≈ paretic step + non-paretic step computed this way. See the docstring in
`load_stroke_spatiotemporal()` for the side-labeling gotcha (a "P"-side stride entry's
step_length_m is the *non-paretic* leg's step, and vice versa -- easy to get backwards).

**Known data-quality issue, already handled:** ~20-30% of control subjects and ~12% of
stroke subject-muscle combinations have the EMG channel entirely `NaN` for a given
muscle (dropped electrode / bad signal quality upstream). `figshare_loader.py` loads
these as-is; `pipeline.py` uses `nanmean`/`nanstd` when building the normative
reference and skips a muscle entirely for a given subject when its curve is all-`NaN`
(verified: no partial-`NaN` curves in this dataset, only fully-missing ones -- see
`extract_summary_from_normalized`).

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
- Feature-extraction pipeline (both paths): **implemented and validated**, including
  against real data.
- Spatiotemporal parameters (gait speed, cadence, step-length symmetry): **implemented
  and validated** against real data for all 50 stroke subjects x 2 sides -- population
  mean gait speed 0.49 m/s (range 0.11-1.36), cadence 79.5 steps/min (range 33.6-117.7),
  both in the expected clinical range for a chronic stroke cohort spanning mild to severe;
  symmetry-index outliers correlate with the slowest subjects, as clinically expected.
  Wired into `to_prompt_text()` with an automatic Perry (1995) ambulation-category label.
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

## Next steps (in order)

1. ~~Select the pilot subset~~ -- **done**: `data/pilot_subset.json`, 18 paretic-side
   subjects, stratified across the 3 ambulation categories (6 each), seed=42
   reproducible, includes 2 deliberate missing-EMG edge cases (Sub46: 1/7 muscles valid,
   Sub47: 0/7). See `## Pilot subset selection` above.
2. ~~Generate reports~~ -- **done**: `data/reports/`, 54/54 succeeded (18 subjects x
   Claude/GPT/Gemini), 0 failures, 0 truncated (verified via `stop_reason`). Reports
   ~2.6k-12.7k chars, ~12-70s per call (Claude slowest/longest, GPT fastest/shortest).
3. Have 1-2 experts write gold-standard reference reports for the same pilot subset
   (for the "human control" arm of the comparison).
4. ~~Blind + package for rating~~ -- **done**: `data/rating_packets/`, 18 packets,
   `rubric.json` (4 Likert dimensions + 2 safety-critical Pass/Fail checks). Distribute
   to 3-5 PT/physiatrist raters (keep `answer_key_DO_NOT_SHARE.csv` away from raters
   until scoring is complete). Still need: the gold-standard reports from step 3 folded
   into the same packets/blinding before distributing, if using a human-written arm.
5. Analyze: inter-rater reliability (ICC / Krippendorff's alpha), model comparison
   (mixed-effects model), correlation between rating and objective deviation severity.

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

- Onset/offset detection uses a simple peak-fraction threshold on the ensemble-averaged,
  gait-cycle-normalized envelope (`onset_offset_pct_from_cycle`), not full Hodges & Bui
  with a static MVC/quiet-standing baseline (not present in this dataset's post-processed
  release). A time-domain Hodges-Bui implementation (`detect_onset_offset`) is included
  in `emg_signal.py` for the raw-signal path if you later pull the `.c3d` files.

  **Known failure mode, quantified:** this method reports "0-100% (full-cycle)
  activation" -- i.e. never finds an off-threshold point -- for a non-trivial fraction of
  subjects on some muscles. Checked how often (`peak-fraction > 0.2` for ≥95% of the
  cycle) across the whole dataset, stroke paretic side vs. healthy controls:

  | Muscle | Stroke (P side) | Controls |
  |---|---|---|
  | ERS | 32/46 (70%) | 37/106 (35%) |
  | GAS | 9/43 (21%) | 0/109 (0%) |
  | BF  | 15/43 (35%) | 7/106 (7%) |

  ERS shows this in over a third of *healthy* subjects too -- erector spinae is a tonic
  postural muscle with no clear quiescent period during walking even in health, so a
  fixed fraction-of-own-peak threshold is likely the wrong tool for it specifically, and
  a "100%-duration ERS activation" finding should not be presented as stroke-specific
  pathology without this caveat. GAS, by contrast, shows this pattern in a meaningful
  stroke-only minority and *never* in controls -- that one is a much more plausible
  genuine finding (e.g. loss of swing-phase plantarflexor relaxation) rather than a
  detection artifact. This distinction matters for how confidently the LLM (or a human
  rater) should treat a "continuous activation" finding per muscle -- don't apply one
  blanket confidence level to all of them. (Found this by reading actual pilot report
  output: Claude's Sub09 report independently flagged the ERS 0-100% finding as possibly
  an artifact worth checking, which is what prompted this check.)
- `gait_profile_score()` is a composite RMS-deviation score over the 4 available sagittal
  kinematic channels (ankle/knee/hip/pelvis), not the validated 9-variable GPS (Baker et
  al., 2009), which also needs coronal/transverse-plane and foot-progression variables
  not in this post-processed export. Report it as "GPS-like" / "composite kinematic
  deviation score", not as GPS.
- The peak-`deviation_z_peak` metric can spike very high (seen up to ~12 SD in real data)
  at gait-cycle points where the healthy-control cohort has near-zero variance (e.g.
  a muscle that's reliably silent in healthy swing phase) -- this is a genuine
  z-score-amplification artifact at low-variance baseline points, not a bug. Consider
  reporting % of cycle exceeding a fixed z-threshold, or a variance-floored z-score, as
  a more robust alternative before using peak-z as a headline number in the paper.
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
