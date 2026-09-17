(() => {
  'use strict';
  const labels = {must_describe_candidate:'哪些发现值得写进报告', allowed_interpretation:'报告怎么写', cannot_infer:'哪些结论不能下'};
  const decisions = {PENDING:'待审核', ACCEPT:'保留', REVISE:'修改表述', REJECT:'不必写入／不采用'};
  const seeds = [...document.querySelectorAll('.review-seed')].map(n => JSON.parse(n.textContent));
  const panels = new Map();
  let reviewer = '', reviewDate = '', changedSinceExport = false, memoryOnly = false;
  const $ = s => document.querySelector(s);
  const el = (tag, text, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; };
  const status = text => { $('#review-status').textContent=text; };
  const today = () => {const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
  const key = seed => `gait-card-review-v1:${seed.case_id}:${seed.version}:${reviewer}`;
  const fresh = seed => ({case_id:seed.case_id, version:seed.version, decisions:seed.items.map(i=>({item_id:i.item_id,decision:'PENDING',edit:'',reason:''})), additions:[], note:''});
  const validText = x => typeof x==='string' && x.length<=20000;
  function validateCase(value, seed) {
    if(!value || value.case_id!==seed.case_id || value.version!==seed.version)throw Error('病例或材料版本不匹配，未导入。');
    if(!Array.isArray(value.decisions) || value.decisions.length!==seed.items.length)throw Error('条目数不匹配。');
    const ids=new Set();
    for(const d of value.decisions){
      if(!seed.items.some(i=>i.item_id===d.item_id) || ids.has(d.item_id) || !Object.hasOwn(decisions,d.decision) || !validText(d.edit) || !validText(d.reason))throw Error('审核条目格式无效。');
      ids.add(d.item_id);
    }
    if(!Array.isArray(value.additions) || value.additions.length>200 || !validText(value.note))throw Error('补充清单格式无效。');
    for(const a of value.additions){
      if(!validText(a.item_id) || ids.has(a.item_id) || !/^NEW-[\w-]+$/.test(a.item_id) || !Object.hasOwn(labels,a.category) || !validText(a.text) || !validText(a.reason))throw Error('补充条目格式无效。');
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
    status(memoryOnly?'浏览器无法暂存。请导出 JSON 保留修改；关闭网页会丢失未导出的内容。':'已暂存到当前浏览器。请导出审核 JSON 交回研究者；本页不会修改原始文件。');
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
        const evidence=el('details');evidence.append(el('summary','查看对应数据'),el('small',`依据：${item.evidence}`));box.append(evidence);
        const select=el('select');select.setAttribute('aria-label',`${item.item_id} 审核决定`);
        for(const [value,name] of Object.entries(decisions)){const o=el('option',name);o.value=value;select.append(o);}
        select.value=answer.decision;
        const edit=textArea(answer.edit,`${item.item_id} 修改后文字`,v=>{answer.edit=v;save(panel);});
        const editField=field('您建议的报告表述',edit);editField.hidden=answer.decision!=='REVISE';
        const reasonField=field('为什么这样改／不采用',textArea(answer.reason,`${item.item_id} 理由`,v=>{answer.reason=v;save(panel);}));reasonField.hidden=!['REVISE','REJECT'].includes(answer.decision);
        select.addEventListener('change',()=>{answer.decision=select.value;editField.hidden=answer.decision!=='REVISE';reasonField.hidden=!['REVISE','REJECT'].includes(answer.decision);save(panel);});
        box.append(field('审核决定',select),editField,reasonField);root.append(box);
      }
    }
    root.append(el('h4','补充条目'));
    for(const item of panel.state.additions){
      const box=el('article',undefined,'review-item addition');box.dataset.itemId=item.item_id;
      const sel=el('select');sel.setAttribute('aria-label','补充条目类别');
      for(const [k,v] of Object.entries(labels)){const o=el('option',v);o.value=k;sel.append(o);}sel.value=item.category;
      sel.addEventListener('change',()=>{item.category=sel.value;save(panel);});
      const remove=el('button','移除此补充条目');remove.type='button';remove.addEventListener('click',()=>{if(confirm('移除此补充条目？')){panel.state.additions=panel.state.additions.filter(i=>i!==item);save(panel);render(panel);}});
      box.append(field('类别',sel),field('补充条目内容',textArea(item.text,'补充条目内容',v=>{item.text=v;save(panel);})),field('依据／理由',textArea(item.reason,'补充条目依据',v=>{item.reason=v;save(panel);})),remove);root.append(box);
    }
    const add=el('button','＋ 添加条目');add.type='button';add.className='add-review-item';
    add.addEventListener('click',()=>{panel.state.additions.push({item_id:`NEW-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,category:'must_describe_candidate',text:'',reason:''});save(panel);render(panel);});root.append(add);
    root.append(field('其他重要发现或需要补充的资料',textArea(panel.state.note,'本例整体意见',v=>{panel.state.note=v;save(panel);}))); 
    root.disabled=!reviewer;
  }
  function updateProgress(){
    let done=0,total=0;
    for(const p of panels.values()){const n=p.state.decisions.filter(i=>i.decision!=='PENDING').length;total+=p.state.decisions.length;done+=n;document.getElementById('progress-'+p.seed.case_id).textContent=`已选择 ${n}/${p.state.decisions.length} 条 · 补充 ${p.state.additions.length} 条`;}
    $('#review-progress').textContent=`${reviewer?'当前审核人：'+reviewer+' · ':''}已选择 ${done}/${total} 条（不代表已联合定稿）`;
  }
  function activate(){
    const name=$('#reviewer-id').value.trim();if(!name){status('请先填写专家姓名或编号。');$('#reviewer-id').focus();return;}
    if(changedSinceExport && !confirm('切换或重新载入会替换当前界面；尚未导出的意见请先导出。确定继续？'))return;
    reviewer=name;reviewDate=$('#review-date').value||today();memoryOnly=false;let corrupt=false;
    for(const p of panels.values()){
      p.state=fresh(p.seed);
      try{const saved=localStorage.getItem(key(p.seed));if(saved){const x=JSON.parse(saved);if(x.reviewer_id!==reviewer)throw Error('identity');p.state=validateCase(x.review,p.seed);}}
      catch(_){corrupt=true;}
      render(p);
    }
    changedSinceExport=false;updateProgress();status(corrupt?'部分暂存无法读取；已显示空白草稿。可导入此前导出的 JSON 恢复。':'已载入此审核人的草稿。意见只保存在本机；完成后请导出 JSON 交回。');
  }
  function issues(){
    const list=[];
    for(const p of panels.values()){
      for(const d of p.state.decisions){
        if(d.decision==='PENDING')list.push(`${p.seed.case_id}/${d.item_id} 待审核`);
        if(d.decision==='REVISE' && !d.edit.trim())list.push(`${p.seed.case_id}/${d.item_id} 缺修改文字`);
        if(['REVISE','REJECT'].includes(d.decision) && !d.reason.trim())list.push(`${p.seed.case_id}/${d.item_id} 缺理由`);
      }
      for(const a of p.state.additions)if(!a.text.trim() || !a.reason.trim())list.push(`${p.seed.case_id}/${a.item_id} 补充条目需内容及依据`);
    }
    return list;
  }
  function payload(){
    if(!reviewer)throw Error('请先填写专家编号并点击“开始／载入审核”。');
    const missing=issues();return {schema:'gait-card-expert-review/v1',reviewer_id:reviewer,review_date:reviewDate,exported_at:new Date().toISOString(),status:missing.length?'DRAFT_INCOMPLETE':'INDIVIDUAL_REVIEW_COMPLETE',expert_consensus:false,remaining_issues:missing,cases:[...panels.values()].map(p=>({...p.state,source_items:p.seed.items}))};
  }
  function download(value,mime,ext){const blob=new Blob([value],{type:mime});const a=el('a');const url=URL.createObjectURL(blob);a.href=url;a.download=`gait-review-${reviewer.replace(/[^\p{L}\p{N}_-]/gu,'_')}-${Date.now()}.${ext}`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function exportJSON(){try{const x=payload();download(JSON.stringify(x,null,2),'application/json;charset=utf-8','json');changedSinceExport=false;status(`已导出 ${x.cases.length} 个审核区 JSON；${x.remaining_issues.length?'仍有 '+x.remaining_issues.length+' 项待完成，已标为草稿。':'个人审核已填写完整，仍需第二位专家复核。'}`);}catch(e){status(e.message);}}
  function csvCell(v){let s=String(v??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
  function exportCSV(){try{
    const x=payload(),rows=[['schema','reviewer_id','review_date','status','case_id','case_version','item_id','category','original_text','decision','revised_or_added_text','reason','case_note']];
    for(const p of panels.values()){
      for(const d of p.state.decisions){const src=p.seed.items.find(i=>i.item_id===d.item_id);rows.push([x.schema,reviewer,reviewDate,x.status,p.seed.case_id,p.seed.version,d.item_id,src.category,src.draft_statement,d.decision,d.edit,d.reason,p.state.note]);}
      for(const a of p.state.additions)rows.push([x.schema,reviewer,reviewDate,x.status,p.seed.case_id,p.seed.version,a.item_id,a.category,'','ADD',a.text,a.reason,p.state.note]);
    }
    download('\uFEFF'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n'),'text/csv;charset=utf-8','csv');status('已导出 Excel 可打开的 CSV。跨设备续填请同时导出 JSON。');
  }catch(e){status(e.message);}}
  async function importJSON(file){
    try{
      if(!file)return;if(file.size>5*1024*1024)throw Error('文件过大，请选择本页导出的审核 JSON。');
      const x=JSON.parse(await file.text());
      if(x.schema!=='gait-card-expert-review/v1' || !validText(x.reviewer_id) || !x.reviewer_id.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(x.review_date) || !Array.isArray(x.cases) || !x.cases.length)throw Error('不是有效审核文件。');
      const incoming=new Map();
      for(const c of x.cases){if(incoming.has(c.case_id))throw Error('文件内病例重复。');const p=panels.get(c.case_id);if(!p)throw Error('此页面未包含导入文件中的所有病例。请在五例总览中导入。');incoming.set(c.case_id,validateCase(c,p.seed));}
      if(!confirm(`导入 ${x.reviewer_id} 的 ${incoming.size} 个审核区意见并替换对应草稿？请先导出需要保留的意见。`))return;
      reviewer=x.reviewer_id.trim();reviewDate=x.review_date;$('#reviewer-id').value=reviewer;$('#review-date').value=reviewDate;
      for(const p of panels.values()){
        if(incoming.has(p.seed.case_id)){p.state=incoming.get(p.seed.case_id);save(p);}
        else{p.state=fresh(p.seed);try{const prev=localStorage.getItem(key(p.seed));if(prev)p.state=validateCase(JSON.parse(prev).review,p.seed);}catch(_){}}
        render(p);
      }
      updateProgress();status('导入完成。已核对病例和材料版本；原始候选条目保持不变。');
    }catch(e){status('导入失败：'+e.message);}
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
