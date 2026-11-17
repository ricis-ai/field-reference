from pathlib import Path
import sys,json,hashlib,copy
import render_support as b
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame

HERE=Path(__file__).resolve().parent
master=json.loads((HERE/'master.json').read_text())
sections=master['sections'];section_ids=[s['id'] for s in sections];page_ids=[p['id'] for s in sections for p in s['pages']]
if len(section_ids)!=len(set(section_ids)) or len(page_ids)!=len(set(page_ids)):raise ValueError('Master contains duplicate section or page identifiers.')
source_ids={s['id'] for s in master['sources']}
for s in sections:
 for p in s['pages']:
  used={int(n.strip()) for n in str(p.get('refs','')).split(',') if n.strip()}
  if not used<=source_ids:raise ValueError('Unknown source reference in '+p['title'])
  if p.get('table'):
   cols=len(p['table'][0]);widths=b.colwidths(p)
   if len(widths)!=cols or any(len(row)!=cols for row in p['table']) or abs(sum(widths)-489.6)>.1:raise ValueError('Invalid table geometry in '+p['title'])
master['revision']=hashlib.sha256((HERE/'master.json').read_bytes()).hexdigest()[:12]
source_pages=[]
for start in range(0,len(master['sources']),2):
 entries=master['sources'][start:start+2];paras=[]
 for s in entries:paras.extend([f'{s["id"]}. {s["title"]}: {s["description"]}',s['url']])
 source_pages.append(dict(id=f'sources-{start+1}',title=f'Sources {start+1} to {start+len(entries)}',paragraphs=paras,sources=True,source_ids=[s['id'] for s in entries],group='Sources',refs='',note=''))
master['source_pages']=source_pages
allpages=[p for s in master['sections'] for p in s['pages']]+source_pages
c=canvas.Canvas(str(HERE/'content_archive.pdf'),pagesize=(612,792),pageCompression=1)
c.setTitle('Field Reference master content archive '+master['revision'])
errors=[]
for i,p in enumerate(allpages):
 p['archiveIndex']=i
 if p.get('table'):p['col_widths']=b.colwidths(p)
 c.setFont('Helvetica',14);c.drawString(79.2,760,'AB9MZ | Field Reference | Edition '+master['edition'])
 fs=b.flowables(p)
 frame=Frame(79.2,76,489.6,660,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
 frame.addFromList(fs,c)
 if fs:errors.append((i,p['title']))
 if p.get('refs'):
  c.setFont('Helvetica',14);c.drawString(79.2,54,'Sources '+p['refs'])
 c.showPage()
c.save()
if errors:raise RuntimeError('Page overflow '+repr(errors))
(HERE/'compiled_master.json').write_text(json.dumps(master,ensure_ascii=False,indent=2))
print('Archive prepared',len(allpages),'pages; revision',master['revision'])
