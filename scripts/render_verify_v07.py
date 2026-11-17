"""Render book geometry, linked contents, same-layout length controls and page checks."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import re,json,hashlib
import pymupdf
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v07';REVIEW=ROOT/'e-book/design/v07/review';REVIEW.mkdir(parents=True,exist_ok=True)
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';errors=[]
htmlpath=OUT/'ebook_review_v07.html';pdfpath=OUT/'ebook_review_v07.pdf'
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':1200,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(htmlpath.as_uri());page.evaluate('document.fonts.ready');page.wait_for_timeout(200)
 assert page.locator('.chapter').count()==12
 assert page.locator('.case-opening').count()==6
 assert page.locator('a[id^="g-"]').count()==36
 assert not any(c in page.locator('body').inner_text() for c in forbidden)
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 broken=page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash)");assert not broken,broken
 page.screenshot(path=str(REVIEW/'cover_desktop.png'))
 page.locator('.chapter').first.scroll_into_view_if_needed();page.screenshot(path=str(REVIEW/'method_desktop.png'))
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);assert not page.evaluate('document.documentElement.scrollWidth>innerWidth');page.screenshot(path=str(REVIEW/'method_mobile.png'))
 page.set_viewport_size({'width':1200,'height':1000});page.emulate_media(media='print')
 overflow=page.evaluate("[...document.querySelectorAll('.reading table,.reading pre,.reading svg')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>e.tagName)");assert not overflow,overflow
 page.pdf(path=str(pdfpath),print_background=True,prefer_css_page_size=True,outline=True,tagged=True)
 with pymupdf.open(pdfpath) as d:tocfirst=[[x[0],re.sub(r'^CHAPTER\s*\d{2}\s*','',x[1]),x[2]] for x in d.get_toc()];first_count=len(d)
 headings=page.locator('.contents a').evaluate_all('(es)=>es.map(e=>({id:e.hash.slice(1),label:e.firstElementChild.textContent}))')
 for h in headings:
  pages=[x[2] for x in tocfirst if x[1]==h['label']]
  assert len(pages)==1,(h,pages)
  page.locator('.folio[data-id="'+h['id']+'"]').evaluate('(e,n)=>e.textContent=n',pages[0])
 # Persist filled folios into the actual reader HTML, not only a screenshot.
 htmlpath.write_text('<!doctype html>\n'+page.locator('html').evaluate('(e)=>e.outerHTML'),encoding='utf-8')
 page.pdf(path=str(pdfpath),print_background=True,prefer_css_page_size=True,outline=True,tagged=True)
 # Render both versions under the same A4 body-only typography. No cover/contents included.
 control_counts={}
 for version in ['v06','v07']:
  if version=='v06':
   import markdown
   oldhtml=(ROOT/'e-book/exports/v06/ebook_review_v06.html').read_text(encoding='utf-8');oldcss=re.search('<style>(.*?)</style>',oldhtml,re.S)[1];text=(ROOT/'e-book/exports/v06/ebook_review_v06.md').read_text(encoding='utf-8');body=markdown.markdown(text,extensions=['tables','toc','fenced_code'])
   for svg in (ROOT/'e-book/exports/v06').glob('*.svg'):body=re.sub(r'<img[^>]+src="'+re.escape(svg.name)+'"[^>]*/?>',lambda m:svg.read_text(encoding='utf-8'),body)
   ctrl=OUT/'content_control_A4_v06.html';ctrl.write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><style>'+oldcss+'</style><main>'+body+'</main></html>',encoding='utf-8')
  else:ctrl=OUT/'content_control_A4_v07.html'
  cp=browser.new_page();cp.goto(ctrl.as_uri());cp.evaluate('document.fonts.ready');target=OUT/f'content_control_A4_{version}.pdf';cp.pdf(path=str(target),print_background=True,prefer_css_page_size=True)
  with pymupdf.open(target) as d:control_counts[version]=len(d)
  cp.close()
 version=browser.version;browser.close()
assert not errors,errors
with pymupdf.open(pdfpath) as d:
 assert len(d)==first_count,'Filling contents changed pagination'
 toc=[[x[0],re.sub(r'^CHAPTER\s*\d{2}\s*','',x[1]),x[2]] for x in d.get_toc()];assert toc==tocfirst
 d.set_toc(toc)
 d.set_metadata({'title':'그래서, 이 캠페인 계속할까요?','author':'허재혁','subject':'CRM A/B 테스트 실무서, 저자 검토본0.7','keywords':'CRM,A/B,TRI-V,맥락항법,JH Motors'})
 for i,pg in enumerate(d):
  if i>0:pg.insert_text((pg.rect.width-40,pg.rect.height-22),str(i+1),fontname='helv',fontsize=9,color=(.31,.38,.37))
 d.saveIncr()
with pymupdf.open(pdfpath) as d:
 texts=[pg.get_text() for pg in d];flat='\n'.join(texts);assert not any(c in flat for c in forbidden)
 body_probe=next(x[2] for x in toc if re.match(r'^5장 ',x[1]))
 serif_sizes=[s['size'] for b in d[body_probe].get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans'] if s['font']!='Helvetica' and s['text'].strip()]
 assert serif_sizes and min(serif_sizes)>=11.9,('Reading-body probe was scaled below12pt',min(serif_sizes) if serif_sizes else None)
 for term in ['허재혁','맥락항법','Variable Control','Vector Segmentation','Value-Linked Decision','0.00274','0.1750','상호작용','Welch','한 건의 캠페인','검정력','키워드 찾아보기']:assert term in flat,term
 chapters={str(i):next(x[2] for x in toc if re.match(rf'^{i}장 ',x[1])) for i in range(1,13)}
 cases={str(i):next(x[2] for x in toc if re.match(rf'^사례 {i} ',x[1])) for i in range(1,7)}
 for i,n in chapters.items():assert re.search(rf'CHAPTER\s*{int(i):02d}',texts[n-1]),('orphan chapter number',i,n)
 for key,n in cases.items():assert re.search(rf'^사례 {key} ',texts[n-1],re.M)
 glossary=next(x[2] for x in toc if x[1]=='키워드 찾아보기와 설명')
 outside=[];footeroverlap=[]
 for i,pg in enumerate(d):
  for w in pg.get_text('words'):
   if w[0]<-.5 or w[1]<-.5 or w[2]>pg.rect.width+.5 or w[3]>pg.rect.height+.5:outside.append((i+1,w[4]))
   if i>0 and w[1]<pg.rect.height-40 and w[3]>pg.rect.height-39:footeroverlap.append((i+1,w[4]))
 assert not outside,outside[:12];assert not footeroverlap,footeroverlap[:12]
 fontrows={f[0]:f for p in d for f in p.get_fonts(full=True) if f[0]};fonts=[]
 for ref,row in fontrows.items():
  name,ext,typ,buf=d.extract_font(ref)
  if row[2]=='Type3':
   kind,procs=d.xref_get_key(ref,'CharProcs');refs=[int(x) for x in re.findall(r'(\d+)\s+0\s+R',procs)]
   if kind=='xref':refs=[int(x) for x in re.findall(r'(\d+)\s+0\s+R',d.xref_object(refs[0]))]
   assert refs and all(d.xref_is_stream(x) for x in refs);fonts.append({'name':'Type3 glyph programs','bytes':sum(len(d.xref_stream(x)) for x in refs)})
  elif name in ['Helvetica','ArialMT'] and not buf:fonts.append({'name':name,'use':'standard PDF folio font'})
  else:assert buf,(ref,name,typ);fonts.append({'name':name,'bytes':len(buf)})
 links=0
 for pg in d:
  for link in pg.get_links():
   links+=1
   if link['kind']==pymupdf.LINK_GOTO:assert 0<=link['page']<len(d)
 for f in REVIEW.glob('contact_*.png'):f.unlink()
 for start in range(0,len(d),12):
  sheet=Image.new('RGB',(1200,1800),'#E1E5E0');draw=ImageDraw.Draw(sheet)
  for n,idx in enumerate(range(start,min(start+12,len(d)))):
   pix=d[idx].get_pixmap(matrix=pymupdf.Matrix(.65,.65),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((380,414));x=n%3*400+10;y=n//3*450+26;sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {idx+1}',fill='black')
  sheet.save(REVIEW/f'contact_{start+1:03d}.png')
 for n in sorted({1,chapters['1'],chapters['5'],chapters['6'],chapters['12'],cases['5'],glossary}):d[n-1].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).save(REVIEW/f'page_{n:03d}.png')
 manifest=json.loads((OUT/'build_manifest_v07.json').read_text(encoding='utf-8'))
 report={'version':'0.7 author review','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'pdf_pages':len(d),'pdf_bytes':pdfpath.stat().st_size,'pdf_sha256':hashlib.sha256(pdfpath.read_bytes()).hexdigest(),'page_geometry_mm':[190,270],'actual_pdf_reading_body_probe_min_pt':min(serif_sizes),'chapter_start_pages':chapters,'case_start_pages':cases,'glossary_start_page':glossary,'glossary_entries':36,'toc_entries':len(toc),'links':links,'contents_have_printed_page_numbers':True,'same_A4_body_only_control_pages':control_counts,'source_characters':manifest['source_characters'],'previous_v06_characters':manifest['previous_v06_characters'],'outside_words':outside,'footer_overlap':footeroverlap,'browser_errors':errors,'desktop_mobile_overflow':False,'broken_internal_links':broken,'fonts':fonts,'middle_dot_counts':{f'U+{ord(c):04X}':flat.count(c) for c in forbidden},'sparse_pages_under180chars':[i+1 for i,t in enumerate(texts) if len(t)<180],'all_heading_pages':[{'title':t[1],'page':t[2]} for t in toc],'browser_version':version,'limits':['Automated checks and simulated personas do not establish publication quality','Real reader tests, human technical and rights review remain pending','Page-size change separately measured from actual text expansion']}
(OUT/'validation_v07.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['fonts','all_heading_pages']},ensure_ascii=False,indent=2))
