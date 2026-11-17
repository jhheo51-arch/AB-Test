# A/B Test

## 최신 통합 안내
- **[지금까지의 프로젝트 통합 정리](PROJECT_SUMMARY.md)**: 결정·산출물·실제/합성 자료·시장 비평·남은 일.
- **[자동 확인 상태](PROJECT_STATUS.json)**: 실제 파일·DB·PDF 확인 시점과 수치.
- **[제품 방향 문서](tool/README.md)**: 별도 tool/ 경로, 현재 구현되지 않은 제품 설계.
- **[제작 체크리스트](e-book/planning/PROGRESS.md)**: 출간 완료와 제작 중 구분.

최신 전체 읽기본은 **[v0.5 본책 PDF](e-book/exports/v05/ebook_review_v05.pdf)**입니다. 트리아타시스를 중심에 놓고 TRI-V의 정화, 해체와 입체화, 언어의 전환을 앞부분1~4장에서 설명한29쪽 개정본입니다. 여섯 사례와 마지막 판단까지 같은 방법론으로 연결했습니다. 문단별 소제목과 강제 쪽나눔을 줄이고 가운데 점을 제거했습니다. [v0.5 편집 원고](e-book/exports/v05/ebook_review_v05.md)도 제공합니다. 기존 워크북과 카드 참조편은 v0.4 자료를 보존하며 이번 윤문 대상이 아닙니다. 판매 승인본이나 일반 분석 앱은 아닙니다.

저자: **허재혁**. CRM A/B 테스트 학습·전자책·합성 데이터 프로젝트.
GitHub 주소용 이름은 `AB-Test`, 프로젝트 표시명은 **A/B Test**입니다.

## 구조
```text
e-book/
  virtual-company/   # JH Motors 기업·여정·운영 가정
  virtual-data/      # v01 기본 / v02 오류·무효과 / v03 표본·기간 설계
  planning/          # 제작 방향·진행 체크리스트
  manuscript/        # 원고·저자 서사·승리 근거 (전권 재편집 중)
  workflow/          # 진단 명세·60개 카드
  exports/           # 시각화 HTML·SVG·시작 원고 PDF
  workbook/          # 실험 계약·증거·보고서와 합성 답안
  design/cover/      # 표지 (제작 전)
  references/        # 공개자료·시장·방법·도구 조사 (권리 검수 미완료)
scripts/             # 생성·계획·분석·시뮬레이션·조판·검사
tool/                # 제품 방향·페르소나·비교·출처, 구현 전
```

## 합성 데이터
가상 기업 작업명은 **JH Motors**입니다. 사용자 요청의 JH를 반영한 임시 제안이며 상표·실제 기업 관련성을 확인하지 않았습니다. 실제 OEM 성과·고객·시장 수치가 아닙니다.
- `e-book/virtual-data/v01/data`: 기본 SQLite DB·CSV·생성 명세·검사 결과
- `e-book/virtual-data/v02`: 기본 비교·효과 없음·배정 기록 오류·선택적 이벤트 누락의 독립 시나리오
- `e-book/virtual-data/v02/instructor`: 교육자 정답지·원본 대조 자료
- `e-book/virtual-data/DATA_DICTIONARY.md`: 기본 스키마 설명

시나리오별 고객 ID는 중복될 수 있으므로 서로 합치지 않습니다. 오류 데이터는 의도적으로 잘못되어 있으며 의사결정에 사용하면 안 됩니다. 일부 비율 계산·표본 계획은 코드로 대조했지만, 모든 분석 조건·현장 타당성·외부 전문가 검수까지 완료한 것은 아닙니다.

## 이전 v01/v02 데이터 생성
아래 기본 생성 경로는 Python 표준 라이브러리만 사용합니다. 당시 생성 환경 Python 3.14.7. 최신 v0.3 계획·분석·출력에는 별도 의존성이 있으며 [v0.3 실행 안내](e-book/virtual-data/v03/README.md)를 따릅니다.
```sh
python scripts/build_db.py
python scripts/prepare_scenarios_v02.py
```
기존 출력이 있으면 덮어쓰지 않습니다. 완전 재생성은 출력 폴더를 백업한 별도 작업 사본에서 수행하세요. 생성용 하위 스크립트의 출력 위치는 `OEM_OUTPUT_ROOT`로 제어할 수 있습니다. 저장소 루트의 scripts가 기준이며, 시나리오 안의 scripts는 생성 당시 보조 사본입니다.

## 현재 상태
전체 읽기본은 v0.5입니다. 원래 방법론 파일을 다시 읽고 본문을 연속 서술로 재집필했습니다. 기본 기업과 DB는 v0.3, 별도 실습은 v0.4 그대로이며 새 통계 결과를 만든 것은 아닙니다. 기존 판은 보존하고 최종 저자 승인과 외부 검토, 실독자 테스트, 권리와 출간 검수는 남아 있습니다.

## 최신 본책 v0.5

방법론1~4장은3,6,7,8쪽에서 시작합니다. 여섯 사례는13,15,16,18,20,22쪽에서 시작합니다. 새 PDF에서 가운데 점0개, 문단별 세부 소제목0개, 여섯 사례와 방법론 명칭, 한글과 책갈피, 링크와 페이지 경계를 확인했습니다. 말투와 저자 표현의 최종 확인은 사람에게 남깁니다. 검사는 `e-book/exports/v05/validation_v05.json`, 집필 기준은 `e-book/planning/AUTHOR_METHOD_AND_VOICE.md`에 기록했습니다.

## 이전 통합 검토본과 보조자료 v0.4
- `e-book/exports/v04/ebook_review_v04.pdf`: 54쪽 본책. 6장 승리 층위, 7장 통계·사업 기준·가드레일, 8장 여섯 완결 사례, 9장 판단 기록.
- `e-book/exports/v04/workbook_v04.pdf`: 17쪽 작성·답안 자료.
- `e-book/exports/v04/diagnostic_cards_reference_v04.pdf`: 기존 v0.2 카드60개를 분리한60쪽 참조편. 새로 모든 카드를 실증한 것은 아님.
- 같은 폴더의 HTML·MD, `validation_v04.json`·`READER_KIT_README.md`를 제공합니다.
- `e-book/analysis/winner_v04`: 원본 재대조·고객별 탐색 손익·측정 역전·사전 집단/층화 효과·공유 용량 민감도 계산과 CSV.
- 재현 순서는 본책 부록과 패키지 안내를 따릅니다. 고정 합성 가정 아래의 구현·제작 검사이지 실제 OEM 성과나 사람의 최종 검토가 아닙니다.

## 최신 데이터·대표 장 v0.3
- `e-book/virtual-company/JH_Motors_v03.md`: 적격 모집단·세 정책·지표별 정보량을 반영한 가상 기업 개정.
- `e-book/virtual-data/v03`: 고객 120,000명, 적격 배정 65,559명. A/B/H 정책, 28일 완료·철회와 180일 계약, 조기 관측 스냅샷.
- `e-book/exports/v03/sample_and_data_chapter_v03.pdf`: 7쪽 대표 장. 전체 전자책의 최종 개정본은 아님.
- `e-book/virtual-data/v03/RESULTS.md`: 표본 계획·보정된 주분석·지표별 정보량.
- 실제 OEM 자료는 맥락·출처로 분리. 합성 전환율·개인 고객 수치가 실제 자료에서 추정됐다고 주장하지 않음.
- 기존 v0.2와는 모형도 다른 새 실험. 두 버전의 유의성을 비교해 표본 수만의 효과라고 해석하지 않음. 동일 모형의 별도 반복 표본 점검을 제공.

## 이전 저자 검토본 v0.2
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
