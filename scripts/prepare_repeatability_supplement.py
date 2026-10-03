"""Prepare an offline, non-executable 25-case repeated-generation supplement."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from importlib.metadata import version
from itertools import permutations
import json
from pathlib import Path
import random
import csv

ROOT=Path(__file__).resolve().parents[1]
BASE='docs/formal_study/'
OUT=ROOT/BASE/'repeatability_supplement_v1'
PROVIDERS=('anthropic','gemini','openai')
SEED=20260925


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def make_schedule(case_ids):
    cases=sorted(case_ids)
    if len(cases)!=25 or len(set(cases))!=25:
        raise ValueError('Exactly the 25 unique original stroke cases are required')
    rng=random.Random(SEED)
    base_cases=cases.copy();rng.shuffle(base_cases)
    orders=list(permutations(PROVIDERS));rng.shuffle(orders)
    assigned={case:orders[i%len(orders)] for i,case in enumerate(base_cases)}
    schedule=[]
    for repeat in (1,2,3):
        wave=cases.copy();rng.shuffle(wave)
        for case in wave:
            order=assigned[case]
            offset=repeat-1
            order=order[offset:]+order[:offset]
            for position,provider in enumerate(order,1):
                schedule.append((case,provider,repeat,position))
    return schedule


def create_tasks(original):
    tasks=[t for t in original['tasks'] if t['group']=='stroke']
    index={(t['case_id'],t['provider']):t for t in tasks}
    cases={t['case_id'] for t in tasks}
    if len(tasks)!=75 or len(index)!=75 or set(index)!={(c,p) for c in cases for p in PROVIDERS}:
        raise ValueError('Original stroke task roster is incomplete or duplicated')
    output=[]
    for seq,(case,provider,repeat,position) in enumerate(make_schedule(cases),1):
        t=index[case,provider]
        if digest([t['system_prompt'],t['user_prompt']])!=t['input_pair_sha256']:
            raise ValueError('Historical task input digest changed')
        output.append({'sequence':seq,'slot_id':f'repeat_v1_r{repeat:02d}_{case}_{provider}',
            'case_id':case,'cohort':'stroke','provider':provider,'model':t['model'],
            'repeat':repeat,'provider_position_within_case':position,
            'original_slot_id':t['slot_id'],'original_task_sha256':digest(t),
            'input_pair_sha256':t['input_pair_sha256'],'parameters':deepcopy(t['parameters']),
            'system_prompt_path':BASE+f'case_review_v1/{case}/model_system_prompt.txt',
            'user_prompt_path':BASE+f'case_review_v1/{case}/model_user_prompt.txt'})
    assert len({t['slot_id'] for t in output})==225
    assert not {t['slot_id'] for t in output}&{t['slot_id'] for t in original['tasks']}
    return output


def main(output=OUT):
    output=output.resolve()
    if output.exists():raise FileExistsError('Use a new output directory; do not overwrite a planning record')
    sources={}
    def read(path):
        raw=(ROOT/path).read_bytes();sources[path]=hashlib.sha256(raw).hexdigest();return raw
    original=json.loads(read(BASE+'formal_execution_v2_candidate/plan.json'))
    completion=json.loads(read(BASE+'formal_stages_v1/GENERATION_COMPLETION.json'))
    assert digest(original)==completion['full_plan_sha256']
    assert completion['report_counts']=={'stroke':75,'control':30,'total':105}
    config=json.loads(read(BASE+'formal_execution_v2_candidate/provider_configuration.json'))
    tasks=create_tasks(original)
    original_index={t['slot_id']:t for t in original['tasks']}
    for task in tasks:
        old=original_index[task['original_slot_id']]
        for field,pathfield in [('system_prompt','system_prompt_path'),('user_prompt','user_prompt_path')]:
            raw=read(task[pathfield]);assert raw.decode()==old[field],task['slot_id']
        provider=next(p for p in config['providers'] if p['provider']==task['provider'])
        assert (provider['model'],provider['parameters'])==(task['model'],task['parameters'])
    reqpath=BASE+'case_requirements_v1/case_requirements.csv'
    reqs=list(csv.DictReader(read(reqpath).decode().splitlines()))
    case_ids=sorted({t['case_id'] for t in tasks})
    included=[r for r in reqs if r['included']=='Yes' and r['case_id'] in case_ids]
    assert len(included)==119
    for path in [BASE+'rubric_v2_draft/RUBRIC.md',BASE+'rubric_v2_draft/EXAMPLES.md',
        BASE+'three_rater_review_v1/DISCUSSION_RULES_LOG.json',
        BASE+'three_rater_review_v1/personal_rechecks/RECHECK_INSTRUCTIONS.md',
        'src/llm/formal_providers.py','src/llm/compatibility_check.py','src/llm/formal_generation.py',
        'scripts/prepare_repeatability_supplement.py']:
        read(path)
    historical_rates=original['reservation_usd_per_attempt']
    historical_reservation=sum(Decimal(str(historical_rates[t['provider']])) for t in tasks)
    runtime={p:version(p) for p in original['sdk_versions']}
    plan={
        'version':'repeatability-supplement-v1-planning','status':'Design prepared; reviewer capacity and execution release pending',
        'user_scope_confirmation':'Cover all 25 original stroke cases; three additional generations per model as proposed in conversation',
        'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'study_role':'Supplement designed after the original results were known; no retrospective preregistration claim',
        'participants':25,'cohort':'stroke','models':3,'new_repeats_per_case_model':3,'planned_reports':225,
        'historical_reports_retained':105,'total_reports_if_all_new_slots_complete':330,
        'schedule_seed':SEED,'schedule_policy':'Three waves, one new response per case-model per wave; shuffle cases; rotate provider positions within each case across waves',
        'analysis_basis':'New three-response blocks are primary for repeatability; original response is a separate historical comparison',
        'live_output_directory':'data/reports_repeatability_v1',
        'live_execution_authorized_by_this_file':False,'executable_with_historical_runner':False,
        'generation_policy':{'input_changes':False,'length_prompt_changes':False,'new_model_substitution':False,
          'output_allowance_tokens':16000,'reasoning':'Historical provider-specific high/adaptive settings unchanged',
          'max_attempts_per_slot':3,'max_total_attempts':675,'attempt_deadline_seconds':600,
          'retry_scope':'Only established transient transport failures with no usable captured report; retain first captured text including partial, refusal or truncated text',
          'unresolved_request_state':'Pause for technical review; never silently redispatch an ambiguous interrupted request'},
        'historical_reservation_only':{'rates_usd_per_attempt':historical_rates,'one_attempt_each_usd':float(historical_reservation),
          'three_attempts_each_usd':float(historical_reservation*3),'current_prices_verified':False,
          'billing_limit_approved':False,'note':'Arithmetic using historical reservations, not a current quote or invoice; set a concrete execution budget before calls'},
        'review_plan':{'proposed_raters':3,'assignments_each':225,'assignments_total':675,
          'case_coverage_rows_each':1071,'reference_limit_rows_each':225,'all_coverage_rows_each':1296,
          'capacity_confirmed':False,'independent_first_pass_primary':True,
          'prior_case_familiarity_expected':True,'current_model_identity_exposure_confirmed':False},
        'sdk_versions_original':original['sdk_versions'],'sdk_versions_installed':runtime,
        'sdk_versions_match':runtime==original['sdk_versions'],
        'current_provider_access_tested':False,'historical_snapshot_equivalence_established':False,
        'source_sha256':sources,'case_ids':case_ids,'tasks':tasks}
    protocol='''# Repeated-generation supplement: all 25 stroke cases

Status: prepared before new outputs, after the original study results were known. The study lead selected all 25 original stroke cases and three additional responses per case and model. Expert capacity, prospective application of the review instructions, and technical/budget release remain to be confirmed. This file does not claim an expert signature, model access check or completed experiment.

## Question and scope

How much do required-content coverage and evidence-fidelity judgments vary across repeated responses to the same gait summary under the same recorded configuration? Include every original stroke case, with no selection based on model performance. Generate 25 x 3 models x 3 new responses = 225 reports. Each model contributes 75 new reports. The original 75 stroke and 30 control reports remain historical evidence. If every new slot yields a report, the project contains 330 reports, including 300 stroke reports, but still only 25 independent stroke participants. No new control generation is planned.

The supplement is exploratory and was designed after seeing the original results. It is not a new external validation set or a remedy for an unvalidated clinical reference. It estimates variability on the existing selected cases. Do not claim a powered sample size, adequate precision for rare errors or population-wide rankings.

## Input and generation

Use the exact original system/user bytes and recorded high/adaptive 16,000-token configuration for each provider. Do not add length constraints, examples, prior reports, expert feedback, case requirements, retrieval or conversational memory. Start each call independently. Temperature and other omitted sampling settings remain omitted; do not introduce a fixed seed that artificially repeats one draw. Record any available returned model version, request identifier, time, usage, finish reason and stream evidence.

PLAN.json specifies every slot, prompt hash and original task. Dispatch three complete waves, each containing one response from each model for all 25 participants. Case ordering is seeded and provider positions rotate, so each provider occupies each position once per participant across the three waves. Operational pauses are allowed and logged; order and output selection cannot depend on report quality.

Verify available model identifiers, installed SDKs and effective requests before release. The original API identifier alone does not establish an unchanged backend snapshot. No silent model substitution is allowed. The primary supplement compares the three new responses with one another. Compare original versus new responses separately and label possible temporal/service drift. Even the new waves can span provider updates; preserve returned metadata and disclose unobservable changes.

Do not reuse the original live runner, authorization or report directory. The planned directory is data/reports_repeatability_v1. New task IDs cannot collide with historical IDs. A dedicated runner must preserve streams durably, validate source/configuration identity on resume, and retain every first usable response. Poor, cautious, malformed, refused or truncated text is not a reason to regenerate. Retries are limited to the original transient transport policy, at most three attempts per slot, with 600-second attempt deadlines. Interrupted ambiguous requests pause for review. No extra clinical-input probe outside the registered slots is included.

## Human scoring

The proposed design uses all three human reviewers independently for all 225 new reports: 675 report-review assignments. Each reviewer has 1,071 case-requirement judgments and 225 separate reference-limit judgments, plus error review. Confirm capacity before generating this workload.

Use the existing 119 stroke requirements, the approved rubric and the substantive D01-D03 clarifications from the outset. Prepare a concise prospective instruction pack before scoring; distinguish agreed general rules from unresolved historical case interpretations. Do not convert any reviewer's preferred reading, later individual decision or historical consensus into an automatic answer key for a new report. Pending remains available. Existing historical case labels are not shown in the new packets.

Use opaque report IDs, concealed provider/repetition metadata and separately randomized reading orders. Separate reports from the same case as far as feasible; distribute manageable batches without showing peer judgments. Collect current model-identity/results exposure and case-familiarity declarations. Prior experience with the cases and rules is expected, so these are new independent judgments on new reports, not ratings by naive reviewers. Do not promise blinding if a reviewer has already seen the identities/results.

Each reviewer retains an independent coverage and error dataset. New first-pass judgments are the primary rating basis for this supplement, reported separately for each reviewer. Later discussion, if undertaken, is secondary and does not overwrite those results or force agreement. No new wording rule may be presented as having preceded scoring if it was created after outputs were inspected.

## Analysis specified before new outputs

For participant i, model m, repeat r and reviewer h, compute full coverage C_imrh as the number of case requirements marked Covered divided by the fixed case-specific K_i. Partially covered receives no fractional credit. Reference-limit coverage remains separate. Report category frequencies as well as binary full coverage. An unassessed or unresolved item is unknown, not a model omission.

The principal repeatability statistic is the participant mean of the absolute difference between each of the three new-response pairs: V_imh = (abs(C_im1h-C_im2h) + abs(C_im1h-C_im3h) + abs(C_im2h-C_im3h))/3. Average V_imh equally across participants within each model and reviewer and express it in percentage points. Also report each participant's three observed scores, range and mean coverage. Zero variability can mean consistently poor reports; always interpret variation with the coverage level.

For each reviewer, report known positive, known negative and unknown any-error status for every new report. Positive means at least one judged in-scope Error; negative requires completed issue review with no Error or Pending; otherwise unknown. Do not call an individual reviewer's Error a unanimous confirmed error. Show error status patterns across the three repeats and the participant-level proportion of discordant response pairs, averaging cases equally. Use complete three-response blocks for observed repeatability summaries, disclose exclusions and retain unknowns in bounds. Never combine positive and Pending states.

Report per-reviewer results side by side; do not average away disagreement or pool 675 assignments as independent observations. Human agreement is a separate endpoint using raw agreement, cross-tabulations and the original pairwise nominal kappa conventions. AC1 may be reported as a predeclared supplementary coefficient for this new stage, alongside kappa and category marginals. Agreement is not correctness.

For each complete-block repeatability statistic use 20,000 percentile bootstrap samples of participants within this stroke cohort, seed 20260925, retaining all models, repeats, items and reviewer labels within each sampled participant. Keep the analysis draws and category definitions fixed. Report 95% intervals as descriptive uncertainty, without confirmatory p-values or superiority/equivalence claims. These cluster intervals describe participant-sample variation conditional on the observed three responses; they do not precisely estimate the full stochastic distribution of future outputs. With fewer than two complete participant blocks, no interval is reported. Constant bootstrap values are identified rather than presented as proof of zero uncertainty.

Report every model's available complete blocks and denominators. Any secondary between-model contrast uses the same participants with complete three-response coverage for both compared models, with equal participant weighting; show all planned-case bounds as a missingness sensitivity. Do not substitute the old response to complete a missing new block. For unknown coverage items, report report-level bounds [known Covered/K_i, (known Covered + unknown)/K_i] and case/model mean bounds across all three planned repeats. For any-error rates, count unknown report states as zero and one for bounds across all 75 new slots per model and reviewer. For repeat-pair discordance, known differing binary states contribute one, known equal states zero, and any pair with an unknown state contributes [0,1]; average all three pair bounds per case and then all 25 cases. Such bounds are not confidence intervals. Coverage-variability bounds need not be inferred from coverage-mean bounds; leave that variability estimate unavailable for incomplete blocks.

Do not calculate ordinary independent-binomial intervals using 75 reports as 75 independent participants. Error-group counts remain report-scoped and unweighted. Report lengths are descriptive, using the existing whitespace-count rule; no per-word correction is claimed to remove length confounding. No new severity scale, composite ranking, subgroup search or best-of-three response selection is introduced.

## Remaining steps before live release

1. Confirm the human scoring arrangement and workload; assemble and review the prospective instructions without new model outputs.
2. Implement a separate bounded runner and verify interruption/resume, first-response retention, transient retry accounting and exact prompt/configuration capture offline.
3. Check current provider access and version information, determine a concrete spending limit and record any service differences. Synthetic checks, if needed, require their own bounded scope; do not spend extra clinical calls outside these 225 slots.
4. Fix the dated supplement and exact execution manifest before dispatch. Record the study lead's concrete execution decision; do not reuse the original batch authorization. The choice of 25 cases has been accepted, but this offline planning file is not a transmitted-call authorization.
5. Generate, blind, independently rate, then analyze with the above definitions. Report deviations and missing outputs without replacing cases or selectively discarding responses.
'''
    readme='''# Repeated-generation supplement planning package

Scope chosen: all 25 original stroke participants, three additional generations per model, 225 new report slots. See [the protocol](PROTOCOL.md), [task inventory](TASKS.csv), [plan](PLAN.json) and [offline checks](OFFLINE_CHECKS.json).

This is researcher planning material with visible model identities; do not send it as a blinded rating packet. It contains no new model outputs or expert signatures. Current provider access, backend version equivalence and spending authorization have not been established. The historical runner cannot execute this manifest. Model calls performed by this preparation: zero.

The proposed three-rater arrangement means 225 reports and 1,296 coverage judgments per person, plus issue review. Capacity remains a required human input. The actual prepared scope is three NEW responses for every case-model pair, not two new responses and one old response.

Historical cost reservations imply USD 127.80 for one attempt at all new slots, or USD 383.40 if every slot required all three allowed attempts. These are arithmetic scenarios using old reservations, not current prices, expected spending, a provider billing cap or approved expenditure. Technical readiness and a concrete spending limit must be settled before release.

Original reports, rating submissions, manuscript results and author approvals are unchanged. Prepare future versions in a new directory; the builder refuses to overwrite this package.
'''
    checks={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'status':'Offline planning checks passed; live readiness pending',
       'cases':25,'slots':225,'models':3,'new_repeats':3,'exact_original_prompt_files_verified':50,
       'original_plan_matches_completion_digest':True,'stroke_requirements':119,
       'unique_new_ids':True,'historical_id_collisions':False,'parameters_match_original':True,
       'provider_position_counts':{p:dict(Counter(t['provider_position_within_case'] for t in tasks if t['provider']==p)) for p in PROVIDERS},
       'sdk_versions_match':plan['sdk_versions_match'],'model_calls':0,
       'current_provider_access_verified':False,'human_capacity_confirmed':False,'dedicated_runner_ready':False,
       'original_outputs_modified':False,'plan_sha256':digest(plan)}
    output.mkdir(parents=True,exist_ok=False)
    def write(name,obj):
        with (output/name).open('x') as f:f.write(json.dumps(obj,indent=2)+'\n')
    write('PLAN.json',plan);write('OFFLINE_CHECKS.json',checks)
    (output/'PROTOCOL.md').write_text(protocol);(output/'README.md').write_text(readme)
    with (output/'TASKS.csv').open('x',newline='') as f:
        keys=['sequence','slot_id','case_id','provider','model','repeat','provider_position_within_case','original_slot_id','input_pair_sha256']
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(tasks)
    for path,h in sources.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
    write('BUILD_RECORD.json',{'source_sha256':sources,'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()},'model_calls':0,'new_expert_approvals':False})
    print(json.dumps({'output':str(output),'cases':25,'new_reports':225,'coverage_rows_per_rater':1296,'historical_one_attempt_reservation_usd':float(historical_reservation),'model_calls':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT)
    main(parser.parse_args().output)
