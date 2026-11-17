/* Offline assembly shared by the master selector and command-line rebuild. */
(function(root,factory){
 if(typeof module==='object'&&module.exports){let pdf,zip;try{pdf=require('pdf-lib')}catch{pdf=require('./pdf-lib.min.js')}try{zip=require('jszip')}catch{zip=require('./jszip.min.js')}module.exports=factory(pdf,zip);}
 else root.FieldBook=factory(root.PDFLib,root.JSZip);
})(typeof globalThis!=='undefined'?globalThis:this,function(PDFLib,JSZip){
 'use strict';
 const WIDTH=489.6;
 const xml=s=>String(s).replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]));
 const text=s=>String(s||'');
 function choose(master,ids){
  if(!Array.isArray(ids)||!ids.length)throw Error('Select at least one section.');
  const known=new Set(master.sections.map(s=>s.id));
  if(ids.some(id=>!known.has(id)))throw Error('The selection contains an unknown section.');
  return master.sections.filter(s=>ids.includes(s.id));
 }
 function makePlan(master,ids,options={}){
  const sections=choose(master,ids),sources=options.sources!==false,cover=options.cover!==false,front=!!options.front;
  const refs=new Set(sections.flatMap(s=>s.pages.flatMap(p=>String(p.refs||'').split(',').map(n=>Number(n.trim())).filter(Boolean))));
  const sourcePages=sources?master.source_pages.filter(p=>p.source_ids.some(id=>refs.has(id))):[];
  const entries=sections.map(s=>({id:s.id,title:s.title,pages:s.pages}));
  if(sourcePages.length)entries.push({id:'sources',title:'Sources for the selected sections',pages:sourcePages});
  const tocCount=cover?Math.ceil(entries.length/12):0;
  let n=cover?1+tocCount:0;
  const result=[],toc=[];
  for(const e of entries){
   if(front&&n%2){result.push({id:'blank-'+n,title:'Binding spacer',paragraphs:['Intentionally blank so the next section starts on a front face.'],group:'Binding',blank:true});n++;}
   toc.push({title:e.title,page:n+1,count:e.pages.length});
   result.push(...e.pages);n+=e.pages.length;
  }
  if(cover){
   const head=[{id:'cover',title:master.title,group:'Start here',paragraphs:[`Custom edition ${master.edition} for ${master.owner}.`,`${sections.length} selected sections. ${n} pages before any printer-added final blank.`, 'Letter size 8.5 by 11 inches. Main text 22 points. Print actual size, duplex, flip on the long edge.', 'Selections and all section documents come from the same master source. Downloaded copies are snapshots; rebuild after editing the master.',`Master revision ${master.revision}. ${master.date}.`]}];
   for(let k=0;k<tocCount;k++)head.push({id:'contents-'+k,title:'Contents '+(k+1),group:'Contents',toc:true,col_widths:[70,419.6],table:[['Page','Section'],...toc.slice(k*12,k*12+12).map(e=>[String(e.page),e.title])],paragraphs:[]});
   return head.concat(result);
  }
  return result;
 }
 async function makePDF(master,archiveBytes,ids,options={},progress=()=>{}){
  const plan=makePlan(master,ids,options),pdf=await PDFLib.PDFDocument.create();
  const archive=await PDFLib.PDFDocument.load(archiveBytes);
  const font=await pdf.embedFont(PDFLib.StandardFonts.Helvetica),bold=await pdf.embedFont(PDFLib.StandardFonts.HelveticaBold);
  const embeds=new Map(),links=[];
  const wrap=(s,size,width,f=font)=>{
   const words=String(s).split(/\s+/),lines=[];let line='';
   for(const word of words){const trial=line?line+' '+word:word;if(line&&f.widthOfTextAtSize(trial,size)>width){lines.push(line);line=word}else line=trial;}if(line)lines.push(line);return lines;
  };
  for(let i=0;i<plan.length;i++){
   const p=plan[i],page=pdf.addPage([612,792]),x=(i+1)%2?79.2:43.2;
   if(Number.isInteger(p.archiveIndex)){
    if(!embeds.has(p.archiveIndex))embeds.set(p.archiveIndex,await pdf.embedPage(archive.getPage(p.archiveIndex)));
    page.drawPage(embeds.get(p.archiveIndex),{x:x-79.2,y:0});
   }else{
    let y=736;
    for(const line of wrap(p.title,28,WIDTH,bold)){page.drawText(line,{x,y:y-28,font:bold,size:28});y-=33;}y-=17;
    for(const para of p.paragraphs||[]){for(const line of wrap(para,22,WIDTH)){page.drawText(line,{x,y:y-22,font,size:22});y-=27;}y-=11;}
    for(const row of (p.table||[])){const lines=wrap(row[1],20,WIDTH-85),top=y;page.drawText(row[0],{x,y:y-20,font,size:20});for(let j=0;j<lines.length;j++)page.drawText(lines[j],{x:x+85,y:y-20-j*24,font,size:20});y-=Math.max(1,lines.length)*24+8;if(p.toc&&Number(row[0])>0)links.push({page,rect:[x,y,x+WIDTH,top],target:Number(row[0])-1});}
    if(y<74)throw Error('Generated front matter exceeded its page.');
    page.drawText('AB9MZ | Field Reference | Edition '+master.edition,{x,y:760,font,size:14});
   }
   page.drawText(`Edition ${master.edition} | ${master.date} | Page ${i+1} of ${plan.length}`,{x,y:30,font,size:14});
   progress(i+1,plan.length);
  }
  for(const link of links){const a=pdf.context.obj({Type:'Annot',Subtype:'Link',Rect:link.rect,Border:[0,0,0],Dest:[pdf.getPage(link.target).ref,PDFLib.PDFName.of('Fit')]});link.page.node.addAnnot(pdf.context.register(a));}
  const seen=new Set(),outline=[];
  for(let i=0;i<plan.length;i++){const p=plan[i],id=p.section_id||(p.group==='Sources'?'sources':null);if(id&&!seen.has(id)){seen.add(id);outline.push({index:i,title:id==='sources'?'Sources':master.sections.find(s=>s.id===id).title});}}
  if(outline.length){
   const root=pdf.context.obj({Type:'Outlines',Count:outline.length}),rootRef=pdf.context.register(root),refs=outline.map(()=>pdf.context.nextRef());
   outline.forEach((entry,i)=>{const o=pdf.context.obj({Title:PDFLib.PDFHexString.fromText(entry.title),Parent:rootRef,Dest:[pdf.getPage(entry.index).ref,PDFLib.PDFName.of('Fit')]});if(i)o.set(PDFLib.PDFName.of('Prev'),refs[i-1]);if(i+1<refs.length)o.set(PDFLib.PDFName.of('Next'),refs[i+1]);pdf.context.assign(refs[i],o);});
   root.set(PDFLib.PDFName.of('First'),refs[0]);root.set(PDFLib.PDFName.of('Last'),refs[refs.length-1]);pdf.catalog.set(PDFLib.PDFName.of('Outlines'),rootRef);
  }
  pdf.setTitle(master.title+' Selected Sections');pdf.setAuthor(master.owner);pdf.setSubject(`Master revision ${master.revision}; sections ${ids.join(',')}`);pdf.setKeywords(['large print','amateur radio',master.revision]);
  const prefs=pdf.catalog.getOrCreateViewerPreferences();prefs.setDuplex(PDFLib.Duplex.DuplexFlipLongEdge);prefs.setPrintScaling(PDFLib.PrintScaling.None);
  return pdf.save();
 }
 function run(s,size=44,bold=false){return `<w:r><w:rPr><w:rFonts w:ascii="Helvetica" w:hAnsi="Helvetica"/><w:sz w:val="${size}"/>${bold?'<w:b/>':''}</w:rPr><w:t xml:space="preserve">${xml(s)}</w:t></w:r>`;}
 function paragraph(s,{heading=false,first=false,small=false,note=false,source=false,newpage=false}={}){return `<w:p><w:pPr>${heading?`<w:pStyle w:val="${first?'Title':'Heading1'}"/>`:''}${newpage?'<w:pageBreakBefore/>':''}<w:spacing w:after="${heading?340:source?0:220}" w:line="${heading?660:source?400:note?500:small?460:540}" w:lineRule="exact"/></w:pPr>${run(s,heading?56:source?32:note?40:small?36:44,heading)}</w:p>`;}
 function table(p){
  const rows=p.table,w=p.col_widths||[126,363.6];
  return `<w:tbl><w:tblPr><w:tblLayout w:type="fixed"/><w:tblBorders>${['top','left','bottom','right','insideH','insideV'].map(e=>`<w:${e} w:val="single" w:sz="4" w:color="D9D9D9"/>`).join('')}</w:tblBorders><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:left w:w="160" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>${w.map(n=>`<w:gridCol w:w="${Math.round(n*20)}"/>`).join('')}</w:tblGrid>${rows.map((row,ri)=>`<w:tr><w:trPr><w:cantSplit/>${ri===0?'<w:tblHeader/>':''}</w:trPr>${row.map((s,ci)=>`<w:tc><w:tcPr><w:tcW w:w="${Math.round(w[ci]*20)}" w:type="dxa"/>${ri===0?'<w:shd w:fill="E7E7E7"/>':''}<w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr><w:spacing w:after="0" w:line="${/^[.\-]+$/.test(s)?560:520}" w:lineRule="exact"/></w:pPr>${run(s,/^[.\-]+$/.test(s)?52:p.toc?40:44,ri===0||/^[.\-]+$/.test(s))}</w:p></w:tc>`).join('')}</w:tr>`).join('')}</w:tbl>`;
 }
 async function makeDOCX(master,ids,options={}){
  const plan=makePlan(master,ids,options),zip=new JSZip();
  const content=plan.map((p,i)=>paragraph(p.title,{heading:true,first:i===0,newpage:i>0})+(p.paragraphs||[]).map(s=>paragraph(s,{small:p.sources})).join('')+(p.table?table(p):'')+(p.note?paragraph(p.note,{note:true}):'')+(p.refs?paragraph('Sources '+p.refs,{source:true}):'')).join('');
  const ns='xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"';
  const sect='<w:sectPr><w:headerReference w:type="default" r:id="header"/><w:footerReference w:type="default" r:id="footer"/><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1123" w:right="864" w:bottom="1080" w:left="1584" w:header="360" w:footer="432"/></w:sectPr>';
  zip.file('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+[['/word/document.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'],['/word/styles.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml'],['/word/settings.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml'],['/word/header1.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml'],['/word/footer1.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml'],['/docProps/core.xml','application/vnd.openxmlformats-package.core-properties+xml']].map(([name,type])=>`<Override PartName="${name}" ContentType="${type}"/>`).join('')+'</Types>');
  zip.file('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="doc" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="core" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>');
  zip.file('word/document.xml',`<?xml version="1.0" encoding="UTF-8"?><w:document ${ns}><w:body>${content}${sect}</w:body></w:document>`);
  zip.file('word/_rels/document.xml.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+[['styles','styles','styles.xml'],['settings','settings','settings.xml'],['header','header','header1.xml'],['footer','footer','footer1.xml']].map(([id,type,target])=>`<Relationship Id="${id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/${type}" Target="${target}"/>`).join('')+'</Relationships>');
  zip.file('word/styles.xml',`<?xml version="1.0"?><w:styles ${ns}><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Helvetica" w:hAnsi="Helvetica"/><w:sz w:val="44"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>${['Title','Heading1'].map(s=>`<w:style w:type="paragraph" w:styleId="${s}"><w:name w:val="${s==='Title'?'Title':'heading 1'}"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="56"/></w:rPr></w:style>`).join('')}</w:styles>`);
  zip.file('word/settings.xml',`<?xml version="1.0"?><w:settings ${ns}><w:mirrorMargins/></w:settings>`);
  zip.file('word/header1.xml',`<?xml version="1.0"?><w:hdr ${ns}><w:p>${run('AB9MZ | Field Reference | Edition '+master.edition,32)}</w:p></w:hdr>`);
  zip.file('word/footer1.xml',`<?xml version="1.0"?><w:ftr ${ns}><w:p>${run(master.date+' | Edition '+master.edition+' | Page ',32)}<w:fldSimple w:instr="PAGE">${run('1',32)}</w:fldSimple></w:p></w:ftr>`);
  zip.file('docProps/core.xml',`<?xml version="1.0"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>${xml(master.title)}</dc:title><dc:creator>${xml(master.owner)}</dc:creator><dc:description>${xml('Master revision '+master.revision+'; sections '+ids.join(','))}</dc:description></cp:coreProperties>`);
  return zip.generateAsync({type:'uint8array',compression:'DEFLATE'});
 }
 return {choose,makePlan,makePDF,makeDOCX};
});
