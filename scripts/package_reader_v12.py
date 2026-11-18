"""Build a portable v0.12 reader plus its short operating record."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,os,tempfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v12';dest=ROOT/'JH_CRM_ebook_reader_v12.zip'
validation=json.loads((OUT/'validation_v12.json').read_text(encoding='utf-8'));integration=json.loads((OUT/'integration_validation_v12.json').read_text(encoding='utf-8'))
allow=['ebook_review_v12.pdf','ebook_review_v12.html','ebook_review_v12.md','validation_v12.json','integration_validation_v12.json','numeric_text_validation_v12.json','chapter12_sql_validation_v12.json','build_manifest_v12.json','MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','VALIDATION.json','COUNTEREXAMPLES.md','COUNTEREXAMPLE_RESULTS.json','counterexample_fixture.json']
files=[OUT/n for n in allow]+sorted((OUT/'assets').glob('*'))+sorted(OUT.glob('*.svg'));assert all(p.is_file() for p in files)
pages=integration['chapter_pages']
start=f'''# TRI-V 전체 읽기본 v0.12

전체 책은 ebook_review_v12.pdf, 웹 읽기는 같은 이름의 HTML, 편집 원고는 같은 이름의 MD입니다. assets 폴더를 함께 유지하세요. 전체 {validation['pdf_pages']}쪽의 저자 검토본이며 출간 승인본이 아닙니다.

들어가며의 경험 서사는 {pages['author_origin']}쪽, 공통 운용 기준은 {pages['operating_contract']}쪽, 충분한 근거가 있을 때 검토를 끝내는 보완 예제는 {pages['positive_cases']}쪽, 기여와 적용 범위는 {pages['scope']}쪽에서 확인할 수 있습니다.

한 장 기록은 이전 판의 여섯 칸을 그대로 재사용한 MINIMUM_RECORD.pdf입니다. 브라우저에서 입력하고 인쇄하려면 MINIMUM_RECORD.html, 편집하려면 MINIMUM_RECORD.md를 쓰세요. 입력형 PDF는 아니며 HTML 입력도 자동 저장하지 않습니다. 기존 계획과 분석은 링크로 재사용하고 필요한 부분만 상세 기록으로 엽니다.

TRI-V의 세 축과 여섯 항목을 유지했습니다. 가능한 선택과 적용 범위를 먼저 정하고, 추가 분석을 멈추는 것과 실험의 통계적 종료 및 운영 중지를 구분합니다. B를 채택하지 않는 판단을 A의 최적성 증명으로 쓰지 않습니다. 다음 확인은 어떤 결과가 어떤 선택을 바꾸는지로 남깁니다.

본문의 가상 시승 자료와 보완 예제의 고정 카운트는 서로 다른 교육용 자료입니다. 고객과 실험을 합치지 않습니다. 저자 경험과 프로젝트 문서는 방법론의 배경 및 작업 기준의 근거이며, 실제 발송 성과나 TRI-V의 시간 절감 효과로 소급하지 않았습니다. 이번 묶음의 계산과 출력 검사는 사람의 독립 검수와 실제 독자 시험을 대신하지 않습니다.

이 묶음은 읽기본과 기록 도구 및 보완 예제의 고정 입력과 결과를 포함합니다. 전체 DB와 개발 환경, 원 프로젝트의 전체 문서와 저자 제공 이미지는 포함하지 않습니다. 원 프로젝트 링크에는 열람 권한이 필요할 수 있습니다. 전체 재현은 저장소의 별도 작업 사본과 실행 환경이 필요합니다.

PUB-02의 남은 문체 교정을 적용한 검토본입니다. 최종 저자 표현 승인, 독립 사람의 통계와 실무 검토, 실제 독자 시험, 권리와 유통 및 출간 승인은 남아 있습니다. 기존 독자 시험 자료를 이 판에 자동 배정하거나 기존 읽기본 해시를 덮어쓰지 마세요.
'''
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(OUT).as_posix())
 z.write(ROOT/'e-book/design/v12/REVIEW.md','REVIEW.md');z.writestr('START_HERE.md',start)
with ZipFile(dest) as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read(p.relative_to(OUT).as_posix())).digest()==hashlib.sha256(p.read_bytes()).digest()
 count=len(z.namelist())
with tempfile.TemporaryDirectory(prefix='reader_v12_',dir=os.environ.get('TMPDIR')) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True)
  for file in ['ebook_review_v12.html','MINIMUM_RECORD.html']:
   page=browser.new_page(viewport={'width':1200,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto((Path(td)/file).as_uri());page.evaluate('document.fonts.ready');assert not errors
   if file=='ebook_review_v12.html':
    assert page.locator('.chapter').count()==12 and page.locator('a[id^="g-"]').count()==36
    assert page.evaluate('document.fonts.check("16px ReaderSerif")')
    assert not page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].some(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1))))")
   else:
    assert page.locator('textarea').count()==6;page.locator('#r1').fill('입력 동작 확인');assert page.locator('#r1').input_value()=='입력 동작 확인'
   page.set_viewport_size({'width':390,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth');page.close()
  browser.close()
report={'archive':str(dest),'file_count':count,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'integrity':'passed','exact_entry_bytes':'passed','extracted_book_and_minimum_record':'passed','full_reproduction_environment':False,'real_reader_test_conducted':False,'human_review_approved':False}
(OUT/'package_smoke_v12.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))