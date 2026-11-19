# v0.15 수치·그래프 별도 코드 감사

실행 검사 82건, 통과 82건, 불일치 0건. 사람 독립검수나 본책 전체 무오류 판정이 아니다.

## 독립 재계산
- v13 SQLite mode=ro: 원배정에서 EXISTS와 개인별 창 양끝을 적용. 3군 × 배정/완료/철회/계약 12개 합계 및 outcomes 뷰 대조.
- 완료 세 대비 pooled z/Bonferroni/Wilson-Newcombe 및 철회 B-A 탐색 95% 재계산.
- 반례 4개와 P02_other 총 5개 고정 카운트: 이항 제약우도 미분 근, MN 보정 score p, 단측 상한 역산, 성과 구간과 표시 상태 대조. 경계 카운트 일반화하지 않음.
- 후속 20,000명: pooled-null 정규 근사의 양쪽 꼬리 합으로 power/MDE 및 정수 최소 n 역산. 기존 함수 미사용.
- 계획 재계산: {"power": 0.6742514668534758, "required_n_each": 13495, "required_n_total": 26990, "additional": 6990, "mde": 0.011661930556879457, "power_previous_integer": 0.7999727737510546, "power_required_integer": 0.800001838266508}

## 원문 근거 위치
- exports/v15/ebook_review_v15.md: 274행 후속 표본 계획; 290–294행 6장 원자료/세 대비 계획; 765–792행 12장 DB/집계/방법; 832행 결정문.
- analysis/winner_v04/core_results.json: groups/primary_family/guardrail_exploratory.
- exports/v15/counterexample_fixture.json 및 COUNTEREXAMPLE_RESULTS.json; analysis/development_v15/PLANNING_EXAMPLE.json.

## 그래프 의미 및 v16 개선
1. winner_effect.svg: 축 pp, 약98.33% CI와 사후 +0.5pp 기준은 적절. 그림 자체에 Wilson–Newcombe, 완료 세 대비 Bonferroni 및 배정 분모 A=21,637/B=22,024를 추가. 점/끝점 숫자도 명시.
2. guardrail_effect.svg: 개별95% 탐색 양측 구간을 안전 비열등성 통과/실패로 해석하지 않도록 유지. 눈금 -0.02/+0.23은 실제 등간격 -0.025/+0.225의 반올림이라 읽기 혼란: -.15,-.05,+.05,+.15,+.25,+.35 같은 일관된 눈금 권장. 증가=악화, 배정 분모와 Newcombe 명시.
3. measurement_v06.svg: 95% Newcombe와 pp 표시 적절. 군당 4,000명 동일 분모, 로그 누락 주입의 별도 합성 실습임을 그림에도 추가. 원장 대조가 모든 현실 측정오류를 복구한다는 일반화 금지.
4. segments_v06.svg: 전체95% 층화 Wald와 상태별97.5% Newcombe를 이미 구분. 전체0.5/0.5 고정 구성, 상태별 군당3,000명/전체 군당6,000명 명시. 개별 구간 차이를 상호작용 유의성으로 대체하지 않음.
5. capacity_v06.svg: 완료 건수와 모형 순가치 만원의 분리 막대, 일60슬롯 고정 수요 조건 명시 적절. 두 열 서로 다른 척도임을 유지하고 0 기준/단위별 눈금 및 모형 기간·총 대상수·10% 정책의 나머지90% 처리를 그림 각주에 명시. 실제 관측 이익/CI 아닌 조건부 결과 표시 유지.

## 불일치
이번 지정 핵심 수치 대조에서 불일치 없음. 전체 책에 이상이 없다는 뜻은 아니다.

## 미검증/막힘
- No scipy/statsmodels installed in current interpreter; stdlib direct calculations only.
- No import/exec/call of any historical audit or production analysis.
- Score applies only to these five interior fixed-count records; boundary counts and general-purpose solver not validated.
- Capacity original demand simulation, financial Welch intervals, historical power grid and Monte Carlo were not rerun.
- SVG XML/axis/numeric inspection, not rendered image/pagination inspection.
- No old files rewritten; historical LF/CRLF equivalence not asserted.
