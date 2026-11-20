# CRM A/B 테스트 도구 — 문답과 기획 기준안

## 현재 기준

[PRD_BASELINE_v02.md](PRD_BASELINE_v02.md)가 제품 정책 기준안입니다. Q01~Q10은 사용자 직접 답변, Q11~Q20은 사용자가 권장 방향 선택을 위임한 기록입니다. 개별 답변으로 위장하지 않습니다. [합의 기록](DECISIONS.md)과 [전체 인터뷰](INTERVIEW.md)를 함께 보세요.

CRM A/B 테스트 설계·분석·판단에 집중합니다. CRM 전체 운영·발송·수집은 제외합니다. 제품 목표 흐름은 **상황 설명 → 목적 확인 → A/B 후보 제안 → 지표·배정·판정 계획 추천 → 사용자 확인 → 결과 분석과 설명**입니다.

현재 실행본은 [작업실 v0.5.1](../../workspace/v051/README.md)입니다. CSV/표 → 검증된 계산 → 결과 → LLM 설명과 저장/공유를 구현했습니다. 자유로운 후보·계획 생성 대화까지 모두 완성된 것은 아닙니다. 기획에서 희망한 기능과 실제 제공 기능은 실행본 README에서 구분합니다.

## 문서 읽는 순서

1. [기준안 v0.2](PRD_BASELINE_v02.md): 직접 합의와 위임 선택, 초기 정책, 검증 게이트.
2. [DECISIONS.md](DECISIONS.md): 네 설계 원칙과 현재 합의.
3. [INTERVIEW.md](INTERVIEW.md): Q01~Q20의 발언/위임 구분.
4. [RESEARCH_REVIEW.md](RESEARCH_REVIEW.md): 당시 조사·가상 페르소나·공식 기능 비교.
5. [draft/index.html](draft/index.html): 문답 이전의 초기 HTML 문서. 제품 앱이 아닙니다.

문답·기준안 본문의 ‘이번 작성은 로컬 저장’이나 ‘구현 미확정’은 당시 기록입니다. 이 동기화로 해당 문서와 이후 앱을 GitHub에 추가했으며 현재 지원 계약은 [입력 계약](../../workspace/v051/INPUT_DECISION_CONTRACT.md), 저장·최신성 변경은 작업실 README와 `project-schema.js`를 참조합니다. 초기 HTML과 검증 이미지는 보존합니다. 저장소는 비공개를 유지하며 GitHub Pages나 공개 배포를 켜지 않습니다.

현재 구현과 남은 과제는 [로드맵](../../ROADMAP.md)을 함께 확인하세요. 열 연결·요약·판단 작성은 v0.5에 구현했고, 전체 자유 설계 대화는 여전히 후속입니다.
