"""Package actual v0.4 deliverables from an explicit allowlist, no OEM originals."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/exports/v04'
v=json.loads((OUT/'validation_v04.json').read_text(encoding='utf-8'))
pages={k:x['pages'] for k,x in v['outputs'].items()}
readme=f'''# v0.4 저자 검토 패키지

저자 허재혁. **출간·판매 승인본 아님.**

## 먼저 열 파일
- `e-book/exports/v04/ebook_review_v04.pdf`: {pages['ebook_review_v04']}쪽 전체 읽기본. 승리 층위·최소 사업 효과·가드레일과 여섯 완결 사례를 본문에 통합했다.
- `e-book/exports/v04/workbook_v04.pdf`: {pages['workbook_v04']}쪽 별도 작성·답안 자료.
- `e-book/exports/v04/diagnostic_cards_reference_v04.pdf`: {pages['diagnostic_cards_reference_v04']}쪽. 기존 v0.2의60개 카드를 분리한 참조편이다. 새 여섯 사례 검증이 모든 카드의 실증을 뜻하지 않는다.
- 같은 폴더의 `.html`은 웹 읽기본, `.md`는 검색·편집용 원고다. 카드 탐색 웹 화면은 저장소의 이전 v0.2 자료로 보존한다.

## 데이터와 재현
기본 v0.1·v0.3 SQLite DB, v0.3 계획, 새 측정/집단/용량 CSV·결과JSON·생성/분석/조판/출력 코드를 포함한다. 책의 재현 부록을 따른다. SQLite를 읽을 수 있는 도구 또는 제공 Python 코드로 확인한다. 의존성은 uv와 인터넷·설치된 Chrome이 필요하다. 같은 이름의 시나리오 고객을 서로 합치지 않는다.

모든 고객·확률·원가·효과는 교육용 가정이다. 실제 OEM 개인별 자료·로고·권리 미확인 원문은 포함하지 않는다. 원래 v0.1·v0.3 데이터는 유지하고 새 시나리오는 별도 폴더에 둔다.

## 확인 범위와 남은 일
계산·원장 집계·파일·여섯 사례·PDF 한글/목차/글꼴 삽입/페이지 경계·패키지 손상을 확인했다. 실제 검사 수치는validation_v04.json과 각 분석JSON을 따른다. 구현 대조는 외부 통계 검토가 아니다. 저자 최종 승인·실무/통계 검토·실제 독자 테스트·접근성·글꼴/인용/배포 권리·판매처 규격은 미완료다.
'''
(OUT/'READER_KIT_README.md').write_text(readme,encoding='utf-8')
files=[OUT/name for name in ['ebook_review_v04.pdf','ebook_review_v04.html','ebook_review_v04.md','winner_chapters_v04.md','workbook_v04.pdf','workbook_v04.html','workbook_v04.md','diagnostic_cards_reference_v04.pdf','winner_effect.svg','guardrail_effect.svg','build_manifest_v04.json','validation_v04.json','READER_KIT_README.md']]
files += [ROOT/'scripts'/name for name in ['analyze_winner_v04.py','build_winner_scenarios_v04.py','build_ebook_v04.py','render_verify_v04.py','package_reader_v04.py']]
files += [ROOT/p for p in ['e-book/virtual-data/v01/data/oem_crm.sqlite','e-book/virtual-data/v03/data/jh_motors_v03.sqlite','e-book/virtual-data/v03/experiment_plan.json','e-book/virtual-data/v03/analysis_report.json','e-book/virtual-data/v03/DATA_DICTIONARY.md','e-book/analysis/v02/verified_analysis.json','e-book/exports/v02/ebook_review_v02.md','e-book/exports/v02/ebook_review_v02.pdf','e-book/exports/v02/validation_v02.json','e-book/exports/v03/sample_and_data_chapter_v03.md','e-book/manuscript/author_story_v02.md','e-book/manuscript/winner_core_v04.md','e-book/manuscript/winner_decision_v04.md','e-book/manuscript/winner_cases_456_v04.md']]
files += [f for f in (ROOT/'e-book/analysis/winner_v04').rglob('*') if f.is_file()]
files=sorted(set(files));assert all(f.is_file() for f in files),[str(f) for f in files if not f.is_file()]
entries=[{'path':f.relative_to(ROOT).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
manifest={'version':'v0.4 author review','files':entries,'file_count_without_manifest':len(entries),'page_counts':pages,'rights':'Only original synthetic/author/reproducible artifacts; real OEM source originals excluded; font/commercial rights review pending'}
mp=OUT/'package_manifest_v04.json';mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
files.append(mp);dest=ROOT/'JH_CRM_ebook_reader_v04.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:z.write(f,f.relative_to(ROOT))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)==len(set(z.namelist()))
    for e in entries:assert hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256']
print(json.dumps({'zip':str(dest),'zip_bytes':dest.stat().st_size,'files':len(files),'page_counts':pages,'zip_integrity':'passed; all manifest hashes matched'},ensure_ascii=False,indent=2))
