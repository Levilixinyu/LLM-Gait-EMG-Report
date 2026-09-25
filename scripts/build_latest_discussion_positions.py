"""Refresh discussion positions from the three merged returns, without adjudication."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'docs/formal_study/three_rater_discussion_v2'
OUT = D / 'Three_rater_current_positions.xlsx'
PATHS = {
    'rater1': D / 'Three_rater_discussion_merged_for_confirmation_rater1.xlsx',
    'rater2': D / 'Three_rater_discussion_merged_for_confirmation_rater2.xlsx',
    'rater3': ROOT / 'outputs/rater3_independent/Three_rater_discussion_merged_rater3_completed.xlsx',
}
# The retained return includes every template field. No obsolete blank workbook
# is needed; only the generated copy's common-outcome fields are cleared.
BASE = PATHS['rater1']
SHEETS = ['Coverage discussion', 'Interpretation discussion', 'Other pending claims']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p): sha(p) for p in [BASE, *PATHS.values()]}
FEEDBACK = D / 'DISCUSSION_FEEDBACK.json'
feedback = {}
feedback_record = {}
closure = False
if FEEDBACK.exists():
    before[str(FEEDBACK)] = sha(FEEDBACK)
    feedback_record = json.loads(FEEDBACK.read_text())
    closure = bool(feedback_record.get('latest_closing_return'))
    for entry in feedback_record['rows']:
        assert (entry['rater'], entry['item']) not in feedback
        if entry.get('source_file'):
            assert sha(ROOT / entry['source_file']) == entry['source_sha256'], 'Closing return changed; review before rebuilding.'
        feedback[entry['rater'], entry['item']] = entry
    assert len(feedback) == 18
if OUT.exists():
    prior = load_workbook(OUT)
    for name in SHEETS:
        assert not any(c.value for row in prior[name].iter_rows(min_row=2, min_col=17, max_col=20) for c in row), 'Shared outcomes entered; do not overwrite.'

w = load_workbook(BASE)
for name in SHEETS:
    for row in w[name].iter_rows(min_row=2, min_col=17, max_col=20):
        for cell in row:
            cell.value = None
returns = {who: load_workbook(p, data_only=True) for who, p in PATHS.items()}
confirmations = w.create_sheet('Returned confirmations')
confirmations.append(['Rater', 'Sheet', 'Item', 'Source row', 'Returned decision field', 'Returned confirmed by', 'Returned date', 'Meaning'])
counts = Counter()
changes = []
for name in SHEETS:
    tabs = {who: {r[0]: (n, r) for n, r in enumerate(list(book[name].values)[1:], 2)} for who, book in returns.items()}
    ws = w[name]
    for i, who in enumerate(PATHS):
        ws.cell(1, 11 + i, f'{who} latest response (source text or labeled summary)')
    assert all(set(tab) == {ws.cell(n, 1).value for n in range(2, ws.max_row + 1)} for tab in tabs.values())
    for n in range(2, ws.max_row + 1):
        key = ws.cell(n, 1).value
        rr = [tabs[who][key][1] for who in PATHS]
        assert all(r[1] == ws.cell(n, 2).value for r in rr)
        r1, r2, r3 = rr
        p1 = re.search(r'Current individual position: ([^.]+)', r1[17]).group(1)
        # Only the unresolved row's author's own prose supplies a position.
        p2 = r2[16] if r2[16] != 'Unresolved' else ('Pending adjudication' if key in ['D010', 'D024'] else 'Acceptable')
        p3 = r3[16] if r3[16] != 'Unresolved' else ('Acceptable' if key == 'D024' else 'Pending adjudication')
        if r2[16] == 'Unresolved':
            assert key in ['D002', 'D004', 'D008', 'D010', 'D024'] or name == 'Other pending claims'
            assert p2.split()[0] in r2[17]
        if r3[16] == 'Unresolved' and ('rater3', key) not in feedback:
            assert p3.split()[0] in r3[17]
        positions = [p1, p2, p3]
        for i, (who, pos, row) in enumerate(zip(PATHS, positions, rr)):
            update = feedback.get((who, key))
            if update:
                pos = update['position']
                positions[i] = pos
            old = ws.cell(n, 6 + i).value
            if old != pos:
                changes.append((name, n, key, who, old, pos))
            ws.cell(n, 6 + i, pos)
            ws.cell(n, 11 + i, row[17])
            source_n = tabs[who][key][0]
            ws.cell(n, 14 + i, f'{PATHS[who].relative_to(ROOT)} | {name} row {source_n}')
            if update:
                label = update.get('source_kind', 'English summary of study-lead-forwarded discussion feedback; not a verbatim quotation or signature.')
                ws.cell(n, 11 + i, label + '\n\n' + update['reason_summary'])
                source_label = f'{update["source_file"]} | {update["source_sheet"]} row {update["source_row"]}' if update.get('source_file') else f'{FEEDBACK.relative_to(ROOT)} | {who} | {key}; earlier workbook response retained in its source file'
                ws.cell(n, 14 + i, source_label)
            confirmations.append([who, name, key, source_n, row[16], row[18], row[19], 'Verbatim returned fields; individual response confirmation only. Not a new joint signature.'])
        p1 = positions[0]
        status = 'Positions differ' if len(set(positions)) != 1 else ('Aligned - pending' if p1 == 'Pending adjudication' else 'Aligned - decision')
        counts[status] += 1
        ws.cell(n, 9, status)
        ws.cell(n, 10).value = None if status == 'Positions differ' else p1
        ws.cell(n, 9).fill = PatternFill('solid', fgColor={'Positions differ': 'FFF0CE', 'Aligned - pending': 'E9DDF5', 'Aligned - decision': 'DDF0E1'}[status])
        assert all(ws.cell(n, c).value is None for c in range(17, 21))
        final_entry = next((e for e in feedback_record.get('final_disposition_register', []) if e['item'] == key and e.get('accepted_final_disposition')), None)
        if final_entry:
            ws.cell(n, 17, final_entry['accepted_final_disposition'])
            ws.cell(n, 18, f"Source-linked administrative registration of accepted final Pending ({final_entry['category']}). Preferred interpretations remain in columns F-H. This is not a confirmed error or a confirmed correct claim. {final_entry['grouping_or_scope']} Rater1/rater2 explicitly accepted in forwarded final replies; rater3 acceptance is documented in the final disposition record. No new interpretation rule or signature is created.")
            ws.cell(n, 19, 'rater1; rater2; rater3 (acceptances transcribed from source records)')
            ws.cell(n, 20, final_entry['registration_date'])
        if key == 'D024':
            report = ROOT / f'docs/formal_study/rating_delivery_v1/rater2/reports/{ws.cell(n, 2).value}.txt'
            line = report.read_text().splitlines()[39]
            assert 'significant standardized deviation' in line and '21.7' in line
            ws.cell(n, 4, line)
            ws.cell(n, 5, 'Exact full report line 40. The remaining E02 question concerns significant in the Given clause. The clinical question does not equate 81% with late stance; the phase allegation is withdrawn. Replaces the older partial anchor, not the source report.')

expected = {'Aligned - decision': 22, 'Positions differ': 4, 'Aligned - pending': 12} if closure else ({'Aligned - decision': 22, 'Positions differ': 5, 'Aligned - pending': 11} if feedback else {'Aligned - decision': 21, 'Positions differ': 6, 'Aligned - pending': 11})
assert dict(counts) == expected
intro = w['Read first']
intro.delete_rows(1, intro.max_row)
for row in [
    ('Topic', 'Instructions'),
    ('Status', 'Current individual positions from retained merged returns and any later study-lead-forwarded feedback in DISCUSSION_FEEDBACK.json. This is a 38-item discussion snapshot, not a complete final scoring dataset or signed consensus. Forwarded feedback is recorded as English summaries, not new signed workbook returns.'),
    ('Counts', f'{counts["Aligned - decision"]} matching substantive decisions; {counts["Aligned - pending"]} shared Pending; {counts["Positions differ"]} differing positions. All 4 coverage items align.'),
    ('Changes', f'{len(changes)} individual-position cells differ from the earlier template. D024 anchor quotes the full actual report line 40 containing significant. Original expert workbooks remain unchanged.'),
    ('Reading source replies', 'The three latest-position columns reflect each author\'s own returned stance. Verbatim reasons can still contain outdated descriptions of peers. Rater1\'s Unresolved fields are administrative holds; explicit individual positions are stated in the reasons. Rater2\'s blank confirmation fields on disputed rows do not imply missing substantive answers.'),
    ('Remaining differences', ('D002, D004; RA857737CABCC0FB8 I001 and RDB18B7C593D48194 I002. D024 now has three Pending positions; rater3 accepts the median-wording rule but rater1 has not accepted it.' if closure else ('D002, D004; D024; RA857737CABCC0FB8 I001 and RDB18B7C593D48194 I002. D008 now has three Acceptable positions.' if feedback else 'D002, D004, D008; D024; RA857737CABCC0FB8 I001 and RDB18B7C593D48194 I002.')) + ' Pending is not a confirmed error. Conditional fallbacks and proposed rules are not adopted decisions.'),
    ('Review limits', 'This audit reviewed the 38 discussion items against relevant report text and rules. It also verified exact report-substring correspondence for the 298 earlier issue quotations. It did not independently rerate every report or every coverage requirement; matching labels do not prove agreement on all categories, grouping or flags.'),
    ('What to fill', 'Record an actually agreed outcome in the final four blue columns. Common decision, Discussion reason, Confirmed by and Confirmation date remain blank. Existing personal confirmations are preserved separately in Returned confirmations; they are not copied into common-signature fields.'),
    ('Evidence', 'Use Report ID and Case ID to consult the blinded report and model input. Read full source reasons using the formula bar or expanded row heights. Source notes retain earlier disclosures and are historical context, not current score totals.'),
    ('Analysis boundary', 'Original independent ratings remain separate. This file creates no new independent assessments, adjudications, missing-score policy or model ranking.'),
]:
    intro.append(row)
if feedback_record.get('closure_completed'):
    for row in intro.iter_rows(min_row=2):
        if row[0].value == 'Remaining differences':
            row[1].value = 'All five targeted dispositions are closed as Pending: D002, D004, D024 and the two within-median claims. Four preferred-label differences remain as discussion evidence, not outstanding requests for another review. The other 11 shared Pending items remain separate; this record is not a final statistical handling policy.'
        if row[0].value == 'What to fill':
            row[1].value = 'The five targeted final Pending outcomes are registered from explicit source acceptances. These are not new signatures. Other common-outcome fields remain blank. The builder refuses to overwrite a workbook containing registered common outcomes.'
    intro.append(('Five-item closure', 'D002/D004 E03; D024 E02 with E04 withdrawn; two within-median claims E01, one group per report. Final disposition agreed; substantive interpretation unresolved. Pending contributes no confirmed error and must not silently become a correct claim. Registration date 2026-09-20.'))

sources = w['Sources']
for who, path in PATHS.items():
    sources.append([f'Latest merged return: {who}', str(path.relative_to(ROOT)), sha(path)])
if feedback:
    sources.append(['Later study-lead-forwarded discussion feedback; English summaries', str(FEEDBACK.relative_to(ROOT)), sha(FEEDBACK)])
log = w.create_sheet('Refresh record')
log.append(['Sheet', 'Row', 'Item', 'Rater', 'Earlier position', 'Latest returned position'])
for row in changes:
    log.append(row)
extra_sheets = []
if feedback_record.get('final_disposition_register'):
    disposition = w.create_sheet('Final disposition record')
    disposition.append(['Item', 'Accepted final disposition' if feedback_record.get('closure_completed') else 'Proposed final disposition', 'Category', 'Rater1 disposition response', 'Rater2 disposition response', 'Rater3 disposition response', 'Status', 'Count as confirmed error', 'Grouping or scope', 'Source and confirmation boundary'])
    for entry in feedback_record['final_disposition_register']:
        disposition.append([entry[k] for k in ['item', 'proposed_final_disposition', 'category', 'rater1', 'rater2', 'rater3', 'status', 'count_as_confirmed_error', 'grouping_or_scope']] + ['DISCUSSION_FEEDBACK.json and referenced returns. Administrative transcription; no new signatures. Preferred interpretations remain in the discussion sheets.'])
    extra_sheets.append(disposition)
    intro.append(('Final disposition versus preference', 'See Final disposition record. All five final Pending outcomes are accepted; preferred interpretations remain unchanged.' if feedback_record.get('closure_completed') else 'See Final disposition record for explicit acceptance of final Pending, separately from preferred interpretations. Rater1/rater2 accept all five; rater3 offers a fallback for D002/D004, retains Pending on D024, and has not accepted final Pending for the two within-median items. No final rule or signature is inferred.'))
for ws in [intro, confirmations, log, *extra_sheets]:
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='24476A')
    for row in ws:
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            ws.column_dimensions[cell.column_letter].width = 32
    for row in range(2, ws.max_row + 1):
        ws.row_dimensions[row].height = 75
intro.column_dimensions['B'].width = 115
for ws in w:
    for row in ws:
        for cell in row:
            assert cell.data_type not in ['f', 'e']
            assert not re.search(r'[\u3400-\u9fff]', str(cell.value or ''))
assert all(sha(Path(path)) == digest for path, digest in before.items()), 'Source changed during refresh.'
w.save(OUT)
reopened = load_workbook(OUT, data_only=False)
assert reopened['Interpretation discussion']['D19'].value.startswith('*   Given the significant')
final_keys = {e['item'] for e in feedback_record.get('final_disposition_register', []) if e.get('accepted_final_disposition')}
for sn in SHEETS:
    for n in range(2, reopened[sn].max_row + 1):
        if reopened[sn].cell(n, 1).value in final_keys:
            assert reopened[sn].cell(n, 17).value == 'Pending adjudication'
            assert reopened[sn].cell(n, 20).value == '2026-09-20'
        else:
            assert all(reopened[sn].cell(n, c).value is None for c in range(17, 21))
print(OUT)
print(dict(counts))
print('Updated position cells:', len(changes), '| Sources unchanged | Registered final dispositions:', len(final_keys))
