"""Inspect the rendered PDF and create review contact sheets."""
import json
from pathlib import Path
import fitz
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/exports'
REVIEW=ROOT/'e-book/design/review_v01'
REVIEW.mkdir(parents=True,exist_ok=True)
doc=fitz.open(OUT/'reading_draft_v01.pdf')
issues=[]
lengths=[]
for i,page in enumerate(doc):
    lengths.append(len(page.get_text()))
    for word in page.get_text('words'):
        x0,y0,x1,y1=word[:4]
        if x0<0 or y0<0 or x1>page.rect.width+1 or y1>page.rect.height+1:
            issues.append({'page':i+1,'text':word[4],'bbox':word[:4]})
for start in range(0,len(doc),15):
    subset=list(range(start,min(start+15,len(doc))))
    sheet=Image.new('RGB',(900,5*450),'#e7e7e7')
    draw=ImageDraw.Draw(sheet)
    for j,index in enumerate(subset):
        pix=doc[index].get_pixmap(matrix=fitz.Matrix(0.48,0.48),alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        im.thumbnail((280,415))
        x=(j%3)*300+10;y=(j//3)*450+25
        sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {index+1}',fill='black')
    sheet.save(REVIEW/f'contact_{start+1:02d}.png')
fonts=sorted({f[3] for page in doc for f in page.get_fonts()})
report={'pages':len(doc),'page_text_lengths':lengths,'outside_page_words':issues,'fonts':fonts,'text_checks':{s:s in ''.join(p.get_text() for p in doc) for s in ['허재혁','현대자동차','기아','CRM-001','CRM-060']},'verification_limits':'Text extraction, media-box bounds and visual contact sheets; not technical/domain/rights review. Diagram labels are smaller than body text; final print diagram requires enlargement or separate spread.'}
assert not issues,issues
assert all(report['text_checks'].values())
(OUT/'pdf_validation_v01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
