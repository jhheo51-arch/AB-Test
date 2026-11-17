"""Render and package the v0.3 review chapter and synthetic data."""
import json
import zipfile
from pathlib import Path
import pymupdf
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/exports/v03'
REVIEW=ROOT/'e-book/design/v03/review';REVIEW.mkdir(parents=True,exist_ok=True)
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1200,'height':1000})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((OUT/'sample_and_data_chapter_v03.html').as_uri())
    page.evaluate('document.fonts.ready')
    assert page.locator('.meter').count()==5
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.locator('.proof').scroll_into_view_if_needed()
    page.screenshot(path=str(REVIEW/'information_readiness.png'),full_page=False)
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.pdf(path=str(OUT/'sample_and_data_chapter_v03.pdf'),print_background=True,prefer_css_page_size=True,outline=True,tagged=True,display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:9px;width:100%;text-align:center;color:#526168">허재혁 · 표본과 데이터 설계 개정 장 v0.3 · <span class="pageNumber"></span></div>')
    browser.close()
assert not errors,errors
doc=pymupdf.open(OUT/'sample_and_data_chapter_v03.pdf')
texts=[p.get_text() for p in doc];text='\n'.join(texts)
for term in ['허재혁','120,000','65,559','2,000','431,212','Bonferroni']:
    assert term in text,term
bad=[]
for i,page in enumerate(doc):
    for word in page.get_text('words'):
        if word[0]<0 or word[1]<0 or word[2]>page.rect.width+.5 or word[3]>page.rect.height+.5:bad.append((i+1,word[4]))
assert not bad,bad
for start in range(0,len(doc),12):
    sheet=Image.new('RGB',(900,4*430),'#e1e5e3');draw=ImageDraw.Draw(sheet)
    for j,k in enumerate(range(start,min(start+12,len(doc)))):
        pix=doc[k].get_pixmap(matrix=pymupdf.Matrix(.45,.45),alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((280,395))
        x=(j%3)*300+10;y=(j//3)*430+24;sheet.paste(im,(x,y));draw.text((x,y-17),f'Page {k+1}',fill='black')
    sheet.save(REVIEW/f'contact_{start+1:02d}.png')
validation={'pages':len(doc),'page_text_lengths':[len(x) for x in texts],'outside_page_words':bad,'js_errors':errors,'readiness_bars':5,'mobile_desktop_overflow':False,'status':'Rendering and structural checks only, not statistical/domain/reader/rights approval'}
(OUT/'validation_v03.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
files=[f for parent in [ROOT/'e-book/virtual-data/v03',OUT] for f in parent.rglob('*') if f.is_file()]
files.append(ROOT/'e-book/virtual-company/JH_Motors_v03.md')
for name in ['plan_oem_v03.py','build_oem_v03.py','analyze_oem_v03.py','simulate_information_v03.py','build_v03_chapter.py','render_package_v03.py']:files.append(ROOT/'scripts'/name)
path=ROOT/'JH_Motors_data_and_chapter_v03.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(set(files)):z.write(f,f.relative_to(ROOT))
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    count=len(z.namelist())
print(json.dumps({'validation':validation,'package':str(path),'package_files':count,'package_bytes':path.stat().st_size},ensure_ascii=False,indent=2))
