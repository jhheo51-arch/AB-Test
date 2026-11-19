"""Create v19 regression and portable-package checks from frozen tooling."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'scripts'
old=(S/'verify_v18_integration.py').read_text(encoding='utf-8');tail=old[old.index("lookup=load('e-book/exports/v18/LOOKUP.json')"):]
tail=tail.replace('v18','v19').replace('V18','V19').replace("'version':'v0.18'","'version':'v0.19'")
tail=tail.replace('e-book/exports/v17/LOOKUP.json','e-book/exports/v18/LOOKUP.json').replace("'substantive_prose_edits'","'reading_layer_edits'").replace("'additional_structural_and_precision_operations'","'worked_insertions'")
prefix='''"""Verify registered v19 changes and preserved numerical/visual inputs."""
from pathlib import Path
import json,re,hashlib,math,xml.etree.ElementTree as ET
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v19';D=R/'e-book/manuscript/development_v19';checks=[]
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def check(name,ok):checks.append({'check':name,'pass':bool(ok)});assert ok,name
def compact(s):return re.sub(r'\\s+','',s)
def near(a,b):return math.isclose(float(a),float(b),abs_tol=1e-9,rel_tol=1e-10)
for path,h in load('e-book/manuscript/development_v19/BASELINE.json')['hashes'].items():check('Frozen '+path,hashlib.sha256((R/path).read_bytes()).hexdigest()==h)
old=(R/'e-book/exports/v18/ebook_review_v18.md').read_text(encoding='utf-8');new=(O/'ebook_review_v19.md').read_text(encoding='utf-8');expected=old.split('# 찾아보기')[0]
pref=load('e-book/manuscript/development_v19/PREFACE_EDITS.json');edits=load('e-book/manuscript/development_v19/READING_LAYERS.json');ops=load('e-book/manuscript/development_v19/WORKED_LINKS.json')
for e in pref+edits:
 check('Exact replacement '+e['before'][:40],expected.count(e['before'])==1 and e['before']!=e['after']);expected=expected.replace(e['before'],e['after'])
for e in ops:
 check('Exact insertion '+str(e['chapter']),expected.count(e['anchor'])==1 and bool(e['text']));expected=expected.replace(e['anchor'],e['anchor']+'\\n\\n'+e['text'])
def clean(s):
 s=re.sub(r'<a id="[gb]-[^\"]+\"></a>\\s*','',s);s=re.sub(r'\\[사례 자료 길잡이\\]\\([^\\n]+\\)\\s*','',s)
 return compact(s.replace('_v19.svg','_v18.svg'))
check('Exact registered main text replay',clean(expected)==clean(new.split('# 찾아보기')[0]))
appendix=new.split('# 부록 A 계산과 자료')[1].split('# 부록 B 사례와 자료 길잡이')[0]
for e in edits:check('Technical source archived verbatim '+str(e['chapter'])+' '+e['before'][:25],e['before'] in appendix)
m=load('e-book/exports/v19/MANUSCRIPT_CHANGES.json');check('Full edition, not prototype',m['prototype'] is False and m['reading_layers']==edits and m['worked_links']==ops and m['preface_edits']==pref)
check('Three substantive fixes represented',len(edits)>=8 and {'1','9'}<={str(e['chapter']) for e in ops})
check('Approved title and scope applied',all(t in (O/'cover_A.svg').read_text(encoding='utf-8') for t in ['그래서, 이 캠페인','계속할까요?','CRM A/B 테스트 실무','TRI-V로 근거를 점검하고','적용 범위와 다음 행동을 정하는 법','허재혁 지음']))
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','analysis_report_v13.json','COUNTEREXAMPLE_RESULTS.json','PLANNING_EXAMPLE.json','REGRESSION_CHECK.json','PROVENANCE.json']:
 check('Preserved companion '+name,(O/name).read_bytes()==(R/'e-book/exports/v18'/name).read_bytes())
'''
(S/'verify_v19_integration.py').write_text(prefix+tail,encoding='utf-8',newline='\n')
t=(S/'package_reader_v18.py').read_text(encoding='utf-8').replace('v18','v19').replace('V18','V19').replace('v0.18','v0.19')
start=t.index("for name in ['REVIEW_01_04.md'");end=t.index("back=v['backmatter_pages']",start)
t=t[:start]+"for name in ['AUTHOR_DECISION.md','READING_LAYERS.md','WORKED_LINKS.md']:\n entries['development/'+name]=R/'e-book/manuscript/development_v19'/name\nentries['DEVELOPMENT.md']=R/'e-book/design/v19/DEVELOPMENT.md'\nentries['WHITESPACE.json']=R/'e-book/design/v19/WHITESPACE.json'\nentries['cover.png']=R/'e-book/design/v19/review/cover.png'\n"+t[end:]
t=t.replace('표지와 가제는 사람의 최종 확정 전 제안입니다.','제목 구성은 저자 승인에 따라 적용했습니다. 최종 표지 시각과 출간 승인은 별도입니다.')
t=t.replace('83개 윤문안과 별도 구조 및 정확성 보완을 반영했습니다. 정량 그림5개는 보존한 계산 결과에서 직접 그렸습니다. REVIEW.md와 editorial_review/PROSE_QUALITY_FINAL.md에서 변경 근거와 남은 약점을 확인하세요. 모의 편집 평가이며 실제 독자시험이나 사람의 통계 검수가 아닙니다. 장별 REVIEW 문서의 원문 인용은 수정 전 v0.17의 평가입니다.','필수 독해와 분석 구현의 경로를 나누고, 기존 명세의 재사용 및 요청과 회신을 반영한 판단문 수정 과정을 보완했습니다. 정량 그림과 기존 계산 결과는 보존했습니다. REVIEW.md와 DEVELOPMENT.md에 실제 변경과 남은 한계를 기록했습니다. 실제 독자시험이나 사람의 통계 검수는 아닙니다.')
(S/'package_reader_v19.py').write_text(t,encoding='utf-8',newline='\n')
print('v19 integration and extracted-reader package checks prepared')
