"""Render and verify the method-led v0.5 main book.
uv run --with playwright --with pymupdf --with pillow scripts/render_verify_v05.py
"""
import json,re,hashlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
import pymupdf
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v05';REVIEW=ROOT/'e-book/design/v05/review';REVIEW.mkdir(parents=True,exist_ok=True)
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';errors=[]
htmlfile=OUT/'ebook_review_v05.html';pdfpath=OUT/'ebook_review_v05.pdf'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True);page=browser.new_page(viewport={'width':1200,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(htmlfile.as_uri());page.evaluate('document.fonts.ready')
    visible=page.locator('body').inner_text();assert not any(c in visible for c in forbidden)
    assert '{{' not in visible
    assert page.locator('h2.case-opening').count()==6 and page.locator('h3').count()==0
    assert page.locator('svg').count()==3
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path=str(REVIEW/'cover_desktop.png'))
    page.locator('h1').filter(has_text='1장 트리아타시스라는 관점').scroll_into_view_if_needed();page.screenshot(path=str(REVIEW/'method_desktop.png'))
    page.set_viewport_size({'width':390,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path=str(REVIEW/'method_mobile.png'))
    page.set_viewport_size({'width':1200,'height':1000});page.emulate_media(media='print')
    overflow=page.evaluate('''[...document.querySelectorAll('table,pre,svg')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>e.tagName)''');assert not overflow,overflow
    footer='<div style="font-family:Arial,sans-serif;font-size:9px;width:100%;padding:0 18mm;color:#526168;display:flex;justify-content:space-between"><span>허재혁</span><span class="pageNumber"></span></div>'
    page.pdf(path=str(pdfpath),print_background=True,prefer_css_page_size=True,outline=True,tagged=True,display_header_footer=True,header_template='<span></span>',footer_template=footer)
    browser_version=browser.version;browser.close()
assert not errors,errors
d=pymupdf.open(pdfpath);d.set_metadata({'title':'그래서, 이 캠페인 계속할까요? — 트리아타시스와 TRI-V','author':'허재혁','subject':'저자 검토본 0.5. 방법론 중심의 서술형 개정판.','keywords':'CRM,A/B,Tri-Ataxis,TRI-V,JH Motors'});d.saveIncr()
texts=[p.get_text() for p in d];flat='\n'.join(texts);toc=d.get_toc()
assert not any(c in flat for c in forbidden),[(c,flat.count(c)) for c in forbidden if c in flat]
for term in ['허재혁','트리아타시스','Tri-Ataxis','Variable Control','Vector Segmentation','Value-Linked Decision','정화','입체화','언어의 전환','0.00274','0.1750','Welch','상호작용']:
    assert term in flat,term
case_pages={}
for i in range(1,7):
    found=[t[2] for t in toc if re.match(rf'^사례\s*{i}\s',t[1])];assert len(found)==1,(i,found)
    assert re.search(rf'^사례\s*{i}\s',texts[found[0]-1],re.M)
    case_pages[str(i)]=found[0]
method_pages={}
for i in range(1,5):
    found=[t[2] for t in toc if re.match(rf'^{i}장\s',t[1])];assert len(found)==1,(i,found);method_pages[str(i)]=found[0]
outside=[];footer_overlap=[]
for i,pg in enumerate(d):
    for w in pg.get_text('words'):
        if w[0]<-.5 or w[1]<-.5 or w[2]>pg.rect.width+.5 or w[3]>pg.rect.height+.5:outside.append((i+1,w[4]))
        if w[1]<790 and w[3]>pg.rect.height-53:footer_overlap.append((i+1,w[4]))
assert not outside,outside[:10];assert not footer_overlap,footer_overlap[:10]
fonts=[]
font_rows={f[0]:f for p in d for f in p.get_fonts(full=True) if f[0]}
for ref,fontrow in sorted(font_rows.items()):
    name,ext,typ,buf=d.extract_font(ref)
    if fontrow[2]=='Type3':
        kind,procs=d.xref_get_key(ref,'CharProcs')
        refs=[int(n) for n in re.findall(r'(\d+)\s+0\s+R',procs)]
        if kind=='xref':
            procs=d.xref_object(refs[0]);refs=[int(n) for n in re.findall(r'(\d+)\s+0\s+R',procs)]
        assert refs and all(d.xref_is_stream(n) for n in refs)
        fonts.append({'name':'PDF Type3 glyph programs','extension':'CharProcs','embedded_bytes':sum(len(d.xref_stream(n)) for n in refs)})
    else:
        assert buf,(ref,name,typ);fonts.append({'name':name,'extension':ext,'embedded_bytes':len(buf)})
links=0
for p in d:
    for link in p.get_links():
        links+=1
        if link['kind']==pymupdf.LINK_GOTO:assert 0<=link.get('page',-1)<len(d)
sparse=[i+1 for i,t in enumerate(texts) if len(t)<180]
# Remove only stale generated preview images from this edition's own directory.
for f in REVIEW.glob('contact_*.png'):f.unlink()
for f in REVIEW.glob('page_*.png'):f.unlink()
for start in range(0,len(d),12):
    sheet=Image.new('RGB',(1200,1800),'#e1e5e3');draw=ImageDraw.Draw(sheet)
    for n,idx in enumerate(range(start,min(start+12,len(d)))):
        pix=d[idx].get_pixmap(matrix=pymupdf.Matrix(.55,.55),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((380,414));x=n%3*400+10;y=n//3*450+26;sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {idx+1}',fill='black')
    sheet.save(REVIEW/f'contact_{start+1:03d}.png')
for idx in sorted(set([0]+[p-1 for p in method_pages.values()]+[case_pages['2']-1,case_pages['5']-1])):
    d[idx].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(REVIEW/f'page_{idx+1:03d}.png')
old=(ROOT/'e-book/exports/v04/ebook_review_v04.md').read_text(encoding='utf-8');new=(OUT/'ebook_review_v05.md').read_text(encoding='utf-8')
report={'version':'0.5 author review','checked_at_seoul':datetime.now(timezone(timedelta(hours=9),'Asia/Seoul')).isoformat(),'pdf_pages':len(d),'pdf_bytes':pdfpath.stat().st_size,'pdf_sha256':hashlib.sha256(pdfpath.read_bytes()).hexdigest(),'author':d.metadata['author'],'methodology_chapter_start_pages':method_pages,'case_start_pages':case_pages,'toc_entries':len(toc),'links':links,'outside_page_words':outside,'footer_overlap':footer_overlap,'fonts':fonts,'page_text_lengths':[len(t) for t in texts],'sparse_pages_under180_chars':sparse,'middle_dot_counts':{f'U+{ord(c):04X}':flat.count(c) for c in forbidden},'paragraph_microheadings':{'previous_h3':len(re.findall(r'^### ',old,re.M)),'new_h3':len(re.findall(r'^### ',new,re.M)),'new_other_h2':len(re.findall(r'^## ',new,re.M))-6},'browser_version':browser_version,'browser_errors':errors,'desktop_mobile_overflow':False,'unresolved_templates':False,'numeric_sources':'Unchanged v0.4 verified analysis + v0.3 plan/repeated sampling; editorial rewrite, not new statistical inference','palette':'Same previously checked ink/teal/muted on white/paper; min text contrast5.85:1; not new company branding','review_limits':['Naturalness and author voice require author confirmation; no claim that AI involvement is undetectable','Human statistical/OEM/reader/rights/publication review pending','Historical v0.4 companion files were not re-edited in this main-book revision']}
(OUT/'validation_v05.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['fonts','page_text_lengths']},ensure_ascii=False,indent=2))
