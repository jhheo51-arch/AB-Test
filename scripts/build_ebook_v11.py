"""Integrate the settled TRI-V record and bounded editorial work into the full book."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v11';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v10/ebook_review_v10.md');text=base
if not (OUT/'assets').exists():shutil.copytree(ROOT/'e-book/exports/v10/assets',OUT/'assets')
for p in (ROOT/'e-book/exports/v10').glob('*.svg'):shutil.copyfile(p,OUT/p.name)
# Canonical operating contract replaces, rather than duplicates, its earlier version.
start=text.index('## TRI-V 공통 운용 기준');end=text.index('# 2장 정화, 비교할 수 있는 결과를 만들기')
text=text[:start]+read('e-book/manuscript/tri_v_operating_contract_v11.md').strip()+'\n\n'+text[end:]
# Keep the supplied education history and app observations; add the substantiated work narrative.
intro_start=text.index('나는 마케팅을 공부하면서');intro_end=text.index('\n\n',intro_start)
author_paragraphs=read('e-book/manuscript/tri_v_author_origin_v03.md').strip().split('\n\n')[2:]
assert len(author_paragraphs)==4
career='나는 마케팅을 공부하면서 고객이 왜 어떤 선택을 하는지 알고 싶었다. 경영학과 마케팅 트랙에서 출발해 정치외교학을 함께 공부한 것은 그 선택을 둘러싼 이해관계와 구조까지 보고 싶어서였다.'
text=text[:intro_start]+career+'\n\n'+'\n\n'.join(author_paragraphs[:3]).replace('정상적으로 동작하는 장면을 더 보여주는 것만으로는 그 판단을 대신할 수 없었다.','정상적으로 동작하는 장면을 더 보여주는 것만으로는 그 판단을 대신할 수 없었다.[5][6]')+text[intro_end:]
# Separate inferential victory from the selected business action.
old='TRI-V에서 말하는 승리는 이 선택을 설명할 수 있는 상태에 가깝다.'
assert old in text;text=text.replace(old,'통계적 우위와 실행 선택은 서로 다른 기록이다. 이 축에서는 확인한 차이가 어느 선택을 뒷받침하는지 설명한다.',1)
old='세 단계를 거친 뒤 독자가 자신의 실험에 대해 설명할 수 있다면 이 방법론은 제 역할을 한 것이다.'
text=text.replace(old,'세 축의 기록으로 중요한 누락과 불필요한 확인을 줄이는지는 실제 작성에서 평가해야 한다. 독자가 자신의 실험과 선택의 이유를 설명할 수 있는지는 그때 관찰할 작업 결과다.',1)
# The positive and stop cases are separate fixtures, not additions to an old experiment.
fixture=json.loads((OUT/'counterexample_fixture.json').read_text(encoding='utf-8'));report=json.loads((OUT/'COUNTEREXAMPLE_RESULTS.json').read_text(encoding='utf-8'));results=report['cases'];assert len(results)==4
labels=['가: 현재 범위','나: 사전 집단','다: 정보 부족','라: 보호 검토'];states={'execution_candidate':'실행 후보','additional_evidence':'추가 근거 검토','protection_review':'보호 우선 검토'}
extra='## 충분한 근거가 있을 때 검토를 끝내기\n\n'
extra+='앞선 사례에서 도입을 보류한 이유를 이해했다면 반대 방향도 확인해야 한다. 모든 결과에 새로운 분석과 재실험을 요구하는 절차는 판단을 안전하게 만들기보다 일을 늘릴 수 있다. 다음 네 조건은 기존 시승 자료를 바꾸거나 합친 실험이 아니라 검토의 경계를 보여주려고 별도로 구성한 교육용 고정 카운트다. 같은 선택적 서비스 안내의 표현 A와 B를 비교하며 혜택과 비용은 같다고 가정한다. 동의와 적격 조건, 개인 배정과 독립 및 비간섭, 원장 대사와 개인별 30일 관측이 충족됐다는 설정이다. 표본 수는 검정력으로 산출한 권장 인원이 아니다.\n\n'
extra+='이 예제에서만 사용할 판단 규칙은 완료율 차이 구간의 하한이 최소 개선 +1.0pp를 넘고, 철회 증가가 허용 한계 +0.5pp보다 작다는 보호 근거가 있을 때 해당 범위의 실행 후보로 넘기는 것이다. 숫자는 가상 회사의 선택 기준이며 TRI-V의 보편적 도입 공식이 아니다. 결과를 구성한 교육 예시에서 사전 기준이라고 말하는 것은 이야기의 순서이지 실제 미래 실험의 사전등록이라는 뜻도 아니다.\n\n'
extra+='| 조건 | A 완료와 배정 | B 완료와 배정 | 차이와 구간 |\n|---|---|---|---|\n'
for label,c,r in zip(labels,fixture['cases'],results):
 extra+=f'| {label} | {c["completed_A"]:,}/{c["n_A"]:,}명 | {c["completed_B"]:,}/{c["n_B"]:,}명 | {r["difference_pp"]:+.2f}pp, [{r["performance_interval_pp"][0]:+.2f}, {r["performance_interval_pp"][1]:+.2f}]pp ({r["interval_coverage_pct"]:g}%) |\n'
extra+='\n완료 차이는 Newcombe 위험차 구간으로 계산하고 Wilson 경계를 직접 조합한 값과 대조했다. 보호 조건에는 해당 집단의 단측 score 비열등성 평가와 대응 상한을 사용했다. 아래 값은 철회율 B-A의 상한이며 단순히 악화의 p값이 크다는 이유로 안전을 선언한 것이 아니다.\n\n'
extra+='| 조건 | A와 B의 철회 | 보호 단측 상한 | 현재 판단 |\n|---|---|---|---|\n'
for label,c,r in zip(labels,fixture['cases'],results):
 extra+=f'| {label} | {c["withdrawn_A"]:,}/{c["n_A"]:,}명, {c["withdrawn_B"]:,}/{c["n_B"]:,}명 | {r["guard_one_sided_upper_pp"]:+.3f}pp ({100*(1-r["alpha_per_population"]):g}%) | {states[r["state"]]} |\n'
extra+='\n조건 가에서는 현재 대상과 정책 범위의 성과 및 보호 조건이 충족됐다. 그러면 실행 후보와 필요한 실제 승인 경로를 남기고, 목적 없는 세분화와 금전 모형은 추가하지 않는다. 모든 고객의 효과가 같거나 장기 효과까지 확인됐다는 뜻은 아니다. 이 예제를 현장 전체 전환의 자동 승인으로 사용해서도 안 된다.\n\n'
c=fixture['cases'][1];o=results[1]['other_group'];other=c['other_prespecified_group']
extra+=f'조건 나는 배정 전에 두 고객군의 적용 주장을 정하고 각 집단의 성과와 보호를 함께 요구한 설정이다. 두 적용 주장에는 Bonferroni로 각 유의수준 0.025를 사용했다. 첫 이용 대상의 완료 구간은 97.5%, 보호 상한은 단측 97.5% 수준이다. 다른 사전 집단은 A {other["completed_A"]:,}/{other["n_A"]:,}명과 B {other["completed_B"]:,}/{other["n_B"]:,}명이며 완료 차이의 97.5% 구간은 [{o["performance_interval_pp"][0]:+.2f}, {o["performance_interval_pp"][1]:+.2f}]pp다. 첫 집단에 적절한 확증 근거가 있다는 이유로 다른 집단의 우위나 두 효과의 차이까지 입증한 것으로 바꾸지 않는다. 반대로 정한 첫 집단 안의 적용을 판단할 때도 무조건 다시 실험하라는 요구는 하지 않는다.\n\n'
extra+='조건 다에서는 주지표 구간이 사업 기준을 넘는 경우와 못 넘는 경우를 모두 남긴다. 이 차이가 실제 선택을 바꾼다면 추가 정보의 사업 필요와 수집 부담을 검토한다. 필요하다고 판단했으면 새 자료를 보기 전에 후속 설계와 종료 규칙을 정한다. 고정 종료한 실험에 유의해질 때까지 표본을 덧붙이는 것은 이 경로가 아니다. 조건 라에서는 완료 개선이 있어도 보호 평가가 충족되지 않으므로 보호 대응을 우선 검토한다. 비열등성을 확인하지 못한 모든 경우가 확정 위해라는 뜻은 아니며 관측 차이와 불확실성도 함께 설명한다.\n\n'
extra+='같은 기준은 빈칸에도 적용된다. 적격 조건과 배정, 주지표와 보호 평가에 사용하지 않는 선택 설문의 미응답만으로 현재 판단을 막을 필요는 없다. 반면 주지표를 지지할 측정 근거가 없다면 예제의 알려진 정답을 대신 사용할 수 없다. 진행에 필수인 근거와 나중에 보완할 맥락을 구분하는 것이 누락 방지와 과잉 검토를 함께 다루는 방법이다.\n\n'
extra+='기본 기록의 첫 칸에는 A 유지와 같은 범위의 B 전환 가운데 무엇을 고르는지 적고, 결과 위치와 적용 범위, 실행 후보 및 실제 승인 상태를 연결한다. 다음 확인이 없다면 그 이유와 다시 검토할 조건을 남긴다. 보류하는 경우도 누구의 어떤 자료가 어떤 선택을 바꿀지 특정한다. 여기서 보여준 것은 기록과 계산이 서로 맞물리는가의 구현 검사이며, 실제 사람이 더 빠르고 정확해졌다는 비교 결과는 아니다.\n\n'
(OUT/'counterexamples_in_book_v11.md').write_text(extra.rstrip()+'\n',encoding='utf-8',newline='\n')
marker='# 9장 학습을 실험 설계로 옮기기';assert text.count(marker)==1;text=text.replace(marker,extra+marker,1)
# A bounded editorial contribution is applied only after the child deliverable is available.
start=text.index('# 9장 학습을 실험 설계로 옮기기');end=text.index('# 11장 TRI-V의 기여와 적용 범위')
editorial=read('e-book/manuscript/editorial_v11/ch09_ch10.md');assert editorial.startswith('# 9장 ') and editorial.count('# 10장 ')==1
text=text[:start]+editorial.strip()+'\n\n'+text[end:]
start=text.index('# 11장 TRI-V의 기여와 적용 범위');end=text.index('# 12장 한 건의 캠페인을 설계에서 결정까지')
text=text[:start]+read('e-book/manuscript/method_scope_v11.md').strip()+'\n\n'+text[end:]
# Reuse the six-field record in the final campaign, without replacing the detailed analysis.
marker='# 부록 사례와 자료를 찾아가는 길';assert text.count(marker)==1
record='기존 캠페인의 상세 계산을 끝낸 뒤에는 1장의 여섯 항목으로 압축한다. 지금 결정할 것은 주어진 대상에서 A를 B로 바꿀지이며, 해당 메시지의 발송 자체와 다른 정책의 효과는 별도 대비에 의존한다. 근거 칸에는 주지표와 보호 결과의 위치를 연결하고, 적용 범위와 현재 선택 및 실제 승인 상태를 나눈다. 추가 확인은 원래 자료에 없던 사업과 보호 기준 및 용량 중 어떤 조건이 선택을 바꿀지로 쓴다. 이 자료에서 B를 바로 채택하지 않는다고 현행 A가 모든 대안 중 최적이라고 결론 내리지 않는다. 추가 분석을 그만하는 판단도 정한 실험 종료 규칙을 바꾸거나 운영상 보호 조치를 늦추는 뜻이 아니다.\n\n'
text=text.replace(marker,record+marker,1)
refs='[5] 허재혁. CRM LOOP 프로젝트의 고객 가치와 캠페인 기획 및 README. 거래 행과 고객 및 기준일을 구분하고 대상 선정의 근거와 설계 범위를 확인했다. 실제 발송 효과를 입증한 자료가 아니다. 저자 프로젝트 문서에는 열람 권한이 필요할 수 있다.\n\nhttps://github.com/jhheo51-arch/crm-loop\n\n[6] 허재혁. Aurora Owners 360의 PRD와 README. T4 기한 계산, T7 공란 접수 허용, T8 필요한 팀장 미지정 저장 차단의 과거 검증 기록을 대조했다. 실제 운영 개선율이나 이번 책 작업에서 org 테스트를 재실행했다는 뜻이 아니다.\n\nhttps://github.com/jhheo51-arch/aurora-owners-360\n\n'
marker='Ron Kohavi, Diane Tang, Ya Xu.';assert text.count(marker)==1;text=text.replace(marker,refs+marker,1)
text=text.replace('scripts/build_ebook_v10.py','scripts/build_ebook_v11.py').replace('scripts/render_verify_v10.py','scripts/render_verify_v11.py')
old_commands='uv run --with scipy --with statsmodels scripts/analyze_winner_v04.py\nuv run --with scipy --with statsmodels scripts/build_winner_scenarios_v04.py\nuv run --with markdown scripts/build_ebook_v11.py\nuv run --with markdown --with playwright --with pymupdf --with pillow scripts/render_verify_v11.py'
new_commands='uv run --with statsmodels --with scipy --with playwright --with pymupdf python scripts/build_tri_v_record_v11.py\nuv run --with markdown python scripts/build_ebook_v11.py\nuv run --with fonttools --with brotli python scripts/prepare_fonts_v11.py\npython scripts/verify_ebook_v11_numbers.py\nuv run --with markdown --with playwright --with pymupdf --with pillow python scripts/render_verify_v11.py\nuv run --with pymupdf python scripts/verify_v11_integration.py'
assert old_commands in text;text=text.replace(old_commands,new_commands,1)
old_reproduction='재현은 저장소 루트에서 아래 순서로 실행한다. 데이터 생성과 분석은 기존 파일을 읽고, 새 판의 조판은 숫자를 바꾸지 않는다. 원본 계획과 데이터의 해시를 보존하며 각 결과 JSON에 실제 실행 환경을 기록했다.'
new_reproduction='이 판의 읽기본을 다시 만들려면 전체 저장소의 명세와 원자료가 있는 별도 작업 사본에서 아래 순서로 실행한다. 원래 분석과 생성 코드를 다시 돌리는 명령은 여기에 섞지 않는다. 숫자 검사는 기존 결과 장부와 읽기 전용 SQL을 사용하고, 새 반례는 별도 고정 카운트로 계산한다. 조판은 원본 계획과 DB 및 지난 판을 덮어쓰지 않는다. 읽기 ZIP에는 전체 개발 환경이 포함되지 않으며 Python과 uv 및 설치 Chrome과 글꼴이 필요하다.'
assert old_reproduction in text;text=text.replace(old_reproduction,new_reproduction,1)
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbidden)
assert not re.search(r'^### ',text,re.M) and len(re.findall(r'^## 사례 [1-6] ',text,re.M))==6
assert text.count('트리아타시스')==1 and text.count('Tri-Ataxis')==1
(OUT/'ebook_review_v11.md').write_text(text,encoding='utf-8',newline='\n')
s=read('scripts/build_ebook_v07.py');s=s[s.index('body=markdown.markdown'):]
for a,b in [('ebook_review_v07.html','ebook_review_v11.html'),('build_manifest_v07.json','build_manifest_v11.json'),('content_control_A4_v07.html','content_control_A4_v11.html')]:s=s.replace(a,b)
s=s.replace("read('e-book/exports/v07/'+name)","read('e-book/exports/v11/'+name)")
s=s.replace("cover=read('e-book/design/v07/covers/selected_cover.html')", "cover=read('e-book/design/v07/covers/selected_cover.html').replace('맥락항법 제안 / TRI-V','TRI-V').replace('0.7','0.11')")
s=s.replace('0.7 author review','0.11 author review').replace('저자 검토본 0.7','저자 검토본 0.11').replace('검토본0.7','검토본0.11')
s=s.replace('맥락항법은 제목 제안이며 저자 승인, 사람의 기술 검수와 출간 검토 전이다.','TRI-V의 A/B 검토 구조를 설명하는 저자 검토본이다. 실제 독자 시험과 사람의 기술 및 권리 검토, 최종 출간 승인은 별도다.')
s=s.replace("glossary_marker=re.search", "body=re.sub(r'<table[^>]*>.*?</table>',lambda m:m[0].replace('<table>','<table class=\"record-summary\">',1) if '<th>기본 기록</th>' in m[0] else m[0],body,flags=re.S)\nglossary_marker=re.search",1)
s=s.replace("toc='<nav", "css+='\\n@media print{table.record-summary{break-inside:avoid}}\\n'\ntoc='<nav",1)
exec(compile(s,__file__,'exec'),globals())
m=json.loads((OUT/'build_manifest_v11.json').read_text(encoding='utf-8'));m.update({'previous_v10_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'methodology_name':'TRI-V','fixed_axes':True,'record_fields':6,'publication_stage':'PUB-02 started, bounded full-book integration and editorial pass; human approval pending','new_content':['Canonical six-field contract with action scope, distinct stopping meanings and decision-changing checks','Attributed author project narrative, not retrospective randomized A/B claims','Four positive and stop counterexamples in chapter8 with fixed educational counts','Bounded chapter9-10 prose editing and consolidated chapter11 claim scope','Final campaign mapped back to the six-field record'],'field_effect_or_reader_learning_proven':False,'old_v10_preserved':True})
(OUT/'build_manifest_v11.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print('v0.11 complete manuscript and HTML built; originals preserved.')
