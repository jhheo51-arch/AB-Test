"""Paginate the full v19 book with real footnotes, folios and repaired PDF navigation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,re,hashlib,math
from PIL import Image,ImageDraw
import pymupdf
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v19';REVIEW=ROOT/'e-book/design/v19/review';REVIEW.mkdir(parents=True,exist_ok=True)
source=OUT/'ebook_review_v19_print.html';reader=OUT/'ebook_review_v19.html';pdfpath=OUT/'ebook_review_v19.pdf';errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':1100,'height':1000});page.set_default_timeout(120000);page.on('pageerror',lambda e:errors.append(str(e)));page.goto(source.as_uri());page.evaluate('document.fonts.ready')
 # Fit oversized footer labels by wrapping, never by shrinking the figure fonts.
 edits=page.evaluate('''() => [...document.querySelectorAll('figure[data-figure]')].map(fig=>{
 const svg=fig.querySelector('svg'),vb=svg.viewBox.baseVal;let changed=false;
 for(const text of [...svg.querySelectorAll('text')]){
  let b=text.getBBox();if(b.x+b.width>vb.width-8){
   const x=parseFloat(text.getAttribute('x')||0),y=parseFloat(text.getAttribute('y')||0),fs=parseFloat(text.getAttribute('font-size')||28),words=text.textContent.trim().split(/\\s+/);let lines=[],line='';
   text.textContent='';const test=document.createElementNS('http://www.w3.org/2000/svg','tspan');text.append(test);
   for(const word of words){test.textContent=(line?line+' ':'')+word;if(test.getComputedTextLength()>vb.width-x-12&&line){lines.push(line);line=word}else line=test.textContent}
   if(line)lines.push(line);text.textContent='';lines.forEach((v,i)=>{let sp=document.createElementNS('http://www.w3.org/2000/svg','tspan');sp.setAttribute('x',x);sp.setAttribute('y',y+i*fs*1.3);sp.textContent=v;text.append(sp)});changed=true;
  }
 }
 let bottom=vb.height;for(const text of svg.querySelectorAll('text')){const b=text.getBBox();bottom=Math.max(bottom,b.y+b.height+10)}
 if(bottom>vb.height){svg.setAttribute('viewBox',`${vb.x} ${vb.y} ${vb.width} ${bottom}`);changed=true}
 const overflow=[...svg.querySelectorAll('text')].filter(t=>{let b=t.getBBox();return b.x<-1||b.x+b.width>svg.viewBox.baseVal.width+1||b.y<-1||b.y+b.height>svg.viewBox.baseVal.height+1}).map(t=>t.textContent);
 return {name:fig.dataset.figure,changed,svg:svg.outerHTML,overflow};})''')
 html=source.read_text(encoding='utf-8');readhtml=reader.read_text(encoding='utf-8')
 for edit in edits:
  assert not edit['overflow'],edit
  if edit['changed']:
   old=(OUT/edit['name']).read_text(encoding='utf-8');html=html.replace(old,edit['svg']);readhtml=readhtml.replace(old,edit['svg']);(OUT/edit['name']).write_text(edit['svg'],encoding='utf-8',newline='\n')
 source.write_text(html,encoding='utf-8',newline='\n');reader.write_text(readhtml,encoding='utf-8',newline='\n')
 stable=None
 for attempt in range(5):
  page.goto(source.as_uri());page.evaluate('document.fonts.ready');page.evaluate('async()=>{let f=await PagedPolyfill.preview();window.renderedPages=f.total;}')
  mapping=page.evaluate('''() => {const rows=[...document.querySelectorAll('.pagedjs_pages h1[id],.pagedjs_pages h2[id]')];return rows.map(e=>({id:e.id,label:e.textContent.replace(/^CHAPTER\\s*\\d{2}\\s*/,'').trim(),level:e.tagName==='H1'?1:2,page:Number(e.closest('.pagedjs_page').dataset.pageNumber)}))}''')
  pagecount=page.evaluate('window.renderedPages');current={r['id']:r['page'] for r in mapping};current.update(page.evaluate("Object.fromEntries([...document.querySelectorAll('.pagedjs_pages [id^=g-],.pagedjs_pages [id^=b-],.pagedjs_pages [id^=case-],.pagedjs_pages [id^=materials-case-]')].map(e=>[e.id,Number(e.closest('.pagedjs_page').dataset.pageNumber)]))"));updated=html
  for key,n in current.items():updated=re.sub(r'(<span class="folio" data-id="'+re.escape(key)+r'">).*?(</span>)',lambda m:m[1]+str(n)+m[2],updated)
  if stable==(pagecount,current):break
  stable=(pagecount,current);html=updated;source.write_text(html,encoding='utf-8',newline='\n')
 else:raise AssertionError('Contents pagination did not stabilize')
 # Number identity is taken from the source note ID, not a page-final counter.
 numbering=page.evaluate('''()=>{let rules=[],rows=[];for(let n of document.querySelectorAll('.pagedjs_footnote_content [data-note-id]')){let k=Number(n.dataset.noteId.replace('fn-','')),c=[...document.querySelectorAll('[data-footnote-call]')].find(c=>c.dataset.ref===n.dataset.ref);if(!c)throw Error('No caller '+k);n.dataset.noteNumber=k;c.dataset.noteNumber=k;rules.push('[data-note-id="'+n.dataset.noteId+'"]::marker{content:"'+k+'. "!important}');rules.push('[data-footnote-call][data-ref="'+n.dataset.ref+'"]::after{content:"'+k+'"!important}');rows.push({id:n.dataset.noteId,number:k})}let s=document.createElement('style');s.textContent=rules.join('\\n');document.head.append(s);return rows}''')
 assert sorted(n['number'] for n in numbering)==list(range(1,9))
 # DOM page membership is the authority for notes and internal PDF destinations.
 notes=page.evaluate('''() => [...document.querySelectorAll('.pagedjs_footnote_content [data-note-id]')].map(e=>{let pg=e.closest('.pagedjs_page'),pr=pg.getBoundingClientRect(),r=e.getBoundingClientRect(),ref=e.dataset.ref,call=[...document.querySelectorAll('[data-footnote-call]')].find(c=>c.dataset.ref===ref);return {number:Number(e.dataset.noteNumber),marker_content:getComputedStyle(e,'::marker').content,caller_content:call?getComputedStyle(call,'::after').content:null,id:e.dataset.noteId,text:e.textContent,page:Number(pg.dataset.pageNumber),callerPage:call?Number(call.closest('.pagedjs_page').dataset.pageNumber):null,y:(r.top-pr.top)*.75,bottom:(r.bottom-pr.top)*.75,body:pg.querySelector('.pagedjs_page_content').getBoundingClientRect().bottom-pr.top}})''')
 expected=json.loads((OUT/'FOOTNOTES.json').read_text(encoding='utf-8'))['notes'];assert len(notes)==len(expected) and {n['id'] for n in notes}=={n['id'] for n in expected};assert all(n['page']==n['callerPage'] for n in notes),notes
 destinations=page.evaluate('''() => Object.fromEntries([...document.querySelectorAll('.pagedjs_pages [id]')].map(e=>{let p=e.closest('.pagedjs_page'),r=e.getBoundingClientRect(),pr=p.getBoundingClientRect();return [e.id,{page:Number(p.dataset.pageNumber)-1,y:(r.top-pr.top)*.75}]}))''')
 links=page.evaluate('''() => [...document.querySelectorAll('.pagedjs_pages a[href^="#"]')].map(e=>{let p=e.closest('.pagedjs_page'),r=e.getBoundingClientRect(),pr=p.getBoundingClientRect();return {source:Number(p.dataset.pageNumber)-1,href:decodeURIComponent(e.hash.slice(1)),rect:[(r.left-pr.left)*.75,(r.top-pr.top)*.75,(r.right-pr.left)*.75,(r.bottom-pr.top)*.75]}}).filter(l=>l.rect[2]>l.rect[0]&&l.rect[3]>l.rect[1])''')
 missing=[l for l in links if l['href'] not in destinations];assert not missing,missing
 unit_layout=page.evaluate('''()=>[...document.querySelectorAll('.pagedjs_pages [data-layout-unit]')].map(e=>({unit:e.dataset.layoutUnit,tag:e.tagName,cls:e.className,page:Number(e.closest('.pagedjs_page').dataset.pageNumber),text:e.textContent.trim().slice(0,90)}))''')
 for unit in {u['unit'] for u in unit_layout}:
  rows=[u for u in unit_layout if u['unit']==unit]
  assert len({u['page'] for u in rows})==1,rows
 figure_layout=page.evaluate('''() => [...document.querySelectorAll('.pagedjs_pages figure[data-figure]')].map(f=>{let s=f.querySelector('svg'),vb=s.viewBox.baseVal,w=s.getBoundingClientRect().width;return {file:f.dataset.figure,page:Number(f.closest('.pagedjs_page').dataset.pageNumber),minimum_label_pt:Math.min(...[...s.querySelectorAll('text')].map(t=>parseFloat(getComputedStyle(t).fontSize)*w/vb.width*.75)),caption:f.querySelector('figcaption').textContent}})''')
 assert all(n['y']>=n['body']*.75-1 for n in notes),'A footnote overlaps the body frame'
 page.pdf(path=str(pdfpath),print_background=True,prefer_css_page_size=True,outline=True,tagged=True)
 # Fill the normal reading edition's matching contents; keep it responsive and unpaginated.
 for key,n in current.items():readhtml=re.sub(r'(<span class="folio" data-id="'+re.escape(key)+r'">).*?(</span>)',lambda m:m[1]+str(n)+m[2],readhtml)
 reader.write_text(readhtml,encoding='utf-8',newline='\n')
 mdpath=OUT/'ebook_review_v19.md';md=mdpath.read_text(encoding='utf-8')
 for key,n in current.items():md=re.sub(r'(<span class="folio" data-id="'+re.escape(key)+r'">).*?(</span>)',lambda m:m[1]+str(n)+m[2],md)
 mdpath.write_text(md,encoding='utf-8',newline='\n')
 q=browser.new_page(viewport={'width':1200,'height':900});q.on('pageerror',lambda e:errors.append(str(e)));q.goto(reader.as_uri());q.evaluate('document.fonts.ready');assert q.locator('.chapter').count()==12;assert q.locator('figure').count()==13
 assert not q.evaluate('document.documentElement.scrollWidth>innerWidth');q.locator('#term-search').fill('SRM');assert q.locator('.index-table tbody tr:visible').count()==1;q.locator('#term-clear').click();assert q.locator('.index-table tbody tr:visible').count()==36;q.screenshot(path=str(REVIEW/'reader_desktop.png'));q.set_viewport_size({'width':390,'height':844});assert not q.evaluate('document.documentElement.scrollWidth>innerWidth');q.screenshot(path=str(REVIEW/'reader_mobile.png'));q.close();browser_version=browser.version;browser.close()
assert not errors,errors
with pymupdf.open(pdfpath) as d:
 assert len(d)==pagecount,(len(d),pagecount)
 toc=[];seen=set()
 for r in mapping:
  if r['id'] in seen:continue
  seen.add(r['id']);toc.append([r['level'],r['label'],r['page']])
 d.set_toc(toc);d.set_metadata({'title':'그래서, 이 캠페인 계속할까요?','author':'허재혁','subject':'TRI-V 시각 편집 저자 검토본0.19','keywords':'CRM,A/B,TRI-V,JH Motors'})
 for pg in d:
  for link in pg.get_links():
   if link['kind']==pymupdf.LINK_GOTO or (link['kind']==pymupdf.LINK_URI and link.get('uri','').startswith('file:')):pg.delete_link(link)
 for link in links:
  target=destinations[link['href']];d[link['source']].insert_link({'kind':pymupdf.LINK_GOTO,'from':pymupdf.Rect(link['rect']),'page':target['page'],'to':pymupdf.Point(0,max(0,target['y']))})
 d.saveIncr()
with pymupdf.open(pdfpath) as d:
 texts=[p.get_text() for p in d];flat='\n'.join(texts);compact=lambda s:re.sub(r'\s+','',s)
 assert not any(c in flat for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb')
 for n in notes:
  assert compact(n['text']) in compact(texts[n['page']-1]),n
  assert n['marker_content'].strip('\"')==str(n['number'])+'. ' and n['caller_content'].strip('\"')==str(n['number']),n
  fragment=d[n['page']-1].get_textbox(pymupdf.Rect(0,n['y']-1,d[0].rect.width,n['bottom']+1))
  assert re.search(r'(?m)^\s*'+str(n['number'])+r'\. ',fragment),(n,fragment)
  assert len(re.findall(r'(?m)^\s*'+str(n['number'])+r'\. ',texts[n['page']-1]))==1,n
 chapters={str(i):next(r[2] for r in toc if re.match(rf'^{i}장 ',r[1])) for i in range(1,13)};cases={str(i):next(r[2] for r in toc if re.match(rf'^사례 {i} ',r[1])) for i in range(1,7)}
 for n,pn in chapters.items():assert re.search(rf'CHAPTER\s*{int(n):02d}',texts[pn-1]),(n,pn)
 for n,pn in cases.items():assert re.search(rf'^사례 {n} ',texts[pn-1],re.M),(n,pn)
 for term in ['Variable Control','Vector Segmentation','Value-Linked Decision','0.00274','0.1750','67.4%','1.17pp']:assert compact(term) in compact(flat),term
 probe=d[chapters['5']-1];sizes=[s['size'] for b in probe.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans'] if s['text'].strip() and 36<s['bbox'][1]<probe.rect.height-55 and s['size']<15];assert sizes and min(sizes)>=11.9,sizes
 outside=[]
 for number,pg in enumerate(d,1):
  for w in pg.get_text('words'):
   if w[0]<-.6 or w[1]<-.6 or w[2]>pg.rect.width+.6 or w[3]>pg.rect.height+.6:outside.append((number,w[4]))
 assert not outside,outside[:10]
 selected={1,chapters['1'],chapters['5'],chapters['6'],chapters['8'],chapters['12'],cases['5']}|{n['page'] for n in notes}|{f['page'] for f in figure_layout if f['file'].endswith('_v19.svg')}
 for old_image in REVIEW.glob('page_*.png'):old_image.unlink()
 for n in sorted(selected):d[n-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(REVIEW/f'page_{n:03d}.png')
 figures=[f for f in figure_layout if f['file'] in ['tri_v_workflow_v19.svg','three_judgments_v19.svg','observation_maturity_v19.svg','decision_record_v19.svg']]
 assert len(figures)==4
 assert all(f['minimum_label_pt']>=11.9 for f in figure_layout),figure_layout
 report={'version':'0.19 reading-path and handoff author review','checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'pdf_pages':len(d),'pdf_bytes':pdfpath.stat().st_size,'pdf_sha256':hashlib.sha256(pdfpath.read_bytes()).hexdigest(),'page_geometry_mm':[190,270],'actual_pdf_reading_body_probe_min_pt':min(sizes),'chapter_start_pages':chapters,'case_start_pages':cases,'glossary_start_page':next(r[2] for r in toc if r[1]=='용어 해설'),'backmatter_pages':{name:next(r[2] for r in toc if r[1]==name) for name in ['찾아보기','용어 해설','참고자료와 계산 범위','부록 A 계산과 자료','부록 B 사례와 자료 길잡이']},'glossary_entries':36,'toc_entries':len(toc),'contents_have_printed_page_numbers':True,'links':sum(len(p.get_links()) for p in d),'footnotes':notes,'footnote_count':len(notes),'footnotes_on_caller_page':True,'lookup_pages':{k:n for k,n in current.items() if k.startswith(('g-','b-'))},'atomic_layout_units':unit_layout,'figure_count':13,'figure_layout':figure_layout,'new_concept_figures':figures,'outside_words':outside,'browser_errors':errors,'desktop_mobile_overflow':False,'browser_version':browser_version,'print_engine':'Paged.js0.4.3, pinned offline dependency','margins_mm':[14,15,16,15],'body_pt':12,'footnote_pt':12,'body_line_height':1.62,'limits':['AI/separate-code numeric review is not human approval','Footnote markers and folios are intentionally smaller than body type','Figure and whitespace inspection does not establish actual reader learning or publication release']}
(OUT/'validation_v19.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['footnotes','new_concept_figures']},ensure_ascii=False,indent=2));print('Footnotes:',[(n['id'],n['page'],n['callerPage']) for n in notes])
