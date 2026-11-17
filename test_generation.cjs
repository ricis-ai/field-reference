const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const engine=require('./book_engine.js'),{PDFDocument}=require('pdf-lib'),JSZip=require('jszip');
const root=__dirname,qa=path.resolve(root,'../qa/v2_tests');fs.mkdirSync(qa,{recursive:true});
const m=JSON.parse(fs.readFileSync(path.join(root,'compiled_master.json'))),archive=fs.readFileSync(path.join(root,'content_archive.pdf'));
const element=()=>({checked:false,disabled:false,dataset:{},attributes:{},handlers:{},textContent:'',addEventListener(k,f){this.handlers[k]=f},async click(){if(this.handlers.click)return this.handlers.click({currentTarget:this})},setAttribute(k,v){this.attributes[k]=v},getAttribute(k){return this.attributes[k]},focus(){this.focused=true},scrollIntoView(){}});
(async()=>{
 const elements={};for(const id of ['status','summary','include-cover','include-sources','front','pdf','word','select-all','select-none','save-selection','load-selection','download-source','larger','smaller','dark','read-selection','reading'])elements[id]=element();elements['include-cover'].checked=true;elements['include-sources'].checked=true;
 elements['master-data']={textContent:JSON.stringify(m)};elements['archive-data']={textContent:archive.toString('base64')};
 const boxes=m.sections.map(s=>Object.assign(element(),{value:s.id,checked:true}));const panels=m.sections.map(s=>Object.assign(element(),{attributes:{'data-preview':s.id}}));const downloads=m.sections.flatMap(s=>['pdf','word'].map(format=>Object.assign(element(),{dataset:{download:s.id,format}})));
 let saved;const urls=new Map();let seq=0;const storage=new Map();
 const document={getElementById:id=>elements[id],querySelectorAll:selector=>selector==='input[data-section]'?boxes:selector==='[data-preview]'?panels:selector==='button[data-download]'?downloads:[],documentElement:{style:{}},body:{append(){},classList:{toggle(){return true}}},createElement:()=>({click(){saved={name:this.download,blob:urls.get(this.href)}},remove(){}})};
 const context={document,FieldBook:engine,Uint8Array,Blob,atob:s=>Buffer.from(s,'base64').toString('binary'),URL:{createObjectURL:b=>{const u='blob:'+seq++;urls.set(u,b);return u},revokeObjectURL:u=>urls.delete(u)},setTimeout(){},localStorage:{setItem:(k,v)=>storage.set(k,v),getItem:k=>storage.get(k)}};
 vm.runInNewContext(fs.readFileSync(path.join(root,'selector.js'),'utf8'),context);
 assert(elements.summary.textContent.includes('22 of 22'));
 await elements['select-none'].click();assert(elements.pdf.disabled&&elements.word.disabled);
 boxes.find(b=>b.value==='phonetics').checked=true;await boxes[1].handlers.change();elements['include-cover'].checked=false;elements['include-sources'].checked=false;elements['include-cover'].handlers.change();
 assert(elements.summary.textContent.includes('1 print pages'));
 await elements.pdf.click();assert(saved.name.endsWith('.pdf'));const pdf=Buffer.from(await saved.blob.arrayBuffer());fs.writeFileSync(path.join(qa,'checkbox_phonetics.pdf'),pdf);assert.equal((await PDFDocument.load(pdf)).getPageCount(),1);
 await elements.word.click();const docx=Buffer.from(await saved.blob.arrayBuffer());fs.writeFileSync(path.join(qa,'checkbox_phonetics.docx'),docx);const z=await JSZip.loadAsync(docx);const xml=await z.file('word/document.xml').async('string');assert(xml.includes('Alfa')&&xml.includes('Zulu')&&!xml.includes('Morse numbers'));
 await elements['save-selection'].click();const profile=JSON.parse(await saved.blob.text());assert.deepEqual(profile.ids,['phonetics']);
 boxes.find(b=>b.value==='morse').checked=true;elements['include-cover'].checked=true;elements['include-sources'].checked=true;elements['front'].checked=true;elements.front.handlers.change();await elements.pdf.click();fs.writeFileSync(path.join(qa,'checkbox_phonetics_morse.pdf'),Buffer.from(await saved.blob.arrayBuffer()));
 const plan=engine.makePlan(m,['phonetics','morse'],{cover:true,sources:true,front:true});assert(plan.some(p=>p.title==='Morse numbers'));assert(plan.some(p=>p.sources));assert(!plan.some(p=>p.title==='ARES'));
 for(const s of ['phonetics','morse']){const pos=plan.findIndex(p=>p.id===m.sections.find(q=>q.id===s).pages[0].id);assert.equal((pos+1)%2,1);}
 assert.throws(()=>engine.makePlan(m,[]));assert.throws(()=>engine.makePlan(m,['invalid']));
 for(const s of m.sections){const d=await PDFDocument.load(fs.readFileSync(path.join(root,'sections',s.id+'.pdf')));assert.equal(d.getPageCount(),s.pages.length,s.id);const a=await JSZip.loadAsync(fs.readFileSync(path.join(root,'sections',s.id+'.docx')));for(const item of ['word/document.xml','word/styles.xml','word/settings.xml','_rels/.rels'])assert(a.file(item));const x=await a.file('word/document.xml').async('string');assert(!x.includes('NaN'));}
 const result={selector_logic:'passed',single_section_pdf_pages:1,real_docx_zip:'passed',saved_profile:'passed',optional_sources:'passed',section_front_faces:'passed',empty_and_invalid_selections:'passed',section_pdf_docx_pairs:m.sections.length,browser_rendering:'Covered separately in ACCESSIBILITY_REVIEW.html; this script checks generation logic',voiceover:'Not tested'};
 fs.writeFileSync(path.join(qa,'generation_checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})();
