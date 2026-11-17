(function(){
 'use strict';
 const master=JSON.parse(document.getElementById('master-data').textContent);
 const archive64=document.getElementById('archive-data').textContent.trim();
 const boxes=[...document.querySelectorAll('input[data-section]')];
 const status=document.getElementById('status'),summary=document.getElementById('summary');
 const ids=()=>boxes.filter(b=>b.checked).map(b=>b.value);
 const options=()=>({cover:document.getElementById('include-cover').checked,sources:document.getElementById('include-sources').checked,front:document.getElementById('front').checked});
 const archive=()=>Uint8Array.from(atob(archive64),c=>c.charCodeAt(0));
 let busy=false,size=22;
 function update(){
  const chosen=ids();
  const plan=chosen.length?FieldBook.makePlan(master,chosen,options()):[];
  summary.textContent=`${chosen.length} of ${boxes.length} sections selected. ${plan.length} print pages, approximately ${Math.ceil(plan.length/2)} double-sided sheets.`;
  document.getElementById('pdf').disabled=busy||!chosen.length;document.getElementById('word').disabled=busy||!chosen.length;
  for(const el of document.querySelectorAll('[data-preview]'))el.hidden=!chosen.includes(el.getAttribute('data-preview'));
  try{localStorage.setItem('ab9mz-v2-selection',JSON.stringify({ids:chosen,options:options()}));}catch{}
 }
 function save(bytes,name,type){
  const url=URL.createObjectURL(new Blob([bytes],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
 }
 async function generate(format,selected=ids(),opts=options(),filename){
  if(busy)return;
  const previousFocus=document.activeElement;
  busy=true;update();status.textContent='Preparing your selected '+format.toUpperCase()+' document.';
  try{
   let bytes;
   if(format==='pdf')bytes=await FieldBook.makePDF(master,archive(),selected,opts,(n,total)=>{status.textContent=`Creating PDF: page ${n} of ${total}.`;});
   else bytes=await FieldBook.makeDOCX(master,selected,opts);
   const ext=format==='pdf'?'pdf':'docx';
   save(bytes,filename||`AB9MZ_Selected_Sections.${ext}`,format==='pdf'?'application/pdf':'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
   status.textContent=`Your ${ext.toUpperCase()} document is ready. The download contains only the selected sections and chosen front matter.`;
  }catch(e){status.textContent='Could not create the document: '+e.message;}
  finally{busy=false;update();if(previousFocus&&previousFocus.isConnected&&!previousFocus.disabled)previousFocus.focus({preventScroll:true});}
 }
 for(const box of boxes)box.addEventListener('change',update);
 for(const id of ['include-cover','include-sources','front'])document.getElementById(id).addEventListener('change',update);
 document.getElementById('select-all').addEventListener('click',()=>{boxes.forEach(b=>b.checked=true);update();});
 document.getElementById('select-none').addEventListener('click',()=>{boxes.forEach(b=>b.checked=false);update();status.textContent='All sections cleared. Select at least one section to create a document.';});
 document.getElementById('pdf').addEventListener('click',()=>generate('pdf'));
 document.getElementById('word').addEventListener('click',()=>generate('word'));
 for(const button of document.querySelectorAll('button[data-download]'))button.addEventListener('click',()=>generate(button.dataset.format,[button.dataset.download],{cover:false,sources:false,front:false},'AB9MZ_'+button.dataset.download+'.'+(button.dataset.format==='pdf'?'pdf':'docx')));
 for(const link of document.querySelectorAll('a[data-read]'))link.addEventListener('click',event=>{event.preventDefault();const el=document.getElementById('read-'+link.dataset.read);el.hidden=false;el.setAttribute('tabindex','-1');el.focus();el.scrollIntoView();status.textContent='Reading this section does not change your selection.';});
 document.getElementById('save-selection').addEventListener('click',()=>save(JSON.stringify({schema_version:1,revision:master.revision,ids:ids(),options:options()},null,2),'AB9MZ_Selection.json','application/json'));
 document.getElementById('load-selection').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  try{const value=JSON.parse(await file.text());FieldBook.choose(master,value.ids);for(const b of boxes)b.checked=value.ids.includes(b.value);for(const [id,key] of [['include-cover','cover'],['include-sources','sources'],['front','front']])if(value.options&&typeof value.options[key]==='boolean')document.getElementById(id).checked=value.options[key];update();status.textContent='Saved section choices loaded.';}catch(e){status.textContent='Could not load choices: '+e.message;}
  event.target.value='';
 });
 document.getElementById('download-source').addEventListener('click',()=>{const source=JSON.parse(JSON.stringify(master));delete source.source_pages;delete source.revision;for(const s of source.sections)for(const p of s.pages)delete p.archiveIndex;save(JSON.stringify(source,null,2),'AB9MZ_Master_Source.json','application/json');});
 function resize(n){size=Math.max(18,Math.min(72,n));document.documentElement.style.fontSize=size+'px';status.textContent='Reading text size '+size+' pixels. Downloaded documents keep their large-print layout.';}
 document.getElementById('larger').addEventListener('click',()=>resize(size+2));document.getElementById('smaller').addEventListener('click',()=>resize(size-2));
 document.getElementById('dark').addEventListener('click',event=>{const on=document.body.classList.toggle('dark');event.currentTarget.setAttribute('aria-pressed',String(on));status.textContent=on?'Dark background enabled.':'Light background enabled.';});
 document.getElementById('read-selection').addEventListener('click',()=>{const el=document.getElementById('reading');el.focus();el.scrollIntoView();});
 try{const value=JSON.parse(localStorage.getItem('ab9mz-v2-selection'));if(value&&Array.isArray(value.ids)&&value.ids.every(id=>master.sections.some(s=>s.id===id))){boxes.forEach(b=>b.checked=value.ids.includes(b.value));if(value.options)for(const [id,key] of [['include-cover','cover'],['include-sources','sources'],['front','front']])if(typeof value.options[key]==='boolean')document.getElementById(id).checked=value.options[key];}}catch{}
 update();status.textContent='Ready offline. Choose sections, then download PDF or Word. No account or network connection is needed for generation.';
})();
