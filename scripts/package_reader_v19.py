"""Package and exercise the final v19 reader without a reproduction-environment claim."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,os,tempfile,re
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v19';dest=R/'JH_CRM_ebook_reader_v19.zip'
v=json.loads((O/'validation_v19.json').read_text(encoding='utf-8'));integration=json.loads((O/'integration_validation_v19.json').read_text(encoding='utf-8'));assert integration['status']=='passed'
allow=['ebook_review_v19.pdf','ebook_review_v19.html','ebook_review_v19.md','validation_v19.json','integration_validation_v19.json','numeric_text_validation_v19.json','chapter12_sql_validation_v19.json','build_manifest_v19.json','LOOKUP.json','FIGURE_DATA_V19.json','MANUSCRIPT_CHANGES.json','visual_geometry_v19.json','FOOTNOTES.json','FIGURE_DATA.json','MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','PLANNING_EXAMPLE.json','SELF_CHECK.md','COUNTEREXAMPLE_RESULTS.json','analysis_report_v13.json','REGRESSION_CHECK.json','PROVENANCE.json']
entries={name:O/name for name in allow}
for p in (O/'assets').iterdir():
 if p.suffix in ['.woff2','.json'] or p.name.startswith('LICENSE'):entries['assets/'+p.name]=p
for name in set(re.findall(r'!\[[^\n]*\]\(([^)]+\.svg)\)',(O/'ebook_review_v19.md').read_text(encoding='utf-8'))):entries[name]=O/name
entries['cover_A.svg']=O/'cover_A.svg';entries['REVIEW.md']=R/'e-book/design/v19/REVIEW.md'
for name in ['AUTHOR_DECISION.md','READING_LAYERS.md','WORKED_LINKS.md']:
 entries['development/'+name]=R/'e-book/manuscript/development_v19'/name
entries['DEVELOPMENT.md']=R/'e-book/design/v19/DEVELOPMENT.md'
entries['WHITESPACE.json']=R/'e-book/design/v19/WHITESPACE.json'
entries['cover.png']=R/'e-book/design/v19/review/cover.png'
back=v['backmatter_pages'];navigation=' / '.join(f'{name} {page}쪽' for name,page in back.items())
start=f'''# TRI-V 전체 읽기본 v0.19

PDF는 ebook_review_v19.pdf({v['pdf_pages']}쪽), 검색 가능한 웹 읽기본은 ebook_review_v19.html입니다. assets 폴더를 함께 유지하세요. 실제 하단 각주와 고정 쪽 판면은 PDF에서 확인하세요. MD는 편집용 원고입니다.

{navigation}. 웹 읽기본에서 용어나 영문 약어를 입력해 찾을 수 있습니다. 제목 구성은 저자 승인에 따라 적용했습니다. 최종 표지 시각과 출간 승인은 별도입니다.

필수 독해와 분석 구현의 경로를 나누고, 기존 명세의 재사용 및 요청과 회신을 반영한 판단문 수정 과정을 보완했습니다. 정량 그림과 기존 계산 결과는 보존했습니다. REVIEW.md와 DEVELOPMENT.md에 실제 변경과 남은 한계를 기록했습니다. 실제 독자시험이나 사람의 통계 검수는 아닙니다.

한 장 작성 양식은 MINIMUM_RECORD.html입니다. 여섯 칸 입력과 인쇄가 가능하지만 자동 저장하지 않습니다. JH Motors와 수치는 교육용 합성 자료입니다. 이 묶음은 전체 DB나 개발 실행 환경을 포함한 완전 재현 패키지가 아닙니다. 사람의 통계 검수, 실제 독자시험 및 권리와 출간 승인은 남아 있습니다.
'''
assert all(p.is_file() for p in entries.values()),[str(p) for p in entries.values() if not p.is_file()]
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for name,p in entries.items():z.write(p,name)
 z.writestr('START_HERE.md',start)
with ZipFile(dest) as z:
 assert z.testzip() is None
 for name,p in entries.items():assert z.read(name)==p.read_bytes()
 count=len(z.namelist());assert count==len(entries)+1
with tempfile.TemporaryDirectory(prefix='reader_v19_',dir=os.environ.get('TMPDIR')) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  b=p.chromium.launch(channel='chrome',headless=True)
  for name in ['ebook_review_v19.html','MINIMUM_RECORD.html']:
   q=b.new_page(viewport={'width':1200,'height':900});errors=[];q.on('pageerror',lambda e:errors.append(str(e)));q.goto((Path(td)/name).as_uri());q.evaluate('document.fonts.ready');assert not errors
   if name.startswith('ebook'):
    assert q.locator('.chapter').count()==12 and q.locator('.term-entry').count()==36
    assert not q.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].some(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1))))")
    for term in ['MDE','SRM','Twyman']:
     q.locator('#term-search').fill(term);assert q.locator('.index-table tbody tr:visible').count()==1
    q.locator('#term-clear').click();assert q.locator('.index-table tbody tr:visible').count()==36
   else:q.locator('#r1').fill('입력 확인');assert q.locator('#r1').input_value()=='입력 확인'
   q.set_viewport_size({'width':390,'height':844});assert not q.evaluate('document.documentElement.scrollWidth>innerWidth');q.close()
  b.close()
report={'archive':str(dest),'file_count':count,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'integrity':'passed','exact_entry_bytes':'passed','extracted_book_search_and_record':'passed','full_reproduction_environment':False,'actual_reader_test':False,'human_review_approved':False}
(O/'package_smoke_v19.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
