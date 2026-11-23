/* Browser decision, project restore, and report all use the same calculation. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./engine.js'));
  else root.ABRollout = factory(root.ABEngine);
})(globalThis, function (engine) {
  'use strict';

  const arms = ['a', 'b'];
  const countKeys = arms.flatMap(arm => ['total', 'visit', 'optout'].map(metric => `${metric}-${arm}`));
  const thresholdKeys = ['visit-min', 'optout-max'];
  const numberKeys = [...countKeys, ...thresholdKeys];
  const statuses = ['unknown', 'ready', 'blocked'];
  const comparisons = {single: '사전 지정 단일 비교 / 95% 신뢰구간', three: '사전 지정 3개 비교 보정 / 약 98.33% 신뢰구간'};
  const sourceLabels = {synthetic: '가상 정기점검 사례', synthetic_edited: '입력을 변경한 가상 정기점검 사례', manual: '사용자 입력'};
  const designLabel = '무작위 배정, 고객별 독립성, 관측 완료 및 사전 종료 기준';
  // Two-sided normal quantile for 1 - 0.05 / (2 × 3).
  const threeComparisonZ = 2.3939797998185104;
  const example = {
    'total-a': 15482, 'total-b': 15603, 'visit-a': 1416, 'visit-b': 1597,
    'optout-a': 129, 'optout-b': 139, 'visit-min': 0.5, 'optout-max': 0.2,
    comparison: 'three', capacity: 'unknown', cost: 'unknown', 'design-confirmed': true
  };

  const percentPoints = value => `${value > 0 ? '+' : ''}${value.toFixed(3)}%p`;
  const operational = (value, label) => ({
    passed: value === 'ready',
    reason: `${label} ${{ready: '조건 충족으로 입력됨', unknown: '미확인', blocked: '조건 미충족'}[value]}`
  });
  const checkLabel = ({passed, reason}) => `${passed ? '충족' : '보류'} — ${reason}`;
  const exceedsTotal = (input, key) => input[key] > input[`total-${key.at(-1)}`];

  function normalize(record) {
    const raw = record?.input;
    if (!raw || typeof record.source !== 'string' || !Object.hasOwn(sourceLabels, record.source)) throw Error('확대 판단의 입력 또는 출처가 유효하지 않습니다.');
    const input = Object.fromEntries(numberKeys.map(key => [key, raw[key]]));
    for (const key of countKeys) {
      const value = input[key];
      if (!Number.isSafeInteger(value) || value < (key.startsWith('total-') ? 1 : 0) || value > 200000 || exceedsTotal(input, key)) {
        throw Error('확대 판단의 배정 인원이나 지표 건수가 유효하지 않습니다.');
      }
    }
    for (const key of thresholdKeys) {
      const value = input[key];
      if (!Number.isFinite(value) || value < 0 || value > 100 || Math.abs(value*100-Math.round(value*100)) > 1e-8) {
        throw Error('확대 판단의 기준값이 유효하지 않습니다.');
      }
    }
    if (typeof raw.comparison !== 'string' || !Object.hasOwn(comparisons, raw.comparison) || !statuses.includes(raw.capacity) ||
        !statuses.includes(raw.cost) || typeof raw['design-confirmed'] !== 'boolean') {
      throw Error('확대 판단의 비교 계획이나 확인 상태가 유효하지 않습니다.');
    }
    Object.assign(input, {
      comparison: raw.comparison, capacity: raw.capacity, cost: raw.cost, 'design-confirmed': raw['design-confirmed']
    });
    // Editing a project file cannot turn user-supplied counts into the original example.
    const source = record.source === 'synthetic' && Object.keys(example).some(key => input[key] !== example[key])
      ? 'synthetic_edited' : record.source;
    const compare = (metric, z) => {
      const [a, b] = arms.map(arm => ({total: input[`total-${arm}`], success: input[`${metric}-${arm}`]}));
      return engine.differenceInterval(a, b, z);
    };
    const corrected = input.comparison === 'three';
    const visit = compare('visit', corrected ? threeComparisonZ : undefined);
    const optout = compare('optout');
    const visitLower = visit.ci[0]*100;
    const optoutUpper = optout.ci[1]*100;
    const visitMin = input['visit-min'];
    const optoutMax = input['optout-max'];
    const checks = [
      {
        passed: visitLower >= visitMin,
        reason: `방문 완료율 차이 ${percentPoints(visit.diff*100)}, ${corrected ? '보정' : '95% 신뢰구간'} 하한 ${percentPoints(visitLower)} / 최소 개선폭 ${percentPoints(visitMin)}`
      },
      {
        passed: optoutUpper <= optoutMax,
        reason: `수신 철회율 차이 ${percentPoints(optout.diff*100)}, 95% 신뢰구간 상한 ${percentPoints(optoutUpper)} / 허용 상한 ${percentPoints(optoutMax)}`
      },
      operational(input.capacity, '센터 수용량'),
      operational(input.cost, '비용')
    ];
    if (!input['design-confirmed']) checks.push({passed: false, reason: `${designLabel}이 미확인입니다.`});
    return {source, input, decision: checks.every(check => check.passed) ? 'review' : 'hold', reasons: checks};
  }

  function decisionLabel(record) {
    return record?.decision === 'review' ? '확대 검토 가능' : '확대 보류';
  }

  function report(record, escape) {
    if (!record) return '';
    const {input} = record;
    return `<section class="rollout-report">
      <h2>방문 완료율과 수신 철회 기준으로 본 확대 판단</h2>
      <p><strong>${decisionLabel(record)}</strong> / ${sourceLabels[record.source]}${record.source.startsWith('synthetic') ? ' / 배정 후 28일 관측 기준' : ''}</p>
      <h3>판단에 쓴 입력값</h3>
      <ul>${arms.map(arm => `<li>${arm.toUpperCase()}군: 배정 ${input[`total-${arm}`].toLocaleString('ko-KR')}명, 방문 완료 ${input[`visit-${arm}`].toLocaleString('ko-KR')}명, 수신 철회 ${input[`optout-${arm}`].toLocaleString('ko-KR')}명</li>`).join('')}
      <li>방문 완료율 비교 계획: ${comparisons[input.comparison]}</li>
      <li>${designLabel}: ${input['design-confirmed'] ? '입력 화면에서 확인됨' : '미확인'}</li></ul>
      <h3>자동 판단 근거</h3>
      <ul>${record.reasons.map(check => `<li>${escape(checkLabel(check))}</li>`).join('')}</ul>
      <p>수용량과 비용은 입력된 확인 상태를 사용합니다. 확대 검토 가능은 실제 확대 승인과 구분합니다.</p>
    </section>`;
  }

  function mount(onChange) {
    const form = document.getElementById('rollout-form');
    const fields = form.elements;
    const decision = document.getElementById('rollout-decision');
    const reasons = document.getElementById('rollout-reasons');
    let source = null;
    let current = null;

    function render() {
      const input = Object.fromEntries(numberKeys.map(key => [key, fields[key].valueAsNumber]));
      let exceeds = false;
      for (const key of countKeys.filter(key => !key.startsWith('total-'))) {
        const invalid = exceedsTotal(input, key);
        exceeds ||= invalid;
        fields[key].setCustomValidity(invalid ? '건수는 배정 인원 이하여야 합니다.' : '');
        fields[key].setAttribute('aria-invalid', String(invalid || (fields[key].value !== '' && !fields[key].validity.valid)));
      }
      Object.assign(input, {
        capacity: fields.capacity.value, cost: fields.cost.value, comparison: fields.comparison.value,
        'design-confirmed': fields['design-confirmed'].checked
      });
      current = source && form.matches(':valid') ? normalize({source, input}) : null;
      decision.textContent = decisionLabel(current);
      const labels = current ? current.reasons.map(checkLabel) : [
        exceeds ? '방문 완료와 수신 철회 건수는 각 군의 배정 인원 이하여야 합니다.' :
          '배정 인원, 두 지표의 건수, 판단 기준을 입력 범위에 맞게 채워 주세요.'
      ];
      reasons.replaceChildren(...labels.map(label => {
        const item = document.createElement('li');
        item.textContent = label;
        return item;
      }));
    }

    function restore(record) {
      form.reset();
      source = record?.source ?? null;
      if (record) {
        for (const [key, value] of Object.entries(record.input)) {
          if (key === 'design-confirmed') fields[key].checked = value;
          else fields[key].value = value;
        }
        form.closest('details').open = true;
      }
      render();
    }

    document.getElementById('rollout-clear').addEventListener('click', () => {
      restore(null);
      onChange();
    });
    form.addEventListener('input', () => {
      source = source === 'synthetic' ? 'synthetic_edited' : (source ?? 'manual');
      render();
      onChange();
    });
    form.addEventListener('submit', event => event.preventDefault());
    render();

    return {
      current: () => current,
      snapshot() {
        if (source && !current) throw Error('확대 판단의 입력을 마저 채우거나 비운 뒤 저장해 주세요.');
        return current;
      },
      restore
    };
  }

  return {normalize, mount, report};
});
