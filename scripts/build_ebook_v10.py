"""Add the simple illustrated explanation and a sourced origin/scope discussion."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v10';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v09/ebook_review_v09.md');text=base
if not (OUT/'assets').exists():shutil.copytree(ROOT/'e-book/exports/v09/assets',OUT/'assets')
for p in (ROOT/'e-book/exports/v09').glob('*.svg'):shutil.copyfile(p,OUT/p.name)
# Keep the three pictures from the tested explainer, but make SVG styles self-contained.
svgs=re.findall(r'<svg\b.*?</svg>',read('e-book/explainers/tri_v_eli5.html'),re.S);assert len(svgs)==3
for name,svg in zip(['tri_v_easy_comparison.svg','tri_v_easy_population.svg','tri_v_easy_decision.svg'],svgs):
 svg=svg.replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" ',1).replace('class="soft"','fill="#F2F5F1" stroke="#142D32" stroke-width="3"').replace('class="ink"','fill="#FFFFFF" stroke="#142D32" stroke-width="4"').replace('class="small"','font-size="21"')
 def style_text(m):
  a=m[1];size='' if 'font-size' in a else ' font-size="22"'
  return '<text'+a+size+' fill="#142D32" font-family="ReaderSans,sans-serif">'
 svg=re.sub(r'<text([^>]*)>',style_text,svg)
 (OUT/name).write_text(svg,encoding='utf-8')
marker='# 1장 맥락항법이라는 관점';assert text.count(marker)==1
text=text.replace(marker,'# 1장 TRI-V로 실험에서 결정까지',1)
first='좋은 문구를 골랐다는 보고와 좋은 사업 결정을 내렸다는 보고 사이에는 거리가 있다.'
assert text.count(first)==1;text=text.replace(first,read('e-book/manuscript/tri_v_easy_start_v10.md')+'\n\n'+first,1)
text=text.replace('이 세 산출물을 연결하는 방법론이 맥락항법이고, 이를 실행하는 절차가 TRI-V다.','이 세 산출물을 연결하는 저자의 방법론이 TRI-V다. 공통 운용 기준은 그 방법을 쓰는 사용설명서다.',1)
text=text.replace('나는 이런 결과를 다루는 관점을 맥락항법이라고 부른다.','나는 이런 결과를 다루는 방법을 TRI-V로 정리했다.',1).replace('이를 실제 순서로 풀어 쓴 것이 TRI-V다.','비교와 적용 범위, 실행 조건을 세 축의 질문과 기록으로 연결한다.',1)
text=text.replace('초기 구상에서는 이 관점을 트리아타시스(Tri-Ataxis)라고 불렀다. 이 책은 독자가 기억할 대표 이름을 맥락항법으로 정리하고, 이를 실행하는 절차를 TRI-V로 둔다. 초기 이름을 별도의 이론이나 추가 단계로 익힐 필요는 없다.','초기 구상에서는 이 문제의식을 트리아타시스(Tri-Ataxis)라고 불렀고 집필 과정에서 맥락항법이라는 이름도 검토했다. 여기서는 실제 질문과 판단 기록으로 연결되는 TRI-V 자체를 저자의 방법론으로 설명한다. 다른 이름을 별개의 이론이나 추가 단계로 외울 필요는 없다.',1)
text=text.replace('맥락항법은 질문을 바라보는 관점이고 TRI-V는 그 질문을 순서대로 실행하는 절차다.','TRI-V는 질문과 확인 절차, 적용 범위와 결정 기록을 연결하는 저자의 방법론이다. 공통 운용 기준은 이 방법을 쓰는 설명서이며 별개의 방법론을 추가한 것이 아니다.',1)
marker='# 11장 맥락항법의 기여와 검증 범위';assert text.count(marker)==1
text=text.replace(marker,'# 11장 TRI-V의 기여와 적용 범위\n\n'+read('e-book/manuscript/tri_v_origin_scope_v10.md'),1)
text=text.replace('맥락항법은 이 책에서 사용하는 대표 방법론 이름이다. 이름의 선택은 최초성이나 상표 이용 가능성을 확인했다는 뜻이 아니다. 실행 절차인 TRI-V와 세 축의 의미는 그대로 유지한다.','이 책은 TRI-V 자체를 저자가 정리한 방법론으로 설명한다. 공통 운용 기준과 양식은 이를 사용하는 도구이며 별도 브랜드를 반드시 붙일 필요는 없다. 명칭의 선택은 최초성이나 상표 이용 가능성의 확인을 뜻하지 않는다.',1)
text=text.replace('집필 과정에서 맥락항법이라는 이름도 검토했다.','집필 과정에서 __HISTORIC_KOREAN_NAME__이라는 이름도 검토했다.',1)
for a,b in [('맥락항법이라는','TRI-V라는'),('맥락항법이라고','TRI-V라고'),('맥락항법으로','TRI-V로'),('맥락항법은','TRI-V는'),('맥락항법을','TRI-V를'),('맥락항법이','TRI-V가'),('맥락항법과','TRI-V와')]:text=text.replace(a,b)
text=text.replace('맥락항법','TRI-V').replace('__HISTORIC_KOREAN_NAME__','맥락항법')
text=text.replace('TRI-V라는 이름과 TRI-V의 연결은 저자가 제안한 방법론이다.','TRI-V라는 이름과 세 축의 연결은 저자가 제안한 방법론이다.')
text=text.replace('이 책에서 제안하는 관점과 TRI-V는 새로운 통계 검정법이 아니다.','TRI-V는 새로운 통계 검정법이 아니다.')
text=text.replace('scripts/build_ebook_v09.py','scripts/build_ebook_v10.py').replace('scripts/render_verify_v09.py','scripts/render_verify_v10.py')
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb';assert not any(c in text for c in forbidden)
assert text.count('트리아타시스')==1 and text.count('Tri-Ataxis')==1
assert len(re.findall(r'^## 사례 [1-6] ',text,re.M))==6 and not re.search(r'^### ',text,re.M)
(OUT/'ebook_review_v10.md').write_text(text,encoding='utf-8')
s=read('scripts/build_ebook_v07.py');s=s[s.index('body=markdown.markdown'):]
for a,b in [('ebook_review_v07.html','ebook_review_v10.html'),('build_manifest_v07.json','build_manifest_v10.json'),('content_control_A4_v07.html','content_control_A4_v10.html')]:s=s.replace(a,b)
s=s.replace("read('e-book/exports/v07/'+name)","read('e-book/exports/v10/'+name)")
s=s.replace("cover=read('e-book/design/v07/covers/selected_cover.html')", "cover=read('e-book/design/v07/covers/selected_cover.html').replace('맥락항법 제안 / TRI-V','TRI-V').replace('0.7','0.10')")
s=s.replace('0.7 author review','0.10 author review').replace('저자 검토본 0.7','저자 검토본 0.10').replace('검토본0.7','검토본0.10')
s=s.replace('맥락항법은 제목 제안이며 저자 승인, 사람의 기술 검수와 출간 검토 전이다.','TRI-V를 저자 제안 방법론으로 설명한다. 다른 브랜드명과 최종 표지 및 출간 승인은 별도이며 현장 우월성을 입증한 책이 아니다.')
exec(compile(s,__file__,'exec'),globals())
m=json.loads((OUT/'build_manifest_v10.json').read_text(encoding='utf-8'))
m.update({'previous_v09_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'new_content':['ELI5-style fictional test-drive explanation and three large illustrations in chapter1','Origin of the three V labels distinguished from established principle sources in chapter11','Applicability limits distinguished from the ability to ask broad questions','TRI-V itself described as author-proposed methodology; operating criteria are its guide'],'methodology_name':'TRI-V','external_brand_approved':False,'origin_limit':'Supplied initial draft already named TRI-V and referred to an earlier framework; first coinage cannot be established from that excerpt','universal_applicability_claim':False,'historical_novelty_claim':False,'field_effect_or_reader_learning_proven':False})
(OUT/'build_manifest_v10.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');print('Built the complete illustrated reading edition; no original data or previous edition modified.')
