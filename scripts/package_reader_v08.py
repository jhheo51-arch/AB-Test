"""Package and exercise the portable v0.8 reading files; no dataset generation."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,os,tempfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v08';dest=ROOT/'JH_CRM_ebook_reader_v08.zip'
readme='''# 허재혁 CRM A/B 테스트 실무서 v0.8 읽기 묶음

PDF로 읽으려면 ebook_review_v08.pdf, 웹으로 읽으려면 ebook_review_v08.html을 여세요. 웹 글꼴을 위해 assets 폴더를 같은 위치에 유지하세요. ebook_review_v08.md는 편집 원고입니다.

대표 방법론은 맥락항법, 실행 절차는 TRI-V입니다. 초기 구상 이름은1장 배경 한 문단에만 남깁니다. 11장에는 교육적 제안의 주장 범위, 합성 자료의 적합성과 실제 독자 학습의 미검증 상태를 반영했습니다.

이 파일은80쪽 저자 검토본입니다. 판매 승인본이 아니며 실제 독자 수행 시험, 독립 사람의 통계와 실무 검토, 권리와 유통 규격 및 최종 교정이 남아 있습니다. 기존103개 수치 대조와 읽기 전용 SQL 일치 확인은 학습 효과와 현장 우월성의 증명이 아닙니다.

실제 독자 시험의 참여자 문제, 진행자 판정지와 운영안은 별도의 저자 검토용 시험 자료로 제공합니다. 정답지를 참여자에게 사전 전달하지 마세요. 임의 외부 공유나 모집 및 보상은 승인되지 않았습니다.

이 읽기 묶음에는 전체 합성 DB와 생성 환경을 넣지 않았습니다. 전체 계산 재현 패키지가 아닙니다. 별도 재현 제공 범위는 출판 체크리스트에서 확정해야 합니다. 기존 분석과 원본 자료를 덮어쓰지 않았습니다. 글꼴 라이선스는 assets의 원문을 확인하세요.
'''
files=[OUT/'ebook_review_v08.pdf',OUT/'ebook_review_v08.html',OUT/'ebook_review_v08.md',OUT/'build_manifest_v08.json',OUT/'validation_v08.json',OUT/'numeric_text_validation_v08.json',OUT/'chapter12_sql_validation_v08.json']+sorted((OUT/'assets').glob('*'))
assert all(p.is_file() for p in files)
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(OUT).as_posix())
 z.writestr('START_HERE.md',readme)
with ZipFile(dest) as z:assert z.testzip() is None
scratch=Path(os.environ.get('TMPDIR') or ROOT/'e-book/exports/v08');scratch.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='reader_v08_smoke_',dir=scratch) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True);page=browser.new_page();errs=[];page.on('pageerror',lambda e:errs.append(str(e)));page.goto((Path(td)/'ebook_review_v08.html').as_uri());page.evaluate('document.fonts.ready')
  assert page.locator('.chapter').count()==12
  assert page.locator('a[id^="g-"]').count()==36
  assert page.evaluate('document.fonts.check(\'16px "Noto Serif KR"\')')
  assert not page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].some(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1))))")
  assert not errs,errs
  browser.close()
report={'archive':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'zip_integrity':'passed','portable_local_html':'passed','chapters':12,'glossary_entries':36,'reader_kit_only':True,'full_reproduction_environment':False,'real_reader_test_conducted':False}
(OUT/'package_smoke_v08.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
