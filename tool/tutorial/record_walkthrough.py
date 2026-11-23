"""Real Chrome interaction recorder. Run with Python; --quick checks the flow without video.
All inputs synthetic. No LLM, external request, audio, publishing or repository writes.
"""
import os, sys, time, json, shutil, hashlib, threading, http.server, functools, subprocess
from pathlib import Path
from tutorial_paths import ROOT, WORK, RUNTIME, args
SCRATCH=WORK
from playwright.sync_api import sync_playwright, expect
QUICK=args.quick
OUT=WORK/('quick' if QUICK else 'evidence'); OUT.mkdir(exist_ok=True)
INPUT=ROOT/'SYNTHETIC_CRM_CUSTOM.csv'
assert INPUT.is_file(), 'Missing fixed synthetic input'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
source={p.relative_to(RUNTIME).as_posix():sha(p) for p in list(RUNTIME.iterdir())+list((RUNTIME/'fonts').glob('*'))+list((RUNTIME/'examples').glob('*')) if p.is_file() and p.suffix in ('.js','.html','.css','.json','.py','.woff2','.txt','.csv')}
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self):
  if self.path=='/api/status':
   body=b'{"cli_available":false}'; self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(body)
  else: super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(RUNTIME)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}'
stats={'requests':[],'blocked':[],'page_errors':[],'checks':{},'source_sha256':source,'input_sha256':sha(INPUT)}
cues=[]; start=None
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=True)
  context=browser.new_context(viewport={'width':1280,'height':800},device_scale_factor=1,accept_downloads=True,**({} if QUICK else {'record_video_dir':str(OUT/'raw'),'record_video_size':{'width':1280,'height':800}}))
  def route(r):
   req=r.request; stats['requests'].append({'method':req.method,'url':req.url})
   if req.method!='GET' or not req.url.startswith(url+'/'):
    stats['blocked'].append({'method':req.method,'url':req.url}); r.abort()
   else: r.continue_()
  context.route('**/*',route)
  page=context.new_page(); start=time.monotonic(); video=page.video
  page.on('pageerror',lambda e:stats['page_errors'].append(str(e)))
  def cue(text,seconds=5):
   now=round(time.monotonic()-start,3)
   if cues: cues[-1]['end']=now
   cues.append({'start':now,'end':None,'text':text})
   page.wait_for_timeout(120 if QUICK else seconds*1000)
  def focus(sel):
   page.locator(sel).evaluate("el=>el.scrollIntoView({block:'center',behavior:'instant'})"); page.wait_for_timeout(100 if QUICK else 450)
  def check(name,condition):
   stats['checks'][name]=bool(condition)
   if not condition: raise AssertionError(name)
  def download(sel,name):
   with page.expect_download() as d: page.locator(sel).click()
   path=OUT/name; d.value.save_as(path); check(name+' downloaded',path.exists() and path.stat().st_size>0); return path
  page.goto(url); expect(page.locator('#engine-status')).not_to_contain_text('확인 중',timeout=30000)
  cue('상황부터 설계하고, 같은 계획으로 결과를 확인합니다.\n이 영상은 무음이며 모든 입력은 고정된 합성 자료입니다.',5)
  page.locator('nav [data-view="design"]').click(); page.locator('#begin-design').click()
  answers=['합성 CRM 실습: 시승 안내 문구를 바꿀지 검토합니다.','시승 완료 비율과 신규·기존 고객의 차이를 이해하기','합성 신규·기존 고객. 동의 및 사전 적격 조건을 충족한 배정 고객','배정 후 28일 안에 시승 완료 여부','수신 거부 증가와 불필요한 접촉. 이 CSV에는 보호 지표 없음','동일 채널·혜택, 안내 1회. 실제 발송은 하지 않는 기능 시연']
  for i,answer in enumerate(answers):
   page.locator('#design-answer').fill(answer)
   if i in (0,2): cue('CRM 상황과 목적, 대상부터 기록합니다.\n고객 개인정보 없이 합성 맥락만 입력합니다.',3)
   page.locator('#design-next').click()
  focus('[data-candidate="message"]'); cue('로컬의 고정 질문과 비교 후보입니다.\n자유 문장을 이해하는 AI나 승자 예측이 아닙니다.',5)
  page.locator('[data-candidate="message"]').click()
  for key,value in {'window':'합성 가정: 개인별 배정 후 28일','analysisSegments':'배정 전 고객 유형 new / existing. 사전성은 미확인','applicationSegments':'전체 적용은 별도 판단. 고객군별 차이는 탐색','business':'비용·최소 관심 효과 미확인','policyA':'합성 control: 현재 시승 안내 문구','policyB':'합성 treatment: 행동 방법을 분명히 쓴 시승 안내'}.items():
   page.locator('#design-'+key).fill(value)
  focus('#design-policyA'); cue('구조화된 계획은 직접 수정할 수 있습니다.\nA와 B의 설명을 고치되 결과나 승자는 만들지 않습니다.',5)
  focus('#design-window'); cue('관측 기간과 분석·적용 범위를 남깁니다.\n계획을 작성한 것만으로 실험 조건이 확인되지는 않습니다.',5)
  plan=download('#save-project','PLAN_ONLY.json'); pdata=json.loads(plan.read_text('utf-8'))
  check('plan has no fabricated cells',pdata['cells']==[] and pdata['engine_version'] is None)
  cue('실제 프로젝트 JSON을 다운로드했습니다.\n계획만 저장되어 고객 수·효과·승자가 없습니다.',5)
  page.goto(url); expect(page.locator('#begin-design')).to_be_attached()
  page.locator('#project-file').set_input_files(str(plan)); expect(page.locator('#design-work')).to_be_visible()
  check('fresh page restored full design',page.evaluate('ABDesign.normalize(design)')==pdata['design'])
  cue('새 페이지에서 방금 저장한 JSON을 복원합니다.\n수정한 계획이 그대로 돌아오는지 확인합니다.',5)
  focus('#design-to-input'); page.locator('#design-to-input').click()
  page.locator('#csv-file').set_input_files(str(INPUT)); expect(page.locator('#data-text')).to_have_value(INPUT.read_text('utf-8'))
  focus('#data-text'); cue('같은 계획에 고정 합성 CSV를 업로드합니다.\n예시 버튼으로 계획을 지우지 않고 직접 파일을 읽습니다.',5)
  page.locator('#prepare').click(); expect(page.locator('#mapping-panel')).to_be_visible()
  focus('#mapping-preview'); cue('원본 열과 값을 먼저 봅니다.\nvariant / converted / participants / cohort를 직접 연결합니다.',5)
  for key,value in {'arm':'variant','success':'converted','total':'participants','segment':'cohort'}.items(): page.locator('#map-'+key).select_option(value)
  page.locator('#arm-value-a').fill('control'); page.locator('#arm-value-b').fill('treatment'); focus('#mapping-fields')
  cue('A는 control, B는 treatment로 명시합니다.\n이 연결은 사용자가 확인하는 역할이며 의미 인증이 아닙니다.',6)
  page.locator('#mapping-confirm').check(); page.locator('#apply-mapping').click(); expect(page.locator('#analysis-options')).to_be_visible()
  check('same plan preserved through upload',page.evaluate('design.fields.purpose.value')==pdata['design']['fields']['purpose']['value'])
  focus('#randomized'); cue('다섯 조건의 기본값은 모두 모름입니다.\n모르는 조건을 확인됨으로 바꿔 문제를 해결하지 마세요.',5)
  check('upload conditions unknown',all(page.locator('#'+i).input_value()=='unknown' for i in ['randomized','independent','mature','fixed-stop','segment-prespecified']))
  page.locator('#confirm-input').check(); page.locator('#analyze').click(); expect(page.locator('#results-view')).to_be_visible()
  limited=page.evaluate('JSON.parse(JSON.stringify(state.result))'); write('descriptive_result.json',limited)
  check('unknown core blocks inference',limited['inference_allowed'] is False and limited['overall']['p_raw'] is None)
  cue('모름 상태에서도 관측 차이는 볼 수 있습니다.\np값·추론 판정은 제한되며 기술통계만 읽습니다.',7)
  page.locator('nav [data-view="input"]').click()
  for id,label in [('randomized','무작위 배정'),('independent','고객 단위 독립성'),('mature','개인별 관측 완료'),('fixed-stop','고정 종료')]:
   focus('#'+id); page.locator('#'+id).select_option('yes'); page.locator('#'+id+'-evidence').fill('합성 시연 가정: '+label+'을 충족했다고 놓음. 실제 실행 기록 확인 아님.')
   cue('합성 시연에서만 다음 조건을 가정: '+label+'\n확인됨과 근거 메모는 사용자 진술이지 독립 인증이 아닙니다.',4)
  focus('#segment-prespecified'); cue('집단 사전성은 모름으로 남깁니다.\n핵심 네 조건과 별개이며 집단 결과는 탐색으로 제한됩니다.',6)
  page.locator('#confirm-input').check(); page.locator('#analyze').click(); expect(page.locator('#results-view')).to_be_visible()
  result=page.evaluate('JSON.parse(JSON.stringify(state.result))'); write('inference_result.json',result)
  check('core four allow overall inference',result['inference_allowed'] and result['overall']['p_raw'] is not None)
  check('segment still unknown',page.locator('#segment-prespecified').input_value()=='unknown')
  actual=page.locator('#result-title').inner_text(); delta=page.locator('#result-summary dd').first.inner_text()
  cue('실제 엔진 결과: '+actual+' / 관측 차이 '+delta+'\n사업·보호 조건은 여전히 미확인, 적용 승인과 구분합니다.',8)
  focus('#overall-results'); page.locator('#overall-results .calc-details summary').click(); focus('#overall-results .calc-details')
  cue('계산 근거를 펼쳐 p값과 구간을 확인합니다.\n통계 보류는 무효과·동등·안전의 증명이 아닙니다.',7)
  focus('#segment-results'); cue('집단 사전성이 모르면 고객군 결과는 탐색입니다.\n전체 추론 가능성과 집단별 확증 판단을 혼동하지 않습니다.',7)
  page.locator('nav [data-view="share"]').click(); page.locator('#decision-direction').select_option('defer')
  page.locator('#decision').fill('합성 자료의 관측 차이와 통계 판정을 분리해 검토. 사업·보호 조건이 없어 실제 적용 판단은 유보합니다.')
  page.locator('#decision-checks').fill('최소 관심 효과, 비용, 수신 거부 및 접촉 부담, 집단 기준의 사전성을 추가 확인합니다.')
  page.locator('#revisit').fill('대상·정책·관측 조건이 바뀌면 재검토. 이 합성 시연은 실제 실행·성과의 증거가 아닙니다.')
  focus('#decision'); cue('판단 이유와 남은 확인 조건을 직접 씁니다.\n통계 판정이 실제 적용이나 안전 승인을 대신하지 않습니다.',6)
  finalproject=download('#save-project','PLAN_AND_AGGREGATES.json'); saved=json.loads(finalproject.read_text('utf-8'))
  check('aggregate save has four cells',len(saved['cells'])==4)
  focus('#share-groups'); page.locator('#share-groups').uncheck()
  cue('프로젝트 JSON에는 조건 근거와 자유 서술이 남습니다.\n보고서에서 제외되어도 프로젝트가 익명화된 것은 아닙니다.',7)
  page.locator('#share-confirm').check(); report=download('#export-report','AB_RESULT_REPORT.html')
  reporttext=report.read_text('utf-8'); check('private condition evidence excluded from HTML',saved['conditions']['randomized']['evidence'] not in reporttext)
  cue('집단 상세를 제외한 공개용 HTML을 실제 저장합니다.\n공유 범위를 확인하며, 파일 저장은 서버 공개가 아닙니다.',6)
  # Actual Chromium PDF invokes the production beforeprint handler; no print-dialog simulation.
  page.pdf(path=str(OUT/'AB_RESULT_REPORT.pdf'),print_background=True,format='A4')
  check('actual PDF produced',(OUT/'AB_RESULT_REPORT.pdf').stat().st_size>1000)
  page.locator('nav [data-view="input"]').click(); focus('#randomized-evidence')
  page.locator('#randomized-evidence').fill('합성 가정 수정: 실제 기록이 없어 재확인이 필요합니다.')
  check('condition evidence edit invalidates result',page.evaluate('state.result===null') and not page.locator('#confirm-input').is_checked() and not page.locator('#share-confirm').is_checked())
  cue('조건 근거만 고쳐도 이전 결과와 확인이 해제됩니다.\n변경 뒤에는 집계·조건을 다시 확인하고 재분석합니다.',7)
  focus('#analyze')
  cue('설계 → 저장·복원 → 열 연결 → 조건 → 판단까지.\n합성 기능 시연이며 실제 사용자 시험이나 실험 인증이 아닙니다.',6)
  cues[-1]['end']=round(time.monotonic()-start,3)
  if not QUICK: page.screenshot(path=str(OUT/'final_ui.png'))
  check('no model or external requests',not stats['blocked'] and all(x['method']=='GET' for x in stats['requests']))
  check('no browser exceptions',not stats['page_errors'])
  write('timeline.json',cues); write('browser_evidence.json',stats)
  context.close()
  if video:
   original=Path(video.path()); video.save_as(str(OUT/'actual_app_recording.webm'))
   if original.exists(): original.unlink()
  browser.close()
finally: server.shutdown(); server.server_close()
print(json.dumps({'output':str(OUT),'checks':stats['checks'],'duration':cues[-1]['end'] if cues else None},ensure_ascii=False,indent=2))
