"""Package and actually open the portable v16 reading edition."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,os,tempfile,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v16';dest=ROOT/'JH_CRM_ebook_reader_v16.zip'
v=json.loads((OUT/'validation_v16.json').read_text(encoding='utf-8'));i=json.loads((OUT/'integration_validation_v16.json').read_text(encoding='utf-8'));assert i['status']=='passed'
allow=['ebook_review_v16.pdf','ebook_review_v16.html','ebook_review_v16.md','validation_v16.json','integration_validation_v16.json','numeric_text_validation_v16.json','chapter12_sql_validation_v16.json','build_manifest_v16.json','REGRESSION_CHECK.json','PROVENANCE.json','MANUSCRIPT_CHANGES.json','SELF_CHECK.md','PLANNING_EXAMPLE.json','analysis_report_v13.json','MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','COUNTEREXAMPLE_RESULTS.json','counterexample_fixture.json','FOOTNOTES.json','FIGURE_DATA.json']
entries={n:OUT/n for n in allow}
for p in (OUT/'assets').iterdir():
 if p.suffix=='.woff2' or p.name.startswith('LICENSE') or p.suffix=='.json':entries['assets/'+p.name]=p
for name in set(re.findall(r'!\[[^\n]*\]\(([^)]+\.svg)\)',(OUT/'ebook_review_v16.md').read_text(encoding='utf-8'))):entries[name]=OUT/name
entries['REVIEW.md']=ROOT/'e-book/design/v16/REVIEW.md'
for p in (ROOT/'e-book/design/v16/covers').iterdir():
 if p.suffix in ['.svg','.png','.json']:entries['cover_options/'+p.name]=p
for name in ['AUDIT.md','AUDIT.json']:entries['numeric_review/'+name]=ROOT/'e-book/review/visual_numeric_v16'/name
start=f'''# TRI-V 전체 읽기본 v0.16

전체 책은 ebook_review_v16.pdf({v['pdf_pages']}쪽), 웹 읽기는 ebook_review_v16.html입니다. assets 폴더를 함께 유지하세요. 편집 원고는 같은 이름의 MD입니다. 일반 인쇄와 실제 하단 각주는 PDF를 사용하세요. 웹 읽기에서는 주석을 본문 근처에 표시합니다.

REVIEW.md에 전후 변화, 수치 검토 범위와 최종 쪽수가 있습니다. TRI-V 워크플로우9쪽, 세 판단22쪽, 관측 성숙27쪽, 여섯 칸 도형46쪽을 먼저 살펴보세요. cover_options에 표지3안과 비교 이미지가 있습니다. 표지 A는 추천 제안이며 최종 확정 전입니다.

한 장 기록은 MINIMUM_RECORD.pdf입니다. MINIMUM_RECORD.html에서는 여섯 칸에 입력하고 인쇄할 수 있지만 자동 저장은 하지 않습니다. SELF_CHECK.md는 v0.15에서 만든 학습 질문과 해설을 그대로 재사용한 참고 자료입니다.

이 묶음은 저자 검토본이며 출간 승인본이 아닙니다. JH Motors와 실습 수치는 교육용 가정입니다. numeric_review의82건 재계산은 사람의 독립 검수나 책 전체의 통계 무오류 판정이 아닙니다. 최종 문체와 표지 승인, 실제 독자 시험, 사람의 통계 검수 및 권리와 유통 검토는 남아 있습니다.

전체 DB와 개발 실행 환경은 포함하지 않으며 완전 재현 패키지가 아닙니다. 이전 판과 원자료 및 기존 감사 기록은 저장소에 보존했습니다. Open Design나 외부 서비스에 게시하지 않았습니다.
'''
assert all(p.is_file() for p in entries.values())
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for name,p in entries.items():z.write(p,name)
 z.writestr('START_HERE.md',start)
with ZipFile(dest) as z:
 assert z.testzip() is None
 for name,p in entries.items():assert hashlib.sha256(z.read(name)).digest()==hashlib.sha256(p.read_bytes()).digest()
 count=len(z.namelist())
with tempfile.TemporaryDirectory(prefix='reader_v16_',dir=os.environ.get('TMPDIR')) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True)
  for filename in ['ebook_review_v16.html','MINIMUM_RECORD.html']:
   page=browser.new_page(viewport={'width':1200,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto((Path(td)/filename).as_uri());page.evaluate('document.fonts.ready');assert not errors
   if filename=='ebook_review_v16.html':
    assert page.locator('.chapter').count()==12 and page.locator('a[id^="g-"]').count()==36
    assert page.locator('figure[data-figure]').count()==13
    assert page.evaluate('document.fonts.check("16px ReaderSerif")')
    assert not page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].some(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1))))")
   else:
    assert page.locator('textarea').count()==6;page.locator('#r1').fill('입력 동작 확인');assert page.locator('#r1').input_value()=='입력 동작 확인'
   page.set_viewport_size({'width':390,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth');page.close()
  browser.close()
report={'archive':str(dest),'file_count':count,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'integrity':'passed','exact_entry_bytes':'passed','extracted_book_and_minimum_record':'passed','full_reproduction_environment':False,'real_reader_test_conducted':False,'human_review_approved':False}
(OUT/'package_smoke_v16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
