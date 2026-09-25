#!/usr/bin/env python3
"""Create a neutrally named blank template from the preserved third-reviewer ZIP."""
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
import zipfile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/formal_study/rating_delivery_rater3_v1'
OUT = ROOT / 'docs/formal_study/independent_expert_review_template_v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rename_instructions(text):
    return (text.replace('Third independent review: rater3', 'Independent expert review template')
            .replace('# Third independent review', '# Independent expert review template')
            .replace('the third independent reviewer', 'an independent clinical reviewer')
            .replace('You did not develop the criteria and are not being asked to endorse earlier decisions.',
                     'No prior participation in criteria development is required. You are not being asked to endorse earlier decisions.')
            .replace('Orientation for the sports medicine reviewer', 'Orientation for the independent clinical reviewer')
            .replace('rater3', 'reviewer'))


def build():
    if OUT.exists():
        raise FileExistsError('Do not overwrite a published template')
    source_bytes = (SOURCE / 'Formal_review_rater3.zip').read_bytes()
    source_record = json.loads((SOURCE / 'BUILD_RECORD.json').read_text())
    assert sha(source_bytes) == source_record['zip_sha256']
    entries = {}
    originals = {}
    changed = []
    administrative = {'ORIENTATION.html', 'START_HERE.html', 'HOW_TO_REVIEW.html',
                      'README.md', 'REVIEWER_BACKGROUND.md'}
    with zipfile.ZipFile(BytesIO(source_bytes)) as source:
        assert source.testzip() is None
        for name in source.namelist():
            assert name.startswith('rater3/') and not name.endswith('/')
            relative = name.removeprefix('rater3/')
            raw = source.read(name)
            originals[relative] = raw
            if relative in administrative or (relative.startswith('reading/') and re.fullmatch(r'R[0-9A-F]{16}\.html', Path(relative).name)):
                revised = rename_instructions(raw.decode()).encode()
            elif relative == 'Independent_ratings.xlsx':
                book = load_workbook(BytesIO(raw))
                assert book['Instructions']['B1'].value == 'rater3'
                book['Instructions']['B1'] = 'Unassigned reviewer (template)'
                stream = BytesIO()
                book.save(stream)
                revised = stream.getvalue()
            else:
                revised = raw
            entries[relative] = revised
            if revised != raw:
                changed.append(relative)
    # All source evidence and the reading order are byte-exact copies.
    for relative, raw in originals.items():
        if relative.startswith(('reports/', 'materials/')) or relative == 'reports.json':
            assert entries[relative] == raw
        if relative.endswith('.html'):
            before = re.findall(r'<pre[^>]*>(.*?)</pre>', raw.decode(), re.S)
            after = re.findall(r'<pre[^>]*>(.*?)</pre>', entries[relative].decode(), re.S)
            assert before == after, relative
    original = load_workbook(BytesIO(originals['Independent_ratings.xlsx']))
    template = load_workbook(BytesIO(entries['Independent_ratings.xlsx']))
    assert original.sheetnames == template.sheetnames
    for sheet in original:
        target = template[sheet.title]
        assert sheet.max_row == target.max_row and sheet.max_column == target.max_column
        assert [v.to_tree().attrib for v in sheet.data_validations.dataValidation] == [v.to_tree().attrib for v in target.data_validations.dataValidation]
        assert [v.formula1 for v in sheet.data_validations.dataValidation] == [v.formula1 for v in target.data_validations.dataValidation]
        for row in sheet:
            for cell in row:
                if (sheet.title, cell.coordinate) != ('Instructions', 'B1'):
                    assert cell.value == target[cell.coordinate].value
    assert template['Review'].max_row == 106 and template['Coverage'].max_row == 553
    assert template['Issues'].max_row == 1
    assert all(template['Instructions'].cell(n, 2).value is None for n in (15, 16, 17))
    assert all(all(value is None for value in row[5:]) for row in template['Coverage'].iter_rows(min_row=2, values_only=True))
    original.close()
    template.close()
    for name, raw in entries.items():
        if Path(name).suffix in {'.html', '.md', '.json', '.txt'}:
            text = raw.decode()
            assert 'rater3' not in text and 'third reviewer' not in text.lower()
            assert not re.search('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]', text)
    OUT.mkdir()
    archive = OUT / 'Independent_expert_review_template.zip'
    now = datetime.now(timezone.utc)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as result:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo('independent_expert_review/' + name, (now.year, now.month, now.day, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            result.writestr(info, raw)
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        assert len(check.namelist()) == len(entries) == 403
        for name, raw in entries.items():
            assert check.read('independent_expert_review/' + name) == raw
    message = (SOURCE / 'MESSAGE_TO_RATER3.md').read_text()
    message = rename_instructions(message).replace('third independent reviewer', 'independent expert reviewer')
    message = message.replace('Formal_review_reviewer.zip', 'Independent_expert_review_template.zip').replace('reviewer/START_HERE.html', 'independent_expert_review/START_HERE.html')
    (OUT / 'MESSAGE_TO_REVIEWER.md').write_text(message)
    (OUT / 'README.md').write_text('''# Independent expert review template

Download **Independent_expert_review_template.zip**, extract it, and open
**independent_expert_review/START_HERE.html**. The accompanying
**MESSAGE_TO_REVIEWER.md** contains instructions suitable for sending to a reviewer.

This is a blank template for the current formal study: 105 anonymized reports
from 25 stroke cases and 10 controls, with 552 coverage judgments. It includes
the exact model inputs, case requirements, reference cards, curves, approved
rubric, error definitions, teaching examples and completion instructions.

The template is not assigned to a named or numbered reviewer. Its completion
fields and judgments are blank. Save the completed workbook as
**Independent_ratings_reviewer_completed.xlsx** and the background form as
**Reviewer_background_reviewer_completed.md**, recording the actual reviewer
identity in the designated fields. The coordinator must assign a distinct
reviewer identity when registering the return.

This neutral name replaces the earlier third-reviewer delivery name. Only
administrative labels and suggested return filenames changed; report text,
inputs, criteria and the existing reading order are unchanged. It remains a
clinical-expert review template for this study, not a completed expert assessment
or a universal rubric for unrelated datasets. For multiple independent reviewers,
the coordinator should prepare distinct reading orders before distribution.

No completed ratings or model identity mapping are included. Preserve the
original blank template and return a separate completed copy. Earlier submitted
background records and review evidence are not renamed or reclassified by this
change.
''')
    record = {'created_utc': now.isoformat(), 'source_zip_sha256': sha(source_bytes),
              'template_zip_sha256': sha(archive.read_bytes()), 'files': len(entries),
              'administrative_files_changed': changed, 'reports': 105, 'coverage_rows': 552,
              'all_judgments_blank': True, 'evidence_and_requirements_unchanged': True,
              'workbook_only_changed_cell': 'Instructions!B1', 'reading_order_unchanged': True,
              'source_archive_preserved': True, 'completed_ratings_read_or_modified': False,
              'model_key_read': False, 'verification': 'Passed byte, workbook and ZIP checks'}
    (OUT / 'LOCAL_CONVERSION_RECORD.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    build()
