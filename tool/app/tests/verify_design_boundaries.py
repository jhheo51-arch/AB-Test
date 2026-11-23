"""Additional design boundaries through actual Chrome; synthetic only, no model calls."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'design-evidence';E.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);u=a.parse_args().url;checks=[]
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True});print('PASS',n)
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 p=b.new_page(accept_downloads=True);posts=[];p.on('request',lambda r:posts.append(r.url) if r.method=='POST' else None)
 p.goto(u,wait_until='networkidle');p.click('nav [data-view=design]');p.click('#begin-design')
 for s in ['SYNTHETIC situation','purpose']:p.fill('#design-answer',s);p.click('#design-next')
 check('audience guided question enforces 300 chars',p.locator('#design-answer').get_attribute('maxlength')=='300')
 p.fill('#design-answer','대'*300);p.click('#design-next')
 check('300-character audience remains exact in context',p.locator('#audience').input_value()=='대'*300)
 p.select_option('#status-audience','confirmed');before=p.evaluate('JSON.stringify({design,state,meta:experimentMeta(),plan:plan()})')
 for escape in [False,True]:
  p.click('#demo-help');expect(p.locator('#demo-dialog')).to_be_visible()
  if escape:p.keyboard.press('Escape')
  else:p.click('#close-demo')
  expect(p.locator('#demo-dialog')).not_to_be_visible()
  check('design and confirmations unchanged by help '+str(escape),p.evaluate('JSON.stringify({design,state,meta:experimentMeta(),plan:plan()})')==before and p.locator('#demo-video').evaluate('v=>v.paused'))
 # The production save path must reject duplicate-context disagreement without truncation.
 p.evaluate("design.fields.audience.value+='x'");p.click('#save-project');expect(p.locator('#toast')).to_contain_text('저장 실패')
 check('save guard rejects overlong audience',p.evaluate('design.fields.audience.value.length===301'))
 p.evaluate("design.fields.audience.value='대'.repeat(300);design.fields.purpose.value='conflict'");p.click('#save-project');expect(p.locator('#toast')).to_contain_text('일치하지 않습니다')
 check('save guard rejects conflicting duplicate context',p.locator('#purpose').input_value()=='purpose')
 p.evaluate("design.fields.purpose.value='purpose'");p.click('#design-to-input')
 p.once('dialog',lambda d:d.dismiss());p.click('#example-aggregate')
 check('cancel synthetic switch preserves original plan',p.evaluate('design!==null') and p.locator('#purpose').input_value()=='purpose')
 p.once('dialog',lambda d:d.accept());p.click('#example-aggregate')
 check('accepted synthetic switch explicitly clears unrelated design',p.evaluate('design===null') and '합성' in p.locator('#source-badge').inner_text())
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
 with p.expect_download() as d:p.click('#save-project')
 seed=json.loads(Path(d.value.path()).read_text(encoding='utf-8'))
 for version in [2,3,4,5]:
  x=json.loads(json.dumps(seed));x['version']=version;x.pop('design',None)
  if version<5:x.pop('lineage',None)
  if version<4:x.pop('judgment',None)
  if version==2:x['plan'].pop('audience',None)
  p.goto(u,wait_until='networkidle');p.set_input_files('#project-file',{'name':'legacy.json','mimeType':'application/json','buffer':json.dumps(x).encode()});expect(p.locator('#data-text')).not_to_have_value('')
  p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible();p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
  with p.expect_download() as d:p.click('#save-project')
  migrated=json.loads(Path(d.value.path()).read_text(encoding='utf-8'))
  check('legacy schema '+str(version)+' restores, analyzes and migrates without fabricated design',migrated['version']==6 and migrated['design'] is None and len(migrated['cells'])==4 and p.evaluate('state.result.overall.B.success===150'))
 check('no model or other POST attempted',posts==[]);b.close()
(E/'BOUNDARY_VERIFICATION.json').write_text(json.dumps({'status':'PASS','count':len(checks),'checks':checks,'human_observations':0,'actual_model_calls':0},ensure_ascii=False,indent=2),encoding='utf-8')
