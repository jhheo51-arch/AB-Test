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
  const metricFields = {goal: 'rollout-goal-name', guard: 'rollout-guard-name'};
  const defaultMetrics = {goal: '방문 완료', guard: '수신 철회'};
  const editWarning = '결과가 나온 뒤 승리 조건을 수정했습니다. 수정 전부터 정해 둔 기준으로 해석할 수 없습니다.';
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

  function normalizeCriteria(raw) {
    const criteria = Object.fromEntries(thresholdKeys.map(key => {
      const value = raw?.[key];
      if (!Number.isFinite(value) || value < 0 || value > 100 || Math.abs(value*100-Math.round(value*100)) > 1e-8) {
        throw Error('확대 판단의 기준값이 유효하지 않습니다.');
      }
      return [key, value];
    }));
    if (typeof raw.comparison !== 'string' || !Object.hasOwn(comparisons, raw.comparison) ||
        (raw.criteriaEdited !== undefined && typeof raw.criteriaEdited !== 'boolean')) {
      throw Error('확대 판단의 비교 계획이나 기준 수정 기록이 유효하지 않습니다.');
    }
    criteria.comparison = raw.comparison;
    const metrics = raw.metrics === undefined ? defaultMetrics : raw.metrics;
    if (!metrics || typeof metrics !== 'object' || Array.isArray(metrics)) throw Error('지표 이름을 확인해 주세요.');
    criteria.metrics = Object.fromEntries(Object.keys(defaultMetrics).map(key => {
      const name = metrics[key];
      if (typeof name !== 'string' || !name.trim() || name.length > 60) throw Error('지표 이름을 확인해 주세요.');
      return [key, name.trim()];
    }));
    if (raw.criteriaEdited) criteria.criteriaEdited = true;
    return criteria;
  }

  function labels(metrics, source) {
    return {
      ...metrics,
      goalRate: metrics.goal === defaultMetrics.goal ? '방문 완료율' : metrics.goal + ' 비율',
      guardRate: metrics.guard === defaultMetrics.guard ? '수신 철회율' : metrics.guard + ' 비율',
      capacity: source?.startsWith('synthetic') ? '센터 수용량' : '운영 수용량'
    };
  }

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
    const {metrics, criteriaEdited, comparison} = normalizeCriteria({
      ...raw, metrics: record.metrics, criteriaEdited: record.criteriaEdited
    });
    if (!statuses.includes(raw.capacity) || !statuses.includes(raw.cost) || typeof raw['design-confirmed'] !== 'boolean') {
      throw Error('확대 판단의 확인 상태가 유효하지 않습니다.');
    }
    Object.assign(input, {
      comparison, capacity: raw.capacity, cost: raw.cost, 'design-confirmed': raw['design-confirmed']
    });
    // Editing a project file cannot turn user-supplied counts into the original example.
    const customMetrics = Object.keys(metrics).some(key => metrics[key] !== defaultMetrics[key]);
    const isEdited = criteriaEdited || customMetrics || Object.keys(example).some(key => input[key] !== example[key]);
    const source = record.source === 'synthetic' && isEdited ? 'synthetic_edited' : record.source;
    const names = labels(metrics, source);
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
        reason: `${names.goalRate} 차이 ${percentPoints(visit.diff*100)}, ${corrected ? '보정' : '95% 신뢰구간'} 하한 ${percentPoints(visitLower)} / 최소 개선폭 ${percentPoints(visitMin)}`
      },
      {
        passed: optoutUpper <= optoutMax,
        reason: `${names.guardRate} 차이 ${percentPoints(optout.diff*100)}, 95% 신뢰구간 상한 ${percentPoints(optoutUpper)} / 허용 상한 ${percentPoints(optoutMax)}`
      },
      operational(input.capacity, names.capacity),
      operational(input.cost, '비용')
    ];
    if (!input['design-confirmed']) checks.push({passed: false, reason: `${designLabel}이 미확인입니다.`});
    const observed = visit.diff === 0 ? `A군과 B군의 목표 지표(${names.goalRate}) 값이 같습니다.`
      : `${visit.diff > 0 ? 'B' : 'A'}군의 목표 지표(${names.goalRate})가 ${percentPoints(Math.abs(visit.diff)*100).slice(1)} 높았습니다.`;
    return {
      source, input, ...(customMetrics ? {metrics} : {}), ...(criteriaEdited ? {criteriaEdited} : {}),
      decision: checks.every(check => check.passed) ? 'review' : 'hold', observed, reasons: checks
    };
  }

  function decisionLabel(record) {
    if (!record) return '판정 대기';
    return record.decision === 'review' ? '확대 검토 가능' : '확대 보류';
  }

  function report(record, escape, metadata) {
    if (!record) return '';
    const {input} = record;
    const synthetic = record.source.startsWith('synthetic');
    const names = labels(record.metrics ?? defaultMetrics, record.source);
    const audience = synthetic
      ? '마케팅 수신에 동의했고 30일 안에 정기점검이 예정된 가상 차주입니다. 이미 예약했거나 필수 안전 고지 대상인 차주는 제외했습니다.'
      : metadata.audience.trim() || '적격 조건 미기록';
    const application = record.decision === 'review'
      ? '입력된 조건에서 확대를 검토할 수 있습니다. 실제 적용 대상과 범위는 미확정입니다.'
      : '확대 보류. 실제 적용 대상과 범위는 미확정입니다.';
    const nextSteps = record.decision === 'review'
      ? '실제 적용 범위와 승인 담당자를 정한 뒤 확대를 검토하세요.'
      : '보류로 표시된 조건을 확인한 뒤 확대 여부를 다시 검토하세요.';
    return `<section class="rollout-report">
      <h2>판정 요약</h2>
      <div class="report-verdict">
        <strong>${decisionLabel(record)}</strong>
        <p>${escape(record.observed)}</p>
        <p>${sourceLabels[record.source]} / ${synthetic ? '배정 후 28일 관측' : escape(metadata.window.trim() || '관측 기간 미기록')}</p>
      </div>
      <h2>실험과 적용 범위</h2>
      ${!synthetic && metadata.purpose.trim() ? `<p>${escape(metadata.purpose)}</p>` : ''}
      <dl class="rollout-scope">
        <dt>실험 대상</dt><dd>${escape(audience)}</dd>
        <dt>분석 고객군</dt><dd>A군 전체와 B군 전체의 집계를 비교했습니다. <strong>고객군별 효과는 미확인</strong>입니다.</dd>
        <dt>적용 범위</dt><dd>${application}</dd>
      </dl>
      <h2>승리 조건과 판단 근거</h2>
      ${record.criteriaEdited ? `<p class="report-warning">${editWarning}</p>` : ''}
      <ul>${record.reasons.map(check => `<li>${escape(checkLabel(check))}</li>`).join('')}</ul>
      <h2>A/B 결과 입력</h2>
      <ul>${arms.map(arm => {
        const count = metric => input[`${metric}-${arm}`].toLocaleString('ko-KR');
        return `<li>${arm.toUpperCase()}군: 배정 ${count('total')}명, ${escape(names.goal)} ${count('visit')}명, ${escape(names.guard)} ${count('optout')}명</li>`;
      }).join('')}</ul>
      ${synthetic ? '<p>A군은 관리 필요성 안내, B군은 예약 편의 안내입니다.</p>' :
        (metadata.policyA.trim() || metadata.policyB.trim() ?
          `<p>A군: ${escape(metadata.policyA || '미기록')} / B군: ${escape(metadata.policyB || '미기록')}</p>` : '')}
      <h2>다음 행동</h2><p>${nextSteps}</p>
      <h2>방법과 한계</h2>
      <ul><li>${escape(names.goalRate)} 비교 계획: ${comparisons[input.comparison]}</li>
        <li>Newcombe–Wilson 방식으로 B−A의 비율 차이를 계산했습니다. 각 군의 최초 배정 인원을 분모로 썼습니다.</li>
        <li>목표 지표는 구간 하한을, 보호 지표는 보정하지 않은 95% 구간 상한을 기준과 비교합니다.</li>
        <li>${designLabel}: ${input['design-confirmed'] ? '입력 화면에서 확인됨' : '미확인'}</li></ul>
      <p>수용량과 비용은 사용자가 입력한 확인 상태입니다. 실제 확대는 승인 절차를 거칩니다.</p>
    </section>`;
  }

  function mount(onChange) {
    const form = document.getElementById('rollout-form');
    const fields = form.elements;
    const metricInputs = Object.fromEntries(Object.entries(metricFields).map(([key, id]) => [key, document.getElementById(id)]));
    const criteriaFields = [...Object.values(metricInputs), ...thresholdKeys.map(key => fields[key]), fields.comparison];
    const panel = form.closest('details');
    const entry = document.getElementById('rollout-entry');
    const decision = document.getElementById('rollout-decision');
    const observed = document.getElementById('rollout-observed');
    const reasons = document.getElementById('rollout-reasons');
    const warning = document.getElementById('rollout-criteria-warning');
    let source = null;
    let current = null;
    let resultSeen = false;
    let criteriaEdited = false;

    function readCriteria() {
      return {
        ...Object.fromEntries(thresholdKeys.map(key => [key, fields[key].valueAsNumber])),
        comparison: fields.comparison.value,
        metrics: Object.fromEntries(Object.entries(metricInputs).map(([key, field]) => [key, field.value.trim()])),
        criteriaEdited
      };
    }

    function render() {
      for (const field of Object.values(metricInputs)) {
        field.setCustomValidity(field.value.trim() ? '' : '행동 이름을 입력해 주세요.');
      }
      const criteria = readCriteria();
      const names = labels({
        goal: criteria.metrics.goal || defaultMetrics.goal,
        guard: criteria.metrics.guard || defaultMetrics.guard
      }, source);
      for (const node of form.querySelectorAll('[data-rollout-label]')) node.textContent = names[node.dataset.rolloutLabel];
      document.getElementById('rollout-arm-a').textContent = source?.startsWith('synthetic') ? 'A군 / 관리 필요성 안내' : 'A군';
      document.getElementById('rollout-arm-b').textContent = source?.startsWith('synthetic') ? 'B군 / 예약 편의 안내' : 'B군';
      const validCriteria = criteriaFields.every(field => field.validity.valid);
      document.getElementById('rollout-criteria-summary').textContent = validCriteria
        ? `이어받은 기준 · ${names.goalRate} 최소 +${criteria['visit-min']}%p / ${names.guardRate} 증가 최대 +${criteria['optout-max']}%p / ${comparisons[criteria.comparison]}`
        : '위의 승리 조건을 먼저 확인해 주세요.';
      warning.hidden = !criteriaEdited;
      warning.textContent = editWarning;

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
      current = source && form.matches(':valid') ? normalize({source, input, metrics: criteria.metrics, criteriaEdited}) : null;
      if (current) resultSeen = true;
      decision.textContent = decisionLabel(current);
      observed.hidden = !current;
      observed.textContent = current?.observed ?? '';
      document.getElementById('rollout-to-report').disabled = !current;
      const messages = current ? current.reasons.map(checkLabel) : [
        exceeds ? '행동 건수는 각 군의 배정 인원 이하여야 합니다.' :
          '배정 인원, 두 지표의 건수, 판단 기준을 입력 범위에 맞게 채워 주세요.'
      ];
      reasons.replaceChildren(...messages.map(message => {
        const item = document.createElement('li');
        item.textContent = message;
        return item;
      }));
    }

    function restore(record, draft) {
      form.reset();
      source = record?.source ?? (draft ? 'manual' : null);
      resultSeen = Boolean(record || draft?.criteriaEdited);
      criteriaEdited = Boolean(record?.criteriaEdited || draft?.criteriaEdited);
      const values = record?.input ?? draft;
      entry.hidden = !values;
      if (values) {
        for (const key of [...numberKeys, 'comparison', 'capacity', 'cost']) {
          if (Object.hasOwn(values, key)) fields[key].value = values[key];
        }
        fields['design-confirmed'].checked = Boolean(values['design-confirmed']);
        for (const [key, field] of Object.entries(metricInputs)) {
          field.value = (record?.metrics ?? draft?.metrics ?? defaultMetrics)[key];
        }
        panel.open = true;
      }
      render();
    }

    function start() {
      panel.open = true;
      document.getElementById('rollout-criteria-heading').focus();
    }

    document.getElementById('rollout-next').addEventListener('click', () => {
      const invalid = criteriaFields.find(field => !field.validity.valid);
      if (invalid) {
        invalid.reportValidity();
        return;
      }
      entry.hidden = false;
      document.getElementById('rollout-entry-heading').focus();
    });
    document.getElementById('rollout-clear').addEventListener('click', () => {
      if (source && !window.confirm('승리 조건과 A/B 입력을 모두 비울까요?')) return;
      restore(null);
      onChange();
      start();
    });
    form.addEventListener('input', event => {
      if (resultSeen && criteriaFields.includes(event.target)) criteriaEdited = true;
      source = source === 'synthetic' ? 'synthetic_edited' : (source ?? 'manual');
      render();
      onChange();
    });
    form.addEventListener('submit', event => event.preventDefault());
    render();

    return {
      current: () => current,
      source: () => source,
      snapshot() {
        if (current) return {record: current};
        if (!source) return {};
        const startedResults = countKeys.some(key => fields[key].value || fields[key].validity.badInput) ||
          fields['design-confirmed'].checked || fields.capacity.value !== 'unknown' || fields.cost.value !== 'unknown';
        if (startedResults) throw Error('A/B 결과를 마저 입력하거나 입력을 비운 뒤 저장해 주세요.');
        return {draft: normalizeCriteria(readCriteria())};
      },
      restore,
      start
    };
  }

  return {normalize, normalizeCriteria, mount, report};
});
