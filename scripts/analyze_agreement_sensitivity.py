"""Add post-hoc AC1 without changing the original agreement analysis or ratings."""
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.eval.agreement_sensitivity import analyze_original_agreement


def main():
    origin=ROOT/'docs/formal_study/three_rater_analysis_v1'
    out=ROOT/'docs/formal_study/agreement_sensitivity_v1'
    record=json.loads((origin/'AGREEMENT_BUILD_RECORD.json').read_text())
    sources={}
    def read(name,expected=None):
        raw=(ROOT/name).read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        if expected and digest!=expected: raise ValueError('Changed source: '+name)
        sources[name]=digest
        return raw
    read(str((origin/'AGREEMENT_BUILD_RECORD.json').relative_to(ROOT)))
    for name,digest in record['source_sha256'].items(): read(name,digest)
    for name,digest in record['output_sha256'].items(): read(str((origin/name).relative_to(ROOT)),digest)
    roster={}
    with (ROOT/'docs/formal_study/case_requirements_v1/case_requirements.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if row['included']=='Yes':
                case=row['case_id'];roster.setdefault(case,{'group':case.split('_')[0],'required_ids':[]})['required_ids'].append(row['record_id'])
    reviews={}
    for who in ('rater1','rater2','rater3'):
        wb=load_workbook(ROOT/f'docs/formal_study/three_rater_review_v1/private/{who}_submitted.xlsx',read_only=True,data_only=False)
        review={'rater':who,'stage':'original_independent'}
        for name in ('Review','Coverage','Issues'):
            rows=iter(wb[name].values);headers=next(rows)
            review[name.lower()]=[dict(zip(headers,row)) for row in rows if any(v is not None for v in row)]
        reviews[who]=review;wb.close()
    result=analyze_original_agreement(reviews,roster)
    # Independent exact-arithmetic check of every point estimate.
    for r in result['rows']:
        x=r['cross_tabulation'];n=r['assessable'];q=len(x)
        if n:
            ps=[Fraction(sum(x[k])+sum(row[k] for row in x),2*n) for k in range(q)]
            pe=sum(p*(1-p) for p in ps)/(q-1)
            pa=Fraction(sum(x[k][k] for k in range(q)),n)
            assert abs(float((pa-pe)/(1-pe))-r['ac1'])<1e-12
    for name in ('scripts/analyze_agreement_sensitivity.py','src/eval/agreement_sensitivity.py'):read(name)
    if out.exists():
        previous=json.loads((out/'BUILD_RECORD.json').read_text())
        if previous['source_sha256']!=sources:raise ValueError('Changed inputs require a new analysis version')
        for name,digest in previous['output_sha256'].items():
            if hashlib.sha256((out/name).read_bytes()).hexdigest()!=digest:raise ValueError('Do not overwrite edited outputs')
    out.mkdir(exist_ok=True)
    (out/'AC1_ANALYSIS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    rows=[{k:r[k] for k in ('pair','cohort','domain','planned','assessable','excluded','participants','raw_agreement','kappa','ac1','percentile_95','constant_pooled_labels')} for r in result['rows']]
    with (out/'AC1_SUMMARY.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines=['# Supplementary original-rating agreement analysis','','This post-hoc sensitivity analysis was authorized after inspection of the existing results. It uses the preserved original independent ratings, not final discussion outcomes. No report, score, category or original exclusion was changed. All 18 original cross-tabulations were reproduced.','',
           'Nominal AC1 = (Pa - Pe)/(1 - Pe), where Pa is observed agreement, Pe = sum[p_k(1-p_k)]/(q-1), and p_k is the mean of the two raters\' marginal proportions. The fixed rubric has q=3 for coverage (including reference limitations) and q=2 for any-error. Categories are not dropped when absent. Point estimates retain the original item/report weighting.','',
           'Exploratory 95% percentile intervals use 20,000 participant-cluster bootstrap samples, seed 20260925. Each draw retains all reports, items and exclusions for the sampled participant; 25 stroke and 10 control participants are sampled within their respective cohorts. These intervals do not address shared-reference dependence or selected sampling. Empty replicates are reported as undefined, never converted to zero.','',
           '| Pair | Cohort | Domain | Assessed/planned | Agreement | Kappa | AC1 | Cluster 95% interval |',
           '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in result['rows']:
        ci=r['percentile_95'];k='Undefined' if r['kappa'] is None else f"{r['kappa']:.3f}"
        lines.append(f"| {r['pair']} | {r['cohort']} | {r['domain']} | {r['assessable']}/{r['planned']} | {r['raw_agreement']:.1%} | {k} | {r['ac1']:.3f} | {ci[0]:.3f} to {ci[1]:.3f} |")
    lines+=['','AC1 is not a replacement for kappa or evidence that a disputed judgment is correct. Interpret both coefficients with raw agreement, marginal distributions and excluded rows. No qualitative kappa bands are applied to AC1. A constant-label AC1 of 1 and interval [1,1] cannot establish discrimination outside the observed category. Different reviewer pairs may evaluate different report subsets. No pair is ranked and no significance tests compare coefficients.','',
            'References: [Gwet, 2008](https://doi.org/10.1348/000711006X126600); [Vach and Gerke, 2023](https://pubmed.ncbi.nlm.nih.gov/37234937/).','']
    (out/'README.md').write_text('\n'.join(lines))
    for name,digest in sources.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name!='BUILD_RECORD.json'}
    (out/'BUILD_RECORD.json').write_text(json.dumps({'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_sha256':sources,'output_sha256':outputs,'point_estimates_checked_with_exact_fractions':True,
        'original_ratings_changed':False,'original_cross_tabs_reproduced':True,'model_mapping_read':False,'post_feedback_ratings_used':False},indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
