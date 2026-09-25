"""Build a blinded, descriptive discussion aid from preserved human submissions.

No scores, expert decisions, accepted locks, or model identities are changed.
"""
from collections import Counter
from difflib import SequenceMatcher
from hashlib import sha256
from io import BytesIO
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.formal_rating import validate_return

OUT = ROOT / 'docs/formal_study/three_rater_review_v1'
PACK = ROOT / 'data/rating_packets_formal_v1/raters/rater1'
RATERS = ('rater1', 'rater2', 'rater3')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def normalize(value):
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def main():
    receipt = json.loads((OUT / 'SUBMISSION_RECEIPT.json').read_text())
    data = {}
    for rater in RATERS:
        source = receipt['sources'][rater]
        for field in ('path', 'snapshot'):
            assert digest(ROOT / source[field]) == source['sha256'], (rater, field)
        book = load_workbook(ROOT / source['snapshot'], data_only=False)
        data[rater] = {'source': source}
        for sheet in ('Review', 'Coverage', 'Issues'):
            values = list(book[sheet].values)
            data[rater][sheet] = [
                dict(zip(values[0], row), source_excel_row=index)
                for index, row in enumerate(values[1:], 2) if any(v is not None for v in row)
            ]
    reports = json.loads((PACK / 'reports.json').read_text())['reports']
    texts = {rid: (PACK / 'reports' / f'{rid}.txt').read_text() for rid in reports}
    coverage = {r: {(x['report_id'], x['requirement_id']): x for x in data[r]['Coverage']} for r in RATERS}
    keys = set(coverage['rater1'])
    assert all(set(coverage[r]) == keys for r in RATERS)
    for key in keys:
        assert len({tuple(coverage[r][key][f] for f in ('case_id', 'required_wording', 'components')) for r in RATERS}) == 1
    validation = {}
    for r in RATERS:
        if r == 'rater3':
            with ZipFile(ROOT / 'docs/formal_study/independent_expert_review_template_v1/Independent_expert_review_template.zip') as z:
                template = BytesIO(z.read('independent_expert_review/Independent_ratings.xlsx'))
        else:
            template = PACK.parent / r / 'Independent_ratings.xlsx'
        try:
            validate_return(ROOT / data[r]['source']['snapshot'], template, reports, texts)
            validation[r] = 'PASS (structural validation; not clinical adjudication)'
        except ValueError as exc:
            validation[r] = f'NOT ACCEPTED: {exc}; validator stops at first failure. See all quote mismatches.'

    stats = {r: {
        'reports': len(data[r]['Review']),
        'coverage_rows': len(data[r]['Coverage']),
        'coverage_labels_including_provisional': dict(Counter(x['decision'] for x in data[r]['Coverage'])),
        'pending_coverage': sum(x['adjudication_status'] != 'Final' for x in data[r]['Coverage']),
        'issue_records': dict(Counter(x['decision'] for x in data[r]['Issues'])),
    } for r in RATERS}
    wb = Workbook()
    wb.remove(wb.active)

    def sheet(name, headers, rows):
        ws = wb.create_sheet(name)
        ws.append(headers)
        for row in rows:
            ws.append(row)
        ws.freeze_panes = 'C2' if len(headers) > 3 else 'A2'
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(color='FFFFFF', bold=True)
            cell.fill = PatternFill('solid', fgColor='244760')
        for col in ws.columns:
            title = str(col[0].value).lower()
            wide = any(t in title for t in ('reason', 'quote', 'component', 'wording', 'instruction', 'evidence', 'context', 'note', 'question'))
            ws.column_dimensions[col[0].column_letter].width = 65 if wide else 25
            for cell in col[1:]:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                if isinstance(cell.value, str):
                    cell.data_type = 's'
        return ws

    sheet('Read first', ['Topic', 'Instructions'], [
        ('Status', 'Internal blinded discussion aid. Three human expert submissions. Original decisions are preserved. Agent review notes are suggestions, not expert decisions or consensus.'),
        ('Sequence', 'Correct the 15 quote mismatches; review priority examples; discuss all 40 coverage rows and issue claims. Keep independent judgments and subsequent discussion outcomes separate.'),
        ('Coverage', 'All required AND components must be conveyed; OR accepts one complete route. Credit correct evidence anywhere in the report. Record a separate false assertion as an issue.'),
        ('Issue alignment', 'Issue IDs are local to each rater and report. Match the actual claim, quote and context, never I001 alone. All 208 source records are included without automatic merging. An unrecorded issue is not an explicit Acceptable decision.'),
        ('Decision fields', 'Human discussion fields start blank. Record participant names and confirmation date only after actual agreement. Disagreement or unresolved status can remain; no majority-based automatic decision.'),
        ('Quote suggestions', 'Candidate lines are retrieved by text similarity and are exact source lines, not approved quote replacements. The originating rater must check scope and context. Scores and original quotes have not been edited.'),
        ('Blinding', 'Only opaque report identifiers, clinical case IDs and delivered materials are used. No identity mapping was opened. Do not circulate this comparison to anyone still performing an independent assessment.'),
        ('Limits', 'Counts are descriptive, not model outcomes, error rates, or a reliability estimate. Reports and items are clustered within 35 participants. G03 is separate from core case coverage. The third-rater analysis role must be documented before final analysis.'),
        ('Preservation', 'SUBMISSION_RECEIPT.json identifies byte-exact administrative snapshots, not accepted canonical review locks or newly created signatures. Rater2 has quote validation failures.'),
        ('Locations', 'Source Excel row numbers refer to the preserved submitted workbooks. Report line numbers refer to data/rating_packets_formal_v1/raters/rater1/reports/<report_id>.txt.'),
    ])
    sheet('Rater summary', ['Rater', 'Reports', 'Covered', 'Partially covered', 'Not covered', 'Pending coverage', 'Error records', 'Acceptable records', 'Pending issue records', 'Validation note'], [
        [r, stats[r]['reports'], *[stats[r]['coverage_labels_including_provisional'].get(k, 0) for k in ('Covered', 'Partially covered', 'Not covered')], stats[r]['pending_coverage'], *[stats[r]['issue_records'].get(k, 0) for k in ('Error', 'Acceptable', 'Pending adjudication')], validation[r]] for r in RATERS
    ])
    all_rows, discuss, agreement = [], [], Counter()
    headers = ['Report ID', 'Case ID', 'Requirement ID', 'Domain', 'Required wording', 'Components']
    for r in RATERS:
        headers += [f'{r} decision', f'{r} status', f'{r} reason', f'{r} source Excel row']
    headers += ['Comparison status', 'Human discussion decision', 'Human discussion reason', 'Confirmed by', 'Confirmation date']
    for key in sorted(keys):
        c = coverage['rater1'][key]
        labels = [coverage[r][key]['decision'] for r in RATERS]
        pending = any(coverage[r][key]['adjudication_status'] != 'Final' for r in RATERS)
        status = 'Pending in at least one submission' if pending else ('Agreed final labels' if len(set(labels)) == 1 else 'Different final labels')
        agreement[status] += 1
        row = [key[0], c['case_id'], key[1], 'G03' if key[1] == 'G03' else 'Case core', c['required_wording'], c['components']]
        for r in RATERS:
            x = coverage[r][key]
            row += [x['decision'], x['adjudication_status'], x['evidence_and_reason'], x['source_excel_row']]
        row += [status, None, None, None, None]
        all_rows.append(row)
        if status != 'Agreed final labels':
            discuss.append(row)
    ws = sheet('Coverage discussion', headers, discuss)
    dv = DataValidation(type='list', formula1='"Covered,Partially covered,Not covered,Unresolved"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f'T2:T{ws.max_row}')
    sheet('All coverage', headers, all_rows)
    issue_rows, mismatches = [], []
    for r in RATERS:
        for x in data[r]['Issues']:
            rid, quote = x['report_id'], x['exact_quote'] or ''
            exact = bool(quote) and quote in texts[rid]
            key = f"{r}|{rid}|{x['issue_id']}"
            issue_rows.append([key, r, rid, reports[rid]['case_id'], x['issue_id'], x['decision'], x['categories'], quote, x['locations'], x['reason'], x['pathology_flag'], x['normality_flag'], x['source_excel_row'], 'Yes' if exact else 'No', None, None, None])
            if quote and not exact:
                candidates = sorted(((SequenceMatcher(None, normalize(quote), normalize(line), autojunk=False).ratio(), n, line) for n, line in enumerate(texts[rid].splitlines(), 1) if line.strip()), reverse=True)[:3]
                context = '\n\n'.join(f'Line {n}: {line}' for _, n, line in candidates)
                mismatches.append([key, r, rid, x['source_excel_row'], quote, context, 'Candidate source lines only; verify intended claim before correcting the original submission in a new returned version.', None, None])
    sheet('All issue records', ['Record key', 'Rater', 'Report ID', 'Case ID', 'Local issue ID', 'Independent decision', 'Categories', 'Original quote', 'Original locations', 'Original reason', 'Pathology flag', 'Normality flag', 'Source Excel row', 'Exact quote match', 'Human claim group', 'Human discussion decision', 'Human discussion reason'], issue_rows)
    sheet('Quote corrections', ['Record key', 'Rater', 'Report ID', 'Source Excel row', 'Original quote', 'Candidate source context', 'Review note', 'Reviewer confirmed quote', 'Reviewer confirmation'], mismatches)
    overview = []
    for rid in sorted(reports):
        row = [rid, reports[rid]['case_id']]
        for r in RATERS:
            count = Counter(x['decision'] for x in data[r]['Issues'] if x['report_id'] == rid)
            row += [count.get(k, 0) for k in ('Error', 'Acceptable', 'Pending adjudication')]
        overview.append(row)
    sheet('Report issue overview', ['Report ID', 'Case ID'] + [f'{r} {k}' for r in RATERS for k in ('Error', 'Acceptable', 'Pending')], overview)

    priorities = [
        ('RF47E397C5898FACA', 'R068', 'rater3', 'particularly the Knee GVS', 'Section 4 explicitly highlights knee and ankle. The rater3 reason says neither is singled out anywhere. Recheck coverage using the whole report; any unsupported clinical inference is a separate issue.'),
        ('R3AD4A91F72A3469A', 'R122', 'rater3', 'pronounced Gait Variable Scores', 'Section 4 explicitly highlights ankle and knee. The rater3 reason says no prominence cue exists anywhere. Required ordering is optional. Recheck coverage separately from any issue in that question.'),
        ('RFDBC4A9D68B47B2E', 'R133', 'rater3', 'Although 0.81', 'The requirement includes speed, near-lower-end position, and in-range not establishing matching. Rater3 cites only speed and matching. Identify evidence for the near-lower-end meaning or reconsider coverage. Apply the same check to R755BB9629402BE66/R133.'),
        ('R075761E4007BA0F7', 'R038', 'rater3', 'knee and pelvis show', 'The requirement includes a contrast between pelvic GVS and small pelvic excursion, beyond naming the joints. Recheck this component; numerical co-presence alone may not convey it. Related rows: R75DDE0A093290272/R038, R19E4468ADE32EF20/R152 and R5311F78DF2AA63EE/R182.'),
        ('RA41394F3D63E1EB5', 'R104', 'rater3', 'knee has the largest', 'The requirement asks for similar-magnitude, distributed differences across knee, ankle and hip. Ranking alone does not explicitly convey this component. Rater3 gives a generic ranking reason. Also check R35A2ECF06979D30D/R104.'),
        ('R1E2D350548AA90DA', 'Issue: explicit no-gap inference', 'rater3; all raters for consistency', 'did not fall below', 'Rater1 and rater2 record this assertion as Error; rater3 has no issue record for this report. Rounded 100% coverage plus a retained interval does not prove every sample stayed above threshold. Ask rater3 to review the specific assertion. No record is not an Acceptable judgment.'),
        ('R1E2D350548AA90DA', 'Issue: unsupported gender pronoun', 'rater1 and rater2', 'for him.', 'Rater1 records Error; rater2 records Acceptable as a non-clinical wording slip. Discuss whether an unsupported demographic assertion falls within E01 under the existing scope; preserve the distinction from the separate no-gap claim.'),
        ('RABAADEA37D48C316', 'G03', 'All three raters', 'Because the participant', 'Rater1 has a provisional partial label pending discussion, rater2 final partial, and rater3 covered. Decide whether the general alternative explanations plus CCI-specific caution convey the required control-case inference limitation across the report.'),
        ('R1D4B237475466B91', 'Issue: symmetry-index denominator', 'rater2', '15.8% of the mean step length', 'Recheck the Error label: 200*(P-N)/(P+N) equals 100*(P-N)/((P+N)/2). A negative index of 15.8% therefore means the difference is 15.8% of the two-step mean, which the report explicitly uses. This is different from an unsupported percentage shortening relative to the non-paretic step. No absolute step length is needed for this algebraic restatement.'),
        ('RF973ED392216FC1A', 'Issue: misidentified CCI pair', 'rater2; all raters for consistency', 'RF-vs-GAS', 'Rater1 and rater3 record the wrong CCI pair as E01; rater2 calls it an acceptable wording slip because the correct pair appears elsewhere. The rubric separates correct coverage from an unretracted false assertion. Recheck whether the stated reason supports Acceptable under that rule; do not automatically waive a factual error because its clinical consequence is small.'),
    ]
    priority_rows = []
    for n, (rid, req, target, phrase, note) in enumerate(priorities, 1):
        evidence = '\n'.join(f'Line {i}: {line}' for i, line in enumerate(texts[rid].splitlines(), 1) if phrase in line)
        assert evidence, (rid, phrase)
        priority_rows.append([f'P{n:02d}', rid, reports[rid]['case_id'], req, target, evidence, note, None, None])
    sheet('Priority rechecks', ['Priority ID', 'Report ID', 'Case ID', 'Requirement or claim', 'Suggested reviewers', 'Source evidence', 'Agent review note', 'Human response', 'Human decision'], priority_rows)
    pairs = {}
    for a, b in combinations(RATERS, 2):
        final = [key for key in keys if all(coverage[r][key]['adjudication_status'] == 'Final' for r in (a, b))]
        pairs[f'{a} vs {b}'] = {'final_pairs': len(final), 'same_label': sum(coverage[a][key]['decision'] == coverage[b][key]['decision'] for key in final)}
    summary = {'status': 'Descriptive blinded review; no consensus or model outcome analysis', 'raters': stats, 'validation': validation, 'coverage_comparison': dict(agreement), 'pairwise_final_label_counts': pairs, 'issue_records': len(issue_rows), 'quote_mismatches': len(mismatches), 'model_identity_key_read': False, 'sources': receipt['sources']}
    assert len(all_rows) == 552 and len(discuss) == 40 and len(issue_rows) == 208 and len(mismatches) == 15
    assert agreement == {'Agreed final labels': 512, 'Different final labels': 39, 'Pending in at least one submission': 1}
    target = OUT / 'Three_rater_discussion.xlsx'
    if target.exists():
        raise FileExistsError('Do not overwrite a discussion workbook that may contain human responses.')
    wb.save(target)
    (OUT / 'DESCRIPTIVE_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
    for r in RATERS:
        assert digest(ROOT / data[r]['source']['path']) == data[r]['source']['sha256']
    check = load_workbook(target)
    for ws in check:
        for row in ws:
            for cell in row:
                assert cell.data_type != 'f'
                assert not re.search(r'[\u3400-\u9fff]', str(cell.value or ''))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
