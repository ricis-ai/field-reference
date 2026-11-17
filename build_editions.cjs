const fs=require('fs'),path=require('path');const e=require('./book_engine.js');
(async()=>{
 const root=__dirname,m=JSON.parse(fs.readFileSync(path.join(root,'compiled_master.json'))),archive=fs.readFileSync(path.join(root,'content_archive.pdf'));
 const args=process.argv.slice(2);let selected=m.sections.map(s=>s.id),opts={cover:true,sources:true};
 const selectionIndex=args.indexOf('--selection');if(selectionIndex>=0){const v=JSON.parse(fs.readFileSync(args[selectionIndex+1]));selected=v.ids;opts=v.options||opts;}
 fs.mkdirSync(path.join(root,'sections'),{recursive:true});
 for(const s of m.sections){
  fs.writeFileSync(path.join(root,'sections',s.id+'.pdf'),await e.makePDF(m,archive,[s.id],{cover:false,sources:false}));
  fs.writeFileSync(path.join(root,'sections',s.id+'.docx'),await e.makeDOCX(m,[s.id],{cover:false,sources:false}));
 }
 for(const [name,ids,options] of [['AB9MZ_Amateur_Radio_Field_Reference',selected,opts],['AB9MZ_Print_Test',['phonetics'],{cover:false,sources:false}]]){
  fs.writeFileSync(path.join(root,name+'.pdf'),await e.makePDF(m,archive,ids,options));
  fs.writeFileSync(path.join(root,name+'.docx'),await e.makeDOCX(m,ids,options));
 }
 fs.writeFileSync(path.join(root,'book_plan.json'),JSON.stringify(e.makePlan(m,selected,opts),null,2));
 console.log('Built',m.sections.length,'PDF and Word section pairs; full edition',e.makePlan(m,selected,opts).length,'pages.');
})();
