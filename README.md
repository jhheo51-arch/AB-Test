# A/B Test

CRM A/B 테스트를 설계하고 분석하며 적용 범위와 다음 행동을 판단하는 비공개 프로젝트입니다. 전자책 저자는 허재혁입니다.

| 작업 | 진입점 |
| --- | --- |
| 전자책 최신본 | [안내](e-book/README.md), [PDF 97쪽](e-book/ebook.pdf), [웹 읽기본](e-book/ebook.html), [원고](e-book/ebook.md) |
| 판단 기록 | [웹 양식](e-book/record.html), [작성 예시](e-book/record-example.md) |
| CRM A/B 테스트 도구 | [현재 앱](tool/app/README.md), [최신 다운로드](tool/downloads/README.md), [시연 영상](tool/app/help/walkthrough.mp4), [제품 합의](tool/prd/README.md), [남은 과제](tool/ROADMAP.md) |
| A/B 실험노트 영상 | [제작 안내](video-production/README.md) |

## 보관 원칙

- 전자책은 GitHub 현재 트리에 버전 표시 없는 최신본 한 세트만 둡니다.
- 이전 판과 제작 입력, 원자료 및 감사 기록은 로컬에 보존하고 Git 추적에서 제외합니다. 기존 Git 커밋 이력은 지우거나 재작성하지 않습니다.
- 본문은 재개발하지 않고 실제 오류와 읽기 장애만 최소 수정합니다. 출판과 판매는 진행하지 않습니다.
- 전자책 사례는 교육용 합성 자료입니다. AI 검수 및 자동 검사와 실제 독자시험 또는 현장 효용은 다릅니다.
- 도구는 실험 한 건의 설계와 분석을 다룹니다. 고객 DB 관리나 실제 발송 및 범용 CRM 플랫폼으로 확장하지 않습니다.

## 확인 명령

```bash
python scripts/check_latest_ebook.py
python scripts/refresh_project_status.py
```

첫 명령은 최신본 해시와 상대 링크를 검사하고 두 번째는 그 결과로 [현재 상태](PROJECT_STATUS.json)를 갱신합니다. 이전 제작 스크립트는 로컬 보관 입력이 필요하므로 새 clone에서 바로 재생성할 수 있다고 가정하지 않습니다. [실행 범위](scripts/README.md), [프로젝트 요약](PROJECT_SUMMARY.md)
