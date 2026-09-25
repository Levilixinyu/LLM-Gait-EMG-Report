"""Create an English manuscript draft from hash-verified analysis outputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/formal_study/manuscript_v1'
PRIVATE = 'data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/'
NAMES = {'anthropic': 'Claude Opus 5', 'openai': 'GPT-6-astra', 'gemini': 'Gemini 3.1 Pro preview'}
MODELS = tuple(NAMES)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def md_table(rows):
    headers = list(rows[0])
    return '| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join('---' for _ in headers) + ' |\n' + ''.join(
        '| ' + ' | '.join(str(row[h]) for h in headers) + ' |\n' for row in rows)


def interval(values, scale=100, digits=1):
    return 'Unavailable' if values is None else f'{values[0]*scale:.{digits}f} to {values[1]*scale:.{digits}f}'


def reading_html(markdown):
    """Render the limited headings, paragraphs, tables and lists in this draft."""
    def inline(s):
        s = html.escape(s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    blocks = []
    for block in markdown.strip().split('\n\n'):
        lines = block.splitlines()
        if all(line.startswith('|') for line in lines):
            cells = [[c.strip() for c in line.strip('|').split('|')] for line in lines]
            blocks.append('<div class="table"><table><thead><tr>' + ''.join('<th>'+inline(c)+'</th>' for c in cells[0]) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in cells[2:]) + '</tbody></table></div>')
        elif lines[0].startswith('#'):
            n = len(lines[0]) - len(lines[0].lstrip('#'))
            blocks.append(f'<h{n}>' + inline(lines[0][n:].strip()) + f'</h{n}>')
        elif all(line.startswith('- ') for line in lines):
            blocks.append('<ul>'+''.join('<li>'+inline(line[2:])+'</li>' for line in lines)+'</ul>')
        else:
            blocks.append('<p>'+inline(' '.join(lines))+'</p>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gait report evaluation: manuscript draft</title><style>body{font:17px/1.65 Georgia,serif;color:#182c39;margin:0;background:#f4f6f8}main{max-width:1100px;margin:24px auto;padding:38px;background:white}h1,h2,h3{font-family:system-ui,sans-serif;line-height:1.3}h1{font-size:30px}h2{margin-top:40px}table{border-collapse:collapse;font:14px/1.45 system-ui,sans-serif;width:100%}th,td{border:1px solid #cbd5dc;padding:9px;text-align:left}th{background:#edf3f7}.table{overflow:auto}a{color:#075985}code{font-size:.9em}@media print{body{background:white}main{padding:0;margin:0;max-width:none}h2,h3{break-after:avoid}tr{break-inside:avoid}}</style><main>' + '\n'.join(blocks) + '</main></html>\n'


def main():
    sources = {}
    def read(name):
        raw = (ROOT / name).read_bytes()
        sources[name] = sha(raw)
        return raw
    def js(name):
        return json.loads(read(name))
    build = js(PRIVATE + 'ANALYSIS_BUILD_RECORD.json')
    def registered(name):
        data = js(name)
        assert sources[name] == build['output_sha256'][name], name
        return data
    final = registered(PRIVATE + 'final_outcomes.json')
    independent = registered(PRIVATE + 'independent_sensitivity.json')
    frozen = js('docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json')
    assert sources['docs/formal_study/analysis_freeze_v1/BLINDED_OUTCOMES.json'] == build['frozen_dataset_sha256']
    agreement_record = js('docs/formal_study/three_rater_analysis_v1/AGREEMENT_BUILD_RECORD.json')
    agreement = js('docs/formal_study/three_rater_analysis_v1/INDEPENDENT_AGREEMENT.json')
    assert sources['docs/formal_study/three_rater_analysis_v1/INDEPENDENT_AGREEMENT.json'] == agreement_record['output_sha256']['INDEPENDENT_AGREEMENT.json']
    sensitivity_record = js('docs/formal_study/wording_sensitivity_v1/BUILD_RECORD.json')
    sensitivity_path = 'data/rating_packets_formal_v1/private/wording_sensitivity_v1/ANALYSIS.json'
    sensitivity = js(sensitivity_path)
    assert sources[sensitivity_path] == sensitivity_record['output_sha256'][sensitivity_path]
    freeze_record = js('docs/formal_study/analysis_freeze_v1/FREEZE_RECORD.json')
    unblinding = js(PRIVATE + 'UNBLINDING_RECORD.json')
    mapping_path = PRIVATE + 'mapping_snapshot.json'
    mapping = js(mapping_path)['mapping']
    assert sources[mapping_path] == build['source_sha256'][mapping_path]
    assert freeze_record['dataset_sha256'] == build['frozen_dataset_sha256']
    completion = js('docs/formal_study/formal_stages_v1/GENERATION_COMPLETION.json')
    plan = js('docs/formal_study/formal_execution_v2_candidate/plan.json')
    # The execution ledger binds canonical JSON, while source provenance uses file bytes.
    canonical_plan_hash = sha(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode())
    assert canonical_plan_hash == completion['full_plan_sha256']
    config = js('docs/formal_study/formal_execution_v2_candidate/provider_configuration.json')
    for task in plan['tasks']:
        provider = next(p for p in config['providers'] if p['provider'] == task['provider'])
        assert task['model'] == provider['model'] and task['parameters'] == provider['parameters']
    participants = list(csv.DictReader(io.StringIO(read('docs/formal_study/control_supplement_v2/selected_study_cases.csv').decode())))
    participant_keys = {r['participant_key']+'_'+r['side'] for r in participants}
    assert participant_keys == set(frozen['roster']) and len(participants) == 35
    for name in (
        'docs/formal_study/REVIEWER_BACKGROUND_CONFIRMATION.json',
        'docs/formal_study/execution_analysis_v3_draft/PROTOCOL.md',
        'docs/formal_study/execution_analysis_v1_draft/exposure_confirmation.json',
        'docs/formal_study/rating_delivery_rater3_v1/REVIEWER_ADDITION_RECORD.md',
        'docs/formal_study/three_rater_analysis_v1/ANALYSIS_ADDENDUM_DRAFT.md',
        'docs/formal_study/three_rater_review_v1/personal_rechecks/RECHECK_INSTRUCTIONS.md',
        'docs/formal_study/three_rater_analysis_v1/SEMANTIC_FLAG_CONFIRMATION.json',
        'docs/formal_study/wording_boundary_confirmation_v1/return_review/RETURN_CHECK.json',
        'docs/formal_study/wording_boundary_confirmation_v1/return_review/RATER2_RATIONALE_CORRECTION.json',
        'docs/formal_study/sample_eligibility_v1/README.md',
        'src/features/emg_signal.py', 'src/features/kinematic.py',
        'scripts/build_manuscript_draft.py'):
        read(name)

    stage_rows = []
    for n in (1, 2, 3):
        name = f'docs/formal_study/formal_stages_v1/stage_0{n}/RESULTS.json'
        d = js(name)
        assert sources[name] == completion['stage_result_sha256'][f'stage_0{n}/RESULTS.json']
        stage_rows += d['rows']
    assert len(stage_rows) == 105 and len({r['slot_id'] for r in stage_rows}) == 105
    generated_start = datetime.fromtimestamp(min(r['first_attempt_timestamp'] for r in stage_rows), timezone.utc).isoformat()
    generated_end = datetime.fromtimestamp(max(r['last_event_timestamp'] for r in stage_rows), timezone.utc).isoformat()

    tables = {}
    participant_rows = []
    for group in ('stroke', 'control'):
        rows = [r for r in participants if r['group'] == group]
        age = np.array([float(r['age_years']) for r in rows])
        speed = np.array([float(r['published_bilateral_speed_m_s']) for r in rows])
        def quantile_text(values, decimals):
            q = np.quantile(values, [.25, .5, .75], method='linear')
            return f'{q[1]:.{decimals}f} ({q[0]:.{decimals}f}-{q[2]:.{decimals}f})'
        participant_rows.append({'Cohort': group.capitalize(), 'Participants': len(rows), 'Reports': 3*len(rows),
            'Age, median (IQR), years': quantile_text(age, 1),
            'Published bilateral speed, median (IQR), m/s': quantile_text(speed, 3),
            'Published speed below 0.80 m/s': int(sum(speed < .8))})
    tables['T1 Sample'] = participant_rows
    model_rows = []
    for model in MODELS:
        p = next(p for p in config['providers'] if p['provider'] == model)
        model_rows.append({'Model identifier': p['model'], 'Recorded API route': p['api_route'],
            'Recorded SDK': p['sdk_package']+' '+plan['sdk_versions'][p['sdk_package']],
            'Reasoning setting': json.dumps({k:v for k,v in p['parameters'].items() if k in ('thinking','output_config','reasoning_effort','thinking_config')}),
            'Output-token allowance': 16000})
    tables['S1 Model configuration'] = model_rows
    main_rows, joint_rows, controls = [], [], []
    for cohort in ('stroke', 'control'):
        for model in MODELS:
            s = final['estimates']['cohort_summaries'][cohort]['by_model'][model]
            e = s['any_error']; j = s['joint']
            main_rows.append({'Cohort': cohort.capitalize(), 'Model': NAMES[model],
                'Mean full coverage, %': f"{s['available_case_coverage_mean']*100:.1f}",
                'Error reports / evaluable': f"{e['events']}/{e['evaluable']}", 'Unknown': e['unknown'],
                'Exact 95% CI, %': interval(e['exact_95_interval']),
                'All-planned bounds, %': interval(e['all_planned_bounds']),
                'Confirmed groups': sum(s['confirmed_issue_counts'])})
            joint_rows.append({'Cohort': cohort.capitalize(), 'Model': NAMES[model],
                'Success / complete reviews': f"{j['events']}/{j['evaluable']}", 'Unknown status': j['unknown'],
                'Excluded from point estimate': j['planned'] - j['evaluable'],
                'Exact 95% CI, %': interval(j['exact_95_interval']), 'All-planned bounds, %': interval(j['all_planned_bounds'])})
            for flag, f in s['control_flags'].items():
                controls.append({'Model': NAMES[model], 'Flag': flag, 'Frozen events / evaluable': f"{f['events']}/{f['evaluable']}",
                    'Unknown': f['unknown'], 'Exact 95% CI, %': interval(f['exact_95_interval']),
                    'Later review': 'Disputed: Yes / No / Yes; unknown scenario 0/9 with 1 unknown' if model == 'gemini' and flag == 'pathology' else 'Unchanged'})
    tables['T2 Frozen outcomes'] = main_rows
    tables['S2 Joint outcome'] = joint_rows
    tables['T4 Control flags'] = controls
    contrast_rows = []
    for key, v in final['estimates']['primary_stroke']['contrasts'].items():
        a, b = key.split(' - ')
        contrast_rows.append({'Contrast': NAMES[a]+' minus '+NAMES[b],
            'Difference, percentage points': f"{v['mean_difference_percentage_points']:.1f}",
            'Descriptive 95% BCa': interval(v['descriptive_95']['interval'], scale=1),
            'Family-adjusted 98.3333% BCa': interval(v['family_adjusted_98_3333']['interval'], scale=1)})
    tables['T3 Paired coverage'] = contrast_rows
    agreement_rows = []
    for pair, p in agreement['pairs'].items():
        for cohort, domains in p['cohorts'].items():
            for domain, d in domains.items():
                n=d['jointly_assessable']; excluded=d.get('excluded_unknown_or_pending',d.get('excluded_incomplete_or_unknown'))
                agreement_rows.append({'Pair': pair.replace('__',' / '), 'Cohort': cohort.capitalize(), 'Domain': domain,
                    'Assessed / planned': f'{n}/{n+excluded}', 'Excluded': excluded,
                    'Raw agreement, %': f"{d['raw_agreement']*100:.1f}",
                    'Unweighted kappa': 'Undefined' if d['unweighted_kappa'] is None else f"{d['unweighted_kappa']:.3f}"})
    tables['T5 Independent agreement'] = agreement_rows
    independent_rows = []
    for who, v in independent.items():
        for cohort in ('stroke','control'):
            for model in MODELS:
                s=v['cohort_summaries'][cohort]['by_model'][model];e=s['any_error']
                independent_rows.append({'Reviewer': who,'Cohort':cohort.capitalize(),'Model':NAMES[model],
                    'Mean full coverage, %':f"{s['available_case_coverage_mean']*100:.1f}",
                    'Error reports / evaluable':f"{e['events']}/{e['evaluable']}",'Unknown':e['unknown'],
                    'All-planned bounds, %':interval(e['all_planned_bounds'])})
    tables['S3 Original individual outcomes'] = independent_rows
    sensitivity_rows = []
    for s in sensitivity['summaries']:
        if s['cohort'] == 'stroke' and s['model'] == 'gemini':
            e=s['any_error']
            sensitivity_rows.append({'Scenario':s['label'],'Gemini error / evaluable':f"{e['events']}/{e['evaluable']}",
                'Unknown':e['unknown'],'All-planned bounds, %':interval(e['all_planned_bounds'])})
    tables['T6 Targeted sensitivity'] = sensitivity_rows

    receipt = js('docs/formal_study/wording_boundary_confirmation_v1/return_review/RETURN_CHECK.json')
    flag_record = js('docs/formal_study/three_rater_analysis_v1/SEMANTIC_FLAG_CONFIRMATION.json')
    discussion_rules = js('docs/formal_study/three_rater_review_v1/DISCUSSION_RULES_LOG.json')
    tables['S4 Coverage across stages'] = [
        {'Cohort': cohort.capitalize(), 'Model': NAMES[model],
         **{who + ' original, %': f"{independent[who]['cohort_summaries'][cohort]['by_model'][model]['available_case_coverage_mean']*100:.1f}" for who in ('rater1','rater2','rater3')},
         'Frozen post-feedback, %': f"{final['estimates']['cohort_summaries'][cohort]['by_model'][model]['available_case_coverage_mean']*100:.1f}"}
        for cohort in ('stroke','control') for model in MODELS]
    lengths = []
    for report in frozen['reports']:
        rid = report['report_id']
        raw = read(f'docs/formal_study/rating_delivery_v1/rater2/reports/{rid}.txt')
        assert sha(raw) == mapping[rid]['report_sha256']
        lengths.append({'cohort': report['cohort'], 'model': mapping[rid]['model_key'],
                        'words': len(raw.decode('utf-8').split())})
    length_rows = []
    for cohort in ('stroke','control'):
        for model in MODELS:
            values = [r['words'] for r in lengths if r['cohort']==cohort and r['model']==model]
            length_rows.append({'Cohort': cohort.capitalize(), 'Model': NAMES[model], 'Reports': len(values),
                                'Median whitespace units': float(np.median(values)),
                                'Minimum': min(values), 'Maximum': max(values)})
    tables['S5 Descriptive report length'] = length_rows

    manuscript = '''# Completeness and evidence fidelity of large language model gait reports

Working manuscript draft for author review. Numerical results are drawn from preserved analysis records. Bracketed author-confirmation fields must be completed before submission. This document does not assert prospective registration, institutional ethical exemption, unconfirmed reviewer credentials or a new expert consensus.

## Abstract

**Objective:** To compare the completeness and evidence fidelity of reports generated by three large language models from structured gait summaries of stroke participants, with a separate healthy-control analysis.

**Methods:** We used a public motion-capture and electromyography dataset to generate one report per model for each of 25 stroke participants and 10 controls (105 reports). Three human experts independently rated the reports, then reviewed their judgments after clarification of the scoring rules. The primary analysis used the ratings finalized after review; original independent ratings were analyzed separately. Full coverage was the mean proportion of case requirements rated Covered, with equal participant weighting. Paired stroke comparisons used 20,000 bias-corrected and accelerated bootstrap resamples. We assessed confirmed errors separately from unresolved judgments and examined sensitivity to disputed wording.

**Results:** Mean full coverage in stroke reports was 98.2% for Claude, 97.0% for GPT and 81.8% for Gemini. Confidence intervals adjusted for the three comparisons excluded zero for Claude-Gemini and GPT-Gemini, but not Claude-GPT. Confirmed errors occurred in 11/22, 2/25 and 12/23 evaluable stroke reports, respectively; error status remained unknown for the other reports. Original and final ratings differed, particularly for error judgments and Gemini coverage. Corresponding control error counts were 6/9, 0/10 and 8/10. One control pathology annotation remained disputed. Alternative interpretations of selected wording yielded 10-12 confirmed-error Gemini stroke reports among 25 planned reports, with coverage unchanged.

**Conclusion:** Reports with high content coverage could still contain unsupported or incorrect claims. Completeness and evidence fidelity should be evaluated separately. The findings apply to the outputs and scoring procedures studied here; clinical benefit and broader model performance require further evaluation.

## Introduction

Interpreting a gait summary requires more than restating its measurements. A report must identify the principal findings and distinguish numerical differences from explanations that the data cannot establish. Comparisons of post-stroke muscle activity with healthy references depend on walking speed, gait-event alignment and variability within the reference population. Srivastava and colleagues addressed these factors in their altered muscle activation patterns (AMAP) method, using speed-matched comparisons and corresponding gait sub-phases. [1](https://doi.org/10.1186/s12984-019-0487-y) The public dataset used here provides kinematics and surface electromyography (EMG) from able-bodied adults and stroke survivors recorded at self-selected speeds. Its authors describe demographic and speed-related constraints on comparisons between groups. [2](https://doi.org/10.1038/s41597-023-02767-y)

Large language model (LLM) evaluations in medicine have assessed more than factual recall. Singhal and colleagues evaluated medical answers for factuality, reasoning and potential harm, among other dimensions. [3](https://doi.org/10.1038/s41586-023-06291-2) In clinical text summarization, Van Veen and colleagues used physician review to assess completeness, correctness and conciseness. [4](https://doi.org/10.1038/s41591-024-02855-5) The Clinical Large Language Model Evaluation by Expert Review (CLEVER) framework similarly uses blinded expert comparisons across factuality, clinical relevance and conciseness. [5](https://doi.org/10.2196/72153) These studies support evaluating distinct aspects of report quality, but their findings do not establish performance on numerical gait summaries.

Gait report generation is also an emerging application. OGA-AID combines movement recordings, kinematic trajectories and clinical profiles in a multimodal system for post-stroke report drafting, with evaluation by physiotherapists. [6](https://arxiv.org/abs/2604.05360v2) Our study addresses a narrower task: interpreting a fixed numerical summary without access to videos, raw recordings or clinician notes. This design allows comparison of how three model configurations handle the same supplied findings and their stated limits.

We assessed completeness and evidence fidelity separately. Completeness concerns whether a report explains the required findings; evidence fidelity concerns whether its claims are supported by the input. A report can omit an important difference despite fluent prose, or describe the required findings while adding an incorrect comparison or unsupported explanation. Case-specific requirements and checks against the source input allow these problems to be recorded separately, while ambiguous claims can remain unresolved.

We compared three model configurations using identical inputs for 25 stroke participants, with required-content coverage as the primary outcome. A separate analysis of 10 healthy controls examined how reports interpreted deviations when healthy cohort membership was known. Three human experts assessed the reports. We compared their original independent ratings with ratings finalized after clarification and discussion, and examined the effect of unresolved interpretations on the findings.

## Methods

### Study design and data source

We conducted a within-participant comparison of three saved model configurations on a constrained gait-report interpretation task. The principal cohort comprised 25 stroke participants; 10 healthy controls formed a separate exploratory supplement. The task was to describe the supplied evidence faithfully and express its limits, rather than diagnose disease, recommend treatment or interpret raw recordings independently. Each participant contributed one report per configuration, yielding 105 reports. Model outputs and repeated ratings did not increase the independent participant count.

Data originated from the public dataset of Van Criekinge and colleagues, which includes 50 stroke survivors and 138 able-bodied adults and provides motion-capture and surface EMG data in source and postprocessed forms. We used released participant-average curves and verified derived features. The original data-collection study reported informed consent and ethics approvals. The determination applicable to the present secondary analysis remains **[AUTHOR CONFIRMATION REQUIRED: institution, review or exemption determination, and reference number if applicable]**. [2](https://doi.org/10.1038/s41597-023-02767-y).

### Case selection and sample size

The stroke cohort was the entire conservative internal eligibility pool of 25 participants. The local inventory began with 50 stroke participants, identified 43 with complete bilateral data, retained 27 with complete data and no prior report in the checked inventory, and excluded two additional individually audited cases. The controls were selected by a single recorded seeded pseudorandom ordering of 98 locally eligible participants, retaining the first 10. Controls were not age- or speed-matched to the stroke cohort. The study lead subsequently confirmed no additional known use outside the recorded project history for the selected participants. This attestation is not an exhaustive audit of all external systems.

Sample size was resource-defined; no power claim for model superiority or equivalence is made. Case-specific requirements for the selected participants were reviewed before formal generation. These were prospectively specified evaluation cases, not untouched external test cases. The controls had contributed to reference or calibration construction; leave-one-out calculations for individual comparisons did not make the control cohort independent external validation. Table 1 describes the retained sample. Age and published bilateral speed are administrative metadata, not additional model inputs; control speed was not supplied to the models. The published bilateral speed is distinct from the analyzed-side speed supplied in stroke prompts.

### Model-visible information and feature definitions

All three configurations received the same saved system/user input pair for a given participant. Stroke inputs described the paretic side; control inputs described the released left/right pooled average. Inputs identified cohort membership. Seven EMG channels and sagittal pelvis, hip, knee and ankle curves were represented on a 1,001-point cycle. Released normalized ensemble-average EMG curves were used without further amplitude normalization. Stroke normalization provenance was checked numerically where evaluable; healthy-side pooling and normalization relied on release documentation and were not numerically revalidated to the same extent.

The summary included relative envelope amplitudes, retained above-threshold intervals, threshold coverage, boundary continuity, maximum absolute phasewise standardized deviation, two whole-cycle overlap indices, sagittal range of motion and reference-deviation scores. Stroke summaries also provided speed, cadence and a successive-footfall step-length index, defined as 200(P-N)/(P+N), where P and N denote paretic and non-paretic step lengths. This index is not the ordinary percentage shortening relative to the other step. Control prompts marked that paretic/non-paretic index as inapplicable and speed/cadence as not supplied.

The EMG threshold was 20% of each supplied mean curve's own peak. A sample was above threshold only when its value exceeded this threshold. Coverage was the proportion of above-threshold samples before interval filtering. Circular above-threshold runs were retained when their sample count met the 3% minimum; on the 1,001-point grid the integer threshold was 30 samples. This filter removes short above-threshold runs, not below-threshold gaps. Wrapped intervals could cross the cycle boundary. Display rounding could obscure small discontinuities; neither rounded 100% coverage nor a displayed 0%-100% retained interval established full-precision continuous exceedance or physiological continuous contraction. EMG onset estimates depend on the detection method and its parameters. [7](https://pubmed.ncbi.nlm.nih.gov/9020824/) The present 20% threshold and 3% run-length rule were study-specific descriptive choices; the cited onset-detection work does not validate them as physiological onset measures or clinical cutoffs.

The overlap index was computed as twice the summed pointwise minimum of two normalized envelopes divided by their summed amplitudes over the cycle, for TA/GAS and RF/BF. It was not simultaneous activation duration. Per-channel kinematic deviation was the root-mean-square difference from the reference mean curve; the composite was the root mean square of the four sagittal channel scores and was explicitly labeled GPS-like rather than the original nine-variable Gait Profile Score (GPS). [8](https://doi.org/10.1016/j.gaitpost.2009.05.020) Validation of the original GPS does not establish validity of this four-channel composite. Maximum absolute z was the maximum across 1,001 phasewise comparisons, not a single-observation z statistic or a clinical abnormality test.

The reference was pooled rather than individually age- or speed-matched. Stroke comparisons used the healthy reference; each control was excluded from its own mean/SD comparison. Pooled calibration summaries remained distinct from leave-one-out individual references. The full reference included 138 participants for kinematics, with effective EMG availability varying by muscle (106-109 before self-exclusion). Supplied empirical percentiles were descriptive and did not establish diagnostic or normality cutoffs. In particular, the supplied span of muscle-specific maximum-|z| percentiles did not reveal every muscle's individual cutoff.

The instructions permitted naming the documented initial-contact boundary, anatomical muscle actions and genuine clinical follow-up questions. They prohibited assigning intermediate gait phases from cycle percentages without events, converting summary metrics into unsupported deficits or diagnoses, or treating an open question as permission to assert an unsupported observed finding. Individual toe-off, matched muscle timing, raw-signal quality and stride variability were outside the input. Models received no plots, expert checklist, reference answers, retrieval tools or prior conversation. Experts could consult the supplied curves and reference materials while respecting this model-visible information boundary.

### Model configuration and generation

We evaluated the recorded identifiers `claude-opus-5`, `gpt-6-astra` and `gemini-3.1-pro-preview`. These identify the saved configurations, not claims about current services or permanently pinned versions. Each had a 16,000-token output allowance with its recorded high/adaptive reasoning configuration (Supplementary Table S1). The allowance and effort labels did not establish equal computational expenditure across providers. Sampling parameters not sent by the adapter remained provider-managed; deterministic generation is not claimed.

Generation used a frozen task manifest, recorded case ordering and balanced provider ordering within case blocks. The batch was executed in three operational stages: 10 stroke participants, another 10 stroke participants, then five stroke participants plus 10 controls. Inputs and settings were unchanged across stages. One retained response was planned per case and model; retries were restricted to specified transport failures without a usable captured report, never poor content. All 105 formal slots completed on 19 September 2026 UTC with no retry, refusal or token-limit finish. Preliminary technical probes were outside the formal 105-report analysis. Responses were retained with generation metadata and verified against captured stream evidence.

### Expert assessment and workflow changes

Three human reviewers independently scored all 105 reports in the original rating round. All three were PhD students at The University of Texas at Austin with at least five years of experience in EMG analysis and neuromuscular control research, as confirmed by the study lead. All scoring judgments were made by the human reviewers themselves. Rater1 and rater2 participated in criteria development; rater3 joined at scoring and did not develop the criteria. Each complete stage comprised 315 report-review assignments and 1,656 coverage judgments, not 315 participants.

The original plan specified two independent reviewers and a third reviewer for unresolved adjudication. The implemented workflow instead added a third complete independent review after the first two submissions and their administrative inspection, while model identities remained concealed. Some blinded outcome counts had already been seen at that decision. This was a documented change after access to outcome-related information, not an original prospective three-rater design. The third reviewer was not treated as a privileged tie-breaker; no coordinator or fourth-reviewer adjudication is asserted.

Review packets used opaque report identifiers, concealed provider metadata, separately randomized reading orders and separated same-case reports. Original prose was preserved rather than paraphrased to conceal style. Reviewers recorded incidental unblinding. Independent submissions were preserved separately from later targeted corrections, discussion and source-linked post-feedback decisions. Administrative material preparation and quotation checks were separate from the experts' scoring. Later discussion and personal rechecks could affect interpretation and were not treated as fresh independent reviews.

Case-specific requirements were fixed before generation: 119 across stroke cases and 30 across controls. Each report had 4-6 stroke requirements or three control requirements. Reviewers used Covered, Partially covered or Not covered, with missing or unresolved assessments recorded separately. A core finding required its specified explanatory content, not only a numerical list. G03 separately assessed meaningful reference-comparability limitations and their implications for disease attribution or diagnosis; one statement could satisfy overlapping requirements without repetition.

Correctness was assessed through distinct report-scoped issue groups under nine categories: misreported facts; unsupported clinical/function inference; threshold/amplitude overinterpretation; unsupported events/phases/functions; invalid reference classification; overlap-index overinterpretation; kinematic-summary overinterpretation; missingness/applicability errors; and unsupported matching/disease attribution. Multiple tags or repeated locations did not multiply a group. Coverage and error judgments remained separate. Interpretive uncertainty could remain Pending; it was neither forced to Error nor cleared by default.

The source-linked blinded outcome dataset was frozen on 23 September 2026 before the authorized model-mapping join. It contained matching coverage judgments, 52 confirmed issue groups and 16 administratively closed but substantively unresolved Pending groups. Different personal category proposals were preserved, without a majority or union category assignment. The protocol's earlier requirement for an E02 co-tag on one form of pathological presupposition was clarified after rating: an explicit qualifying human annotation and confirmed in-scope issue were required, but a simultaneous E02 label was not. This change is reported as post-rating clarification.

The D01-D03 clarification was issued after the original independent submissions. It required interpretation beyond numerical or magnitude-sorted lists and clarified that genuine clinical questions propose possibilities, while wrong facts or explicit unsupported observed premises remain reviewable. These rules were applied in personal rechecks and subsequent discussion. The frozen results are post-feedback outcomes, not unchanged scores from the original independent round.

### Outcomes and analysis

The primary outcome was full coverage of included case requirements: C_im = Covered_im / K_i. Participants were equally weighted, K_i remained fixed across models, partial coverage received no half-credit, and G03 was excluded from K_i. The primary comparison used the same 25 stroke participants with all three coverage scores available. For each model pair, we calculated participant-level percentage-point differences and their mean. We used 20,000 paired BCa resamples, the same saved participant-index matrix for all contrasts and seed 20260918. Descriptive 95% and approximate Bonferroni-adjusted 98.3333% intervals were reported for the three primary contrasts. The implementation preserved paired sampling and reported unavailable intervals without switching methods; these are approximate intervals rather than guaranteed finite-sample bounds. [9](https://doi.org/10.1080/01621459.1987.10478410) [10](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).

Secondary outcomes included any confirmed case error, unique confirmed issue counts, G03 coverage, technical completion and an operational joint-success measure requiring all case requirements and G03 Covered with no confirmed or Pending error after complete review. These were not clinical safety or usefulness endpoints. Any-error was positive if at least one confirmed error existed; otherwise it was negative only after complete review with no Pending issue, and unknown otherwise. Evaluable denominators and all-planned bounds were shown together. Bounds counted unknown states as zero or one and were not confidence intervals. Joint-success point estimates retained the protocol's complete-review denominator, separately from all-planned known/unknown status.

Binary outcomes used exact two-sided 95% binomial intervals on the stated evaluable denominators; their assumptions are limited by selected cases and shared references. The zero-event control result also has a one-sided 95% upper limit of 1-0.05^(1/10), approximately 25.9%. Secondary and control comparisons were exploratory, without additional confirmatory tests or an overall quality ranking. [11](https://doi.org/10.1093/biomet/26.4.404) [12](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).

Original independent agreement was evaluated separately by cohort and domain using raw agreement, three-category coverage cross-tabulations and unweighted Cohen's kappa; report-level any-error used binary states. [13](https://doi.org/10.1177/001316446002000104) Pairwise unknown/incomplete observations were excluded with counts disclosed. Rater1-rater2 was the originally planned comparison; the other pairs were supplementary. Kappas were not averaged into a three-rater coefficient. We reported raw agreement alongside kappa because kappa depends on the marginal distributions of ratings. [14](https://pubmed.ncbi.nlm.nih.gov/2348207/) No confidence interval treating all item rows as independent was used. Original independent model-specific outcomes were retained as a sensitivity analysis distinct from post-feedback outcomes.

### Separate healthy-control analysis and later sensitivity

All 30 control reports were analyzed separately. Two nonexclusive annotations captured unsupported pathological/clinical-impairment assertions and unsupported overall-normality/function assertions. Cohort membership, numerical deviation or a genuine clinical question alone did not qualify. Each annotation required its own explicit judgment and a confirmed in-scope issue for a positive endpoint. The annotations were not diagnostic classifications, sensitivity, specificity or clinical false-positive rates. The 30 reports represented 10 correlated case sets, not 30 independent controls.

After analysis-team unblinding, eight wording-sensitive groups underwent targeted personal review. Packets omitted identities, model results and peer positions; all three reviewers declared no model-identity or comparison-result exposure, while earlier discussion exposure remained recorded. Four labels matched as Error, four remained divergent, and one control pathology annotation differed. We preserved the frozen primary results and performed exploratory hybrid overlays substituting only each reviewer's eight latest decisions and one annotation into the shared baseline. Additional scenarios treated the four divergent claims as Pending, Acceptable or Error, with the disputed annotation unknown, negative or positive. Previously Pending groups remained Pending. These scenarios were neither new expert consensus nor full independent-rater estimates.

## Results

### Sample and report completion

The retained sample comprised 25 stroke participants and 10 controls (Table 1). The age distributions differed, with medians of 65.0 and 75.5 years, respectively. Twenty-two selected stroke participants had published bilateral speed below 0.80 m/s; this descriptive count uses administrative source metadata and is not a count derived from rounded prompt values. All 105 reports were captured. Generation records showed normal stream completion for every report, with zero retries, refusals and token-limit finishes. Reviewers recorded all reports as having the requested four-section format and reported no incidental unblinding during the original review; these are declarations and technical observations, not proof of factual correctness.

### Table 1. Retained participant characteristics

{{T1 Sample}}

IQR uses the 25th and 75th percentiles with linear interpolation. Administrative age and published bilateral speed were summarized after checking membership against the frozen roster; they were not added to model inputs. Historical planning-status fields in the source metadata were not interpreted as current eligibility or generation status.

### Primary stroke coverage

Mean full coverage was 98.2% for Claude, 97.0% for GPT and 81.8% for Gemini. Claude-Gemini and GPT-Gemini contrasts were positive under the planned family-adjusted interval procedure. The Claude-GPT interval included zero and did not establish either superiority or equivalence (Table 3). No participant was excluded from the complete paired coverage analysis. All G03 judgments in the frozen post-feedback layer were Covered. The denominator comprised case-specific requirements rather than all possible factual assertions.

### Table 2. Frozen coverage and report-level errors, by cohort

{{T2 Frozen outcomes}}

Coverage is the equally weighted participant mean. Error proportions use the displayed evaluable denominator; unknown reports remain in the all-planned bounds. Confirmed groups are not severity-weighted and are not the number of erroneous reports. Later wording-review alternatives are reported below; this table preserves the historical frozen layer.

### Table 3. Paired stroke coverage contrasts

{{T3 Paired coverage}}

All intervals are in percentage points; n=25 paired participants. Gemini minus GPT is the negative form of GPT minus Gemini.

### Stroke errors and joint outcome

In the frozen layer, Claude had confirmed errors in 11/22 evaluable stroke reports, Gemini in 12/23 and GPT in 2/25; three Claude and two Gemini reports were unknown because a Pending issue remained without a confirmed error. The all-planned bounds were 44%-56%, 48%-56% and 8%-8%, respectively. Confirmed issue groups numbered 17, 13 and two. This descriptive pattern was not subjected to a new confirmatory superiority test. Full coverage could coexist with a factual or interpretive error. Supplementary Table S2 reports the joint outcome with its complete-review denominator, which differs from the any-error denominator when a known failure also has unresolved issues.

### Healthy-control reports

The 10 controls contributed all 30 planned reports. Mean full coverage was 90.0% for Claude, 86.7% for GPT and 73.3% for Gemini. Confirmed-error reports numbered 6/9 evaluable for Claude, 0/10 for GPT and 8/10 for Gemini; one Claude report remained unknown. These counts include factual, metric and evidence-boundary violations, not only pathological assertions or diagnoses. No control normality annotation was positive in the frozen data. One Gemini control pathology annotation was positive at freeze, but later personal review produced Yes/No/Yes rather than a matching judgment (Table 4). The other models had no positive pathology annotation. Zero events among 10 controls did not establish absence of risk; the one-sided 95% upper limit was 25.9% under the binomial assumptions.

### Table 4. Control semantic annotations and later disagreement

{{T4 Control flags}}

For the disputed Gemini pathology annotation, preserving disagreement as unknown gives zero known-positive reports among nine evaluable reports and one unknown, with all-planned bounds 0%-10%. This is not equivalent to 0/10 negative or to a new unanimous positive. Control any-error status remains unchanged in all targeted scenarios because other confirmed errors remain in the affected reports.

### Descriptive report length

Saved blinded report texts were counted by whitespace splitting, including headings and table markup. This post-hoc descriptive measure is not linguistic word segmentation, billable tokens, reasoning length or a measure of quality. Stroke median counts were 2,049 for Claude, 818 for GPT and 761 for Gemini; control medians were 1,992, 803.5 and 712.5 (Supplementary Table S5). No length adjustment or additional significance test was introduced.

### Original independent agreement and stage sensitivity

Original case-requirement agreement for stroke was 95.5%, 94.4% and 95.0% for rater1-rater2, rater1-rater3 and rater2-rater3, respectively; kappas were 0.550, 0.305 and 0.559. Report-level error agreement was less consistent and used different assessable subsets. Controls also showed differences between high raw coverage agreement and modest or variable kappa (Table 5). G03 kappa was often undefined because the included ratings had no category variation. Neither agreement nor kappa established correctness or reviewer quality.

### Table 5. Original independent agreement

{{T5 Independent agreement}}

These are descriptive item/report comparisons with within-participant dependence; pair-specific exclusions prevent treating all pairs as if they assessed the same reports. The full original independent outcome table is Supplementary Table S3. Rater1 and rater2 originally recorded fewer confirmed-error stroke reports for GPT than for the other models. Rater3 originally recorded 0/25 for Claude, 1/25 for GPT and 1/10 for Gemini with 15 unknown Gemini reports. Thus the later Claude-GPT error ordering was not reproduced by every original reviewer. Original coverage results consistently placed Claude and GPT above Gemini in mean full coverage, with different effect magnitudes.

Supplementary Table S4 directly compares coverage stages. Gemini stroke coverage was 93.8%, 86.0% and 86.5% in the three original reviews, versus 81.8% in the shared frozen layer. Claude and GPT changed less. These differences combine clarification, personal reconsideration and discussion; they cannot be attributed causally to D01 or D02 alone. Model separation in the frozen layer must not be presented as the magnitude found independently by all original reviewers.

### Post-unblinding targeted sensitivity

The eight-item follow-up did not alter coverage scores. Claude retained 11 confirmed-error stroke reports and GPT retained two. Gemini varied from 10 to 12 confirmed-error reports across the 25 planned slots, with an overall unknown-status envelope of 40%-56% (Table 6). Only two report-level any-error statuses could change; other changed claim labels left a separate confirmed error. The description of fewer flagged stroke reports for GPT persisted within this targeted sensitivity, while the Claude-Gemini ordering was not stable. These classification bounds are not sampling intervals or evidence of general superiority. The control pathology disagreement remained separately visible.

### Table 6. Gemini stroke sensitivity to targeted interpretations

{{T6 Targeted sensitivity}}

Named-reviewer overlays replace only the eight targeted decisions and one annotation. All other judgments retain the shared frozen baseline; these rows must not be labeled complete independent-rater analyses. Disputed-claim scenarios are analyst-defined, not votes or additional expert judgments.

## Discussion

High content coverage did not ensure evidence fidelity. Claude and GPT included more required content than Gemini in the final stroke ratings, but Claude reports also contained confirmed errors in 11 of 22 evaluable cases. GPT had fewer reports with confirmed errors, although this comparison was descriptive. The coverage difference between Claude and GPT remained uncertain. These findings favor assessing completeness and errors separately: combining them into a single score would obscure differences that matter when reviewing a report. This distinction is consistent with the separate completeness and correctness judgments used by Van Veen and colleagues and the factuality dimension in CLEVER. [4](https://doi.org/10.1038/s41591-024-02855-5) [5](https://doi.org/10.2196/72153) Their tasks, models and evaluation criteria differed, so their results do not provide a direct benchmark for the error proportions reported here.

The coverage pattern was consistent across the original reviewers, each of whom rated Claude and GPT above Gemini on average. Its magnitude changed after clarification and discussion. Error judgments varied more, and one reviewer's original ratings did not show the later Claude-GPT ordering. The final ratings therefore reflect both the reports and how the experts applied the evaluation criteria. High raw agreement accompanied by a lower kappa also needs care: imbalanced rating distributions can produce this pattern, as Feinstein and Cicchetti demonstrated. [14](https://pubmed.ncbi.nlm.nih.gov/2348207/) It does not by itself identify which reviewer is correct. Reporting the original ratings alongside the final results shows this dependence and preserves disagreements that the review did not resolve.

Report length may help explain the observed pattern, but the present design cannot isolate its contribution. Longer reports have more space to explain required findings and more opportunities to introduce unsupported claims. Length varied with model, writing style and reasoning configuration. A study that specifies comparable length limits and obtains repeated responses for each case could examine these relationships directly. Conciseness was a separate evaluation dimension in both the clinical summarization study and CLEVER; we did not score conciseness here. [4](https://doi.org/10.1038/s41591-024-02855-5) [5](https://doi.org/10.2196/72153)

Healthy-control reports provided a separate test of how models handled deviations in participants explicitly identified as healthy. The any-error outcome included incorrect numerical comparisons as well as unsupported interpretations, so it cannot be read as a rate of pathological diagnoses. Only 10 controls were included, and one pathology annotation remained disputed. These findings describe errors in the sampled reports but offer limited evidence about rare harmful assertions or performance in new populations.

Preserved prompts, judgments linked to the source reports and reproducible analyses allow readers to examine the basis of these findings. These practices are consistent with the transparency emphasized by the Chatbot Assessment Reporting Tool (CHART); they do not establish complete compliance with that guideline. [15](https://doi.org/10.1136/bmj-2024-083305). The next evaluation should use independent cases, specify how ambiguous language will be scored before review, and obtain repeated model outputs. Clinical usefulness also remains to be tested: this study did not measure review time, changes in management or patient outcomes. DECIDE-AI addresses reporting of early live clinical evaluations, including the interaction between users and decision-support systems. [16](https://doi.org/10.1038/s41591-022-01772-9) Such an evaluation would be a separate step beyond the present offline report comparison.

## Limitations

This was a resource-defined, selected internal sample of 25 stroke participants and 10 controls. It was not a random clinical population sample, a powered equivalence study or external validation. The available stroke cohort and the selected subset do not represent all stroke stages or ambulatory abilities. Controls were relatively old, not matched to stroke cases, and had contributed to reference/calibration construction. Age and speed differences, shared reference estimates and missing muscle data limit physiological comparability. Leave-one-out self-exclusion does not remove all shared-data dependence.

The task tested constrained interpretation of supplied summaries. Models knew cohort membership and did not inspect raw EMG, individual strides or clinical examinations. High rubric coverage therefore does not establish diagnostic accuracy, patient benefit or readiness for clinical use. Correctly expressing uncertainty can be appropriate, while a true but unsupplied detail can violate the task's evidence boundary. The endpoints combine different types of error without a validated severity weighting. The four-channel GPS-like composite and threshold-derived envelope summaries are not clinical diagnostic tests.

The reference standard was an expert-defined interpretation framework rather than independent clinical ground truth. Two raters helped develop the rules, while the third joined after the first submissions. Review and discussion clarified ambiguous wording and sometimes changed labels. Blinding to model identity reduced one source of bias but did not remove stylistic clues, prior beliefs, development involvement or later exposure to peer views. The frozen post-feedback results must be read alongside the original independent agreement and outcome analyses; original rater3 error judgments did not reproduce every later model ordering.

The source audit and eight-item follow-up occurred after analysis-team unblinding. Their purposive scope and analyst-defined scenarios make the supplement exploratory. Coverage was unchanged because the follow-up did not reassess it; this provides no independent validation of coverage. Retaining four divergent issue judgments and one disputed pathology annotation is more faithful than implying new unanimity. The targeted sensitivity does not establish robustness to all possible errors, alternative rubrics or selection of a different reference standard.

Only one response was generated per case and configuration. The study cannot estimate within-model stochastic reliability or performance across prompt variants. Recorded effort labels, token allowances and provider-managed sampling settings do not establish equal compute. Saved identifiers may be service aliases, and operational staging introduces time/batch context despite unchanged settings. Results apply to these saved configurations and responses.

Item and report counts exceed the number of independent participants. Pairwise agreement denominators differ, and naive item-level precision would be misleading. Exact binomial intervals do not remedy selected sampling or shared references; bootstrap intervals remain approximate. Ten controls provide limited precision, particularly for rare semantic flags. No overall winner, clinical false-positive rate or proof of safety should be inferred from these results.

## Conclusion

Claude and GPT achieved higher content coverage than Gemini in this sample. GPT had fewer stroke reports with confirmed errors in the final ratings and targeted sensitivity analyses, although original error judgments varied across reviewers. Assessing completeness and evidence fidelity separately revealed differences that a single quality score would miss. Independent cases, repeated outputs and an independently applied reference standard are needed to assess whether these findings generalize.

## Supplementary tables

### Supplementary Table S1. Recorded generation configurations

{{S1 Model configuration}}

Client retries were disabled; allowed retry behavior was controlled by the study runner and no formal retry occurred. Stored SDK versions and model identifiers are historical generation records. Sampling parameters not explicitly passed were provider-managed; equal effort labels are not evidence of equal compute. Generation ran from {{GENERATION_START}} to {{GENERATION_END}}.

### Supplementary Table S2. Joint-success outcomes in the frozen layer

{{S2 Joint outcome}}

A known joint failure with unresolved issues can be outside the complete-review denominator while still constraining all-planned bounds. The joint measure is operational, not clinical usability certification.

### Supplementary Table S3. Original independent outcomes

{{S3 Original individual outcomes}}

These are the preserved original independent stage, unlike the targeted hybrid overlays in Table 6. They must not be substituted selectively to obtain a preferred model ordering.

### Supplementary Table S4. Coverage before and after review

{{S4 Coverage across stages}}

The frozen column is one shared post-feedback layer, not a fourth independent reviewer. All columns use the fixed case denominators and equal participant weighting. Differences are descriptive stage sensitivity, not an estimated causal effect of one clarification.

### Supplementary Table S5. Saved report length

{{S5 Descriptive report length}}

Counts use Python str.split() on the hash-verified blinded report text, including Markdown. They are neither provider tokens nor a validated measure of verbosity or quality. This analysis was added after unblinding; no length-adjusted outcome or new inferential test was specified.

## References

- [1](https://doi.org/10.1186/s12984-019-0487-y) Srivastava S, Patten C, Kautz SA. Altered muscle activation patterns (AMAP): an analytical tool to compare muscle activity patterns of hemiparetic gait with a normative profile. Journal of NeuroEngineering and Rehabilitation. 2019;16:21.
- [2](https://doi.org/10.1038/s41597-023-02767-y) Van Criekinge T, et al. A full-body motion capture gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors. Scientific Data. 2023;10:852.
- [3](https://doi.org/10.1038/s41586-023-06291-2) Singhal K, et al. Large language models encode clinical knowledge. Nature. 2023;620:172-180.
- [4](https://doi.org/10.1038/s41591-024-02855-5) Van Veen D, et al. Adapted large language models can outperform medical experts in clinical text summarization. Nature Medicine. 2024;30:1134-1142.
- [5](https://doi.org/10.2196/72153) Kocaman V, Kaya MA, Feier AM, Talby D. Clinical Large Language Model Evaluation by Expert Review (CLEVER): Framework Development and Validation. JMIR AI. 2025;4:e72153.
- [6](https://arxiv.org/abs/2604.05360v2) Nguyen KTN, et al. OGA-AID: Clinician-in-the-loop AI Report Drafting Assistant for Multimodal Observational Gait Analysis in Post-Stroke Rehabilitation. 2026. arXiv:2604.05360v2. Cited arXiv version; the record identifies the work with the 2026 CV4Clinic CVPR Workshop Proceedings.
- [7](https://pubmed.ncbi.nlm.nih.gov/9020824/) Hodges PW, Bui BH. A comparison of computer-based methods for the determination of onset of muscle contraction using electromyography. Electroencephalography and Clinical Neurophysiology. 1996;101(6):511-519. PMID:9020824.
- [8](https://doi.org/10.1016/j.gaitpost.2009.05.020) Baker R, et al. The gait profile score and movement analysis profile. Gait & Posture. 2009;30(3):265-269.
- [9](https://doi.org/10.1080/01621459.1987.10478410) Efron B. Better Bootstrap Confidence Intervals. Journal of the American Statistical Association. 1987;82(397):171-185.
- [10](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) SciPy. Bootstrap confidence intervals, including paired resampling and BCa. Technical documentation. Accessed September 25, 2026. Cited for methodological context; local code produced the saved estimates.
- [11](https://doi.org/10.1093/biomet/26.4.404) Clopper CJ, Pearson ES. The use of confidence or fiducial limits illustrated in the case of the binomial. Biometrika. 1934;26(4):404-413.
- [12](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm) National Institute of Standards and Technology. Exact binomial confidence limits. Dataplot Reference Manual. Accessed September 25, 2026.
- [13](https://doi.org/10.1177/001316446002000104) Cohen J. A coefficient of agreement for nominal scales. Educational and Psychological Measurement. 1960;20(1):37-46.
- [14](https://pubmed.ncbi.nlm.nih.gov/2348207/) Feinstein AR, Cicchetti DV. High agreement but low kappa: I. The problems of two paradoxes. Journal of Clinical Epidemiology. 1990;43(6):543-549. doi:10.1016/0895-4356(90)90158-L.
- [15](https://doi.org/10.1136/bmj-2024-083305) The CHART Collaborative. Reporting guidelines for chatbot health advice studies: explanation and elaboration for the Chatbot Assessment Reporting Tool (CHART). BMJ. 2025;390:e083305.
- [16](https://doi.org/10.1038/s41591-022-01772-9) Vasey B, et al. Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI. Nature Medicine. 2022;28:924-933.

## Declarations requiring author completion

The institutional ethics determination for this secondary analysis, author affiliations and contributions, funding, competing interests, and the final data/code release statement remain to be supplied by the authors. The original dataset's approvals do not constitute an approval or exemption for this project. The recorded human expert judgments must not be described as newly signed through manuscript preparation. The role of AI-assisted drafting, software development and source auditing should be described accurately in the journal's required disclosure, without assigning such tools authorship or decision authority. See AUTHOR_CONFIRMATION.md.
'''
    for name, rows in tables.items():
        manuscript = manuscript.replace('{{'+name+'}}', md_table(rows).rstrip())
    manuscript = manuscript.replace('{{GENERATION_START}}',generated_start).replace('{{GENERATION_END}}',generated_end)
    assert '{{' not in manuscript and not re.search(r'[\u4e00-\u9fff]',manuscript)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'MANUSCRIPT.md').write_text(manuscript)
    (OUT/'MANUSCRIPT.html').write_text(reading_html(manuscript))
    w=Workbook();w.remove(w.active)
    for name,rows in tables.items():
        s=w.create_sheet(name);s.append(list(rows[0]))
        for row in rows:s.append(list(row.values()))
        s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
        for cell in s[1]:
            cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='23475A')
        for row in s:
            for c in row:
                c.alignment=Alignment(wrap_text=True,vertical='top')
                if isinstance(c.value,str):c.data_type='s'
        for column in s.columns:s.column_dimensions[column[0].column_letter].width=28
        for r in range(1,s.max_row+1):s.row_dimensions[r].height=60
    w.save(OUT/'Manuscript_tables.xlsx')
    (OUT/'TABLE_DATA.json').write_text(json.dumps({'tables':tables,'generation_utc':[generated_start,generated_end],
        'participant_quantile_method':'NumPy linear interpolation; administrative published bilateral speeds, not rounded model inputs',
        'source_sha256':sources},indent=2)+'\n')
    source_map='''# Manuscript source map

| Content | Authoritative local source |
| --- | --- |
| Frozen numerical outcomes and paired intervals | `data/rating_packets_formal_v1/private/three_rater_model_analysis_v1/final_outcomes.json` |
| Current reviewer background | `docs/formal_study/REVIEWER_BACKGROUND_CONFIRMATION.json`; study-lead confirmation, not a new expert signature |
| Original independent outcomes and coverage stage comparison | Same protected directory, `independent_sensitivity.json` |
| Descriptive length | 105 hash-verified blinded report texts in `rating_delivery_v1/rater2/reports`; whitespace splitting including Markdown |
| Original agreement and exclusions | `docs/formal_study/three_rater_analysis_v1/INDEPENDENT_AGREEMENT.json` |
| Targeted sensitivity | `data/rating_packets_formal_v1/private/wording_sensitivity_v1/ANALYSIS.json` |
| Sample characteristics | `docs/formal_study/control_supplement_v2/selected_study_cases.csv`, membership checked against the frozen roster; old status fields excluded |
| Eligibility and exposure history | `sample_eligibility_v1/README.md`, `execution_analysis_v1_draft/exposure_confirmation.json` |
| Original plan versus implemented review | `execution_analysis_v3_draft/PROTOCOL.md`, `rating_delivery_rater3_v1/REVIEWER_ADDITION_RECORD.md`, `three_rater_analysis_v1/ANALYSIS_ADDENDUM_DRAFT.md` and later authorization records |
| Semantic flag clarification | `three_rater_analysis_v1/SEMANTIC_FLAG_CONFIRMATION.json` |
| Generation settings and dates | `formal_execution_v2_candidate/plan.json`, `provider_configuration.json`, `formal_stages_v1/GENERATION_COMPLETION.json`, stage result rows |
| Feature definitions | Saved model prompts; `src/features/emg_signal.py`, `src/features/kinematic.py`; Baker et al. provides the original GPS context, not validation of this study-specific composite |
| Related work and methodological references | Numbered manuscript references: AMAP for matched EMG comparisons; Singhal, Van Veen and CLEVER for evaluation dimensions; OGA-AID for related gait reporting; Hodges and Bui for detection-method dependence; Efron, Clopper-Pearson and Cohen for statistical methods; Feinstein and Cicchetti for kappa interpretation; CHART and DECIDE-AI for reporting context |

Only later, scoped completion/authorization records supersede historical pending-status statements. Historical protocol text was not edited or represented as if it originally specified three independent raters or the later semantic clarification. The manuscript preserves this chronology.

External references verified while preparing this draft: the [dataset publication](https://www.nature.com/articles/s41597-023-02767-y), [SciPy paired-bootstrap/BCa documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), and [NIST exact binomial limits](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm). These support dataset context and calculation concepts, not the project's selection, ethical determination or empirical results. The project's BCa implementation is local code; the manuscript does not claim that scipy.stats.bootstrap directly produced the saved estimates.

The manuscript contains 16 references selected for direct relevance, including 13 journal articles, one explicitly identified arXiv workshop version and two technical documentation sources. Metadata and the cited propositions were checked against publisher, PubMed, arXiv or Crossref records on September 25, 2026. OGA-AID is cited as arXiv:2604.05360v2, not as a journal article. Hodges and Bui is linked through PMID:9020824 because PubMed and Crossref expose different DOI prefixes for the same title. Bibliographic verification does not imply that every full text was available. This is a focused background, not a systematic literature review. CHART is cited for reporting context, not as evidence of completed checklist compliance. No journal-specific reporting-compliance claim is made. Per-report model identities remain outside reviewer packets.
'''
    (OUT/'SOURCE_MAP.md').write_text(source_map)
    confirmation='''# Author confirmations before submission

The working draft includes an abstract, introduction, methods, results, discussion and limitations. The following author-owned facts have not been inferred from project files. A question was sent to the study lead; no response is inferred from elapsed time.

| Field | Current status | Information needed |
| --- | --- | --- |
| Reviewer background | Confirmed by the study lead: all three are PhD students at The University of Texas at Austin with at least five years of experience in EMG analysis and neuromuscular control research | Background paragraph completed; no completed doctorate, candidacy milestone or clinical licensure inferred |
| Ethics for this secondary analysis | Not established by the original dataset's approval | Actual institutional review/exemption determination and reference number, if applicable; do not invent exemption |
| Funding and competing interests | Not provided | Funder/grant details or an author-confirmed no-funding statement, and each author's relevant interests |
| Authorship and contributions | Not provided | Author names, affiliations, contributions and corresponding-author details |
| Data/code release | Original dataset public; project release scope not finalized here | Exact repository/version intended for publication, licensed material and permitted expert-record sharing |
| AI assistance disclosure | Assistant-supported coding, source audit, material preparation and manuscript drafting occurred | Accurate journal-specific description of tool roles and author verification; human judgments remain the experts' responsibility |
| Target journal and style | Not selected | Journal, article type, length and reference style before submission formatting |

No further forced expert agreement is needed to report the existing personal disagreements. Completing these declarations does not change any score, endpoint or frozen result.
'''
    if not (OUT/'AUTHOR_CONFIRMATION.md').exists():
        (OUT/'AUTHOR_CONFIRMATION.md').write_text(confirmation)
    (OUT/'README.md').write_text('''# English manuscript working draft

Read [the browser version](MANUSCRIPT.html) or edit [the Markdown manuscript](MANUSCRIPT.md). The draft contains an abstract, introduction, methods, results, discussion and limitations, with a separate healthy-control analysis, six main tables and five supplementary tables. Supplementary tables include coverage across scoring stages and descriptive report length. [Excel tables](Manuscript_tables.xlsx) use the same source values.

Numerical results come from the frozen model analysis, original independent agreement/outcomes and the subsequent targeted sensitivity. Original reports, reviewer submissions, model-analysis files and the frozen dataset were not modified. The manuscript distinguishes the original two-reviewer plan, later third independent reviewer and post-unblinding follow-up. It does not claim a unanimous pathology annotation after the later disagreement.

[Author confirmations](AUTHOR_CONFIRMATION.md) record the confirmed reviewer background and identify the remaining ethics and author declarations. These fields remain explicit placeholders, so this is not yet a submission-ready manuscript. [Source map](SOURCE_MAP.md), [table data](TABLE_DATA.json) and [build record](BUILD_RECORD.json) support verification. All project documents are in English.

Rebuild numerical tables and the draft with `python scripts/build_manuscript_draft.py` from the repository root. This overwrites generated manuscript files; preserve author edits before rerunning. The author-confirmation file is not overwritten on rebuild. For a separate build, use `python scripts/build_manuscript_draft.py --output /path/to/new/manuscript`; an existing explicit output directory is refused.
''')
    for name,digest in sources.items():
        assert sha((ROOT/name).read_bytes())==digest,f'Source changed during build: {name}'
    outputs=[p for p in OUT.iterdir() if p.is_file() and p.name!='BUILD_RECORD.json']
    (OUT/'BUILD_RECORD.json').write_text(json.dumps({'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'English full working manuscript; separate stroke/control results, review-stage comparison and descriptive report length',
        'source_sha256':sources,'output_sha256':{p.name:sha(p.read_bytes()) for p in outputs},
        'external_references_checked_on':'2026-09-25','table_count':len(tables),
        'generation_plan_canonical_json_sha256':canonical_plan_hash,
        'scores_or_frozen_results_modified':False,'author_owned_declarations_inferred':False},indent=2)+'\n')
    print(json.dumps({'output':str(OUT),'tables':len(tables),'draft_words':len(manuscript.split())}))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Source project or extracted reproduction bundle')
    parser.add_argument('--output', type=Path, help='New output directory; refuses an existing directory')
    args = parser.parse_args()
    ROOT = args.root.resolve()
    if args.output:
        OUT = args.output.resolve()
        if OUT.exists():
            parser.error('--output must not already exist')
    else:
        OUT = ROOT / 'docs/formal_study/manuscript_v1'
    main()
