# JH Motors 합성 DB 안내·데이터 사전 v0.1

저자: 허재혁. 모든 기업·고객·차량·이벤트·비용은 교육용이다. JH Motors는 상표 확인 전 작업명이며 실제 기업과 관계없다.

## 기업과 실험
가상의 승용차 OEM으로 12개 판매 접점과 SUV·Sedan·Crossover 모델을 가정한다. 수도권·중부·남부는 교육용 권역 라벨이다.
실험 질문: 마케팅 SMS 수신에 동의한 잠재 고객 중 시승 경험이 없는 고객에게, 차량 가치 중심 안내 A와 시승 편의 중심 안내 B를 비교하면 실제 시승 완료에 어떤 차이가 나타나는가?
대상: 고객 12,000명 중 prospect·sms_consent=1·prior_test_drive=0인 고객 전원.
배정: 고객 단위 독립 확률 배정, A/B 각 확률 0.5. 반드시 같은 수로 나뉘는 방식은 아니다.
가상 등록 기간: 2026-09-01~2026-09-28, Asia/Seoul. 관측 종료: 2026-10-26 23:59:59 +09:00.
주지표: 배정 후 28일 내 시승 완료 고객 수 / 배정 고객 수. 발송 실패도 분모에 포함.
보조지표: 동일 기간 내 예약. 가드레일: 동일 기간 내 수신 거부.
원래 구매 가능성 대비 마케팅의 증분 효과를 추정하는 무발송 대조군은 없다. A 대비 B만 비교한다.

## 테이블
| 테이블 | 한 행의 의미 | 키·주요 필드 |
|---|---|---|
| company | 가상 OEM 하나 | company_id, name, synthetic=1 |
| dealerships | 판매 접점 하나 | dealer_id, company_id, region |
| vehicle_models | 관심 차종 하나 | model_id, company_id, body_style |
| customers | 합성 고객 하나 | customer_id, dealer_id, model_id, lifecycle, sms_consent, prior_test_drive, lead_source, created_at |
| experiments | 실험 정의 하나 | experiment_id, primary_metric, window_days, data_cutoff |
| assignments | 고객의 실험 배정 하나 | assignment_id, experiment_id, customer_id, arm, assigned_at, probability |
| messages | 배정 고객에 대한 발송 시도 하나 | message_id, assignment_id, attempted_at, delivered_at, status |
| journey_events | 관측 이벤트 하나 | event_id, assignment_id, event_type, event_at |
| cost_assumptions | 교육용 비용 가정 하나 | cost_key, amount, currency, basis, source |

뷰 experiment_outcomes는 고객 배정별 한 행으로 booked·completed·opted_out의 0/1 결과를 집계한다. 28일 관측 기간 밖의 이벤트는 제외한다.

### 범주 정의
- lifecycle: prospect는 잠재 고객, owner는 보유 고객. 실험에는 prospect만 포함.
- sms_consent: 1이면 기준 시점 마케팅 SMS 수신 동의. 실제 운영의 동의 감사 이력을 대체하지 않는 단순화된 값.
- prior_test_drive: 기준 시점 시승 이력 유무.
- lead_source: website / event / referral. 모두 배정 전에 정해진 속성이다.
- journey_events.event_type: booking / test_drive_completed / booking_cancelled / opt_out.
- probability: 실제로 배정된 군의 사전 배정 확률. 현재 모두 0.5.
- 시간: ISO 8601 +09:00 문자열. 날짜 비교는 SQLite julianday로 수행.

## 생성 규칙
시드: 20261116. Python random.Random을 사용한다. 정확한 재현에는 Python 버전도 함께 기록한다.
전달 확률 0.96. 전달 후 먼저 수신 거부 여부를 생성하고, 수신 거부하지 않은 고객에서 예약을 생성한다.
예약 확률 A=0.12, B=0.15. 예약 이후 시승 완료 확률 0.75. 이 값들은 참조한 시장 수치가 아니라 명시적으로 만든 학습용 가정이다.
예약은 발송 1~7일 후, 시승 또는 취소는 예약 1~14일 후로 단순화한다. 실제 예약 취소·재예약·상담 운영을 재현하지 않는다.
생성된 표본의 비율은 위 확률과 다를 수 있다. 표본 결과와 생성 모수는 구분한다.
확정적인 세그먼트별 효과 차이는 주입하지 않았다. 사후 발견을 실제 고객 인사이트라고 주장하지 않는다.
비용은 발송 시도당 20원, 시승 완료당 15,000원, B 고정 준비비 200,000원의 교육용 가정이다. 차량 매출·기여이익·LTV는 생성하지 않았으므로 ROI 또는 매출 개선을 확정할 수 없다.

## 분석 시작 SQL
```sql
SELECT arm, COUNT(*) AS assigned,
       SUM(completed) AS completed,
       1.0 * SUM(completed) / COUNT(*) AS completion_rate,
       SUM(opted_out) AS opt_outs
FROM experiment_outcomes
GROUP BY arm;
```

## 현재 검사와 한계
생성 스크립트는 외래키·DB 무결성·대상 적합성·이벤트 시간·관측 성숙도·예약 없는 완료·발송 상태·뷰 분모를 검사한다. CSV와 JSON을 함께 출력한다.
배정 비율 정상근사 p-value는 품질 점검용이며, 통과가 실험의 유효성을 보장하지 않는다. 주 효과에 대한 p-value나 신뢰구간이 아니다.
현재 DB는 정상 구조의 기본 실습이다. 누락·중복·SRM·효과 없음 시나리오는 아직 별도 제작 전이다.
표본 설계·검정력·종료 규칙·다중 비교·경제성 판단에 대한 독립 검증은 후속 단계다. 이 DB를 실제로 사전등록한 실험이라고 표현하지 않는다.
실제 고객·개인정보·차량 VIN은 포함하지 않는다. 계약·출고·정비·가구·장기 관계·접점 수용량·군 간 간섭은 현재 범위 밖이다.

## 열람
SQLite를 지원하는 도구에서 data/oem_crm.sqlite를 읽거나 data/csv의 UTF-8 BOM CSV를 스프레드시트로 연다. 설치가 필요한 뷰어는 별도 승인 후 사용한다.
