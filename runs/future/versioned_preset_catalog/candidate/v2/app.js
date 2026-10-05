'use strict';
const $ = id => document.getElementById(id);
const records = [
 {id:'R-041',title:'北侧展厅照明调整',owner:'林溪',body:'调整照明角度，减少展柜表面的反光。示例资料已补齐，等待审阅。',state:'待审阅'},
 {id:'R-042',title:'周末工作坊物料清单',owner:'陈远',body:'核对工作坊需要的纸张与工具数量，保留备用物料。',state:'待审阅'},
 {id:'R-043',title:'器材借用说明更新',owner:'苏禾',body:'补充归还位置与检查事项，方便下一位使用者接手。',state:'待审阅'}
];
let selected=null, confirmAction=null, dialogTrigger=null;
function status(id,text,kind=''){const n=$(id);n.textContent=text;n.className='status'+(kind?' '+kind:'');}
function confirm(title,body,action){dialogTrigger=document.activeElement;$('confirm-title').textContent=title;$('confirm-body').textContent=body;confirmAction=action;$('confirm').returnValue='';$('confirm').showModal();}
function finishConfirmation(value){
 const action=confirmAction,trigger=dialogTrigger;
 confirmAction=null;dialogTrigger=null;
 $('confirm').close(value);
 if(value==='confirm'&&action)action();
 if(trigger?.isConnected&&!trigger.disabled&&trigger.getClientRects().length)trigger.focus();
}
$('confirm').querySelector('form').addEventListener('submit',event=>{event.preventDefault();finishConfirmation(event.submitter?.value||'cancel');});
$('confirm').addEventListener('cancel',event=>{event.preventDefault();finishConfirmation('cancel');});
document.querySelectorAll('.views button').forEach(button=>button.addEventListener('click',()=>{
 const view=button.dataset.view;document.body.dataset.view=view;
 document.querySelectorAll('main>section').forEach(s=>s.hidden=s.id!==view);
 document.querySelectorAll('.views button').forEach(b=>{if(b===button)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
}));
function renderReview(){
 const query=$('review-search').value.toLowerCase().trim(),list=$('review-list');list.replaceChildren();
 const shown=records.filter(r=>(r.title+r.owner).toLowerCase().includes(query));$('review-empty').hidden=shown.length!==0;
 for(const record of shown){const li=document.createElement('li'),button=document.createElement('button');button.type='button';button.dataset.record=record.id;button.setAttribute('aria-pressed',String(selected?.id===record.id));
  for(const [tag,text,cls] of [['strong',record.title,''],['span',record.id+' · '+record.owner,'meta'],['span',record.state==='待审阅'?'○ 待审阅':'✓ 已通过示例','state']]){const e=document.createElement(tag);e.textContent=text;e.className=cls;button.append(e);}
  button.addEventListener('click',()=>{selected=record;renderReview();$('record-title').textContent=record.title;$('record-body').textContent=record.body;$('record-state').textContent='负责人：'+record.owner+' · '+record.state;$('review-approve').disabled=record.state!=='待审阅';$('record-title').focus();});li.append(button);list.append(li);
 }
}
$('review-search').addEventListener('input',renderReview);$('review-clear').addEventListener('click',()=>{$('review-search').value='';renderReview();$('review-search').focus();});
$('review-approve').addEventListener('click',()=>{const record=selected;if(!record)return;confirm('通过这条示例记录？',record.title+'。这只会更新本页示例，不执行真实审批。',()=>{record.state='已通过示例';$('record-state').textContent='负责人：'+record.owner+' · '+record.state;$('review-approve').disabled=true;renderReview();$('record-title').focus();status('review-status','✓ 已通过示例：'+record.title,'success');});});
$('review-error').addEventListener('click',()=>{status('review-status','读取失败。已有记录保留，可重试。','error');$('review-retry').hidden=false;});$('review-retry').addEventListener('click',()=>{status('review-status','已恢复示例记录。');$('review-retry').hidden=true;$('review-error').focus();});
renderReview();
const stockKey='forge-preset-stock-v1',noteKey='forge-preset-annotation-v1';let stockVersion=0,stockBusy=false,failNextNote=false;
function readStock(){const raw=localStorage.getItem(stockKey);if(raw===null)return {quantity:12,note:'',version:0};const v=JSON.parse(raw);if(!v||!Number.isInteger(v.quantity)||v.quantity<0||v.quantity>99999||typeof v.note!=='string'||!Number.isInteger(v.version)||v.version<0)throw Error('Invalid saved record');return v;}
function loadStock(){try{const v=readStock();stockVersion=v.version;$('quantity').value=v.quantity;$('stock-note').value=v.note;$('stock-previous').textContent=v.quantity;if(v.version)status('stock-status','✓ 已从当前浏览器恢复盘点记录。','success');}catch{status('stock-status','无法读取本地记录。输入仍可编辑，保存前请处理浏览器存储问题。','error');}}
function commitStock(quantity,note){
 stockBusy=true;$('stock-save').disabled=true;$('stock-form').setAttribute('aria-busy','true');status('stock-status','正在保存到当前浏览器…');
 setTimeout(()=>{try{const latest=readStock(),v={quantity,note,version:latest.version+1};localStorage.setItem(stockKey,JSON.stringify(v));stockVersion=v.version;$('stock-previous').textContent=quantity;status('stock-status','✓ 盘点已保存于当前浏览器。','success');}catch{status('stock-status','保存失败，输入已保留。处理存储问题后可再次保存。','error');}finally{stockBusy=false;$('stock-save').disabled=false;$('stock-form').removeAttribute('aria-busy');}},220);
}
$('stock-form').addEventListener('submit',event=>{event.preventDefault();if(stockBusy)return;const raw=$('quantity').value.trim();
 if(!/^\d{1,5}$/.test(raw)){ $('quantity').setAttribute('aria-invalid','true');$('quantity-error').hidden=false;$('quantity-error').textContent='请输入 0–99999 的整数，原输入已保留。';$('quantity').focus();return; }
 $('quantity').removeAttribute('aria-invalid');$('quantity-error').hidden=true;const quantity=Number(raw),note=$('stock-note').value;
 try{const latest=readStock();if(latest.version!==stockVersion){status('stock-status','发现另一份示例记录，你的输入已保留。','warning');confirm('使用此次盘点覆盖本地记录？','当前记录：'+latest.quantity+' 件；你的输入：'+quantity+' 件。取消将保留输入。',()=>commitStock(quantity,note));}else commitStock(quantity,note);}catch{status('stock-status','无法读取本地记录，输入已保留。','error');}
});
$('stock-incoming').addEventListener('click',()=>{try{const v=readStock();localStorage.setItem(stockKey,JSON.stringify({quantity:18,note:'另一份示例记录',version:v.version+1}));status('stock-status','已模拟另一份 18 件的记录；你的输入未改变。保存时可比较。','warning');}catch{status('stock-status','无法保存状态样例，当前输入未改变。','error');}});
loadStock();
function renderNote(){try{const note=localStorage.getItem(noteKey);$('annotation-saved').hidden=!note;$('annotation-text').textContent=note||'';$('annotation-open').hidden=!!note;}catch{status('annotation-status','无法读取批注，浏览器存储不可用。','error');}}
function openNote(){try{$('annotation-input').value=localStorage.getItem(noteKey)||'';}catch{$('annotation-input').value='';} $('annotation-form').hidden=false;status('annotation-status','草稿尚未保存。');$('annotation-input').focus();}
$('annotation-open').addEventListener('click',openNote);$('annotation-edit').addEventListener('click',openNote);
$('annotation-cancel').addEventListener('click',()=>{$('annotation-form').hidden=true;($('annotation-saved').hidden?$('annotation-open'):$('annotation-edit')).focus();});
$('annotation-form').addEventListener('submit',event=>{event.preventDefault();const text=$('annotation-input').value.trim();if(!text){status('annotation-status','请先写下批注，输入已保留。','error');return;}if(failNextNote){failNextNote=false;status('annotation-status','示例保存错误：草稿已保留，再次保存即可重试。','error');return;}
 try{localStorage.setItem(noteKey,text);renderNote();$('annotation-form').hidden=true;$('annotation-edit').focus();}catch{status('annotation-status','保存失败，草稿已保留。处理浏览器存储问题后可重试。','error');}
});
$('annotation-delete').addEventListener('click',()=>confirm('删除这条本地批注？','取消会保留批注。此操作只影响当前浏览器。',()=>{try{localStorage.removeItem(noteKey);renderNote();$('annotation-form').hidden=true;$('annotation-open').focus();}catch{status('annotation-status','无法删除本地批注。','error');}}));
$('annotation-error').addEventListener('click',()=>{failNextNote=true;openNote();status('annotation-status','已准备可重试错误样例，下一次保存将保留草稿。','warning');});
document.querySelectorAll('.contents a').forEach(a=>a.addEventListener('click',()=>{const target=document.querySelector(a.getAttribute('href'));target.focus({preventScroll:true});}));
renderNote();
