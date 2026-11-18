# v0.12 AI 및 별도 코드 재계산 검수 — 기본 A/B·v03 A/B/H·손익

검사: passed 329, mismatch 2, blocked 0. 실행 종료상태: 1.

## 핵심 발견
- v03 `outcomes` 뷰에는 사건 창의 배정일 하한 검사가 없다. 재계산에서는 하한·상한을 모두 적용한다. 실제 자료의 배정 전 사건 유무 및 숫자 일치 여부는 아래 검사와 RESULTS.json에 남긴다.
- 계획 파일의 정확 바이트 SHA256은 장부/DB에 저장된 값과 다르다. 현재 LF 파일을 메모리에서 CRLF로만 바꾸면 저장 해시와 정확히 일치한다. 내용 변경이 아니라 줄바꿈 직렬화 차이로 설명되지만 원래 정확 바이트 검사의 mismatch는 보존한다.
- 구조적 문제·바이트 해시 차이를 통계 숫자 불일치와 구별하며 실패를 숨기지 않도록 mismatch가 있으면 종료 1을 반환한다. 장부/본문 숫자의 일치 여부는 검사별 표에 기재한다.

## 실행 중 문제 및 해결
- 최초 실행은 uv Python의 bundled git 하위 프로세스 실행에서 WinError 5로 중단됐다. git 호출을 제거하고 기존 파일을 직접 읽어 SHA256 및 .git/HEAD를 확인하는 방식으로 수정한 뒤 실제 재실행했다.
- 중간 검증에서 본문의 앞선 배정 표를 손익 표로 잘못 선택한 검수 파서 오류 3건을 확인했다. 사례 3 아래의 손익 표로 범위를 제한하여 수정한 후 재실행했으며 원문은 수정하지 않았다.

## 원자료·방법
- SQLite URI `mode=ro` 및 `PRAGMA query_only=ON`. 원배정/고객/원사건/메시지를 직접 읽어 Python 고객별 플래그를 만들고 별도 원사건 EXISTS SQL과 대조했다. 저장 뷰는 입력이 아니라 대조 대상이다.
- 28일/180일 창은 `[배정, 배정+창]` 양끝 포함. 모든 종류의 원사건별 실제 최소/최대 경과일, 하한 미만/상한 초과/관측 종료 이후/고아/중복 건수를 기록했다. 날짜·정수 SQL의 경계 fixture도 검사했다.
- 두 이항비율 pooled z = 차이 / sqrt(pooled×(1-pooled)×(1/n1+1/n0)); 양측 p는 erfc로 직접 계산했다.
- Wilson 폐형식과 Newcombe 제곱합 결합식을 직접 구현하고 statsmodels pooled z/Wilson/Newcombe와 대조했다. v03 완료 가족만 alpha=0.05/3 및 min(1,3p). 철회는 alpha=0.05 미보정 탐색이다.
- 고객당 순기여액 = 계약×계획 기여액 − 완료×계획 운영비 − 발송시도×계획 단가 − B고정비/nB. 고객별 결합을 유지하여 표본분산, Welch-Satterthwaite df, t구간을 계산하고 scipy ttest_ind(equal_var=False)와 대조했다. t분포 CDF/역CDF는 scipy를 사용한다.
- 먼저 원자료에서 계산하고 이후 core_results.json을 읽어 숫자를 대조했다. 본문 사례 1~3 표와 철회 문장의 숫자를 파싱하여 반올림 허용오차로 대조했다.

## 환경
```json
{
  "python": "3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]",
  "executable": "C:\\Users\\Administrator\\AppData\\Local\\uv\\cache\\builds-v0\\.tmpHwPlgl\\Scripts\\python.exe",
  "platform": "Windows-11-10.0.26300-SP0",
  "numpy": "2.5.5",
  "scipy": "1.18.1",
  "statsmodels": "0.15.0",
  "started_at": "2026-11-18T07:52:03.468520+00:00",
  "git_head": "eefdd4ee9ea026c06d65a760706a742e02407bce",
  "command": "uv run --with scipy --with statsmodels --with numpy python \"C:\\Users\\Administrator\\Downloads\\AB-Test-v07\\e-book\\review\\ai_statistical_v12\\core\\재계산.py\"",
  "sqlite": "3.53.1"
}
```

기존 보호 소스 740개 SHA256 전후 대조. 개별 해시는 RESULTS.json에 수록한다. 기존 파일 전체(review, .git, .venv, __pycache__, node_modules 제외)를 보호 대상으로 삼았다.

## 계산 요약
### v01
원자료: `C:\Users\Administrator\Downloads\AB-Test-v07\e-book\virtual-data\v01\data\oem_crm.sqlite`
모집단 12000, 적격 6555, 배정 6555.
```json
{
  "A": {
    "arm": "A",
    "n": 3269,
    "booked": 373,
    "completed": 298,
    "opted_out": 27
  },
  "B": {
    "arm": "B",
    "n": 3286,
    "booked": 456,
    "completed": 332,
    "opted_out": 41
  }
}
```
메시지: `{"A": {"attempts": 3269, "delivered": 3135}, "B": {"attempts": 3286, "delivered": 3143}}`
#### case1
```json
{
  "completed": {
    "n_A": 3269,
    "n_B": 3286,
    "events_A": 298,
    "events_B": 332,
    "rate_A": 0.09115937595594983,
    "rate_B": 0.101034692635423,
    "diff_pp": 0.9875316679473167,
    "relative_lift": 0.10833023565502611,
    "p_raw": 0.17499538689720853,
    "ci_level": 0.95,
    "ci_low_pp": -0.44097919352030884,
    "ci_high_pp": 2.416949290947308
  },
  "booked": {
    "n_A": 3269,
    "n_B": 3286,
    "events_A": 373,
    "events_B": 456,
    "rate_A": 0.11410217191801775,
    "rate_B": 0.13877054169202677,
    "diff_pp": 2.466836977400902,
    "relative_lift": 0.21619544448052408,
    "p_raw": 0.002660607619875726,
    "ci_level": 0.95,
    "ci_low_pp": 0.8579017603161803,
    "ci_high_pp": 4.076369517120361
  },
  "opted_out": {
    "n_A": 3269,
    "n_B": 3286,
    "events_A": 27,
    "events_B": 41,
    "rate_A": 0.008259406546344448,
    "rate_B": 0.012477175897748022,
    "diff_pp": 0.4217769351403574,
    "relative_lift": 0.5106625188791958,
    "p_raw": 0.09196304450453592,
    "ci_level": 0.95,
    "ci_low_pp": -0.07410638558918142,
    "ci_high_pp": 0.9320938183357309
  }
}
```
#### costs_KRW
```json
{
  "A": {
    "total": 4535380.0
  },
  "B": {
    "total": 5245720.0
  }
}
```
### v03
원자료: `C:\Users\Administrator\Downloads\AB-Test-v07\e-book\virtual-data\v03\data\jh_motors_v03.sqlite`
모집단 120000, 적격 65559, 배정 65559.
```json
{
  "A": {
    "arm": "A",
    "n": 21637,
    "booked": 3301,
    "completed": 1971,
    "withdrawn": 181,
    "contracted": 198
  },
  "B": {
    "arm": "B",
    "n": 22024,
    "booked": 3694,
    "completed": 2212,
    "withdrawn": 202,
    "contracted": 268
  },
  "H": {
    "arm": "H",
    "n": 21898,
    "booked": 2231,
    "completed": 1338,
    "withdrawn": 25,
    "contracted": 231
  }
}
```
메시지: `{"A": {"attempts": 21637, "delivered": 20740}, "B": {"attempts": 22024, "delivered": 21111}, "H": {"attempts": 0, "delivered": 0}}`
#### primary_family
```json
[
  {
    "n_A": 21637,
    "n_B": 22024,
    "events_A": 1971,
    "events_B": 2212,
    "rate_A": 0.09109395942136156,
    "rate_B": 0.10043588812204868,
    "diff_pp": 0.9341928700687119,
    "relative_lift": 0.10255266935401684,
    "p_raw": 0.0009133083961252945,
    "ci_level": 0.9833333333333333,
    "ci_low_pp": 0.2597990453563094,
    "ci_high_pp": 1.6084954426550537,
    "comparison": "B-A",
    "p_family": 0.0027399251883758833
  },
  {
    "n_A": 21898,
    "n_B": 21637,
    "events_A": 1338,
    "events_B": 1971,
    "rate_A": 0.06110147045392273,
    "rate_B": 0.09109395942136156,
    "diff_pp": 2.999248896743883,
    "relative_lift": 0.4908636198871267,
    "p_raw": 3.6017629913938105e-32,
    "ci_level": 0.9833333333333333,
    "ci_low_pp": 2.392115620292533,
    "ci_high_pp": 3.6084222462857447,
    "comparison": "A-H",
    "p_family": 1.0805288974181432e-31
  },
  {
    "n_A": 21898,
    "n_B": 22024,
    "events_A": 1338,
    "events_B": 2212,
    "rate_A": 0.06110147045392273,
    "rate_B": 0.10043588812204868,
    "diff_pp": 3.9334417668125945,
    "relative_lift": 0.6437556637493438,
    "p_raw": 1.1593190305095485e-51,
    "ci_level": 0.9833333333333333,
    "ci_low_pp": 3.3134006311970268,
    "ci_high_pp": 4.5553817099415745,
    "comparison": "B-H",
    "p_family": 3.4779570915286455e-51
  }
]
```
#### guardrail_exploratory
```json
{
  "n_A": 21637,
  "n_B": 22024,
  "events_A": 181,
  "events_B": 202,
  "rate_A": 0.0083653001802468,
  "rate_B": 0.009171812568107519,
  "diff_pp": 0.08065123878607197,
  "relative_lift": 0.09641164937095245,
  "p_raw": 0.3662127252724378,
  "ci_level": 0.95,
  "ci_low_pp": -0.09494866033497797,
  "ci_high_pp": 0.2564597254022712
}
```
#### financial_means
```json
{
  "A": 16915.57332347368,
  "B": 22801.467490010895,
  "H": 20181.295095442507
}
```
#### financial_exploratory
```json
[
  {
    "comparison": "B-A",
    "currency": "KRW",
    "diff_krw": 5885.894166537215,
    "ci95_low_krw": 2060.8525780568393,
    "ci95_high_krw": 9710.93575501759,
    "p_unadjusted": 0.0025625190425343416,
    "welch_df": 43013.6474064879,
    "standard_error_krw": 1951.5327758723627,
    "t": 3.016036542817549
  },
  {
    "comparison": "A-H",
    "currency": "KRW",
    "diff_krw": -3265.721771968827,
    "ci95_low_krw": -6950.478784860983,
    "ci95_high_krw": 419.03524092332964,
    "p_unadjusted": 0.08237258472762436,
    "welch_df": 43387.282157035974,
    "standard_error_krw": 1879.9601672346066,
    "t": -1.7371228544552915
  },
  {
    "comparison": "B-H",
    "currency": "KRW",
    "diff_krw": 2620.172394568388,
    "ci95_low_krw": -1316.726072454218,
    "ci95_high_krw": 6557.070861590993,
    "p_unadjusted": 0.19207854015668177,
    "welch_df": 43734.635740299615,
    "standard_error_krw": 2008.6029864232496,
    "t": 1.304475006897291
  }
]
```

## 검사별 expected / actual / tolerance / status
큰 해시 사전은 JSON 참조. 상대오차는 희귀 p값을 절대오차로 무시하지 않도록 사용했다. 본문 pp 2자리 ±0.005pp, 원 단위 ±0.5원 등 표시 정밀도에 따른 허용오차를 적용했다.

| 검사 | expected | actual | tolerance | status |
|---|---|---|---|---|
| Git HEAD expected | "eefdd4ee9ea026c06d65a760706a742e02407bce" | "eefdd4ee9ea026c06d65a760706a742e02407bce" | {"absolute": 0, "relative": 0} | passed |
| v01 SQLite query_only | 1 | 1 | {"absolute": 0, "relative": 0} | passed |
| v01 integrity_check | ["ok"] | ["ok"] | {"absolute": 0, "relative": 0} | passed |
| v01 foreign_key_check | [] | [] | {"absolute": 0, "relative": 0} | passed |
| v01 assignment ID uniqueness | 6555 | 6555 | {"absolute": 0, "relative": 0} | passed |
| v01 assigned customer uniqueness | 6555 | 6555 | {"absolute": 0, "relative": 0} | passed |
| v01 assigned eligibility violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 eligible population fully assigned | 6555 | 6555 | {"absolute": 0, "relative": 0} | passed |
| v01 assignment arm set | ["A", "B"] | ["A", "B"] | {"absolute": 0, "relative": 0} | passed |
| v01 assignment probabilities | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v01 booking duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v01 booking complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking_cancelled below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking_cancelled above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking_cancelled after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking_cancelled orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 booking_cancelled duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v01 booking_cancelled duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v01 booking_cancelled complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 opt_out below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 opt_out above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 opt_out after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 opt_out orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 opt_out duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v01 opt_out duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v01 opt_out complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 test_drive_completed below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 test_drive_completed above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 test_drive_completed after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 test_drive_completed orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 test_drive_completed duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v01 test_drive_completed duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v01 test_drive_completed complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 Python raw-event flags vs independent raw SQL | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 stored view vs lower-and-upper-bounded raw flags | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 orphan messages | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 unique message IDs | 6555 | 6555 | {"absolute": 0, "relative": 0} | passed |
| v01 per-assignment messages: A/B exactly 1, H exactly 0 | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 message time after assignment and before cutoff violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 delivery timestamp violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v01 allocation SRM diagnostic p>=0.001 | true | true | {"absolute": 0, "relative": 0} | passed |
| v01 costs DB vs manifest | {"attempted_sms": 20, "completed_test_drive": 15000, "B_fixed_setup": 200000} | {"attempted_sms": 20.0, "completed_test_drive": 15000.0, "B_fixed_setup": 200000.0} | {"absolute": 0, "relative": 0} | passed |
| v03 SQLite query_only | 1 | 1 | {"absolute": 0, "relative": 0} | passed |
| v03 integrity_check | ["ok"] | ["ok"] | {"absolute": 0, "relative": 0} | passed |
| v03 foreign_key_check | [] | [] | {"absolute": 0, "relative": 0} | passed |
| v03 assignment ID uniqueness | 65559 | 65559 | {"absolute": 0, "relative": 0} | passed |
| v03 assigned customer uniqueness | 65559 | 65559 | {"absolute": 0, "relative": 0} | passed |
| v03 assigned eligibility violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 eligible population fully assigned | 65559 | 65559 | {"absolute": 0, "relative": 0} | passed |
| v03 assignment arm set | ["A", "B", "H"] | ["A", "B", "H"] | {"absolute": 0, "relative": 0} | passed |
| v03 assignment probabilities | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 booking below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 booking above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 booking after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 booking orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 booking duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v03 booking duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v03 booking complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 consent_withdrawn below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 consent_withdrawn above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 consent_withdrawn after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 consent_withdrawn orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 consent_withdrawn duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v03 consent_withdrawn duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v03 consent_withdrawn complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contract_signed below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contract_signed above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contract_signed after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contract_signed orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contract_signed duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v03 contract_signed duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v03 contract_signed complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 test_drive_completed below_lower | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 test_drive_completed above_upper | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 test_drive_completed after_cutoff | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 test_drive_completed orphan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 test_drive_completed duplicate customer events | 0 | 0 | {"absolute": 0, "relative": 0} | passed |

> v03 test_drive_completed duplicate customer events: 현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.

| v03 test_drive_completed complete observation windows | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 Python raw-event flags vs independent raw SQL | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 stored view vs lower-and-upper-bounded raw flags | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 stored outcomes view contains assignment lower bound | true | false | {"absolute": 0, "relative": 0} | mismatch |

> v03 stored outcomes view contains assignment lower bound: 원래 뷰는 상한만 검사한다. 현재 원사건에는 배정 전 사건이 없어 실제 집계는 일치하지만 미래/오염 자료에서는 위험. 원본 수정 안 함.

| v03 orphan messages | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 unique message IDs | 43661 | 43661 | {"absolute": 0, "relative": 0} | passed |
| v03 per-assignment messages: A/B exactly 1, H exactly 0 | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 message time after assignment and before cutoff violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 delivery timestamp violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 H no experimental messages | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 allocation SRM diagnostic p>=0.001 | true | true | {"absolute": 0, "relative": 0} | passed |
| v03 contract IDs unique | 697 | 697 | {"absolute": 0, "relative": 0} | passed |
| v03 contracts one per assignment | 697 | 697 | {"absolute": 0, "relative": 0} | passed |
| v03 contracts vs valid contract-event flags | RESULTS.json 해당 검사 참조 | RESULTS.json 해당 검사 참조 | {"absolute": 0, "relative": 0} | passed |
| v03 contract signed_day vs event_day | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contractual synthetic contribution vs plan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contractual synthetic value vs plan | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 contract table window [0,180] violations | 0 | 0 | {"absolute": 0, "relative": 0} | passed |
| v03 Welch B-A t/df/p vs scipy | [3.016036542817549, 43013.6474064879, 0.0025625190425343416] | [3.016036542817549, 43013.6474064879, 0.0025625190425343416] | {"absolute": 1e-10, "relative": 1e-10} | passed |
| v03 Welch B-A interval vs scipy | [2060.8525780568393, 9710.93575501759] | [2060.8525780568393, 9710.93575501759] | {"absolute": 1e-07, "relative": 0} | passed |
| v03 Welch A-H t/df/p vs scipy | [-1.7371228544552917, 43387.28215703598, 0.08237258472762435] | [-1.7371228544552915, 43387.282157035974, 0.08237258472762436] | {"absolute": 1e-10, "relative": 1e-10} | passed |
| v03 Welch A-H interval vs scipy | [-6950.478784860983, 419.03524092332964] | [-6950.478784860983, 419.03524092332964] | {"absolute": 1e-07, "relative": 0} | passed |
| v03 Welch B-H t/df/p vs scipy | [1.304475006897291, 43734.635740299615, 0.19207854015668177] | [1.304475006897291, 43734.635740299615, 0.19207854015668177] | {"absolute": 1e-10, "relative": 1e-10} | passed |
| v03 Welch B-H interval vs scipy | [-1316.726072454218, 6557.070861590993] | [-1316.726072454218, 6557.070861590993] | {"absolute": 1e-07, "relative": 0} | passed |
| v03 customer net vs aggregate accounting A | 16915.57332347368 | 16915.57332347368 | {"absolute": 1e-07, "relative": 0} | passed |
| v03 customer net vs aggregate accounting B | 22801.4674900109 | 22801.467490010895 | {"absolute": 1e-07, "relative": 0} | passed |
| v03 customer net vs aggregate accounting H | 20181.295095442507 | 20181.295095442507 | {"absolute": 1e-07, "relative": 0} | passed |
| v03 plan confirmatory family | ["B-A completed", "A-H completed", "B-H completed"] | ["B-A completed", "A-H completed", "B-H completed"] | {"absolute": 0, "relative": 0} | passed |
| completed B-A alpha=0.05 pooled z vs statsmodels | [1.3563262503241411, 0.1749953868972085] | [1.3563262503241411, 0.17499538689720853] | {"absolute": 0, "relative": 1e-11} | passed |
| completed B-A alpha=0.05 Newcombe vs statsmodels | [-0.004409791935203099, 0.024169492909473088] | [-0.004409791935203088, 0.024169492909473077] | {"absolute": 1e-13, "relative": 0} | passed |
| completed B-A alpha=0.05 Wilson 332/3286 | [0.09119167947385222, 0.11180942777710161] | [0.09119167947385222, 0.11180942777710161] | {"absolute": 1e-14, "relative": 0} | passed |
| completed B-A alpha=0.05 Wilson 298/3269 | [0.08176637022184263, 0.10151212535088075] | [0.08176637022184265, 0.10151212535088074] | {"absolute": 1e-14, "relative": 0} | passed |
| booked B-A alpha=0.05 pooled z vs statsmodels | [3.004450827655081, 0.002660607619875727] | [3.004450827655081, 0.002660607619875726] | {"absolute": 0, "relative": 1e-11} | passed |
| booked B-A alpha=0.05 Newcombe vs statsmodels | [0.008579017603161803, 0.04076369517120361] | [0.008579017603161803, 0.04076369517120361] | {"absolute": 1e-13, "relative": 0} | passed |
| booked B-A alpha=0.05 Wilson 456/3286 | [0.1273715809623914, 0.15101309814278188] | [0.1273715809623914, 0.15101309814278188] | {"absolute": 1e-14, "relative": 0} | passed |
| booked B-A alpha=0.05 Wilson 373/3269 | [0.10365328148928554, 0.12545694833861612] | [0.10365328148928554, 0.12545694833861612] | {"absolute": 1e-14, "relative": 0} | passed |
| opted_out B-A alpha=0.05 pooled z vs statsmodels | [1.685132323795203, 0.09196304450453588] | [1.685132323795203, 0.09196304450453592] | {"absolute": 0, "relative": 1e-11} | passed |
| opted_out B-A alpha=0.05 Newcombe vs statsmodels | [-0.0007410638558918168, 0.00932093818335731] | [-0.0007410638558918142, 0.00932093818335731] | {"absolute": 1e-13, "relative": 0} | passed |
| opted_out B-A alpha=0.05 Wilson 41/3286 | [0.009210880239104527, 0.01688200596686651] | [0.009210880239104529, 0.01688200596686651] | {"absolute": 1e-14, "relative": 0} | passed |
| opted_out B-A alpha=0.05 Wilson 27/3269 | [0.005682624795863109, 0.01199053766814949] | [0.0056826247958631105, 0.011990537668149488] | {"absolute": 1e-14, "relative": 0} | passed |
| completed B-A alpha=0.016666666666666666 pooled z vs statsmodels | [3.315954064280072, 0.0009133083961252922] | [3.315954064280072, 0.0009133083961252945] | {"absolute": 0, "relative": 1e-11} | passed |
| completed B-A alpha=0.016666666666666666 Newcombe vs statsmodels | [0.002597990453563094, 0.016084954426550536] | [0.002597990453563094, 0.016084954426550536] | {"absolute": 1e-13, "relative": 0} | passed |
| completed B-A alpha=0.016666666666666666 Wilson 2212/22024 | [0.09569056839150245, 0.10538910485894135] | [0.09569056839150245, 0.10538910485894135] | {"absolute": 1e-14, "relative": 0} | passed |
| completed B-A alpha=0.016666666666666666 Wilson 1971/21637 | [0.08651858622379371, 0.0958858947022174] | [0.08651858622379371, 0.0958858947022174] | {"absolute": 1e-14, "relative": 0} | passed |
| completed A-H alpha=0.016666666666666666 pooled z vs statsmodels | [11.806759644751569, 3.601762991393729e-32] | [11.806759644751569, 3.6017629913938105e-32] | {"absolute": 0, "relative": 1e-11} | passed |
| completed A-H alpha=0.016666666666666666 Newcombe vs statsmodels | [0.02392115620292533, 0.036084222462857446] | [0.02392115620292533, 0.036084222462857446] | {"absolute": 1e-13, "relative": 0} | passed |
| completed A-H alpha=0.016666666666666666 Wilson 1971/21637 | [0.08651858622379371, 0.0958858947022174] | [0.08651858622379371, 0.0958858947022174] | {"absolute": 1e-14, "relative": 0} | passed |
| completed A-H alpha=0.016666666666666666 Wilson 1338/21898 | [0.05734027739276591, 0.06509234023887349] | [0.05734027739276591, 0.06509234023887349] | {"absolute": 1e-14, "relative": 0} | passed |
| completed B-H alpha=0.016666666666666666 pooled z vs statsmodels | [15.122019539004933, 1.1593190305094997e-51] | [15.122019539004933, 1.1593190305095485e-51] | {"absolute": 0, "relative": 1e-11} | passed |
| completed B-H alpha=0.016666666666666666 Newcombe vs statsmodels | [0.03313400631197027, 0.04555381709941574] | [0.03313400631197027, 0.04555381709941574] | {"absolute": 1e-13, "relative": 0} | passed |
| completed B-H alpha=0.016666666666666666 Wilson 2212/22024 | [0.09569056839150245, 0.10538910485894135] | [0.09569056839150245, 0.10538910485894135] | {"absolute": 1e-14, "relative": 0} | passed |
| completed B-H alpha=0.016666666666666666 Wilson 1338/21898 | [0.05734027739276591, 0.06509234023887349] | [0.05734027739276591, 0.06509234023887349] | {"absolute": 1e-14, "relative": 0} | passed |
| withdrawn B-A alpha=0.05 pooled z vs statsmodels | [0.9035902271640395, 0.36621272527243764] | [0.9035902271640395, 0.3662127252724378] | {"absolute": 0, "relative": 1e-11} | passed |
| withdrawn B-A alpha=0.05 Newcombe vs statsmodels | [-0.000949486603349781, 0.0025645972540227126] | [-0.0009494866033497797, 0.0025645972540227118] | {"absolute": 1e-13, "relative": 0} | passed |
| withdrawn B-A alpha=0.05 Wilson 202/22024 | [0.007995608821711324, 0.010519208419148227] | [0.007995608821711325, 0.010519208419148225] | {"absolute": 1e-14, "relative": 0} | passed |
| withdrawn B-A alpha=0.05 Wilson 181/21637 | [0.007235969928625902, 0.009669170267370455] | [0.007235969928625902, 0.009669170267370455] | {"absolute": 1e-14, "relative": 0} | passed |
| boundary integer SQL window 28 lag -1 | false | false | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 28 lag 0 | true | true | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 28 lag 28 | true | true | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 28 lag 29 | false | false | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 180 lag -1 | false | false | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 180 lag 0 | true | true | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 180 lag 180 | true | true | {"absolute": 0, "relative": 0} | passed |
| boundary integer SQL window 180 lag 181 | false | false | {"absolute": 0, "relative": 0} | passed |
| boundary timestamp SQL 28d lag seconds -1 | false | false | {"absolute": 0, "relative": 0} | passed |
| boundary timestamp SQL 28d lag seconds 0 | true | true | {"absolute": 0, "relative": 0} | passed |
| boundary timestamp SQL 28d lag seconds 2419200 | true | true | {"absolute": 0, "relative": 0} | passed |
| boundary timestamp SQL 28d lag seconds 2419201 | false | false | {"absolute": 0, "relative": 0} | passed |
| core_results.json/case1/completed/n_A | 3269 | 3269 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/n_B | 3286 | 3286 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/events_A | 298 | 298 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/events_B | 332 | 332 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/rate_A | 0.09115937595594983 | 0.09115937595594983 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/rate_B | 0.101034692635423 | 0.101034692635423 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/diff_pp | 0.9875316679473167 | 0.9875316679473167 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/relative_lift | 0.10833023565502611 | 0.10833023565502611 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/p_raw | 0.1749953868972085 | 0.17499538689720853 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/case1/completed/ci_level | 0.95 | 0.95 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/ci_low_pp | -0.4409791935203099 | -0.44097919352030884 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/completed/ci_high_pp | 2.4169492909473087 | 2.416949290947308 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/n_A | 3269 | 3269 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/n_B | 3286 | 3286 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/events_A | 373 | 373 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/events_B | 456 | 456 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/rate_A | 0.11410217191801775 | 0.11410217191801775 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/rate_B | 0.13877054169202677 | 0.13877054169202677 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/diff_pp | 2.466836977400902 | 2.466836977400902 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/relative_lift | 0.21619544448052408 | 0.21619544448052408 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/p_raw | 0.002660607619875727 | 0.002660607619875726 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/case1/booked/ci_level | 0.95 | 0.95 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/ci_low_pp | 0.8579017603161803 | 0.8579017603161803 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/booked/ci_high_pp | 4.076369517120361 | 4.076369517120361 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/n_A | 3269 | 3269 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/n_B | 3286 | 3286 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/events_A | 27 | 27 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/events_B | 41 | 41 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/rate_A | 0.008259406546344448 | 0.008259406546344448 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/rate_B | 0.012477175897748022 | 0.012477175897748022 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/diff_pp | 0.4217769351403574 | 0.4217769351403574 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/relative_lift | 0.5106625188791958 | 0.5106625188791958 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/p_raw | 0.09196304450453588 | 0.09196304450453592 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/ci_level | 0.95 | 0.95 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/ci_low_pp | -0.07410638558918167 | -0.07410638558918142 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/case1/opted_out/ci_high_pp | 0.9320938183357309 | 0.9320938183357309 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/0/n | 21637 | 21637 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/0/booked | 3301 | 3301 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/0/completed | 1971 | 1971 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/0/withdrawn | 181 | 181 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/0/contracted | 198 | 198 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/1/n | 22024 | 22024 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/1/booked | 3694 | 3694 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/1/completed | 2212 | 2212 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/1/withdrawn | 202 | 202 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/1/contracted | 268 | 268 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/2/n | 21898 | 21898 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/2/booked | 2231 | 2231 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/2/completed | 1338 | 1338 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/2/withdrawn | 25 | 25 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/groups/2/contracted | 231 | 231 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/n_A | 21637 | 21637 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/n_B | 22024 | 22024 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/events_A | 1971 | 1971 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/events_B | 2212 | 2212 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/rate_A | 0.09109395942136156 | 0.09109395942136156 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/rate_B | 0.10043588812204868 | 0.10043588812204868 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/diff_pp | 0.9341928700687119 | 0.9341928700687119 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/relative_lift | 0.10255266935401684 | 0.10255266935401684 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/p_raw | 0.0009133083961252922 | 0.0009133083961252945 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/ci_level | 0.9833333333333333 | 0.9833333333333333 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/ci_low_pp | 0.2597990453563094 | 0.2597990453563094 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/ci_high_pp | 1.6084954426550537 | 1.6084954426550537 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/0/p_family | 0.002739925188375877 | 0.0027399251883758833 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/n_A | 21898 | 21898 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/n_B | 21637 | 21637 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/events_A | 1338 | 1338 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/events_B | 1971 | 1971 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/rate_A | 0.06110147045392273 | 0.06110147045392273 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/rate_B | 0.09109395942136156 | 0.09109395942136156 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/diff_pp | 2.999248896743883 | 2.999248896743883 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/relative_lift | 0.4908636198871267 | 0.4908636198871267 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/p_raw | 3.601762991393729e-32 | 3.6017629913938105e-32 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/ci_level | 0.9833333333333333 | 0.9833333333333333 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/ci_low_pp | 2.392115620292533 | 2.392115620292533 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/ci_high_pp | 3.6084222462857447 | 3.6084222462857447 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/1/p_family | 1.0805288974181187e-31 | 1.0805288974181432e-31 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/n_A | 21898 | 21898 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/n_B | 22024 | 22024 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/events_A | 1338 | 1338 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/events_B | 2212 | 2212 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/rate_A | 0.06110147045392273 | 0.06110147045392273 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/rate_B | 0.10043588812204868 | 0.10043588812204868 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/diff_pp | 3.9334417668125945 | 3.9334417668125945 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/relative_lift | 0.6437556637493438 | 0.6437556637493438 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/p_raw | 1.1593190305094997e-51 | 1.1593190305095485e-51 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/ci_level | 0.9833333333333333 | 0.9833333333333333 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/ci_low_pp | 3.3134006311970268 | 3.3134006311970268 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/ci_high_pp | 4.5553817099415745 | 4.5553817099415745 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/primary_family/2/p_family | 3.477957091528499e-51 | 3.4779570915286455e-51 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/n_A | 21637 | 21637 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/n_B | 22024 | 22024 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/events_A | 181 | 181 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/events_B | 202 | 202 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/rate_A | 0.0083653001802468 | 0.0083653001802468 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/rate_B | 0.009171812568107519 | 0.009171812568107519 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/diff_pp | 0.08065123878607197 | 0.08065123878607197 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/relative_lift | 0.09641164937095245 | 0.09641164937095245 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/p_raw | 0.36621272527243764 | 0.3662127252724378 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/ci_level | 0.95 | 0.95 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/ci_low_pp | -0.09494866033497809 | -0.09494866033497797 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/guardrail_exploratory/ci_high_pp | 0.25645972540227124 | 0.2564597254022712 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_means/A | 16915.57332347368 | 16915.57332347368 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_means/B | 22801.467490010895 | 22801.467490010895 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_means/H | 20181.295095442507 | 20181.295095442507 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/0/diff_krw | 5885.894166537215 | 5885.894166537215 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/0/ci95_low_krw | 2060.8525780568393 | 2060.8525780568393 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/0/ci95_high_krw | 9710.93575501759 | 9710.93575501759 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/0/p_unadjusted | 0.0025625190425343416 | 0.0025625190425343416 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/0/welch_df | 43013.6474064879 | 43013.6474064879 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/1/diff_krw | -3265.721771968827 | -3265.721771968827 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/1/ci95_low_krw | -6950.478784860983 | -6950.478784860983 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/1/ci95_high_krw | 419.03524092332964 | 419.03524092332964 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/1/p_unadjusted | 0.08237258472762436 | 0.08237258472762436 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/1/welch_df | 43387.282157035974 | 43387.282157035974 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/2/diff_krw | 2620.172394568388 | 2620.172394568388 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/2/ci95_low_krw | -1316.726072454218 | -1316.726072454218 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/2/ci95_high_krw | 6557.070861590993 | 6557.070861590993 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/2/p_unadjusted | 0.19207854015668177 | 0.19207854015668177 | {"absolute": 0, "relative": 1e-10} | passed |
| core_results.json/financial_exploratory/2/welch_df | 43734.635740299615 | 43734.635740299615 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/0/assumed_contribution_per_contract | 500000 | 500000 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/0/means_krw/A | 3189.0862873781025 | 3189.0862873781025 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/0/means_krw/B | 4548.652379222666 | 4548.652379222666 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/0/means_krw/H | 4357.932231253996 | 4357.932231253996 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/0/B_minus_H_krw | 190.72014796867006 | 190.72014796867006 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/1/assumed_contribution_per_contract | 1000000 | 1000000 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/1/means_krw/A | 7764.581966076628 | 7764.581966076628 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/1/means_krw/B | 10632.924082818743 | 10632.924082818743 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/1/means_krw/H | 9632.386519316833 | 9632.386519316833 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/1/B_minus_H_krw | 1000.53756350191 | 1000.53756350191 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/2/assumed_contribution_per_contract | 2000000 | 2000000 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/2/means_krw/A | 16915.57332347368 | 16915.57332347368 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/2/means_krw/B | 22801.4674900109 | 22801.4674900109 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/2/means_krw/H | 20181.295095442507 | 20181.295095442507 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/2/B_minus_H_krw | 2620.1723945683916 | 2620.1723945683916 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/3/assumed_contribution_per_contract | 3000000 | 3000000 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/3/means_krw/A | 26066.56468087073 | 26066.56468087073 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/3/means_krw/B | 34970.01089720305 | 34970.01089720305 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/3/means_krw/H | 30730.20367156818 | 30730.20367156818 | {"absolute": 1e-10, "relative": 1e-10} | passed |
| core_results.json/financial_sensitivity/3/B_minus_H_krw | 4239.807225634871 | 4239.807225634871 | {"absolute": 1e-08, "relative": 1e-10} | passed |
| v03 raw plan SHA256 vs ledger | "f1226b7743ed4705f0e79a03f53fca2f057c7500e5e97f70131d4a5a7fe721f7" | "4bcd06f0b5f6a8259f27022f3df8db6285d141091c984f3ee7581044f7e86a56" | {"absolute": 0, "relative": 0} | mismatch |

> v03 raw plan SHA256 vs ledger: 정확한 바이트 해시는 불일치. 현재 LF 파일을 메모리에서 CRLF로만 변환하면 기존 장부 해시와 일치함을 별도 검사했다. 줄바꿈 직렬화 차이이며 내용 변조의 증거로 해석하지 않는다. 원파일은 수정하지 않았다.

| v03 plan CRLF-only representation matches stored ledger hash | "f1226b7743ed4705f0e79a03f53fca2f057c7500e5e97f70131d4a5a7fe721f7" | "f1226b7743ed4705f0e79a03f53fca2f057c7500e5e97f70131d4a5a7fe721f7" | {"absolute": 0, "relative": 0} | passed |

> v03 plan CRLF-only representation matches stored ledger hash: 해시 변환은 진단만 수행하며 기존 정확 바이트 검사 mismatch를 passed로 바꾸지 않는다.

| v03 DB generation plan hash vs ledger | "f1226b7743ed4705f0e79a03f53fca2f057c7500e5e97f70131d4a5a7fe721f7" | "f1226b7743ed4705f0e79a03f53fca2f057c7500e5e97f70131d4a5a7fe721f7" | {"absolute": 0, "relative": 0} | passed |
| 본문 L314 완료, 주지표 A 사건/배정 | [298.0, 3269.0] | [298, 3269] | {"absolute": 0, "relative": 0} | passed |
| 본문 L314 완료, 주지표 B 사건/배정 | [332.0, 3286.0] | [332, 3286] | {"absolute": 0, "relative": 0} | passed |
| 본문 L314 완료, 주지표 diff | 0.99 | 0.9875316679473167 | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L314 완료, 주지표 CI | [-0.44, 2.42] | [-0.44097919352030884, 2.416949290947308] | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L314 완료, 주지표 p | 0.175 | 0.17499538689720853 | {"absolute": 5.0001e-05, "relative": 0} | passed |
| 본문 L315 예약, 진단 A 사건/배정 | [373.0, 3269.0] | [373, 3269] | {"absolute": 0, "relative": 0} | passed |
| 본문 L315 예약, 진단 B 사건/배정 | [456.0, 3286.0] | [456, 3286] | {"absolute": 0, "relative": 0} | passed |
| 본문 L315 예약, 진단 diff | 2.47 | 2.466836977400902 | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L315 예약, 진단 CI | [0.86, 4.08] | [0.8579017603161803, 4.076369517120361] | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L315 예약, 진단 p | 0.0027 | 0.002660607619875726 | {"absolute": 5.0001e-05, "relative": 0} | passed |
| 본문 L316 철회, 보호 A 사건/배정 | [27.0, 3269.0] | [27, 3269] | {"absolute": 0, "relative": 0} | passed |
| 본문 L316 철회, 보호 B 사건/배정 | [41.0, 3286.0] | [41, 3286] | {"absolute": 0, "relative": 0} | passed |
| 본문 L316 철회, 보호 diff | 0.42 | 0.4217769351403574 | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L316 철회, 보호 CI | [-0.07, 0.93] | [-0.07410638558918142, 0.9320938183357309] | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L316 철회, 보호 p | 0.092 | 0.09196304450453592 | {"absolute": 5.0001e-05, "relative": 0} | passed |
| 본문 L341 완료 B-A diff | 0.93 | 0.9341928700687119 | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L341 완료 CI | [0.26, 1.61] | [0.2597990453563094, 1.6084954426550537] | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L341 완료 보정 p | 0.00273993 | 0.0027399251883758833 | {"absolute": 0, "relative": 5e-06} | passed |
| 본문 L342 완료 A-H diff | 3.0 | 2.999248896743883 | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L342 완료 CI | [2.39, 3.61] | [2.392115620292533, 3.6084222462857447] | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L342 완료 보정 p | 1.08053e-31 | 1.0805288974181432e-31 | {"absolute": 0, "relative": 5e-06} | passed |
| 본문 L343 완료 B-H diff | 3.93 | 3.9334417668125945 | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L343 완료 CI | [3.31, 4.56] | [3.3134006311970268, 4.5553817099415745] | {"absolute": 0.00500001, "relative": 0} | passed |
| 본문 L343 완료 보정 p | 3.47796e-51 | 3.4779570915286455e-51 | {"absolute": 0, "relative": 5e-06} | passed |
| 본문 L376 A 손익평균 | 16916.0 | 16915.57332347368 | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L377 B 손익평균 | 22801.0 | 22801.467490010895 | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L378 H 손익평균 | 20181.0 | 20181.295095442507 | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L387 B-A 손익차이 | 5886.0 | 5885.894166537215 | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L387 손익 CI | [2061.0, 9711.0] | [2060.8525780568393, 9710.93575501759] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L388 A-H 손익차이 | -3266.0 | -3265.721771968827 | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L388 손익 CI | [-6950.0, 419.0] | [-6950.478784860983, 419.03524092332964] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L389 B-H 손익차이 | 2620.0 | 2620.172394568388 | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L389 손익 CI | [-1317.0, 6557.0] | [-1316.726072454218, 6557.070861590993] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L396 손익 민감도 | [3189.0, 4549.0, 4358.0, 191.0] | [3189.0862873781025, 4548.652379222666, 4357.932231253996, 190.72014796867006] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L397 손익 민감도 | [7765.0, 10633.0, 9632.0, 1001.0] | [7764.581966076628, 10632.924082818743, 9632.386519316833, 1000.53756350191] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L398 손익 민감도 | [16916.0, 22801.0, 20181.0, 2620.0] | [16915.57332347368, 22801.4674900109, 20181.295095442507, 2620.1723945683916] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L399 손익 민감도 | [26067.0, 34970.0, 30730.0, 4240.0] | [26066.56468087073, 34970.01089720305, 30730.20367156818, 4239.807225634871] | {"absolute": 0.500001, "relative": 0} | passed |
| 본문 L354 철회 수치 추출 | true | true | {"absolute": 0, "relative": 0} | passed |
| 본문 L354 철회 항목0 | 0.837 | 0.83653001802468 | {"absolute": 0.000500001, "relative": 0} | passed |
| 본문 L354 철회 항목1 | 0.917 | 0.9171812568107519 | {"absolute": 0.000500001, "relative": 0} | passed |
| 본문 L354 철회 항목2 | 0.081 | 0.08065123878607197 | {"absolute": 0.000500001, "relative": 0} | passed |
| 본문 L354 철회 항목3 | -0.095 | -0.09494866033497797 | {"absolute": 0.000500001, "relative": 0} | passed |
| 본문 L354 철회 항목4 | 0.256 | 0.2564597254022712 | {"absolute": 0.000500001, "relative": 0} | passed |
| 본문 L354 철회 항목5 | 0.3662 | 0.3662127252724378 | {"absolute": 5.0001e-05, "relative": 0} | passed |
| all protected source hashes unchanged | RESULTS.json 해당 검사 참조 | RESULTS.json 해당 검사 참조 | {"absolute": 0, "relative": 0} | passed |

## 해석과 범위 제한
- 합성 데이터 및 교육용 비용; 실제 OEM 매출/회계 손익 검증 아님.
- 개인 독립, 고정 관측, 군집/간섭 없음에 조건부. 가구/지점 독립성을 DB 고유성만으로 입증하지 않음.
- 철회는 미보정 탐색. 사전 안전 비열등성 설계와 한계가 없어 정식 안전 통과/실패를 계산하지 않음.
- 손익 Welch는 미보정 탐색이며 계약/완료의 고객별 결합과 고정 비용 가정에 조건부.
- 기본 A/B에는 계약이 없으므로 비용만 계산; v03의 계약 수익을 기본 A/B에 대입하지 않음.
- 기존 분석 코드 함수를 가져오거나 실행하지 않았으며 기존 소스/책/DB/이전 결과는 수정하지 않음.
- 검수 스크립트 내부 재계산은 기존 분석 코드와 별개이나 별도 사람 검수 또는 외부 검증을 뜻하지 않음.

완료/손익/철회는 별도 판단이다. 검수 완료가 실제 정책 채택, 사람 검수 또는 다음 출판 단계의 진행을 뜻하지 않는다.
