"""R08 synthetic actual-Chrome audit. Keyboard path, CSS zoom, bounds/recovery.
Native file picker is NOT exercised: set_input_files is browser automation.
"""
from pathlib import Path
import argparse,base64,json,os,shutil,tempfile,time,traceback
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'r08-evidence';E.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);a.add_argument('--baseline',action='store_true');args=a.parse_args()
checks=[];timings={};blocked=[];errors=[];p=None
RAW='arm,success,total\nA,10,100\nB,20,100'
def check(n,v,detail=None):
 checks.append({'name':n,'pass':bool(v),'detail':detail});print('PASS' if v else 'FAIL',n,flush=True)
 if not v and not args.baseline:raise AssertionError(n)
def poll(fn,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  v=fn()
  if v:return v
  p.wait_for_timeout(25)
 raise AssertionError('bounded poll timeout; '+p.locator('#prepare-state').inner_text())
def tab(selector):
 for _ in range(180):
  if p.locator(selector).evaluate('e=>e===document.activeElement'):return
  p.keyboard.press('Tab')
 raise AssertionError('keyboard unreachable '+selector+' active='+p.evaluate('document.activeElement.outerHTML'))
def key(selector,key='Enter'):tab(selector);p.keyboard.press(key)
def upload(text):
 p.set_input_files('#csv-file',{'name':'SYNTHETIC_R08.csv','mimeType':'text/csv','buffer':text.encode()});expect(p.locator('#data-text')).to_have_value(text);expect(p.locator('#prepare')).to_be_enabled()
def prepare():
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible(timeout=30000)
def analyze():
 p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible(timeout=30000)
def snap():return p.evaluate('JSON.stringify({state,conditions:readConditions(),meta:experimentMeta(),raw:$("#data-text").value,design,rawMeta:[...rawMeta],forms:[...document.querySelectorAll("input,textarea,select")].filter(e=>e.type!=="file").map(e=>[e.id,e.value,e.checked,e.disabled]),print:$("#print-area").innerHTML})')
def save(name):
 with p.expect_download() as d:p.click('#save-project')
 d.value.save_as(str(E/name));return json.loads((E/name).read_text('utf-8'))
result={'status':'FAIL','checks':checks,'timings':timings,'blocked_requests':blocked,'page_errors':errors,'human_observations':0,'actual_model_calls':0,'untested':['actual NVDA/Narrator/audio screenreader use','real human study','native OS file dialog','actual weak physical device','other operating systems','real system without Python'], 'scope':'synthetic automated actual Chrome; actual browser zoom 200% through disposable-profile settings plus separate CSS zoom stress (not deviceScaleFactor-only); AX tree inspection not assistive-technology use; actual read/hash/Worker with controlled completion gates'}
try:
 with sync_playwright() as w:
  b=w.chromium.launch(channel='chrome');result['browser_version']=b.version
  p=b.new_page(viewport={'width':1440,'height':1100},accept_downloads=True);p.set_default_timeout(12000)
  def guard(route):
   if route.request.method!='GET' or not route.request.url.startswith(args.url+'/'):blocked.append({'url':route.request.url,'method':route.request.method});route.abort()
   else:route.continue_()
  p.route('**/*',guard);p.on('pageerror',lambda e:errors.append(str(e)));p.goto(args.url,wait_until='networkidle')
  # A meaningful input -> confirmation -> actual analysis -> judgment path uses keys only.
  key('#data-text','Space');p.keyboard.press('Control+A');p.keyboard.insert_text(RAW);key('#prepare')
  expect(p.locator('#analysis-options')).to_be_visible();check('keyboard only paste and prepare',p.evaluate('state.prepared.sourceRowCount===2'))
  for id in ['randomized','independent','mature','fixed-stop']:
   tab('#'+id);p.keyboard.press('Home');p.keyboard.press('ArrowDown');p.keyboard.press('Tab')
  key('#confirm-input','Space');key('#analyze');expect(p.locator('#results-view')).to_be_visible();check('keyboard arrows Space Enter analyze actual engine',p.evaluate('state.result.inference_allowed&&state.result.overall.B.success===20'))
  key('nav [data-view=share]');tab('#decision');p.keyboard.insert_text('합성 키보드 검토');key('#share-confirm','Space');check('keyboard judgment and sharing confirmation',p.locator('#decision').input_value()=='합성 키보드 검토' and p.locator('#share-confirm').is_checked())
  key('nav [data-view=input]');project=save('KEYBOARD_PROJECT.json')
  # Raw imported note preservation, not merely normalized DOM values.
  project['conditions']['mature']['evidence']='RAW_R08\r\n둘째\r셋째';p.set_input_files('#project-file',{'name':'RAW.json','mimeType':'application/json','buffer':json.dumps(project).encode()});expect(p.locator('#toast')).to_contain_text('복원했습니다');prepare();analyze();p.click('nav [data-view=input]')
  p.locator('summary').filter(has_text='열 연결 템플릿').click();p.check('#profile-consent');before=snap();key('#demo-help');expect(p.locator('#demo-dialog')).to_be_visible()
  p.locator('#demo-video').evaluate('e=>e.play()');poll(lambda:p.locator('#demo-video').evaluate('e=>!e.paused&&e.currentTime>0'))
  p.keyboard.press('Escape');expect(p.locator('#demo-dialog')).not_to_be_visible();check('keyboard Escape pauses video immediately and exact RAW/form/template consent state',p.locator('#demo-video').evaluate('e=>e.paused') and snap()==before)
  check('modal focus restored to named help trigger',p.locator('#demo-help').evaluate('e=>e===document.activeElement'))
  c=p.context.new_cdp_session(p);ax=c.send('Accessibility.getFullAXTree');(E/'ACCESSIBILITY_TREE.json').write_text(json.dumps(ax,ensure_ascii=False,indent=2),encoding='utf-8')
  for id in ['data-text','format','randomized','mature-evidence','profile-consent']:
   check('accessible label '+id,p.locator('#'+id).evaluate('e=>Boolean(e.labels?.length||e.getAttribute("aria-label")||e.getAttribute("aria-labelledby"))'))
  (E/'CORE_STATE.html').write_text(p.content(),encoding='utf-8')
  for width,zoom in [(1440,2),(390,1),(320,1),(390,2),(320,2)]:
   p.set_viewport_size({'width':width,'height':1000});p.locator('html').evaluate('(e,z)=>e.style.zoom=z',zoom)
   layout=p.evaluate('({inner:innerWidth,scroll:document.documentElement.scrollWidth,zoom:getComputedStyle(document.documentElement).zoom,body:document.body.getBoundingClientRect().width})')
   p.screenshot(path=str(E/('layout_'+str(width)+'_'+str(zoom)+'.png')),full_page=True)
   result.setdefault('layout_observations',[]).append({'width':width,'zoom':zoom,**layout});
   if width==1440 or zoom==1:check('CSS layout zoom '+str(zoom)+' width '+str(width)+' no page horizontal overflow',layout['scroll']<=width,layout)
  p.locator('html').evaluate('e=>e.style.zoom=1');p.set_viewport_size({'width':1440,'height':1100})
  # Actual browser zoom through Chrome settings in a disposable profile, not DPR emulation.
  zd=tempfile.mkdtemp(prefix='r08_browser_zoom_',dir=os.environ['TMPDIR']);zc=None
  try:
   zc=w.chromium.launch_persistent_context(zd,channel='chrome',headless=True,no_viewport=True,args=['--window-size=1440,1100','--force-device-scale-factor=1'])
   zp=zc.pages[0];zp.set_default_timeout(12000);zp.goto('chrome://settings/appearance')
   zp.evaluate('()=>new Promise(r=>chrome.settingsPrivate.setDefaultZoom(2,r))');factor=zp.evaluate('()=>new Promise(r=>chrome.settingsPrivate.getDefaultZoom(r))')
   zp.route('**/*',guard);zp.goto(args.url,wait_until='networkidle');geometry=zp.evaluate('({innerWidth,outerWidth,dpr:devicePixelRatio,cssZoom:getComputedStyle(document.documentElement).zoom,scroll:document.documentElement.scrollWidth})');result['actual_browser_zoom']={'factor':factor,**geometry}
   check('actual Chrome 200% zoom not deviceScaleFactor or CSS zoom',factor==2 and geometry['cssZoom']=='1' and geometry['dpr']==2 and geometry['innerWidth']<geometry['outerWidth']*.55,geometry)
   check('actual Chrome 200% responsive layout no page overflow',geometry['scroll']<=geometry['innerWidth'])
   zp.click('#example-aggregate');zp.click('#prepare');expect(zp.locator('#analysis-options')).to_be_visible();zp.check('#confirm-input');zp.click('#analyze');expect(zp.locator('#results-view')).to_be_visible();check('actual browser 200% core preparation and engine results usable',zp.evaluate('state.result.overall.A.total===1000&&state.result.overall.B.total===1000'))
   capture=zc.new_cdp_session(zp).send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False});(E/'browser_zoom_200.png').write_bytes(base64.b64decode(capture['data']));(E/'BROWSER_ZOOM_200.html').write_text(zp.content(),encoding='utf-8')
  finally:
   if zc:zc.close()
   shutil.rmtree(zd)
  # Instrument real stage times. Neither worker replies nor hash values are fabricated.
  p.evaluate('''()=>{window.stage=[];window.realRead=File.prototype.arrayBuffer;File.prototype.arrayBuffer=async function(){const t=performance.now();const v=await realRead.call(this);stage.push({type:'read',ms:performance.now()-t,bytes:v.byteLength});return v;};window.realPost=Worker.prototype.postMessage;Worker.prototype.postMessage=function(m){const t=performance.now();this.addEventListener('message',function done(e){if(e.data.id===m.id){stage.push({type:m.type,ms:performance.now()-t});this.removeEventListener('message',done);}});return realPost.call(this,m);};}''')
  lines=['subject_id,arm,outcome']+[f'SYNTHETIC_{i:020d},{"A" if i%2==0 else "B"},{1 if i%10==0 else 0}' for i in range(50000)]
  raw='\n'.join(lines);padding=2*1024*1024-len(raw.encode());assert padding>=0;lines[1]='P'*padding+lines[1];raw='\n'.join(lines);assert len(raw.encode())==2097152
  p.select_option('#format','individual');t=time.perf_counter();upload(raw);timings['read_ui_seconds']=time.perf_counter()-t;t=time.perf_counter();prepare();timings['prepare_ui_seconds']=time.perf_counter()-t
  check('exact 2MiB 50000 rows prepared losslessly',p.evaluate('state.prepared.sourceRowCount===50000&&state.prepared.cells.reduce((n,c)=>n+c.total,0)===50000'))
  check('large source quality gate no dropped IDs rows',p.evaluate('!state.prepared.issues.some(i=>i.severity==="error")'))
  t=time.perf_counter();analyze();timings['analyze_descriptive_ui_seconds']=time.perf_counter()-t;check('large unknown conditions do not infer',not p.evaluate('state.result.inference_allowed'))
  p.click('nav [data-view=input]')
  for id in ['randomized','independent','mature','fixed-stop']:p.select_option('#'+id,'yes')
  t=time.perf_counter();analyze();timings['analyze_confirmed_ui_seconds']=time.perf_counter()-t;timings['real_stage_ms']=p.evaluate('stage');check('large confirmed source passes actual inferential engine',p.evaluate('state.result.inference_allowed&&state.result.overall.A.total===25000&&state.result.overall.B.total===25000'))
  p.click('nav [data-view=input]');good=p.locator('#data-text').input_value();prior=snap()
  p.set_input_files('#csv-file',{'name':'OVER.csv','mimeType':'text/csv','buffer':raw.encode()+b'X'});expect(p.locator('#toast')).to_contain_text('파일 읽기 실패');check('over 2MiB rejected before actual file read compute and retains valid text',p.locator('#data-text').input_value()==good and len(p.evaluate('stage.filter(x=>x.type==="read")'))==1)
  check('oversize invalid CSV import preserves valid result and conditions',snap()==prior)
  prior=snap();post_count=len(p.evaluate('stage.filter(x=>x.type==="prepare"||x.type==="analyze")'));p.set_input_files('#csv-file',{'name':'OVER_ROWS.csv','mimeType':'text/csv','buffer':('subject_id,arm,outcome\n'+'\n'.join(f'X{i},A,0' for i in range(50001))).encode()});expect(p.locator('#toast')).to_contain_text('TOO_MANY_ROWS');check('50001 file rows rejected before Worker with existing valid result intact',snap()==prior and len(p.evaluate('stage.filter(x=>x.type==="prepare"||x.type==="analyze")'))==post_count)
  p.locator('#data-text').evaluate("(e,text)=>{e.value=text;e.dispatchEvent(new Event('input',{bubbles:true}));}",'subject_id,arm,outcome\n'+'\n'.join(f'X{i},A,0' for i in range(50001)));p.click('#prepare');expect(p.locator('#issues')).to_contain_text('TOO_MANY_ROWS');check('50001 pasted rows blocked before analyze',p.locator('#analyze').is_disabled() and p.evaluate('state.result===null'))
  # Recovery from malformed CSV and invalid project/template is followed by real save/download.
  p.select_option('#format','aggregate');p.fill('#data-text','arm,success,total\nA,"unterminated');p.click('#prepare');expect(p.locator('#issues')).not_to_be_empty();check('malformed CSV gives actionable state without analysis',p.locator('#analyze').is_disabled())
  upload(RAW);prepare();analyze();p.click('nav [data-view=input]');before=snap()
  for selector,text,message in [('#project-file','{}','복원 실패'),('#profile-file','{}','가져오기 실패')]:
   p.set_input_files(selector,{'name':'INVALID.json','mimeType':'application/json','buffer':text.encode()});expect(p.locator('#toast') if selector=='#project-file' else p.locator('#profile-status')).to_contain_text(message);check('invalid import retains valid existing state '+selector,snap()==before)
  prior=snap();p.set_input_files('#csv-file',{'name':'MALFORMED.csv','mimeType':'text/csv','buffer':b'arm,success,total\nA,"unterminated'});expect(p.locator('#toast')).to_contain_text('파일 읽기 실패');check('malformed CSV syntax file preserves exact valid input and result',snap()==prior)
  prior=snap();p.set_input_files('#csv-file',{'name':'INVALID_UTF8.csv','mimeType':'text/csv','buffer':b'\xc3\x28'});expect(p.locator('#toast')).to_contain_text('파일 읽기 실패');check('malformed UTF8 CSV preserves exact valid data result and RAW conditions',snap()==prior)
  save('RECOVERED_PROJECT.json');check('after errors valid new input analyze and actual project download',p.evaluate('state.prepared!==null&&state.result!==null'))
  # Actual file bytes gated at completion; cancellation followed by a new read tests old finally.
  p.evaluate('''()=>{window.readGates=[];File.prototype.arrayBuffer=async function(){const v=await realRead.call(this);return await new Promise(r=>readGates.push(()=>r(v)));};}''')
  p.set_input_files('#csv-file',{'name':'OLD.csv','mimeType':'text/csv','buffer':b'old'});poll(lambda:p.evaluate('readGates.length===1'))
  p.fill('#data-text',RAW);p.set_input_files('#csv-file',{'name':'NEW.csv','mimeType':'text/csv','buffer':RAW.encode()});poll(lambda:p.evaluate('readGates.length===2'));p.evaluate('()=>{readGates[0]();}');p.wait_for_timeout(80)
  check('old file finally cannot unlock new file read',p.evaluate('inputTask?.kind==="file"&&$("#prepare").disabled'))
  p.evaluate('()=>{readGates[1]();File.prototype.arrayBuffer=realRead;}');expect(p.locator('#prepare')).to_be_enabled();check('new owner file applied exact after old cancelled',p.locator('#data-text').input_value()==RAW)
  p.evaluate('''()=>{window.realDigest=crypto.subtle.digest.bind(crypto.subtle);window.hashGates=[];crypto.subtle.digest=async(...args)=>{const v=await realDigest(...args);return await new Promise(r=>hashGates.push(()=>r(v)));};}''')
  p.click('#prepare');poll(lambda:p.evaluate('hashGates.length===1'));p.fill('#data-text',RAW+'\n');p.click('#prepare');poll(lambda:p.evaluate('hashGates.length===2'));p.evaluate('()=>{hashGates[0]();}');p.wait_for_timeout(80)
  check('old hash finally cannot unlock new prepare hash',p.evaluate('inputTask?.kind==="prepare"&&$("#prepare").disabled'))
  p.evaluate('()=>{hashGates[1]();crypto.subtle.digest=realDigest;}');expect(p.locator('#analysis-options')).to_be_visible()
  # Real Worker calculation dispatched; JS synchronous cancellation before any reply can apply.
  p.check('#confirm-input');p.evaluate('''text=>{analyze();window.cancelledWorker=worker;window.workerWasBusy=state.busy;$("#data-text").value=text;$("#data-text").dispatchEvent(new Event('input',{bubbles:true}));}''','arm,success,total\nA,3,10\nB,4,10')
  check('cancel dispatched real Worker calculation discards old ownership',p.evaluate('workerWasBusy&&worker===null&&!state.busy&&state.result===null&&inputTask===null'))
  prepare();analyze();check('after Worker cancellation new Worker computes current input',p.evaluate('state.result.overall.A.success===3&&state.result.overall.B.success===4'))
  p.click('nav [data-view=share]');p.check('#share-confirm')
  with p.expect_download() as d:p.click('#export-report')
  d.value.save_as(str(E/'RECOVERED_REPORT.html'));check('after cancel valid report download', (E/'RECOVERED_REPORT.html').stat().st_size>0)
  check('no JS errors model calls external requests',not errors and not blocked);b.close()
 result['status']='PASS' if all(x['pass'] for x in checks) else 'FAIL'
except Exception as e:
 result['error']=str(e);result['traceback']=traceback.format_exc()
 if p:
  try:p.screenshot(path=str(E/'FAILURE.png'),full_page=True);(E/'FAILURE.html').write_text(p.content(),encoding='utf-8')
  except Exception:pass
finally:
 result['count']=len(checks);(E/('BROWSER_BASELINE.json' if args.baseline else 'BROWSER_VERIFICATION.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'count':len(checks),'error':result.get('error'),'timings':timings},ensure_ascii=False),flush=True)
raise SystemExit(0 if result['status']=='PASS' else 1)
