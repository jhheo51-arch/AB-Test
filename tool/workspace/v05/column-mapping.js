/* Local-only column mapping. No I/O, logging, storage, eval, or automatic confirmation.
 * inspect(text, format) -> {headers, rowsPreview, rowCount, canonical, suggestions}
 * convert(text, format, mapping, armValues?) -> canonical CSV string
 * mapping: target -> exact source header string | null. Passing a mapping is the
 * caller's explicit confirmation that unselected source columns may be omitted.
 * armValues: {A: exactSourceLabel, B: exactSourceLabel}; defaults to A / B.
 * Semantic validation (counts, outcomes, IDs, observations) remains Engine.prepare.
 */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./engine.js'));
  else root.ABColumnMapping = factory(root.ABEngine);
}(typeof globalThis !== 'undefined' ? globalThis : this, function (Engine) {
  'use strict';
  const MAX_BYTES = 2 * 1024 * 1024, MAX_ROWS = 50000;
  const own = function (o, key) { return Object.prototype.hasOwnProperty.call(o, key); };
  const aliases = {
    arm: ['arm', 'variant', 'group', '실험군', '그룹', '군', '실험그룹', '배정군'],
    success: ['success', 'converted', 'conversions', '전환수', '전환 수', '성공수', '성공 수'],
    total: ['total', 'participants', '전체수', '전체 수', '참여자수', '참여자 수', '대상자수', '대상자 수'],
    segment: ['segment', 'cohort', '세그먼트', '코호트', '고객군'],
    subject_id: ['subject_id', 'user_id', 'customer_id', '사용자id', '사용자_id', '고객id', '고객_id', '대상자id', '사용자 식별자', '고객 식별자'],
    outcome: ['outcome', 'converted', 'conversion', '전환', '전환여부', '전환 여부', '결과'],
    observed: ['observed', '관측', '관측여부', '관측 여부']
  };
  function fail(code, row, column, message) {
    const messages = {
      FORMAT: '집계형(aggregate) 또는 개인형(individual)을 선택하세요.',
      ENGINE_REQUIRED: 'ABEngine을 먼저 불러와야 합니다.',
      FILE_TOO_LARGE: '입력 또는 변환 결과가 2 MiB를 초과합니다.',
      TOO_MANY_ROWS: '데이터는 50,000행 이하여야 합니다.',
      TOO_MANY_HEADERS: '열은 100개 이하여야 합니다.',
      MAPPING_REQUIRED: '열 연결을 명시적으로 확인해야 합니다.',
      INVALID_TARGET: '지원하지 않는 대상 열입니다.',
      INVALID_HEADER: '원본에 있는 정확한 열 이름 또는 null을 선택하세요.',
      DUPLICATE_HEADER: '원본 열 이름이 중복되어 연결할 수 없습니다.',
      MISSING_MAPPING: '필수 열 연결이 누락되었습니다.',
      DUPLICATE_SOURCE: '같은 원본 열을 여러 대상에 연결할 수 없습니다.',
      OBSERVED_MAPPING_REQUIRED: '원본 observed 열은 observed에 그대로 연결해야 합니다. 관측 여부를 생략할 수 없습니다.',
      INVALID_ARM_VALUES: 'A와 B에 서로 다른 비어 있지 않은 원본 군 이름을 지정하세요.',
      SAME_ARM_LABELS: 'A와 B의 원본 군 이름은 서로 달라야 합니다.',
      COLUMN_COUNT: '데이터 행의 열 수가 머리글과 다릅니다.',
      INVALID_ARM: '군 값이 지정한 A 또는 B의 원본 값과 정확히 일치하지 않습니다.'
    };
    const e = new Error(messages[code] || message); e.code = code; e.row = row; e.column = column; throw e;
  }
  function fields(format) {
    if (format === 'aggregate') return {required: ['arm', 'success', 'total'], optional: ['segment']};
    if (format === 'individual') return {required: ['subject_id', 'arm', 'outcome'], optional: ['segment', 'observed']};
    fail('FORMAT', null, null, 'Format must be aggregate or individual.');
  }
  function byteLength(text) {
    if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(text).length;
    let n = 0;
    for (let i = 0; i < text.length; i++) {
      const c = text.charCodeAt(i);
      if (c < 128) n++;
      else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i + 1 < text.length && text.charCodeAt(i + 1) >= 0xdc00 && text.charCodeAt(i + 1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
    }
    return n;
  }
  function parse(text) {
    if (!Engine || typeof Engine.parseTable !== 'function') fail('ENGINE_REQUIRED', null, null, 'ABEngine.parseTable is required.');
    // Engine errors propagate unchanged, including byte/row limits and malformed CSV.
    const table = Engine.parseTable(text);
    if (table.headers.length > 100) fail('TOO_MANY_HEADERS', 1, null, 'Headers exceed 100.');
    if (byteLength(text) > MAX_BYTES) fail('FILE_TOO_LARGE', null, null, 'Input exceeds 2 MiB.');
    if (table.rows.length > MAX_ROWS) fail('TOO_MANY_ROWS', null, null, 'Input exceeds 50000 data rows.');
    return table;
  }
  function inspect(text, format) {
    const spec = fields(format), allowed = spec.required.concat(spec.optional), table = parse(text);
    const headers = table.headers, suggestions = {}, used = new Set();
    allowed.forEach(function (target) {
      // Exact canonical names take priority. Ambiguous aliases are never selected.
      let matches = headers.filter(function (h) { return h === target; });
      if (matches.length === 0) matches = headers.filter(function (h) { return aliases[target].indexOf(h.trim().toLowerCase()) >= 0; });
      if (matches.length === 1 && !used.has(matches[0])) { suggestions[target] = matches[0]; used.add(matches[0]); }
    });
    return {
      headers: headers.slice(),
      rowsPreview: table.rows.slice(0, 5).map(function (r) { return r.slice(); }),
      rowCount: table.rows.length,
      canonical: new Set(headers).size === headers.length && headers.every(function (h) { return allowed.indexOf(h) >= 0; }) && spec.required.every(function (h) { return headers.indexOf(h) >= 0; }),
      suggestions: suggestions
    };
  }
  function quote(value) { return /[",\r\n\t]/.test(value) ? '"' + value.replace(/"/g, '""') + '"' : value; }
  function convert(text, format, mapping, armValues) {
    const spec = fields(format), allowed = spec.required.concat(spec.optional), table = parse(text);
    if (!mapping || typeof mapping !== 'object' || Array.isArray(mapping)) fail('MAPPING_REQUIRED', null, null, 'An explicitly confirmed mapping is required.');
    Object.keys(mapping).forEach(function (target) {
      if (allowed.indexOf(target) < 0) fail('INVALID_TARGET', 1, null, 'Mapping target is not supported.');
      if (mapping[target] !== null && typeof mapping[target] !== 'string') fail('INVALID_HEADER', 1, target, 'Source selection must be an exact header string or null.');
    });
    const headers = table.headers;
    if (format === 'individual' && headers.indexOf('observed') >= 0 && (!own(mapping, 'observed') || mapping.observed !== 'observed')) fail('OBSERVED_MAPPING_REQUIRED', 1, 'observed', 'Original observed must remain mapped.');
    if (new Set(headers).size !== headers.length) fail('DUPLICATE_HEADER', 1, null, 'Source headers must be unique.');
    const targets = [], indices = [], used = new Set();
    allowed.forEach(function (target) {
      const source = own(mapping, target) ? mapping[target] : null;
      if (source === null) {
        if (spec.required.indexOf(target) >= 0) fail('MISSING_MAPPING', 1, target, 'Required source selection is missing.');
        return;
      }
      const index = headers.indexOf(source);
      if (index < 0) fail('INVALID_HEADER', 1, target, 'Selected source header does not exist.');
      if (used.has(source)) fail('DUPLICATE_SOURCE', 1, target, 'A source column cannot be selected more than once.');
      used.add(source); targets.push(target); indices.push(index);
    });
    const labels = armValues === undefined ? {A: 'A', B: 'B'} : armValues;
    if (!labels || typeof labels !== 'object' || Array.isArray(labels) || !own(labels, 'A') || !own(labels, 'B') || typeof labels.A !== 'string' || typeof labels.B !== 'string' || labels.A.length === 0 || labels.B.length === 0 || Object.keys(labels).some(function (k) { return k !== 'A' && k !== 'B'; })) fail('INVALID_ARM_VALUES', null, 'arm', 'Arm values must contain two nonempty exact string labels A and B.');
    if (labels.A === labels.B) fail('SAME_ARM_LABELS', null, 'arm', 'Arm labels must differ.');
    const armIndex = targets.indexOf('arm');
    const output = [targets.join(',')];
    table.rows.forEach(function (row, i) {
      if (row.length !== headers.length) fail('COLUMN_COUNT', i + 2, null, 'Row width does not match the header.');
      const values = indices.map(function (index) { return row[index]; });
      const arm = values[armIndex];
      if (arm !== labels.A && arm !== labels.B) fail('INVALID_ARM', i + 2, 'arm', 'Arm value does not match either explicitly selected label.');
      values[armIndex] = arm === labels.A ? 'A' : 'B';
      output.push(values.map(quote).join(','));
    });
    const csv = output.join('\n');
    if (byteLength(csv) > MAX_BYTES) fail('FILE_TOO_LARGE', null, null, 'Canonical CSV exceeds 2 MiB.');
    // Reparse also verifies canonical output row cap and valid quoting.
    parse(csv);
    return csv;
  }
  return {inspect: inspect, convert: convert};
}));
