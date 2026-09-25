"""Assemble current post-feedback rater positions and a blinded discussion workbook.

Original independent ratings remain unchanged. No majority vote, automated clinical
adjudication or model identity mapping is used. Source quotations remain verbatim.
"""
from pathlib import Path
from copy import deepcopy
import re,json,hashlib,collections
import openpyxl
P=Path(__file__).resolve().parents[1];ROOT=P/'docs/formal_study/three_rater_review_v1';D=ROOT/'personal_rechecks'
def records(s):
 rows=list(s.values);return [dict(zip(rows[0],r),excel_row=n) for n,r in enumerate(rows[1:],2) if any(v is not None for v in r)]
def read(path):return openpyxl.load_workbook(path,data_only=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={};data={};positions={}
def source(path):sources[str(path.relative_to(P))]=sha(path);return read(path)
for who in ['rater1','rater2']:
 original=source(ROOT/f'private/{who}_submitted.xlsx');personal=source(D/who/f'Personal_recheck_{who}_completed.xlsx');target=source(D/who/f'Targeted_review_items_{who}_completed_v2.xlsx')
 data[who]={name:records(original[name]) for name in ['Review','Coverage','Issues']}
 for sn in ['Coverage','Issues']:
  for r in data[who][sn]:r['last_source']=f'private/{who}_submitted.xlsx | {sn} {r["excel_row"]}'
 cov={(r['report_id'],r['requirement_id']):r for r in data[who]['Coverage']};issues={(r['report_id'],r['issue_id']):r for r in data[who]['Issues']}
 for r in records(personal['Coverage recheck']):
  t=cov[r['Report ID'],r['Requirement ID']]
  if r['Action']=='Revise':
   if r['Revised decision']:t['decision']=r['Revised decision']
   if r['Revised status']:t['adjudication_status']=r['Revised status']
  elif r['Action']=='Unresolved':t['adjudication_status']='Pending adjudication'
  if r['Reason and source evidence']:t['evidence_and_reason']=r['Reason and source evidence']
  t['last_source']=f'{who}/Personal_recheck_{who}_completed.xlsx | Coverage recheck {r["excel_row"]}'
 for r in records(personal['Question issue recheck']):
  t=issues[r['Report ID'],r['Your issue ID']]
  if r['Action']=='Revise':
   for old,new in [('Revised decision','decision'),('Revised categories','categories'),('Revised exact quote','exact_quote'),('Revised locations','locations'),('Revised pathology flag','pathology_flag'),('Revised normality flag','normality_flag')]:
    if r[old] is not None:t[new]=r[old]
  elif r['Action']=='Unresolved':t['decision']='Pending adjudication'
  if r['Reason']:t['reason']=r['Reason']
  t['last_source']=f'{who}/Personal_recheck_{who}_completed.xlsx | Question issue recheck {r["excel_row"]}'
 for r in records(personal['Additional findings']):
  key=r['Report ID'],r['Existing issue ID or new local ID']
  t=issues.get(key,dict(report_id=key[0],issue_id=key[1]))
  for old,new in [('Decision','decision'),('Categories','categories'),('Exact quote','exact_quote'),('Locations','locations'),('Reason','reason'),('Pathology flag','pathology_flag'),('Normality flag','normality_flag')]:t[new]=r[old]
  if key not in issues:data[who]['Issues'].append(t);issues[key]=t
  t['last_source']=f'{who}/Personal_recheck_{who}_completed.xlsx | Additional findings {r["excel_row"]}'
 if 'Quote corrections' in personal:
  for r in records(personal['Quote corrections']):
   t=issues[r['Report ID'],r['Your issue ID']]
   if r['Corrected exact quote']:t['exact_quote']=r['Corrected exact quote']
   if r['Corrected locations']:t['locations']=r['Corrected locations']
   t['quote_source']=f'{who}/Personal_recheck_{who}_completed.xlsx | Quote corrections {r["excel_row"]}'
 positions[who]=records(target['Review items'])
 if who=='rater1':
  lookup={r['Review ID']:r for r in positions[who]}
  for r in records(target['Disposition index']):
   rid=r['Report ID'];ref=r['Review IDs'].split(';')[0].strip();result=r['Result after this review'];label=r['Record']
   if label in ['G03','R038']:
    t=cov[rid,label];t.update(decision=result,adjudication_status=r['Category or status'],evidence_and_reason=r['Reason / scope'],last_source=f'{who}/Targeted_review_items_{who}_completed_v2.xlsx | Disposition index {r["excel_row"]}');continue
   match=re.match(r'I\d+',label)
   if not match:continue # Explicit no-new-issue responses stay in the position table, not invented issue records.
   key=rid,match.group();t=issues.get(key,dict(report_id=rid,issue_id=key[1],pathology_flag=None,normality_flag=None))
   if key not in issues:
    t['exact_quote']='medial gastrocnemius (GAS)' if ref=='A035' else lookup[ref]['Exact quote or located evidence'];t['locations']=f'Report line {lookup[ref]["Report line"]}'
    issues[key]=t;data[who]['Issues'].append(t)
   if ref=='A022':t['exact_quote']='the mean envelope below threshold between the retained interval endpoints at 34% and 44%';t['locations']='Section 2, report line 52 (ERS location claim only)'
   t.update(decision=result,categories='' if r['Category or status']=='No error category' else r['Category or status'],reason=r['Reason / scope'],last_source=f'{who}/Targeted_review_items_{who}_completed_v2.xlsx | Disposition index {r["excel_row"]}',decision_reference=r['Review IDs'])
  for r in records(target['Sub62 linked issues']):
   t=issues[r['Report ID'],r['Issue ID']];t.update(exact_quote=r['Exact report quote'],locations=r['Locations'],reason=r['Reason'],categories=r['Category'],decision=r['Decision'],linked_issue=r['Linked issue'])
 else:
  for r in records(target['Rater2 revised records']):
   key=r['report_id'],r['issue_id'];t=issues.get(key,dict(report_id=key[0],issue_id=key[1]))
   if key not in issues:data[who]['Issues'].append(t);issues[key]=t
   for field in ['decision','categories','exact_quote','locations','pathology_flag','normality_flag','reason']:t[field]=r[field]
   t.update(last_source=f'{who}/Targeted_review_items_{who}_completed_v2.xlsx | Rater2 revised records {r["excel_row"]}',decision_reference=r['review_ids'])
  for r in records(target['Rater2 coverage changes']):
   t=cov[r['report_id'],r['requirement_id']];assert t['decision']==r['previous_decision'];t.update(decision=r['revised_decision'],adjudication_status=r['adjudication_status'],evidence_and_reason=r['reason'],last_source=f'{who}/Targeted_review_items_{who}_completed_v2.xlsx | Rater2 coverage changes {r["excel_row"]}')
# A retained coverage label can still have a newer, more specific explanation.
# Preserve those explicit Keep reasons instead of displaying the earlier generic text.
for reply in positions['rater2']:
 if reply['Reviewer action']!='Keep':continue
 ref=reply['Review ID']
 if ref.startswith('C'):
  key=reply['Report ID'],reply['Issue or requirement']
 elif ref=='D029':
  key=reply['Report ID'],'R038'
 else:continue
 current=next(r for r in data['rater2']['Coverage'] if (r['report_id'],r['requirement_id'])==key)
 current['evidence_and_reason']=reply['Reviewer reason']
 current['last_source']=f'rater2/Targeted_review_items_rater2_completed_v2.xlsx | Review items {reply["excel_row"]}'
final3=source(P/'outputs/rater3_independent/Final_ratings_rater3.xlsx');data['rater3']={sn:records(final3[sn]) for sn in ['Review','Coverage','Issues']}
for sn in ['Coverage','Issues']:
 for r in data['rater3'][sn]:r['last_source']=f'outputs/rater3_independent/Final_ratings_rater3.xlsx | {sn} {r["excel_row"]}'
positions['rater3']=[]
covkeys=None
texts={};cases={}
for who,d in data.items():
 assert len(d['Coverage'])==552 and len(d['Review'])==105
 keys={(r['report_id'],r['requirement_id']) for r in d['Coverage']}
 if covkeys is None:covkeys=keys
 else:assert keys==covkeys
 assert len({(r['report_id'],r['issue_id']) for r in d['Issues']})==len(d['Issues'])
 for r in d['Review']:cases[r['report_id']]=r['case_id']
 for r in d['Issues']:
  rid=r['report_id']
  if rid not in texts:texts[rid]=(P/f'data/rating_packets_formal_v1/raters/rater1/reports/{rid}.txt').read_text()
  assert r['exact_quote'] in texts[rid],(who,rid,r['issue_id'],r['exact_quote'])
  r['quote_start']=texts[rid].index(r['exact_quote']);r['quote_end']=r['quote_start']+len(r['exact_quote']);r['report_line']=texts[rid][:r['quote_start']].count('\n')+1
  r['record_key']=f'{who}|{rid}|{r["issue_id"]}'
  if r['decision']=='Pending adjudication':r['adjudication_status']='Pending adjudication'
  elif 'adjudication_status' not in r:r['adjudication_status']='Rater position; not common adjudication'
summary={who:{'coverage':dict(collections.Counter(r['decision'] for r in d['Coverage'])),'issues':dict(collections.Counter(r['decision'] for r in d['Issues']))} for who,d in data.items()}
coverage_maps={who:{(r['report_id'],r['requirement_id']):r for r in d['Coverage']} for who,d in data.items()}
diff=[]
for key in sorted(covkeys):
 vals=[coverage_maps[who][key]['decision'] for who in data]
 if len(set(vals))>1:diff.append((key,vals))



# Produce one current discussion workbook; preserve all independent source files.
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
OUT=P/'docs/formal_study/three_rater_discussion_v2'
OUT.mkdir(parents=True,exist_ok=True)
target=OUT/'Three_rater_discussion.xlsx'
if target.exists():
 existing=read(target)
 for s in existing:
  heads=list(next(s.values));cols=[n for n,h in enumerate(heads) if h in ['Common decision','Discussion reason','Confirmed by','Confirmation date','Human claim group']]
  for row in list(s.values)[1:]:
   if any(row[n] is not None for n in cols):raise RuntimeError('Existing workbook contains human discussion fields; do not overwrite it.')
RATERS=('rater1','rater2','rater3')
wb=openpyxl.Workbook();wb.remove(wb.active)
def sheet(name,heads,rows,decision_options=None):
 s=wb.create_sheet(name);s.append(heads)
 for row in rows:s.append(row)
 s.freeze_panes='D2' if len(heads)>4 else 'A2';s.auto_filter.ref=s.dimensions
 for c in s[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='244760');c.alignment=Alignment(wrap_text=True)
 for col in s.columns:
  title=str(col[0].value).lower();wide=any(x in title for x in ['reason','quote','evidence','context','wording','components','instructions','position','source'])
  s.column_dimensions[col[0].column_letter].width=65 if wide else 24
  for c in col[1:]:
   if isinstance(c.value,str):
    if len(c.value)>32767:raise ValueError((name,c.coordinate,'Excel text limit'))
    c.data_type='s'
   c.alignment=Alignment(wrap_text=True,vertical='top')
 if decision_options and 'Common decision' in heads and s.max_row>1:
  col=get_column_letter(heads.index('Common decision')+1)
  dv=DataValidation(type='list',formula1='"'+','.join(decision_options)+'"',allow_blank=True);s.add_data_validation(dv);dv.add(f'{col}2:{col}{s.max_row}')
 return s
blank=['Common decision','Discussion reason','Confirmed by','Confirmation date']
# Actual coverage disagreements, using the latest effective labels.
coverage_rows=[];coverage_all=[]
ch=['Report ID','Case ID','Requirement','Required wording','Components']
for who in RATERS:ch += [f'{who} decision',f'{who} status',f'{who} reason',f'{who} source']
ch+=blank
for key in sorted(covkeys):
 base=coverage_maps['rater1'][key];row=[key[0],base['case_id'],key[1],base['required_wording'],base['components']]
 for who in RATERS:
  r=coverage_maps[who][key];assert r['required_wording']==base['required_wording'] and r['components']==base['components'];row += [r['decision'],r['adjudication_status'],r['evidence_and_reason'],r['last_source']]
 row += ['']*4;coverage_all.append(row)
 if len({coverage_maps[who][key]['decision'] for who in RATERS})>1 or any(coverage_maps[who][key]['adjudication_status']!='Final' for who in RATERS):coverage_rows.append(row)
sheet('Coverage discussion',ch,coverage_rows,['Covered','Partially covered','Not covered','Unresolved'])
# Review-item positions are explicit post-feedback responses, not inferred from an absent issue.
lookup={who:{r['Review ID']:r for r in positions[who]} for who in ['rater1','rater2']}
audit=source(D/'RATER1_RATER2_DETAILED_AUDIT.xlsx')
base_disc={r['Audit ID']:r for r in records(audit['Discussion needed'])}
issue_list=[dict(r,rater=who) for who in RATERS for r in data[who]['Issues']]
def matches(rid,q,who):
 text=texts[rid];spans=[];start=0
 while True:
  k=text.find(q,start)
  if k<0:break
  spans.append((k,k+len(q)));start=k+1
 found=[]
 for r in data[who]['Issues']:
  if r['report_id']!=rid:continue
  if any(a<r['quote_end'] and r['quote_start']<b for a,b in spans):found.append(r)
 return found
r2_pending={'D010','D014','D015','D016','D024'}
r2_error={'D005','D006','D011','D012','D013','D017','D018','D019','D020','D021','D022','D023','D026'}
r3_ref={'D031':'E026','D032':'E036'}
interpret=[];checked=[];covered_keys=set()
ph=['Discussion ID','Report ID','Case ID','Topic','Exact anchor quote','Report line','Scope note']
for who in RATERS:ph += [f'{who} position',f'{who} reason',f'{who} source']
ph+=blank
for ref,r in base_disc.items():
 if ref in ['D028','D029']:continue # These coverage requirements now agree in all three returns.
 rid=r['Report ID'];q=r['Exact report quote']
 p1=lookup['rater1'][ref];p2=lookup['rater2'][ref]
 m=re.search(r'= (Pending adjudication|Acceptable|Error|No issue added)',p1['Reviewer reason']);assert m,ref
 v1=m.group(1);v1='Acceptable' if v1=='No issue added' else v1
 v2='Pending adjudication' if ref in r2_pending else 'Error' if ref in r2_error else 'Acceptable'
 rs3=[x for x in data['rater3']['Issues'] if x['report_id']==rid and x.get('decision_reference')==r3_ref.get(ref,ref)]
 if not rs3:rs3=matches(rid,q,'rater3')
 assert len(rs3)==1,(ref,'rater3 record scope',len(rs3))
 v3=rs3[0]['decision']
 topic='Continuity and retained-interval wording' if ref in ['D001','D002','D004','D005','D006','D007','D008','D011','D012','D013','D025','D026'] else 'Non-exceedance versus a strict below-threshold segment' if ref in ['D031','D032'] else 'Degree words and severity' if ref in ['D014','D015','D016','D017'] else 'Prolonged: descriptive extent or abnormal timing' if ref in ['D020','D021','D022','D023'] else 'Observed limits: excursion or established restriction' if ref in ['D009','D018','D019'] else 'Normalization intervention and mathematical premise' if ref in ['D010','D027','D030'] else 'Clinical phase question and significance wording' if ref=='D024' else 'Inline correction of a pair label' if ref=='D033' else 'Scope of supplied-reference comparisons'
 reasons=[p1['Reviewer reason'],p2['Reviewer reason'],rs3[0]['reason']]
 vals=[v1,v2,v3]
 row=[ref,rid,cases[rid],topic,q,r['Report line'],'Positions apply to the quoted claim; shared source sentences can contain other independently assessable claims.']
 for who,val,reason in zip(RATERS,vals,reasons):
  source_text=(f'{who}/Targeted_review_items_{who}_completed_v2.xlsx | Review items '+str(lookup[who][ref]['excel_row'])) if who!='rater3' else rs3[0]['last_source']
  row += [val,reason,source_text]
 row+=['']*4
 checked.append((ref,vals))
 if len(set(vals))>1 or 'Pending adjudication' in vals or any('unresolved' in str(x.get('adjudication_status','')).lower() for x in rs3):interpret.append(row)
 for who in RATERS:
  for x in matches(rid,q,who):covered_keys.add(x['record_key'])
# Three explicit retained disagreements from the A rows.
for ref,rid,quote,topic,r3code,r1iid in [
 ('A002','RDEBA7F747795D5A2','Because that value is close to the 10.7 boundary and is displayed at rounded precision, it should be described as near that boundary rather than assigned to either side of it with confidence.','Numerical ordering versus classification caution','E003','I003'),
 ('A003','REB63B5C959B61142','100% of the cycle above threshold (no below-threshold segment detected)','Detected interval list versus a no-gap claim','E006','I001'),
 ('A009','REB162D9F656B2188','leave-one-out limits would be wider still.','Unsupported reference claim versus methodological caution','E021',None)]:
 rs1=matches(rid,quote,'rater1') if r1iid is None else [x for x in data['rater1']['Issues'] if x['report_id']==rid and x['issue_id']==r1iid]
 rs3=[x for x in data['rater3']['Issues'] if x['report_id']==rid and x.get('decision_reference')==r3code];assert len(rs1)==len(rs3)==1
 rs2=matches(rid,quote,'rater2');r2rec=next((x for x in rs2 if ref in x.get('decision_reference','')),None)
 v2=r2rec['decision'] if r2rec else 'Acceptable'
 row=[ref,rid,cases[rid],topic,quote,texts[rid][:texts[rid].index(quote)].count('\n')+1,'Rater2 position is explicitly stated in the targeted response; absence of a new issue is not used as an inferred label.']
 row += [rs1[0]['decision'],rs1[0]['reason'],rs1[0]['last_source'],v2,lookup['rater2'][ref]['Reviewer reason'],f'rater2/Targeted_review_items_rater2_completed_v2.xlsx | Review items {lookup["rater2"][ref]["excel_row"]}',rs3[0]['decision'],rs3[0]['reason'],rs3[0]['last_source']]+['']*4
 interpret.append(row)
 for who in RATERS:
  for x in matches(rid,quote,who):covered_keys.add(x['record_key'])
sheet('Interpretation discussion',ph,interpret,['Error','Acceptable','Pending adjudication','Out of scope','Unresolved'])
# Include every currently pending record, including ten rater1 records outside the focused response list.
pending_rows=[]
ih=['Record key','Rater','Report ID','Case ID','Local issue ID','Current decision','Categories','Exact quote','Report line','Locations','Reason','Pathology flag','Normality flag','Adjudication status','Source','Quoted-scope note']
all_issue_rows=[]
for r in issue_list:
 row=[r['record_key'],r['rater'],r['report_id'],cases[r['report_id']],r['issue_id'],r['decision'],r.get('categories'),r['exact_quote'],r['report_line'],r['locations'],r['reason'],r.get('pathology_flag'),r.get('normality_flag'),r['adjudication_status'],r['last_source'],'Use claim meaning, not local issue ID or report-level record count, for alignment.']
 all_issue_rows.append(row)
 if r['decision']=='Pending adjudication' or 'unresolved' in str(r['adjudication_status']).lower():pending_rows.append(row+['']*4)
sheet('All pending records',ih+blank,pending_rows,['Error','Acceptable','Pending adjudication','Out of scope','Unresolved'])
# A complete quote-overlap inventory catches candidates not represented in the focused discussion.
# It is deliberately not an automatic claim merger or a count of confirmed disagreements.
byreport=collections.defaultdict(list)
for r in issue_list:byreport[r['report_id']].append(r)
clusters=[]
for rid,rs in sorted(byreport.items()):
 current=[];end=-1
 for r in sorted(rs,key=lambda x:(x['quote_start'],x['quote_end'])):
  if current and r['quote_start']>=end:clusters.append((rid,current));current=[];end=-1
  current.append(r);end=max(end,r['quote_end'])
 if current:clusters.append((rid,current))
ah=['Candidate group','Report ID','Case ID','Alignment status','Source context']
for who in RATERS:ah += [f'{who} candidate records',f'{who} quoted positions and reasons']
ah += ['Human claim group']+blank
alignment=[];alignment_counts=collections.Counter()
for n,(rid,rs) in enumerate(clusters,1):
 per={who:[r for r in rs if r['rater']==who] for who in RATERS};labels={r['decision'] for r in rs}
 if any(len(v)>1 for v in per.values()):status='Multiple scopes in an overlapping sentence: align before comparing'
 elif any(not v for v in per.values()):status='No overlapping quote found for at least one rater; inspect other locations'
 elif 'Pending adjudication' in labels:status='Pending in at least one rater'
 elif len(labels)>1:status='Different labels on overlapping quote candidates'
 elif len({(r['quote_start'],r['quote_end']) for r in rs})>1:status='Same label; verify equivalent claim scope'
 elif len({r.get('categories') for r in rs})>1:status='Same exact quote and label; category tags differ'
 else:status='Same exact quote, label and categories; not new consensus'
 alignment_counts[status]+=1
 a=min(r['quote_start'] for r in rs);b=max(r['quote_end'] for r in rs);text=texts[rid]
 start=text.rfind('\n',0,a)+1;finish=text.find('\n',b);finish=len(text) if finish<0 else finish
 row=[f'Q{n:03}',rid,cases[rid],status,text[start:finish]]
 for who in RATERS:
  rr=per[who];row += ['; '.join(f'{r["issue_id"]}: {r["decision"]}' for r in rr) or 'No overlapping quoted record found; not an Acceptable judgment','\n\n'.join(f'{r["record_key"]}\nQuote: {r["exact_quote"]}\nReason: {r["reason"]}\nSource: {r["last_source"]}' for r in rr)]
 row += ['']*5;alignment.append(row)
sheet('Quote alignment inventory',ah,alignment,['Error','Acceptable','Pending adjudication','Out of scope','Unresolved'])
# Highlight other explicit Pending claims so they cannot disappear behind the 33 targeted rule examples.
remaining=[]
for r in issue_list:
 if r['decision']=='Pending adjudication' and r['record_key'] not in covered_keys:
  remaining.append([r['record_key'],r['report_id'],cases[r['report_id']],r['rater'],r['exact_quote'],r['reason'],r['last_source'],'Preserve Pending. Match the exact claim with other records or request an explicit position; no missing-record inference.']+['']*4)
sheet('Other pending claims',['Record key','Report ID','Case ID','Rater','Exact quote','Reason','Source','Requested handling']+blank,remaining,['Error','Acceptable','Pending adjudication','Out of scope','Unresolved'])
sheet('All current issue records',ih,all_issue_rows)
sheet('All current coverage',ch,coverage_all)
summary_rows=[]
for who in RATERS:
 d=data[who];labels=collections.Counter(r['decision'] for r in d['Issues']);cl=collections.Counter(r['decision'] for r in d['Coverage'])
 summary_rows.append([who,105,552,cl['Covered'],cl['Partially covered'],labels['Error'],labels['Acceptable'],labels['Pending adjudication'],'Submitted/current record counts only; scope alignment incomplete, not comparable error rates.'])
sheet('Current record counts',['Rater','Reports','Coverage rows','Covered','Partially covered','Error records','Acceptable records','Pending records','Interpretation note'],summary_rows)
sheet('Sources',['Source path','SHA-256','Use'],[[p,h,'Read-only source; current post-feedback assembly, not an independent rerating'] for p,h in sources.items()])
rule_rows=[
 ['R01','Coverage: required meaning across paragraphs','Resolve four coverage rows. R086 asks for knee AND ankle as principal differences, with no knee-leading requirement. Similarity and relative prominence must be conveyed semantically; no keyword is mandatory.'],
 ['R02','Threshold extent and precision','Distinguish a retained full-window interval from an assertion that every sample exceeds threshold. Read the subject and predicate in context, including alternatives and explicit precision limits.'],
 ['R03','Non-exceedance versus strict below-threshold segments','Below-100% sample coverage establishes samples not counted as exceeding threshold; equality and masking differ from strictly below-threshold runs. Do not infer physiological inactivity.'],
 ['R04','Degree words','Unanchored degree words remain Pending unless a documented interpretation resolves their role. Do not transfer a composite cutoff to a joint. Reference-anchored description and a clinical severity grade differ.'],
 ['R05','Clinical questions','A mechanism proposed for verification is allowed. Assess any separately asserted factual premise. Determine whether prolonged describes broad detector extent and whether observed limits means excursion bounds or established restriction.'],
 ['R06','Normalization','Uniform positive rescaling preserves own-peak crossings for a fixed curve. Pre-pooling weighting can alter mean shape; CCI may change under unequal channel scaling. Identify the actual intervention.'],
 ['R07','References and corrections','Separate numerical ordering from clinical classification; distinguish methodological concerns from case-reference claims. Apply the inline correction rule without treating a distant correct table as an automatic retraction.'],
 ['R08','Unit of error','Split independently assessable claims, cross-link them, and group repetitions of the same claim. ERS and BF in Sub62 are now split. Local I001 values are not cross-rater claim IDs. Missing records do not equal Acceptable.']]
sheet('Rules for discussion',['Rule group','Topic','Instructions'],rule_rows)
read_rows=[
 ['Status','Current post-feedback discussion aid. Original independent ratings and submitted revisions are preserved. No common decision, signature or confirmation is prefilled.'],
 ['Start here',f'Coverage discussion: {len(coverage_rows)} rows. Interpretation discussion: {len(interpret)} specific claim comparisons, including all-Pending rows. Other pending claims: {len(remaining)} explicit Pending records outside those anchors. These sets are not additive error counts.'],
 ['Sequence','Resolve the four coverage rows, then shared interpretation rules and anchored examples. Review Other pending claims and use the complete quote-alignment inventory to identify unrecorded or differently scoped claims.'],
 ['Coverage',f'{552-len(coverage_rows)} of 552 coverage labels agree across the three current submissions. Agreement in current labels is not a new consensus decision.'],
 ['Issue alignment',f'All {len(issue_list)} current issue records are preserved. {len(clusters)} quote-overlap candidate groups are a navigation aid, not adjudicated claim units. Repeated claims can occur at different locations; overlapping sentences can contain distinct claims.'],
 ['No majority decision','Do not replace individual judgments by majority vote. Record an agreed decision with a reason and actual confirming people/date, or retain Unresolved. Blank confirmation fields must remain blank until agreement occurs.'],
 ['Missingness','No overlapping quote or no issue record is not an explicit Acceptable rating. A recipient may need to confirm the exact claim before comparison.'],
 ['Pending','The full current records contain 24 rater1, 6 rater2 and 4 rater3 Pending labels. Additional no-error positions retain unresolved common interpretation. This differs from counts of new Pending actions in a particular return.'],
 ['Analysis boundary','Use the original private snapshots for prespecified original independent-agreement analysis. This workbook combines feedback-informed revisions; do not label its comparisons independent reliability or calculate model rankings from unaligned issue counts.'],
 ['Clinical flags','Existing submitted flags are retained. Missing pathology/normality flags remain unsupplied; they were not converted to No. Review dependent flags when decisions change.'],
 ['Sources','See Sources for hashes. Rater1/rater2 use frozen originals + personal rechecks + targeted v2 replies. Rater3 uses its consolidated final workbook. No model identity mapping was accessed.'],
 ['Presentation note','Rater2 v2 Reviewer note still says 34 revised records; the verified authoritative sheet contains 39. This workbook uses the actual rows and their stated import rule.'],
 ['Preserved disclosures','Source reviewer identities and exposure disclosures remain as supplied. Automated assembly does not create human signatures, new independent ratings or consensus.']]
sheet('Read first',['Topic','Instructions'],read_rows)
wb._sheets=[wb['Read first'],wb['Coverage discussion'],wb['Interpretation discussion'],wb['Other pending claims'],wb['Rules for discussion'],wb['All pending records'],wb['Quote alignment inventory'],wb['All current issue records'],wb['All current coverage'],wb['Current record counts'],wb['Sources']]
wb.save(target)
# Re-open serialized data, validate decisions, blank human fields, language and immutable sources.
check=read(target)
assert check['Coverage discussion'].max_row==5 and check['All current coverage'].max_row==553
assert check['All current issue records'].max_row==len(issue_list)+1
for s in check:
 heads=list(next(s.values));cols=[n for n,h in enumerate(heads) if h in blank+['Human claim group']]
 for row in list(s.values)[1:]:assert all(row[n] is None for n in cols)
 for row in s:
  for c in row:
   assert c.data_type not in ['f','e'],(s.title,c.coordinate)
   assert not re.search(r'[\u3400-\u9fff]',str(c.value or '')),(s.title,c.coordinate)
for p,h in sources.items():assert sha(P/p)==h,p
README=f'''# Current three-rater discussion package

Use [Three_rater_discussion.xlsx](Three_rater_discussion.xlsx). This is a blinded post-feedback discussion aid; it is not a new independent rating round or a completed adjudication.

The current source assembly yields **{len(coverage_rows)} coverage disagreements among 552 requirements**. All four are Covered for rater2 and Partially covered for rater1/rater3:

| Report | Requirement | Required meaning to discuss |
| --- | --- | --- |
| R1976A4BAD24C1414 | R080 | Knee and hip as principal differences, without required ordering. |
| R35C7A84FBF5C7923 | R197 | Pelvis and hip as relatively larger differences. |
| R370766F1A57479E3 | R172 | Knee and pelvis as similarly sized, relatively larger differences. |
| R7162190F941CB937 | R086 | Knee and ankle as principal differences; knee need not lead ankle. |

Start with Coverage discussion, then the **{len(interpret)} anchored interpretation comparisons**. The **{len(remaining)} Other pending claims** include retained questions outside the targeted response lists. Agree on the shared rule, apply it to the examples consistently, and record a common decision/reason only when actually confirmed. A two-to-one split is not an automatic verdict.

All **{len(issue_list)} current issue records** are included. The quote-alignment inventory contains **{len(clusters)} candidate groups** for navigation; these are not confirmed disagreements, distinct error counts or adjudicated claim groups. Some records cite repeated claims at different locations, while one sentence can contain multiple claims. No recorded issue does not mean Acceptable. Check unmatched cases before treating any apparent omission as a disagreement.

Current full-submission Pending labels are rater1 **24**, rater2 **6**, rater3 **4**; these differ from counts of newly Pending actions in an individual return. Original independent ratings remain in `../three_rater_review_v1/private/`. Do not use this post-feedback table as the original independent-agreement dataset or derive model rankings from unaligned issue counts.

The workbook preserves source paths/hashes, exact quotes, reviewer reasons and individual positions. Discussion and confirmation cells start blank. Clinical flags absent from a response remain absent. No model identity mapping was opened.

Build script: `scripts/build_current_three_rater_discussion.py`. It refuses to overwrite a workbook with populated human discussion fields. Source files are read-only and their hashes are checked after generation.
'''
# This builder reconstructs the earlier full inventory. Do not replace the
# current workflow entry point after newer discussion returns have arrived.
if not (OUT/'README.md').exists():
 (OUT/'README.md').write_text(README)
print(json.dumps({'workbook':str(target),'coverage_disagreements':len(coverage_rows),'interpretation_comparisons':len(interpret),'other_pending_claims':len(remaining),'current_issue_records':len(issue_list),'quote_alignment_candidates':len(clusters),'issue_record_counts':summary,'sources_unchanged':True},indent=2))
