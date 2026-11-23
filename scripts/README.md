# 최신 전자책 확인과 로컬 제작 코드

저장소 루트에서 실행합니다.

```bash
python scripts/check_latest_ebook.py
python scripts/refresh_project_status.py
```

`check_latest_ebook.py`는 현재 e-book/manifest.json에 선언된 최신 파일의 SHA-256과 문서의 로컬 링크를 검사합니다. 이전 판 폴더나 통계 라이브러리에 의존하지 않고 Python 표준 라이브러리로 실행합니다. `refresh_project_status.py`는 이 검사를 통과한 뒤 PROJECT_STATUS.json을 갱신합니다. 검증 시각 갱신을 기존 통계와 브라우저 검사의 재실행으로 표시하지 않습니다.

나머지 버전별 제작, 교정 및 분석 스크립트는 로컬 보존용 개발 이력입니다. GitHub에서 제외한 이전 원고, 데이터와 동결 입력을 전제로 하므로 새 clone에서 바로 실행하거나 최신본을 덮어쓰는 일반 명령으로 사용하지 않습니다. 재조판이 필요하면 보존된 로컬 자료의 별도 작업 사본에서 진행합니다. 기존 감사 기록의 원문과 당시 실행 결과는 로컬 백업에 그대로 있습니다.
