'use strict';
const stages=['Saved','Applied','Assessment','Interview','Offer','Rejected','Withdrawn'];
const $=selector=>document.querySelector(selector);
let applications=[],editing=null,token='',loadVersion=0;
for(const stage of stages){for(const select of [$('#filter'),$('#form').elements.stage]){const option=document.createElement('option');option.value=stage;option.textContent=stage;select.append(option)}}
function today(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function daysUntil(value){return Math.round((Date.parse(value+'T00:00:00Z')-Date.parse(today()+'T00:00:00Z'))/86400000)}
function isActive(app){return !['Offer','Rejected','Withdrawn'].includes(app.stage)}
async function api(path,options={}){const response=await fetch(path,options);const data=await response.json();if(!response.ok)throw Error(data.error||'Request failed');return data}
function cell(text){const td=document.createElement('td');td.textContent=text;return td}
function render(){
 $('#total').textContent=applications.length;
 $('#active').textContent=applications.filter(isActive).length;
 $('#interviews').textContent=applications.filter(a=>a.stage==='Interview').length;
 $('#due').textContent=applications.filter(a=>isActive(a)&&a.deadline&&daysUntil(a.deadline)>=0&&daysUntil(a.deadline)<=7).length;
 const query=$('#search').value.toLowerCase();const stage=$('#filter').value;
 const visible=applications.filter(a=>(!stage||a.stage===stage)&&`${a.company} ${a.role}`.toLowerCase().includes(query));
 $('#rows').replaceChildren();$('#empty').hidden=visible.length>0;
 if(applications.length&&!visible.length){$('#empty h2').textContent='No matching applications.';$('#empty p').textContent='Try another search or stage.'}else{$('#empty h2').textContent='Start with one opportunity.';$('#empty p').textContent="Save a role you're considering, then track each step here."}
 for(const a of visible){const tr=document.createElement('tr');const role=cell('');const name=document.createElement('strong');name.textContent=a.company;const subtitle=document.createElement('small');subtitle.textContent=a.role;role.append(name,subtitle);const status=cell('');const badge=document.createElement('span');badge.className='badge';badge.textContent=a.stage;status.append(badge);const deadline=cell(a.deadline||'No deadline');if(isActive(a)&&a.deadline&&daysUntil(a.deadline)<0)deadline.className='overdue';const action=cell('');const button=document.createElement('button');button.className='row-button';button.textContent='View / edit';button.setAttribute('aria-label',`Edit ${a.role} at ${a.company}`);button.onclick=()=>openEditor(a);action.append(button);tr.append(role,status,cell(a.location||'—'),deadline,action);$('#rows').append(tr)}
}
async function reload(){applications=await api('/api/applications');render()}
async function openEditor(a=null){
 const version=++loadVersion;editing=a;$('#form').reset();$('#error').textContent='';$('#title').textContent=a?'Application details':'New application';$('#history').replaceChildren();$('#history-box').hidden=!a;
 if(a)for(const field of ['company','role','stage','location','deadline','url','notes'])$('#form').elements[field].value=a[field];
 $('#editor').showModal();
 if(a){try{const events=await api('/api/history/'+a.id);if(version!==loadVersion)return;for(const event of events){const li=document.createElement('li');li.textContent=`${event.stage} · ${new Date(event.happened_at).toLocaleString()}`;$('#history').append(li)}}catch(e){if(version===loadVersion)$('#error').textContent=e.message}}
}
$('#add').onclick=()=>openEditor();$('#close').onclick=()=>{$('#editor').close();loadVersion++};$('#editor').addEventListener('cancel',()=>loadVersion++);
$('#search').oninput=render;$('#filter').onchange=render;
$('#form').onsubmit=async event=>{
 event.preventDefault();const body=Object.fromEntries(new FormData(event.target));if(editing)body.revision=editing.revision;
 $('#save').disabled=true;$('#error').textContent='';
 try{await api('/api/applications'+(editing?'/'+editing.id:''),{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify(body)});$('#editor').close();loadVersion++;await reload();$('#message').textContent='Application saved.'}
 catch(e){$('#error').textContent=e.message;$('#message').textContent=e.message}
 finally{$('#save').disabled=false}
};
(async()=>{try{token=(await api('/api/session')).token;await reload()}catch(e){$('#message').textContent='Could not load applications: '+e.message}})();
