from pathlib import Path
from html import escape
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

# Standard PDF Helvetica faces require no bundled font installation.
BODY=ParagraphStyle('Body',fontName='Helvetica',fontSize=22,leading=27,spaceAfter=11)
TITLE=ParagraphStyle('Title',parent=BODY,fontName='Helvetica-Bold',fontSize=28,leading=33,spaceAfter=17)
NOTE=ParagraphStyle('Note',parent=BODY,fontSize=20,leading=25,spaceBefore=10,spaceAfter=0)
SMALL=ParagraphStyle('Small',parent=BODY,fontSize=18,leading=23,spaceAfter=11)
CELL=ParagraphStyle('Cell',parent=BODY,fontSize=22,leading=26,spaceAfter=0)
HEAD=ParagraphStyle('Head',parent=CELL,fontName='Helvetica-Bold')
MONO=ParagraphStyle('Morse',parent=CELL,fontName='Helvetica-Bold',fontSize=26,leading=28)
def html_text(s):
 parts=[];last=0
 for m in re.finditer(r'(?<![A-Za-z0-9])[.\-]{2,}(?![A-Za-z0-9])',s):
  parts.append(escape(s[last:m.start()]));code=m.group();spoken=' '.join('dit' if c=='.' else 'dah' for c in code)
  parts.append(f'<span aria-hidden="true">{escape(code)}</span><span class="spoken">{spoken}</span>');last=m.end()
 parts.append(escape(s[last:]));return ''.join(parts)
def colwidths(p):
 if p.get('col_widths'):return p['col_widths']
 t=p['table'];n=len(t[0]);title=p['title']
 if title=='Signal reports':return [190,299.6]
 if title=='Dipole starting lengths':return [106,190,193.6]
 if n==1:return [489.6]
 if title in ('Microwave allocations','VHF privileges','UHF privileges'):return [220,269.6]
 if title in ('75 meter phone','40 meters'):return [210,279.6]
 if title.startswith('60 meters retained'):return [244.8,244.8]
 return [126,363.6]
def flowables(p):
 out=[Paragraph(escape(p['title']),TITLE)]
 for text in p.get('paragraphs',[]):
  if text.startswith('https://'):out.append(Paragraph('<link href="'+escape(text,quote=True)+'">'+escape(text)+'</link>',SMALL))
  else:out.append(Paragraph(escape(text),SMALL if p.get('sources') else BODY))
 if p.get('table'):
  data=[]
  for ri,row in enumerate(p['table']):
   line=[]
   for cell in row:
    sty=HEAD if ri==0 else CELL
    if ri and re.fullmatch(r'[.\-]+',cell):sty=MONO
    line.append(Paragraph(escape(cell),sty))
   data.append(line)
  t=Table(data,colWidths=colwidths(p),hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7E7E7')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));out.append(t)
 if p.get('note'):out.append(Paragraph(escape(p['note']),NOTE))
 return out
