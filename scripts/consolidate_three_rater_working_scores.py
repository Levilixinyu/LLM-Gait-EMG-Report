"""Consolidate blinded post-discussion records, preserving independent baselines.

No model key, final-consensus importer, majority vote or new clinical judgment is
used. Discussion claims are aligned to existing records by exact source spans;
ambiguous or reused matches fail rather than silently merge separate claims.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / 'docs/formal_study/three_rater_discussion_v2'
OUT = ROOT / 'docs/formal_study/consolidated_ratings_v1'
RATERS = ['rater1', 'rater2', 'rater3']
hashes = {}


def source(path):
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return load_workbook(path, data_only=True)


def records(sheet):
    rows = list(sheet.values)
    return [dict(zip(rows[0], row)) for row in rows[1:]]


inventory = source(DISC / 'Three_rater_discussion.xlsx')
discussion = source(DISC / 'Three_rater_current_positions.xlsx')
feedback_path = DISC / 'DISCUSSION_FEEDBACK.json'
hashes[str(feedback_path.relative_to(ROOT))] = hashlib.sha256(feedback_path.read_bytes()).hexdigest()
feedback = json.loads(feedback_path.read_text())
assert feedback['closure_completed']['confirmed_error_count_for_these_items'] == 0
baseline = {who: source(ROOT / f'docs/formal_study/three_rater_review_v1/private/{who}_submitted.xlsx') for who in RATERS}
reviews = {who: {r['report_id']: r for r in records(book['Review'])} for who, book in baseline.items()}
coverage = records(inventory['All current coverage'])
issue_sources = records(inventory['All current issue records'])
issues = deepcopy(issue_sources)
texts = {}
for r in coverage:
    rid = r['Report ID']
    if rid not in texts:
        path = ROOT / f'docs/formal_study/rating_delivery_v1/rater2/reports/{rid}.txt'
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        texts[rid] = path.read_text()
assert len(texts) == 105 and len(coverage) == 552 and len(issues) == 298
for r in issues:
    assert r['Exact quote'] in texts[r['Report ID']]
    r.update({'Before decision': r['Current decision'], 'Before categories': r['Categories'],
              'Before quote': r['Exact quote'], 'Discussion item': None, 'Preferred interpretation': None,
              'Disposition basis': 'Retained individual post-recheck record; not newly adjudicated.'})

cov_index = {(r['Report ID'], r['Requirement']): r for r in coverage}
coverage_changes = []
for update in records(discussion['Coverage discussion']):
    row = cov_index[update['Report ID'], update['Item']]
    assert row['Required wording'] == update['Required meaning or exact anchor']
    for who in RATERS:
        old = row[f'{who} decision']
        new = update[f'{who} latest position']
        row[f'{who} decision'] = new
        row[f'{who} status'] = 'Final'
        row[f'{who} reason'] = update[f'{who} latest response (source text or labeled summary)']
        row[f'{who} source'] = update[f'{who} source']
        if old != new:
            coverage_changes.append([update['Report ID'], update['Item'], who, old, new])
for row in coverage:
    labels = {row[f'{who} decision'] for who in RATERS}
    statuses = {row[f'{who} status'] for who in RATERS}
    assert len(labels) == 1 and statuses == {'Final'}, (row['Report ID'], row['Requirement'])
    # Agreement is descriptive; do not manufacture a common confirmation.
    row['Matching post-discussion label'] = labels.pop()

CATS = {item: 'E03' for item in ['D001', 'D002', 'D004', 'D007', 'D008', 'D010', 'D012', 'D031', 'D032', 'A003']}
CATS.update({item: 'E02' for item in ['D014', 'D015', 'D016', 'D017', 'D024']})
CATS.update({item: 'E07' for item in ['D018', 'D019']})
CATS.update({item: 'E03;E04' for item in ['D020', 'D021', 'D022', 'D023']})
CATS.update(D033='E01', A002='E01;E05', A009='E05')
OTHER_CATS = {
    'RE6F8701EEB40440A': 'E08', 'RC0B47BA812A09BB5': 'E01', 'R5F404DA56F2E1FA6': 'E02',
    'R4835C5BD71F87EC3': 'E08', 'RA857737CABCC0FB8': 'E01', 'R35A2ECF06979D30D': 'E02',
    'RDB18B7C593D48194': 'E01', 'R320DCD2D7ECF50B9': 'E07',
    'R3AD4A91F72A3469A': 'E02', 'R35C7A84FBF5C7923': 'E07',
}


def spans(text, quote):
    start, result = 0, []
    while (start := text.find(quote, start)) >= 0:
        result.append((start, start + len(quote)))
        start += 1
    return result


claim_rows, crosswalk, used = [], [], set()
for sheet in ['Interpretation discussion', 'Other pending claims']:
    for row in records(discussion[sheet]):
        item, rid = row['Item'], row['Report ID']
        quote = row['Required meaning or exact anchor']
        text = texts[rid]
        assert quote in text
        preferred = [row[f'{who} latest position'] for who in RATERS]
        if row['Common decision']:
            assert row['Common decision'] == 'Pending adjudication'
            decision, basis = row['Common decision'], 'Explicitly accepted final Pending; preferences retained separately.'
        else:
            assert len(set(preferred)) == 1, item
            decision, basis = preferred[0], 'Matching explicit discussion positions; not a newly signed full-dataset release.'
        category = CATS[item] if item in CATS else OTHER_CATS[rid]
        canonical = item if sheet == 'Interpretation discussion' else f'OTHER_{rid}_{item.rsplit("|", 1)[1]}'
        line = text[:text.index(quote)].count('\n') + 1
        claim_rows.append({'claim_id': canonical, 'report_id': rid, 'case_id': row['Case ID'],
                           'decision': decision, 'categories': category, 'exact_quote': quote,
                           'report_line': line, 'basis': basis, 'discussion_item': item})
        anchor_spans = spans(text, quote)
        for who, pref in zip(RATERS, preferred):
            candidates = []
            for old in issue_sources:
                if old['Rater'] != who or old['Report ID'] != rid:
                    continue
                if any(max(a, c) < min(b, d) for a, b in anchor_spans for c, d in spans(text, old['Exact quote'])):
                    candidates.append(old)
            assert len(candidates) <= 1, (item, who, 'Ambiguous source-span match')
            if candidates:
                record_key = candidates[0]['Record key']
                assert record_key not in used, (record_key, 'Two claims map to one record; split explicitly')
                used.add(record_key)
                target = next(x for x in issues if x['Record key'] == record_key)
                action = 'Update existing record from explicit discussion of this claim'
            else:
                record_key = f'{who}|{rid}|DISC_{canonical}'
                target = {'Record key': record_key, 'Rater': who, 'Report ID': rid, 'Case ID': row['Case ID'],
                          'Local issue ID': f'DISC_{canonical}', 'Pathology flag': None, 'Normality flag': None,
                          'Before decision': None, 'Before categories': None, 'Before quote': None}
                issues.append(target)
                action = 'Add explicitly assessed discussion claim; not inferred from absent old issue'
            # Declared no-change flags remain as supplied. Missing flags remain
            # unsupplied rather than being silently converted to No.
            target.update({'Current decision': decision, 'Categories': category, 'Exact quote': quote,
                           'Report line': line, 'Locations': f'Report line {line}; retain source locations for grouped repetitions.',
                           'Reason': row[f'{who} latest response (source text or labeled summary)'],
                           'Adjudication status': 'Pending' if decision == 'Pending adjudication' else 'Post-discussion',
                           'Source': row[f'{who} source'], 'Discussion item': item,
                           'Preferred interpretation': pref, 'Disposition basis': basis,
                           'Quoted-scope note': 'Exact anchor identifies the discussed claim; repetition grouping and independent claims remain separate.'})
            if row['Common decision']:
                final = next(r for r in feedback['final_disposition_register'] if r['item'] == item)
                assert final['accepted_final_disposition'] == decision
                target['Final disposition evidence'] = (
                    f"Registered {final['registration_date']}: {final[who]} "
                    f"Final disposition: {decision}. {final['grouping_or_scope']} "
                    'Source: DISCUSSION_FEEDBACK.json, final_disposition_register. '
                    'Reason retains the earlier/source interpretation, which may predate this final acceptance.'
                )
            crosswalk.append([canonical, rid, who, record_key, action, target['Before decision'], decision,
                              pref, category, row[f'{who} source']])
assert len(claim_rows) == 34 and len(crosswalk) == 102
assert Counter(r['decision'] for r in claim_rows) == {'Acceptable': 14, 'Pending adjudication': 16, 'Error': 4}
assert len({r['Record key'] for r in issues}) == len(issues)
assert all(r['Exact quote'] in texts[r['Report ID']] for r in issues)

# Preserve all source record fields for reverse tracing, including flags and
# complete repeated-location descriptions, instead of erasing old group scope.
old_lookup = {r['Record key']: r for r in issue_sources}
for r in issues:
    old = old_lookup.get(r['Record key'])
    r['Original locations'] = old['Locations'] if old else None
    r['Original source'] = old['Source'] if old else None
    if old:
        assert r['Pathology flag'] == old['Pathology flag']
        assert r['Normality flag'] == old['Normality flag']

# Apply only the five explicitly requested residual responses. These add missing
# individual assessments; they do not establish a new global interpretation rule.
residual_specs = {
    'R25F5AA9361D9E14F': ('medial gastrocnemius (GAS)', 'E01', {'rater3'}),
    'R31D0B47CA4DF36CF': ('the mean envelope below threshold between the retained interval endpoints at 34% and 44%', 'E03', {'rater2', 'rater3'}),
    'RAF417EE5FDC33A78': ('maintained above-threshold activity for 100% of the gait cycle, remaining above threshold continuously across the cycle boundary', 'E03', {'rater1', 'rater3'}),
}
intake_path = OUT / 'RESIDUAL_RETURN_CHECK.json'
hashes[str(intake_path.relative_to(ROOT))] = hashlib.sha256(intake_path.read_bytes()).hexdigest()
intake = json.loads(intake_path.read_text())
residual_returns = []
for who in RATERS:
    path = ROOT / intake['sources'][who]['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == intake['sources'][who]['sha256']
    returned = source(path)
    for row in records(returned['Residual record differences']):
        decision = row.get('Returned disposition')
        if not decision:
            continue
        rid = row['Report ID']
        quote, category, expected_raters = residual_specs[rid]
        assert who in expected_raters and decision == 'Error'
        assert row.get('Rater', row.get('Confirmed by')) == who
        assert row.get('Error category', row.get('Existing category')) == category
        assert row['Returned reason'] and row['Confirmation date']
        assert quote in texts[rid]
        line = texts[rid][:texts[rid].index(quote)].count('\n') + 1
        assert not any(r['Rater'] == who and r['Report ID'] == rid and
                       any(max(a, c) < min(b, d) for a, b in spans(texts[rid], quote)
                           for c, d in spans(texts[rid], r['Exact quote'])) for r in issues)
        key = f'{who}|{rid}|RESIDUAL'
        issues.append({'Record key': key, 'Rater': who, 'Report ID': rid,
                       'Case ID': row['Case ID'], 'Local issue ID': 'RESIDUAL',
                       'Current decision': decision, 'Categories': category,
                       'Exact quote': quote, 'Locations': f'Report line {line}',
                       'Reason': row['Returned reason'], 'Pathology flag': None,
                       'Normality flag': None, 'Discussion item': f'RESIDUAL_{rid}',
                       'Preferred interpretation': decision,
                       'Disposition basis': 'Explicit human residual response; no new global rule adopted.',
                       'Source': str(path.relative_to(ROOT))})
        residual_returns.append([rid, row['Case ID'], who, decision, category, quote,
                                 line, row['Returned reason'], row['Confirmation date'],
                                 str(path.relative_to(ROOT))])
assert len(residual_returns) == 5 and len(issues) == 326
assert len({r['Record key'] for r in issues}) == len(issues)
for rid, (quote, category, _) in residual_specs.items():
    for who in RATERS:
        matched = [r for r in issues if r['Report ID'] == rid and r['Rater'] == who
                   and any(max(a, c) < min(b, d) for a, b in spans(texts[rid], quote)
                           for c, d in spans(texts[rid], r['Exact quote']))]
        assert len(matched) == 1 and matched[0]['Current decision'] == 'Error'
        assert matched[0]['Categories'] == category

# Import explicit audit decisions and flag annotations, keeping category proposals
# separate from registered categories and any common decision.
audit_path = OUT / 'SCORING_AUDIT_RETURN_CHECK.json'
hashes[str(audit_path.relative_to(ROOT))] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
audit = json.loads(audit_path.read_text())
audit_decisions, audit_flags, audit_categories = [], [], []
audit_start = deepcopy(issues)
for submitted in audit['sources']:
    who = submitted['rater']
    path = ROOT / submitted['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == submitted['sha256']
    returned = source(path)
    for row in records(returned['Targeted issue']):
        if row['Rater'] != who:
            continue
        assert row['Finding'] == 'F01' and row['Report ID'] == 'RDB18B7C593D48194'
        assert row['Returned disposition'] == 'Error' and row['Returned categories'] == 'E01'
        quote, rid = row['Exact quote'], row['Report ID']
        assert quote == 'medial gastrocnemius (GAS)' and quote in texts[rid]
        assert row['Returned reason'] and row['Confirmation date']
        assert not any(r['Rater'] == who and r['Report ID'] == rid and
                       any(max(a, c) < min(b, d) for a, b in spans(texts[rid], quote)
                           for c, d in spans(texts[rid], r['Exact quote'])) for r in issues)
        key = f'{who}|{rid}|AUDIT_F01'
        issues.append({'Record key': key, 'Rater': who, 'Report ID': rid,
                       'Case ID': row['Case'], 'Local issue ID': 'AUDIT_F01',
                       'Current decision': row['Returned disposition'],
                       'Categories': row['Returned categories'], 'Exact quote': quote,
                       'Locations': f"Report line {row['Line']}", 'Reason': row['Returned reason'],
                       'Pathology flag': None, 'Normality flag': None,
                       'Disposition basis': 'Explicit human targeted audit response; one new report-scoped group across three raters.',
                       'Source': submitted['path'] + ' | Targeted issue'})
        audit_decisions.append([key, who, rid, row['Returned disposition'],
                                row['Returned categories'], quote, row['Returned reason'],
                                row['Confirmation date'], submitted['path']])
    for row in records(returned['Control flags']):
        if row['Rater'] != who:
            continue
        matches = [r for r in issues if r['Record key'] == row['Record key']]
        assert len(matches) == 1
        target_row = matches[0]
        assert target_row['Rater'] == who and target_row['Report ID'] == row['Report ID']
        assert target_row['Exact quote'] == row['Quote']
        assert target_row['Current decision'] == row['Decision']
        assert row['Confirmed by'] == who and row['Reason'] and row['Date']
        old_flags = [target_row['Pathology flag'], target_row['Normality flag']]
        for field, returned_field in [('Pathology flag', 'Returned pathology'), ('Normality flag', 'Returned normality')]:
            assert row[returned_field] in ('Yes', 'No')
            target_row[field] = row[returned_field]
        audit_flags.append([row['Record key'], who, row['Report ID'], *old_flags,
                            row['Returned pathology'], row['Returned normality'],
                            row['Reason'], row['Date'], submitted['path']])
    for row in records(returned['Category alignment']):
        assert row['Confirmed by'] == who and row['Reason'] and row['Date']
        assert row['Quote'] in texts[row['Report ID']]
        assert set(row['Common tags if confirmed'].split(';')) <= {f'E{i:02}' for i in range(1, 10)}
        audit_categories.append([row['Report ID'], row['Case'], row['Quote'], who,
                                 row[f'{who} tags'], row['Common tags if confirmed'],
                                 row['Reason'], row['Date'], submitted['path'],
                                 'Personal proposal only; no common category decision or counting rule inferred.'])
assert len(audit_decisions) == 3 and len(audit_flags) == 24 and len(audit_categories) == 18
assert len(issues) == 329 and len({r['Record key'] for r in issues}) == 329
for old in audit_start:
    new = next(r for r in issues if r['Record key'] == old['Record key'])
    assert all(new[k] == value for k, value in old.items() if k not in ('Pathology flag', 'Normality flag'))
assert all(r['Exact quote'] in texts[r['Report ID']] for r in issues)

report_rows = []
for rid in sorted(texts):
    case = next(r['Case ID'] for r in coverage if r['Report ID'] == rid)
    for who in RATERS:
        cr = [r for r in coverage if r['Report ID'] == rid]
        core = [r for r in cr if r['Requirement'] != 'G03']
        g03 = next(r for r in cr if r['Requirement'] == 'G03')
        ir = [r for r in issues if r['Rater'] == who and r['Report ID'] == rid]
        error = sum(r['Current decision'] == 'Error' for r in ir)
        pending = sum(r['Current decision'] == 'Pending adjudication' for r in ir)
        completed = reviews[who][rid]['issue_review_complete'] == 'Yes'
        any_error = 'Yes' if error else ('No' if completed and not pending else 'Unknown')
        k = len(core)
        covered = sum(r[f'{who} decision'] == 'Covered' for r in core)
        joint = 'No' if error or covered < k or g03[f'{who} decision'] != 'Covered' else ('Yes' if completed and not pending else 'Unknown')
        report_rows.append([rid, case, who, k, covered, k-covered, covered/k, g03[f'{who} decision'],
                            error, pending, any_error, joint, 'Post-discussion individual record summary; not model-level final outcomes'])

# Review report-level differences without manufacturing a common union of
# issue records. Quote overlap alone never defines final error groups.
report_differences = []
residual_details = {
    'R25F5AA9361D9E14F': ('medial gastrocnemius (GAS)', 'rater3',
        'Rater1/rater2 separately record E01 for the unprovided medial-head designation. Rater3 records the pelvic-ROM issue but no disposition for this separate anatomical-specificity claim. Missing record is not Acceptable. Check both model inputs; GAS alone does not establish a supplied medial-head designation.', 'E01'),
    'R31D0B47CA4DF36CF': ('the mean envelope below threshold between the retained interval endpoints at 34% and 44%', 'rater2; rater3',
        'Rater1 records E03 for the entire inter-endpoint region claim. Neither other rater records this exact claim. Rater3\'s Acceptable normalization question is a different claim. Check displayed retained intervals against the minimum-duration rule; do not infer a disposition from silence.', 'E03'),
    'RAF417EE5FDC33A78': ('maintained above-threshold activity for 100% of the gait cycle, remaining above threshold continuously across the cycle boundary', 'rater1; rater3',
        'Rater2 records E03. The other raters retain the separate moderately-shorter-step Pending claim but do not record this continuity claim. Distinguish the allowed boundary-continuity statement from an asserted whole-cycle no-gap guarantee; do not decide from continuously alone.', 'E03'),
}
for rid in sorted(texts):
    rr = [r for r in report_rows if r[0] == rid]
    if len({r[10] for r in rr}) > 1 or len({r[8] for r in rr}) > 1:
        quote, raters_to_check, explanation, category = residual_details[rid]
        assert quote in texts[rid]
        line = texts[rid][:texts[rid].index(quote)].count('\n')+1
        report_differences.append([rid, rr[0][1], *[r[8] for r in rr], *[r[10] for r in rr],
                                  quote, line, raters_to_check, category, explanation,
                                  None, None, None, None])

book = Workbook()
book.remove(book.active)


def sheet(name, headers, rows):
    s = book.create_sheet(name)
    s.append(headers)
    for row in rows:
        s.append(row)
    s.freeze_panes = 'D2' if len(headers) > 3 else 'A2'
    s.auto_filter.ref = s.dimensions
    for cell in s[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='24476A')
    for row in s:
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            s.column_dimensions[cell.column_letter].width = 27 if len(str(cell.value or '')) < 100 else 60
            assert cell.data_type not in ['f', 'e']
            assert not re.search(r'[\u3400-\u9fff]', str(cell.value or ''))
    for n in range(2, s.max_row+1):
        s.row_dimensions[n].height = 60
    return s


summary = {who: dict(Counter(r['Current decision'] for r in issues if r['Rater'] == who)) for who in RATERS}
sheet('Read first', ['Topic', 'Meaning'], [
    ['Status', 'Complete blinded working consolidation, not a final consensus release or model comparison.'],
    ['Coverage', '552 unique report-requirement rows; all three post-discussion labels now match. 447 case requirements and 105 G03 rows remain separate. Original independent labels are preserved separately.'],
    ['Issues', f'{len(issues)} current per-rater records; prior records, discussion updates, five explicit residual responses and three explicit audit responses. Added records never infer a judgment from absence.'],
    ['Residual responses', 'All three residual claims now have matching Error judgments from all three raters. Source reasons and dates are preserved. Receipt and consolidation date: 2026-09-21. This does not change the 16 closed Pending claims or adopt a new global strict rule.'],
    ['Claim alignment', 'Source-span alignment for the 34 discussed claims is in Discussion crosswalk. No cross-rater issue union or final error-count denominator is inferred. Local issue IDs are rater-specific.'],
    ['Pending policy', 'Approved protocol section 9: Pending is not confirmed Error or confirmed Acceptable. Any-error is positive if a confirmed error exists, negative only after complete review without any confirmed or pending issue, otherwise unknown. Unknown flags enter planned-slot lower/upper bounds, not silent recoding.'],
    ['Coverage policy', 'Fixed case-requirement denominators; partial does not equal 0.5. Pending issue decisions alone do not make an otherwise complete coverage score missing.'],
    ['Control flags', 'The 24 requested annotations were supplied by their respective human reviewers and imported with reasons and dates in Audit flag updates. Other flags remain as supplied. A blank flag is not No. Final flag-level outcomes are not inferred here.'],
    ['Audit category proposals', 'Audit category proposals contains all 18 personal proposals, including four groups with different proposed sets. Issues current Categories retains the prior registered sets; consult both before category analysis. Proposals are not silently applied as common decisions, and tags never multiply issue counts.'],
    ['Independent analysis', 'Original coverage and issue records are included separately. Do not use post-feedback agreement as independent reliability.'],
    ['Source reasons and final acceptance', 'Some preserved source reasons describe earlier peer positions or conditional acceptance. For the five final Pending dispositions, Final disposition evidence records the later explicit acceptance; the old wording does not reopen the decision.'],
    ['Analysis compatibility', 'Existing final importer assumes two independent raters and a third adjudicator; it is not used for these three independent raters. No model mapping was opened by this builder.'],
    ['Remaining assembly review', f'{len(report_differences)} reports retain differences in per-rater confirmed-record counts or any-error flags outside the resolved 38-item scope. These require claim/group alignment before a single final error dataset can be released; not a request to repeat the completed five-item discussion.'],
])
ch = ['Report ID', 'Case ID', 'Requirement', 'Required wording', 'Components']
for who in RATERS:
    ch += [f'{who} decision', f'{who} status', f'{who} reason', f'{who} source']
ch += ['Matching post-discussion label']
sheet('Coverage current', ch, [[r.get(k) for k in ch] for r in coverage])
sheet('Coverage change log', ['Report ID', 'Requirement', 'Rater', 'Before label', 'Latest label'], coverage_changes)
ih = ['Record key', 'Rater', 'Report ID', 'Case ID', 'Local issue ID', 'Current decision', 'Categories', 'Exact quote', 'Locations', 'Reason', 'Final disposition evidence', 'Pathology flag', 'Normality flag', 'Discussion item', 'Preferred interpretation', 'Disposition basis', 'Source', 'Before decision', 'Before categories', 'Before quote', 'Original locations', 'Original source']
sheet('Issues current', ih, [[r.get(k) for k in ih] for r in issues])
sheet('Discussion crosswalk', ['Claim ID', 'Report ID', 'Rater', 'Record key', 'Action', 'Before decision', 'Disposition', 'Preferred interpretation', 'Categories', 'Source'], crosswalk)
clh = list(claim_rows[0])
sheet('Discussion dispositions', clh, [[r[k] for k in clh] for r in claim_rows])
sheet('Report summaries', ['Report ID', 'Case ID', 'Rater', 'Fixed K', 'Covered', 'Partial or not covered', 'Coverage fraction', 'G03', 'Confirmed records', 'Pending records', 'Any error', 'Joint outcome', 'Scope'], report_rows)
sheet('Residual record differences', ['Report ID', 'Case ID', 'rater1 confirmed records', 'rater2 confirmed records', 'rater3 confirmed records', 'rater1 any error', 'rater2 any error', 'rater3 any error', 'Exact claim to check', 'Report line', 'Raters with no explicit claim record', 'Existing category', 'Scope and next action', 'Returned disposition', 'Returned reason', 'Confirmed by', 'Confirmation date'], report_differences)
sheet('Residual return decisions', ['Report ID', 'Case ID', 'Rater', 'Disposition', 'Category', 'Exact report anchor', 'Report line', 'Returned reason', 'Source confirmation date', 'Source'], residual_returns)
sheet('Audit issue decisions', ['Record key', 'Rater', 'Report ID', 'Disposition', 'Category', 'Exact quote', 'Reason', 'Confirmation date', 'Source'], audit_decisions)
sheet('Audit flag updates', ['Record key', 'Rater', 'Report ID', 'Before pathology', 'Before normality', 'Returned pathology', 'Returned normality', 'Reason', 'Confirmation date', 'Source'], audit_flags)
sheet('Audit category proposals', ['Report ID', 'Case ID', 'Exact quote', 'Rater', 'Prior registered categories', 'Personal proposed categories', 'Reason', 'Confirmation date', 'Source', 'Status'], audit_categories)
for original_sheet in ['Coverage', 'Issues']:
    headers = list(baseline['rater1'][original_sheet].values)[0]
    rows = [[who, *[r.get(k) for k in headers]] for who in RATERS for r in records(baseline[who][original_sheet])]
    sheet('Independent '+original_sheet.lower(), ['Rater', *headers], rows)
sheet('Sources', ['Path', 'SHA-256'], list(hashes.items()))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in hashes.items())
OUT.mkdir(exist_ok=True)
target = OUT / 'Consolidated_ratings_working.xlsx'
if target.exists():
    prior_manifest = json.loads((OUT/'BUILD_RECORD.json').read_text())
    assert hashlib.sha256(target.read_bytes()).hexdigest() == prior_manifest['workbook_sha256'], 'Workbook changed since build; do not overwrite reviewer input.'
book.save(target)
check = load_workbook(target, read_only=True, data_only=True)
assert check['Coverage current'].max_row == 553
assert check['Independent coverage'].max_row == 1657
assert check['Independent issues'].max_row == 209
assert check['Issues current'].max_row == len(issues)+1
manifest = {'stage': 'Blinded working consolidation; not a signed final release', 'reports': 105,
            'participants': 35, 'coverage_rows': 552, 'coverage_labels_match_across_three': 552,
            'case_requirements': 447, 'g03_rows': 105, 'issue_records': len(issues),
            'discussion_claims': 34, 'discussion_decisions': dict(Counter(r['decision'] for r in claim_rows)),
            'per_rater_record_counts': summary, 'residual_report_differences': report_differences,
            'residual_responses_applied': len(residual_returns), 'residual_claims_aligned_error': 3,
            'residual_consolidation_date': '2026-09-21',
            'audit_issue_responses_applied': len(audit_decisions), 'audit_new_report_scoped_claims': 1,
            'audit_flag_records_updated': len(audit_flags), 'personal_category_proposals_preserved': len(audit_categories),
            'audit_category_proposals_applied_as_common_decisions': False,
            'model_mapping_read_by_builder': False, 'sources_unchanged': True,
            'workbook_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'source_hashes': hashes}
(OUT/'BUILD_RECORD.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='source_hashes'}, indent=2))
