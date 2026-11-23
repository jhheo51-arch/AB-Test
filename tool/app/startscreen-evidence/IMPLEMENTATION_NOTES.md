# 시작 화면 사례 버튼과 R08 입력 소유권의 최종 통합

현재 기준은 `ff6d463adbafa5b5525204ab9bc3adb6a8f10465`입니다. [현재 기준 장부](BASELINE.json)는 부모가 보존한 a0의 Git blob 검증 장부와 a0→ff 공개 변경 목록의 실제 SHA-1 blob 바이트를 결합했습니다. 엔진·project-schema·rollout·index·스타일과 기존 자산은 ff 기준으로 보존하며 수학은 수정하지 않았습니다.

이전 a0 검증은 [이전 통합 기록](../integration-evidence/IMPLEMENTATION_NOTES.md), 부모가 보존한 로컬 커밋 `99736c9` 및 활성 scratch의 충돌 전 스냅샷에서 확인할 수 있습니다. 288 기준 최초 R08과 a0 기준 보고서를 현재 ff 검사로 바꿔 쓰지 않습니다. 현재 실제 검사 수·해시·저장 형식은 상위 verification/STATUS가 새 실행 장부에서 생성합니다.

## 네 충돌과 보존 범위

`tool/README.md`, `app/app.js`, `app/tests/rebuild_package.py`, `downloads/README.md`의 내용을 결합했습니다. 공개된 시작 화면의 세 사례 버튼, 실제 프로젝트 JSON fetch, 서버의 예제 경로와 새 upstream 검사를 보존했습니다. 최신 검증 ZIP과 기존 공개 Release 링크도 구분해 유지했습니다. R08의 CSV 원자적 검증·확대 판단 초기화·Windows 실행기·STATUS 자동 동기화와 배포 허용목록도 남겼습니다. Git index/rebase 계속/게시 작업은 부모의 범위이며 이 작업자는 수행하지 않았습니다.

## 재현과 최소 수정

[수정 전 실제 fetch 검사](ASYNC_BASELINE.json)에서 늦게 도착한 사례가 나중 CSV/조건 편집에 적용되는 경계, 새 파일 읽기 중 옛 사례가 끼어드는 경계, 이전 파일 완료가 나중 사례를 지우는 경계가 실패했습니다. 새 프로젝트 복원과 재클릭 취소 등 이미 보호된 경로도 그대로 기록했습니다.

예제 로드를 공통 입력 epoch의 작업으로 등록하고, 기존 입력 취소가 fetch AbortController도 정리하게 했습니다. fetch/text await 후 적용과 finally의 제어 복구는 현재 소유 ticket만 수행합니다. 나중 CSV/프로젝트/조건 편집은 이전 fetch를 취소하며, 나중 사례 선택은 이전 파일/사례 처리를 취소합니다. CSV 크기/UTF-8/문법 실패 시 기존 데이터와 확대 판단을 보존하는 기존 스테이징은 변경하지 않았습니다.

[현재 fetch 소유권 검사](BROWSER_VERIFICATION.json)는 실제 localhost GET과 실제 응답 text를 먼저 읽고 완료 시점만 지연합니다. 가짜 성공 JSON/해시/Worker 응답을 만들지 않았습니다. [기존 결합 검사 재실행](COMBINED_VERIFICATION.json)과 upstream의 1440/375px 세 버튼·저장·보고서 검사를 함께 실행합니다. 두 viewport 흐름 그룹은 개별 단언 수가 아닙니다. source/ZIP의 반복 실행을 고유 검사에 더하지 않습니다.

## 산출물과 한계

명시 허용목록의 최신 ZIP을 만들고 CRC·모든 멤버의 소스 바이트를 대조한 뒤, 한글/공백 경로의 새 추출본에서 같은 전체 회귀를 실행합니다. 제공된 세 schema 8 프로젝트는 upstream 바이트를 유지합니다. CSV/계획만 저장할 때의 schema 7과 형식 2–8 읽기, 160.16초 영상·글꼴, 기존 입력 상한과 개인정보 경계도 유지합니다.

실제 모델 호출과 사람 관찰은 0건입니다. 실제 스크린리더 음성·네이티브 파일 창·다른 OS·실제 약한 기기의 검증은 하지 않았습니다. 이전 CSS 초협폭 추가 스트레스 한계를 해결했다고 주장하지 않습니다. 이번 작업은 이미 공개된 UI의 통합·소유권 수정·회귀/배포 검사이며 새 통계나 UX 재설계가 아닙니다.
