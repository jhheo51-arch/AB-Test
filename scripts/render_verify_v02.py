"""Exercise visual cards, render and inspect v0.2 PDF."""
import json
from pathlib import Path
import pymupdf
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/exports/v02'
REVIEW=ROOT/'e-book/design/v02/review'
REVIEW.mkdir(parents=True,exist_ok=True)
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1200})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((OUT/'diagnostic_atlas_v02.html').as_uri())
    assert page.locator('[data-id]').count()==60
    for i in range(1,61):
        id=f'CRM-{i:03d}'
        page.locator(f'[data-id="{id}"]').click()
        assert id in page.locator('#selected').inner_text()
        assert '확인해야 할 증거' in page.locator('#selected').inner_text()
        assert '피할 답변' in page.locator('#selected').inner_text()
    page.locator('#q').fill('시승')
    match=page.locator('[data-id]').count(); assert match>0
    page.locator('#q').fill('__no_results__')
    assert page.locator('[data-id]').count()==0
    assert '일치하는 상황이 없습니다' in page.locator('#selected').inner_text()
    page.locator('#reset').click()
    page.locator('#category').select_option('배정·대상')
    assert page.locator('[data-id]').count()==5
    page.locator('#next').click();assert 'CRM-002' in page.locator('#selected').inner_text()
    page.locator('#prev').click();assert 'CRM-001' in page.locator('#selected').inner_text()
    page.locator('#reset').click()
    page.locator('[data-id="CRM-017"]').focus();page.keyboard.press('Enter')
    assert '클릭 상승' in page.locator('#selected h2').inner_text()
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path=str(REVIEW/'atlas_desktop.png'),full_page=False)
    page.locator('[data-view="proof"]').click()
    assert page.locator('#view-proof').is_visible()
    assert '0.1750' in page.locator('#view-proof').inner_text()
    page.screenshot(path=str(REVIEW/'proof_desktop.png'),full_page=False)
    page.locator('[data-view="flow"]').click();assert page.locator('#view-flow svg').is_visible()
    page.locator('[data-view="cards"]').click()
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path=str(REVIEW/'atlas_mobile.png'),full_page=True)
    page.goto((OUT/'ebook_review_v02.html').as_uri())
    page.evaluate('document.fonts.ready')
    assert page.locator('.print-case').count()==60
    assert '{{' not in page.locator('body').inner_text()
    assert page.locator('.proof-print svg').count()==1
    page.emulate_media(media='print')
    # Browser reports any horizontal overflow of a single diagnostic card.
    assert page.evaluate('[...document.querySelectorAll(".print-case")].every(e=>e.scrollWidth<=e.clientWidth+1)')
    page.pdf(path=str(OUT/'ebook_review_v02.pdf'),print_background=True,prefer_css_page_size=True,display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:9px;width:100%;padding:0 16mm;color:#526168;display:flex;justify-content:space-between"><span>허재혁 · CRM A/B 테스트 진단 플레이북 · 저자 검토본 v0.2</span><span class="pageNumber"></span></div>',outline=True,tagged=True)
    browser.close()
assert not errors,errors
pdfpath=OUT/'ebook_review_v02.pdf'
doc=pymupdf.open(pdfpath)
doc.set_metadata({'title':'그래서, 이 캠페인 계속할까요? — CRM A/B 테스트 진단 플레이북','author':'허재혁','subject':'저자 검토본 v0.2; 합성 실습·지표 검증·60개 진단 카드','keywords':'CRM,A/B Test,TRI-V,JH Motors'})
# Save metadata incrementally without reflowing the browser output.
doc.saveIncr()
texts=[p.get_text() for p in doc]
alltext='\n'.join(texts)
for term in ['허재혁','정치외교학','CRM-001','CRM-060','0.1750','현대자동차','기아']:
    assert term in alltext,term
outside=[]
case_pages={}
for i,page in enumerate(doc):
    for word in page.get_text('words'):
        if word[0]<-.5 or word[1]<-.5 or word[2]>page.rect.width+.5 or word[3]>page.rect.height+.5:
            outside.append({'page':i+1,'text':word[4],'bbox':word[:4]})
    for n in range(1,61):
        key=f'CRM-{n:03d}'
        if key in texts[i]:case_pages.setdefault(key,[]).append(i+1)
assert not outside,outside
# The cover/contents may mention endpoints, so use each card's last occurrence.
actual_case_pages=[case_pages[f'CRM-{n:03d}'][-1] for n in range(1,61)]
assert len(set(actual_case_pages))==60,'Each printed card should occupy its own page'
for i in range(0,len(doc),12):
    sheet=Image.new('RGB',(1000,4*390),'#e1e5e3');draw=ImageDraw.Draw(sheet)
    for j,index in enumerate(range(i,min(i+12,len(doc)))):
        pix=doc[index].get_pixmap(matrix=pymupdf.Matrix(.4,.4),alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((310,355))
        x=(j%3)*333+12;y=(j//3)*390+24
        sheet.paste(im,(x,y));draw.text((x,y-16),f'Page {index+1}',fill='black')
    sheet.save(REVIEW/f'pdf_contact_{i+1:03d}.png')
# Full-size representative pages for legibility inspection.
selected=[0,actual_case_pages[16]-1]
proof_page=next(i for i,t in enumerate(texts) if '양측 p' in t)
selected.append(proof_page)
for i in selected:
    doc[i].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False).save(REVIEW/f'pdf_page_{i+1:03d}.png')
report={'pdf_pages':len(doc),'pdf_bytes':pdfpath.stat().st_size,'text_lengths':[len(t) for t in texts],'case_count':len(actual_case_pages),'each_case_on_distinct_page':True,'case_page_map':{f'CRM-{n+1:03d}':p for n,p in enumerate(actual_case_pages)},'toc_entries':len(doc.get_toc()),'outside_page_words':outside,'metadata_author':doc.metadata.get('author'),'visual_app':{'all_60_card_selections':'passed','matching_search_cases':match,'empty_search':'passed','category_filter':'passed','next_previous':'passed','keyboard_activation':'passed','tabs':'passed','desktop_mobile_overflow':False,'javascript_errors':errors},'unverified':['Human author story approval','Human statistical and OEM domain review','Complete scientific validation for each diagnostic card','Commercial rights and distribution requirements','Real target-reader tests'],'generation':'Local Playwright Chromium; no Quarto installed.'}
(OUT/'validation_v02.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdf_pages':report['pdf_pages'],'pdf_bytes':report['pdf_bytes'],'case_count':60,'first_card_page':actual_case_pages[0],'last_card_page':actual_case_pages[-1],'toc_entries':report['toc_entries'],'outside_page_words':len(outside),'javascript_errors':errors,'proof_page':proof_page+1,'pdf':str(pdfpath)},ensure_ascii=False,indent=2))
