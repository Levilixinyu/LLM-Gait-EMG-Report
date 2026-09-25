"""Verify translated working files without opening external archived evidence.

This checks the English-conversion snapshot, not the original experimental freeze.
After deliberate later edits, a mismatch means the conversion snapshot has changed.
It is never a reason to restore an archive or regenerate a completed model batch.
"""
from pathlib import Path
import hashlib
import json
import sys


def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root / 'docs/english_conversion/manifest.json').read_text())
    failures = []
    for entry in manifest['files']:
        path = root / entry['english_path']
        if not path.resolve().is_relative_to(root):
            failures.append({'path': entry['english_path'], 'reason': 'outside project'})
        elif not path.is_file():
            failures.append({'path': entry['english_path'], 'reason': 'missing'})
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry['english_sha256']:
            failures.append({'path': entry['english_path'], 'reason': 'changed since conversion'})
    return {'files_checked': len(manifest['files']), 'failures': failures,
            'external_archives_accessed': False}


if __name__ == '__main__':
    result = verify(Path(__file__).resolve().parents[1])
    print(json.dumps(result, indent=2))
    sys.exit(bool(result['failures']))
