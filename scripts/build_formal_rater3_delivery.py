#!/usr/bin/env python3
"""Prepare a third independent blank review using only frozen blinded assets.

Never read completed reviews or the model key. Keep the original two-rater
package, its integrity manifest and the approved scoring content unchanged.
"""
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import secrets
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eval.formal_rating import _workbook, spaced_order
from scripts.build_formal_rating_delivery import page, guide, sha, write_json

SOURCE = ROOT / 'data/rating_packets_formal_v1'
OUT = ROOT / 'docs/formal_study/rating_delivery_rater3_v1'

ORIENTATION = '''<header><nav><a href="START_HERE.html">Report list</a><a href="HOW_TO_REVIEW.html">Workbook instructions</a><a href="reading/RUBRIC.html">Full rubric</a><a href="reading/EXAMPLES.html">Approved teaching examples</a></nav><h1>Orientation for the sports medicine reviewer</h1><p>You are joining as the third independent reviewer at the scoring stage. You did not develop the criteria and are not being asked to endorse earlier decisions. Assess every report on its own evidence under the same frozen rules.</p></header>
<section><h2>What this study asks</h2><p>How faithfully do three language models describe supplied gait and surface-EMG findings, respect uncertainty, and avoid unsupported interpretations? There are 25 stroke cases and 10 healthy controls, each with three reports: 105 reports in total. This is a limited-evidence research interpretation task, not a test of autonomous diagnosis, treatment selection, or readiness for clinical deployment.</p><p>Your clinical expertise is important for interpreting what a statement actually claims. Judge whether that claim is supported by the information given to the model. A clinically plausible explanation is not necessarily established in this participant.</p><p>The reports are anonymized by source, not by participant group: stroke/control status and the analyzed side are intentional evidence. Do not try to identify models. Report any actual identity disclosure in Review; a guess based on style is not confirmed unblinding.</p></section>
<section><h2>Read these materials before scoring</h2><ol><li>Read this orientation and <a href="HOW_TO_REVIEW.html">How to review</a>.</li><li>Read the full <a href="reading/RUBRIC.html">rubric</a>, the <a href="ERROR_DEFINITIONS.html">nine error definitions</a>, and <a href="reading/EXAMPLES.html">all 42 teaching examples</a>. They are synthetic training material, not outcomes from these 105 reports.</li><li>Read the <a href="reading/CURRENT_REVIEW_SCOPE.html">current scope</a> and <a href="reading/RUBRIC_APPROVAL_STATUS.html">rubric approval status</a>. Historical draft labels and references to a five-case annex do not make this a new rubric-approval exercise. Use the 35-case requirements in your Coverage sheet, not the developmental five-case list.</li><li>Read the exact system instruction and case summary on each report page, then assess the report against its own requirements. Review the reference card and plots when needed.</li></ol><p>This orientation summarizes the supplied rules; it adds no scoring category, numerical tolerance, clinical cutoff or required report statement. If anything appears inconsistent, identify the location and ask the coordinator for a documented clarification. Do not silently invent a replacement rule.</p><p>Historical approval notes refer to earlier rubric-development decisions. They do not disclose formal report ratings. Other reviewers' completed ratings and disagreements are not included.</p></section>
<section><h2>The evidence the model actually received</h2><p>Each reading page contains the complete original report and the exact system and user text supplied to generate it. The model received those texts, not the expert plots, individual-stride curves or a full clinical assessment. The plots and reference card help you check the evidence; they must not create new mandatory findings unavailable in the text input.</p><p>Use the case-specific source statement: the stroke reference is pooled; the control comparison uses a leave-one-out reference that excludes that control. Pooled calibration percentiles are not automatically matched leave-one-out normal limits. Information not supplied to the model is not necessarily absent from the source dataset.</p></section>
<section><h2>Metric guide in clinical language</h2><table><tr><th>Term</th><th>Meaning and limits in this task</th></tr>
<tr><td>EMG envelope</td><td>A processed, averaged activity curve with relative amplitude. Its size does not measure muscle strength, force or absolute neural activation. An average does not establish stride-to-stride consistency. Follow the exact case normalization statement.</td></tr>
<tr><td>Detected interval / coverage</td><td>The averaged envelope exceeds 20% of its own peak; retained above-threshold runs must last at least 3% of the cycle by sample count. This is a signal-processing rule, not a clinical abnormality cutoff or proof of physiological onset, offset or continuous contraction. The 3% rule filters short above-threshold runs, not short below-threshold gaps. Rounded 100% coverage alone is not proof that every sample exceeds threshold.</td></tr>
<tr><td>Cycle position</td><td>Use the supplied initial-contact anchor and numerical percentages. An interval whose first percentage exceeds its last wraps across the cycle boundary. No individual toe-off or intermediate phase boundary is supplied, so do not infer stance/swing, push-off or clearance timing from a conventional percentage split. Healthy cycles pool initial-contact-aligned contributing strides, with the documentary qualification given in the input.</td></tr>
<tr><td>Maximum absolute z deviation</td><td>The largest standardized difference from the reference across the cycle. Its position is not necessarily the EMG amplitude peak. The accompanying above/below direction refers to the reference mean at that location, not a percentile boundary. The ordinary 2-SD abnormality rule is not valid for this maximum statistic.</td></tr>
<tr><td>CCI</td><td>A whole-cycle overlap index calculated from continuous normalized envelopes, including sub-threshold values. It is not the proportion of time two muscles are active, a force measurement or proof of pathological co-contraction. Within the supplied empirical range does not establish normal muscle function.</td></tr>
<tr><td>GVS / GPS-like / ROM</td><td>GVS summarizes a channel's waveform difference from the reference. GPS-like combines the available sagittal channel scores; it is not the validated full nine-variable GPS. Neither identifies the direction or phase of a waveform deviation. ROM is measured excursion, not by itself proof of clinical restriction.</td></tr>
<tr><td>Speed and step-length index</td><td>A speed-band label does not measure community independence or safety. Speed within the reference range does not establish matching. For the supplied paretic/non-paretic step-length index, a negative value means the paretic step is shorter. A near-zero index does not establish whole-gait symmetry. This index is not applicable to controls; general left/right symmetry is a different question.</td></tr></table><p>Muscle labels: GAS = gastrocnemius; RF = rectus femoris; VL = vastus lateralis; BF = biceps femoris; ST = semitendinosus; TA = tibialis anterior; ERS = erector spinae. Anatomical actions can be named, but the supplied intervals do not establish their gait-phase function.</p></section>
<section><h2>What to score, and what to keep separate</h2><ul><li><strong>Coverage:</strong> did the report convey every required substantive component? AND needs all components; OR needs one complete permitted route. Do not demand exact wording or every optional number.</li><li><strong>G03:</strong> one row per report asks for both a meaningful reference-comparability limitation and its inference limitation. Age and speed are not mandatory keywords. For controls, the comparison cannot establish disease or overall normality.</li><li><strong>Errors:</strong> an optional assertion can still be wrong. A correct required statement can earn coverage even if an unretracted contradiction elsewhere also needs an issue row.</li><li><strong>Clinical questions:</strong> asking whether a possible mechanism exists is different from presupposing that the participant has it. Apply the contextual rules, not a keyword ban.</li><li><strong>Uncertainty:</strong> a supported inability to classify is not an error. Use Pending for unresolved interpretation; Cannot assess is for material problems, not clinical caution.</li><li><strong>Duplicates:</strong> one repeated equivalent claim is one issue group. Add its locations and applicable E tags rather than counting each repetition or tag as another error.</li><li><strong>Controls:</strong> group membership alone proves neither normal function nor absence of disease. Attach pathology/normality flags only under the approved rules.</li></ul><p>The workbook has 447 case-specific coverage rows plus 105 G03 rows. Do not turn Partially covered into 0.5, create severity weights, or calculate a personal overall model score. Complete the separate format and identity-disclosure fields.</p></section>
<section><h2>How to work independently</h2><p>Follow the fixed reading order across sessions. Do not compare the three reports for a case side by side. Do not request other reviewers' scores or disagreement lists, and do not use another language model to generate your judgments. Take breaks as needed; there is no requirement to complete the packet in one sitting.</p><p>If a rule needs clarification, send the coordinator the rule ID and your question without seeking a preferred score. Preserve your original judgment and flag unresolved cases. Any substantive change to the frozen criteria must be documented and applied consistently; it is not a private adjustment for this reviewer.</p><p>Copy quotations from the original report text file. Preserve punctuation and use one exact continuous passage in exact_quote. Put other locations and explanations in their own fields; do not insert ellipses to join passages.</p><p>Before starting, complete <a href="REVIEWER_BACKGROUND.md">Reviewer background</a> in a separate saved copy. State your actual experience; nothing has been prefilled as a credential, conflict declaration or signature. Familiarity with gait/EMG interpretation should be described rather than inferred from specialty alone.</p></section>
<section><h2>Completion and return</h2><p>After completing all reports, enter your name, ISO date as text, and Yes in the workbook's completion fields. Documented Pending items are allowed. Return <strong>Independent_ratings_rater3_completed.xlsx</strong> and <strong>Reviewer_background_rater3_completed.md</strong>. Keep your judgments private until all independent submissions are preserved and the coordinator opens the discussion stage. Your scores will not be substituted silently for another reviewer's scores, and your judgment is not automatically the deciding vote.</p></section>'''

BACKGROUND = '''# Reviewer background: rater3

Complete a separate copy named Reviewer_background_rater3_completed.md.
These fields describe the reviewer; they are not report scores or a signature.
Do not replace blank fields with assumed credentials or confirmations.

- Reviewer name:
- Professional role and specialty:
- Institution / department:
- Years of relevant clinical practice:
- Experience interpreting gait kinematics and surface EMG:
- Relevant research or scoring experience:
- Prior involvement with this dataset, reports, or study (describe any):
- Access to other formal ratings, model identities, or disagreement discussions (describe any):
- Relevant conflicts of interest (state None only if applicable):
- Orientation, full rubric, error definitions and examples read (Yes only after reading):
- Questions needing clarification before scoring:
- Date (YYYY-MM-DD):
'''


def multi_reviewer_guide(text):
    replacements = {
        'with the other reviewer until both independent reviews are locked': 'with any other reviewer until all independent reviews are locked',
        'not agreement with the other reviewer': 'not agreement with other reviewers',
        "the other reviewer's ratings before both independent submissions are locked": "other reviewers' ratings before all independent submissions are locked",
    }
    for old, new in replacements.items():
        assert old in text, old
        text = text.replace(old, new)
    return text


def error_definitions(categories):
    content = '<nav><a href="ORIENTATION.html">Orientation</a><a href="reading/RUBRIC.html">Full rubric</a></nav><h1>Error definitions</h1><p>Exact category wording from the approved rubric, presented for reading. Apply the contextual boundaries in the full rubric.</p>'
    for category in categories:
        assert set(category) == {'id', 'name', 'scope', 'boundary'}
        content += '<section><h2>' + escape(category['id'] + ': ' + category['name']) + '</h2><p><strong>What this category covers:</strong> ' + escape(category['scope']) + '</p><p><strong>How to apply it:</strong> ' + escape(category['boundary']) + '</p></section>'
    return page('Error definitions', content)


def build():
    if OUT.exists():
        raise FileExistsError('Do not overwrite an existing third-reviewer packet')
    source = SOURCE / 'raters/rater1'
    integrity = json.loads((SOURCE / 'private/package_integrity.json').read_text())
    prefix = 'raters/rater1/'
    checked = {}
    for name, expected in integrity['files_sha256'].items():
        if name.startswith(prefix):
            assert sha(SOURCE / name) == expected, name
            checked[name] = expected
    public = json.loads((source / 'reports.json').read_text())
    previous_orders = [public['order'], json.loads((SOURCE / 'raters/rater2/reports.json').read_text())['order']]
    grouped = defaultdict(list)
    for rid, row in sorted(public['reports'].items()):
        assert set(row) == {'case_id', 'material_status'}
        grouped[row['case_id']].append(rid)
    seed = secrets.randbits(128)
    order = spaced_order(grouped, seed)
    assert order not in previous_orders
    public = {'order': order, 'reports': dict(sorted(public['reports'].items()))}
    OUT.mkdir()
    dest = OUT / 'rater3'
    dest.mkdir()
    # Copy only explicit frozen reports/materials, never a returned workbook.
    shutil.copytree(source / 'reports', dest / 'reports')
    shutil.copytree(source / 'materials', dest / 'materials')
    write_json(dest / 'reports.json', public)
    _workbook(dest / 'Independent_ratings.xlsx', 'rater3', order, public['reports'], integrity['requirements'])
    from openpyxl import load_workbook
    book = load_workbook(dest / 'Independent_ratings.xlsx')
    book['Instructions']['B2'] = 'Use only this rater folder. Do not consult other reviewers until all independent reviews are locked.'
    book.save(dest / 'Independent_ratings.xlsx')
    coverage = defaultdict(list)
    for n, row in enumerate(book['Coverage'].iter_rows(min_row=2, values_only=True), 2):
        coverage[row[0]].append((n, row))
    book.close()
    (dest / 'README.md').write_text('# Third independent review\n\nExtract the whole ZIP and open START_HERE.html. Read ORIENTATION.html before scoring. Record judgments only in a separate copy of Independent_ratings.xlsx. All scores and confirmations are blank. Use the fixed reading order and the frozen requirements. Do not consult other reviewers until all independent submissions are locked.\n')
    (dest / 'ORIENTATION.html').write_text(page('Sports medicine reviewer orientation', ORIENTATION))
    (dest / 'REVIEWER_BACKGROUND.md').write_text(BACKGROUND)
    rubric = json.loads((dest / 'materials/rubric.json').read_text())
    (dest / 'HOW_TO_REVIEW.html').write_text(multi_reviewer_guide(guide('rater3', rubric['error_categories'])))
    (dest / 'ERROR_DEFINITIONS.html').write_text(error_definitions(rubric['error_categories']))
    reading = dest / 'reading'
    reading.mkdir()
    for name in ('RUBRIC', 'EXAMPLES', 'RUBRIC_APPROVAL_STATUS', 'CURRENT_REVIEW_SCOPE'):
        raw = (dest / 'materials' / f'{name}.md').read_text()
        content = '<nav><a href="../START_HERE.html">Report list</a><a href="../ORIENTATION.html">Orientation</a><a href="../HOW_TO_REVIEW.html">How to review</a></nav><section><h1>' + escape(name.replace('_', ' ').title()) + '</h1><p>Verbatim approved source document. Historical draft/five-case wording is explained by the approval status and current scope. Apply the current workbook requirements.</p><pre id="document-text">' + escape(raw) + '</pre></section>'
        (reading / f'{name}.html').write_text(page(name, content))
    rows = []
    for pos, rid in enumerate(order, 1):
        case = public['reports'][rid]['case_id']
        prev = f'<a href="{order[pos-2]}.html">Previous report</a>' if pos > 1 else ''
        nxt = f'<a href="{order[pos]}.html">Next report</a>' if pos < len(order) else ''
        requirements = ''.join('<tr><td>' + str(n) + '</td><td>' + escape(row[2]) + '</td><td>' + escape(row[3]) + '</td><td>' + escape(row[4]) + '</td></tr>' for n, row in coverage[rid])
        text = (dest / 'reports' / f'{rid}.txt').read_text()
        asset = f'../materials/{case}/'
        content = f'''<header><nav><a href="../START_HERE.html">Report list</a><a href="../ORIENTATION.html">Orientation</a><a href="../HOW_TO_REVIEW.html">Filling instructions</a><a href="../Independent_ratings.xlsx">Workbook</a>{prev}{nxt}</nav><p>rater3 / Report {pos} of 105 / Review spreadsheet row {pos+1}</p><h1>{rid}</h1><p>Case: <strong>{case}</strong></p><p class="notice">Read independently and enter judgments in the workbook. These pages do not save ratings.</p></header><section><h2>Report: exact saved text</h2><p><a href="../reports/{rid}.txt">Original report text for exact quotations</a></p><pre id="report-text">{escape(text)}</pre></section><section><h2>Requirements for this report</h2><p>Fill these Coverage rows. G03 applies once. No judgments are prefilled.</p><table><tr><th>Excel row</th><th>ID</th><th>Required content</th><th>Components / optional content</th></tr>{requirements}</table></section>'''
        for key, filename, label in [('system-text', 'model_system_prompt.txt', 'Exact model input: system instruction'), ('user-text', 'model_user_prompt.txt', 'Exact model input: case summary'), ('reference-text', 'reference_card.md', 'Reference context for expert review')]:
            raw = (dest / 'materials' / case / filename).read_text()
            content += f'<details><summary>{label}</summary><a href="{asset}{filename}">Original file</a><pre id="{key}">{escape(raw)}</pre></details>'
        content += f'''<details><summary>EMG and kinematic curves</summary><p>Supplementary expert evidence. Only the saved text inputs were given to the model; curve-only observations are not additional required content.</p><h2>EMG</h2><a href="{asset}curves_emg.png"><img src="{asset}curves_emg.png" alt="EMG curves for {case}" loading="lazy"></a><h2>Kinematics</h2><a href="{asset}curves_kinematics.png"><img src="{asset}curves_kinematics.png" alt="Kinematic curves for {case}" loading="lazy"></a></details><section><nav>{prev}<a href="../START_HERE.html">Report list</a>{nxt}</nav></section>'''
        (reading / f'{rid}.html').write_text(page(rid + ' - independent review', content))
        rows.append(f'<tr><td>{pos}</td><td><a href="reading/{rid}.html">{rid}</a></td><td>{case}</td><td>{pos+1}</td></tr>')
    content = '''<header><h1>Third independent review: rater3</h1><p>105 anonymous reports / 35 cases / 552 coverage judgments.</p><nav><a href="ORIENTATION.html">Start with the orientation</a><a href="HOW_TO_REVIEW.html">Workbook instructions</a><a href="Independent_ratings.xlsx">Blank workbook</a><a href="reading/RUBRIC.html">Full rubric</a><a href="ERROR_DEFINITIONS.html">Error definitions</a><a href="reading/EXAMPLES.html">Teaching examples</a><a href="REVIEWER_BACKGROUND.md">Reviewer background</a></nav></header><section><h2>Before you start</h2><ol><li>Extract the complete ZIP. Read the orientation, rubric, definitions and examples.</li><li>Save a separate workbook named Independent_ratings_rater3_completed.xlsx.</li><li>Follow the fixed order below across sessions; the workbook has the same order.</li><li>For each report, complete Coverage, record Issues, then complete its Review row.</li></ol><p class="notice">Only the workbook saves ratings. No other reviewer's formal judgments or model identity key are included. Keep your judgments independent until all independent submissions are locked.</p><p>This is scoring under approved criteria, not a new criteria-approval exercise. Current case requirements are in Coverage; the historical five-case annex is not the formal sample list.</p></section><section><h2>Fixed reading order</h2><p>Use browser Find to resume at a report ID. Do not sort by case or compare same-case reports side by side.</p><table><tr><th>Position</th><th>Report and evidence</th><th>Case</th><th>Review row</th></tr>''' + ''.join(rows) + '</table></section>'
    (dest / 'START_HERE.html').write_text(page('rater3 - start here', content))
    private = OUT / 'private'
    private.mkdir(mode=0o700)
    write_json(private / 'order_provenance.json', {'seed': seed, 'algorithm': 'src.eval.formal_rating.spaced_order', 'input': 'Opaque report IDs grouped by case, sorted before randomization', 'order': order})
    archive = OUT / 'Formal_review_rater3.zip'
    now = datetime.now(timezone.utc)
    timestamp = (now.year, now.month, now.day, 0, 0, 0)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for file in sorted(dest.rglob('*')):
            if file.is_file():
                info = zipfile.ZipInfo(str(Path('rater3') / file.relative_to(dest)), date_time=timestamp)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, file.read_bytes())
    write_json(OUT / 'BUILD_RECORD.json', {'created_utc': now.isoformat(), 'source_files_verified': checked, 'source_integrity_sha256': sha(SOURCE / 'private/package_integrity.json'), 'source_order_metadata_sha256': {r: sha(SOURCE / 'raters' / r / 'reports.json') for r in ('rater1', 'rater2')}, 'reports': 105, 'cases': 35, 'coverage_rows': 552, 'case_specific_rows': 447, 'g03_rows': 105, 'private_model_key_read': False, 'completed_reviews_read_by_builder': False, 'source_files_modified': False, 'model_calls': 0, 'human_judgments_created': False, 'delivery_sent': False, 'script_sha256': sha(Path(__file__)), 'zip_sha256': sha(archive), 'packet_files_sha256': {str(p.relative_to(dest)): sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}})
    print(json.dumps({'packet': str(archive), 'sha256': sha(archive), 'reports': 105, 'coverage_rows': 552, 'all_judgments_blank': True}, indent=2))


if __name__ == '__main__':
    build()
