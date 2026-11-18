"""Apply the author's approved terminology and publication claim boundaries."""
from pathlib import Path
import re,shutil,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v08';OUT.mkdir(parents=True,exist_ok=True)
if not (OUT/'assets').exists():shutil.copytree(ROOT/'e-book/exports/v07/assets',OUT/'assets')
def normalize_publication_text(text):
 text=text.replace('이 세 산출물을 연결하는 저자의 관점은 트리아타시스이고 실행 절차는 TRI-V다. 이번 판에서는 그 지향을 더 쉽게 전달할 이름으로 맥락항법을 제안한다.','이 세 산출물을 연결하는 방법론이 맥락항법이고, 이를 실행하는 절차가 TRI-V다.')
 text=text.replace('트리아타시스(Tri-Ataxis)','맥락항법').replace('트리아타시스','맥락항법').replace('Tri-Ataxis','맥락항법')
 for a,b in [('맥락항법라는','맥락항법이라는'),('맥락항법라고','맥락항법이라고'),('맥락항법를','맥락항법을'),('맥락항법가','맥락항법이'),('맥락항법는','맥락항법은'),('맥락항법와','맥락항법과'),('맥락항법로','맥락항법으로')]:text=text.replace(a,b)
 text=text.replace('# 11장 맥락항법이라는 제안, 어디까지 유효한가','# 11장 맥락항법의 기여와 검증 범위')
 text=re.sub(r'제안한 제목 ‘맥락항법’은.*?한국어 제목을 저자 검토용 제안으로 남긴다\.', '맥락항법은 이 책에서 사용하는 대표 방법론 이름이다. 이름의 선택은 최초성이나 상표 이용 가능성을 확인했다는 뜻이 아니다. 실행 절차인 TRI-V와 세 축의 의미는 그대로 유지한다.',text,count=1,flags=re.S)
 history='초기 구상에서는 이 관점을 트리아타시스(Tri-Ataxis)라고 불렀다. 이 책은 독자가 기억할 대표 이름을 맥락항법으로 정리하고, 이를 실행하는 절차를 TRI-V로 둔다. 초기 이름을 별도의 이론이나 추가 단계로 익힐 필요는 없다.'
 text=text.replace('# 1장 맥락항법이라는 관점','# 1장 맥락항법이라는 관점\n\n'+history,1)
 position=(ROOT/'e-book/manuscript/publication_position_v08.md').read_text(encoding='utf-8').split('\n\n',1)[1]
 text=text.replace('# 12장 한 건의 캠페인을 설계에서 결정까지',position+'\n\n# 12장 한 건의 캠페인을 설계에서 결정까지',1)
 text=text.replace('scripts/build_ebook_v07.py','scripts/build_ebook_v08.py').replace('scripts/render_verify_v07.py','scripts/render_verify_v08.py')
 assert text.count('트리아타시스')==1 and text.count('Tri-Ataxis')==1
 return text
s=(ROOT/'scripts/build_ebook_v07.py').read_text(encoding='utf-8')
s=s.replace("OUT=ROOT/'e-book/exports/v07'","OUT=ROOT/'e-book/exports/v08'")
for a,b in [('ebook_review_v07.md','ebook_review_v08.md'),('ebook_review_v07.html','ebook_review_v08.html'),('build_manifest_v07.json','build_manifest_v08.json'),('content_control_A4_v07.html','content_control_A4_v08.html'),('campaign_path_v07.svg','campaign_path_v08.svg')]:s=s.replace(a,b)
s=s.replace("read('e-book/exports/v07/'+name)","read('e-book/exports/v08/'+name)")
s=s.replace("def read(p):return (ROOT/p).read_text(encoding='utf-8')", "def read(p):\n t=(ROOT/p).read_text(encoding='utf-8')\n if p.endswith('.svg'):t=t.replace('트리아타시스','맥락항법').replace('Tri-Ataxis','맥락항법')\n return t")
s=s.replace("forbidden='\\u00b7", "text=normalize_publication_text(text)\nforbidden='\\u00b7",1)
s=s.replace("cover=read('e-book/design/v07/covers/selected_cover.html')", "cover=read('e-book/design/v07/covers/selected_cover.html').replace('맥락항법 제안 /','맥락항법 /').replace('0.7','0.8')")
s=s.replace('맥락항법은 제목 제안이며 저자 승인, 사람의 기술 검수와 출간 검토 전이다.','맥락항법은 저자의 실무 프레임워크이며 사람의 기술 검수와 출간 검토 전이다.')
s=s.replace('0.7 author review','0.8 author review').replace('저자 검토본 0.7','저자 검토본 0.8').replace('검토본0.7','검토본0.8')
exec(compile(s,str(ROOT/'scripts/build_ebook_v08.py'),'exec'),{'__file__':str(ROOT/'scripts/build_ebook_v08.py'),'__name__':'__main__','normalize_publication_text':normalize_publication_text})
manifest=json.loads((OUT/'build_manifest_v08.json').read_text(encoding='utf-8'));manifest.update({'previous_v07_characters':len((ROOT/'e-book/exports/v07/ebook_review_v07.md').read_text(encoding='utf-8')),'new_content':['Approved terminology: 맥락항법, executed through TRI-V; original name retained once as background','Chapter11 revised claim boundary, educational synthetic data rationale and untested reader learning evidence'],'methodology_name':'맥락항법','procedure':'TRI-V','terminology_approval':'User instructed proceeding with the proposed naming structure; book title, cover and publication not thereby approved','original_name_scope':'single historical paragraph in chapter1','reader_learning_evidence':'not yet tested with real participants','field_superiority_evidence':'not established and not a prerequisite for a scoped educational proposal','synthetic_scope':'educational scenarios, not actual OEM rates or outcomes'})
(OUT/'build_manifest_v08.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Applied approved method name and all three publication judgments to the actual reading manuscript.')
