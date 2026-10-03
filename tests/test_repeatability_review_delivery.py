"""Packet delivery and import checks; synthetic judgments exist only in memory."""
from collections import Counter
from io import BytesIO
import json
import zipfile

import pytest
from openpyxl import load_workbook

from scripts.build_repeatability_review import OUT, PRIVATE, RATERS, sha, verify_folder, spaced_order
from src.eval.formal_rating import validate_return


def test_spacing_and_distinct_orders():
    orders = []
    for rater in RATERS:
        public = json.loads((OUT/rater/'reports.json').read_text())
        order, reports = public['order'], public['reports']
        assert len(order) == len(set(order)) == 150
        assert set(order) == set(reports)
        assert set(Counter(r['case_id'] for r in reports.values()).values()) == {6}
        last = {}
        for pos, rid in enumerate(order):
            case = reports[rid]['case_id']
            if case in last:
                assert pos - last[case] >= 8
            last[case] = pos
        orders.append(tuple(order))
    assert len(set(orders)) == 3


def test_scheduler_rejects_wrong_scope():
    with pytest.raises(ValueError):
        spaced_order({'one': ['R1']}, seed=1)


@pytest.mark.parametrize('rater', RATERS)
def test_blank_self_contained_packet_and_archive(rater):
    folder = OUT/rater
    public = json.loads((folder/'reports.json').read_text())
    integrity = json.loads((PRIVATE/'package_integrity.json').read_text())
    texts = {rid:(folder/'reports'/f'{rid}.txt').read_bytes() for rid in public['reports']}
    verify_folder(folder, public['order'], public['reports'], texts, integrity['requirements'])
    with zipfile.ZipFile(OUT/f'Repeatability_review_{rater}.zip') as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {str(p.relative_to(OUT)) for p in folder.rglob('*') if p.is_file()}
        for name in archive.namelist():
            assert archive.read(name) == (OUT/name).read_bytes()
    for metadata in public['reports'].values():
        assert set(metadata) == {'case_id','material_status'}
    book = load_workbook(folder/'Independent_ratings.xlsx')
    assert book.defined_names['ReportIDs'].attr_text == "'Review'!$A$2:$A$151"
    assert any(v.formula1 == 'ReportIDs' for v in book['Issues'].data_validations.dataValidation)
    assert sum(r[2]=='Partial text: administrative interruption' for r in book['Delivery_status'].iter_rows(min_row=2,values_only=True)) == 1


@pytest.mark.parametrize('rater', RATERS)
def test_synthetic_return_import_and_quote_validation_without_writing_scores(rater):
    folder = OUT/rater
    template = folder/'Independent_ratings.xlsx'
    before = sha(template)
    public = json.loads((folder/'reports.json').read_text())['reports']
    texts = {rid:(folder/'reports'/f'{rid}.txt').read_text() for rid in public}
    book = load_workbook(template)
    book['Instructions']['B15'] = 'Synthetic parser test; not an expert submission'
    book['Instructions']['B16'] = '2026-09-25'
    book['Instructions']['B17'] = 'Yes'
    for row in book['Review'].iter_rows(min_row=2):
        for cell, value in zip(row[3:], ['Completed','Yes','No','No','Synthetic parser fixture']):
            cell.value = value
    for row in book['Coverage'].iter_rows(min_row=2):
        for cell, value in zip(row[5:], ['Not covered','Final','Synthetic parser fixture']):
            cell.value = value
    rid = next(iter(public))
    book['Issues'].append([rid,'I001','Pending adjudication','E01',texts[rid][:80],
        'Synthetic parser location','Synthetic parser fixture',None,None])
    buffer = BytesIO(); book.save(buffer); buffer.seek(0)
    result = validate_return(buffer, template, public, texts)
    assert len(result['review']) == 150 and len(result['coverage']) == 864
    book['Issues']['E2'] = 'THIS SYNTHETIC QUOTATION DOES NOT APPEAR IN THE REPORT'
    buffer = BytesIO(); book.save(buffer); buffer.seek(0)
    with pytest.raises(ValueError, match='exact substring'):
        validate_return(buffer, template, public, texts)
    assert sha(template) == before
