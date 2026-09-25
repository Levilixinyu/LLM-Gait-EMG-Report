(() => {
  'use strict';
  const labels = {must_describe_candidate:"Which findings are worth including in the report", allowed_interpretation:"How to write the report", cannot_infer:"Which conclusions cannot be drawn"};
  const decisions = {PENDING:"Pending review", ACCEPT:"Retain", REVISE:"Modify wording", REJECT:"Need not include／Do not adopt"};
  const seeds = [...document.querySelectorAll('.review-seed')].map(n => JSON.parse(n.textContent));
  const panels = new Map();
  let reviewer = '', reviewDate = '', changedSinceExport = false, memoryOnly = false;
  const $ = s => document.querySelector(s);
  const el = (tag, text, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; };
  const status = text => { $('#review-status').textContent=text; };
  const today = () => {const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
  const key = seed => `gait-card-review-v1-en:${seed.case_id}:${seed.version}:${reviewer}`;
  const fresh = seed => ({case_id:seed.case_id, version:seed.version, decisions:seed.items.map(i=>({item_id:i.item_id,decision:'PENDING',edit:'',reason:''})), additions:[], note:''});
  const validText = x => typeof x==='string' && x.length<=20000;
  function validateCase(value, seed) {
    if(!value || value.case_id!==seed.case_id || value.version!==seed.version)throw Error("Case or material version mismatch; not imported.");
    if(!Array.isArray(value.decisions) || value.decisions.length!==seed.items.length)throw Error("Item count mismatch.");
    const ids=new Set();
    for(const d of value.decisions){
      if(!seed.items.some(i=>i.item_id===d.item_id) || ids.has(d.item_id) || !Object.hasOwn(decisions,d.decision) || !validText(d.edit) || !validText(d.reason))throw Error("Invalid review item format.");
      ids.add(d.item_id);
    }
    if(!Array.isArray(value.additions) || value.additions.length>200 || !validText(value.note))throw Error("Invalid supplementary checklist format.");
    for(const a of value.additions){
      if(!validText(a.item_id) || ids.has(a.item_id) || !/^NEW-[\w-]+$/.test(a.item_id) || !Object.hasOwn(labels,a.category) || !validText(a.text) || !validText(a.reason))throw Error("Invalid additional item format.");
      ids.add(a.item_id);
    }
    // Whitelist the review fields; imported text cannot replace the source evidence.
    return {case_id:value.case_id,version:value.version,decisions:value.decisions.map(d=>({item_id:d.item_id,decision:d.decision,edit:d.edit,reason:d.reason})),additions:value.additions.map(a=>({item_id:a.item_id,category:a.category,text:a.text,reason:a.reason})),note:value.note};
  }
  function save(panel) {
    if(!reviewer)return;
    changedSinceExport=true;
    try{ localStorage.setItem(key(panel.seed),JSON.stringify({reviewer_id:reviewer,review_date:reviewDate,review:panel.state})); }
    catch(_){memoryOnly=true;}
    updateProgress();
    status(memoryOnly?"The browser cannot save temporarily. Please export JSON to preserve your changes; closing the page will lose unexported content.":"Temporarily saved in the current browser. Please export the review JSON and return it to the researcher; this page does not modify the original files.");
  }
  function field(label, node) {const wrap=el('label',undefined,'review-field');wrap.append(el('span',label),node);return wrap;}
  function textArea(value,label,change){const n=el('textarea');n.value=value;n.rows=3;n.setAttribute('aria-label',label);n.addEventListener('input',()=>change(n.value));return n;}
  function render(panel){
    const root=panel.root;root.replaceChildren();
    for(const [category,label] of Object.entries(labels)){
      if(!panel.seed.items.some(i=>i.category===category))continue;
      root.append(el('h4',label));
      for(const item of panel.seed.items.filter(i=>i.category===category)){
        const answer=panel.state.decisions.find(d=>d.item_id===item.item_id);
        const box=el('article',undefined,'review-item');box.dataset.itemId=item.item_id;
        box.append(el('p',item.draft_statement,'original-statement'));
        const evidence=el('details');evidence.append(el('summary',"View corresponding data"),el('small',`Evidence: ${item.evidence}`));box.append(evidence);
        const select=el('select');select.setAttribute('aria-label',`${item.item_id} Review decision`);
        for(const [value,name] of Object.entries(decisions)){const o=el('option',name);o.value=value;select.append(o);}
        select.value=answer.decision;
        const edit=textArea(answer.edit,`${item.item_id} Revised text`,v=>{answer.edit=v;save(panel);});
        const editField=field("Your suggested report wording",edit);editField.hidden=answer.decision!=='REVISE';
        const reasonField=field("Reason for this revision／non-adoption",textArea(answer.reason,`${item.item_id} Reason`,v=>{answer.reason=v;save(panel);}));reasonField.hidden=!['REVISE','REJECT'].includes(answer.decision);
        select.addEventListener('change',()=>{answer.decision=select.value;editField.hidden=answer.decision!=='REVISE';reasonField.hidden=!['REVISE','REJECT'].includes(answer.decision);save(panel);});
        box.append(field("Review decision",select),editField,reasonField);root.append(box);
      }
    }
    root.append(el('h4',"Additional item"));
    for(const item of panel.state.additions){
      const box=el('article',undefined,'review-item addition');box.dataset.itemId=item.item_id;
      const sel=el('select');sel.setAttribute('aria-label',"Additional item category");
      for(const [k,v] of Object.entries(labels)){const o=el('option',v);o.value=k;sel.append(o);}sel.value=item.category;
      sel.addEventListener('change',()=>{item.category=sel.value;save(panel);});
      const remove=el('button',"Remove this additional item");remove.type='button';remove.addEventListener('click',()=>{if(confirm("Remove this additional item?")){panel.state.additions=panel.state.additions.filter(i=>i!==item);save(panel);render(panel);}});
      box.append(field("Category",sel),field("Additional item content",textArea(item.text,"Additional item content",v=>{item.text=v;save(panel);})),field("Evidence／reason",textArea(item.reason,"Additional item evidence",v=>{item.reason=v;save(panel);})),remove);root.append(box);
    }
    const add=el('button',"＋ Add item");add.type='button';add.className='add-review-item';
    add.addEventListener('click',()=>{panel.state.additions.push({item_id:`NEW-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,category:'must_describe_candidate',text:'',reason:''});save(panel);render(panel);});root.append(add);
    root.append(field("Other important findings or additional information needed",textArea(panel.state.note,"Overall opinion on this case",v=>{panel.state.note=v;save(panel);}))); 
    root.disabled=!reviewer;
  }
  function updateProgress(){
    let done=0,total=0;
    for(const p of panels.values()){const n=p.state.decisions.filter(i=>i.decision!=='PENDING').length;total+=p.state.decisions.length;done+=n;document.getElementById('progress-'+p.seed.case_id).textContent=`Selections made for ${n}/${p.state.decisions.length} items · ${p.state.additions.length} items added`;}
    $('#review-progress').textContent=`${reviewer?'Current reviewer: '+reviewer+' · ':''}Selections made for ${done}/${total} items (does not indicate joint finalization)`;
  }
  function activate(){
    const name=$('#reviewer-id').value.trim();if(!name){status("Please enter your expert name or ID first.");$('#reviewer-id').focus();return;}
    if(changedSinceExport && !confirm("Switching or reloading will replace the current interface; please export any unexported comments first. Continue?"))return;
    reviewer=name;reviewDate=$('#review-date').value||today();memoryOnly=false;let corrupt=false;
    for(const p of panels.values()){
      p.state=fresh(p.seed);
      try{const saved=localStorage.getItem(key(p.seed));if(saved){const x=JSON.parse(saved);if(x.reviewer_id!==reviewer)throw Error('identity');p.state=validateCase(x.review,p.seed);}}
      catch(_){corrupt=true;}
      render(p);
    }
    changedSinceExport=false;updateProgress();status(corrupt?"Some temporarily saved data could not be read; a blank draft is displayed. You can restore it by importing a previously exported JSON.":"This reviewer's draft has been loaded. Comments are saved only on this device; when finished, please export the JSON and submit it.");
  }
  function issues(){
    const list=[];
    for(const p of panels.values()){
      for(const d of p.state.decisions){
        if(d.decision==='PENDING')list.push(`${p.seed.case_id}/${d.item_id} Pending review`);
        if(d.decision==='REVISE' && !d.edit.trim())list.push(`${p.seed.case_id}/${d.item_id} Missing revised text`);
        if(['REVISE','REJECT'].includes(d.decision) && !d.reason.trim())list.push(`${p.seed.case_id}/${d.item_id} Missing rationale`);
      }
      for(const a of p.state.additions)if(!a.text.trim() || !a.reason.trim())list.push(`${p.seed.case_id}/${a.item_id} Additional item requires content and supporting evidence`);
    }
    return list;
  }
  function payload(){
    if(!reviewer)throw Error("Please enter your expert ID first and click “Start／Load review”.");
    const missing=issues();return {schema:'gait-card-expert-review/v1',reviewer_id:reviewer,review_date:reviewDate,exported_at:new Date().toISOString(),status:missing.length?'DRAFT_INCOMPLETE':'INDIVIDUAL_REVIEW_COMPLETE',expert_consensus:false,remaining_issues:missing,cases:[...panels.values()].map(p=>({...p.state,source_items:p.seed.items}))};
  }
  function download(value,mime,ext){const blob=new Blob([value],{type:mime});const a=el('a');const url=URL.createObjectURL(blob);a.href=url;a.download=`gait-review-${reviewer.replace(/[^\p{L}\p{N}_-]/gu,'_')}-${Date.now()}.${ext}`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function exportJSON(){try{const x=payload();download(JSON.stringify(x,null,2),'application/json;charset=utf-8','json');changedSinceExport=false;status(`Exported JSON for ${x.cases.length} review sections; ${x.remaining_issues.length?'There are still '+x.remaining_issues.length+' items to complete; marked as draft.':'The individual review is complete; a second expert must still review it.'}`);}catch(e){status(e.message);}}
  function csvCell(v){let s=String(v??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
  function exportCSV(){try{
    const x=payload(),rows=[['schema','reviewer_id','review_date','status','case_id','case_version','item_id','category','original_text','decision','revised_or_added_text','reason','case_note']];
    for(const p of panels.values()){
      for(const d of p.state.decisions){const src=p.seed.items.find(i=>i.item_id===d.item_id);rows.push([x.schema,reviewer,reviewDate,x.status,p.seed.case_id,p.seed.version,d.item_id,src.category,src.draft_statement,d.decision,d.edit,d.reason,p.state.note]);}
      for(const a of p.state.additions)rows.push([x.schema,reviewer,reviewDate,x.status,p.seed.case_id,p.seed.version,a.item_id,a.category,'','ADD',a.text,a.reason,p.state.note]);
    }
    download('\uFEFF'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n'),'text/csv;charset=utf-8','csv');status("Exported a CSV that can be opened in Excel. To continue on another device, please also export the JSON.");
  }catch(e){status(e.message);}}
  async function importJSON(file){
    try{
      if(!file)return;if(file.size>5*1024*1024)throw Error("The file is too large. Please select a review JSON exported from this page.");
      const x=JSON.parse(await file.text());
      if(x.schema!=='gait-card-expert-review/v1' || !validText(x.reviewer_id) || !x.reviewer_id.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(x.review_date) || !Array.isArray(x.cases) || !x.cases.length)throw Error("Not a valid review file.");
      const incoming=new Map();
      for(const c of x.cases){if(incoming.has(c.case_id))throw Error("Duplicate cases in the file.");const p=panels.get(c.case_id);if(!p)throw Error("This page does not contain all the cases in the import file. Please import it in the five-case overview.");incoming.set(c.case_id,validateCase(c,p.seed));}
      if(!confirm(`Import comments from ${x.reviewer_id} for ${incoming.size} review sections and replace the corresponding drafts? Please first export any comments you wish to keep.`))return;
      reviewer=x.reviewer_id.trim();reviewDate=x.review_date;$('#reviewer-id').value=reviewer;$('#review-date').value=reviewDate;
      for(const p of panels.values()){
        if(incoming.has(p.seed.case_id)){p.state=incoming.get(p.seed.case_id);save(p);}
        else{p.state=fresh(p.seed);try{const prev=localStorage.getItem(key(p.seed));if(prev)p.state=validateCase(JSON.parse(prev).review,p.seed);}catch(_){}}
        render(p);
      }
      updateProgress();status("Import complete. Cases and material versions have been checked; the original candidate items remain unchanged.");
    }catch(e){status("Import failed:"+e.message);}
    finally{$('#review-import').value='';}
  }
  for(const seed of seeds){const panel={seed,state:fresh(seed),root:document.getElementById('review-'+seed.case_id)};panels.set(seed.case_id,panel);render(panel);}
  $('#review-date').value=today();$('#review-start').addEventListener('click',activate);
  $('#review-date').addEventListener('change',()=>{if(reviewer){reviewDate=$('#review-date').value||today();for(const p of panels.values())save(p);}});
  $('#export-review-json').addEventListener('click',exportJSON);$('#export-review-csv').addEventListener('click',exportCSV);
  $('#review-import').addEventListener('change',e=>importJSON(e.target.files[0]));
  window.addEventListener('beforeunload',e=>{if(changedSinceExport){e.preventDefault();e.returnValue='';}});
  updateProgress();
})();
