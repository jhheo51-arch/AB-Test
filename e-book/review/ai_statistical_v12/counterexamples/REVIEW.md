# 고정 반례의 별도 재계산 검수

AI and separately implemented numerical audit, not human review

Direct Wilson-Newcombe construction; constrained-binomial likelihood score under fixed risk difference with MN finite-sample correction; one-sided upper bound obtained by root inversion; separate statsmodels checks

| 사례 | 완료 차이 pp | 완료 구간 pp | 보호 단측 상한 pp | 비열등성 p | 상태 |
|---|---:|---|---:|---:|---|
| P01 | +3.000000 | [+1.750669, +4.250831] | +0.222138 | 0.001428673 | execution_candidate |
| P02 | +5.000000 | [+3.469456, +6.536577] | +0.333042 | 0.003817956 | execution_candidate |
| P03 | +0.800000 | [-0.397287, +1.997877] | +0.222138 | 0.001428673 | additional_evidence |
| P04 | +3.000000 | [+1.750669, +4.250831] | +1.624449 | 0.997737126 | protection_review |

검사 76개: 통과 51개, 불일치 25개. 기존 출력과의 비교는 새 계산을 만든 뒤 수행했다.

P02의 다른 사전 집단도 같은 비교 가족 수준에서 재계산했다. 성과와 보호를 함께 충족해야 하는 적용 주장은 교집합 조건이며 두 적용 집단의 Bonferroni 범위와 구분했다. 계산 일치는 사전등록이나 실행 승인, 현장 효과를 입증하지 않는다.

실행: `uv run --with scipy --with statsmodels python e-book/review/ai_statistical_v12/counterexamples/RECALCULATE.py`

미검증: 원 UI의 선택 설문 및 측정 누락 분기, 실제 사람 수행과 현장 운영.
