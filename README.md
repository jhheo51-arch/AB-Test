# A/B Test

CRM A/B 테스트의 설계·분석·판단을 돕는 공개 프로젝트입니다. 전자책 저자는 허재혁입니다.

| 작업 | 진입점 |
| --- | --- |
| 전자책 최신본 | [안내](e-book/README.md), [PDF 97쪽](e-book/ebook.pdf), [웹 읽기본](e-book/ebook.html), [원고](e-book/ebook.md) |
| 판단 기록 | [웹 양식](e-book/record.html), [작성 예시](e-book/record-example.md) |
| CRM A/B 테스트 도구 | [현재 앱](tool/app/README.md), [최신 다운로드](tool/downloads/README.md), [시연 영상](tool/app/help/walkthrough.mp4), [제품 합의](tool/prd/README.md), [남은 과제](tool/ROADMAP.md) |
| A/B 실험노트 영상 | [제작 안내](video-production/README.md) |

## 처음 방문하셨나요?

- **책 읽기:** [전자책 PDF](e-book/ebook.pdf) 또는 [웹 읽기본 HTML](e-book/ebook.html)을 내려받으세요. HTML은 `e-book/assets/`도 함께 같은 상대 위치에 둡니다. GitHub 파일 페이지는 앱이나 HTML 실행 화면이 아닙니다.
- **도구 사용하기:** [최신 ZIP](tool/downloads/AB_Test_Workspace.zip)을 내려받아 압축을 풀고 `launch.cmd`를 실행하세요. Windows와 Python 3가 필요합니다. 실행 창에 표시된 로컬 주소를 Chrome/Edge에서 엽니다. [실행 안내](tool/app/README.md)
- **사용법 보기:** [시연 영상 MP4](tool/app/help/walkthrough.mp4)를 내려받거나, 실행한 앱의 **시연 영상 보기**를 누르세요. GitHub에서 바로 재생되지 않으면 파일 페이지의 다운로드 버튼을 이용하세요.

기본 CSV 확인·통계 계산은 LLM 없이 사용할 수 있습니다. 선택 기능인 LLM 설명에는 별도의 Hermes 설치·프로필·모델 인증 설정이 필요하며, 연결 설정과 이용 비용은 사용자 환경에 따릅니다. 자유로운 자연어 설계 대화는 아직 제공하지 않습니다.

## 보관 원칙

- 전자책은 GitHub 현재 트리에 버전 표시 없는 최신본 한 세트만 둡니다.
- 이전 판과 제작 입력, 원자료 및 감사 기록은 로컬에 보존하고 Git 추적에서 제외합니다. 기존 Git 커밋 이력은 지우거나 재작성하지 않습니다.
- 본문은 재개발하지 않고 실제 오류와 읽기 장애만 최소 수정합니다. 출판과 판매는 진행하지 않습니다.
- 전자책 사례는 교육용 합성 자료입니다. AI 검수 및 자동 검사와 실제 독자시험 또는 현장 효용은 다릅니다.
- 도구는 실험 한 건의 설계와 분석을 다룹니다. 고객 DB 관리나 실제 발송 및 범용 CRM 플랫폼으로 확장하지 않습니다.

## 이용 조건

저장소 공개는 프로젝트 전체에 오픈소스 라이선스를 부여한다는 뜻이 아닙니다. 재사용·수정·재배포 전 자료별 이용 조건을 확인하세요. 포함된 글꼴·라이브러리에는 각각의 라이선스 고지가 적용됩니다. 프로젝트 전체의 별도 라이선스는 아직 지정하지 않았습니다.

## 확인 명령

```bash
python scripts/check_latest_ebook.py
python scripts/refresh_project_status.py
```

첫 명령은 최신본 해시와 상대 링크를 검사하고 두 번째는 그 결과로 [현재 상태](PROJECT_STATUS.json)를 갱신합니다. 이전 제작 스크립트는 로컬 보관 입력이 필요하므로 새 clone에서 바로 재생성할 수 있다고 가정하지 않습니다. [실행 범위](scripts/README.md), [프로젝트 요약](PROJECT_SUMMARY.md)
