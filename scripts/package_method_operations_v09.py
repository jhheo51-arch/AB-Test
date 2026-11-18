"""Package the actual v0.9 book and unified operating tools, then open the extracted HTML."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,tempfile,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v09';dest=ROOT/'JH_CRM_method_operations_v09.zip'
names=['ebook_review_v09.pdf','ebook_review_v09.html','ebook_review_v09.md','tri_v_operating_card_v09.pdf','tri_v_operating_card_v09.html','tri_v_decision_record_v09.pdf','tri_v_decision_record_v09.html','tri_v_decision_record_v09.md','tri_v_criteria_change_log_v09.csv','validation_v09.json','operations_validation_v09.json','numeric_text_validation_v09.json','chapter12_sql_validation_v09.json','build_manifest_v09.json']
files=[OUT/n for n in names]+sorted((OUT/'assets').glob('*'))+sorted(OUT.glob('*.svg'))
assert all(p.is_file() for p in files)
readme='''# TRI-V 운용 보완 v0.9

처음에는 tri_v_operating_card_v09.pdf 한 장을 보세요. 전체 책은 ebook_review_v09.pdf이며 공통 기준은8쪽에서 시작합니다. tri_v_decision_record_v09.pdf는3쪽 인쇄 양식이고, 같은 이름의 Markdown은 편집할 원본입니다. PDF 자체는 입력형 폼이 아닙니다.

작성은 실험 전 공통 기준, 결과 후 세 축, 기준 변경 이력 순서입니다. 변경 이력 CSV는 헤더만 들어 있으며 실제 변경과 승인 기록은 없습니다. 모르는 값을 만들어 채우지 말고 미확인과 확인 책임자를 적으세요.

HTML을 보려면 assets 폴더를 그대로 유지하세요. 여섯 기존 사례는 동일한 운용 기록과 연결했으며 기존 수치와 원자료는 보존했습니다. 이 묶음은 읽기 및 작성 도구이지 전체 DB와 분석 개발 환경이 아닙니다. 숫자 대조와 정상 출력은 실제 독자의 사용성 개선이나 학습 효과, 현장 우월성의 증거가 아닙니다.

영문 최종 이름은 아직 미확정입니다. 이전 제안 Contexvia와 사용자 표기 contextvia를 서로 다른 후보로 보존했습니다. v0.9 표지의 명칭을 새 영문 이름으로 자동 치환하지 않았습니다. 다른 출판 단계의 작업도 새로 시작하지 않았습니다.

REVIEW.md에 보완 전후와 구현 범위 및 남은 확인을 기록했습니다. 기존 실제 독자 시험 준비본은 v0.8 읽기 후보를 기록하므로 실제 시행 전 사용할 판과 과제 및 판정 버전을 함께 다시 승인해야 합니다. 전체 자료의 공개나 상업 배포를 승인한 묶음이 아닙니다. 글꼴 라이선스는 assets에서 확인하세요.
'''
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(OUT).as_posix())
 z.write(ROOT/'e-book/design/v09/REVIEW.md','REVIEW.md');z.write(ROOT/'e-book/manuscript/tri_v_case_records_v09.json','CASE_RECORD_MAPPING.json');z.writestr('START_HERE.md',readme)
with ZipFile(dest) as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read(p.relative_to(OUT).as_posix())).digest()==hashlib.sha256(p.read_bytes()).digest()
with tempfile.TemporaryDirectory(prefix='tri_v_v09_',dir=os.environ.get('TMPDIR')) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True)
  for filename in ['ebook_review_v09.html','tri_v_operating_card_v09.html','tri_v_decision_record_v09.html']:
   page=browser.new_page(viewport={'width':1200,'height':900});errs=[];page.on('pageerror',lambda e:errs.append(str(e)));page.goto((Path(td)/filename).as_uri());page.evaluate('document.fonts.ready');assert page.evaluate('document.fonts.check("16px ReaderSans")');assert not errs
   if filename=='ebook_review_v09.html':
    assert page.locator('.chapter').count()==12 and page.locator('#tri-v-operating-contract').count()==1
    bad=page.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash)");assert not bad,bad
   page.close()
  browser.close()
report={'archive':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'zip_integrity':'passed','exact_packaged_bytes':'passed','extracted_html_open_checks':3,'full_reproduction_environment':False,'human_learning_or_field_effect_validation':False}
(OUT/'package_smoke_v09.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
