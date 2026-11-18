from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'e-book/explainers/tri_v_eli5.html';REV=ROOT/'e-book/explainers/review';REV.mkdir(parents=True,exist_ok=True)
errors=[];states=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':760,'height':1200});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(P.as_uri())
 assert page.locator('[role=tabpanel]').count()==3
 for n in range(3):
  page.locator(f'#tab-{n}').click()
  assert page.locator(f'#scene-{n}').is_visible()
  assert page.locator('[role=tabpanel]:not([hidden])').count()==1
  assert page.locator(f'#tab-{n}').get_attribute('aria-selected')=='true'
  assert page.locator('#position').inner_text()==f'{n+1} / 3'
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  page.screenshot(path=str(REV/f'tri_v_eli5_step_{n+1}.png'),full_page=True)
  states.append(page.locator(f'#scene-{n} h2').inner_text())
 assert page.locator('#next').is_disabled()
 page.locator('#tab-2').focus();page.keyboard.press('Home');assert page.locator('#scene-0').is_visible();assert page.locator('#prev').is_disabled()
 page.locator('#next').click();assert page.locator('#scene-1').is_visible();page.locator('#prev').click();assert page.locator('#scene-0').is_visible()
 page.set_viewport_size({'width':390,'height':844})
 for n in range(3):
  page.locator(f'#tab-{n}').click();assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.screenshot(path=str(REV/'tri_v_eli5_mobile.png'),full_page=True)
 page.emulate_media(media='print');assert page.locator('[role=tabpanel]:visible').count()==3
 browser.close()
assert not errors,errors
report={'status':'passed','scenes':states,'tab_navigation':'passed','keyboard_and_previous_next':'passed','desktop_and_mobile_overflow':False,'print_shows_all_scenes':True,'browser_errors':errors,'main_book_renamed':False,'scope':'ELI5 illustration, not statistical or field evidence','design_rationale':['Use one fictional test-drive story to avoid switching contexts.','Show one large picture and one question at a time to reduce terminology load.','Keep the method, operating guide and optional brand distinct without inventing another theoretical layer.']}
(REV/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
