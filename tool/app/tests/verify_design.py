from condition_controls import set_checked, is_checked
"""R05 real loopback Chrome workflow. Synthetic inputs, no model requests or human observations."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1]; E=R/'design-evidence';E.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--url',required=True);url=a.parse_args().url;checks=[]
def check(name,value):
 assert value,name
 checks.append({'name':name,'pass':True});print('PASS',name,flush=True)
def save(p,name):
 with p.expect_download() as d:p.click('#save-project')
 d.value.save_as(str(E/name));return json.loads((E/name).read_text(encoding='utf-8'))
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 p=b.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);errors=[];posts=[]
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:posts.append({'url':r.url,'body':r.post_data}) if r.method=='POST' else None)
 p.goto(url,wait_until='networkidle');p.click('nav [data-view=design]');p.click('#begin-design')
 answers=['SYNTHETIC_SITUATION: 시승 안내 후 예약이 적음','시승 예약 완료를 늘리기','수신 동의한 안내 대상 / 최근 예약자는 제외','배정 후 예약 완료 여부','수신 거부·불만 증가','혜택과 채널은 같게 / 발송 비용 확인 필요']
 for answer in answers:
  p.fill('#design-answer',answer);p.click('#design-next')
 check('one-question flow retains six answers',p.evaluate('ABDesign.questions.every(k=>design.fields[k].value.length>0)'))
 p.click('[data-candidate=message]')
 check('candidate produces proposals not confirmations',p.locator('#design-policyB').input_value()!='' and p.locator('#status-policyB').input_value()=='proposed')
 check('unknown window and analysis/application segments not invented',all(p.locator('#status-'+k).input_value()=='unknown' for k in ['window','analysisSegments','applicationSegments']))
 p.fill('#design-analysisSegments','배정 전 신규 / 기존 두 비중첩 집단; 보유 여부 확인 필요')
 p.fill('#design-applicationSegments','적격 대상 안에서 비용·보호 조건 확인 후 검토')
 p.fill('#design-window','개인별 배정 후 14일 / 관측 가능성 확인 필요')
 p.select_option('#status-purpose','confirmed');p.select_option('#status-audience','confirmed')
 p.fill('#design-risk','수신 거부와 불만 증가를 확인')
 check('editing revokes dependent confirmations',p.locator('#status-purpose').input_value()=='proposed' and p.locator('#status-audience').input_value()=='proposed')
 p.select_option('#status-purpose','confirmed')
 check('plan confirmation never certifies analysis assumptions',p.evaluate("!plan().randomized&&!plan().independent&&!plan().mature&&!plan().fixedStop"))
 x=save(p,'PLAN_ONLY.json')
 check('download is schema7 with no cells/result/fake counts',x['version']==7 and x['cells']==[] and x['engine_version'] is None and 'result' not in x and x['source_digest'] is None)
 check('three segment roles and explicit status survive save',x['design']['fields']['audience']['value']==answers[2] and x['design']['fields']['analysisSegments']['value'] and x['design']['fields']['applicationSegments']['value'] and x['design']['fields']['purpose']['status']=='confirmed')
 p.screenshot(path=str(E/'plan-desktop.png'),full_page=True)
 p.set_viewport_size({'width':390,'height':844});check('mobile design has no horizontal overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'));p.screenshot(path=str(E/'plan-mobile.png'),full_page=True);p.set_viewport_size({'width':1440,'height':1000})
 p.close();p=b.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:posts.append({'url':r.url,'body':r.post_data}) if r.method=='POST' else None)
 p.goto(url,wait_until='networkidle');p.set_input_files('#project-file',str(E/'PLAN_ONLY.json'));expect(p.locator('#design-view')).to_be_visible();expect(p.locator('#design-purpose')).to_have_value(answers[1])
 y=save(p,'PLAN_RESTORED.json')
 check('plan-only restore and reexport preserve design exactly',y['design']==x['design'] and y['cells']==[] and y['lineage']==x['lineage'])
 p.click('#design-to-input');expect(p.locator('#purpose')).to_have_value(answers[1]);expect(p.locator('#audience')).to_have_value(answers[2])
 check('transition preserves context without fabricating data',p.locator('#data-text').input_value()=='' and p.locator('#policy-b').input_value()==x['plan']['policyB'])
 raw='arm,success,total,segment\nA,10,100,new\nB,20,100,new\nA,15,100,existing\nB,18,100,existing'
 p.set_input_files('#csv-file',{'name':'SYNTHETIC_FOLLOWUP.csv','mimeType':'text/csv','buffer':raw.encode()});expect(p.locator('#source-badge')).to_contain_text('사용자 CSV')
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible()
 check('CSV retains design and requires separate observation checks',p.locator('#purpose').input_value()==answers[1] and not is_checked(p.locator('#randomized')) and not is_checked(p.locator('#segment-prespecified')))
 for k in ['randomized','independent','mature','fixed-stop','segment-prespecified','confirm-input']:set_checked(p, '#' + k)
 p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
 check('real engine analysis linked to same experiment',p.evaluate('state.result.overall.A.total===200&&state.result.overall.B.success===38&&design.resultSeen') and answers[1] in p.locator('#experiment-context').text_content())
 check('new free text excluded from LLM facts',all(token not in p.evaluate('JSON.stringify(explanationFacts())') for token in ['SYNTHETIC_SITUATION',answers[1],answers[2]]))
 z=save(p,'PLAN_WITH_AGGREGATES.json');check('resultSeen and real aggregate counts persist',z['design']['resultSeen'] and len(z['cells'])==4 and z['lineage']['current']['digest'])
 p.click('nav [data-view=share]');set_checked(p, '#share-confirm')
 with p.expect_download() as d:p.click('#export-report')
 d.value.save_as(str(E/'RESULT_REPORT.html'));html=(E/'RESULT_REPORT.html').read_text(encoding='utf-8')
 check('HTML preserves context but not private design situation',answers[1] in html and 'SYNTHETIC_SITUATION' not in html)
 p.emulate_media(media='print');p.pdf(path=str(E/'RESULT_REPORT.pdf'),format='A4',print_background=True);p.emulate_media(media='screen')
 p.click('nav [data-view=design]');p.fill('#design-purpose','결과 열람 후 수정한 목적')
 check('post-result plan edit invalidates result/share/print',p.evaluate('state.result===null&&design.changedAfterResult') and not is_checked(p.locator('#share-confirm')) and p.locator('#print-area').inner_text()=='')
 p.emulate_media(media='print');p.pdf(path=str(E/'INVALIDATED_REPORT.pdf'),format='A4');p.emulate_media(media='screen')
 changed=save(p,'POST_RESULT_EDIT.json');check('post-result provenance not backdated',changed['design']['resultSeen'] and changed['design']['changedAfterResult'])
 p.goto(url,wait_until='networkidle');p.set_input_files('#project-file',str(E/'PLAN_WITH_AGGREGATES.json'));expect(p.locator('#data-text')).to_have_value(raw)
 p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible();set_checked(p, '#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible()
 check('aggregate restore reanalysis preserves actual counts and typed lineage',p.evaluate("state.result.overall.B.success===38&&state.lineage.current.kind==='restored_aggregate_csv_utf8'&&design.resultSeen"))
 # Invalid file must preserve current data and design.
 bad=json.loads(json.dumps(z));bad['design']['fields']['purpose']['status']='approved'
 p.set_input_files('#project-file',{'name':'bad.json','mimeType':'application/json','buffer':json.dumps(bad).encode()});expect(p.locator('#toast')).to_contain_text('복원 실패')
 check('invalid design restore leaves current result untouched',p.evaluate('state.result.overall.B.success===38'))
 check('no external model/free-text POST calls',posts==[])
 check('no page JavaScript errors',errors==[])
 b.close()
(E/'BROWSER_VERIFICATION.json').write_text(json.dumps({'status':'PASS','count':len(checks),'checks':checks,'posts':posts,'page_errors':errors,'scope':'synthetic real Chrome via loopback; no human observations; no live LLM'},ensure_ascii=False,indent=2),encoding='utf-8')
print('RESULT',len(checks),'R05 checks passed')
