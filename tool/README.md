# CRM A/B 테스트 도구

## 현재 진입점

- **[작업실 v0.5.1 실행법·지원 범위](workspace/v051/README.md)** — 열 연결 → 결과 요약 → 판단 작성.
- **[앞으로 남은 과제](ROADMAP.md)** — 제안 우선순위, 근거, 완료 기준과 제외 범위.
- [검증된 ZIP](releases/v051/README.md), [v0.5.1 검증 요약](workspace/v051/VERIFICATION_v051.json).
- [제품 기획 기준안](prd/v01/PRD_BASELINE_v02.md), [문답](prd/v01/INTERVIEW.md), [합의](prd/v01/DECISIONS.md).

CRM 전체 관리·발송기가 아니라 **CRM A/B 테스트 설계·분석·판단 전문 도구**입니다. 외부에서 실험하고 기기 안에서 입력·계산·판단 기록을 연결합니다. 고객 원자료를 GitHub나 설명 서버에 올리는 도구가 아닙니다.

## 현재 구현과 목표

직접 열 연결·명시적 A/B 값 변환, 검증된 이항 계산, 요약 우선 결과와 중립 카드, 판단 작성 발판, 계획·집계 저장/복원, HTML/PDF 공유와 동의 후 실제 LLM 설명을 구현했습니다. 자유로운 상황 설명 → 목적 → 후보 → 계획 추천의 전체 설계 대화는 목표이며 현재는 규칙 기반 안내입니다.

v0.5의 새 흐름 37개, 기존 흐름 43개(실제 모델 포함), 이전 네 문제 회귀 22개, 맥락 19개, 열 연결 모듈 12개, 스키마 27개 그룹을 통과했습니다. 새 ZIP도 별도 추출해 새 흐름 37개를 재실행했습니다. 서로 관련된 검사를 독립 사용자 수로 합산하지 않습니다. 실제 실무자의 사용성·성과, 전체 접근성·보안 인증을 뜻하지 않습니다.

## 보존한 이력

- [v0.4.1 실행 스냅샷](workspace/v041/README.md) — 수정 전 기준 보존.
- [v0.4.1 재평가](reviews/v041_reevaluation/REVIEW.md) — v0.5 개선의 근거. 당시 문제와 현재 상태를 구분하세요.
- [v0.4 추가 감사](reviews/v04_audit/AUDIT_REVIEW.md), [v0.5에서도 실행한 최신성 회귀](workspace/v05/FIX_REGRESSION_v041.json).
- [v0.3 가상 페르소나](reviews/v03_personas/PERSONA_REVIEW.md).

FRAMEWORK_v02·DIRECTION·PERSONA_REVIEW·BENCHMARK·SOURCES는 초기 방향/평가입니다. 그 안의 미구현·미확정은 작성 당시 상태이며 현재 실행 상태는 v0.5.1 문서를 우선합니다. 초기 초안, 이전 버전, 전자책·영상 원본은 보존합니다. 공개 배포·Pages는 켜지 않습니다.

## 안정화와 다음 단계

R01~R03은 [v0.5.1](workspace/v051/README.md)에서 구현·회귀 확인했습니다. [실제 사용자 과업 자료](user-review/v051/README.md)는 준비됐지만 참여자·관찰은 아직 없습니다. [진행 상태](REVIEW_STATUS.json)를 확인하세요. 설계 진입은 실제 관찰 후 구현하며 AI 모의 응답으로 검토를 완료하지 않습니다. [v0.5 원본](workspace/v05/README.md)은 그대로 보존합니다.
