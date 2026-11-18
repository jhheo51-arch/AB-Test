"""Integrate only the supplied reading-guide gaps into the complete book."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v14';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v13/ebook_review_v13.md');text=base;changes=[]
def replace(old,new,count=1):
 global text
 assert text.count(old)==count,(old[:80],text.count(old));text=text.replace(old,new);changes.append({'before':old,'after':new,'occurrences':count})
proposals=json.loads(read('e-book/review/study_integration_v14/PASTE_V13_INSERTION_PROPOSALS.json'))['proposals']
concepts=json.loads(read('e-book/analysis/study_integration_v14/CONCEPT_CHECKS.json'))
grouped={};adopted=[]
for p in proposals:
 paragraph=p['insert_after']
 if p['id']=='P2':
  paragraph='지점마다 평소의 완료율이나 고객 구성이 크게 다르다면 배정 단계에서 그 정보를 쓸지 검토한다. 단순 무작위배정은 운영하기 쉽지만 모든 상황에서 가장 정밀한 방법은 아니다. 처치 전에 알 수 있고 결과와 관련이 큰 고객 상태나 지점 안에서 무작위로 나누는 블록 설계는 비교의 정밀도를 높이는 데 도움이 될 수 있다. 다만 집단을 지나치게 잘게 만들면 배정과 분석의 부담이 커진다. 실제로 관리할 수 있는 사전 정보인지, 분석이 배정 구조를 반영하는지 보고 선택한다. 블록 안에서 고객을 무작위로 나누더라도 모든 특성이 정확히 같아지는 것은 아니다. 같은 지점의 시승차를 서로 빼앗는 간섭도 블록이라는 이름으로 해결되지 않는다. 이때에는 배정 단위와 비교 정책부터 다시 검토한다.[3]'
 if p['id']=='P1':paragraph+='[7]'
 if p['id']=='P3':
  example=concepts['independent_true_null_tests']
  paragraph=f"작은 오류 확률은 정해진 횟수마다 반드시 도착하는 할당량이 아니다. 귀무가설이 모두 참이고 실제 제1종 오류율이 1%인 독립 검정 100회를 가정하면, 잘못 기각하는 횟수의 기댓값은 한 번이지만 한 번 이상 잘못 기각할 확률은 약 {example['display_percent']:.1f}%다. 오류가 없을 수도 있고 여러 번 나올 수도 있다. 이는 조건을 고정한 확률 예시이지 실제 CRM 실험들의 오류율을 측정한 결과가 아니다. 각 실험의 오류 기준이 작다는 말과 여러 결과를 묶어 정책을 고를 때의 오류 가능성이 작다는 말도 다르다. 어떤 비교와 종료 규칙을 함께 관리할지 먼저 정해야 한다."
 if p['id']=='P4':
  paragraph='작은 차이를 구분하는 데 필요한 정보의 증가 형태도 살펴보자. 기준율과 변동성, 유의수준과 검정력 및 배정 구조를 같게 둔 작은 효과의 근사에서는 필요한 표본이 목표 효과 제곱의 역수에 대략 비례한다. 이 근사에서는 목표 차이를 절반으로 줄이면 표본은 약 네 배가 된다. 정확한 고객 수를 대신하는 공식은 아니다. 희귀 사건이나 군집, 중간 판단과 관측 누락이 있으면 해당 구조에 맞게 다시 계산해야 한다. 감당할 수 없는 표본 수가 나왔다면 사업적으로 중요한 차이와 이번 설계가 읽을 수 있는 차이의 간격을 드러낸다. 모집에 걸리는 시간과 마지막 고객의 결과를 기다리는 시간도 따로 적는다.'
 if p['id']=='P5':paragraph+=' 순차 방법을 쓴다고 언제나 더 빨리 끝나거나 적은 정보로 같은 결론을 얻는 것도 아니다. 정해진 조회 때의 경계를 쓰는 설계와 계속 확인할 수 있도록 만든 추론의 조건을 구분하고, 보통의 고정 표본 p값을 이름만 바꾸어 사용하지 않는다.[8]'
 grouped.setdefault(p['anchor_exact'],[]).append(paragraph)
 adopted.append({'id':p['id'],'concept_ids':p['concept_ids'],'chapter':p['chapter'],'text':paragraph})
for anchor,paragraphs in grouped.items():replace(anchor,anchor+'\n\n'+'\n\n'.join(paragraphs))
replace('uv run --with numpy --with scipy --with statsmodels python scripts/correct_statistics_v13.py','python scripts/check_study_concepts_v14.py')
for a,b in [('build_ebook_v13.py','build_ebook_v14.py'),('prepare_fonts_v13.py','prepare_fonts_v14.py'),('verify_ebook_v13_numbers.py','verify_ebook_v14_numbers.py'),('render_verify_v13.py','render_verify_v14.py'),('verify_v13_integration.py','verify_v14_integration.py')]:replace('scripts/'+a,'scripts/'+b)
replace('원래 생성기를 다시 돌리지는 않는다. 먼저 정정 코드가 원자료의 읽기 전용 입력으로 교정 장부와 파생 DB를 만들고, 숫자 검사는 기존의 불변 결과와 이번 정정 값을 함께 대조한다. 반례는 같은 고정 카운트에서 보호 계산만 교정한다.','이 판에서는 생성기와 이전 정정 코드를 다시 돌리지 않는다. v0.13에서 교정한 DB와 통계 장부를 고정 입력으로 읽고 새로 설명한 확률 예시와 근사 관계만 별도 확인한다. 기존 사례의 카운트와 효과, 보호 계산은 바꾸지 않는다. 본문의 새 연결 설명과 조판을 검증한 것이며 순차 검정 엔진이나 새로운 현장 실험을 만든 것은 아니다.')
reference='[7] American Statistical Association. 2016년 p값 성명 발표 자료. 공개 발표문 전체 3쪽에 실린 여섯 원칙을 읽고 p값의 해석과 사업 판단의 경계를 대조했다. 성명 논문 전체를 열람했다는 뜻은 아니다.\n\nhttps://www.amstat.org/asa/files/pdfs/P-ValueStatement.pdf\n\n[8] Ramesh Johari, Leo Pekelis, David Walsh. Always Valid Inference: Continuous Monitoring of A/B Tests. arXiv:1512.04922v3, 2019. 공개 사전 논문의 물리 1~4쪽에서 연속 모니터링 문제와 항상 유효한 추론의 도입 설명을 참고했다. 전체 증명과 구현을 재검증한 것은 아니다.\n\nhttps://arxiv.org/abs/1512.04922\n\n'
replace('Ron Kohavi, Diane Tang, Ya Xu.',reference+'Ron Kohavi, Diane Tang, Ya Xu.')
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbidden);assert not re.search(r'^### ',text,re.M)
(OUT/'ebook_review_v14.md').write_text(text,encoding='utf-8',newline='\n')
for p in (ROOT/'e-book/exports/v13').glob('*.svg'):shutil.copyfile(p,OUT/p.name)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','counterexample_fixture.json','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','REGRESSION_CHECK.json','PROVENANCE.json']:shutil.copyfile(ROOT/'e-book/exports/v13'/name,OUT/name)
shutil.copytree(ROOT/'e-book/exports/v13/assets',OUT/'assets',dirs_exist_ok=True)
for source,name in [('e-book/manuscript/study_integration_v14/READ_SCOPE.json','READ_SCOPE.json'),('e-book/analysis/study_integration_v14/CONCEPT_CHECKS.json','CONCEPT_CHECKS.json'),('e-book/review/study_integration_v14/PASTE_V13_CONCEPT_MAP.json','BEFORE_COVERAGE.json')]:shutil.copyfile(ROOT/source,OUT/name)
s=read('scripts/build_ebook_v11.py');s=s[s.index("s=read('scripts/build_ebook_v07.py')"):s.index("m=json.loads((OUT/")];s=s.replace('v11','v14').replace('0.11','0.14')
s=s.replace("exec(compile(s,__file__,'exec'),globals())", "s=s.replace('.glossary h2{font-size:15pt;margin:5mm 0 3mm}', '.glossary h2{font-size:15pt;margin:3.5mm 0 2mm}')\nexec(compile(s,__file__,'exec'),globals())")
exec(compile(s,__file__,'exec'),globals())
hp=OUT/'ebook_review_v14.html';hp.write_text(hp.read_text(encoding='utf-8').replace('</style>','@media print{pre{break-inside:avoid;page-break-inside:avoid}}\n</style>',1),encoding='utf-8',newline='\n')
m=json.loads((OUT/'build_manifest_v14.json').read_text(encoding='utf-8'));m.update({'previous_v13_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'methodology_name':'TRI-V','fixed_axes':True,'record_fields':6,'publication_stage':'Bounded study-note integration, author review; no human or publication approval','new_content':[p['id'] for p in adopted],'old_v13_preserved':True,'notion_direct_body_read':False,'scope':'Only the user supplied passage; corrected concepts, no whole-source adaptation'})
(OUT/'build_manifest_v14.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.13','changes':changes,'adopted_paragraphs':adopted,'human_approved':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'edition':'v0.14','paragraphs_added':len(adopted),'registered_change_groups':len(changes),'source_characters':len(text),'original_statistics':'preserved'},ensure_ascii=False))
