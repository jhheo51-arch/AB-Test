# 개인정보·보고서·입력 계약 읽기 전용 감사

## 결과
- **재현 결함 / 중간 — PC-01:** 저장과 복원 조건이 달라 자체 생성 프로젝트 복원이 실패한다. 정상 파싱된 201자 집단명, 7개 집단/14셀, 군별 200001명 사례 모두 저장 객체를 생성할 수 있지만 복원에서 거절했다. `app.js:34,36,48`, `engine.js:103-128,229-238`.
- **검증 간극 / 낮음 — PC-02:** 서버 `issues`는 알려진 코드 목록이 아니라 정규식만 검사한다. 개인정보처럼 생긴 합성 식별자 두 개가 `validate_facts`를 통과했다. `raw_data_sent:false`는 모든 클라이언트 입력에 대한 비식별 보증이 아니라 정상 앱 생성 경로에 의존한다. **실제 전송·모델 호출·외부 공격은 재현하지 않았다.** `server.py:25,93-100`.
- **정적 관찰 / 참고 — PC-03:** 저장한 `source_digest`는 복원하지 않는다. 재준비 시 집계 CSV의 해시로 바뀐다. 원천 계보 보존의 한계이며, 원자료 검증 인증 우회라고 단정하지 않는다. `app.js:14,22,34,36`.

## 확인된 통제
- 새 audience/정책/목적 등 자유서술과 원래 집단명은 `explanationFacts()`에 들어가지 않았다. 서버는 추가 자유서술 필드도 거절했다.
- 집단 공유 제외 시 생성 보고서 문자열에 집단명·집단 설명 카드·검사한 집단 p값이 남지 않았다. 포함 케이스에는 집단명이 나타났다. 비교 가족의 G1/G2 식별자는 계약상 유지되며 상세 수치와 구별한다.
- 직접 적은 audience/정책/목적은 공유되지만 UI에 경고가 실제로 있다. 이 의도된 동작은 버그로 세지 않았다. 합성 `<img>` 입력은 이스케이프됐다.
- loopback/Host/Origin/confirmed/facts 제한은 소스로 확인했다. 실제 서버 요청은 하지 않았다.

## 증거와 범위
- `privacy_contract_evidence.json`: 실행 결과 및 읽은 7개 소스의 전후 SHA256 일치.
- `privacy_contract_findings.json`: 각 항목의 위치·방법·범위·심각도·한계.
- 재현: `python C:/Users/Administrator/Downloads/AB_Test_Workspace_v04_Audit/static/privacy_contract_probe.py`
- Node 격리 VM과 Python AST로 순수 함수/파일 처리만 실행. 실제 다운로드·브라우저 DOM·PDF·CLI가 추가하는 문맥·provider payload는 검증하지 않았다. 모델 실호출·원자료 전송·credentials 접근 없음. 앱·기존 테스트·ZIP 수정 없음.
