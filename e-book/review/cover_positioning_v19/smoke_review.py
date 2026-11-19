"""Exercise the new comparison report in a separate read-only browser."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent;rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True)
 q=b.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
 for width in [1440,390]:
  q.set_viewport_size({'width':width,'height':1000});q.goto((D/'POSITIONING_REVIEW.html').as_uri());q.evaluate('document.fonts.ready')
  q.wait_for_function('[...document.images].every(i=>i.complete&&i.naturalWidth>0)')
  v=q.evaluate('''() => ({width:innerWidth,images:document.images.length,titleOptions:document.querySelectorAll('.title-option').length,personaSections:document.querySelectorAll('.evidence').length,evidenceRecords:document.querySelectorAll('.evidence article').length,columns:getComputedStyle(document.querySelector('.title-options')).gridTemplateColumns.split(' ').length,overflow:document.documentElement.scrollWidth>innerWidth})''')
  assert v['images']==6 and v['titleOptions']==4 and v['personaSections']==3 and v['evidenceRecords']==33
  assert v['columns']==(2 if width==1440 else 1) and not v['overflow'],v
  q.locator('details').first.locator('summary').click();assert q.locator('details').first.evaluate('(e)=>e.open')
  q.locator('details').first.locator('summary').click();assert not q.locator('details').first.evaluate('(e)=>e.open')
  rows.append(v)
 assert not errors; b.close()
report={'status':'passed','viewports':rows,'details_open_close':'passed','browser_errors':errors,'scope':'New cover/persona HTML report only; no book PDF or citation/contact-sheet job executed.'}
(D/'REPORT_SMOKE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
