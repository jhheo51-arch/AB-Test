# v13 통계 교정 실행 보고서

결과: 세 수정사항을 새 canonical 경로에서 실행했고 모든 회귀검사를 통과했다. 원자료·기존 결과·v12 감사는 변경하지 않았다.

## A01: 군별 계획 검정력
| 지표 | 원장 % | 교정 % | A n | B n |
|---|---:|---:|---:|---:|
| drive_primary | 87.888447793 | 87.878147532 | 21637 | 22024 |
| contract_rare | 51.760590487 | 51.699642477 | 21637 | 22024 |
| optout_risk | 60.000642132 | 59.936207323 | 21637 | 22024 |
| complaint_rare | 9.685783950 | 9.637040727 | 21637 | 22024 |
| drive_tiny | 6.240868914 | 6.238875275 | 21637 | 22024 |

5개 metric_readiness 행 모두 수정했다. A=계획 baseline, B=계획 target과 각각의 실제 배정 n을 명시했다. 관측효과 사후 검정력이 아니다. 나머지 원장 값은 보존했다.

## A02: 비영 위험차 보호 score
직접 이항 제약우도 미분 root + MN N/(N−1) 분산 보정, 단측 정규 p 및 단측 상한 역산을 사용했다. 라이브러리 비영차 score 호출이나 패치를 사용하지 않았다.
| 사례 | 교정 p | 교정 단측 상한 pp |
|---|---:|---:|
| P01 | 0.00142867348332 | 0.222138406071 |
| P02 | 0.0038179556864 | 0.333042167546 |
| P02_other | 0.0038179556864 | 0.333042167546 |
| P03 | 0.00142867348332 | 0.222138406071 |
| P04 | 0.997737125638 | 1.62444923044 |

COUNTEREXAMPLE_RESULTS.json은 기존의 모든 키와 다른 숫자·문구·상태를 그대로 복사했고 보호 p/상한 두 필드만 교정했다. 중첩 other_group도 포함한다. 기존 감사값은 비교목표로만 사용했으며 새 계산에서 생성했다.

## A03: 파생 DB와 시간 창
v03 DB를 읽기 전용으로 열어 SQLite backup으로 v13 DB를 만들고 outcomes 뷰에 배정일 이상 하한만 추가했다. 모든 원테이블의 행 수·정렬 내용 해시와 다른 스키마는 같고, 새 뷰 집계는 기존 원장과 일치한다.

## 회귀검사
실행 통과 109건. 확률/n 동시 라벨 교환 불변, 불균등 n 역매핑 오류 검출, 독립 정규 계산, 우도 잔차·다항식 root·수치 최적화, p/상한 판정 일관성, 네 사건의 −1/0/window/window+1 경계 16개와 원DB 복제본의 오염 주입을 검사했다. 최종 저장 DB를 재개방하여 integrity·테이블 내용·뷰·집계도 확인했다.

## 산출물
- e-book/virtual-data/v13/analysis_report_v13.json
- e-book/virtual-data/v13/data/jh_motors_v13.sqlite
- e-book/virtual-data/v13/DERIVED_MANIFEST.json
- e-book/analysis/corrections_v13/COUNTEREXAMPLE_RESULTS.json
- e-book/analysis/corrections_v13/SCORE_DETAILS.json
- e-book/analysis/corrections_v13/REGRESSION_CHECK.json
- e-book/analysis/corrections_v13/PROVENANCE.json
- e-book/analysis/corrections_v13/outcomes_v13.sql

## 미해결 한계
원계획의 정확 바이트 해시 문제는 고치지 않았다. 실제 입력 해시·DB의 역사적 해시·LF/CRLF 표현 해시·HEAD JSON/표현 동등성을 분리 기록했으며, 동등성을 역사적 정확 바이트 보존으로 승격하지 않는다. 계획/DB 원본과 원 generation_manifest는 불변이다. 정규 근사와 내부 성공/실패 카운트의 score 경로만 검증했으며 경계 카운트 일반화·정확 공동 FWER·현장 타당성·사람 검수·출간 승인은 범위 밖이다. 원고·표지·새 실험·외부 공유는 수행하지 않았다.
