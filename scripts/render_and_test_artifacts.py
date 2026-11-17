"""Render PDF and smoke-test local HTML using Playwright Chromium."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/exports'
REVIEW=ROOT/'e-book/design/review_v01'
REVIEW.mkdir(parents=True,exist_ok=True)
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1400,'height':1050})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((OUT/'workflow_explorer_v01.html').as_uri())
    assert page.locator('.node').count()==9
    assert page.locator('.case').count()==60
    for key,term in [('jh','합성'),('hyundai','현대자동차'),('kia','기아')]:
        page.locator(f'[data-company="{key}"]').click()
        assert term in page.locator('#context').inner_text()
    for i in range(9):
        page.locator(f'[data-step="{i}"]').focus()
        page.keyboard.press('Enter')
        assert f'G{i}' in page.locator('#detail').inner_text()
    page.locator('#search').fill('시승')
    search_count=page.locator('.case').count()
    assert search_count>0
    page.locator('#search').fill('__no_match__')
    assert page.locator('.case').count()==0
    page.locator('#reset').click()
    page.locator('#dimension').select_option('경제·비용')
    assert page.locator('.case').count()==5
    page.locator('#reset').click()
    page.locator('.case summary').first.click()
    assert page.locator('.case').first.get_attribute('open') is not None
    page.locator('.case summary').first.click()
    page.locator('[data-company="jh"]').click()
    page.locator('[data-step="0"]').click()
    desktop_overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not desktop_overflow
    page.screenshot(path=str(REVIEW/'workflow_desktop.png'),full_page=False)
    page.set_viewport_size({'width':390,'height':844})
    mobile_overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not mobile_overflow
    page.goto((OUT/'reading_draft_v01.html').as_uri())
    page.evaluate('document.fonts.ready')
    assert page.locator('.case-print').count()==60
    assert '{{BASELINE_TABLE}}' not in page.locator('body').inner_text()
    page.pdf(path=str(OUT/'reading_draft_v01.pdf'),print_background=True,prefer_css_page_size=True,display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:9px;width:100%;text-align:center;color:#526168">허재혁 · 시작 원고 v0.1 · <span class="pageNumber"></span></div>')
    browser.close()
assert not errors,errors
report={'stage_count':9,'case_count':60,'company_contexts_tested':3,'keyboard_stage_selection':'passed','search_matching_cases':search_count,'empty_search':'passed','dimension_filter_expected_5':'passed','case_expansion':'passed','desktop_overflow':desktop_overflow,'mobile_overflow':mobile_overflow,'javascript_errors':errors,'pdf_rendered':True,'limits':'Interaction smoke tests and document export, not validated causal recommendation engine or accessibility audit.'}
(OUT/'interaction_validation_v01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
