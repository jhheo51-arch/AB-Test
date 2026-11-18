"""Apply verified statistical corrections to the full v13 reading edition."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v13';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v12/ebook_review_v12.md');text=base;changes=[]
def replace(old,new,count=1):
 global text
 assert text.count(old)==count,(old[:90],text.count(old),count);text=text.replace(old,new);changes.append({'before':old,'after':new,'occurrences':count})
corrections=ROOT/'e-book/analysis/corrections_v13'
analysis=json.loads((ROOT/'e-book/virtual-data/v13/analysis_report_v13.json').read_text(encoding='utf-8'))
ready={r['scenario']:r['planning_power_under_stated_effect'] for r in analysis['metric_readiness']}
replace('계약 1%에서 1.2% 변화는 약 51.8%, 철회 0.8%에서 1.0% 변화는 약 60.0%다.',f"계약 1%에서 1.2% 변화는 약 {100*ready['contract_rare']:.1f}%, 철회 0.8%에서 1.0% 변화는 약 {100*ready['optout_risk']:.1f}%다.")
replace('보호 조건에는 해당 집단의 단측 score 비열등성 평가와 대응 상한을 사용했다.','보호 조건에는 이항 제약우도를 직접 푼 단측 score 비열등성 평가와 MN 유한표본 보정 및 대응 상한을 사용했다. 상세 수치에서 발견한 구현 불일치는 이 직접 계산으로 교정했으며, 아래 반올림 표시와 실행 후보 판단은 바뀌지 않았다.')
replace('e-book/virtual-data/v03/data/jh_motors_v03.sqlite','e-book/virtual-data/v13/data/jh_motors_v13.sqlite',2)
replace('이며 `DATA_DICTIONARY.md`와 실제 SQLite 정의를 함께 확인한다.','이며 원자료의 `e-book/virtual-data/v03/DATA_DICTIONARY.md`와 v13의 `outcomes_v13.sql` 및 실제 SQLite 정의를 함께 확인한다.')
old='집계가 나왔다고 정화를 끝내지 않는다. 실제 정의를 보면 이 뷰의 시간 조건은 배정일에 관측 창을 더한 상한을 확인하지만 사건이 배정일 이후라는 하한을 별도로 적지는 않았다. 따라서 다른 자료로 옮겨 쓸 때에는 배정 전 사건이 섞이지 않는지도 확인해야 한다. 이번 읽기 전용 확인에서는 배정 전 사건이 없었고, 원본 사건을 배정일부터 각 창의 종료일까지 고유 배정 단위로 다시 세었을 때 위 합계와 일치했다. 뷰의 출력만 믿지 않고 원장과 시간 정의를 함께 확인해야 하는 이유다. 현실의 데이터에서는 이 확인을 생략한 채 같은 필드 이름이라는 이유로 결과를 재사용하지 않는다.'
new='집계가 나왔다고 정화를 끝내지 않는다. 원래 v03 뷰는 관측 창의 상한만 확인했고 배정일 이후라는 하한이 빠져 있었다. 이번 판에서는 원 DB를 보존한 파생 v13 DB의 뷰에 하한과 상한을 모두 넣었다. 배정 전 사건과 창 밖 사건이 제외되고 양 끝의 사건은 포함되는지 경계 검사를 추가했다. 현재 원자료에는 배정 전 사건이 없어 교정 전후의 집계는 같지만, 다른 자료에 옮겨 쓸 때도 같은 결과가 된다고 가정해서는 안 된다. 원장과 시간 정의를 함께 확인한 뒤 재사용한다.'
replace(old,new)
replace('자료는 v03 DB이며 작성 시 읽기 전용으로 실제 outcomes 뷰와','자료는 v03 원자료에서 뷰만 교정한 v13 DB이며 작성 시 읽기 전용으로 실제 outcomes 뷰와')
replace('| 추가 실습 코드 | `scripts/build_winner_scenarios_v04.py` |','| 추가 실습 코드 | `scripts/build_winner_scenarios_v04.py` |\n| 이번 판의 통계 정정 | `scripts/correct_statistics_v13.py`, `e-book/analysis/corrections_v13/` |\n| 교정한 뷰와 입력 이력 | `e-book/virtual-data/v13/`, `e-book/analysis/corrections_v13/PROVENANCE.json` |')
replace('python scripts/edit_ebook_v12.py','uv run --with numpy --with scipy --with statsmodels python scripts/correct_statistics_v13.py')
for a,b in [('build_ebook_v12.py','build_ebook_v13.py'),('prepare_fonts_v12.py','prepare_fonts_v13.py'),('verify_ebook_v12_numbers.py','verify_ebook_v13_numbers.py'),('render_verify_v12.py','render_verify_v13.py'),('verify_v12_integration.py','verify_v13_integration.py')]:replace('scripts/'+a,'scripts/'+b)
replace('원래 분석과 생성 코드를 다시 돌리는 명령은 여기에 섞지 않는다. 숫자 검사는 기존 결과 장부와 읽기 전용 SQL을 사용하고, 새 반례는 별도 고정 카운트로 계산한다.','원래 생성기를 다시 돌리지는 않는다. 먼저 정정 코드가 원자료의 읽기 전용 입력으로 교정 장부와 파생 DB를 만들고, 숫자 검사는 기존의 불변 결과와 이번 정정 값을 함께 대조한다. 반례는 같은 고정 카운트에서 보호 계산만 교정한다.')
# Keep the exact-byte provenance issue explicit, without rewriting the old hash.
marker='방법 문서는 statsmodels의 두 비율 검정, 비율 차이 구간, 검정력과 scipy의 Welch 검정 설명을 참고했다.'
replace(marker,'원 계획의 체크아웃은 LF이고 DB에 저장된 계획 해시는 CRLF 표현에 대응한다. 줄바꿈만 변환한 내용 동등성과 원본의 정확 바이트 일치는 서로 다르다. 이 이력은 덮어쓰지 않고 이번 파생 자료의 매니페스트에 실제 입력 해시와 표현 동등성을 나누어 기록했다. 반복실험도 기존 명세의 같은 시드와 난수 순서를 별도 구현으로 재생했으며, 새로 보존한 배열을 당시의 역사적 원배열이라고 부르지 않는다.\n\n'+marker)
(OUT/'ebook_review_v13.md').write_text(text,encoding='utf-8',newline='\n')
for p in (ROOT/'e-book/exports/v12').glob('*.svg'):shutil.copyfile(p,OUT/p.name)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','counterexample_fixture.json']:shutil.copyfile(ROOT/'e-book/exports/v12'/name,OUT/name)
shutil.copyfile(corrections/'COUNTEREXAMPLE_RESULTS.json',OUT/'COUNTEREXAMPLE_RESULTS.json')
shutil.copyfile(ROOT/'e-book/virtual-data/v13/analysis_report_v13.json',OUT/'analysis_report_v13.json')
for name in ['REGRESSION_CHECK.json','PROVENANCE.json']:shutil.copyfile(corrections/name,OUT/name)
# Rounded companion values must agree with the corrected full precision results.
rs=json.loads((OUT/'COUNTEREXAMPLE_RESULTS.json').read_text(encoding='utf-8'))['cases']
for r in rs:
 assert f"+{r['guard_one_sided_upper_pp']:.3f}" in read('e-book/exports/v12/COUNTEREXAMPLES.md')
shutil.copytree(ROOT/'e-book/exports/v12/assets',OUT/'assets',dirs_exist_ok=True)
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(x in text for x in forbidden)
s=read('scripts/build_ebook_v11.py');s=s[s.index("s=read('scripts/build_ebook_v07.py')"):s.index("m=json.loads((OUT/")]
s=s.replace('v11','v13').replace('0.11','0.13')
s=s.replace("exec(compile(s,__file__,'exec'),globals())", "s=s.replace('.glossary h2{font-size:15pt;margin:5mm 0 3mm}', '.glossary h2{font-size:15pt;margin:3.5mm 0 2mm}')\nexec(compile(s,__file__,'exec'),globals())")
exec(compile(s,__file__,'exec'),globals())
html_path=OUT/'ebook_review_v13.html'
html_path.write_text(html_path.read_text(encoding='utf-8').replace('</style>','@media print{pre{break-inside:avoid;page-break-inside:avoid}}\n</style>',1),encoding='utf-8',newline='\n')
m=json.loads((OUT/'build_manifest_v13.json').read_text(encoding='utf-8'));m.update({'previous_v12_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'methodology_name':'TRI-V','fixed_axes':True,'record_fields':6,'publication_stage':'Verified statistical corrections applied; no new publication gate or human approval','new_content':['Correct A/B sample size and planning probability mapping','Direct constrained-likelihood score protection results','Derived database with both event-window bounds, preserving original tables','Explicit provenance and replay trace limitations'],'original_book_v12_preserved':True,'human_statistical_review_completed':False})
(OUT/'build_manifest_v13.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(OUT/'MANUSCRIPT_CHANGES.json').write_text(json.dumps({'baseline':'v0.12','changes':changes,'human_approved':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'version':'v0.13','source_characters':len(text),'replacement_groups':len(changes),'contract_power_pct':100*ready['contract_rare'],'withdrawal_power_pct':100*ready['optout_risk']},ensure_ascii=False))
