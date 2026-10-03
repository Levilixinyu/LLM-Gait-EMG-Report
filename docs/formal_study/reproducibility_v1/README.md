# Offline numerical reproduction

The local researcher bundle is `data/reproducibility_v1/Analysis_reproduction_v1.zip` (relative to the project root). It contains the allowlisted inputs needed for numerical replay, including model identities. It is not a blinded scoring packet and has not been authorized as a public release. It is excluded from normal Git tracking.

## Run from a separate directory

Extract the ZIP into a new working directory. Inside the extracted `analysis_reproduction` folder:

```bash
python3.13 -m venv ../gait-analysis-env
../gait-analysis-env/bin/python -m pip install -r requirements-analysis.lock.txt
../gait-analysis-env/bin/python -B scripts/reproduce_analysis.py --output ../reproduced-results
```

Install dependencies before disconnecting from the network, or install the pinned wheels from a prepared wheelhouse. The numerical replay uses no network, model API credentials, raw-data downloads or machine-specific project path. The results directory must be new and outside the extracted bundle.

Successful execution writes `REPRODUCTION_RESULT.json`, recomputed JSON estimates, the 20,000 shared resample-index rows and a separate rebuilt manuscript. The source bundle is verified before and after computation. Expected tables and saved estimate objects are comparison targets, not substitutes for recomputation.

## What is reproduced

- Frozen estimates for all 35 participants / 105 reports, including paired stroke BCa contrasts, control outcomes and unknown-status bounds.
- All three original independent outcome analyses, using reduced field-for-field exports from hash-verified original workbooks.
- Original pairwise agreement by cohort/domain and post-hoc nominal AC1 with participant-cluster bootstrap intervals; historical role labels remain metadata rather than numerical results.
- Seven targeted wording scenarios, including every per-report scenario row and aggregate summary.
- All 12 manuscript tables, including coverage-stage comparisons, post-hoc whitespace-based report lengths and supplementary original-rating AC1.

The bundle includes 105 saved report texts so claim anchors and report-length calculations can be checked. Original signature/background workbooks, API keys, raw recordings and external archive originals are omitted. Original workbook SHA-256 values accompany the reduced exports; no source judgment is changed. Some historical manifests refer to nonincluded files, but these are provenance references rather than replay dependencies.

For separate feature-source work, see [source retrieval and historical hashes](SOURCE_DATA_RETRIEVAL.md). For manuscript completion, see the [populated TRIPOD-LLM checklist](../reporting_checklist_v1/TRIPOD_LLM_CHECKLIST.md) and the earlier [selected reporting-topic crosswalk](REPORTING_CROSSWALK.md).

## Scope limits

This entry point starts from preserved scoring inputs. It does not independently judge report correctness, regenerate LLM responses, repeat raw C3D/MAT processing, establish a new expert consensus or confer ethical approval. Byte hashes establish file identity, not external authenticity. Rebuilt workbook ZIP metadata and generation timestamps may differ; numerical objects and all table values must match exactly in the tested environment.

## Maintain the bundle

After an intentional manuscript or replay-code change, build a new export to a new path:

```bash
python scripts/build_reproduction_bundle.py --output /path/to/new/Analysis_reproduction.zip
```

The exporter refuses an existing destination, checks source hashes, includes only an explicit allowlist and writes a manifest. Re-run the isolated replay before replacing the local working ZIP. Reviewer packets and frozen outcomes are not export destinations. See [validation record](VALIDATION.json) for the exact tested artifact and environment.
