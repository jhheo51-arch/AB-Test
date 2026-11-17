"""Package the private reader-review kit, excluding third-party raw sources."""
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/exports/v02'
readme='''# 허재혁 · CRM A/B 테스트 진단 플레이북 — 저자 검토본 v0.2

먼저 e-book/exports/v02/ebook_review_v02.pdf를 여세요.
시각 진단 카드는 같은 폴더의 diagnostic_atlas_v02.html을 브라우저로 여세요. HTML은 외부 라이브러리 없이 동작하고 ebook_review_v02.html로 연결됩니다.
워크북은 e-book/workbook/workbook_v02.md입니다. DB·CSV는 e-book/virtual-data/v01/data, 분석 결과는 e-book/analysis/v02에 있습니다.

제공된 경력에 근거한 저자 서사, 주지표/진단/가드레일 계산, 회의 반론, 60개 진단 카드를 포함합니다. 최종 출간 승인본·실제 OEM 성과 보고가 아닙니다.
모든 고객·비용·확률은 합성입니다. 실제 기업 로고·고객 원본·권리 미검토 OEM 원파일·공개 이메일 실험 원본은 포함하지 않았습니다.
자료는 사용자가 검토하는 비공개 작업 패키지입니다. 상업 배포 전 저자 승인·권리·실무/통계/독자 검수와 판매처 요건을 확인하세요.

분석 재현: uv run --with scipy --with statsmodels scripts/analyze_ebook_cases.py
HTML 재생성: Markdown 파이썬 패키지가 있는 환경에서 python scripts/build_ebook_v02.py
PDF·화면 검사: Playwright+설치된 Chromium+PyMuPDF+Pillow 환경에서 python scripts/render_verify_v02.py
분석의 실제 런타임 버전과 가정은 verified_analysis.json, 출력·화면 검사는 validation_v02.json을 확인하세요.
'''
(OUT/'READER_KIT_README.md').write_text(readme,encoding='utf-8')
files=[]
for folder in [OUT,ROOT/'e-book/analysis/v02',ROOT/'e-book/virtual-data/v01/data']:
    files.extend(f for f in folder.rglob('*') if f.is_file())
for rel in ['e-book/workbook/workbook_v02.md','e-book/manuscript/reading_draft_v01.md','e-book/manuscript/author_story_v02.md','e-book/manuscript/winner_evidence_v02.md','e-book/workflow/diagnostic_cards_v02.json','e-book/workflow/case_catalog_v01.csv','e-book/virtual-data/DATA_DICTIONARY.md','e-book/design/v02/REVIEW.md','scripts/analyze_ebook_cases.py','scripts/build_diagnostic_cards_v02.py','scripts/build_ebook_v02.py','scripts/render_verify_v02.py']:
    files.append(ROOT/rel)
files=sorted(set(files))
path=ROOT/'JH_CRM_ebook_reader_v02.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
    for file in files:z.write(file,file.relative_to(ROOT))
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    report={'package':str(path),'files':len(z.namelist()),'bytes':path.stat().st_size,'zip_integrity':'passed','third_party_raw_sources_included':False}
(OUT/'package_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
