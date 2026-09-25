"""Ensure replay refuses changed input and protected destinations before analysis."""
import hashlib
import json

import pytest

from scripts.reproduce_analysis import run, verify_bundle


def bundle(tmp_path, name='input.json'):
    root = tmp_path/'bundle'
    root.mkdir()
    raw = b'{"value": 1}\n'
    (root/'input.json').write_bytes(raw)
    (root/'REPRODUCTION_MANIFEST.json').write_text(json.dumps({
        'schema':1,'files':{name:hashlib.sha256(raw).hexdigest()}}))
    return root


def test_modified_input_cannot_produce_results(tmp_path):
    root = bundle(tmp_path)
    (root/'input.json').write_text('{"value": 2}\n')
    output = tmp_path/'results'
    with pytest.raises(ValueError,match='hash mismatch'):
        run(root,output)
    assert not output.exists()


def test_manifest_cannot_read_outside_bundle(tmp_path):
    root = bundle(tmp_path, '../input.json')
    with pytest.raises(ValueError,match='Unsafe manifest path'):
        verify_bundle(root)


def test_existing_results_and_bundle_directory_are_protected(tmp_path):
    root = bundle(tmp_path)
    output = tmp_path/'existing'
    output.mkdir()
    marker = output/'keep.txt'
    marker.write_text('preserve')
    for destination in (output, root/'new-results'):
        with pytest.raises(ValueError,match='new directory outside'):
            run(root,destination)
    assert marker.read_text() == 'preserve'
    assert not (root/'new-results').exists()
