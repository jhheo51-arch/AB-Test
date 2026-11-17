# A/B Test

저자: **허재혁**. CRM A/B 테스트 학습·전자책·합성 데이터 프로젝트.
GitHub 주소용 이름은 `AB-Test`, 프로젝트 표시명은 **A/B Test**입니다.

## 구조
```text
e-book/
  virtual-company/   # JH Motors 기업·여정·운영 가정
  virtual-data/      # 데이터 사전, v01 기본 DB, v02 실습 시나리오
  planning/          # 제작 방향·진행 체크리스트
  manuscript/        # 시작 원고 v0.1 (전체 집필 미완료)
  workflow/          # 진단 명세·60개 카드
  exports/           # 시각화 HTML·SVG·시작 원고 PDF
  workbook/          # 독자 양식 (제작 전)
  design/cover/      # 표지 (제작 전)
  references/        # 참고문헌·권리 기록 (정리 전)
scripts/             # 데이터 생성·검증 코드
```

## 합성 데이터
가상 기업 작업명은 **JH Motors**입니다. 사용자 요청의 JH를 반영한 임시 제안이며 상표·실제 기업 관련성을 확인하지 않았습니다. 실제 OEM 성과·고객·시장 수치가 아닙니다.
- `e-book/virtual-data/v01/data`: 기본 SQLite DB·CSV·생성 명세·검사 결과
- `e-book/virtual-data/v02`: 기본 비교·효과 없음·배정 기록 오류·선택적 이벤트 누락의 독립 시나리오
- `e-book/virtual-data/v02/instructor`: 교육자 정답지·원본 대조 자료
- `e-book/virtual-data/DATA_DICTIONARY.md`: 기본 스키마 설명

시나리오별 고객 ID는 중복될 수 있으므로 서로 합치지 않습니다. 오류 데이터는 의도적으로 잘못되어 있으며 의사결정에 사용하면 안 됩니다. 통계적 주효과·검정력·현장 타당성 검증은 아직 미완료입니다.

## 재현
Python 표준 라이브러리만 사용합니다. 생성 환경 Python 3.14.7.
```sh
python scripts/build_db.py
python scripts/prepare_scenarios_v02.py
```
기존 출력이 있으면 덮어쓰지 않습니다. 완전 재생성은 출력 폴더를 백업한 별도 작업 사본에서 수행하세요. 생성용 하위 스크립트의 출력 위치는 `OEM_OUTPUT_ROOT`로 제어할 수 있습니다. 저장소 루트의 scripts가 기준이며, 시나리오 안의 scripts는 생성 당시 보조 사본입니다.

## 현재 상태
최신 v0.2는 76쪽 저자 검토본, 60개 시각 진단 카드, 독립 라이브러리로 대조한 비율 분석과 워크북을 포함합니다. 최종 저자 승인·외부 통계/OEM 검토·실독자 테스트·권리·출간 검수는 미완료입니다.

## 최신 저자 검토본 v0.2
- `e-book/exports/v02/ebook_review_v02.pdf`: 본문·도식 16쪽 + 독립 참조 카드 60쪽, 총 76쪽.
- `e-book/exports/v02/diagnostic_atlas_v02.html`: 60개 반론·증거 카드, 실제 계산·판단 흐름 탭.
- `e-book/workbook/workbook_v02.md`: 실험 계약·증거 장부·한 장 보고서 양식과 합성 답안.
- `e-book/manuscript/author_story_v02.md`: 제공된 경력에 기초한 저자 서사, 최종 저자 확인 전.
- `e-book/analysis/v02/verified_analysis.json`: 비율 검정·Newcombe 구간·별도 표본 계획 예. 자체 수식과 statsmodels 및 원본 SQL 대조.
- 검증 한계·권리·외부 검토 상태는 `e-book/design/v02/REVIEW.md` 참고. 기존 v0.1은 보존.

## 이전 읽기·시각화 v0.1
- `e-book/exports/workflow_explorer_v01.html`: G0~G8 단계 선택, 60개 카드 검색·필터, JH Motors/현대자동차/기아 맥락 설명.
- `e-book/exports/reading_draft_v01.pdf`: 프롤로그·본문 6장·워크북 질문·60개 진단 카드의 시작 원고.
- `e-book/exports/reading_draft_v01.html`: 웹 읽기본. PDF 도식은 인쇄 크기 확대, 일부 페이지의 여백은 후속 조정 필요.
- `scripts/build_reading_artifacts.py`: Markdown 패키지 필요. HTML·SVG 생성.
- `scripts/render_and_test_artifacts.py`: Playwright와 설치된 Chromium 필요. 상호작용 검사·PDF 출력.
- `scripts/verify_reader_pdf.py`: PyMuPDF·Pillow 필요. PDF 텍스트·페이지 경계·연락 시트 검사.
데이터 생성 코드는 표준 라이브러리만 사용하지만 읽기용 아티팩트 빌드는 별도 의존성이 있습니다.
계획 문서에 남은 과거 로컬 경로보다 이 README의 폴더 구조를 우선합니다. 과거 체크 표시는 당시 범위의 결과이며 새 검증 완료를 뜻하지 않습니다.

## 권리·공개
초안은 비공개로 관리합니다. 공개 라이선스는 아직 부여하지 않았습니다. 개인정보·인증정보·권한 없는 원문·실제 OEM 로고를 커밋하지 않습니다.
