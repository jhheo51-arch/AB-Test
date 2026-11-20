"""Loopback-only static UI + explicit minimal-facts Hermes explanation bridge.
No raw CSV endpoint exists. No auth files or secret values are read by this app.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import argparse, json, mimetypes, os, re, shutil, subprocess, threading, time

ROOT=Path(__file__).resolve().parent
STATUSES={'valid','limited','invalid','unsupported'}
DECISIONS={'A','B','hold','not_tested'}
LOCK=threading.Lock()
SYSTEM_PROMPT='''당신은 A/B 테스트 결과를 재계산하지 않는 한국어 설명 도우미입니다. 입력은 로컬 엔진이 만든 판정 상태만이며 원자료나 숫자는 전달되지 않습니다. 통계적 승패와 실제 적용 판단을 분리하세요. overall_decision A/B는 선택한 방법·조건 안의 통계적 우세이며, 보호 미확인이 그 통계 결과 자체를 취소하는 것은 아닙니다. hold는 차이 없음·동등·안전의 증명이 아닙니다. not_tested는 판정을 수행하지 못했다는 뜻입니다. 집단 한쪽만 유의하다는 이유로 집단 효과 차이를 확정하지 마세요. interaction supported가 아닐 때 그 차이를 입증했다고 쓰지 마세요. 원인, 이익, 안전, 외적 타당성이나 승인 여부를 만들어내지 마세요. 통계·배정 조건은 사용자 확인이지 독립 인증이 아닙니다. 숫자·확률을 새로 쓰지 말고 아래 상태의 의미와 한계를 설명하세요. 도구를 사용하지 마세요. 오직 JSON 객체를 반환하세요: {"summary":"짧은 한국어 설명","cautions":["한계 설명"],"next_steps":["다음 확인"],"evidence_refs":["overall","segments","interaction","issues"]}. summary/cautions/next_steps 문장에는 숫자를 쓰지 마세요. evidence_refs는 실제 주어진 항목만 쓰세요. 결과를 변경하거나 새 winner를 선택하지 마세요.'''

def validate_facts(x):
    keys={'analysis_status','overall_decision','segments','interaction','guardrail','design_user_confirmed','adjustment','issues'}
    if not isinstance(x,dict) or set(x)!=keys:raise ValueError('허용된 판정 상태 필드만 전송할 수 있습니다.')
    if x['analysis_status'] not in STATUSES or x['overall_decision'] not in DECISIONS:raise ValueError('판정 상태가 유효하지 않습니다.')
    if x['interaction'] not in {'supported','not_supported','not_tested'} or x['guardrail']!='not_assessed':raise ValueError('지원하지 않는 판정입니다.')
    if type(x['design_user_confirmed']) is not bool or x['adjustment'] not in {'holm','none'}:raise ValueError('설계 상태가 유효하지 않습니다.')
    groups=x['segments']
    if not isinstance(groups,list) or len(groups)>2:raise ValueError('집단 상태는 최대 두 개입니다.')
    for i,g in enumerate(groups):
        if not isinstance(g,dict) or set(g)!={'id','decision'} or g['id']!=f'G{i+1}' or g['decision'] not in DECISIONS:raise ValueError('집단 이름이나 원자료는 보낼 수 없습니다.')
    issues=x['issues']
    if not isinstance(issues,list) or len(issues)>30 or any(not isinstance(v,str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,60}',v) for v in issues):raise ValueError('오류 코드는 식별자 형식이어야 합니다.')
    return x

def extract_response(text):
    text=text.strip()
    for m in re.finditer(r'\{',text):
        try:obj,end=json.JSONDecoder().raw_decode(text[m.start():])
        except json.JSONDecodeError:continue
        if isinstance(obj,dict) and set(obj)=={'summary','cautions','next_steps','evidence_refs'}:
            return obj
    raise ValueError('모델이 요구한 JSON 구조를 반환하지 않았습니다.')

def validate_response(obj,facts):
    if not isinstance(obj.get('summary'),str) or not 1<=len(obj['summary'])<=1200:raise ValueError('설명 길이가 유효하지 않습니다.')
    for key in ['cautions','next_steps']:
        if not isinstance(obj.get(key),list) or not 1<=len(obj[key])<=6 or any(not isinstance(s,str) or not 1<=len(s)<=1200 for s in obj[key]):raise ValueError('설명 항목 형식이 유효하지 않습니다.')
    refs=obj.get('evidence_refs')
    if not isinstance(refs,list) or not refs or any(v not in {'overall','segments','interaction','issues'} for v in refs):raise ValueError('근거 키가 유효하지 않습니다.')
    prose=' '.join([obj['summary'],*obj['cautions'],*obj['next_steps']])
    if re.search(r'\d',prose):raise ValueError('모델이 숫자를 재서술해 설명을 표시하지 않았습니다. 원래 계산 결과를 확인하세요.')
    if re.search(r'<\s*(?:script|iframe|img)|https?://',prose,re.I):raise ValueError('허용하지 않는 링크·마크업 응답입니다.')
    return obj

class AppServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,handler,hermes,profile):
        super().__init__(address,handler)
        self.hermes=hermes;self.profile=profile;self.llm_successes=0;self.llm_failures=0

class Handler(BaseHTTPRequestHandler):
    server_version='ABLocal/0.2'
    def log_message(self,*args):pass
    def expected_host(self):return f'127.0.0.1:{self.server.server_port}'
    def headers_common(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; worker-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
    def respond(self,status,payload):
        data=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(status);self.headers_common();self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def local_host_ok(self):return self.headers.get('Host')==self.expected_host()
    def do_GET(self):
        if not self.local_host_ok():return self.respond(403,{'error':'HOST_REJECTED'})
        route=self.path.split('?',1)[0]
        if route=='/api/status':
            return self.respond(200,{'route':'existing_hermes_profile_cli','profile':self.server.profile,'cli_available':bool(self.server.hermes),'live_successes':self.server.llm_successes,'live_failures':self.server.llm_failures,'credential_state':'not asserted; only an actual request proves connectivity','raw_csv_endpoint':False})
        path='index.html' if route=='/' else route.lstrip('/')
        if path not in {'index.html','styles.css','app.js','engine.js','worker.js','theme-v03.css','narrative.js','project-schema.js','column-mapping.js','workflow-v05.js','workflow-v05.css','decision-v04.css','fonts/PretendardVariable.woff2'} and not re.fullmatch(r'examples/[A-Za-z0-9_.-]+\.csv',path):return self.respond(404,{'error':'NOT_FOUND'})
        target=(ROOT/path).resolve()
        if ROOT not in target.parents or not target.is_file():return self.respond(404,{'error':'NOT_FOUND'})
        data=target.read_bytes();self.send_response(200);self.headers_common();self.send_header('Content-Type',(mimetypes.guess_type(str(target))[0] or 'application/octet-stream')+('; charset=utf-8' if target.suffix in {'.html','.css','.js','.csv'} else ''));self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        if not self.local_host_ok():return self.respond(403,{'error':'HOST_REJECTED'})
        expected='http://'+self.expected_host()
        if self.headers.get('Origin')!=expected:return self.respond(403,{'error':'ORIGIN_REJECTED'})
        if self.path!='/api/explain':return self.respond(404,{'error':'NOT_FOUND'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.respond(415,{'error':'JSON_REQUIRED'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16384:raise ValueError('요청 크기가 허용 범위를 벗어났습니다.')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict) or set(body)!={'confirmed','facts'} or body['confirmed'] is not True:raise ValueError('전송 미리보기 확인이 필요합니다.')
            facts=validate_facts(body['facts'])
        except (ValueError,TypeError,KeyError) as e:return self.respond(400,{'error':'PAYLOAD_REJECTED','message':str(e)})
        if not self.server.hermes:return self.respond(503,{'error':'LLM_UNAVAILABLE','message':'Hermes CLI를 찾지 못했습니다. 계산 결과와 규칙 설명은 계속 사용할 수 있습니다.'})
        if not LOCK.acquire(blocking=False):return self.respond(429,{'error':'LLM_BUSY','message':'설명 요청 하나가 진행 중입니다.'})
        try:
            prompt=SYSTEM_PROMPT+'\n\n사실 상태 JSON:\n'+json.dumps(facts,ensure_ascii=False)
            argv=[self.server.hermes,'--profile',self.server.profile,'chat','--query-file','-','--oneshot','-Q','-t','context_engine','--ignore-rules','--source','tool','--max-turns','1','--run-budget','60','--reasoning','low']
            started=time.monotonic()
            result=subprocess.run(argv,input=prompt,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=85,cwd=str(ROOT))
            if result.returncode:raise RuntimeError('기존 Hermes 프로필의 모델 요청이 실패했습니다. 인증·사용량·연결 상태를 Hermes에서 확인하세요.')
            answer=validate_response(extract_response(result.stdout),facts)
            self.server.llm_successes+=1
            return self.respond(200,{'source':'actual_llm_via_existing_hermes_profile','profile':self.server.profile,'answer':answer,'elapsed_seconds':round(time.monotonic()-started,2),'validation':'JSON schema, allowed evidence keys, no numeric restatement; not a proof of semantic correctness','sent_fields':list(facts),'raw_data_sent':False})
        except subprocess.TimeoutExpired:
            self.server.llm_failures+=1;return self.respond(504,{'error':'LLM_TIMEOUT','message':'실제 설명 요청 시간이 초과됐습니다. 계산 결과는 유지됩니다.'})
        except (ValueError,RuntimeError,OSError) as e:
            self.server.llm_failures+=1;return self.respond(502,{'error':'LLM_RESPONSE_REJECTED','message':str(e)})
        finally:LOCK.release()
    def do_OPTIONS(self):self.respond(403,{'error':'CROSS_ORIGIN_NOT_ALLOWED'})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=0);parser.add_argument('--hermes-exe',default=os.environ.get('AB_HERMES_EXE') or shutil.which('hermes'));parser.add_argument('--profile',default='mira');args=parser.parse_args()
    server=AppServer(('127.0.0.1',args.port),Handler,args.hermes_exe,args.profile)
    print(f'AB_LOCAL_URL=http://127.0.0.1:{server.server_port}',flush=True)
    print('Raw CSV stays in the browser. LLM is called only after explicit minimal-facts confirmation.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
