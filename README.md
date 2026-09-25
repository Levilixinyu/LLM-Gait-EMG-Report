# LLM-Gait-EMG-Report

A paired evaluation of how three saved language-model configurations describe supplied stroke gait and EMG summaries. The completed study has **25 stroke participants, 10 healthy controls and 105 model reports**. Three human experts made the original scoring judgments independently; subsequent clarification, personal rechecks and discussion are separate stages.

The study evaluates required-content coverage and fidelity to available evidence. It does not establish diagnosis, physiological mechanisms, treatment benefit or clinical deployment readiness. Healthy controls are a separate exploratory supplement with disclosed cohort membership.

## Current work

- [Full working manuscript and 12 tables](docs/formal_study/manuscript_v1/README.md): includes review chronology, original-versus-frozen coverage, report length, separate control results and targeted sensitivity.
- [Current project index](docs/CURRENT_PROJECT_INDEX.md): authoritative entry points for reports, human submissions, rules, analysis and provenance.
- [Frozen model comparison](docs/formal_study/model_comparison_v1/README.md) and [later wording sensitivity](docs/formal_study/wording_sensitivity_v1/README.md): preserve original judgments, unknown states and personal disagreements.
- [Offline reproduction instructions](docs/formal_study/reproducibility_v1/README.md): self-contained researcher package and a new-output-directory replay command.
- [Maturity audit](docs/formal_study/project_maturity_review_v1/README.md) and [implementation follow-up](docs/formal_study/project_maturity_review_v1/IMPLEMENTATION_FOLLOWUP.md).
- [Author confirmations](docs/formal_study/manuscript_v1/AUTHOR_CONFIRMATION.md): reviewer background is confirmed; secondary-analysis ethics, authorship, funding, conflicts, release permissions and journal selection remain author-owned.

Formal generation and expert collection are complete. Do not regenerate the completed 105 reports or modify frozen outcomes to rebuild the paper. The next submission work is author completion, final manuscript review and journal-specific formatting.

## Offline analysis

The portable bundle starts from preserved human judgments and saved report material; it recomputes the frozen analysis, all original-rater outcome estimates, pairwise agreement, targeted wording scenarios and manuscript tables. It does not call model APIs or reconstruct raw recordings. See the [bundle instructions](docs/formal_study/reproducibility_v1/README.md) for the local researcher-only ZIP and tested commands.

A public clone does not include every private numerical input, raw dataset or model identity mapping. The allowlisted bundle supplies the inputs needed for numerical replay without relying on those ignored local folders. It contains identities and rating data and must not be sent to a blinded reviewer. Public release scope remains an author decision.

## Development environment and checks

Use Python 3.13. Create your own environment; no pre-existing `.venv` is assumed:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-cards.txt
PYTHONPYCACHEPREFIX=/tmp/gait-emg-pycache .venv/bin/python -m pytest -q -p no:cacheprovider tests
```

`requirements-cards.txt` includes the historical SDK/numerical lock plus the plotting dependency used by card integration tests. `requirements-analysis.lock.txt` is the smaller four-package environment for portable analysis and manuscript generation. `requirements.txt` describes broad dependencies; use the appropriate pinned file for reproduction.

The complete project suite also needs the local reviewed case assets and cached data; it is not a promise that every test works from a public clone lacking ignored inputs. The portable numerical replay has a separate self-contained input boundary. Keep Python bytecode outside cloud-managed folders to avoid on-demand file hydration during child-process startup.

To build a separate manuscript from the current local project:

```bash
.venv/bin/python scripts/build_manuscript_draft.py --output /tmp/gait-manuscript-review
```

The explicit output directory must not already exist. Omitting `--output` rebuilds generated files in `docs/formal_study/manuscript_v1`; preserve author edits first. The author-confirmation file is not overwritten. No API credentials are required for either analysis or manuscript generation.

## Dataset and interpretation boundaries

Source: Van Criekinge et al., *Scientific Data* (2023), [dataset publication](https://doi.org/10.1038/s41597-023-02767-y) and [Figshare collection](https://doi.org/10.6084/m9.figshare.c.6503791.v1). The release contains 50 stroke survivors and 138 able-bodied adults. Project analysis uses released participant-average normalized curves, with separate event-derived stroke spatiotemporal features. Raw downloads live in ignored `data/raw/`.

- The formal inputs use a threshold of 20% of each mean EMG curve's own peak. The minimum-run rule retains above-threshold runs meeting the 3% sample-count criterion; it does not filter below-threshold gaps. These are detector summaries, not clinical activation onsets or proof of continuous contraction.
- The supplied composite is **GPS-like**, based on four sagittal channels, rather than the validated nine-variable GPS. Peak absolute standardized deviation is a maximum across the cycle, not a single-point diagnostic z test.
- The normative reference is pooled, not individually age/speed matched. Controls use self-exclusion for their individual reference comparisons, while pooled calibration remains distinct. Shared reference participation limits external-validation claims.
- Cohort membership is disclosed. Missing events, matched timing references, stride variability and raw signal quality limit what can be inferred. Clinical questions and unsupported assertions are judged separately under the approved rules.

The [approved interpretation instructions](docs/formal_study/candidate_v3_1/APPROVAL_STATUS.md), [rubric](docs/formal_study/rubric_v2_draft/APPROVAL_STATUS.md), [case requirements](docs/formal_study/case_requirements_v1/README.md) and [execution protocol](docs/formal_study/execution_analysis_v3_draft/PROTOCOL.md) define the actual formal study. Later dated amendments and review stages are documented explicitly, not retroactively inserted into the historical protocol.

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/features/` | Feature extraction, normalized-data loaders and reference calculations |
| `src/llm/` | Prompt construction, provider adapters and guarded generation |
| `src/eval/` | Human-rating validation, frozen outcomes, agreement and sensitivity arithmetic |
| `scripts/` | Explicit build, audit, analysis and historical generation entry points |
| `tests/` | Numerical, workflow, integrity and offline fixture checks |
| `docs/formal_study/` | Approved study materials, review provenance, analysis and manuscript |
| `data/rating_packets_formal_v1/private/` | Local model mapping and detailed analysis inputs; excluded from normal Git tracking |
| `data/reproducibility_v1/` | Local researcher-only reproduction ZIP; excluded from normal Git tracking |

Completed batch runners retain source-identity and authorization guards. A historical plan can intentionally reject a changed source tree. Offline tests use temporary synthetic parent plans to test runner behavior; they do not update historical authorization or enable new live calls.

## Historical materials and language provenance

The initial 18-case pilot and four-control spot-check are development history. Early v1 inputs had extraction and framing defects; their reports and old `data/rating_packets/` are not the formal comparison or current reviewer materials. Old Likert rubrics and pilot generation scripts do not define the completed formal study. Use the [current independent review template](docs/formal_study/independent_expert_review_template_v1/README.md) when a blank example packet is needed; it includes all 105 formal reports.

Project documents and expert evidence are in English. Exact original-language evidence is isolated outside the active repository and is not a routine computational input. The [conversion record](docs/english_conversion/README.md) distinguishes original and translated hashes. Cleanup logs explain intentionally removed obsolete correspondence; historical provenance records remain historical.
