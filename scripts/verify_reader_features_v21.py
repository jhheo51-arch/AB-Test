"""Exercise offline zoom, return position, clipboard and real file downloads."""
from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];fixture='--fixture' in sys.argv
O=Path('C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch/v21_ui_fixture') if fixture else R/'e-book/exports/v21'
V=R/'e-book/design/v21';V.mkdir(parents=True,exist_ok=True);errors=[];rows=[];network=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);ctx=b.new_context(accept_downloads=True,permissions=['clipboard-read','clipboard-write']);q=ctx.new_page();q.on('pageerror',lambda e:errors.append(str(e)));q.on('request',lambda r:network.append(r.url) if r.url.startswith(('http:','https:')) else None)
 for width in [1200,390]:
  q.set_viewport_size({'width':width,'height':844});q.goto((O/'ebook_review_v21.html').as_uri());q.evaluate('document.fonts.ready');assert q.locator('.figure-zoom-button').count()==13
  for i in range(13):
   button=q.locator('.figure-zoom-button').nth(i);button.scroll_into_view_if_needed();before=q.evaluate('scrollY');button.click();q.wait_for_selector('dialog[open]');size=q.locator('.figure-zoom-stage svg').evaluate('(s)=>({actual:s.getBoundingClientRect().width,native:s.viewBox.baseVal.width,minText:Math.min(...[...s.querySelectorAll("text")].map(t=>parseFloat(getComputedStyle(t).fontSize)))})');assert abs(size['actual']-size['native'])<1,size
   q.keyboard.press('Tab');assert q.evaluate('document.querySelector("dialog").contains(document.activeElement)')
   if width==390 and q.locator('figure').nth(i).get_attribute('data-figure')=='winner_effect.svg':q.screenshot(path=str(V/'mobile_zoom.png'))
   if i%2:q.keyboard.press('Escape')
   else:q.locator('.figure-zoom-dialog button').click()
   q.wait_for_function('!document.querySelector("dialog").open');q.wait_for_timeout(30);after=q.evaluate('scrollY');assert abs(after-before)<1,(width,i,before,after);assert button.evaluate('(b)=>document.activeElement===b');rows.append({'width':width,'figure':i,'return_error_px':abs(after-before),'size':size})
  assert not q.evaluate('document.documentElement.scrollWidth>innerWidth');assert not q.evaluate('document.body.style.position==="fixed"');assert q.locator('dialog svg').count()==0
 q.goto((O/'MINIMUM_RECORD.html').as_uri());assert q.locator('.field textarea').count()==6
 probe='검사용 기록 <script>실행되지 않음</script>\n보류 이유와 다음 확인';q.locator('#r1').fill(probe);q.locator('.meta input').first.fill('LOCAL-TEST-21')
 q.locator('#record-copy').click();q.wait_for_function('document.querySelector("#record-transfer-status").textContent.length>0');status=q.locator('#record-transfer-status').inner_text()
 if '클립보드에 복사했습니다' in status:copied=q.evaluate('navigator.clipboard.readText()').replace('\r\n','\n');assert probe in copied and 'LOCAL-TEST-21' in copied;copy_result='native clipboard write/read passed'
 else:assert q.locator('#record-copy-fallback').input_value().find(probe)>=0;copy_result='permission-safe manual selection fallback passed'
 with q.expect_download() as info:q.locator('#record-export').click()
 dl=info.value;raw=Path(dl.path()).read_bytes();text=raw.decode('utf-8-sig');assert probe in text and 'LOCAL-TEST-21' in text and 'Asia/Seoul' in text;assert all(q.locator('label[for="r'+str(i)+'"]').inner_text() in text for i in range(1,7));assert raw.startswith(b'\xef\xbb\xbf');assert '실험 실행이나 발송 승인이 아닙니다' in text
 # Exercise the denied-clipboard state without claiming it is a native success.
 q.evaluate('Object.defineProperty(navigator,"clipboard",{value:{writeText:()=>Promise.reject(new Error("test denial"))},configurable:true})');q.locator('#record-copy').click();q.wait_for_selector('#record-copy-fallback');assert probe in q.locator('#record-copy-fallback').input_value();assert '허용하지 않았습니다' in q.locator('#record-transfer-status').inner_text()
 q.set_viewport_size({'width':390,'height':844});assert not q.evaluate('document.documentElement.scrollWidth>innerWidth');q.screenshot(path=str(V/'record_mobile.png'));assert q.evaluate('localStorage.length')==0
 q.reload();assert q.locator('#r1').input_value()=='';b.close()
assert not errors,errors;assert not network,network
report={'status':'passed','fixture_only':fixture,'zoom_cases':rows,'copy':copy_result,'copy_denial_fallback':'passed','download_exact_values_and_six_fields':'passed','download_name':dl.suggested_filename,'utf8_bom':'passed','automatic_storage':False,'remote_requests':network,'browser_errors':errors}
(V/('ui_fixture_validation.json' if fixture else 'ui_validation_v21.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='zoom_cases'},ensure_ascii=False,indent=2));print('Zoom and position cases:',len(rows))
