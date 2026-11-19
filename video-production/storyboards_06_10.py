from math import sqrt
from statistics import NormalDist

from storyboards import card, one, pair, shot

A_RATE, B_RATE = .10, .13
GAP = B_RATE - A_RATE
LARGE = 2_000
NORMAL = NormalDist()
Z95 = NORMAL.inv_cdf(.975)
HALF = Z95 * sqrt((A_RATE * (1-A_RATE) + B_RATE * (1-B_RATE)) / LARGE)
CI = tuple(round(100 * edge, 1) for edge in (GAP-HALF, GAP+HALF))
REPEATED = ((.8, 4.8), (1.4, 5.4), (-.6, 3.4), (3.5, 7.5),
            (2.0, 6.0), (.3, 4.3), (1.1, 5.1), (.7, 4.7))
TARGET = 2
OPTIONS = ((.4, 1.6), (2.2, 4.0))
LOOKS = (.12, .04, .10)
ALPHA = .05
ERROR_LIMIT = .5
ERROR_A, ERROR_B = .002, .013
ERROR_GAP = ERROR_B - ERROR_A
ERROR_HALF = Z95 * sqrt((ERROR_A*(1-ERROR_A) + ERROR_B*(1-ERROR_B)) / LARGE)
ERROR_RESULT = tuple(round(100 * edge, 1) for edge in (ERROR_GAP-ERROR_HALF, ERROR_GAP, ERROR_GAP+ERROR_HALF))


def power(n):
    average = (A_RATE+B_RATE)/2
    critical = Z95*sqrt(2*average*(1-average)/n)
    spread = sqrt((A_RATE*(1-A_RATE)+B_RATE*(1-B_RATE))/n)
    return 1-NORMAL.cdf((critical-GAP)/spread)+NORMAL.cdf((-critical-GAP)/spread)


SIZES = (200, LARGE)
POWERS = tuple(round(power(n)*100) for n in SIZES)
RATES = pair(card("기존 화면 A", "10%", "2,000명 중 200명 가입"),
             card("새 화면 B", "13%", "2,000명 중 260명 가입"))
GAIN = one("전환율 차이", "+3%포인트", "B의 전환율에서 A의 전환율을 뺀 값")


def cues(first, changes):
    return (("", first), *changes)


def chart(speaker, text, title, kind, first, *changes):
    return (*shot(speaker, text, title, [], cues(first, changes)), kind)


def single(speaker, text, title, label, value, note, first="value", *changes):
    return shot(speaker, text, title, one(label, value, note), cues(first, changes))


def rates(speaker, text):
    return shot(speaker, text, "두 화면의 가입률", RATES, cues("first", (("비는", "second"),)))


def lessons():
    ci_open = chart("B", "95% 신뢰구간이라고요? 이번 구간에 진짜 차이가 들어 있을 확률이 95%라는 뜻일까요?",
                    "95% 신뢰구간에서 95%란?", "interval", "sample")
    ci_example = chart("해설", "차이의 추정값은 3%포인트예요. 구간은 약 1에서 5%포인트입니다.",
                       "전환율 차이의 95% 신뢰구간", "interval", "point", ("구간은", "sample"))
    ci_truth = chart("A", "같은 실험을 다시 한다고 상상해요. 숨은 실제 차이는 그대로고, 구간은 매번 달라져요.",
                     "실험을 반복하면", "repeat", "truth", ("구간은", "all"))
    ci_miss = chart("B", "어떤 구간은 실제 차이를 지나가요. 그런데 이 구간은 오른쪽으로 비켜났네요.",
                    "같은 값, 다른 구간", "repeat", "hit", ("그런데", "miss"))
    ci_rule = single("해설", "같은 조건에서 같은 방법을 반복하면, 장기적으로 구간 약 95%가 실제 차이를 포함해요.",
                     "95%가 가리키는 것", "오래 반복했을 때", "약 95%", "실제 차이를 포함하는 구간의 비율")
    ci_close = chart("A", "이번 구간은 이렇게 읽어요. 우리 데이터에서 추정한 차이는 3, 오차를 반영한 범위는 약 1에서 5%포인트.",
                     "하나의 실험을 읽는 법", "interval", "point", ("오차를", "sample"))
    yield 6, ("95% 신뢰구간은", "무슨 뜻일까?"), [
        ci_open, ci_example, ci_truth, ci_miss,
        chart("해설", "화면에 그린 여덟 줄은 포함하는 경우와 놓치는 경우를 보여주는 예시예요.",
              "여덟 줄은 설명용 예시", "repeat", "example", ("놓치는", "miss")),
        ci_rule,
    ], [
        ci_open, rates("해설", "두 화면에 각각 2,000명이 들어왔어요. A의 가입률은 10%, B는 13%였습니다."),
        shot("B", "전환율 차이는 3%포인트네요. 다음번에 똑같이 해도 3이 나올지는 모르겠어요.",
             "한 번의 실험에서 본 차이", GAIN, cues("value", (("다음번에", "note"),))),
        ci_example,
        chart("해설", "가운데 점은 관측한 차이예요. 양끝은 두 그룹의 표본 변동을 반영해서 계산했어요.",
              "점과 양끝의 역할", "interval", "point", ("양끝은", "sample")),
        ci_truth,
        chart("해설", "그림을 그리려고 실제 차이를 3으로 가정했어요. 세로 점선이 그 값이고, 가로 선 하나가 실험 한 번의 구간입니다.",
              "세로선은 고정, 가로선은 여러 개", "repeat", "truth", ("가로", "all")),
        ci_miss,
        chart("해설", "여덟 줄은 포함하는 경우와 놓치는 경우를 보여주는 예시예요. 이 그림의 줄 수로 95%를 계산하지는 않아요.",
              "반복 원리를 그린 예", "repeat", "all", ("놓치는", "miss")),
        ci_rule,
        single("B", "실험을 이미 마쳤다면 이번 구간의 양끝은 정해졌어요. 95%는 그 구간을 만든 방법에 붙는 숫자네요.",
               "구간을 만드는 방법의 성질", "신뢰수준", "95%", "한 구간이 아니라 반복할 때의 포함률", "label", ("그 구간을", "value")),
        ci_close,
    ]

    pw_open = chart("B", "실제로 가입률을 3%포인트 높여도, 우리 실험이 그 차이를 놓칠 수 있나요?",
                    "효과가 있는데도 놓친다면", "power80", "miss")
    pw_assume = shot("해설", "예를 들어 실제로 A가 10%, B는 13%라고 가정해요. 이 차이를 실험이 알아볼 확률을 묻는 거예요.",
                     "실제로 차이가 있다고 가정", pair(card("기존 화면 A", "10%", "설계에 사용하는 가상의 실제 전환율"),
                     card("새 화면 B", "13%", "가정한 개선 폭은 +3%포인트")), cues("first", (("비는", "second"),)))
    pw_define = chart("해설", "검정력 80%라면, 그 효과가 존재할 때 같은 설계의 실험 백 번 중 약 여든 번에서 통계적으로 감지해요.",
                      "검정력 80%를 그림으로", "power80", "detected")
    pw_miss = chart("A", "그러면 효과가 있어도 약 스무 번은 놓치겠네요. 같은 크기의 효과를 가정한 계산이에요.",
                    "감지하지 못하는 경우도 있어요", "power80", "miss")
    sample_line = f"그룹당 200명은 약 {POWERS[0]}%, 2,000명일 때는 약 {POWERS[1]}%입니다. 이 예제의 근사 계산이에요."
    pw_sizes = chart("해설", sample_line, "같은 +3%포인트, 다른 표본", "power_sizes", "first", ("때는", "second"))
    pw_plan = single("B", "그래서 실험 전에 놓치고 싶지 않은 효과 크기와 목표 검정력을 정해요. 그다음 표본 수를 계산합니다.",
                     "실험 전에 정할 것", "예시 목표 검정력", "80%", "감지할 변화 폭과 함께 정하기", "label", ("그다음", "note"))
    yield 7, ("검정력 80%는", "무슨 뜻일까?"), [pw_open, pw_assume, pw_define, pw_miss, pw_plan], [
        pw_open, pw_assume,
        single("A", "우리는 양쪽 방향을 모두 볼 거예요. 실험 전에 유의수준을 5%로 정했다고 합시다.",
               "판정 규칙도 먼저 정해요", "양측 검정", "유의수준 5%", "더 좋아지는 경우와 나빠지는 경우 모두 검사", "label", ("유의수준을", "value")),
        pw_define, pw_miss,
        single("해설", "효과가 없을 때 잘못 감지할 위험과, 효과가 있을 때 올바르게 감지할 확률은 출발 조건이 달라요.",
               "개념마다 출발 조건이 달라요", "가정한 효과가 있을 때", "검정력", "정해 둔 검정에서 감지할 확률", "label", ("올바르게", "value")),
        pw_sizes,
        chart("해설", "두 계산에서 가입률 가정과 판정 기준을 똑같이 뒀어요. 표본이 많아지면 전환율 차이의 우연한 변동이 줄어듭니다.",
              "표본 수를 늘리면 달라지는 것", "power_sizes", "all", ("표본이", "second")),
        single("A", "만약 실제 개선이 1%포인트뿐이라면요? 같은 표본으로 그보다 큰 3%포인트를 찾을 때보다 더 잘 놓쳐요.",
               "작은 효과는 알아보기 어려워요", "같은 그룹 크기와 검정 기준", "+1%포인트", "+3%포인트보다 감지하기 어려운 예", "value", ("같은", "note")),
        single("해설", "결과가 유의하지 않았다면, 설계가 어느 크기의 효과를 감지할 수 있었는지 함께 보세요.",
               "유의하지 않은 결과를 읽을 때", "실험 설계 다시 보기", "감지할 효과 크기", "표본 수와 판정 규칙을 함께 확인"),
        pw_plan,
    ]

    pr_open = chart("B", "가입률이 조금이라도 올랐다는 증거가 있으면, 새 화면을 바로 적용해도 될까요?",
                    "차이가 있으면 바로 적용할까?", "practical", "zero")
    pr_goal = chart("해설", "바꾸는 비용이 있다고 해요. 팀은 최소 2%포인트는 올라야 적용할 가치가 있다고 미리 정했어요.",
                    "팀이 미리 정한 적용 기준", "practical", "goal")
    pr_small = chart("A", "첫 구간은 0보다 높아요. 그런데 0.4에서 1.6%포인트라서 적용 기준에는 못 미칩니다.",
                     "차이는 보이지만 기준에 못 미쳐요", "practical", "zero", ("그런데", "low"))
    pr_big = chart("해설", "둘째 구간은 2.2에서 4%포인트입니다. 구간 전체가 적용 기준인 2%포인트보다 높아요.",
                   "구간 전체가 적용 기준을 넘어요", "practical", "high", ("적용 기준인", "goal"))
    pr_close = chart("B", "차이가 있는지는 0과 비교하고, 적용할 만큼 큰지는 2%포인트 기준과 비교하는군요.",
                     "달라졌는지, 충분히 달라졌는지", "practical", "zero", ("적용할", "goal"))
    yield 8, ("차이가 나면", "바로 바꿀까?"), [pr_open, pr_goal, pr_small, pr_big, pr_close], [
        pr_open,
        single("A", "새 화면을 적용하려면 운영도 바꿔야 해요. 가입이 늘더라도 늘어나는 폭이 그 비용만큼 중요해야 합니다.",
               "새 화면을 적용하는 데 드는 비용", "판단할 질문", "얼마나 늘었나?", "비용과 기대하는 개선 폭을 비교"),
        pr_goal,
        chart("해설", "그래프에 비교선이 두 개 있어요. 왼쪽 0은 변화가 없는 위치, 주황색 2는 팀이 정한 최소 개선 폭입니다.",
              "비교선이 두 개인 이유", "practical", "zero", ("주황색", "goal")),
        pr_small,
        chart("B", "첫 번째의 추정값은 1%포인트예요. 구간 끝도 1.6이라서 팀의 기준까지 닿지 않아요.",
              "첫 번째 결과의 크기", "practical", "low", ("팀의", "goal")),
        pr_big,
        chart("A", "다른 결과에서 구간이 2%포인트 양쪽에 걸치면요? 기준을 넘을지는 이 실험 결과로 아직 분명하지 않아요.",
              "적용 기준에 걸치는 예", "overlap", "middle", ("기준을", "goal")),
        single("해설", "새 화면을 판단할 최소 효과는 결과를 보기 전에 써 두세요. 운영 비용과 고객 영향을 같이 생각하면 정하기 쉬워요.",
               "최소 효과를 언제 정할까?", "서비스마다 다른 기준", "실험 시작 전", "운영 비용과 고객 영향을 고려", "value", ("운영 비용과", "note")),
        pr_close,
        single("B", "다음에 결과를 보면 차이와 구간부터 확인하고, 우리 팀에서 바꿀 가치가 있는지도 따로 보겠어요.",
               "결과표에 함께 넣을 것", "추정한 차이와 그 구간", "최소 개선 폭", "세 값을 함께 두면 판단 근거가 남아요", "label", ("바꿀 가치가", "value")),
    ]

    pk_open = chart("B", "중간에 p값이 0.04예요. 0.05보다 작으니 지금 실험을 끝내도 될까요?",
                    "중간 p값이 0.04라면", "peeking", "middle", ("작으니", "threshold"))
    pk_path = chart("해설", "첫 번째는 0.12예요. 두 번째는 0.04, 세 번째로 미리 정한 마지막 날엔 0.10이 됐습니다.",
                    "같은 실험에서 달라진 p값", "peeking", "first", ("두 번째는", "middle"), ("세 번째로", "last"))
    pk_risk = single("해설", "매번 같은 기준으로 보면서 처음 통과한 순간에 멈추면, 효과가 없어도 있다고 결론 낼 위험이 커질 수 있어요.",
                     "여러 번 보고 첫 통과에서 멈추면", "효과가 없는 상황", "잘못 감지할 위험", "반복해서 볼 때 누적되는 기회", "label", ("결론", "value"))
    pk_fixed = chart("A", "마지막에 한 번 판단하는 설계라면, 미리 정한 마지막 날의 결과를 사용해요.",
                     "정해 둔 마지막 날에 판단", "peeking", "last")
    pk_sequential = single("B", "중간에도 결론을 내야 한다면, 시작 전에 중간 확인 시점과 판정 기준을 반영한 순차 검정을 설계해요.",
                           "중간 판단도 설계할 수 있어요", "여러 번 보도록 만든 검정", "순차 검정", "중간 확인과 종료 규칙을 사전에 정함")
    yield 9, ("중간에 좋아 보이면", "멈춰도 될까?"), [pk_open, pk_path, pk_risk, pk_fixed, pk_sequential], [
        pk_open,
        single("해설", "미리 정한 실험의 종료일이 아직 남아 있어요. 그런데 첫째와 둘째 시점에서도 결과를 봤다고 가정할게요.",
               "이 예제의 원래 판단 시점", "한 번에 판단하기로 한 날", "세 번째 시점", "앞의 두 시점은 도중에 본 값"),
        pk_path,
        chart("A", "점 세 개는 독립된 실험 세 개가 아니에요. 같은 실험에 방문자가 계속 추가된 세 시점입니다.",
              "하나의 실험, 세 번의 확인", "peeking", "all"),
        chart("해설", "둘째 값만 보고 끝냈다면 0.05 선을 넘겼다고 했겠죠. 원래 정한 마지막 날의 값은 그 선 위에 있습니다.",
              "통과한 시점만 골라 본다면", "peeking", "middle", ("마지막 날의", "last")),
        pk_risk,
        single("A", "한 번 보는 기준이 5%라고 해서, 그 기준으로 여러 번 본 전체 과정까지 자동으로 5%가 되진 않아요.",
               "한 번과 여러 번은 다른 절차예요", "한 번 판단할 때 정한 기준", "5%", "여러 번 보면 전체 절차의 오류율을 다시 관리", "value", ("여러 번", "note")),
        pk_fixed,
        single("해설", "측정 오류나 안전 지표는 실험 중에도 볼 수 있어요. 서비스 보호를 위한 중단과 새 화면이 우세하다는 통계 판단은 따로 기록합니다.",
               "실험 중에도 살펴볼 것", "서비스를 보호하기 위한 확인", "오류와 안전 지표", "성과 채택 판정과 구분해서 기록"),
        pk_sequential,
        chart("B", "그러니까 결과를 보고 종료일을 고르기 전에, 실험을 시작할 때 어떤 기준으로 멈출지 정해야겠네요.",
              "언제 멈출지부터 정해요", "peeking", "middle", ("시작할 때", "last")),
    ]

    dc_open = chart("B", "가입률이 3%포인트 올랐는데, 결제 오류도 함께 늘었어요. 그래도 새 화면을 적용할까요?",
                    "가입은 늘고 오류도 늘었다면", "decision", "gain", ("결제", "safety"))
    dc_gain = chart("해설", "가입률은 3%포인트 올랐고, 구간은 1에서 5예요. 적용에 필요한 최소 개선 폭은 2%포인트였습니다.",
                    "가입률 개선 폭 확인", "decision", "gain", ("적용에", "gain_limit"))
    dc_error = chart("A", "결제 오류는 최대 0.5%포인트의 증가까지만 허용하기로 했어요. 관측한 증가는 1.1%포인트였습니다.",
                     "방문자 중 결제 오류율 확인", "decision", "safety_limit", ("관측한", "safety"))
    dc_hold = single("해설", "오류 증가가 허용 범위를 넘었어요. 이 예제에선 새 화면의 적용을 보류하고, 결제 오류 원인을 확인합니다.",
                     "이 실험에서 내릴 결정", "결제 오류가 안전 기준을 넘었어요", "적용 보류", "결제 오류 원인을 파악한 뒤 재검토")
    dc_close = chart("B", "바꿀지 결정할 땐, 가입률이 얼마나 달라졌는지와 함께, 지켜야 할 기준을 넘었는지도 살펴봐요.",
                     "실험 결과를 적용 결정으로", "decision", "gain", ("지켜야", "safety_limit"))
    yield 10, ("가입은 늘었는데", "적용해도 될까?"), [dc_open, dc_gain, dc_error, dc_hold, dc_close], [
        dc_open,
        shot("A", "실험 전에 두 가지를 정했어요. 가입률이 얼마나 개선되면 좋을지와, 결제 오류가 얼마나 늘 때 멈출지예요.",
             "실험을 시작할 때 정한 두 기준", pair(card("가입률 목표", "최소 +2%포인트", "가입률은 높이려는 지표"),
             card("결제 오류 허용 한도", "최대 +0.5%포인트", "오류는 억제하려는 지표")), cues("first", (("결제 오류가", "second"),))),
        rates("해설", "가상 실험에서 두 화면에 2,000명씩 배정했어요. A의 가입률은 10%, B는 13%였습니다."),
        dc_gain,
        chart("B", "가입률 구간이 0보다 높지만, 2%포인트 선을 걸쳐요. 적용할 만큼의 개선인지에는 아직 불확실성이 있어요.",
              "가입률 구간은 적용 기준에 걸려요", "decision", "gain", ("선을", "gain_limit")),
        single("해설", "결제 오류율의 분모도 전체 방문자예요. 같은 화면에서 결제 오류를 한 번 이상 겪은 사람의 비율을 봅니다.",
               "안전 지표의 분모부터 확인", "결제 오류를 겪은 방문자", "전체 배정 방문자", "분자에는 같은 방문자를 한 번만 셉니다", "label", ("사람의", "value")),
        shot("해설", "A에서 2,000명 중 4명, B는 26명이 결제 오류를 겪었다고 해요. 각각 0.2%와 1.3%예요.",
             "가상 결제 오류율 비교", pair(card("기존 화면 A", "0.2%", "방문자 2,000명 중 4명"),
             card("새 화면 B", "1.3%", "방문자 2,000명 중 26명")), cues("first", (("비는", "second"),))),
        dc_error,
        chart("A", "오류가 늘어난 폭의 구간은 0.6에서 1.6%포인트예요. 가장 낮은 쪽도 0.5%포인트 한도를 넘었네요.",
              "오류 증가 구간 전체가 한도 밖", "decision", "safety", ("가장 낮은", "safety_limit")),
        dc_hold,
        single("해설", "실험 기록에는 무엇이 얼마나 바뀌었고, 어떤 기준에 걸렸고, 다음에 무엇을 확인할지 남기세요.",
               "결정의 근거를 남기는 방법", "실험 결과에 붙일 메모", "수치, 기준, 다음 행동", "이 예제의 다음 행동은 결제 오류 원인 확인", "value", ("무엇을 확인할지", "note")),
        dc_close,
    ]
