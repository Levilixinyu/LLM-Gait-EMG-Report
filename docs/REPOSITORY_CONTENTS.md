# Repository contents

This repository stores the project source code, tests, dependency files, study
planning documents, and audit records. Historical v1 code is retained under
`v1_freeze/`; it is not the current generation entry point.

The following local files are intentionally excluded from Git:

- `.env`, API keys, virtual environments, and caches.
- Downloaded datasets under `data/raw/` and reference PDFs.
- Generated model reports and expert-rating packets, including unblinding keys.
- Downloaded audit sources and the large `audit/outputs/curves.npz` cache.

These files remain on the original computer. This repository is not a complete
backup of the datasets or generated research artifacts. See the main README for
the original dataset sources. Audit manifests may describe excluded local files;
retain the local artifacts to reproduce those historical checks. Some audit probe
scripts also refer to machine-specific temporary snapshots.

For local tests, create a virtual environment, install `requirements.lock.txt`,
and run `python -m pytest -q tests`. Copy `.env.example` to `.env` only when configuring
API access; never commit the filled-in file. Generation scripts make paid API
calls. Keep unblinding keys separate from materials shared with expert raters.
