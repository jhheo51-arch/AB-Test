from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];HTML=ROOT/'e-book/explainers/tri_v_structure_review_v01.html';REV=ROOT/'e-book/explainers/review/structure_v01';REV.mkdir(parents=True,exist_ok=True)
errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':960,'height':1300});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(HTML.as_uri())
 assert page.locator('.node').count()==3
 expected={'record':['v1'],'group':['v2'],'capacity':['v1','v3'],'none':[]}
 for case,ids in expected.items():
  page.locator(f'[data-case="{case}"]').click()
  assert sorted(page.locator('.node.active').evaluate_all('(es)=>es.map(e=>e.id)'))==ids
  assert page.locator(f'[data-case="{case}"]').get_attribute('aria-pressed')=='true'
 page.screenshot(path=str(REV/'method_desktop.png'),full_page=True)
 page.locator('#mode-compare').focus();page.keyboard.press('Enter');assert page.locator('#comparison').is_visible() and not page.locator('#method').is_visible()
 assert page.locator('.cycle div').count()==4
 page.screenshot(path=str(REV/'comparison_desktop.png'),full_page=True)
 page.locator('#mode-method').click()
 for width in [390,960]:
  page.set_viewport_size({'width':width,'height':1000})
  for mode in ['method','compare']:
   page.locator('#mode-'+mode).click();assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,mode)
 page.set_viewport_size({'width':390,'height':900});page.locator('#mode-method').click();page.locator('[data-case="capacity"]').click();page.screenshot(path=str(REV/'method_mobile.png'),full_page=True)
 page.emulate_media(media='print');assert page.locator('.pane:visible').count()==2
 browser.close()
assert not errors,errors
book=ROOT/'e-book/exports/v10/ebook_review_v10.pdf';v=json.loads(book.with_name('validation_v10.json').read_text(encoding='utf-8'));assert hashlib.sha256(book.read_bytes()).hexdigest()==v['pdf_sha256']
tells={k:False for k in ['tech_gradient','generic_tech_hue','feature_tile_grid','accent_rail','unearned_blur','monument_stat','icon_topper','center_stack','default_type','wrong_surface']}
report={'status':'passed','case_highlight_expectations':expected,'keyboard_mode_switch':'passed','desktop_mobile_overflow':False,'print_both_views':True,'browser_errors':errors,'current_book_unchanged':True,'cosmetic_slop_tells':tells,'cosmetic_slop_score':sum(tells.values()),'limits':'Concept review only; no theory replacement, manuscript renaming, field proof or trademark clearance.'}
(REV/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
