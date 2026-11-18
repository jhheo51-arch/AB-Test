"""Balanced A/B counterexamples and a printable minimum record, not field validation."""
from pathlib import Path
from statistics import NormalDist
import json,math,hashlib
from statsmodels.stats.proportion import confint_proportions_2indep,test_proportions_2indep
from playwright.sync_api import sync_playwright
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'e-book/review/methodology/tri_v_refinement_v03';fixture=json.loads((D/'counterexample_fixture.json').read_text(encoding='utf-8'))
def wilson(x,n,alpha):
 p=x/n;z=NormalDist().inv_cdf(1-alpha/2);den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return c-h,c+h
def evaluate(c):
 if c.get('measurement_ready') is False:
  return {'id':c['id'],'state':'measurement_review','difference_pp':None,'scope_note':'현재 주지표 비교를 지지할 측정 근거가 없으므로 알려진 정답 수치를 대신 사용하지 않음. 다른 독립 근거의 상태는 별도.'}
 alpha=.05/c['family_size'];na,nb=c['n_A'],c['n_B'];a,b=c['completed_A'],c['completed_B'];pa,pb=a/na,b/nb;diff=pb-pa
 lo,hi=confint_proportions_2indep(b,nb,a,na,method='newcomb',compare='diff',alpha=alpha)
 la,ua=wilson(a,na,alpha);lb,ub=wilson(b,nb,alpha);manual=[diff-math.hypot(pb-lb,ua-pa),diff+math.hypot(ub-pb,pa-la)]
 assert max(abs(v-w) for v,w in zip([lo,hi],manual))<1e-12
 ga,gb=c['withdrawn_A'],c['withdrawn_B'];margin=c['guard_margin_pp']/100
 ni=test_proportions_2indep(gb,nb,ga,na,value=margin,method='score',compare='diff',alternative='smaller',correction=True)
 guardci=confint_proportions_2indep(gb,nb,ga,na,method='score',compare='diff',alpha=2*alpha,correction=True)
 guard_ok=bool(ni.pvalue<alpha);assert guard_ok==(guardci[1]<margin)
 performance_ok=lo*100>c['minimum_effect_pp'];supported=c['same_scope'] and c['prespecified_confirmatory']
 if not guard_ok:state='protection_review'
 elif not supported:state='scope_review'
 elif performance_ok:state='execution_candidate'
 elif hi*100<c['minimum_effect_pp']:state='no_rollout_candidate'
 else:state='additional_evidence'
 return {'id':c['id'],'difference_pp':100*diff,'performance_interval_pp':[float(100*lo),float(100*hi)],'interval_coverage_pct':100*(1-alpha),'family_size':c['family_size'],'alpha_per_population':alpha,'guard_difference_pp':100*(gb/nb-ga/na),'guard_one_sided_upper_pp':float(100*guardci[1]),'guard_limit_pp':c['guard_margin_pp'],'guard_NI_p':float(ni.pvalue),'guard_pass':guard_ok,'minimum_effect_pp':c['minimum_effect_pp'],'state':state,'actual_approval':'not_performed','what_can_stop':c['stop'],'scope_note':'가상 계약과 독립, 비간섭 및 측정 가정 아래 실행 후보를 판단. 효과 균일성, 전체 모집단, 장기 효과나 실제 승인을 보장하지 않음'}
results=[]
for c in fixture['cases']:
 r=evaluate(c);assert r['state']==c['expected'],r
 if 'other_prespecified_group' in c:
  other={**c,**c['other_prespecified_group'],'id':c['id']+'_other','stop':'기존 고객의 구간은 사업 기준을 확정하지 못한다. 첫 이용 대상의 실행 근거를 여기로 옮기지 않으며, 이 집단의 별도 결정이 필요할 때 후속 정보의 가치와 부담을 검토한다.'};r['other_group']=evaluate(other)
 results.append(r)
assert {r['state'] for r in results}=={'execution_candidate','additional_evidence','protection_review'}
# Same candidate data with confirmation removed must not pass as a confirmed subgroup policy.
reclassified={**fixture['cases'][1],'prespecified_confirmatory':False};assert evaluate(reclassified)['state']=='scope_review'
optional_missing={**fixture['cases'][0],'missing_optional_survey_response':True};assert evaluate(optional_missing)['state']=='execution_candidate'
critical_missing={**fixture['cases'][0],'measurement_ready':False};critical=evaluate(critical_missing);assert critical['state']=='measurement_review' and critical['difference_pp'] is None
manual_checks={'Newcombe_intervals_match_manual_Wilson_combination':True,'score_one_sided_upper_matches_NI_test':True,'exploratory_relabel_does_not_pass':True,'missing_optional_non_decision_survey_does_not_block':True,'missing_primary_measurement_does_not_use_known_fixture_answer':True}
(D/'COUNTEREXAMPLE_RESULTS.json').write_text(json.dumps({'status':fixture['status'],'cases':results,'checks':manual_checks,'field_effectiveness':'not_measured'},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
labels={'execution_candidate':'실행 후보','additional_evidence':'추가 근거 검토','protection_review':'보호 우선 검토','no_rollout_candidate':'미확대 후보','scope_review':'적용 범위 재검토'}
md='# 멈추기만 하는 절차가 아닌지 확인한 반례\n\n구성한 고정 카운트의 계산과 판단 규칙 검사다. 실제 회사 성과, 실제 사전등록, 과거 프로젝트 결과 또는 사람의 효율 비교가 아니다. 표본은 검정력 산출값이 아니다.\n\n'
md+='| 사례 | 완료율 차이 B-A | 성과 구간과 수준 | 보호 단측 상한 / 한계 | 현재 결과 |\n|---|---|---|---|---|\n'
for r in results:
 md+=f'| {r["id"]} | {r["difference_pp"]:+.2f}pp | [{r["performance_interval_pp"][0]:+.2f}, {r["performance_interval_pp"][1]:+.2f}]pp, {r["interval_coverage_pct"]:g}% | {r["guard_one_sided_upper_pp"]:+.3f} / +{r["guard_limit_pp"]:.2f}pp | {labels[r["state"]]} |\n'
for c,r in zip(fixture['cases'],results):
 md+='\n## '+c['id']+' '+c['question']+'\n\n**현재 선택:** '+labels[r['state']]+'。\n\n'.replace('。','.')
 md+='**반드시 확인:** 배정과 측정, 같은 적용 범위, 정한 최소 효과와 보호 한계 및 다중성. 실제 승인은 별도다.\n\n**지금 더 하지 않을 것:** '+c['stop']+'\n\n'
 if r['state']=='additional_evidence':md+='**다음 확인:** 현재 주지표 구간은 사업 기준을 넘는 경우와 못 넘는 경우를 모두 허용한다. 별도 검증이 사업적으로 필요한지와 수집 부담을 검토하고, 필요하면 새 자료를 보기 전에 설계와 정보량 및 종료를 정한다. 무효과나 동등으로 선언하지 않는다.\n\n'
 if r['state']=='protection_review':md+='**다음 확인:** 보호 문제의 원인과 필요한 조치를 우선 검토한다. 보호 비열등성 미통과가 항상 확정 위해라는 뜻은 아니며, 이번 입력의 차이와 구간도 함께 읽는다.\n\n'
 if 'other_group' in r:
  o=r['other_group'];md+=f'**다중성:** 사전 두 집단 적용 주장에 Bonferroni를 적용해 각 alpha는 {r["alpha_per_population"]:g}다. 각 집단에서 성과와 보호를 모두 요구하는 예시다. 다른 집단의 완료율 차이는 {o["difference_pp"]:+.2f}pp, 구간 [{o["performance_interval_pp"][0]:+.2f}, {o["performance_interval_pp"][1]:+.2f}]pp다. 첫 집단의 근거를 다른 집단이나 효과 차이의 확증으로 바꾸지 않는다.\n\n'
md+='\n기존 v0.2의 완료 원장 제한과 비용 범위 사례는 그대로 보존한다. 이번 반례는 전체 골격을 바꾸지 않고 실행 후보, 추가 확인, 보호 우선 검토를 모두 다루도록 한 개발 검사다. 좋은 표준 절차로도 같은 결론을 낼 수 있으며 우월성이나 시간 절감을 입증하지 않는다.\n'
(D/'COUNTEREXAMPLES.md').write_text(md,encoding='utf-8',newline='\n')
# Apply the reduced record to the positive case without claiming a human-use trial.
p=results[0]
worked={
 '실험과 기존 문서':'P01 / counterexample_fixture.json의 common_assumptions와 P01 / COUNTEREXAMPLE_RESULTS.json의 P01. 실제 승인 책임자는 미지정.',
 '지금 결정할 것':'같은 적격 조건과 정책 범위에서 안내 B를 실행 후보로 넘길지 판단한다.',
 'V1 믿고 쓸 근거와 제한':f'교육용 측정 가정 아래 완료 차이 {p["difference_pp"]:+.2f}pp, 95% 구간 [{p["performance_interval_pp"][0]:+.2f}, {p["performance_interval_pp"][1]:+.2f}]pp. 보호 단측 상한 {p["guard_one_sided_upper_pp"]:+.3f}pp는 예시 한계 +0.50pp 아래. 각 출처는 위 JSON 참조. 실제 기업의 결과가 아니다.',
 'V2 적용 대상':'배정과 분석 및 적용 모집단의 적격 조건과 정책이 같다는 가정. 효과 균일성이나 다른 대상과 장기 적용은 주장하지 않는다.',
 'V3 현재 선택':'실행 후보. 예시 성과와 보호 조건은 충족하지만 실제 승인과 발송은 수행하지 않았다. 승인 책임자 지정과 기존 승인 절차는 별도다.',
 '추가 확인 또는 생략':'현재 선택을 위해 목적 없는 세분화와 금전 모형은 추가하지 않는다. 실제 승인, 보호 및 감사 의무는 기존 경로를 따른다. 새로운 데이터 수집을 자동 요구하지 않는다.',
 '다시 검토할 조건':'대상과 접촉 정책, 측정 또는 용량과 간섭 가정이 바뀌거나 새로운 보호 위험이 생기면 근거와 범위를 다시 본다.'}
worked_md='# 최소 기록 적용 예시\n\n작성자가 고정 반례 P01에 적용한 예시다. 사람의 시간 절감 또는 실제 실행을 관찰한 기록이 아니다.\n\n'
for title,text in worked.items():worked_md+='**'+title+'**\n\n'+text+'\n\n'
(D/'MINIMUM_RECORD_WORKED.md').write_text(worked_md.rstrip()+'\n',encoding='utf-8',newline='\n')
rows=[('지금 결정할 것','무엇을 누구에게 적용할지. 기존 대비를 다시 쓰지 말고 참조 가능.'),('V1 믿고 쓸 근거와 제한','주지표와 보호 결과 위치. 사용할 수 없는 근거가 있으면 그 범위.'),('V2 적용 대상','배정, 분석, 적용 대상이 같으면 같다고. 다르면 차이와 근거.'),('V3 현재 선택','실행 후보 / 조건부 후보 / 추가 확인 / 미확대 / 중단. 보호와 실제 승인 상태.'),('추가 확인 또는 생략','필요 시 질문, 조건별 행동, 담당과 기한. 없으면 생략 이유와 예외.'),('다시 검토할 조건','어떤 관측 또는 가정 변화가 생기면 현재 선택을 다시 볼지.')]
css='''*{box-sizing:border-box}body{margin:0;background:#FFFFFF;color:#142D32;font:16px/1.4 "Malgun Gothic",sans-serif}main{max-width:880px;padding:22px}h1{font-size:25px;margin:0 0 8px}.meta{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin:12px 0}.meta input{width:100%;height:44px;font:inherit;color:#142D32;border:1px solid #4F625F;padding:7px}p{margin:8px 0}.field{margin:9px 0}label{display:block;font-weight:700;margin:0 0 4px}small{display:block;color:#4F625F;font-size:16px}textarea{display:block;width:100%;height:60px;resize:vertical;border:1px solid #4F625F;border-radius:0;color:#142D32;background:white;font:inherit;padding:6px}button{min-height:44px;font:inherit;color:#FFFFFF;background:#142D32;border:0;padding:8px 14px;margin:6px 0}button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #142D32;outline-offset:3px}details{margin:10px 0}summary{cursor:pointer}footer{font-size:16px;color:#4F625F;margin-top:10px}input::placeholder{color:#4F625F;opacity:1}@media(max-width:600px){main{padding:16px}.meta{grid-template-columns:1fr}h1{font-size:23px}}@media print{@page{size:A4;margin:12mm}body{font-size:12pt}main{max-width:none;padding:0}h1{font-size:18pt}.meta{grid-template-columns:1fr 1fr;margin:8px 0}.meta input{height:8mm}.field{margin:7px 0;break-inside:avoid}textarea{height:15mm;resize:none}small,footer{font-size:12pt}button,details{display:none}footer{margin-top:7px}}'''
body='<main><h1>TRI-V 실전 기록</h1><p>새 문서를 늘리기보다 기존 계획과 분석을 연결합니다. 상세 기록은 필요한 경우에만 엽니다.</p><div class="meta"><input aria-label="실험 ID" placeholder="실험 ID"><input aria-label="계획 참조" placeholder="기존 계획 링크와 버전"><input aria-label="분석 참조" placeholder="분석 파일과 버전"><input aria-label="책임과 승인" placeholder="작성자 / 승인 책임자와 상태"></div>'
for i,(title,hint) in enumerate(rows,1):body+=f'<div class="field"><label for="r{i}">{title}</label><small>{hint}</small><textarea id="r{i}" aria-label="{title}"></textarea></div>'
body+='<details><summary>상세 기록을 여는 경우</summary><p>측정 결함, 적용 대상과 정책 변화, 결정을 바꾸는 비용과 용량, 필요한 계약이나 보호 및 승인 근거가 없을 때 해당 부분만 추가합니다.</p></details><button type="button" onclick="window.print()">현재 입력 인쇄</button><footer>계획 참조에서 대비, 동의, 배정과 분석 단위, 주지표와 분모, 관측과 종료, 다중성 및 사업과 보호 기준을 확인할 수 없으면 먼저 그 공백을 보완합니다. 실행 후보는 실제 승인이 아닙니다. 안전과 권리 및 감사 의무는 생략하지 않습니다. 입력은 서버로 전송하거나 자동 저장하지 않습니다.</footer></main>'
html=D/'MINIMUM_RECORD.html';html.write_text('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TRI-V 실전 기록 v0.3</title><style>'+css+'</style></head><body>'+body+'</body></html>',encoding='utf-8',newline='\n')
validation={'page_errors':[],'viewports':[],'input_count':0,'authority':'실제 사람의 사용성, 시간 절감과 오류 감소는 미측정'}
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True);page=browser.new_page(viewport={'width':1000,'height':1100});page.on('pageerror',lambda e:validation['page_errors'].append(str(e)));page.goto(html.as_uri());page.wait_for_load_state('load')
 assert page.locator('textarea').count()==len(rows);validation['input_count']=page.locator('textarea').count()
 for width in [1000,390]:
  page.set_viewport_size({'width':width,'height':1100});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1');validation['viewports'].append({'width':width,'overflow':False})
 page.locator('#r1').fill('테스트 입력: 실제 사례가 아닌 입력 동작 확인');assert page.locator('#r1').input_value().startswith('테스트 입력');page.locator('#r1').fill('')
 page.locator('summary').focus();page.keyboard.press('Enter');assert page.locator('details').get_attribute('open') is not None;page.keyboard.press('Enter')
 page.set_viewport_size({'width':1000,'height':1100});page.screenshot(path=str(D/'minimum_record_desktop.png'),full_page=True);page.pdf(path=str(D/'MINIMUM_RECORD.pdf'),prefer_css_page_size=True,print_background=True)
 assert not validation['page_errors'];browser.close()
with fitz.open(D/'MINIMUM_RECORD.pdf') as pdf:
 validation['pdf_pages']=len(pdf);assert len(pdf)==1
 spans=[s for pg in pdf for b in pg.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans'] if s['text'].strip()]
 validation['minimum_text_pt']=min(s['size'] for s in spans);assert validation['minimum_text_pt']>=11.9
 text=''.join(pg.get_text() for pg in pdf);assert all(title in text for title,_ in rows)
 for bad in ['\u00b7','\u2022','\u2027','\u318d','\u22c5','\u30fb']:assert bad not in text
 pdf[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(D/'minimum_record_print.png')
validation['contrast']='Actual body #142D32/#FFFFFF 14.47:1 and muted #4F625F/#FFFFFF 6.47:1, selected button white/#142D32 14.47:1; previously calculated with Mira contrast matrix. Colors and system font are artifact proposals, not sourced company tokens.'
validation['fixture_sha256']=hashlib.sha256((D/'counterexample_fixture.json').read_bytes()).hexdigest();validation['counterexample_count']=len(results);validation['states']=[r['state'] for r in results]
(D/'VALIDATION.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'results':results,'form_validation':validation},ensure_ascii=False,indent=2))
