/* Local-only binary A/B engine. No dependencies, storage, network, or logging. */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ABEngine = factory();
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = '0.2.0';
  const MAX_BYTES = 2 * 1024 * 1024, MAX_ROWS = 50000, MAX_N = 200000;
  const Z = 1.959963984540054;
  function issue(code, row, column, message, severity) {
    return {code: code, row: row == null ? null : row, column: column == null ? null : column,
      message: message, severity: severity || 'error'};
  }
  function fail(code, row, column, message) {
    const e = new Error(message); e.code = code; e.row = row; e.column = column; throw e;
  }
  function byteLength(text) {
    if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(text).length;
    let n = 0;
    for (let i = 0; i < text.length; i++) {
      const c = text.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i + 1 < text.length && text.charCodeAt(i+1) >= 0xdc00 && text.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
    }
    return n;
  }
  function parseTable(text) {
    if (typeof text !== 'string') fail('INPUT_TYPE', null, null, 'Input must be text.');
    if (byteLength(text) > MAX_BYTES) fail('FILE_TOO_LARGE', null, null, 'Input exceeds 2 MiB.');
    text = text.replace(/^\uFEFF/, '');
    if (!text.length) fail('EMPTY_INPUT', 1, null, 'The table is empty.');
    // Detect delimiter only outside quoted fields in the first logical record.
    let quoted = false, commas = 0, tabs = 0;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (c === '"') { if (quoted && text[i+1] === '"') i++; else quoted = !quoted; }
      else if (!quoted) { if (c === '\r' || c === '\n') break; if (c === ',') commas++; if (c === '\t') tabs++; }
    }
    const delim = tabs > commas ? '\t' : ',';
    const records = []; let record = [], field = '', state = 0, line = 1, fieldLine = 1;
    // state 0 unquoted, 1 quoted, 2 closed quote. Never silently repair malformed quotes.
    function pushField() { record.push(field); field = ''; state = 0; fieldLine = line; }
    function pushRecord() {
      pushField(); records.push(record); record = [];
      if (records.length > MAX_ROWS + 1) fail('TOO_MANY_ROWS', line, null, 'Input exceeds 50000 data rows.');
    }
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (state === 1) {
        if (c === '"') { if (text[i+1] === '"') { field += '"'; i++; } else state = 2; }
        else { field += c; if (c === '\n' || (c === '\r' && text[i+1] !== '\n')) line++; }
      } else if (c === delim) pushField();
      else if (c === '\r' || c === '\n') {
        pushRecord(); if (c === '\r' && text[i+1] === '\n') i++; line++; fieldLine = line;
      } else if (c === '"') {
        if (state === 2 || field.length) fail('CSV_QUOTE', line, record.length+1, 'Unexpected quote in unquoted field.');
        state = 1; fieldLine = line;
      } else {
        if (state === 2) fail('CSV_AFTER_QUOTE', line, record.length+1, 'Unexpected character after closing quote.');
        field += c;
      }
    }
    if (state === 1) fail('CSV_UNCLOSED_QUOTE', fieldLine, record.length+1, 'Quoted field is not closed.');
    if (record.length || field.length || state === 2) pushRecord();
    if (!records.length) fail('EMPTY_INPUT', 1, null, 'The table is empty.');
    const headers = records.shift();
    return {headers: headers, rows: records};
  }
  function prepare(text, format) {
    const result = {cells: [], issues: [], format: format, sourceRowCount: 0};
    const issues = result.issues;
    if (format !== 'aggregate' && format !== 'individual') {
      issues.push(issue('FORMAT', null, null, 'Format must be aggregate or individual.')); return result;
    }
    let table;
    try { table = parseTable(text); }
    catch (e) { issues.push(issue(e.code || 'PARSE_ERROR', e.row, e.column, e.code ? e.message : 'Table parsing failed.')); return result; }
    result.sourceRowCount = table.rows.length;
    const required = format === 'aggregate' ? ['arm','success','total'] : ['subject_id','arm','outcome'];
    const allowed = required.concat(format === 'aggregate' ? ['segment'] : ['segment','observed']);
    const h = table.headers, index = Object.create(null);
    h.forEach(function (name, i) {
      if (Object.prototype.hasOwnProperty.call(index, name)) issues.push(issue('DUPLICATE_HEADER', 1, i+1, 'Header is duplicated.'));
      else index[name] = i;
      if (allowed.indexOf(name) < 0) issues.push(issue('UNKNOWN_HEADER', 1, i+1, 'Header is not supported; exact English headers are required.'));
    });
    required.forEach(function (name) { if (index[name] == null) issues.push(issue('MISSING_HEADER', 1, name, 'Required header is missing.')); });
    if (issues.length) return result;
    if (!table.rows.length) issues.push(issue('NO_DATA', 2, null, 'The table has no data rows.'));
    const ids = new Set(), seen = new Set(), cells = new Map();
    function integer(value, row, col) {
      if (!/^\d+$/.test(value) || !Number.isSafeInteger(Number(value))) {
        issues.push(issue('INVALID_INTEGER', row, col, 'Expected a nonnegative safe integer in decimal notation.')); return null;
      }
      return Number(value);
    }
    table.rows.forEach(function (r, ri) {
      const row = ri + 2, before = issues.length;
      if (r.length !== h.length) issues.push(issue('COLUMN_COUNT', row, null, 'Row width does not match the header.'));
      const get = function (key) { return index[key] == null || r[index[key]] == null ? '' : r[index[key]].trim(); };
      const arm = get('arm'), segment = index.segment == null ? null : get('segment');
      if (arm !== 'A' && arm !== 'B') issues.push(issue('INVALID_ARM', row, 'arm', 'Arm must be A or B.'));
      if (index.segment != null && !segment) issues.push(issue('MISSING_SEGMENT', row, 'segment', 'Missing segment remains in overall totals; segment inference is blocked.', 'warning'));
      let success, total;
      if (format === 'aggregate') {
        success = integer(get('success'), row, 'success'); total = integer(get('total'), row, 'total');
        if (success !== null && total !== null && success > total) issues.push(issue('SUCCESS_GT_TOTAL', row, 'success', 'Success exceeds total.'));
        const key = JSON.stringify([arm, segment]);
        if (seen.has(key)) issues.push(issue('DUPLICATE_CELL', row, 'arm', 'An arm/segment cell is duplicated.'));
        seen.add(key);
      } else {
        const id = get('subject_id');
        if (!id) issues.push(issue('MISSING_ID', row, 'subject_id', 'A pseudonymous subject key is required.'));
        else if (ids.has(id)) issues.push(issue('DUPLICATE_ID', row, 'subject_id', 'A subject key is duplicated.'));
        ids.add(id);
        const v = get('outcome');
        if (!v) issues.push(issue('MISSING_OUTCOME', row, 'outcome', 'Missing outcome cannot be treated as zero.'));
        else if (v !== '0' && v !== '1') issues.push(issue('INVALID_OUTCOME', row, 'outcome', 'Outcome must be 0 or 1.'));
        if (index.observed != null && get('observed') !== '1') issues.push(issue('IMMATURE_OBSERVATION', row, 'observed', 'Every observed value must be 1 in this fixed observation path.'));
        success = v === '1' ? 1 : 0; total = 1;
      }
      if (issues.slice(before).some(function (x) { return x.severity === 'error'; })) return;
      const key = JSON.stringify([arm, segment]);
      if (!cells.has(key)) cells.set(key, {arm: arm, segment: segment, success: 0, total: 0});
      const c = cells.get(key); c.success += success; c.total += total;
      if (!Number.isSafeInteger(c.success) || !Number.isSafeInteger(c.total)) issues.push(issue('INTEGER_OVERFLOW', row, 'total', 'Aggregated counts exceed safe integer range.'));
    });
    result.cells = Array.from(cells.values());
    return result;
  }
  function wilson(s, n, z = Z) {
    const p = s/n, zz = z*z, den = 1+zz/n;
    const center = (p+zz/(2*n))/den, half = z*Math.sqrt(p*(1-p)/n+zz/(4*n*n))/den;
    return [Math.max(0, center-half), Math.min(1, center+half)];
  }
  function differenceInterval(a, b, z = Z) {
    const rateA = a.success/a.total, rateB = b.success/b.total;
    const diff = rateB-rateA;
    const rateIntervalA = wilson(a.success, a.total, z);
    const rateIntervalB = wilson(b.success, b.total, z);
    const ci = [
      Math.max(-1, diff-Math.hypot(rateB-rateIntervalB[0], rateIntervalA[1]-rateA)),
      Math.min(1, diff+Math.hypot(rateIntervalB[1]-rateB, rateA-rateIntervalA[0]))
    ];
    return {diff, ci, rateIntervalA, rateIntervalB};
  }
  // Hypergeometric probabilities relative to the mode: recurrence avoids factorial
  // cancellation, overflow, and underflow near the mode, even at n=200000/arm.
  function fisher(sa, na, sb, nb) {
    const k = sa+sb, N = na+nb, lo = Math.max(0, k-nb), hi = Math.min(na, k);
    const mode = Math.max(lo, Math.min(hi, Math.floor((na+1)*(k+1)/(N+2))));
    const logs = new Float64Array(hi-lo+1); logs[mode-lo] = 0;
    for (let x = mode; x < hi; x++) logs[x+1-lo] = logs[x-lo] + Math.log(na-x) + Math.log(k-x) - Math.log(x+1) - Math.log(nb-k+x+1);
    for (let x = mode; x > lo; x--) logs[x-1-lo] = logs[x-lo] + Math.log(x) + Math.log(nb-k+x) - Math.log(na-x+1) - Math.log(k-x+1);
    const threshold = logs[sa-lo] + 1e-10;
    let numerator = 0, denominator = 0;
    for (let i = 0; i < logs.length; i++) {
      const w = Math.exp(logs[i]); denominator += w;
      if (logs[i] <= threshold) numerator += w;
    }
    return Math.max(0, Math.min(1, numerator/denominator));
  }
  // Regularized upper incomplete gamma Q(1/2,x), i.e. erfc(sqrt(x)).
  // Series / continued fraction gives a full precision two-sided normal tail.
  function normalTwoSided(z) {
    const x = z*z/2, a = 0.5;
    if (!Number.isFinite(x)) return 0;
    if (x === 0) return 1;
    const scale = Math.exp(-x+a*Math.log(x)-0.5723649429247001);
    if (x < a+1) {
      let term = 1/a, sum = term, ap = a;
      for (let i = 0; i < 10000; i++) { ap++; term *= x/ap; sum += term; if (Math.abs(term) < Math.abs(sum)*2e-16) break; }
      return Math.max(0, Math.min(1, 1-sum*scale));
    }
    let b = x+1-a, c = 1e300, d = 1/b, h = d;
    for (let i = 1; i < 10000; i++) {
      const an = -i*(i-a); b += 2; d = an*d+b; if (Math.abs(d) < 1e-300) d = 1e-300;
      c = b+an/c; if (Math.abs(c) < 1e-300) c = 1e-300;
      d = 1/d; const delta = d*c; h *= delta; if (Math.abs(delta-1) < 2e-16) break;
    }
    return Math.max(0, Math.min(1, scale*h));
  }
  function group(cells) {
    const g = {A: {success: 0, total: 0, rate: null}, B: {success: 0, total: 0, rate: null},
      diff: null, relative_change: null, ci: null, p_raw: null, p_adjusted: null, winner: 'not_tested',
      inference_allowed: false, status: 'descriptive'};
    cells.forEach(function (c) { g[c.arm].success += c.success; g[c.arm].total += c.total; });
    ['A','B'].forEach(function (a) { if (g[a].total > 0) g[a].rate = g[a].success/g[a].total; });
    if (g.A.rate !== null && g.B.rate !== null) {
      g.diff = g.B.rate-g.A.rate;
      if (g.A.rate !== 0) g.relative_change = g.diff/g.A.rate;
    }
    return g;
  }
  function infer(g) {
    const a = g.A, b = g.B, intervals = differenceInterval(a, b);
    a.ci = intervals.rateIntervalA; b.ci = intervals.rateIntervalB;
    g.ci = intervals.ci;
    g.p_raw = fisher(a.success,a.total,b.success,b.total);
    g.inference_allowed = true; g.status = 'tested';
  }
  function analyze(prepared, plan) {
    plan = plan || {};
    const out = {version: VERSION, status: 'descriptive', inference_allowed: false, overall: null,
      segments: [], interaction: {diff: null, ci: null, p_raw: null, p_adjusted: null, winner: 'not_tested', status: 'not_requested'},
      family: {m: 0, method: 'Holm', alpha: 0.05, hypotheses: []}, issues: [],
      interval_note: 'Nominal 95% Wilson / Newcombe intervals; not Holm simultaneous intervals and not dual to Fisher exact tests.',
      assumptions: {randomized: plan.randomized === true, independent: plan.independent === true,
        mature: plan.mature === true, fixedStop: plan.fixedStop === true, basis: 'user_confirmed'},
      segmentPrespecified: plan.segmentPrespecified === true};
    if (!prepared || !Array.isArray(prepared.cells) || !Array.isArray(prepared.issues)) {
      out.status = 'invalid'; out.issues.push(issue('INVALID_PREPARED', null, null, 'Expected a prepare result.')); return out;
    }
    // Only copy safe issue metadata, never arbitrary input properties or raw values.
    out.issues = prepared.issues.map(function (e) { return issue(e.code, e.row, e.column, e.message, e.severity); });
    if (out.issues.some(function (e) { return e.severity !== 'warning'; })) { out.status = 'invalid'; return out; }
    const cells = [], seen = new Set();
    prepared.cells.forEach(function (c) {
      if (!c || (c.arm !== 'A' && c.arm !== 'B') || !Number.isSafeInteger(c.success) || !Number.isSafeInteger(c.total) || c.success < 0 || c.total < c.success || (c.segment != null && typeof c.segment !== 'string')) {
        out.issues.push(issue('INVALID_CELL', null, null, 'Prepared cell has invalid counts, arm, or segment.')); return;
      }
      const key = JSON.stringify([c.arm, c.segment == null ? null : c.segment]);
      if (seen.has(key)) out.issues.push(issue('DUPLICATE_CELL', null, null, 'Prepared cells contain duplicate arm/segment.'));
      seen.add(key); cells.push({arm: c.arm, segment: c.segment == null ? null : c.segment, success: c.success, total: c.total});
    });
    if (!cells.length) out.issues.push(issue('NO_DATA', null, null, 'No valid cells.'));
    if (out.issues.some(function (e) { return e.severity !== 'warning'; })) { out.status = 'invalid'; return out; }
    const overall = out.overall = group(cells);
    const names = Array.from(new Set(cells.map(function (c) { return c.segment; }).filter(function (s) { return s !== null && s !== ''; })));
    const missingSegment = cells.some(function (c) { return c.segment === ''; }) || (names.length > 0 && cells.some(function (c) { return c.segment === null; }));
    if (plan.includeSegments === true) out.segments = names.map(function (s, i) {
      const g = group(cells.filter(function (c) { return c.segment === s; }));
      g.label = 'G'+(i+1); g.exploratory = plan.segmentPrespecified !== true; return g;
    });
    let allowed = ['randomized','independent','mature','fixedStop'].every(function (k) { return plan[k] === true; });
    if (!allowed) out.issues.push(issue('ASSUMPTIONS_UNCONFIRMED', null, null, 'All four inference assumptions require explicit boolean true.', 'warning'));
    if (plan.alpha != null && plan.alpha !== 0.05) { allowed = false; out.issues.push(issue('UNSUPPORTED_ALPHA', null, null, 'This path supports only alpha=0.05.', 'warning')); }
    if (overall.A.total <= 0 || overall.B.total <= 0) { allowed = false; out.issues.push(issue('EMPTY_ARM', null, 'total', 'Overall denominators must both be positive.', 'warning')); }
    if (overall.A.total > MAX_N || overall.B.total > MAX_N || !Number.isSafeInteger(overall.A.total) || !Number.isSafeInteger(overall.B.total)) {
      allowed = false; out.issues.push(issue('ARM_LIMIT', null, 'total', 'Each arm must have at most 200000 participants.', 'warning'));
    }
    // Reject explicitly declared designs outside the supported fixed independent binary path.
    const unsupportedFlags = ['sequential','adaptive','repeated','crossover','clustered','sharedCapacity','multiplePolicies'];
    if (unsupportedFlags.some(function (k) { return plan[k] === true; }) || (plan.outcomeType != null && plan.outcomeType !== 'binary')) {
      allowed = false; out.issues.push(issue('UNSUPPORTED_DESIGN', null, null, 'Declared design or outcome is outside this inference path.', 'warning'));
    }
    if (names.length > 2) { allowed = false; out.issues.push(issue('TOO_MANY_SEGMENTS', null, 'segment', 'More than two segments: descriptive statistics only.', 'warning')); }
    const wantsSegments = plan.includeSegments === true && plan.segmentPrespecified === true;
    const familyFour = wantsSegments && names.length === 2;
    out.family.m = familyFour ? 4 : 1;
    if (plan.includeSegments === true && plan.segmentPrespecified !== true) out.issues.push(issue('POSTHOC_SEGMENTS', null, 'segment', 'Post-hoc segment results are descriptive only; only the overall planned comparison uses m=1.', 'warning'));
    let segmentAllowed = allowed && familyFour && !missingSegment;
    if (missingSegment && plan.includeSegments === true) out.issues.push(issue('SEGMENT_INFERENCE_BLOCKED', null, 'segment', 'Missing segment values are included overall but block segment inference.', 'warning'));
    if (wantsSegments && names.length !== 2) out.issues.push(issue('SEGMENT_COUNT_UNSUPPORTED', null, 'segment', 'The confirmatory segment family requires exactly two groups.', 'warning'));
    if (!allowed) { out.status = out.issues.some(function (e) { return ['ARM_LIMIT','TOO_MANY_SEGMENTS','UNSUPPORTED_DESIGN','UNSUPPORTED_ALPHA'].indexOf(e.code) >= 0; }) ? 'unsupported' : 'descriptive'; return out; }
    infer(overall); out.inference_allowed = true; out.status = 'ok';
    if (segmentAllowed) out.segments.forEach(function (g) {
      if (g.A.total > 0 && g.B.total > 0) infer(g);
      else { g.status = 'unsupported'; out.issues.push(issue('EMPTY_SEGMENT_ARM', null, g.label, 'Both segment denominators must be positive.', 'warning')); }
    });
    if (familyFour) {
      out.interaction.status = 'unsupported';
      const gs = out.segments;
      if (gs.length === 2 && gs.every(function (g) { return g.diff !== null; })) out.interaction.diff = gs[0].diff-gs[1].diff;
      const enough = segmentAllowed && gs.every(function (g) { return [g.A,g.B].every(function (c) { return c.success >= 5 && c.total-c.success >= 5; }); });
      if (enough) {
        let variance = 0; gs.forEach(function (g) { [g.A,g.B].forEach(function (c) { variance += c.rate*(1-c.rate)/c.total; }); });
        const se = Math.sqrt(variance), d = out.interaction.diff;
        out.interaction.ci = [Math.max(-2,d-Z*se),Math.min(2,d+Z*se)];
        out.interaction.p_raw = normalTwoSided(d/se); out.interaction.status = 'tested';
      } else out.issues.push(issue('INTERACTION_UNSUPPORTED', null, null, 'Direct risk-difference inference requires complete prespecified groups and at least five successes and failures in each of four cells.', 'warning'));
      if (!segmentAllowed || out.segments.some(function (g) { return !g.inference_allowed; }) || !enough) out.status = 'limited';
    } else if (plan.includeSegments === true) out.status = 'limited';
    const hs = [{key: 'overall', target: overall}];
    if (familyFour) { hs.push({key: 'G1', target: out.segments[0]}, {key: 'G2', target: out.segments[1]}, {key: 'interaction', target: out.interaction}); }
    const ranked = hs.map(function (h, i) { return {h: h, index: i, p: h.target.p_raw === null ? 1 : h.target.p_raw}; }).sort(function (a,b) { return a.p-b.p || a.index-b.index; });
    let cumulative = 0;
    ranked.forEach(function (r, rank) {
      cumulative = Math.max(cumulative, Math.min(1,(hs.length-rank)*r.p));
      if (r.h.target.p_raw !== null) {
        r.h.target.p_adjusted = cumulative;
        const d = r.h.target.diff;
        // Interaction direction is not a treatment winner.
        r.h.target.winner = r.h.key === 'interaction' ? (cumulative <= 0.05 && d !== 0 ? (d > 0 ? 'G1' : 'G2') : 'hold') : (cumulative <= 0.05 && d !== 0 ? (d > 0 ? 'B' : 'A') : 'hold');
      }
    });
    out.family.hypotheses = hs.map(function (h) { return {key: h.key, supported: h.target.p_raw !== null, p_raw: h.target.p_raw, p_adjusted: h.target.p_adjusted, included: true}; });
    return out;
  }
  return {VERSION: VERSION, parseTable: parseTable, prepare: prepare, analyze: analyze, differenceInterval};
}));
