'use strict';
const $=id=>document.getElementById(id);
const labels={open:'待处理',in_progress:'处理中',resolved:'已解决'};
const next={open:'in_progress',in_progress:'resolved',resolved:'open'};
const actions={open:'开始处理',in_progress:'标记解决',resolved:'重新打开'};
const priorities={low:'低',normal:'普通',urgent:'紧急'};
let filter='',request=0,controller;
function node(tag,text,className){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(className)e.className=className;return e;}
async function api(path,options={}){const response=await fetch(path,options);const data=await response.json();if(!response.ok){const e=new Error(data.error||'操作失败，请重试。');e.status=response.status;throw e;}return data;}
function render(tickets){$('tickets').replaceChildren();$('empty').hidden=tickets.length!==0;
 for(const t of tickets){const article=node('article',undefined,'ticket');article.dataset.id=t.id;
 const body=node('div'),meta=node('div',undefined,'meta');meta.append(node('span','#'+t.id),node('span',priorities[t.priority]+'优先级','badge '+t.priority),node('span','版本 '+t.version));body.append(meta,node('h3',t.title),node('p',t.description));
 const details=node('details'),summary=node('summary','查看处理记录'),history=node('ol');details.append(summary,history);let fetched=false;
 details.addEventListener('toggle',async()=>{if(!details.open||fetched)return;summary.textContent='正在读取记录…';try{const d=await api('/api/tickets/'+t.id+'/history');history.replaceChildren(...d.history.map(h=>node('li',(h.from_status?labels[h.from_status]+' → ':'创建 → ')+labels[h.to_status]+' · 版本 '+h.version)));fetched=true;}catch(e){history.replaceChildren(node('li',e.message));}finally{summary.textContent='查看处理记录';}});body.append(details);
 const controls=node('div',undefined,'ticket-actions'),status=node('span',labels[t.status],'state'),button=node('button',actions[t.status]);button.type='button';button.setAttribute('aria-label',actions[t.status]+'：'+t.title);
 button.addEventListener('click',async()=>{button.disabled=true;$('list-error').textContent='';try{await api('/api/tickets/'+t.id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:next[t.status],expected_version:t.version})});$('notice').textContent='#'+t.id+' 已更新为'+labels[next[t.status]];await load();const replacement=document.querySelector('article[data-id="'+t.id+'"] button');(replacement||$('refresh')).focus();}catch(e){$('list-error').textContent=e.message;if(e.status===409){await load();$('refresh').focus();}else button.disabled=false;}});
 controls.append(status,button);article.append(body,controls);$('tickets').append(article);}
}
async function load(){const generation=++request;if(controller)controller.abort();controller=new AbortController();$('loading').hidden=false;
 try{const d=await api('/api/tickets?'+new URLSearchParams({status:filter,q:$('search').value}),{signal:controller.signal});if(generation!==request)return;render(d.tickets);let total=0;for(const k of Object.keys(labels)){$('count-'+k).textContent=d.counts[k];total+=d.counts[k];}$('count-all').textContent=total;}
 catch(e){if(e.name!=='AbortError'&&generation===request)$('list-error').textContent='无法读取队列，请点击刷新重试。';}
 finally{if(generation===request)$('loading').hidden=true;}
}
$('create').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget,button=form.querySelector('button');$('form-error').textContent='';
 for(const name of ['title','description']){$(name).removeAttribute('aria-invalid');if(!$(name).value.trim()){$(name).setAttribute('aria-invalid','true');$('form-error').textContent=(name==='title'?'请填写问题标题。':'请填写问题说明。')+' 已保留其他内容。';$(name).focus();return;}}
 button.disabled=true;button.textContent='正在创建…';try{const data=await api('/api/tickets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:$('title').value,description:$('description').value,priority:$('priority').value})});form.reset();$('notice').textContent='已创建工单 #'+data.ticket.id;filter='';$('search').value='';selectFilter();await load();$('title').focus();}
 catch(e){$('form-error').textContent=e.message+' 已保留输入；可刷新队列核对后重试。';}finally{button.disabled=false;button.textContent='创建工单 ↗';}});
function selectFilter(){document.querySelectorAll('[data-status]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.status===filter)));}
document.querySelectorAll('[data-status]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.status;selectFilter();$('list-error').textContent='';load();}));
$('search-form').addEventListener('submit',e=>{e.preventDefault();load();});$('refresh').addEventListener('click',()=>{$('list-error').textContent='';load();});load();
