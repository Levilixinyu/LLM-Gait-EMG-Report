#!/usr/bin/env python3
"""Verify the third-reviewer packet without opening model keys or scored returns."""
from collections import Counter
from datetime import datetime, timezone
from html import unescape
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from openpyxl import load_workbook
from PIL import Image
from scripts.verify_formal_rating_delivery import Links, CJK, IDENTITY, REQUEST, sha
from src.eval.formal_rating import spaced_order

OUT = ROOT / 'docs/formal_study/rating_delivery_rater3_v1'
CANONICAL = ROOT / 'data/rating_packets_formal_v1'


def verify(folder_override=None):
    folder = Path(folder_override) if folder_override is not None else OUT / 'rater3'
    source = CANONICAL / 'raters/rater1'
    record = json.loads((OUT / 'BUILD_RECORD.json').read_text())
    integrity = json.loads((CANONICAL / 'private/package_integrity.json').read_text())
    assert sha(CANONICAL / 'private/package_integrity.json') == record['source_integrity_sha256']
    for name, expected in record['source_files_verified'].items():
        assert sha(CANONICAL / name) == expected == integrity['files_sha256'][name], name
    files = {str(p.relative_to(folder)): p for p in folder.rglob('*') if p.is_file()}
    assert set(files) == set(record['packet_files_sha256'])
    for name, path in files.items():
        assert sha(path) == record['packet_files_sha256'][name], name
        if name.startswith(('reports/', 'materials/')):
            assert path.read_bytes() == (source / name).read_bytes(), name
    public = json.loads((folder / 'reports.json').read_text())
    originals = {r: json.loads((CANONICAL / 'raters' / r / 'reports.json').read_text()) for r in ('rater1', 'rater2')}
    assert set(public) == {'order', 'reports'}
    assert public['reports'] == originals['rater1']['reports'] == originals['rater2']['reports']
    assert len(public['order']) == len(set(public['order'])) == len(public['reports']) == 105
    assert list(public['reports']) == sorted(public['reports'])
    assert all(set(meta) == {'case_id', 'material_status'} for meta in public['reports'].values())
    assert all(public['order'] != old['order'] for old in originals.values())
    cases = [public['reports'][rid]['case_id'] for rid in public['order']]
    assert len(set(cases)) == 35 and set(Counter(cases).values()) == {3}
    assert sum(c.startswith('stroke_') for c in cases) == 75
    assert sum(c.startswith('control_') for c in cases) == 30
    assert all(case not in cases[max(0, n-2):n] for n, case in enumerate(cases))
    provenance = json.loads((OUT / 'private/order_provenance.json').read_text())
    grouped = {}
    for rid, meta in public['reports'].items():
        grouped.setdefault(meta['case_id'], []).append(rid)
    assert spaced_order(grouped, provenance['seed']) == public['order'] == provenance['order']
    book = load_workbook(folder / 'Independent_ratings.xlsx', data_only=False)
    oldbook = load_workbook(source / 'Independent_ratings.xlsx', data_only=False)
    assert book.sheetnames == oldbook.sheetnames == ['Instructions', 'Review', 'Coverage', 'Issues']
    assert book['Instructions']['B1'].value == 'rater3'
    assert all(book['Instructions'].cell(n, 2).value is None for n in (15, 16, 17))
    for row in range(1, oldbook['Instructions'].max_row+1):
        for col in (1, 2):
            if (row, col) not in {(1, 2), (2, 2)}:
                assert book['Instructions'].cell(row, col).value == oldbook['Instructions'].cell(row, col).value
    assert [r[0] for r in book['Review'].iter_rows(min_row=2, values_only=True)] == public['order']
    assert book['Review'].max_row == 106 and book['Coverage'].max_row == 553 and book['Issues'].max_row == 1
    for name in ('Review', 'Coverage', 'Issues'):
        assert [c.value for c in book[name][1]] == [c.value for c in oldbook[name][1]]
        assert [v.formula1 for v in book[name].data_validations.dataValidation] == [v.formula1 for v in oldbook[name].data_validations.dataValidation]
    for row in book['Review'].iter_rows(min_row=2, values_only=True):
        assert row[1] == public['reports'][row[0]]['case_id']
        assert row[2:4] == ('Available', 'Not started') and all(v is None for v in row[4:])
    original_requirements = {(r[0], r[2]): r[:5] for r in oldbook['Coverage'].iter_rows(min_row=2, values_only=True)}
    actual_requirements = {}
    coverage_rows = {}
    for n, row in enumerate(book['Coverage'].iter_rows(min_row=2, values_only=True), 2):
        actual_requirements[(row[0], row[2])] = row[:5]
        coverage_rows.setdefault(row[0], []).append((n, row))
        assert all(v is None for v in row[5:])
    assert actual_requirements == original_requirements
    assert sum(r[2] == 'G03' for r in actual_requirements.values()) == 105
    assert [rows[0][1][0] for rows in coverage_rows.values()] == public['order']
    for sheet in book:
        for row in sheet:
            for cell in row:
                assert cell.data_type != 'f'
                if isinstance(cell.value, str):
                    assert not CJK.search(cell.value) and not IDENTITY.search(cell.value) and not REQUEST.search(cell.value)
    book.close()
    oldbook.close()
    start = (folder / 'START_HERE.html').read_text()
    assert re.findall(r'href="reading/(R[0-9A-F]{16})\.html"', start) == public['order']
    for pos, rid in enumerate(public['order'], 1):
        view = (folder / 'reading' / f'{rid}.html').read_text()
        case = public['reports'][rid]['case_id']
        for key, path in [('report-text', folder / 'reports' / f'{rid}.txt'), ('system-text', folder / 'materials' / case / 'model_system_prompt.txt'), ('user-text', folder / 'materials' / case / 'model_user_prompt.txt'), ('reference-text', folder / 'materials' / case / 'reference_card.md')]:
            assert unescape(re.search('<pre id="' + key + '">(.*?)</pre>', view, re.S).group(1)) == path.read_text()
        assert f'Report {pos} of 105 / Review spreadsheet row {pos+1}' in view
        for n, row in coverage_rows[rid]:
            from html import escape
            expected = '<tr><td>' + str(n) + '</td><td>' + escape(row[2]) + '</td><td>' + escape(row[3]) + '</td><td>' + escape(row[4]) + '</td></tr>'
            assert expected in view
        nav = re.findall(r'href="(R[0-9A-F]{16})\.html"', view)
        expected_nav = ([public['order'][pos-2]] if pos > 1 else []) + ([public['order'][pos]] if pos < 105 else [])
        assert nav == expected_nav * 2
    links = 0
    images = 0
    for name, path in files.items():
        assert not any(x in name.lower() for x in ('private', 'answer_key', 'completed', 'mapping', 'reconciliation', '__macosx'))
        assert not IDENTITY.search(name)
        if path.suffix in {'.txt', '.md', '.html', '.json'}:
            text = path.read_text()
            assert not CJK.search(text) and not REQUEST.search(text), name
            assert not IDENTITY.search(text), name
            if path.suffix == '.html':
                parser = Links()
                parser.feed(text)
                assert not parser.remote
                for link in parser.links:
                    if link.startswith('#'):
                        continue
                    target = (path.parent / link.split('#')[0]).resolve()
                    assert target.is_relative_to(folder.resolve()) and target.is_file(), (name, link)
                    links += 1
        elif path.suffix == '.png':
            with Image.open(path) as image:
                image.verify()
            images += 1
    with zipfile.ZipFile(folder / 'Independent_ratings.xlsx') as z:
        for name in z.namelist():
            if name.endswith('.xml'):
                text = z.read(name).decode()
                assert not IDENTITY.search(text) and not REQUEST.search(text)
    for name in ('HOW_TO_REVIEW.html', 'ORIENTATION.html', 'START_HERE.html', 'README.md'):
        assert 'both independent' not in (folder / name).read_text()
    archive = OUT / 'Formal_review_rater3.zip'
    assert sha(archive) == record['zip_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {'rater3/' + name for name in files}
        assert len({info.date_time for info in z.infolist()}) == 1
        for name, path in files.items():
            assert z.read('rater3/' + name) == path.read_bytes()
    result = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS', 'reports': 105, 'cases': 35, 'coverage_rows': 552, 'human_judgments_and_completion_fields_blank': True, 'original_source_hashes_unchanged': True, 'report_input_reference_and_curve_bytes_unchanged': True, 'requirement_wording_and_components_unchanged': True, 'order_distinct_from_both_original_raters': True, 'minimum_same_case_gap': 'Two other reports', 'order_reproducible_from_saved_seed': True, 'workbook_dropdowns_and_immutable_columns_verified': True, 'html_text_and_workbook_row_links_verified': True, 'local_links_verified': links, 'curve_images_decoded': images, 'no_provider_names_or_private_material_in_packet': True, 'no_chinese_characters_in_text_or_workbook': True, 'zip_entry_count': len(files), 'zip_crc_and_entry_bytes_verified': True, 'zip_sha256': sha(archive), 'model_key_read': False, 'completed_review_files_read': False, 'browser_rendering_test_performed': False, 'validator_sha256': sha(Path(__file__))}
    (OUT / 'VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    if (OUT / 'rater3').is_dir():
        verify()
    else:
        # The superseded extracted copy may be removed after ZIP verification.
        # Validate from a temporary extraction, without recreating a working copy.
        with tempfile.TemporaryDirectory(prefix='gait-legacy-packet-verify-') as temporary:
            with zipfile.ZipFile(OUT / 'Formal_review_rater3.zip') as archive:
                for name in archive.namelist():
                    assert name.startswith('rater3/') and '..' not in Path(name).parts
                archive.extractall(temporary)
            verify(Path(temporary) / 'rater3')
