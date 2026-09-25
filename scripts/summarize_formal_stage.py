#!/usr/bin/env python3
"""Summarize technical outcomes without rating clinical quality or rerunning models."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.formal_generation import IntegrityError, digest, read_journal, write_once
from src.llm.formal_stages import PACKAGE, FULL_PLAN, LIVE_ROOT
from src.llm.formal_batch import TERMINAL


def summarize(number):
    plan = json.loads(FULL_PLAN.read_text())
    stage = json.loads((PACKAGE / f"stage_{number:02d}/plan.json").read_text())
    envelope = json.loads((LIVE_ROOT / 'run_manifest.json').read_text())
    if envelope['plan_sha256'] != digest(plan) or stage['full_plan_sha256'] != digest(plan):
        raise IntegrityError('Plan identity changed')
    records, head = read_journal(LIVE_ROOT)
    rows, texts = [], {}
    for task in plan['tasks']:
        slot = task['slot_id']
        if slot not in stage['slot_ids']:
            continue
        selected = [r for r in records if r['slot_id'] == slot]
        starts = [r for r in selected if r['kind'] == 'attempt_started']
        if any(r['task_sha256'] != digest(task) for r in starts):
            raise IntegrityError('Task identity changed')
        decisions = [r for r in selected if r['kind'] in {'attempt_resolved', 'recovery'}]
        final = decisions[-1] if decisions else {}
        events = [r['event'] for r in selected if r['kind'] == 'stream_event']
        metadata = next((e['metadata'] for e in reversed(events) if e.get('metadata')), {})
        terminal = bool(starts and final.get('state') in TERMINAL and final.get('attempt') == starts[-1]['attempt'])
        text = final.get('text', '') if terminal else ''
        if final.get('state') == 'captured':
            captured = ''.join(r['event'].get('text', '') for r in selected if r['kind'] == 'stream_event' and r['attempt'] == final['attempt'] and r['event']['type'] == 'text')
            if captured != text:
                raise IntegrityError('Captured report differs from stream evidence')
            texts[slot] = text
        finish = metadata.get('finish_reason')
        refusal = finish == 'refusal' or any(e.get('raw', {}).get('delta', {}).get('stop_details', {}).get('type') == 'refusal' for e in events)
        usage = metadata.get('usage', {})
        row = {'slot_id': slot, 'case_id': task['case_id'], 'provider': task['provider'],
               'state': final.get('state', 'in_progress' if starts else 'not_started'),
               'terminal': terminal, 'attempts': len(starts),
               'dispatches': sum(e['type'] == 'dispatch_requested' for e in events),
               'words': len(text.split()), 'finish_reason': finish,
               'refusal': refusal, 'truncation': finish in {'MAX_TOKENS', 'max_tokens', 'length'},
               'stream_completed': any(e['type'] == 'completed' for e in events),
               'requested_model': task['model'], 'response_model': metadata.get('response_model'),
               'response_id': metadata.get('response_id'),
               'input_tokens': usage.get('input_tokens', usage.get('prompt_tokens', usage.get('prompt_token_count'))),
               'usage': usage,
               'first_attempt_timestamp': starts[0]['time'] if starts else None,
               'last_event_timestamp': next((r['time'] for r in reversed(selected) if 'time' in r), None),
               'report_sha256': hashlib.sha256(text.encode()).hexdigest() if slot in texts else None}
        rows.append(row)
    selected_starts = [r for r in records if r['kind'] == 'attempt_started' and r['slot_id'] in stage['slot_ids']]
    return {'stage_number': number, 'planned_slots': len(rows),
            'completed_slots': sum(r['terminal'] for r in rows), 'captured_reports': len(texts),
            'refusals': sum(r['refusal'] for r in rows), 'truncations': sum(r['truncation'] for r in rows),
            'dispatches': sum(r['dispatches'] for r in rows),
            'retry_attempts': sum(max(0, r['attempts'] - 1) for r in rows),
            'stage_reservation_consumed_usd': round(sum(plan['reservation_usd_per_attempt'][r['provider']] for r in selected_starts), 6),
            'journal_head': head, 'full_plan_sha256': digest(plan), 'stage_sha256': digest(stage),
            'clinical_quality_assessed': False, 'rows': rows}, texts


def save(number, result, texts):
    if result['completed_slots'] != result['planned_slots']:
        raise IntegrityError('Stage is not terminal; do not publish a completed-stage result')
    folder = PACKAGE / f'stage_{number:02d}'
    private = LIVE_ROOT / 'reports_unblinded_research_only'
    private.mkdir(exist_ok=True)
    for slot, text in texts.items():
        path = private / (slot + '.md')
        if path.exists():
            if path.read_bytes() != text.encode():
                raise IntegrityError('Existing report bytes differ')
        else:
            with path.open('xb') as handle:
                handle.write(text.encode())
    target = folder / 'RESULTS.json'
    if target.exists():
        if json.loads(target.read_text()) != result:
            raise IntegrityError('Existing result identity changed')
        return
    write_once(target, result)
    fields = ['slot_id', 'case_id', 'provider', 'state', 'attempts', 'dispatches', 'words', 'finish_reason', 'refusal', 'truncation', 'stream_completed', 'requested_model', 'response_model', 'response_id', 'input_tokens', 'usage', 'first_attempt_timestamp', 'last_event_timestamp', 'report_sha256']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for row in result['rows']:
        writer.writerow({**row, 'usage': json.dumps(row['usage'], sort_keys=True)})
    (folder / 'technical_outcomes.csv').write_text(stream.getvalue())
    providers = []
    for provider in ('anthropic', 'openai', 'gemini'):
        rows = [r for r in result['rows'] if r['provider'] == provider]
        providers.append(f"| {provider} | {len(rows)} | {sum(r['state'] == 'captured' for r in rows)} | {sum(r['refusal'] for r in rows)} | {sum(r['truncation'] for r in rows)} |")
    (folder / 'RESULTS.md').write_text(f'''# Formal stage {number}: technical completion summary

All {result['planned_slots']} authorized slots are terminal. Captured reports: {result['captured_reports']}. Requests dispatched: {result['dispatches']}. Retry attempts: {result['retry_attempts']}.

| Provider | Slots | Captured text | Refusals | Token-limit finishes |
| --- | --- | --- | --- | --- |
''' + '\n'.join(providers) + f'''

These are technical outcomes, not clinical-quality scores. Captured text includes partial, refused or truncated text if present. Review `technical_outcomes.csv` for completion flags and `RESULTS.json` for metadata. No report was replaced for content quality. All outcomes are retained for the formal study.

The cumulative stage reservation consumed is ${result['stage_reservation_consumed_usd']:.2f} under the registered conservative allowance. This is not actual invoiced expenditure. Usage is retained per response; no new pricing or account-balance claim is made.

Verbatim reports are saved under the repository path `data/reports_formal_v1/reports_unblinded_research_only/`. These files and this provider-labelled summary are researcher-only and must not be sent as blinded rating packets. Raw stream and request evidence remain in the parent ledger directory. Report bytes are verified against captured stream text before export.

The stage boundary has been reached. Subsequent stages are not automatically authorized or started. Do not change configurations based on preliminary apparent model quality, and do not treat a batch as an independent statistical replicate. Final review and analysis retain the predeclared participant-level protocol.
''')
    case_ids = list(dict.fromkeys(r['case_id'] for r in result['rows']))
    index = ['# Researcher-only report index', '', 'These links reveal provider identity. Do not send this index or these filenames as blinded rater materials. The texts are verbatim formal outputs; technical completion does not establish clinical accuracy.', '', '| Case | Claude | GPT | Gemini |', '| --- | --- | --- | --- |']
    for case_id in case_ids:
        cells = []
        for provider in ('anthropic', 'openai', 'gemini'):
            row = next(r for r in result['rows'] if r['case_id'] == case_id and r['provider'] == provider)
            if row['slot_id'] in texts:
                relative = '../../../../data/reports_formal_v1/reports_unblinded_research_only/' + row['slot_id'] + '.md'
                cells.append(f"[Report ({row['words']} words)]({relative})")
            else:
                cells.append('No report: ' + row['state'])
        index.append('| ' + case_id + ' | ' + ' | '.join(cells) + ' |')
    (folder / 'REPORT_INDEX.md').write_text('\n'.join(index) + '\n')
    write_once(folder / 'results_manifest.json', {'journal_head': result['journal_head'], 'file_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=int, required=True, choices=(1, 2, 3))
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    result, texts = summarize(args.stage)
    if args.save:
        save(args.stage, result, texts)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
