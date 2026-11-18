from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,os,tempfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v10';dest=ROOT/'JH_CRM_ebook_reader_v10.zip'
files=[OUT/n for n in ['ebook_review_v10.pdf','ebook_review_v10.html','ebook_review_v10.md','validation_v10.json','origin_scope_validation_v10.json','numeric_text_validation_v10.json','chapter12_sql_validation_v10.json','build_manifest_v10.json']]+sorted((OUT/'assets').glob('*'))+sorted(OUT.glob('*.svg'))
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(OUT).as_posix())
 z.write(ROOT/'e-book/explainers/tri_v_eli5.html','tri_v_eli5.html');z.write(ROOT/'e-book/design/v10/REVIEW.md','REVIEW.md')
 z.writestr('START_HERE.md','# TRI-V 읽기본 v0.10\n\n전체 책은 ebook_review_v10.pdf, 웹 읽기는 같은 이름의 HTML입니다. assets 폴더를 유지하세요. 쉬운 그림 설명은 tri_v_eli5.html에서 넘겨 볼 수 있습니다.\n\n책의 쉬운 설명은6쪽, 공통 운용 기준은10쪽, 출발점과 적용 범위는57쪽입니다. 전체90쪽 저자 검토본이며 판매 승인본은 아닙니다. TRI-V 자체를 저자 제안 방법론으로 설명하고 다른 브랜드명은 확정하지 않았습니다.\n\n기존 원칙의 연결과 새로운 통계 원리의 발견, 범용 질문과 모든 상황의 효과 추정, 합성 설명과 실제 학습 및 현장 증거를 구분합니다. 원문 구상에 있는 칭찬은 신규성 증거가 아닙니다.\n\n이 묶음은 읽기 파일이며 전체 데이터와 재현 환경을 포함하지 않습니다. 기존 v0.9 작성 양식은 별도 보존합니다. 실제 시험 전 읽기본과 과제 및 판정 버전을 함께 고정해야 합니다. 독자 시험과 사람의 검수, 권리와 유통 및 최종 출간 승인은 미완료입니다.\n')
with ZipFile(dest) as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read(p.relative_to(OUT).as_posix())).digest()==hashlib.sha256(p.read_bytes()).digest()
with tempfile.TemporaryDirectory(prefix='reader_v10_',dir=os.environ.get('TMPDIR')) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True)
  for f in ['ebook_review_v10.html','tri_v_eli5.html']:
   page=browser.new_page(viewport={'width':1200,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto((Path(td)/f).as_uri());page.evaluate('document.fonts.ready');assert not errors
   if f=='ebook_review_v10.html':
    assert page.locator('.chapter').count()==12 and page.locator('a[id^="g-"]').count()==36
    assert page.evaluate('document.fonts.check("16px ReaderSerif")')
    assert not page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].some(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1))))")
   else:
    for n in range(3):page.locator(f'#tab-{n}').click();assert page.locator(f'#scene-{n}').is_visible()
   page.close()
  browser.close()
report={'archive':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'integrity':'passed','exact_entry_bytes':'passed','extracted_book_and_illustrated_explainer':'passed','full_reproduction_environment':False,'real_reader_test_conducted':False}
(OUT/'package_smoke_v10.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
