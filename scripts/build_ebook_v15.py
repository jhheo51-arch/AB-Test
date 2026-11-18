"""Develop design choices and worked decisions without changing frozen data."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v15';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v14/ebook_review_v14.md');text=base;changes=[];developments=[]
plan=json.loads(read('e-book/analysis/development_v15/PLANNING_EXAMPLE.json'))['available_plan']
def replace(old,new):
 global text
 assert text.count(old)==1,(old[:90],text.count(old));text=text.replace(old,new);changes.append({'before':old,'after':new,'occurrences':1})
def add(prefix,content,key,reason):
 found=[p.strip() for p in text.split('\n\n') if p.strip().startswith(prefix)];assert len(found)==1,prefix
 replace(found[0],found[0]+'\n\n'+content);developments.append({'id':key,'reason':reason,'text':content})
block='''뒤의 사례5를 설계 단계로 되돌려 보자. 신규 관심 고객과 기존 고객이 메시지를 받기 전부터 구분되고, 평소 반응과 운영 조건도 다를 것으로 예상된다면 이 상태 안에서 A와 B를 배정하는 안을 검토할 수 있다. 기록에는 배정 직전의 상태와 블록 식별자, 각 상태 안의 배정 확률과 실제 배정 수를 남긴다. 발송 뒤 클릭한 사람을 새 블록으로 만드는 것은 이 설계가 아니다. 클릭 자체가 메시지의 영향을 받기 때문이다.

| 설계에서 확인한 조건 | 선택과 남길 근거 |
|---|---|
| 같은 적격 대상에서 독립적인 개인을 비교하며 중요한 사전 차이를 따로 관리할 이유가 크지 않음 | 단순 무작위배정을 기본안으로 두고 배정 확률과 분모를 기록한다. |
| 결과와 관련된 고객 상태를 처치 전에 안정적으로 알 수 있음 | 상태 안 무작위배정을 검토하고 목표 고객 구성과 분석 가중치를 사전에 정한다. |
| 같은 지점의 시승 슬롯을 고객끼리 경쟁함 | 상태별 균형만으로 해결하지 않는다. 배정 단위와 운영 정책을 다시 설계한다. |

사례5의 고정된 신규와 기존 구성은 그 실습의 추정 대상이다. 블록을 쓴 뒤에는 전체 고객을 아무렇게나 합치는 대신 정한 목표 구성에 맞게 효과와 불확실성을 읽어야 한다. 신규가 많은 다음 캠페인으로 옮기면 평균 효과가 달라질 수 있으므로 같은 추정값을 복사하지 않는다. 설계 검토 기록은 “사전 고객 상태 안에서 무작위배정하고 정한 구성으로 전체 효과를 읽는다. 지점 간 자원 간섭이 있으면 개인 비교를 그대로 승인하지 않는다”로 정리할 수 있다. 이는 실제 배정을 완료했다는 보고가 아니라, V1의 비교 근거와 V2의 적용 대상을 정하는 문장이다.'''
add('지점마다 평소의 완료율이나 고객 구성이 크게 다르다면',block,'D1','블록의 장단점 설명을 배정 선택, 필요한 필드와 분석 대상 문장으로 완성')
planning=f'''이번에는 같은 회사의 후속 실험을 새로 계획한다고 가정해 보자. 이는 앞의 A/B/H 실험을 다시 해석하거나 그 표본을 바꾸는 일이 아니다. 미리 확보할 수 있는 적격 고객이 총 20,000명이고, 같은 기간에 A와 B에 10,000명씩 배정할 수 있다는 별도 교육용 조건이다. 독립 개인의 시승 완료를 단일 양측 비교로 보고, 기준율 9%에서 10%로의 1pp 변화, 유의수준 5%와 검정력 80%를 목표로 둔다. 미발송군은 없으므로 발송 자체의 증분 효과에는 답하지 않는다. 관측 창은 배정 후 28일로 놓되 누락, 군집과 중간 분석 보정은 이 계산에 넣지 않았다.

같은 정규 근사 계획법으로 계산하면 현재 수에서 1pp 변화를 발견할 검정력은 약 {plan['power_display_percent']:.1f}%다. 목표 80%에 필요한 수는 군당 {plan['required_n_each']:,}명, 합계 {plan['required_n_total']:,}명이어서 적격 고객 {plan['additional_eligible_customers']:,}명을 더 확보해야 한다. 현재 20,000명에 목표 검정력을 맞추어 역산한 최소 검출 효과는 약 {plan['mde_display_pp']:.2f}pp다. 이 값은 실제 관측 효과나 보장된 발견 경계가 아니다. 정한 근사와 가정 아래 검정력이 목표에 도달하는 계획 효과다. 새로운 계획값은 직접 정규 근사식과 별도 라이브러리 호출을 대조했다.

| 가능한 선택 | 얻는 것과 포기하는 것 |
|---|---|
| 적격 고객을 추가 확보해 목표 수를 채움 | 같은 1pp 질문의 목표 검정력을 유지한다. 모집 가능성과 대기 비용, 관측 성숙 시간을 확인해야 한다. |
| 현재 수에서 더 큰 변화를 노리는 개입을 설계함 | 큰 효과를 학습할 수 있지만 기존의 1pp 질문을 해결한 것은 아니다. 결과를 보기 전에 새로운 개입과 목표를 정한다. |
| 현재 수와 1pp 질문을 유지하고 낮은 검정력을 수용함 | 무작위 비교가 자동으로 무효가 되는 것은 아니다. 계획 효과를 놓칠 위험을 더 감수하며 비유의를 효과 없음으로 보고하지 않는다. |

사업 담당자가 최소 1pp를 중요하게 본다면 MDE를 {plan['mde_display_pp']:.2f}pp로 고쳐 적는 것만으로 간격이 사라지지 않는다. 지금 필요한 확인은 고객을 더 모을 수 있는지와 그 대기가 현재 선택을 바꿀 만큼 가치가 있는지다. “고객이 부족하다”는 보고 대신 “현재 모수에서는 정한 계획 효과의 발견 능력이 목표보다 낮다. 추가 모집 가능성과 비용을 확인한 뒤 목표 검정력을 유지할지, 다른 개입을 학습할지, 낮은 발견 능력을 수용할지 정한다”라고 쓸 수 있다. 어느 선택을 하든 결과를 본 뒤 유리한 효과 크기로 계획을 갈아 끼우지는 않는다.

이 기록은 기존 여섯 칸을 그대로 쓴다. 첫 칸의 결정은 후속 설계의 선택이고, V1에는 계산 가정과 정밀도 한계, V2에는 연락 동의와 미시승 적격 고객의 범위, V3에는 현재 승인 상태를 남긴다. 추가 확인에는 모집 가능성과 대기 비용의 담당 역할을, 재검토 조건에는 확보 가능한 고객 수나 기준율이 바뀌는 경우를 적는다. 위 수는 주지표에 대한 계획일 뿐 철회와 불만의 보호 정보량까지 충족했다는 뜻은 아니다. 실제 모집과 발송 전에 보호 기준과 필요한 수를 별도로 설계하고 승인받아야 한다.'''
add('MDE는 정한 표본과 유의수준, 검정력, 분석 방법 아래',planning,'D2','표본 부담의 직관을 가용 모수, 계산, 세 가지 합법적 설계 선택과 여섯 칸 기록으로 연결')
stopping='''추가 모집으로 목표 수를 확보하는 안이 채택됐다면, 종료 조건도 같은 설계서에서 정한다. 이 후속 설계가 고정 종료 방식이라면 목표 고객의 배정이 끝난 날과 모든 고객의 개인별 28일 창이 성숙한 날을 따로 기록한다. 목표 인원을 채웠다는 이유로 마지막 고객의 미성숙 결과를 미완료로 확정하지 않는다. 모집이 멈췄어도 결과 확인은 계속될 수 있다.

| 실행 중 들어온 정보 | 그때 할 수 있는 행동과 결론 |
|---|---|
| 배정 누락이나 이벤트 수집 장애 | 원장을 조사하고 해당 지표의 해석을 제한한다. 성과 우위로 읽지 않는다. |
| 일반 고정 표본 p값이 중간에 작아짐 | 예정한 최종 판단을 대신하지 않는다. 조기 효능 판단 절차가 없었다면 그 통과선으로 확대를 제안하지 않는다. |
| 중대한 권리 침해나 고객 피해 | 보호 절차에 따라 대응하고 필요하면 운영을 중단한다. 통계적 유의성을 기다리지 않는다. |

중간 효능 판단이 꼭 필요하다는 요구가 실험 전에 나온다면 분석 담당 역할이 조회 규칙과 오류 통제를 갖춘 설계를 제시하고 사업 담당 역할은 그 정보가 어떤 행동을 바꿀지 정한다. 이미 결과를 본 뒤라면 같은 자료의 일반 p값에 새 순차 이름만 붙여 소급 승인하지 않는다. 계획 이탈과 보류한 주장을 기록하고, 기존 결과에서 어디까지 말할 수 있는지 검토한 뒤 아직 보지 않은 자료의 후속 설계를 정한다. 여기에 보편적으로 쓸 수 있는 순차 경계 숫자를 제시하지 않은 이유는 각 설계의 가정과 비교 가족이 다르기 때문이다. 빠른 종료라는 요구가 고객 보호 대응이나 관측 기회의 생략으로 바뀌지 않게 하는 것이 핵심이다.'''
add('계획된 중간 판단의 경계는 여러 번 기회를 얻으면서도',stopping,'D3','순차 경계의 설명을 실제 조회 상황별 행동과 결과 성숙 조건으로 전환')
report='''같은 완료 개선이라도 어떤 문장으로 넘길지는 8장의 보완 예제에서 확인할 수 있다. 조건 가와 라의 완료 결과는 같지만 보호 결과가 다르다. 조건 가에서는 정한 현재 범위의 성과와 보호 근거가 충족돼 실행 후보로 넘기고 실제 승인과 운영 책임을 확인한다. 조건 라에서는 완료 개선을 인정하면서도 보호 평가가 허용 조건을 충족하지 못했으므로 그 근거로 확대를 제안하지 않는다. 이때 비열등성 근거 부족을 곧바로 확정 위해라는 말로 바꾸거나, 성과가 좋다는 이유로 보호 한계를 사후에 느슨하게 고쳐서도 안 된다.

회의에서 “B가 유의하니 확대한다”는 문장이 나왔다면 관측과 통계, 현재 선택을 나누어 고쳐 쓴다. 조건 가의 기록은 “정한 지표와 보호 조건이 현재 범위에서 충족돼 실행 후보로 넘긴다. 승인 전에는 발송하지 않으며 적용 규모와 관찰 및 되돌릴 책임을 확인한다”가 된다. 조건 라에서는 “완료 개선 근거는 있으나 보호 조건의 충족 근거가 부족해 확대를 제안하지 않는다. 보호 담당 역할이 철회와 피해 원장을 확인하고 실제 피해가 있으면 정한 대응을 먼저 실행한다”가 된다. 이 문장들은 예제의 조건을 따른 작성 예시이지 실제 담당자가 승인하거나 조치했다는 보고가 아니다. 추가 분석을 마냥 늘리는 대신 어느 확인이 실행과 보호 선택을 바꾸는지 적는 것이 TRI-V의 끝이다.'''
add('이 오류 기준을 사업의 손실 한도와 혼동하지 않아야 한다.',report,'D4','통계 위험과 사업 피해의 구분을 기존 실행 후보와 보호 검토 반례의 결정문으로 구체화')
replace('python scripts/check_study_concepts_v14.py','uv run --with scipy --with statsmodels python scripts/develop_planning_v15.py')
for a,b in [('build_ebook_v14.py','build_ebook_v15.py'),('prepare_fonts_v14.py','prepare_fonts_v15.py'),('verify_ebook_v14_numbers.py','verify_ebook_v15_numbers.py'),('render_verify_v14.py','render_verify_v15.py'),('verify_v14_integration.py','verify_v15_integration.py')]:replace('scripts/'+a,'scripts/'+b)
replace('이 판에서는 생성기와 이전 정정 코드를 다시 돌리지 않는다. v0.13에서 교정한 DB와 통계 장부를 고정 입력으로 읽고 새로 설명한 확률 예시와 근사 관계만 별도 확인한다. 기존 사례의 카운트와 효과, 보호 계산은 바꾸지 않는다. 본문의 새 연결 설명과 조판을 검증한 것이며 순차 검정 엔진이나 새로운 현장 실험을 만든 것은 아니다.','이 판에서는 생성기와 이전 정정 코드를 다시 돌리지 않는다. v0.13의 교정 DB와 기존 통계 장부는 고정 입력으로 읽는다. 별도 후속 설계의 가용 모수와 검정력 및 MDE 계산을 확인하고 기존 사례의 카운트와 효과, 보호 계산은 바꾸지 않는다. 후속 설계의 계획값과 작성 예시는 실제 모집이나 실험 결과가 아니며 순차 검정 엔진을 구현한 것도 아니다.')
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbidden);assert not re.search(r'^### ',text,re.M)
(OUT/'ebook_review_v15.md').write_text(text,encoding='utf-8',newline='\n')
for p in (ROOT/'e-book/exports/v14').glob('*.svg'):shutil.copyfile(p,OUT/p.name)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','counterexample_fixture.json','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','REGRESSION_CHECK.json','PROVENANCE.json','READ_SCOPE.json','CONCEPT_CHECKS.json']:
 shutil.copyfile(ROOT/'e-book/exports/v14'/name,OUT/name)
shutil.copyfile(ROOT/'e-book/analysis/development_v15/PLANNING_EXAMPLE.json',OUT/'PLANNING_EXAMPLE.json')
shutil.copytree(ROOT/'e-book/exports/v14/assets',OUT/'assets',dirs_exist_ok=True)
s=read('scripts/build_ebook_v11.py');s=s[s.index("s=read('scripts/build_ebook_v07.py')"):s.index("m=json.loads((OUT/")];s=s.replace('v11','v15').replace('0.11','0.15')
s=s.replace("exec(compile(s,__file__,'exec'),globals())", "s=s.replace('.glossary h2{font-size:15pt;margin:5mm 0 3mm}', '.glossary h2{font-size:15pt;margin:3.5mm 0 2mm}')\nexec(compile(s,__file__,'exec'),globals())")
exec(compile(s,__file__,'exec'),globals())
hp=OUT/'ebook_review_v15.html';hp.write_text(hp.read_text(encoding='utf-8').replace('</style>','@media print{pre{break-inside:avoid;page-break-inside:avoid}}\n</style>',1),encoding='utf-8',newline='\n')
m=json.loads((OUT/'build_manifest_v15.json').read_text(encoding='utf-8'));m.update({'previous_v14_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'methodology_name':'TRI-V','fixed_axes':True,'record_fields':6,'new_content':[x['id'] for x in developments],'original_data_and_prior_edition_preserved':True,'new_experiment_conducted':False,'human_approval':False})
(OUT/'build_manifest_v15.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.14','changes':changes,'developments':developments,'human_approved':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'edition':'v0.15','development_groups':len(developments),'source_characters':len(text),'statistics':'Historical results unchanged; separate prospective planning illustration'},ensure_ascii=False))
