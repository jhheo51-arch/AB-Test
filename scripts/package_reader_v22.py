"""Package the verified v22 reading edition and exercise extracted files."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,re,tempfile,os
import pymupdf
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v22';V=R/'e-book/design/v22';dest=R/'e-book/packages/JH_CRM_ebook_reader_v22.zip'
v=json.loads((O/'validation_v22.json').read_text(encoding='utf-8'));assert json.loads((O/'integration_validation_v22.json').read_text(encoding='utf-8'))['status']=='passed'
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);q=b.new_page();q.goto((O/'MINIMUM_RECORD.html').as_uri());q.evaluate('document.fonts.ready');q.pdf(path=str(O/'MINIMUM_RECORD.pdf'),format='A4',print_background=True,prefer_css_page_size=True);b.close()
with pymupdf.open(O/'MINIMUM_RECORD.pdf') as d:assert len(d)==1,len(d)
allow=['ebook_review_v22.pdf','ebook_review_v22.html','ebook_review_v22.md','MINIMUM_RECORD.html','MINIMUM_RECORD.pdf','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','LOOKUP.json','FOOTNOTES.json','FIGURE_DATA.json','FIGURE_DATA_V22.json','validation_v22.json','integration_validation_v22.json','numeric_text_validation_v22.json','chapter12_sql_validation_v22.json','MANUSCRIPT_CHANGES.json','build_manifest_v22.json','visual_geometry_v22.json']
entries={n:O/n for n in allow}
for p in (O/'assets').iterdir():
 if p.suffix in ['.woff2','.json'] or p.name.startswith('LICENSE'):entries['assets/'+p.name]=p
for n in set(re.findall(r'!\[[^\n]*\]\(([^)]+\.svg)\)',(O/'ebook_review_v22.md').read_text(encoding='utf-8'))):entries[n]=O/n
entries.update({'cover_A.svg':O/'cover_A.svg','DEVELOPMENT.md':V/'DEVELOPMENT.md','REVIEW.md':V/'REVIEW.md','UI_VALIDATION.json':V/'ui_validation_v22.json','development/CORRECTION_NOTES.md':R/'e-book/manuscript/development_v22/CORRECTION_NOTES.md'})
entries['PRINT_VALIDATION.json']=V/'print_validation_v22.json'
entries['development/PROOF_CORRECTIONS.json']=R/'e-book/manuscript/development_v22/PROOF_CORRECTIONS.json'
start=f'''# TRI-V 전체 읽기본 v0.22

PDF는 ebook_review_v22.pdf({v['pdf_pages']}쪽)입니다. 완성 결정문은 79쪽 한 면이며 이전 판의 문구를 보존했습니다.
웹 읽기본은 ebook_review_v22.html입니다. ZIP을 먼저 압축 해제하고 assets 폴더를 함께 유지하세요.

웹에서는 그림이나 그림 확대 버튼을 누르면 원래 크기로 볼 수 있습니다. 작은 화면에서는 그림 안을 가로와 세로로 움직이세요. 닫기 또는 Esc로 닫으면 읽던 위치로 돌아갑니다. PDF의 그림은 정적입니다.

작성 양식은 MINIMUM_RECORD.html입니다. 여섯 항목과 메타정보를 작성한 뒤 기록 복사 또는 텍스트 파일로 저장을 누르세요. 자동 복사가 차단되면 선택된 기록을 직접 복사할 수 있습니다. 입력은 자동 저장하거나 외부로 보내지 않습니다. 창을 닫거나 새로고침하기 전에 직접 보관하세요. 파일 공유 전 고객 정보와 내부 링크를 확인하세요. 저장은 실제 실행이나 발송 승인이 아닙니다.

이번 판은 검수에서 확인한 참조 오류와 두 표현의 범위, 긴 입력의 인쇄 누락만 고쳤습니다. 입력한 기록이 길면 여러 쪽으로 인쇄됩니다. 빈 양식은 한 쪽을 유지합니다. 기존 정량 자료와 79쪽 결정문은 그대로입니다.

JH Motors와 수치는 교육용 합성 자료입니다. 이 묶음은 원 DB를 포함한 완전 재현 환경이 아닙니다. 사람의 통계 검수, 실제 독자시험과 권리 및 최종 출간 승인은 별도입니다.
'''
assert all(p.is_file() for p in entries.values()),[str(p) for p in entries.values() if not p.is_file()]
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for n,p in entries.items():z.write(p,n)
 z.writestr('START_HERE.md',start)
with ZipFile(dest) as z:
 assert z.testzip() is None
 for n,p in entries.items():assert z.read(n)==p.read_bytes()
 count=len(z.namelist());assert count==len(entries)+1
with tempfile.TemporaryDirectory(prefix='reader_v22_',dir=os.environ['TMPDIR']) as td:
 with ZipFile(dest) as z:z.extractall(td)
 with sync_playwright() as p:
  b=p.chromium.launch(channel='chrome',headless=True);q=b.new_page(viewport={'width':390,'height':844},accept_downloads=True);errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
  q.goto((Path(td)/'ebook_review_v22.html').as_uri());q.evaluate('document.fonts.ready');q.locator('#term-search').fill('SRM');assert q.locator('.index-table tbody tr:visible').count()==1;q.locator('#term-clear').click();assert q.locator('.index-table tbody tr:visible').count()==36
  fig=q.locator('figure[data-figure="winner_effect.svg"] svg');fig.scroll_into_view_if_needed();before=q.evaluate('scrollY');fig.click();q.wait_for_selector('dialog[open]');q.keyboard.press('Escape');q.wait_for_timeout(40);assert abs(q.evaluate('scrollY')-before)<1
  q.goto((Path(td)/'MINIMUM_RECORD.html').as_uri());q.locator('#r1').fill('압축 해제 후 작성 확인')
  with q.expect_download() as dl:q.locator('#record-export').click()
  assert '압축 해제 후 작성 확인' in Path(dl.value.path()).read_text(encoding='utf-8-sig');assert not errors;assert not q.evaluate('document.documentElement.scrollWidth>innerWidth');b.close()
report={'status':'passed','archive':dest.relative_to(R).as_posix(),'file_count':count,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'exact_entry_bytes':'passed','extracted_search_svg_click_return_and_download':'passed','worksheet_pdf_pages':1,'full_reproduction_environment':False,'actual_reader_test':False,'human_approval':False}
(O/'package_smoke_v22.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2))
