(() => {
  'use strict';
  const form = document.getElementById('rollout-form');
  const fields = form.elements;
  const decision = document.getElementById('rollout-decision');
  const reasons = document.getElementById('rollout-reasons');
  // Two-sided normal quantile for 1 - 0.05 / (2 × 3).
  const threeComparisonZ = 2.3939797998185104;

  const percentPoints = value => `${value > 0 ? '+' : ''}${value.toFixed(3)}%p`;
  const operational = (value, label) => ({
    passed: value === 'ready',
    reason: `${label} ${{ready: '조건 충족으로 입력됨', unknown: '미확인', blocked: '조건 미충족'}[value]}`
  });

  function render() {
    const arms = ['a', 'b'].map(arm => ({
      total: fields[`total-${arm}`].valueAsNumber,
      visit: fields[`visit-${arm}`].valueAsNumber,
      optout: fields[`optout-${arm}`].valueAsNumber
    }));
    let exceedsTotal = false;
    for (const arm of ['a', 'b']) {
      for (const metric of ['visit', 'optout']) {
        const field = fields[`${metric}-${arm}`];
        const invalid = field.valueAsNumber > fields[`total-${arm}`].valueAsNumber;
        exceedsTotal ||= invalid;
        field.setCustomValidity(invalid ? '건수는 배정 인원 이하여야 합니다.' : '');
        field.setAttribute('aria-invalid', String(invalid || (field.value !== '' && !field.validity.valid)));
      }
    }
    if (!form.matches(':valid')) {
      decision.textContent = '확대 보류';
      reasons.replaceChildren();
      const item = document.createElement('li');
      item.textContent = exceedsTotal ? '방문 완료와 수신 철회 건수는 각 군의 배정 인원 이하여야 합니다.' :
        '배정 인원, 두 지표의 건수, 판단 기준을 입력 범위에 맞게 채워 주세요.';
      reasons.append(item);
      return;
    }

    const compare = (metric, z) => ABEngine.differenceInterval(
      ...arms.map(arm => ({total: arm.total, success: arm[metric]})), z
    );
    const corrected = fields.comparison.value === 'three';
    const visit = compare('visit', corrected ? threeComparisonZ : undefined);
    const optout = compare('optout');
    const visitLower = visit.ci[0]*100;
    const optoutUpper = optout.ci[1]*100;
    const visitMin = fields['visit-min'].valueAsNumber;
    const optoutMax = fields['optout-max'].valueAsNumber;
    const visitPassed = visitLower >= visitMin;
    const optoutPassed = optoutUpper <= optoutMax;
    const checks = [
      {
        passed: visitPassed,
        reason: `방문 완료율 차이 ${percentPoints(visit.diff*100)}, ${corrected ? '보정' : '95% 신뢰구간'} 하한 ${percentPoints(visitLower)} / 최소 개선폭 ${percentPoints(visitMin)}`
      },
      {
        passed: optoutPassed,
        reason: `수신 철회율 차이 ${percentPoints(optout.diff*100)}, 95% 신뢰구간 상한 ${percentPoints(optoutUpper)} / 허용 상한 ${percentPoints(optoutMax)}`
      },
      operational(fields.capacity.value, '센터 수용량'),
      operational(fields.cost.value, '비용')
    ];
    if (!fields['design-confirmed'].checked) {
      checks.push({passed: false, reason: '무작위 배정, 고객별 독립성, 관측 완료 및 사전 종료 기준이 미확인입니다.'});
    }
    decision.textContent = checks.every(check => check.passed) ? '확대 검토 가능' : '확대 보류';
    reasons.replaceChildren(...checks.map(({passed, reason}) => {
      const item = document.createElement('li');
      item.textContent = `${passed ? '충족' : '보류'} — ${reason}`;
      return item;
    }));
  }

  document.getElementById('rollout-example').addEventListener('click', () => {
    form.reset();
    const example = {
      'total-a': 15482, 'total-b': 15603,
      'visit-a': 1416, 'visit-b': 1597,
      'optout-a': 129, 'optout-b': 139,
      'visit-min': 0.5, 'optout-max': 0.2, comparison: 'three'
    };
    for (const [field, value] of Object.entries(example)) fields[field].value = value;
    fields['design-confirmed'].checked = true;
    render();
  });
  form.addEventListener('input', render);
  form.addEventListener('submit', event => event.preventDefault());
  render();
})();
