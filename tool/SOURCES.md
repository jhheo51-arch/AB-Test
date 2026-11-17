# 출처와 검증 범위

조사일: 2026-11-17 (Asia/Seoul). 기능 문서의 직접 열람은 hands-on 제품 시험이나 독립 성능 검증이 아니다. 검색 요약만 확인한 자료를 본문 열람과 구분한다. 문서 명칭·접근 경로는 조사 시점 기준이다.

## A. 웹 기술 보급도
### M1. BuiltWith Top 1m 카테고리
- URL: https://trends.builtwith.com/analytics/a-b-testing
- 표시 제목: A/B Testing Web Usage Distribution.
- 갱신 표시: 2026-11-13. Totals 링크와 제품별 Top 1m 값을 교차 확인.
- 실제 브라우저 본문 확인 및 텍스트 보존. 상위 100만 사이트 표본의 선택값: Brevo 42,080, Visual Website Optimizer 9,607, Optimizely 6,099, AB Tasty 2,407.
- 부모 작업에서는 저장된 본문과 수치를 대조했다. 별도 HTTP 재조회는 human-test 화면으로 연결되었으므로 그 HTTP 응답을 통계 본문 증거로 쓰지 않았다.

### M2. BuiltWith 전체 웹 탐지 범위
- URL: https://trends.builtwith.com/analytics/a-b-testing/traffic/Entire-Internet
- 실제 브라우저 본문 확인 및 보존. 갱신 표시: 2026-11-13.
- 선택값: Brevo 1,559,921, Optimizely 195,486, Visual Website Optimizer 89,715, AB Tasty 39,583.
- 표의 값과 제품별 live 사이트 값을 대조했다. 전체 웹은 탐지 범위이지 인터넷 전수/활성 실험/고유 고객기업 수가 아니다.

### M3. Live/historical 구분
- https://trends.builtwith.com/analytics/Brevo
- https://trends.builtwith.com/analytics/Optimizely
- https://trends.builtwith.com/analytics/Visual-Website-Optimizer
- 제품 페이지의 live, historical, redirect 포함 다운로드 수를 구분했다. 역사적 설치·리다이렉트를 live에 합산하지 않는다.

### M4. WMTips — 정량 근거에서 제외
- URL: https://www.wmtips.com/technologies/a-b-testing/
- 검색 색인 결과는 있으나 브라우저/HTTP 본문이 보안 확인으로 차단됨.
- 순위·비율·분모를 직접 검증하지 못해 확정 숫자 비교에 사용하지 않았다.

## B. 공식 기능 문서
### O1. Optimizely 자동 SRM
https://docs.optimizely.com/experimentation-strategy/docs/optimizely-s-automatic-sample-ratio-mismatch-detection
- 본문 직접 확인. 부모 작업 HTTP 재조회에서도 sequential sample ratio mismatch와 운영 중 점검 설명 확인.
- manual traffic/Stats Accelerator 비활성, 최소 방문자·운영 기간 등 조건과 세그먼트 미지원 한계가 있다. CSV 종료 후 SRM 점검과 동일하지 않다.

### O2. Optimizely 결과 페이지
https://docs.optimizely.com/experimentation-strategy/docs/p_zW-optimizely-experiment-results-page
- 본문 직접 확인: Stats Engine, confidence intervals, FDR, metric 역할, segment/date filter, share, CSV export.
- 세그먼트/필터는 탐색용이라는 주의를 확인했다.

### O3. Optimizely Web 타기팅
https://docs.optimizely.com/web-experimentation/docs/custom-audience-targeting
- 본문 직접 확인: Web 코드·audience 평가·event push 예시.
- 서버·모바일 SDK 전체 가용성으로 확대하지 않는다.

### O4. 통계 방법 개요 — 제품군 제한
https://docs.optimizely.com/experimentation-strategy/docs/statistical-analysis-methods-overview
- 본문은 Feature Experimentation 및 Analytics 범위. 이 문서만으로 Web에 고정/베이지안/순차 모든 선택이 동일 제공된다고 쓰지 않는다.

### V1. VWO Experiment Vitals 입력 경로
https://help.vwo.com/hc/en-us/articles/30447386854681-Keep-Your-Campaigns-Healthy-With-Experiment-Vitals
- 실제 연결: https://help.wingify.com/hc/en-us/articles/58838251378457-Keep-Your-Campaigns-Healthy-With-Experiment-Vitals
- 본문 직접 확인, 부모 HTTP 재조회도 성공. Data Tracking, Conversion Tracking, Minimum Runtime Alert, Guardrails, Experimentation Conduct, SRM 및 campaign/metric별 점검을 확인했다.
- 기능 경고를 모든 잘못된 실험을 자동 판별하는 보증으로 해석하지 않는다.

### V2. SmartStats 구성
https://help.wingify.com/hc/en-us/articles/58838252139545-Achieve-Accurate-Campaign-Results-with-SmartStats-Configuration
- 본문 직접 확인: Bayesian(default), Frequentist, Sequential, Fixed Horizon, Dynamic, 다중 비교 구성.
- 모델·실험 설정의 조건과 계정/에디션 차이는 별도 검토가 필요하다.

### V3. 보고·감사·결정 기록
https://help.wingify.com/hc/en-us/articles/58838194604825-Navigate-the-Campaign-Reports-Dashboard
- 본문 직접 확인, 부모 HTTP 재조회도 성공.
- Activity Timeline을 audit log/collaboration hub로 설명하며 changes/comments/approvals를 기록. variation decision timestamps와 final campaign decision, 보고 공유·CSV를 확인했다.
- 자동 결과 표시와 고객사의 최종 사업 승인 절차가 동일하다고 단정하지 않는다.

### V4. 계획/가설
https://help.wingify.com/hc/en-us/articles/58766251732889-Monitor-and-Manage-Hypotheses-in-Wingify-Plan
- 공개 HTML 본문 직접 확인: 가설 수집·우선순위·상태·linked tests·CSV 가설 import, 별도 Plan 접근 조건.
- 가설 CSV import와 외부 실험 결과 CSV 통계 분석은 다르다.

### B1. Braze Global Control Group
https://braze.com/docs/user_guide/audience/global_control_group
- 본문 직접 확인, 부모 HTTP 재조회도 성공.
- 캠페인/Canvas global holdout, 개별 control과의 관계, API/tag 예외, 그룹 크기·중복 ID 위험과 reporting 정의 확인.
- 해당 GCG reporting의 반복 이벤트/일별 그룹 수 합 분모를 고정 사용자 0/1 전환율과 혼용하지 않는다.

### B2. Braze A/B 통계 — 일부 확인만
https://www.braze.com/docs/user_guide/messaging/ab_testing/analytics
- 공식 검색 요약은 외부 pooled z 계산과 dashboard confidence가 다를 수 있다고 설명.
- 직접 본문 확인 미완료. 정확한 알고리즘·계정별 통계 기능을 단정하지 않았다.

### B3. Braze SDK — 일부 확인만
https://braze.com/docs/developer_guide/sdk_integration
- 검색 소개 확인, 본문 직접 조회 제한. SDK 세부 언어·설치 조건을 확정 비교하지 않았다.

### A1/A2. Adobe Target — 보조 조사
- https://experienceleague.adobe.com/en/docs/target/using/introduction/how-target-works
- https://experienceleague.adobe.com/en/docs/target/using/reports/statistical-methodology/statistical-calculations
- 본문 직접 확인: Web SDK/at.js 실행·타기팅·bot 처리, Manual A/Bn의 Welch 및 Conversion 한정 Bayesian 설명.
- 최종 매트릭스는 길이를 줄이기 위해 VWO/Optimizely/Braze 중심으로 작성했다. Adobe 미선정은 제품 부재·열위 판단이 아니다.

### C1. Brevo 제품 맥락
https://www.brevo.com/
- 공식 제품 페이지 검색·본문 요약에서 이메일·SMS·자동화·CRM 맥락 확인.
- 이번 문서에서는 정확한 통계 엔진·품질 경고·CSV 분석 범위·계약 가격을 평가하지 않았다.

## C. 프로젝트 내부 근거
GitHub API로 실제 내용·경로를 읽었다.
- https://github.com/jhheo51-arch/AB-Test/blob/main/README.md
- https://github.com/jhheo51-arch/AB-Test/blob/main/e-book/virtual-company/JH_Motors.md
- https://github.com/jhheo51-arch/AB-Test/blob/main/e-book/workflow/WORKFLOW_SPEC_v02.md
- https://github.com/jhheo51-arch/AB-Test/blob/main/e-book/workflow/DIAGNOSTIC_RULE_REFINEMENTS.md
- https://github.com/jhheo51-arch/AB-Test/blob/main/e-book/workbook/workbook_v02.md
- `e-book/analysis/v02/verified_analysis.json` 경로 존재는 확인했으나 이번 방향성 작업에서 분석 JSON 전체를 재검토하거나 계산을 재실행하지 않았다. 페르소나 문서의 기존 수치는 실제 읽은 workbook 본문을 인용했다.

## D. 이번에 하지 않은 검증
실제 고객 인터뷰, 페르소나 대상 사용성 시험, 공급자 계정·SDK·실험 실행, 라이선스/가격 견적, 보안 심사, 원천 데이터 처리, 우리 통계 엔진 실행, 시장 전수조사, 기능별 독립 성능 평가.

비교의 상태: 공개 기능의 존재·문서 범위는 근거화했지만, 우리 계획의 편익·우월성·수요는 검증 전이다.
