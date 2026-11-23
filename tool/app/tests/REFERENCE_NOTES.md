# 독립 수학 기준 fixture

## 범위와 독립성

- `INPUT_CONTRACT.md`의 수치 조건을 기준으로 작성했다. 합성 고정 집계만 사용한다. 원자료나 자격증명에 접근하지 않았다.
- `engine.js` 또는 다른 작업자의 구현·출력을 읽거나 호출하지 않았다. 이 결과는 엔진 검증 완료가 아니라 **엔진과 비교할 독립 기준**이다.
- 프로젝트 작성 파일은 `tests/generate_reference.py`, `tests/golden_reference.json`, 이 문서뿐이다. 패키지 환경은 프로젝트 밖 mira scratch에만 설치했다.
- 첫 계산 전에 Python 소스의 28개 시나리오, 11개 상호작용 시나리오, 8개 Holm 시나리오를 명시적으로 고정했다. 난수와 seed 탐색은 없다(`rng_used=false`, `seed=null`). 양 군 분모 각각 1..4의 모든 성공 수 조합 196개도 전수 포함한다. 원하는 p값·승패에 맞춘 카운트 수정은 하지 않았다.

## JSON 구조

`cases` 224개는 `{id,input,expected}`이며 `input` 키는 정확히 `a_success,a_total,b_success,b_total`이다. `expected`는 다음을 포함한다.

- `fisher_p`: 양측 Fisher p값
- `wilson_a`, `wilson_b`: 각 `[lower,upper]`
- `newcombe_diff_ci`: B-A의 `[lower,upper]`
- `diff`: B 성공률 - A 성공률

합계 분모가 200 이하인 211개는 `exact_fisher_fraction`에 약분한 정확 유리수의 분자·분모를 십진 문자열로 함께 저장한다. 이는 부동소수점 기준만 반복한 값이 아니다. 정상·동일 비율·음의 효과·양쪽 0·한쪽 0·양쪽 전체 성공·한쪽 전체 성공·완전 분리·배정 불균형·희귀 사건·분모 200,000·작은 표·단일 관측을 포함한다. 작은 표가 명시 시나리오와 중복되는 경우도 이름을 달리해 의도적으로 유지한다.

`interaction_cases` 11개는 `input.g1`, `input.g2` 각각 같은 네 입력 키를 갖는다. 6개 지원, 5개 미지원(성공 4, 실패 4, 0 성공, 전체 성공, 0 분모)의 경계를 포함한다. `expected`에는 `supported,diff,standard_error,z,p_raw,ci,holm_input_p`를 둔다. 0 분모는 diff도 null이다. 다른 미지원 경우 기술적 diff는 계산하되 추론은 null이며 Holm 투입값만 1이다.

`holm_cases` 8개는 `input.p_values`, `unsupported_indices`와 `expected.p_adjusted`, `reject`를 갖는다. 원래 가설 순서로 반환한다. m=1, m=4, 비정렬, 동률, step-down 단조성, 0/1, 미지원 유지, alpha 경계를 포함한다. 미지원의 p=1은 실제 계산된 p값이 아니다.

## 고정 방법

- 독립·무작위·성숙 관측·고정 중단을 전제하는 수학 비교다. 실제 실험 조건을 증명하지 않는다. alpha=0.05, 명목 신뢰수준 0.95, 연속성 보정 없음.
- Fisher: `scipy.stats.fisher_exact([[a,n_a-a],[b,n_b-b]], alternative='two-sided')`. `method`를 전달하지 않는 2x2 정확 검정이며 Monte Carlo가 아니다. 관측 표 확률 이하인 가능한 표들의 확률을 합하는 probability-ordering 양측 정의다. 두 단측 p값의 작은 쪽에 2를 곱하는 정의가 아니다.
- 작은 표 독립 교차검증: `comb(n_a,x)*comb(n_b,s-x)`를 정수로 비교해 관측값 이하인 표를 전수 합산하고 공통 분모 `comb(n_a+n_b,s)`로 나눈 `Fraction`. 동률은 정수의 정확한 `<=`로 포함하며 epsilon을 쓰지 않는다.
- Wilson: statsmodels `proportion_confint(...,alpha=0.05,method='wilson')`. 별도 stdlib 공식으로 대조한다. z는 SciPy `norm.ppf(0.975)`이다.
- Newcombe: statsmodels `confint_proportions_2indep(b,n_b,a,n_a,method='newcomb',compare='diff',alpha=0.05,correction=False)`. B가 첫 군이므로 방향은 B-A다. 별도 Wilson 계산으로 `d-sqrt((pB-LB)^2+(UA-pA)^2)`, `d+sqrt((UB-pB)^2+(pA-LA)^2)`를 대조한다. Fisher와 완전히 쌍대인 구간이라고 주장하지 않는다.
- 상호작용: `D=(pB1-pA1)-(pB2-pA2)`; `SE=sqrt(sum(p_i*(1-p_i)/n_i))`로 독립인 네 이항 비율의 비풀링 분산을 합산한다. 네 군 각각 성공·실패가 모두 5 이상일 때만 `z=D/SE`, 양측 `2*norm.sf(abs(z))`, `D±z_0.975*SE`. 정규 꼬리는 별도 stdlib `erfc(abs(z)/sqrt(2))`와 대조한다. 이는 로지스틱 회귀의 odds-ratio 상호작용이 아니다.
- Holm: statsmodels `multipletests(...,alpha=0.05,method='holm')`. 별도 정렬→`(m-rank)*p`→누적 최댓값→1 절단→원순서 복구와 대조한다. `reject`는 조정 p<=0.05다. 구간은 Holm 동시 구간이 아니다.

## 실행 환경과 재생성

시스템 Python에는 SciPy/statsmodels가 없음을 실제 확인했다. uv가 사용 가능하여 다음 **격리 환경에만** 설치했다. 전역 Python이나 다른 Hermes 프로필을 변경하지 않았다.

- Python 3.14.7
- SciPy 1.18.1
- statsmodels 0.15.0
- numpy 2.5.5
- 전체 설치 의존성 버전은 JSON `reference.installed_distributions`에 기록했다.
- 환경: `C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch/ab-reference-venv`
- 작업 경로: `C:/Users/Administrator/Downloads/AB_Test_Local_MVP_v02`

Git Bash에서 프로젝트 경로를 작업 디렉터리로 사용하여 실행:

```bash
'C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch/ab-reference-venv/Scripts/python.exe' tests/generate_reference.py
'C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch/ab-reference-venv/Scripts/python.exe' tests/generate_reference.py --check
```

`--check`는 JSON을 다시 쓰지 않고 전체 재계산 결과(환경 버전 포함)와 기존 JSON의 구조적 동등성을 확인한다. scratch는 임시 경로이므로 추후 환경이 정리되면 아래처럼 같은 버전으로 재구성한다.

```bash
uv venv 'C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch/ab-reference-venv' --python python
uv pip install --python 'C:/Users/Administrator/AppData/Local/hermes/profiles/mira/cache/scratch/ab-reference-venv/Scripts/python.exe' 'scipy==1.18.1' 'statsmodels==0.15.0'
```

완전한 환경 버전까지 동일하게 비교하려면 JSON에 기록한 전이 의존성 버전도 고정해야 한다. Python 버전이 달라도 `--check`의 환경 메타데이터 비교는 실패한다. 네트워크 다운로드·설치는 성공했으며 fallback은 사용하지 않았다.

## 실제 실행 결과

생성 및 `--check` 모두 exit code 0, `status=PASS`.

```text
group_cases: 224
interaction_cases: 11
holm_cases: 8
exact_fraction_case_count: 211
max_absolute_discrepancy:
  fisher_exact: 1.1102230246251565e-16
  wilson_a:     2.220446049250313e-16
  wilson_b:     2.220446049250313e-16
  newcombe:     2.220446049250313e-16
  interaction_p: 1.1102230246251565e-16
  holm:         0.0
```

## 비교 오차 권장과 한계

- 비율·위험차·구간 끝점과 일반 p값: 절대 오차 1e-10 권장. p값의 상대 오차 허용은 1e-7 권장.
- `0 < reference_p < 1e-10`이면 절대 오차만으로 통과시키지 말고 상대 오차 <=1e-7를 요구한다. 기준값이 양수인데 엔진이 0이면 실패시킨다.
- `large_extreme_underflow`의 SciPy 결과 0은 binary64 underflow이지 수학적으로 확률 0이라는 뜻이 아니다. 이 케이스는 binary64 0을 허용하되 정확한 log-p 또는 임의 정밀도 꼬리 검증으로 주장하지 않는다.
- 작은 표의 독립 정수/Fraction 대조는 211개에 한한다. 큰 표의 Fisher 기준은 SciPy이며 큰 표를 별도 임의 정밀도 구현으로 전수 대조하지 않았다.
- Wilson/Newcombe/Holm은 statsmodels와 별도 공식 대조, 상호작용은 SciPy 정규 꼬리와 stdlib erfc 대조다. 정규분포 분위수는 같은 SciPy에서 가져오므로 모든 요소가 완전히 독립인 두 소프트웨어 스택이라는 주장은 하지 않는다.
- 이 fixture는 수학 엔진 비교용이다. 파서, 브라우저, 고객 데이터, 집단 계획의 사전성, LLM, 실험 타당성 검증은 범위 밖이다.
