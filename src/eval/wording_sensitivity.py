"""Post-freeze scenario arithmetic; no interpretation, voting or rating edits."""
from collections import Counter, defaultdict
from copy import deepcopy


def overlay_reports(frozen, decisions, *, pathology_overrides=None):
    """Replace explicit group labels in memory and retain every other outcome.

    The caller owns scenario definitions. An overlay on a shared frozen baseline
    is not a complete independent assessment by the named reviewer.
    Pathology overrides are explicit report-level True/False/None values; they
    cannot be inferred from error tags. Existing normality outcomes are retained.
    """
    groups = {g['group_id']: g for g in frozen['issue_groups']}
    if len(groups) != len(frozen['issue_groups']) or set(decisions) - groups.keys():
        raise ValueError('Duplicate or unknown issue group')
    legal = {'Error', 'Acceptable', 'Pending adjudication', 'Outside case-error scope'}
    if any(d not in legal for d in decisions.values()):
        raise ValueError('Invalid scenario decision')
    by_report = defaultdict(Counter)
    for gid, g in groups.items():
        label = decisions.get(gid, g['decision'])
        if label not in legal:
            raise ValueError('Invalid frozen decision')
        by_report[g['report_id']][label] += 1
    rows = deepcopy(frozen['reports'])
    reports = {r['report_id']: r for r in rows}
    if len(reports) != len(rows) or set(by_report) - reports.keys():
        raise ValueError('Duplicate or unknown report')
    for r in rows:
        counts = by_report[r['report_id']]
        errors, pending = counts['Error'], counts['Pending adjudication']
        r['confirmed_issue_count'], r['pending_issue_count'] = errors, pending
        r['any_error'] = True if errors else (
            False if r['available'] and r['issue_review_complete'] and not pending else None)
        complete = bool(r['available'] and not r['unknown_items'] and r['g03'] is not None
                        and r['issue_review_complete'] and not pending)
        r['joint_complete_review'] = complete
        fails = (errors or r['counts']['Partially covered'] or r['counts']['Not covered']
                 or (r['g03'] is not None and r['g03'] != 'Covered'))
        r['joint'] = (False if fails else True if complete else None) if r['available'] else None
    for rid, flag in (pathology_overrides or {}).items():
        if rid not in reports or reports[rid]['cohort'] != 'control':
            raise ValueError('Pathology override requires a known control report')
        if flag is not None and type(flag) is not bool:
            raise ValueError('Pathology flag must be True, False or None')
        if flag is True and not reports[rid]['confirmed_issue_count']:
            raise ValueError('A positive confirmed flag needs a confirmed in-scope error')
        reports[rid]['control_flags']['pathology'] = flag
    return rows
