# CRM A/B 테스트 도구

## 현재 진입점

- **[실행 가능한 작업실 v0.4.1](workspace/v041/README.md)** — 실행법, 지원 범위, 네 최신성·저장 문제 수정, 검증과 남은 일.
- [제품 기획 기준안](prd/v01/PRD_BASELINE_v02.md), [문답/위임 기록](prd/v01/INTERVIEW.md), [합의](prd/v01/DECISIONS.md).
- [v0.3 가상 페르소나 검토](reviews/v03_personas/PERSONA_REVIEW.md).
- [v0.4 추가 감사](reviews/v04_audit/AUDIT_REVIEW.md), [v0.4.1 수정 회귀](workspace/v041/FIX_REGRESSION_v041.json).

CRM 전체 관리·발송기가 아니라 **CRM A/B 테스트 설계·분석·판단 전문 도구**입니다. 외부에서 실험하고 로컬에서 입력·계산·판단 기록을 연결합니다. 고객 원자료를 GitHub나 설명 서버로 올리는 도구가 아닙니다.

## 구현과 목표를 구분합니다

CSV/표 입력, 실제 이항 계산, 결과/집단 설명, 계획·집계 저장/복원, HTML/PDF 공유와 동의 후 실제 LLM 설명을 구현·검사했습니다. 자유로운 상황 설명 → 목적 → 후보 → 계획 추천의 전체 대화는 제품 목표이며 현재는 규칙 기반 안내입니다. 모든 세그먼트 수·설계·지표를 지원하지 않습니다. 실제 사용자의 효용·전체 보안·통계 전 범위의 검증 완료가 아닙니다.

현재 검증은 전체 브라우저 43개, 수정 회귀 22개, 스키마 22개 그룹과 별도 수치 기준·PDF를 포함합니다. 정확한 범위와 최초 실패·미완료는 작업실 README와 결과 JSON을 보세요. 원 감사의 실패 기록을 수정판의 현재 실패로 오인하거나, 수정판 PASS를 모든 문제 해결로 확대하지 않습니다.

## 이전 방향성 기록

[FRAMEWORK_v02.md](FRAMEWORK_v02.md), [DIRECTION.md](DIRECTION.md), [PERSONA_REVIEW.md](PERSONA_REVIEW.md), [BENCHMARK.md](BENCHMARK.md), [SOURCES.md](SOURCES.md)는 초기 방향·평가 자료입니다. 그 문서의 ‘미구현/미확정’은 작성 당시 상태입니다. 현재 실행 상태는 위 v0.4.1을 우선합니다. 기존 초안과 전자책은 삭제·덮어쓰지 않았습니다.
