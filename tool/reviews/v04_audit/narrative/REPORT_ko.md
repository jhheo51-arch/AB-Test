# 엔진 → 로컬 설명 독립 감사

## 결론
- 실제 `engine.js`(0.2.0)와 `narrative.js`(0.4.0)를 읽고 Node에서 합성 입력만 실행했다. 결과 객체 손상·주입은 0건이다.
- 고정 입력 1,728건, 프로그램 검사 15,441건, 실패 0건이다. 이는 아래 명시한 자동 검사 통과이며 설명 완전성까지 보장하지 않는다.
- 지원된 결과에서 승자 반전, 잘못된 유의/비유의 설명, Holm 보류 오분류 또는 교환 불변성 위반은 발견하지 못했다. 작은 셀 Fisher 독립 기준에서도 수학 오류를 발견하지 못했다.
- 낮은 심각도의 설명 보완 2건과 invalid 결과에 대한 설명 API 범용 문구 1건을 기록했다. 중대 통계 결함으로 분류하지 않는다.
- 앱 폴더 전체 68개 파일의 실행 전후 SHA-256이 동일하다. 기존 앱·tests·ZIP은 수정하지 않았다. ZIP 바이트 감사 자체는 이번 범위에 포함하지 않았다.

## 실행과 범위

```bash
node C:/Users/Administrator/Downloads/AB_Test_Workspace_v04_Audit/narrative/audit_narrative.cjs
```

공통 계획: `randomized=true, independent=true, mature=true, fixedStop=true, segmentPrespecified=true, alpha=0.05`. 집단 검사는 `includeSegments=true`, 전체 검사는 false. 아래 개별 사례에서만 덮어쓴다.

| 검사 | 횟수 | 내용 |
|---|---:|---|
| 독립 Fisher | 400 | 양쪽 분모 1..5의 모든 성공 수 조합. 조합수 기반 별도 구현과 엔진의 점화식 구현 비교 |
| Holm | 4,792 | 결과 가족에서 null을 1로 두고 정렬·누적 최대값을 별도로 재계산 |
| 집단 판정/설명 | 6,055 | 추론 가능한 실제 결과의 SUPERIOR/HOLD/HOLM_HOLD 및 우세 안 이름 |
| A/B 교환 | 1,691 | p값 보존, 위험차 부호 반전, 설명 코드 불변 |
| 집단 순서 교환 | 1,250 | 직접 차이 부호 반전, p값·설명 코드 보존 및 대응 집단 설명 일치 |
| 경계 | 1,253 | 각 셀 성공·실패 최소 5 및 전체 군 상한 199999/200000/200001 |

작은 분모 0..5의 모든 성공 수 조합, 각 셀 total=10/success∈{0,4,5,6,10}의 고정 4셀 격자, total=100/success∈{10,30,50,70,90}의 고정 4셀 격자를 사용했다. 이 외 false/undefined/문자열 true/숫자 1의 가정 플래그, 7가지 지원 밖 설계 플래그, alpha/outcome 지원 밖 선언, 사후 집단, 집단 결측, 한 집단, 세 집단, 빈 집단 안을 시험했다. 교환 대조 호출은 기본 1,728건과 별도이며 검사 횟수에 반영했다.

## 설명 보완 사항

### N-01 — 사후 집단 + 결측의 복합 제한을 설명 카드가 하나만 안내
- 심각도: 낮음. **부족한 설명**, 수학 오류 아님.
- 재현 ID: `missing_posthoc`.
- 계획: 공통 계획 + `includeSegments=true, segmentPrespecified=false`.
- 재현 입력:
```csv
arm,success,total,segment
A,10,100,x
B,20,100,x
A,10,100,y
B,20,100,y
A,1,10,
```
- 실제 엔진: 전체에 누락 행을 포함해 A=21/210, B=40/200. `POSTHOC_SEGMENTS`와 `SEGMENT_INFERENCE_BLOCKED`가 함께 존재한다. 집단은 추론하지 않는다.
- 관측 설명: 두 집단 모두 `EXPLORATORY`. 본문은 “집단 기준의 사전성이 확인되지 않아 확증 승패를 내리지 않았어요.” 다음 확인은 기존 사전 계획 확인을 제시한다.
- 기대: 탐색 지위와 별개로 결측 제한도 함께 안내해야 한다. 사전 계획을 확인하더라도 결측 문제는 남는다.
- 위치: 원본 `C:/Users/Administrator/Downloads/AB_Test_Workspace_v04/narrative.js:19-20`.
- 한계: 설명 카드만의 누락이다. 엔진 issues에는 결측 경고가 정확히 남는다. 앱 전체에서 결측이 숨겨진다고 주장하지 않는다.

### N-02 — 빈 집단 안의 정확한 원인을 포괄 안내로 대체
- 심각도: 낮음. **부족한 설명**, 수학 오류 아님.
- 재현 ID: `zero_segment`.
- 계획: 공통 계획 + `includeSegments=true`.
- 재현 입력:
```csv
arm,success,total,segment
A,0,0,x
B,10,100,x
A,10,100,y
B,10,100,y
```
- 실제 엔진: 전체 분모는 양수. x 집단 A.rate=null, diff=null, winner=not_tested이며 `EMPTY_SEGMENT_ARM`이 존재한다.
- 관측 설명: `GROUP_UNSUPPORTED`, “양쪽 안의 분모와 지원 조건을 충족하는지 확인이 필요해요.” 다음 확인은 “빈 군·집단 수·입력 제한”을 나열한다.
- 기대: “이 집단의 A 분모가 0이라 성공 비율이 정의되지 않음”처럼 확정된 원인을 직접 안내한다. 전체 EMPTY_ARM과는 구분해야 한다.
- 위치: 원본 `narrative.js:21`.
- 한계: 잘못된 승자를 만들지 않았고 빈 군 가능성도 이미 언급한다. 정확성과 행동 가능성의 개선 항목이다.

### N-03 — invalid 결과에서 직접 차이 설명의 범용 안내
- 심각도: 낮음. **설명 API의 부정확할 수 있는 범용 문구**, 수학 오류 아님. 지원된 유효 결과의 주된 결함으로 세지 않는다.
- 재현 ID: `invalid`.
- 계획: 공통 계획.
- 재현 입력:
```csv
arm,success,total
A,11,10
B,1,10
```
- 실제 경로: 손상한 결과 객체가 아니라 실제 `prepare→analyze`의 입력 검증 결과다. `status=invalid`, `overall=null`, `SUCCESS_GT_TOTAL`.
- 관측 설명: group()은 올바른 `INVALID`지만 interaction()은 `INTERACTION_BLOCKED`. 다음 확인에 “조건 미확인 상태에서는 기술 통계만 사용해 주세요.”가 포함된다. 이 결과에는 사용할 기술 통계도 없다.
- 기대: invalid 입력은 먼저 수정하고 그 결과의 수치를 사용하지 않도록 group()과 정렬한다.
- 위치: 원본 `narrative.js:30`.
- 노출 한계: `app.js:24`는 prepare 오류가 있으면 분석을 시작하지 않는다. 따라서 정상 입력 화면 흐름에서 이 문구가 표시된 결함으로 보고하지 않는다. 설명 API 직접 호출의 방어적 개선 사항이다.

## 산출물
- `audit_narrative.cjs`: 별도 실행형 독립 검사. 원본은 읽기만 한다.
- `narrative_results.json`: 모든 고정 재현 입력, 계획, 실제 엔진 결과, 실제 설명 문장, 요약, 원본 전후 해시.
- `narrative_summary.json`: 검사 수·실패·설명 코드 분포·발견사항·원본 전후 해시.
- `REPORT_ko.md`: 이 보고서.

모두 `C:/Users/Administrator/Downloads/AB_Test_Workspace_v04_Audit/narrative/`에만 생성했다. 실제 고객자료·외부 LLM·네트워크 호출은 사용하지 않았다. 독립 고정밀 interaction 정규 근사 기준, 대규모 Fisher 정밀도, 브라우저 렌더·공유·ZIP 실행은 이번 검증에 포함하지 않았다. 따라서 수학 전반의 무결성 인증으로 확대하지 않는다.
