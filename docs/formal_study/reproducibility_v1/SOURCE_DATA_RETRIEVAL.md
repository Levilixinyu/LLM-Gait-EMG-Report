# Source-data retrieval and verification boundary

The numerical replay ZIP does not need the source Excel/MAT downloads. Use this guide only when separately auditing feature extraction. Work in a separate checkout so historical audit outputs and frozen study inputs are not overwritten.

1. Start from the [Van Criekinge dataset publication](https://doi.org/10.1038/s41597-023-02767-y) and its linked [versioned Figshare collection](https://doi.org/10.6084/m9.figshare.c.6503791.v1). Retrieve the released postprocessed files named below. Preserve the original download bytes and publisher/version metadata; do not save the spreadsheets through Excel before hashing.
2. Place the files in the separate checkout's `data/raw/` directory. Fully download cloud-managed files before computation.
3. Compare SHA-256 values against the historical source-verification record below. A mismatch requires investigating the dataset version or downloaded bytes; do not update expected hashes merely to make the check pass.

| File | Recorded SHA-256 |
| --- | --- |
| `PostStrokeAdults.xlsx` | `905512c4deb0f90d54d01032f577446886280d6a6f8b6ead9c7096aab1ad16dd` |
| `AbleBodiedAdults.xlsx` | `a579373a15e3a92e4812bc38460fd3022b2d9d1c6f9fbe2c9da80acf25b6ffab` |
| `MAT_normalizedData_PostStrokeAdults.mat` | `e6abaea7e2f28e885b4332031cb2018583dd60f89b89cb79f33dbbc5ca38700b` |

Run from that checkout:

```bash
shasum -a 256 data/raw/PostStrokeAdults.xlsx data/raw/AbleBodiedAdults.xlsx data/raw/MAT_normalizedData_PostStrokeAdults.mat
```

These are project-recorded hashes from [sample eligibility verification](../sample_eligibility_v1/verification.json), not newly downloaded publisher-certified hashes. This follow-up did not download the raw files. The preceding maturity audit freshly checked the stroke Excel against the curve cache, but did not freshly reload the control Excel or processed MAT.

Feature code is in `src/features/figshare_loader.py`, `mat_spatiotemporal.py`, `pipeline.py`, `emg_signal.py` and `kinematic.py`. The historical `audit/recompute.py` reads all three downloads and writes to `audit/outputs`; it is an exploratory source audit, not a command to rebuild or replace formal reports. It includes historical comparison definitions and should only be run in a disposable checkout with its documented inputs. Control self-exclusion and final prompt formatting must be checked against the saved formal case summaries, not inferred from that exploratory script alone.

The cached curve SHA-256 recorded at eligibility was `e827c2a9abe73883232dd383b913b27a5a7bb5d886d0b66d258bf06815d76b18` for `audit/outputs/curves.npz`. The maturity audit recomputed all 35 formal cases and 3,302 stored numerical fields from verified cached curves/events. This is distinct from a new end-to-end reconstruction from raw C3D recordings. No such raw acquisition-to-feature validation is claimed by the portable analysis package.
