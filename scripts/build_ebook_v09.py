"""Integrate the operating contract, tiered routes and criterion history into the book."""
from pathlib import Path
import re,json,hashlib,html,shutil
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v09';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return (ROOT/p).read_text(encoding='utf-8')
base=read('e-book/exports/v08/ebook_review_v08.md');text=base
if not (OUT/'assets').exists():shutil.copytree(ROOT/'e-book/exports/v08/assets',OUT/'assets')
for p in (ROOT/'e-book/exports/v08').glob('*.svg'):
 if p.name!='tri_v_method.svg':shutil.copyfile(p,OUT/p.name)
shutil.copyfile(ROOT/'e-book/design/v09/tri_v_operating_flow.svg',OUT/'tri_v_method.svg')
text=text.replace('![맥락항법과 TRI-V의 세 단계]','![TRI-V 공통 기준과 세 산출물]')
contract=read('e-book/manuscript/tri_v_operating_contract_v09.md').replace('# TRI-V 공통 운용 기준','## TRI-V 공통 운용 기준',1)
marker='# 2장 정화, 비교할 수 있는 결과를 만들기';assert text.count(marker)==1
text=text.replace(marker,'<a id="tri-v-operating-contract"></a>\n\n'+contract+'\n\n'+marker,1)
route='처음 읽을 때는 1장의 [TRI-V 공통 운용 기준](#tri-v-operating-contract)에서 비교 명세, 적용 범위 문장과 결정문을 먼저 확인해도 좋다. 세 축의 질문은 함께 검토하되 모든 실험에 복잡한 집단 분석과 경제 모형을 요구하지 않는다. 별도 결정 기록 양식은 실험 전 기준, 결과 후 해석, 기준 변경과 재검토 이력을 같은 실험 식별자 아래 연결한다.'
text=text.replace('# 들어가며',route+'\n\n# 들어가며',1)
annotations=json.loads(read('e-book/manuscript/tri_v_case_records_v09.json'))['cases'];assert [x['id'] for x in annotations]==list(range(1,7))
for row in annotations:
 marker='## 사례 '+str(row['id']+1)+' ' if row['id']<6 else '# 8장 다시 한 건의 결정으로'
 assert text.count(marker)==1,(row['id'],marker)
 text=text.replace(marker,row['paragraph']+'\n\n'+marker,1)
links={
 '# 3장 해체와 입체화, 평균 아래의 고객을 읽기':'이 축의 작성 결과는 1장의 공통 운용 기준에 있는 비교 명세다. 해석 가능, 일부 지표 제한, 비교 보류 중 현재 상태와 근거를 남기고, 미확인 자료의 소유자와 확인 기한 또는 기한 결정 책임자를 적는다. 모든 칸을 채웠다는 사실이 통계적 타당성을 보증하는 것은 아니다.',
 '# 4장 언어의 전환, 차이를 회사의 선택으로 옮기기':'여기서 남길 것은 공통 운용 기준의 적용 범위 문장이다. 현재 전체 효과만 읽는 이유와 다음 대상의 차이를 적는 것까지가 최소 경로다. 추가 집단 분석이 필요하다면 그 질문과 정보량, 사전 및 사후 지위를 표시한다. 세분화를 하지 않은 기록도 효과가 균일하다고 보장하지 않는다면 정당한 결과물이 될 수 있다.',
 '# 5장 숫자를 읽을 때 필요한 통계':'이 축의 산출물은 공통 운용 기준의 결정문이다. 현재 선택과 근거, 미확인 조건, 책임과 기한 및 재검토 계기를 함께 쓴다. 사업과 보호 기준은 가능하면 결과 전에 공통 기준에 기록하고 사후 변경은 별도 이력으로 남긴다. 조건부 실행 후보와 실제 승인, 보호 조치와 분석 결론을 서로 대신하지 않도록 한다.'}
for marker,p in links.items():assert text.count(marker)==1;text=text.replace(marker,p+'\n\n'+marker,1)
marker='# 부록 사례와 자료를 찾아가는 길'
closing='이 결정문을 자신의 업무로 옮길 때는 별도 TRI-V 결정 기록의 실험 전 공통 기준, 결과 후 세 축, 기준 변경과 재검토 이력을 함께 사용한다. 위 사례의 최소 사업 효과와 철회 한계는 사후 교육 가정이므로 변경 시점과 결과 열람 여부를 명시한다. 아직 정해지지 않은 실제 담당자와 기한, 손실 한계는 임의의 이름과 숫자로 채우지 않는다. 누가 그 공란을 확정할지 남기는 것까지가 기록이며 이 예시가 실제 승인을 대신하지 않는다.'
assert text.count(marker)==1;text=text.replace(marker,closing+'\n\n'+marker,1)
text=text.replace('scripts/build_ebook_v08.py','scripts/build_ebook_v09.py').replace('scripts/render_verify_v08.py','scripts/render_verify_v09.py')
forbidden='\u00b7\u2022\u2027\u318d\u22c5\u30fb'
assert not any(c in text for c in forbidden) and not re.search(r'^### ',text,re.M)
assert text.count('트리아타시스')==1 and text.count('Tri-Ataxis')==1
assert len(re.findall(r'^## 사례 [1-6] ',text,re.M))==6
(OUT/'ebook_review_v09.md').write_text(text,encoding='utf-8')
# Reuse the tested editorial layout, not its old manuscript-assembly steps.
s=read('scripts/build_ebook_v07.py');s=s[s.index('body=markdown.markdown'):]
for a,b in [('ebook_review_v07.html','ebook_review_v09.html'),('build_manifest_v07.json','build_manifest_v09.json'),('content_control_A4_v07.html','content_control_A4_v09.html')]:s=s.replace(a,b)
s=s.replace("read('e-book/exports/v07/'+name)","read('e-book/exports/v09/'+name)")
s=s.replace("cover=read('e-book/design/v07/covers/selected_cover.html')", "cover=read('e-book/design/v07/covers/selected_cover.html').replace('맥락항법 제안 /','맥락항법 /').replace('0.7','0.9')")
s=s.replace('0.7 author review','0.9 author review').replace('저자 검토본 0.7','저자 검토본 0.9').replace('검토본0.7','검토본0.9')
s=s.replace('맥락항법은 제목 제안이며 저자 승인, 사람의 기술 검수와 출간 검토 전이다.','영문 대표 명칭은 검토 중이며 TRI-V 운용 기준과 작성 양식을 보완한 판이다. 사람의 검수와 출간 승인은 별도다.')
exec(compile(s,__file__,'exec'),globals())
m=json.loads((OUT/'build_manifest_v09.json').read_text(encoding='utf-8'))
m.update({'previous_v08_characters':len(base),'previous_v06_characters':len(read('e-book/exports/v06/ebook_review_v06.md')),'new_content':['Shared TRI-V operating contract in chapter1 and cross-references in chapters2-4','Required deliverables and minimum/deep-route triggers','Pre-result criteria with explicit post-result change history','All six existing cases mapped to the same operating record','Chapter12 linked to the unified blank record'],'english_name_status':{'previous_proposal':'Contexvia','user_latest_spelling':'contextvia','display_candidate':'Contextvia','approved':False,'book_cover_not_renamed':True},'reader_learning_evidence':'not yet tested','not_an_automatic_approval_rule':True})
(OUT/'build_manifest_v09.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');print('Integrated operating repairs into the complete v0.9 manuscript; original data and v0.8 preserved.')
