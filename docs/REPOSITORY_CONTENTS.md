# Repository contents

This repository stores the project source code, tests, dependency files, study
planning documents, and audit records. Historical v1 code is retained under
`v1_freeze/`; it is not the current generation entry point.

The following local files are intentionally excluded from Git:

- `.env`, API keys, virtual environments, and caches.
- Downloaded datasets under `data/raw/` and reference PDFs.
- Generated model reports and expert-rating packets, including unblinding keys.
- Downloaded audit sources and the large `audit/outputs/curves.npz` cache.
- The researcher-only numerical reproduction bundle under `data/reproducibility_v1/`.

These files remain on the original computer. This repository is not a complete
backup of the datasets or generated research artifacts. See the main README for
the original dataset sources. Audit manifests may describe excluded local files;
retain the local artifacts to reproduce those historical checks. Some audit probe
scripts also refer to machine-specific temporary snapshots.

For full local tests, use Python 3.13, create a virtual environment, and install
`requirements-cards.txt` (the base lock plus matplotlib). Run
`PYTHONPYCACHEPREFIX=/tmp/gait-emg-pycache python -m pytest -q -p no:cacheprovider tests`
with the required local case assets present. For self-contained offline numerical
replay, follow [reproduction instructions](formal_study/reproducibility_v1/README.md)
and use the smaller `requirements-analysis.lock.txt` environment. A clone alone is
not the portable research bundle. Copy `.env.example` to `.env` only when configuring
API access; never commit the filled-in file. Generation scripts make paid API
calls. Keep unblinding keys separate from materials shared with expert raters.
