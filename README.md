# A/B Test

CRM A/B 테스트의 설계, 결과 해석, 적용 결정을 연습하는 비공개 프로젝트입니다. 전자책 저자는 허재혁입니다.

| 작업 | 현재 자료 |
| --- | --- |
| 전자책 v0.19 | [PDF 95쪽](e-book/exports/v19/ebook_review_v19.pdf), [웹 읽기본](e-book/exports/v19/ebook_review_v19.html), [다운로드 ZIP](e-book/packages/JH_CRM_ebook_reader_v19.zip) |
| 전자책 편집과 검수 | [반영 내역](e-book/design/v19/DEVELOPMENT.md), [제출 준비도](e-book/design/v19/SUBMISSION_READINESS.md), [자동 확인 상태](PROJECT_STATUS.json) |
| 합성 데이터와 실습 | [데이터와 실습 안내](e-book/README.md), [표본 설계 예제](e-book/learning-materials/sample-and-data/sample_and_data_chapter_v03.pdf), [워크북](e-book/learning-materials/workbook-and-cards/workbook_v04.pdf) |
| A/B 실험노트 영상 제작 | [대본부터 렌더링까지](video-production/README.md), [11화 추가 예제](video-production/README.md#새-회차-만들기-예시-11화) |
| A/B 테스트 도구 설계 | [최신 PRD와 합의](tool/prd/v01/README.md) |

## 폴더 구조

- `e-book/exports/v19/`에는 현재 읽기본, 원고, 작성 양식과 검증 기록이 있습니다.
- `e-book/packages/`에는 현재 읽기본 ZIP이 있습니다.
- `e-book/build-inputs/`에는 현재 읽기본 생성과 변경 검증에 쓰는 동결 입력이 있습니다.
- `e-book/learning-materials/`에는 독립 실습 장, 워크북과 진단 카드가 있습니다.
- `e-book/virtual-data/`와 `e-book/analysis/`에는 교육용 합성 데이터와 결과 계산 근거가 있습니다.
- `scripts/`에는 전자책과 데이터의 생성 및 검증 코드가 있습니다. [현재 실행 순서](scripts/README.md)
- `video-production/`에는 영상의 대본, 도표와 렌더링 코드가 있습니다. 완성 영상은 기존 비공개 Drive에서 관리합니다.
- `tool/`에는 구현 전 제품 기획 문서가 있습니다.

## 이전 판과 현재 상태

이전 판의 배포본, 검수 이미지와 당시 실행 코드는 [정리 직전 Git 기록](https://github.com/jhheo51-arch/AB-Test/tree/c8cd72253f4b11131f71405e0ab4d26b3f0b46b0)에서 열 수 있습니다. 재생성에 필요한 이전 원고와 그림은 `build-inputs/`에 보존합니다.

v0.19는 저자 검토본입니다. 사람의 통계 및 편집 검수, 실제 독자 수행시험, 권리 및 제출처 요건 검토는 남아 있습니다. [프로젝트 요약](PROJECT_SUMMARY.md)
