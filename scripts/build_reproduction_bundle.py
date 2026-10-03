"""Export an allowlisted researcher-only offline analysis bundle; no live calls."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import zipfile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = 'data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(output):
    if output.exists():
        raise FileExistsError('Refusing to overwrite a reproduction bundle')
    files, original_sources = {}, {}

    def add(name, expected=None):
        if name in files:
            if expected and sha(files[name]) != expected:
                raise ValueError(f'Conflicting source identity: {name}')
            return files[name]
        path = ROOT/name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'Invalid bundle source: {name}')
        raw = path.read_bytes()
        if expected and sha(raw) != expected:
            raise ValueError(f'Source changed: {name}')
        files[name] = raw
        original_sources[name] = sha(raw)
        return raw

    manuscript_dir = 'docs/formal_study/manuscript_v1/'
    record = json.loads(add(manuscript_dir+'BUILD_RECORD.json'))
    for name, digest in record['source_sha256'].items():
        add(name, digest)
    for name in ('TABLE_DATA.json','AUTHOR_CONFIRMATION.md'):
        add(manuscript_dir+name, record['output_sha256'][name])
    checklist_dir = 'docs/formal_study/reporting_checklist_v1/'
    checklist_record = json.loads(add(checklist_dir+'BUILD_RECORD.json'))
    for name,digest in checklist_record['source_sha256'].items():
        add(name,digest)
    for name,digest in checklist_record['output_sha256'].items():
        add(checklist_dir+name,digest)
    frozen = json.loads(files['docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json'])
    reviews, provenance = {}, {}
    fields = {
        'Review': ('report_id','case_id','material_status','issue_review_complete'),
        'Coverage': ('report_id','case_id','requirement_id','decision','adjudication_status'),
        'Issues': ('report_id','issue_id','decision','categories','exact_quote','pathology_flag','normality_flag'),
    }
    for who, meta in frozen['original_independent_sources'].items():
        raw = (ROOT/meta['path']).read_bytes()
        if sha(raw) != meta['sha256']:
            raise ValueError(f'Original rating source changed: {who}')
        book = load_workbook(io.BytesIO(raw), data_only=False, read_only=True)
        review = {'rater':who,'stage':'original_independent'}
        for sheet, keys in fields.items():
            rows = iter(book[sheet].values)
            headers = next(rows)
            review[sheet.lower()] = [{k:dict(zip(headers,row)).get(k) for k in keys}
                                    for row in rows if any(v is not None for v in row)]
        book.close()
        reviews[who] = review
        provenance[who] = {'source_path':meta['path'],'source_sha256':meta['sha256'],
                           'export':'Only fields used by numerical analysis; source workbook not modified or included.'}
    name = 'reproduction_inputs/original_reviews.json'
    files[name] = (json.dumps({'reviews':reviews,'provenance':provenance},indent=2)+'\n').encode()
    for name in ('requirements-analysis.lock.txt','scripts/reproduce_analysis.py',
                 'scripts/build_reproduction_bundle.py','src/__init__.py','src/eval/__init__.py',
                 'src/eval/formal_analysis.py','src/eval/frozen_model_analysis.py',
                 'src/eval/three_rater_blinded.py','src/eval/wording_sensitivity.py'):
        add(name)
    files['README.md'] = b'''# Offline analysis reproduction bundle

Researcher-only: includes model identities and human rating data. Do not send this
archive to a blinded reviewer. Publication permissions and release licensing remain
author decisions. No credentials, raw recordings or original signature workbooks
are included. This package replays judgments; it does not make new judgments.

Use Python 3.13. From the extracted bundle directory:

```bash
python3.13 -m venv ../gait-analysis-env
../gait-analysis-env/bin/python -m pip install -r requirements-analysis.lock.txt
../gait-analysis-env/bin/python -B scripts/reproduce_analysis.py --output ../reproduced-results
```

Dependency installation requires a package source (or a prepared wheelhouse).
After installation, replay needs no network or API keys. The output directory must
not exist and must be outside the bundle. The script checks every manifest SHA-256
before computation and again afterward, then verifies exact equality of main and
original-rater estimates, pairwise agreement, post-hoc AC1, wording scenarios and all 12 manuscript
tables. It writes new results, resample indices and a rebuilt manuscript separately.
An existing explicit manuscript output directory is also refused.

Original workbook hashes accompany the reduced numerical exports. Hash verification
establishes identity, not external authenticity or correctness of expert judgments.
Agreement metadata retain the historical pair-role labels; numerical cohort results
are compared. Generated timestamps and spreadsheet container bytes are not required
to match; all table cell values and numerical estimate objects are.

Scope: saved features/reports and human scoring inputs through numerical analysis.
Raw C3D/MAT feature reconstruction, model API regeneration, independent clinical
validation and author's ethics/declaration completion are outside this package.
Some source registries refer to historical files outside this allowlist; they are
provenance records, not required replay inputs. Never load external archive originals.
'''
    manifest = {'schema':1,'python_build':platform.python_version(),
        'scope':'Researcher-only offline replay; includes identity mapping; not a reviewer packet or public release.',
        'files':{name:sha(raw) for name,raw in sorted(files.items())},
        'unchanged_project_source_sha256':original_sources,
        'original_review_export_provenance':provenance,
        'omitted':'Credentials, raw recordings, original workbooks/signatures, reviewer backgrounds and archived originals.'}
    files['REPRODUCTION_MANIFEST.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    for name,digest in original_sources.items():
        if sha((ROOT/name).read_bytes()) != digest:
            raise ValueError(f'Source changed during export: {name}')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,raw in sorted(files.items()):
            info = zipfile.ZipInfo('analysis_reproduction/'+name, date_time=(2026,9,24,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as dest:
        dest.write(buffer.getvalue())
    result = {'bundle':str(output),'sha256':sha(buffer.getvalue()),'files':len(files),
              'manifest_sha256':sha(files['REPRODUCTION_MANIFEST.json']),
              'original_workbooks_included':False,'source_ratings_changed':False}
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'data/reproducibility_v1/Analysis_reproduction_v1.zip')
    build(parser.parse_args().output.resolve())
