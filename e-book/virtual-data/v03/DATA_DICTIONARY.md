# JH Motors v0.3 데이터 사전
모든 고객·이벤트·금액은 합성. 시간은 가상 캠페인 시작 이후 정수 일수. 실제 달력·실적이 아니다.

## assignments (table; 65,559행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| assignment_id | TEXT | False | True |
| customer_id | TEXT | True | False |
| arm | TEXT | True | False |
| assigned_day | INTEGER | True | False |
| probability | REAL | True | False |

## contracts (table; 697행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| contract_id | TEXT | False | True |
| assignment_id | TEXT | True | False |
| signed_day | INTEGER | True | False |
| synthetic_contract_value | INTEGER | True | False |
| synthetic_contribution | INTEGER | True | False |

## customers (table; 120,000행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| customer_id | TEXT | False | True |
| region | TEXT | True | False |
| interest_model | TEXT | True | False |
| lifecycle | TEXT | True | False |
| sms_consent | INTEGER | True | False |
| prior_drive | INTEGER | True | False |
| dealer_id | TEXT | True | False |
| lead_source | TEXT | True | False |

## events (table; 15,852행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| event_id | INTEGER | False | True |
| assignment_id | TEXT | True | False |
| event_type | TEXT | True | False |
| event_day | INTEGER | True | False |

## external_sources (table; 3행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| source_id | TEXT | False | True |
| url | TEXT | True | False |
| grain | TEXT | True | False |
| allowed_analytic_role | TEXT | True | False |
| restriction | TEXT | True | False |

## generation_manifest (table; 9행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| key | TEXT | False | True |
| value_json | TEXT | True | False |

## messages (table; 43,661행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| message_id | TEXT | False | True |
| assignment_id | TEXT | True | False |
| attempt_day | INTEGER | True | False |
| delivered | INTEGER | True | False |

## early_snapshot_day28 (view; 58,000행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| assignment_id | TEXT | False | False |
| arm | TEXT | False | False |
| assigned_day | INTEGER | False | False |
| primary_window_mature |  | False | False |
| contract_window_mature |  | False | False |
| completion_observed_so_far |  | False | False |

## outcomes (view; 65,559행)
| 필드 | SQLite 유형 | NOT NULL | PK |
|---|---|---|---|
| assignment_id | TEXT | False | False |
| customer_id | TEXT | False | False |
| arm | TEXT | False | False |
| assigned_day | INTEGER | False | False |
| booked_28 |  | False | False |
| completed_28 |  | False | False |
| withdrawn_28 |  | False | False |
| contracted_180 |  | False | False |

## 분석 해석
outcomes는 전체 적격 배정 고객을 분모로 한 최종 성숙 집계다. early_snapshot_day28은 캠페인 28일 시점까지 등록된 고객과 그때까지 보인 완료를 기록한다. primary_window_mature=0인 고객의 무사건을 확정 미완료로 취급하지 않는다.
계약의 금액은 가정 기반 계약 가치이며 실제 출고·매출 인식과 다르다. external_sources는 출처 메타데이터일 뿐 실제 고객 정보를 연결한 테이블이 아니다. H에는 실험 메시지 발송이 없으며 자연 전환·철회가 가능하다.
