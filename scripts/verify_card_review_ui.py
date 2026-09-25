"""Manual macOS integration check using isolated headless Chrome and websockets.
Run from the project Python environment; no personal browser profile or network API.
Requires data_cards_v5 built first. Writes audit/card_review_ui/ test evidence.
"""
import argparse,subprocess,tempfile,time,json,base64,urllib.request
from pathlib import Path
from websockets.sync.client import connect
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base',type=Path,default=ROOT/'docs/expert_trial/data_cards_v5')
parser.add_argument('--out',type=Path,default=ROOT/'audit/card_review_ui/v5')
args=parser.parse_args()
OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
BASE=args.base.resolve()
results={}
with tempfile.TemporaryDirectory(prefix='gait-review-browser-',dir='/private/tmp') as tmp:
 tmp=Path(tmp);downloads=tmp/'downloads';downloads.mkdir()
 chrome=subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+str(tmp/'profile'),'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  active=tmp/'profile/DevToolsActivePort'
  for _ in range(200):
   if active.exists():break
   time.sleep(.1)
  port=active.read_text().splitlines()[0]
  targets=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
  target=next(t for t in targets if t['type']=='page')
  with connect(target['webSocketDebuggerUrl'],max_size=30_000_000) as ws:
   cid=0;errors=[]
   def rpc(method,params=None):
    global cid
    cid+=1;wanted=cid;ws.send(json.dumps({'id':wanted,'method':method,'params':params or {}}))
    while True:
     msg=json.loads(ws.recv(timeout=20))
     if msg.get('method')=='Page.javascriptDialogOpening':
      cid+=1;ws.send(json.dumps({'id':cid,'method':'Page.handleJavaScriptDialog','params':{'accept':True}}))
     if msg.get('method')=='Runtime.exceptionThrown':errors.append(msg['params'])
     if msg.get('id')==wanted:
      if 'error' in msg:raise RuntimeError(msg)
      return msg.get('result',{})
   def js(code):
    r=rpc('Runtime.evaluate',{'expression':code,'returnByValue':True,'awaitPromise':True})
    if 'exceptionDetails' in r:raise RuntimeError(r['exceptionDetails'])
    return r.get('result',{}).get('value')
   def until(code):
    for _ in range(100):
     try:
      if js(code):return
     except RuntimeError as exc:
      if 'Inspected target navigated or closed' not in str(exc):raise
     time.sleep(.1)
    raise AssertionError(code)
   def fill(selector,value):js(f"(()=>{{let n=document.querySelector({json.dumps(selector)}); n.value={json.dumps(value)}; n.dispatchEvent(new Event('input',{{bubbles:true}}));}})()")
   def click(selector):js(f"document.querySelector({json.dumps(selector)}).click()")
   def decide(selector,value):js(f"(()=>{{let n=document.querySelector({json.dumps(selector)});n.value={json.dumps(value)};n.dispatchEvent(new Event('change',{{bubbles:true}}));}})()")
   def latest(ext,previous):
    for _ in range(100):
     files=[p for p in downloads.glob('*.'+ext) if p not in previous]
     if files:return max(files,key=lambda p:p.stat().st_mtime)
     time.sleep(.1)
    raise AssertionError('No download '+ext)
   rpc('Page.enable');rpc('Runtime.enable');rpc('Emulation.setDeviceMetricsOverride',{'width':1280,'height':1000,'deviceScaleFactor':1,'mobile':False})
   rpc('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(downloads)})
   rpc('Page.navigate',{'url':(BASE/'index.html').as_uri()});until("document.querySelectorAll('.review-item').length>10")
   results['common_plus_five_case_forms']=js("document.querySelectorAll('.review-fields').length")==6
   results['common_section_first']=js("document.querySelector('.review-fields').id")=='review-common_rules'
   results['locked_until_reviewer']=js("[...document.querySelectorAll('.review-fields')].every(n=>n.disabled)")
   fill('#reviewer-id','Rater01');click('#review-start')
   decide('#review-common_rules [data-item-id="G01"] select','ACCEPT')
   panel='#review-stroke_Sub09_P';first=panel+' .review-item:first-of-type'
   # Exact selectors by stable item id, not visual child order.
   item=panel+' [data-item-id="C01"]'
   decide(item+' select','REVISE');fill(item+' textarea[aria-label="C01 Revised text"]','Specify the paretic side; retain the original data scope.');fill(item+' textarea[aria-label="C01 Reason"]','Avoid left/right confusion.')
   decide(panel+' [data-item-id="C02"] select','REJECT');fill(panel+' [data-item-id="C02"] textarea[aria-label="C02 Reason"]','Optional description; no mandatory penalty.')
   click(panel+' .add-review-item');fill(panel+' .addition textarea[aria-label="Additional item content"]','Addition: check the explanation of missing information.');fill(panel+' .addition textarea[aria-label="Additional item evidence"]','Must be consistent with the information available in the input.')
   fill(panel+' textarea[aria-label="Overall opinion on this case"]','I would like to discuss the clinical importance of mandatory items first.')
   before=set(downloads.iterdir());click('#export-review-json');review=latest('json',before);data=json.loads(review.read_text());case=next(c for c in data['cases'] if c['case_id']=='stroke_Sub09_P')
   results['common_exported_once']=sum(c['case_id']=='common_rules' for c in data['cases'])==1
   results['export_preserves_revision']=case['decisions'][0]['edit']=='Specify the paretic side; retain the original data scope.'
   results['export_preserves_rejection']=case['decisions'][1]['decision']=='REJECT'
   results['export_preserves_addition']=len(case['additions'])==1 and case['additions'][0]['text'].startswith('Addition: ')
   results['common_decision_exported']=next(c for c in data['cases'] if c['case_id']=='common_rules')['decisions'][0]['decision']=='ACCEPT'
   results['unfinished_is_draft']=data['status']=='DRAFT_INCOMPLETE' and data['expert_consensus'] is False
   before=set(downloads.iterdir());click('#export-review-csv');csv=latest('csv',before)
   results['csv_has_utf8_bom']=csv.read_bytes().startswith(b'\xef\xbb\xbf')
   results['csv_has_review_and_case_id']='Specify the paretic side' in csv.read_text(encoding='utf-8-sig') and 'stroke_Sub09_P' in csv.read_text(encoding='utf-8-sig')
   js('window.__beforeNavigation=true');rpc('Page.reload');until("!window.__beforeNavigation && document.readyState==='complete' && document.querySelectorAll('.review-item').length>10");fill('#reviewer-id','Rater01');click('#review-start')
   results['reload_restores_browser_draft']=js(f'document.querySelector({json.dumps(item+' textarea[aria-label="C01 Revised text"]')}).value')==case['decisions'][0]['edit']
   fill('#reviewer-id','Rater02');click('#review-start')
   results['second_reviewer_is_separate']=js(f'document.querySelector({json.dumps(item+" select")}).value')=='PENDING'
   def upload(path):
    doc=rpc('DOM.getDocument');node=rpc('DOM.querySelector',{'nodeId':doc['root']['nodeId'],'selector':'#review-import'})['nodeId'];rpc('DOM.setFileInputFiles',{'nodeId':node,'files':[str(path)]})
   upload(review);until("document.querySelector('#review-status').textContent.startsWith('Import complete')")
   results['json_import_restores_review']=js(f'document.querySelector({json.dumps(item+" select")}).value')=='REVISE' and js("document.querySelector('#reviewer-id').value")=='Rater01'
   altered=json.loads(review.read_text());altered['cases'][0]['version']='wrong-version';wrong=tmp/'wrong.json';wrong.write_text(json.dumps(altered));upload(wrong);until("document.querySelector('#review-status').textContent.startsWith('Import failed')")
   results['wrong_version_rejected_without_mutation']=js(f'document.querySelector({json.dumps(item+" select")}).value')=='REVISE'
   # Imported markup must remain textarea text, never execute.
   altered=json.loads(review.read_text());altered['cases'][0]['decisions'][0]['edit']='<img src=x onerror="window.__unsafe=true">';unsafe=tmp/'text.json';unsafe.write_text(json.dumps(altered));upload(unsafe);until("document.querySelector('#review-status').textContent.startsWith('Import complete')")
   results['import_text_not_html']=js('window.__unsafe===undefined')
   # Restore representative edited text for screenshot.
   upload(review);until("document.querySelector('#review-status').textContent.startsWith('Import complete')")
   js("document.getElementById('review-heading-stroke_Sub09_P').scrollIntoView()")
   shot=rpc('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False});(OUT/'interactive_review.png').write_bytes(base64.b64decode(shot['data']))
   # Single-case files also contain working controls and compatible version IDs.
   js('window.__beforeNavigation=true');rpc('Page.navigate',{'url':(BASE/'stroke_Sub47_P/card.html').as_uri()});until("!window.__beforeNavigation && document.readyState==='complete' && document.querySelectorAll('.review-item').length>5")
   results['single_case_ui_works']=js("document.querySelectorAll('.review-fields').length")==2
   fill('#reviewer-id','Rater01');click('#review-start')
   results['common_shared_with_single_page']=js("document.querySelector('#review-common_rules [data-item-id=\"G01\"] select').value")=='ACCEPT'
   results['no_browser_runtime_errors']=not errors
   (OUT/'browser_checks.json').write_text(json.dumps(results,indent=2))
   print(json.dumps(results,indent=2));assert all(results.values()),results
 finally:
  chrome.terminate()
  try:chrome.wait(timeout=10)
  except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
