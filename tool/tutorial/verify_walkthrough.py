"""Read-only real Chrome playback/state/PDF verification against the staging copy."""
import os,json,threading,http.server,functools,time,hashlib
from pathlib import Path
from tutorial_paths import ROOT, WORK, RUNTIME, HELP
from playwright.sync_api import sync_playwright,expect
import fitz
OUT=WORK/'evidence'
class Handler(http.server.SimpleHTTPRequestHandler):
 def translate_path(self, path):
  if path in ('/help/walkthrough.mp4','/help/walkthrough.ko.srt','/help/walkthrough.timeline.json'):
   return str(HELP/path.rsplit('/',1)[1])
  return super().translate_path(path)
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/api/status':
   self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"cli_available":false}')
  else:super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(RUNTIME)))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
results={'checks':{},'blocked':[],'exceptions':[],'served_port':server.server_port}
def check(k,v):
 results['checks'][k]=bool(v)
 if not v:raise AssertionError(k)
def snapshot(page):return page.evaluate("""()=>({fields:[...document.querySelectorAll('input,textarea,select')].map(e=>({id:e.id,value:e.value,checked:e.checked})),result:state.result,prepared:state.prepared,conditions:readConditions(),design,share:document.querySelector('#share-confirm').checked})""")
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True)
  results['browser_version']=browser.version
  context=browser.new_context(viewport={'width':1280,'height':900})
  def route(r):
   if r.request.method!='GET' or not r.request.url.startswith(url+'/'):
    results['blocked'].append(r.request.url);r.abort()
   else:r.continue_()
  context.route('**/*',route)
  page=context.new_page();page.on('pageerror',lambda e:results['exceptions'].append(str(e)))
  page.goto(url);expect(page.locator('#engine-status')).not_to_contain_text('확인 중',timeout=30000)
  page.locator('#project-file').set_input_files(str(OUT/'PLAN_AND_AGGREGATES.json'))
  expect(page.locator('#purpose')).to_have_value('시승 완료 비율과 신규·기존 고객의 차이를 이해하기')
  page.locator('#prepare').click();expect(page.locator('#analysis-options')).to_be_visible()
  page.locator('#confirm-input').check();page.locator('#analyze').click();expect(page.locator('#results-view')).to_be_visible()
  page.locator('nav [data-view="share"]').click();page.locator('#share-confirm').check()
  page.locator('nav [data-view="results"]').click();page.locator('#llm-consent').check()
  before=snapshot(page)
  for mode in ('close-button','Escape'):
   page.locator('#demo-help').click();expect(page.locator('#demo-dialog')).to_be_visible()
   video=page.locator('#demo-video')
   until=time.monotonic()+20
   while video.evaluate('el=>el.readyState')<2:
    if time.monotonic()>until:raise TimeoutError('video metadata')
    page.wait_for_timeout(100)
   metadata=video.evaluate('el=>({duration:el.duration,width:el.videoWidth,height:el.videoHeight,src:el.currentSrc})')
   results['video_metadata']=metadata
   check(mode+' current video loaded',abs(metadata['duration']-float(json.loads((OUT/'ffprobe.json').read_text('utf-8'))['format']['duration']))<.05 and metadata['width']==1280 and metadata['height']==900)
   video.evaluate('el=>el.play()');page.wait_for_timeout(600)
   check(mode+' actual playback advances',video.evaluate('el=>!el.paused&&el.currentTime>.15'))
   if mode=='close-button':page.locator('#close-demo').click()
   else:page.keyboard.press('Escape')
   check(mode+' synchronously paused',video.evaluate('el=>el.paused'))
   check(mode+' state preserved',snapshot(page)==before)
   expect(page.locator('#demo-dialog')).not_to_be_visible();page.wait_for_timeout(100)
  page.set_viewport_size({'width':390,'height':844});page.locator('#demo-help').click();expect(page.locator('#demo-dialog')).to_be_visible()
  bounds=page.locator('#demo-video').bounding_box();dialog=page.locator('#demo-dialog').bounding_box()
  results['mobile_bounds']={'viewport_width':390,'video':bounds,'dialog':dialog}
  check('mobile video within viewport',bounds['x']>=0 and bounds['x']+bounds['width']<=390)
  mobilevideo=page.locator('#demo-video')
  until=time.monotonic()+20
  while mobilevideo.evaluate('el=>el.readyState')<2:
   if time.monotonic()>until:raise TimeoutError('mobile video metadata')
   page.wait_for_timeout(100)
  mobilevideo.evaluate('el=>el.play()');page.wait_for_timeout(3000)
  check('mobile actual playback advances',mobilevideo.evaluate('el=>!el.paused&&el.currentTime>1'))
  page.screenshot(path=str(OUT/'mobile_help.png'))
  page.locator('#close-demo').click();check('mobile close paused',page.locator('#demo-video').evaluate('el=>el.paused'))
  check('mobile close preserves state',snapshot(page)==before)
  check('no external or POST requests',not results['blocked'])
  check('no browser exceptions',not results['exceptions'])
  context.close();browser.close()
 doc=fitz.open(OUT/'AB_RESULT_REPORT.pdf');pdftext=''.join(p.get_text() for p in doc)
 results['pdf_pages']=len(doc); (OUT/'pdf_text.txt').write_text(pdftext,encoding='utf-8')
 project=json.loads((OUT/'PLAN_AND_AGGREGATES.json').read_text('utf-8'))
 check('private evidence excluded from real PDF',all(c['evidence'] not in pdftext for c in project['conditions'].values() if c['evidence']))
 check('real PDF has judgment', '판단' in pdftext and '합성' in pdftext)
 inference=json.loads((OUT/'inference_result.json').read_text('utf-8'))
 check('all segments exploratory without p values',all(s['exploratory'] and s['p_raw'] is None and s['p_adjusted'] is None for s in inference['segments']))
 check('overall actual hold and positive difference',inference['overall']['winner']=='hold' and inference['overall']['diff']>0)
 # Lock untouched current-app code to the immutable parent-verified copy.
 original=json.loads((OUT/'browser_evidence.json').read_text('utf-8'))['source_sha256']
 manifest={}
 for relname, expected in original.items():
  path=RUNTIME/relname
  rel=path.relative_to(RUNTIME)
  if not path.is_file() or '__pycache__' in str(rel) or rel.parts[0]=='help':continue
  digest=hashlib.sha256(path.read_bytes()).hexdigest();manifest[str(rel).replace('\\','/')]=digest
  check('source unchanged since own capture '+str(rel),digest==expected)
 results['current_app_sha256']=manifest
finally:
 server.shutdown();server.server_close()
 results['server_stopped']=True
 (OUT/'playback_verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(results['checks']),'all_pass':all(results['checks'].values()),'metadata':results.get('video_metadata'),'pdf_pages':results.get('pdf_pages'),'server_stopped':results['server_stopped']},ensure_ascii=False,indent=2))
