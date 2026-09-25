# Model comparison from the frozen three-rater dataset

Computed UTC: 2026-09-23T19:42:09.686420+00:00. Frozen dataset SHA-256: `9cf006f23d5660118f5ac4da9e631e68645fa17686a0742841e267e616ca9167`.

Model identities were joined only after the blinded freeze and study-lead authorization. The historical two-rater adjudicator importer was not used. Original scores and the frozen dataset were not modified.

## Main and supplementary outcomes

| Cohort | Model identifier | Mean full coverage | Confirmed-error reports / evaluable | Unknown error reports | All-planned error bounds | Confirmed issue groups | Pending groups |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stroke | claude-opus-5 | 98.2% | 11/22 | 3 | 44.0%–56.0% | 17 | 4 |
| stroke | gemini-3.1-pro-preview | 81.8% | 12/23 | 2 | 48.0%–56.0% | 13 | 9 |
| stroke | gpt-6-astra | 97.0% | 2/25 | 0 | 8.0%–8.0% | 2 | 0 |
| control | claude-opus-5 | 90.0% | 6/9 | 1 | 60.0%–70.0% | 9 | 3 |
| control | gemini-3.1-pro-preview | 73.3% | 8/10 | 0 | 80.0%–80.0% | 11 | 0 |
| control | gpt-6-astra | 86.7% | 0/10 | 0 | 0.0%–0.0% | 0 | 0 |

Coverage is the mean of each participant's Covered/K, not the pooled item fraction. G03 is excluded from K. The primary paired stroke analysis includes all 25 participants. Error proportions use evaluable reports; the bounds retain all planned slots. Pending is not an error-free judgment.

## Paired primary stroke contrasts

| A minus B | Mean difference, percentage points | Descriptive 95% BCa | Family-adjusted 98.3333% BCa |
| --- | --- | --- | --- |
| claude-opus-5 minus gemini-3.1-pro-preview | 16.400 | 10.800 to 22.800 | 9.600 to 24.200 |
| claude-opus-5 minus gpt-6-astra | 1.200 | -1.400 to 5.200 | -1.600 to 6.200 |
| gemini-3.1-pro-preview minus gpt-6-astra | -15.200 | -20.800 to -10.000 | -22.000 to -9.000 |

Intervals use 20,000 shared participant-resampling indices, seed 20260918. An unavailable interval is retained as unavailable; no alternative interval method is chosen after seeing results. Zero-crossing intervals do not establish equivalence. No secondary-outcome confirmatory tests or omnibus model-quality score are introduced.

## Control semantic flags

| Model | Flag | Events / evaluable | Unknown | Exact 95% interval | Zero-event one-sided 95% upper |
| --- | --- | --- | --- | --- | --- |
| claude-opus-5 | normality | 0/10 | 0 | 0.000 to 0.308 | 25.9% |
| claude-opus-5 | pathology | 0/10 | 0 | 0.000 to 0.308 | 25.9% |
| gemini-3.1-pro-preview | normality | 0/10 | 0 | 0.000 to 0.308 | 25.9% |
| gemini-3.1-pro-preview | pathology | 1/10 | 0 | 0.003 to 0.445 | Not applicable |
| gpt-6-astra | normality | 0/10 | 0 | 0.000 to 0.308 | 25.9% |
| gpt-6-astra | pathology | 0/10 | 0 | 0.000 to 0.308 | 25.9% |

These are unsupported semantic inferences in reports, not diagnostic false-positive rates. A pathology annotation need not carry E02 if the human reviewer explicitly confirms the impairment inference. Ten controls per model provide limited precision; zero observed flags do not establish zero risk.

## Interpretation and provenance

- The sample is selected and internal; controls contributed to reference construction. One report per configuration cannot quantify repeated-generation variation.
- Primary outcomes are post-feedback source-linked human judgments. The independent sensitivity sheet preserves the original judgments; it is not interchangeable with final outcomes or new reliability.
- Category tables retain each reviewer's latest explicit proposal where present and registered tags otherwise. There is no majority category, tag-order rule, or multiplication of error groups.
- Requested/returned model identifiers are taken from the saved generation metadata, not a claim about current product availability.
- The protected analysis directory retains the raw estimates, independent sensitivities, category trace, generation capture metadata, source hashes, and exact resampling matrices. The identity key was not placed in rater materials.
- See Model_comparison.xlsx for per-case values, cohort summaries, denominators, control flags, category views and original-independent sensitivity.
