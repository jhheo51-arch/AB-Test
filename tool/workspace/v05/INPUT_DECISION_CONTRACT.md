# 입력·판정 계약 v1.1 — 로컬 A/B MVP v0.2

상태: 사용자 위임에 따라 선택한 초기 구현 명세. 검증 결과는 별도 파일에 기록한다. 실제 고객 데이터 또는 실험 타당성을 인증하지 않는다. 원자료는 브라우저에서 파싱·집계·계산하고 서버에는 전송하지 않는다.

## 입력

CSV 또는 탭으로 구분된 표를 지원한다. UTF-8 BOM, 인용부호와 인용부호 안 줄바꿈을 처리한다. 파일 상한은 첫 구현에서 2MiB, 데이터 행 50,000개로 제한한다. 이 제한은 성능 보장이 아니며 회귀시험 대상으로 삼는다.

집계형 헤더: arm,success,total,segment(선택). arm은 A 또는 B. success와 total은 정수이며 0<=success<=total. 전체만 있으면 A/B 두 행. 집단을 넣으면 각 집단에서 A/B 한 행씩이며 전체 합계 행을 다시 넣지 않는다. 같은 arm/segment 행 중복은 오류다.

개인형 헤더: subject_id,arm,outcome,segment(선택),observed(선택). 각 참여자는 한 행, ID는 중복되지 않는 가명 키. outcome은 0/1이며 미기록을 자동 0으로 바꾸지 않는다. observed가 있으면 모두 1이어야 이 고정 관측 경로를 분석한다. 0·미기록은 미성숙 오류다. 전체/개인 정보의 연결은 사용자 책임 아래 확인하며 이름·이메일·전화는 필요 없다.

열 이름은 위 계약을 사용한다. 임의 열 의미를 AI가 추정해 확정하지 않는다. 오류는 코드·행·열·설명을 반환하며 잘못된 입력을 조용히 버리지 않는다. 고객별 원자료·식별자는 로그·프로젝트 저장·LLM 전송에서 제외한다.

## 분석 조건

plan: randomized, independent, mature, fixedStop은 사용자가 명시적으로 확인하는 boolean이다. 확인은 증명 자체가 아니며 보고서에도 ‘사용자 확인’으로 표시한다. 불명확한 조건이면 기술 통계만 표시하고 p값·구간·승패는 내지 않는다. 순차·적응배분·반복·교차·군집·공유 용량·다수 정책·시간/금액은 이 경로에서 미지원이다.

plan.alpha=0.05 고정, plan.includeSegments, plan.segmentPrespecified를 기록한다. 결과를 본 뒤 새 집단이나 기준을 고르면 탐색으로 표시한다. 사후 탐색을 사전 확증으로 바꾸지 않는다. 각 군 최대 배정 수 200,000명, 전체 분석을 위한 A/B 분모는 양수여야 한다. 집단의 분모가 0이면 그 집단 검정은 불가다.

## 통계 방법

1. 효과는 B-A 위험차와 A를 기준으로 한 상대 변화다. A 비율이 0이면 상대 변화는 정의 불가다.
2. 비율 구간은 Wilson, 위험차 구간은 Newcombe(Wilson 조합)의 명목 95% 근사 구간. 이는 정확 검정과 완전히 쌍대인 구간이라고 주장하지 않는다.
3. 전체·집단 검정은 Fisher exact 양측 검정. 고정 두 군의 성공확률 차이 영가설이며 초등 확률 조건에 맞는지를 확인한다. 큰 정수·0 사건도 시험한다.
4. 집단 차이는 위험차 척도의 직접 차이 (B-A)_G1-(B-A)_G2다. 네 셀 각각 성공·실패가 5 이상일 때만 Wald 정규 근사 검정·명목 구간을 제공한다. 조건 미달이면 직접 차이 추론 미지원으로 남긴다.
5. 전체만 사전 비교하면 가족 m=1. 사전 두 집단과 직접 차이를 함께 검토하면 전체·G1·G2·직접 차이의 가족 m=4에 Holm 보정을 적용한다. 미지원 가설은 p=1을 가족 안에 유지하며, 이를 실제 계산된 p값으로 표시하지 않는다. 이 가족만 보정하며 다른 지표·반복 조회·사후 탐색 전체를 보호하지 않는다.
6. 사후 집단 탐색은 기술 통계로 표시하고 확증 winner를 제공하지 않는다. 집단 정보가 없으면 생성하지 않는다. 빈 집단 속성이 있으면 전체에서 고객을 삭제하지 않고, 집단 확증을 제한한다. 둘을 넘는 집단 축/집단은 초기 상세 검정 미지원으로 표시한다.
7. winner는 조정 p<=alpha와 효과 방향을 함께 사용한다. 양측 판정이고 무차이는 hold. 검정 불가/조건 미확인/탐색이면 not_tested. ‘hold’는 동등성·무해함의 증명이 아니다.
8. 구간은 명목 구간이며 Holm 가족 동시 신뢰구간이 아니다. UI와 보고서에 이를 명시한다. 구간만으로 가족 수준 유의성이나 승리 판정을 대신하지 않는다.

## 실질적 판단

최소 사업 효과와 보호 상태는 통계 승패와 분리한다. 초기에는 해당 기준을 기록하고, 별도의 보호 비열등성 엔진은 제공하지 않는다. 수신 거부 차이가 비유의하다는 이유로 안전 판정을 내리지 않는다. 실행 승인은 항상 사람의 결정이며 자동 발송·고객 적용은 하지 않는다.

## 계산 API

engine.js는 브라우저 전역 ABEngine과 Node module.exports를 제공한다.
- parseTable(text): {headers,rows}; 실패 시 식별 가능한 오류.
- prepare(text,format): {cells,issues,format,sourceRowCount}; format은 aggregate/individual. cells는 {arm,segment,success,total}뿐이며 ID·원래 행을 반환하지 않는다.
- analyze(prepared,plan): {version,status,inference_allowed,overall,segments,interaction,family,issues}. 원자료는 포함하지 않는다.
- VERSION 문자열.

각 group 결과: {A:{success,total,rate},B:{success,total,rate},diff,relative_change,ci,p_raw,p_adjusted,winner}. inference_allowed=false이면 추론 필드는 null. 지원 오류는 상태와 issues로 표현한다.

구현의 status는 ok / descriptive / limited / unsupported / invalid다. 설명 전송에서는 ok를 valid, descriptive를 limited로 정규화한다. segments는 입력의 집단 등장 순서에 따른 label G1/G2만 반환하며 원래 집단 이름은 로컬 준비 집계에서만 대응한다. ci는 [하한,상한], family는 {m,method,alpha,hypotheses}다. parseTable만 원시 rows를 반환하므로 프로젝트·설명 전송에는 사용하지 않는다. v1.1은 구현 키와 전송 경계를 명확히 했으며 v1.0의 수학 방법은 바꾸지 않았다.

## LLM 계약

서버는 계산 결과의 최소 요약만 받는다. 원자료 텍스트·고객 ID·파일명·세그먼트 원래 이름·자유 대화 원문은 보내지 않는다. 집단은 G1/G2로 치환하고, 작은 집단은 설명 페이로드에서 제외해도 핵심 결과의 제한을 알린다. 사용자가 전송 미리보기를 확인하고 명시적으로 설명 요청할 때만 호출한다.

LLM은 수치를 다시 계산하지 않는다. 결과 요약·한계·다음 확인을 한국어로 설명하며, 근거 키는 overall/segments/interaction/issues 중 실제 전송한 키만 허용한다. 모델 출력의 숫자 재진술은 금지하고 수치는 앱이 원래 계산 결과로 표시한다. LLM 텍스트는 HTML로 실행하지 않는다. 연결 실패·출력 검증 실패는 그대로 표시하고 규칙 기반 설명을 유지한다.

이 구현은 정상 기존 인증을 사용하는 Hermes CLI의 mira 프로필을 호출한다. 앱은 인증 파일을 직접 읽지 않는다. 비밀값은 대화·HTML·보고서·프로젝트에 넣지 않는다. 사용 가능한 인증이 없으면 실제 호출 완료라고 하지 않는다. LLM 연결 자체가 로컬 원자료 전송 승인을 뜻하지 않는다. 전송 허용 키는 analysis_status, overall_decision, segments, interaction, guardrail, design_user_confirmed, adjustment, issues이며 모두 숫자 없는 상태·코드다.

## 검증

입력 파서·오류·지원 경계, 작은 표의 정확 조합 확률 또는 SciPy Fisher, statsmodels Newcombe·Wilson, 직접 위험차와 Holm을 별도 기준으로 대조한다. 정상/효과 없음/역방향/0 사건/전체 성공/극단 비율/희귀 사건/집단 정보 부족/사후 탐색을 포함한다. 수치 기준은 검증 스크립트에서 고정하고 실제 차이를 보고한다. 브라우저 완주·프로젝트·공유·원자료 미전송·LLM 성공과 실패를 별도 시험한다. 실제 사용자 효용이나 통계 전 범위 정확성을 보증하지 않는다.
