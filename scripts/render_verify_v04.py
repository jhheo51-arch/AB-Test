"""Render the actual v0.4 full book, workbook, and separate existing card reference.
uv run --with playwright --with pymupdf --with pillow scripts/render_verify_v04.py
"""
import json,re,hashlib,zipfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pymupdf
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v04';REVIEW=ROOT/'e-book/design/v04/review';REVIEW.mkdir(parents=True,exist_ok=True)
errors=[];browser_checks={}
with sync_playwright() as p:
    # Installed Chrome avoids silently downloading/changing the user's browser.
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1200,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
    for stem in ['ebook_review_v04','workbook_v04']:
        page.goto((OUT/(stem+'.html')).as_uri());page.evaluate('document.fonts.ready')
        assert '{{' not in page.locator('body').inner_text()
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),stem
        if stem=='ebook_review_v04':
            assert page.locator('h2.case-opening').count()==6
            assert page.locator('svg').count()==2
            page.screenshot(path=str(REVIEW/'book_desktop.png'))
            page.locator('h2.case-opening').nth(1).scroll_into_view_if_needed();page.screenshot(path=str(REVIEW/'case2_desktop.png'))
        page.set_viewport_size({'width':390,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),stem+' mobile'
        page.set_viewport_size({'width':1200,'height':1000});page.emulate_media(media='print')
        bad=page.evaluate('''[...document.querySelectorAll('table,pre,svg')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>({tag:e.tagName,text:e.textContent.slice(0,60)}))''')
        assert not bad,bad
        footer='<div style="font-family:Arial,sans-serif;font-size:9px;width:100%;padding:0 18mm;color:#526168;display:flex;justify-content:space-between"><span>JH / CRM A/B / '+('BOOK' if stem=='ebook_review_v04' else 'WORKBOOK')+' / 0.4 AUTHOR REVIEW</span><span class="pageNumber"></span></div>'
        page.pdf(path=str(OUT/(stem+'.pdf')),print_background=True,prefer_css_page_size=True,outline=True,tagged=True,display_header_footer=True,header_template='<span></span>',footer_template=footer)
        browser_checks[stem]={'desktop_mobile_horizontal_overflow':False,'print_table_pre_svg_overflow':False}
    chrome_version=browser.version;browser.close()
assert not errors,errors
# Preserve historical card content as an independent reference, with no implication of six-case validation for all60.
old=ROOT/'e-book/exports/v02/ebook_review_v02.pdf';oldv=json.loads((ROOT/'e-book/exports/v02/validation_v02.json').read_text(encoding='utf-8'))
start=oldv['case_page_map']['CRM-001']-1;end=oldv['case_page_map']['CRM-060']-1
src=pymupdf.open(old);cards=pymupdf.open();cards.insert_pdf(src,from_page=start,to_page=end)
assert len(cards)==60
cards.set_metadata({'title':'CRM 진단 카드 참조편 — v0.2 내용 보존 / v0.4 별책','author':'허재혁','subject':'60개 기존 참조 카드; 모든 카드 실증 검증 아님'})
cards.save(OUT/'diagnostic_cards_reference_v04.pdf');cards.close();src.close()
reports={};coverage={};selected=[]
for stem in ['ebook_review_v04','workbook_v04','diagnostic_cards_reference_v04']:
    path=OUT/(stem+'.pdf');d=pymupdf.open(path)
    if stem!='diagnostic_cards_reference_v04':
        d.set_metadata({'title':'그래서, 이 캠페인 계속할까요?' if stem=='ebook_review_v04' else 'Winner 워크북','author':'허재혁','subject':'v0.4 저자 검토본; 합성 사례; 판매 승인 전','keywords':'CRM,A/B,TRI-V,Winner,JH Motors'})
        d.saveIncr()
    texts=[p.get_text() for p in d];flat='\n'.join(texts)
    assert '허재혁' in flat,stem
    outside=[];footer_overlaps=[]
    for index,pg in enumerate(d):
        for w in pg.get_text('words'):
            if w[0]<-.5 or w[1]<-.5 or w[2]>pg.rect.width+.5 or w[3]>pg.rect.height+.5:outside.append({'page':index+1,'text':w[4],'bbox':w[:4]})
            if stem!='diagnostic_cards_reference_v04' and w[1]<790 and w[3]>pg.rect.height-53:footer_overlaps.append((index+1,w[4],w[3]))
    assert not outside,outside[:10]
    assert not footer_overlaps,footer_overlaps[:10]
    embedded=[]
    font_rows={f[0]:f for p in d for f in p.get_fonts(full=True) if f[0]}
    for xref,fontrow in sorted(font_rows.items()):
        name,ext,typ,content=d.extract_font(xref)
        if fontrow[2]=='Type3':
            kind,procs=d.xref_get_key(xref,'CharProcs')
            glyph_refs=[int(x) for x in re.findall(r'(\d+)\s+0\s+R',procs)]
            if kind=='xref':
                procs=d.xref_object(glyph_refs[0]);glyph_refs=[int(x) for x in re.findall(r'(\d+)\s+0\s+R',procs)]
            assert glyph_refs and all(d.xref_is_stream(n) for n in glyph_refs),xref
            embedded.append({'name':'Type3 glyph programs','extension':'PDF CharProcs','embedded_bytes':sum(len(d.xref_stream(n)) for n in glyph_refs),'note':'Inherited card PDF outline glyphs, not an extractable font file'})
        else:embedded.append({'name':name,'extension':ext,'embedded_bytes':len(content)})
    assert all(x['embedded_bytes']>0 for x in embedded),embedded
    bad_links=[];links=0
    for i,p in enumerate(d):
        for link in p.get_links():
            links+=1
            if link['kind']==pymupdf.LINK_GOTO and not 0<=link.get('page',-1)<len(d):bad_links.append(i+1)
    assert not bad_links,bad_links
    sparse=[i+1 for i,t in enumerate(texts) if len(t)<180]
    if stem=='ebook_review_v04':
        for i in range(1,7):
            # Locate the actual case heading, not merely the contents or a running mention.
            pattern=rf'^사례\s*{i}\s*[·.\-:：]'
            pages=[item[2] for item in d.get_toc() if re.search(pattern,item[1])]
            assert len(pages)==1,f'Missing or duplicate case {i} bookmark'
            assert re.search(pattern,texts[pages[0]-1],re.M),f'Case {i} bookmark target mismatch'
            coverage[f'case{i}']=pages
            selected.append(pages[0]-1)
        assert len(d.get_toc())>=35
        for term in ['최소 사업 효과','가드레일','0.00274','0.1750','Welch','상호작용','용량','Winner']:
            assert term in flat,term
        assert 'CRM-060' not in flat,'Main book should not silently append all cards'
        for start in range(0,len(d),12):
            sheet=Image.new('RGB',(1200,4*450),'#e1e5e3');draw=ImageDraw.Draw(sheet)
            for k,idx in enumerate(range(start,min(start+12,len(d)))):
                pix=d[idx].get_pixmap(matrix=pymupdf.Matrix(.55,.55),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((380,414));x=k%3*400+10;y=k//3*450+26;sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {idx+1}',fill='black')
            sheet.save(REVIEW/f'contact_{start+1:03d}.png')
        for index in sorted(set([0]+selected)):
            d[index].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(REVIEW/f'page_{index+1:03d}.png')
        (OUT/'ebook_review_v04_extracted.txt').write_text(flat,encoding='utf-8')
    if stem=='diagnostic_cards_reference_v04':
        ids=set(re.findall(r'CRM-\d{3}',flat));assert len(ids)==60
    reports[stem]={'pages':len(d),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'author':d.metadata['author'],'toc_entries':len(d.get_toc()),'links':links,'broken_internal_links':bad_links,'outside_page_words':outside,'footer_overlaps':footer_overlaps,'fonts':embedded,'page_text_lengths':[len(t) for t in texts],'sparse_pages_under180_chars':sparse}
    d.close()
validation={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9),'Asia/Seoul')).isoformat(),'version':'0.4 author review','outputs':reports,'six_worked_case_page_locations':coverage,'browser':{'engine':'installed Chrome via Playwright','version':chrome_version,'errors':errors,'checks':browser_checks},'request_coverage':{'1_winner_layers':'chapter6 actual PDF text','2_primary_vs_business_threshold':'chapter7 and case2 actual PDF text','3_guardrails':'chapter7 case2 chapter9 actual PDF text','4_six_complete_cases':'chapter8 all six present, data and calculations linked'},'contrast':{'tool':'mira_contrast_matrix','checked_pairs':8,'normal_AA_passed':8,'minimum_ratio':5.85,'scope':'Text palette on white and paper; not full accessibility audit'},'limits':['Human statistical/OEM/editorial/reader testing pending','Font/citation/distribution rights not cleared','No real-company outcome claim','Some sparse chapter tails may remain; inspect contact sheets','Inherited card reference content not all empirically verified']}
(OUT/'validation_v04.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'outputs':{k:{'pages':v['pages'],'bytes':v['bytes'],'toc_entries':v['toc_entries'],'sparse_pages':v['sparse_pages_under180_chars']} for k,v in reports.items()},'case_pages':coverage,'errors':errors,'review_directory':str(REVIEW)},ensure_ascii=False,indent=2))
