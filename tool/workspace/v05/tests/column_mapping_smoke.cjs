'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const Engine = require('../engine.js');
const M = require('../column-mapping.js');
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('PASS ' + name); }
function error(code, fn) { assert.throws(fn, e => e.code === code); }
const aggregate = {arm: 'arm', success: 'success', total: 'total'};
const individual = {subject_id: 'subject_id', arm: 'arm', outcome: 'outcome', segment: 'segment', observed: 'observed'};

test('exact schema, canonical identity, header-only detection', () => {
  const info = M.inspect('total,arm,success,segment\n2,A,1,x', 'aggregate');
  assert.deepEqual(Object.keys(info).sort(), ['canonical', 'headers', 'rowCount', 'rowsPreview', 'suggestions']);
  assert.equal(info.canonical, true);
  assert.equal(M.inspect('arm,success,total,extra\nA,1,2,x', 'aggregate').canonical, false);
  assert.equal(M.inspect('arm,success\nA,1', 'aggregate').canonical, false);
  assert.equal(M.inspect('arm,arm,success,total\nA,A,1,2', 'aggregate').canonical, false);
  assert.equal(M.inspect('ARM,success,total\nA,1,2', 'aggregate').canonical, false);
  assert.equal(M.inspect('arm,success,total\nX,not-a-count,2', 'aggregate').canonical, true);
});
test('explicit English aliases and Korean suggestions, no automatic confirmation', () => {
  assert.deepEqual(M.inspect('variant,converted,participants,cohort\nA,1,2,x', 'aggregate').suggestions,
    {arm: 'variant', success: 'converted', total: 'participants', segment: 'cohort'});
  const text = '실험군,전환 수,참여자 수,코호트\n대조군,1,2,신규\n실험군,2,3,기존';
  const s = M.inspect(text, 'aggregate');
  assert.equal(s.canonical, false);
  assert.deepEqual(s.suggestions, {arm: '실험군', success: '전환 수', total: '참여자 수', segment: '코호트'});
  error('MAPPING_REQUIRED', () => M.convert(text, 'aggregate'));
  const csv = M.convert(text, 'aggregate', s.suggestions, {A: '대조군', B: '실험군'});
  assert.equal(csv, 'arm,success,total,segment\nA,1,2,신규\nB,2,3,기존');
  assert.deepEqual(Engine.prepare(csv, 'aggregate').issues, []);
});
test('quoted commas, quotes, CRLF, tabs and newlines preserve every selected value', () => {
  const text = 'subject_id,arm,outcome,segment,observed\r\n"id,\"\"one\"\"",A,1,"line1\r\nline2",1\r\n"id\ttwo",B,0,"a,b",1';
  const csv = M.convert(text, 'individual', individual);
  assert.deepEqual(Engine.parseTable(csv), Engine.parseTable(text));
  assert.deepEqual(Engine.prepare(csv, 'individual').issues, []);
});
test('explicit selection alone may omit extras; outcomes and whitespace never recoded', () => {
  const text = 'subject_id,arm,outcome,secret\nu1,A,yes,private\nu2,B, 0 ,private2';
  const csv = M.convert(text, 'individual', {subject_id: 'subject_id', arm: 'arm', outcome: 'outcome', observed: null});
  assert.equal(csv, 'subject_id,arm,outcome\nu1,A,yes\nu2,B, 0 ');
  assert.equal(Engine.prepare(csv, 'individual').issues.some(x => x.code === 'INVALID_OUTCOME'), true);
});
test('missing, invalid, duplicate selections and duplicate source headers rejected', () => {
  const text = 'arm,success,total\nA,1,2';
  error('MISSING_MAPPING', () => M.convert(text, 'aggregate', {arm: 'arm', success: 'success'}));
  error('MISSING_MAPPING', () => M.convert(text, 'aggregate', {...aggregate, arm: null}));
  error('DUPLICATE_SOURCE', () => M.convert(text, 'aggregate', {...aggregate, total: 'success'}));
  error('INVALID_HEADER', () => M.convert(text, 'aggregate', {...aggregate, total: 'missing'}));
  error('INVALID_HEADER', () => M.convert(text, 'aggregate', {...aggregate, total: undefined}));
  error('INVALID_TARGET', () => M.convert(text, 'aggregate', {...aggregate, typo: null}));
  error('DUPLICATE_HEADER', () => M.convert('arm,success,total,total\nA,1,2,2', 'aggregate', aggregate));
  error('COLUMN_COUNT', () => M.convert('arm,success,total\nA,1,2,extra', 'aggregate', aggregate));
  error('COLUMN_COUNT', () => M.convert('arm,success,total\nA,1', 'aggregate', aggregate));
});
test('exact explicit arm mapping, unknown and missing arms rejected', () => {
  const text = 'variant,converted,participants\ncontrol,1,2\ntreatment,2,3';
  const map = {arm: 'variant', success: 'converted', total: 'participants'};
  error('INVALID_ARM', () => M.convert(text, 'aggregate', map));
  assert.equal(M.convert(text, 'aggregate', map, {A: 'control', B: 'treatment'}), 'arm,success,total\nA,1,2\nB,2,3');
  error('SAME_ARM_LABELS', () => M.convert(text, 'aggregate', map, {A: 'x', B: 'x'}));
  for (const labels of [null, {A: '', B: 'b'}, {A: 'a'}, {A: 1, B: 2}]) error('INVALID_ARM_VALUES', () => M.convert(text, 'aggregate', map, labels));
  for (const value of ['', 'C', 'a', ' A ']) error('INVALID_ARM', () => M.convert('arm,success,total\n' + value + ',1,2', 'aggregate', aggregate));
});
test('parser errors propagate unchanged; format validation', () => {
  for (const text of ['', 'arm,success,total\n"A,1,2', 'arm,success,total\n"A"x,1,2']) {
    let original; try { Engine.parseTable(text); } catch (e) { original = e; }
    for (const fn of [() => M.inspect(text, 'aggregate'), () => M.convert(text, 'aggregate', aggregate)]) {
      assert.throws(fn, e => e.code === original.code && e.row === original.row && e.column === original.column && e.message === original.message);
    }
  }
  error('FORMAT', () => M.inspect('a', 'other'));
  error('FORMAT', () => M.convert('a', 'other', {}));
  error('INPUT_TYPE', () => M.inspect(null, 'aggregate'));
});
test('preview is only first five rows; no full individual ID list or data logging', () => {
  const text = 'subject_id,arm,outcome\n' + Array.from({length: 9}, (_, i) => 'private-id-' + i + ',' + (i % 2 ? 'B' : 'A') + ',1').join('\n');
  const info = M.inspect(text, 'individual');
  assert.equal(info.rowCount, 9); assert.equal(info.rowsPreview.length, 5);
  assert.equal(JSON.stringify(info).includes('private-id-5'), false);
  assert.equal(own(info, 'rows'), false);
  function own(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }
});
test('50000-row boundary accepted, 50001 rejected before conversion', () => {
  const text = 'arm,success,total\n' + Array(50000).fill('A,0,1').join('\n');
  assert.equal(M.inspect(text, 'aggregate').rowCount, 50000);
  assert.equal(Engine.parseTable(M.convert(text, 'aggregate', aggregate)).rows.length, 50000);
  error('TOO_MANY_ROWS', () => M.inspect(text + '\nB,0,1', 'aggregate'));
  error('TOO_MANY_ROWS', () => M.convert(text + '\nB,0,1', 'aggregate', aggregate));
});
test('2 MiB UTF-8 input boundary and post-conversion expansion limit', () => {
  const cap = 2 * 1024 * 1024;
  const prefix = 'arm,success,total,segment\nA,0,1,';
  const atCap = prefix + 'x'.repeat(cap - Buffer.byteLength(prefix));
  assert.equal(Buffer.byteLength(M.convert(atCap, 'aggregate', {...aggregate, segment: 'segment'})), cap);
  error('FILE_TOO_LARGE', () => M.inspect(atCap + 'x', 'aggregate'));
  error('FILE_TOO_LARGE', () => M.convert(atCap + 'x', 'aggregate', {...aggregate, segment: 'segment'}));
  error('FILE_TOO_LARGE', () => M.inspect(prefix + '한'.repeat(Math.ceil(cap / 3)), 'aggregate'));
  // Short source headers expand to longer canonical headers, pushing output past cap.
  const short = 'a,b,c,d\nA,0,1,';
  const expands = short + 'x'.repeat(cap - Buffer.byteLength(short));
  error('FILE_TOO_LARGE', () => M.convert(expands, 'aggregate', {arm: 'a', success: 'b', total: 'c', segment: 'd'}));
});
test('browser UMD executes with CSP-style no eval/Function and UTF-8 fallback', () => {
  const sandbox = {ABEngine: Engine, console: {log() { throw new Error('Unexpected logging'); }}};
  vm.createContext(sandbox, {codeGeneration: {strings: false, wasm: false}});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../column-mapping.js'), 'utf8'), sandbox);
  const csv = sandbox.ABColumnMapping.convert('arm,success,total,segment\nA,1,2,한😀', 'aggregate', {...aggregate, segment: 'segment'});
  assert.equal(csv, 'arm,success,total,segment\nA,1,2,한😀');
  assert.equal(sandbox.ABColumnMapping.inspect(csv, 'aggregate').canonical, true);
});
test('header cap and mandatory original observed preservation', () => {
  const hundred = ['arm', 'success', 'total', ...Array.from({length: 97}, (_, i) => 'extra' + i)].join(',');
  assert.equal(M.inspect(hundred, 'aggregate').headers.length, 100);
  error('TOO_MANY_HEADERS', () => M.inspect(hundred + ',extra101', 'aggregate'));
  error('TOO_MANY_HEADERS', () => M.convert(hundred + ',extra101', 'aggregate', aggregate));
  const text = 'subject_id,arm,outcome,observed,other\nu1,A,1,0,1';
  const map = {subject_id: 'subject_id', arm: 'arm', outcome: 'outcome'};
  for (const selection of [{}, {observed: null}, {observed: 'other'}]) {
    error('OBSERVED_MAPPING_REQUIRED', () => M.convert(text, 'individual', {...map, ...selection}));
  }
  const csv = M.convert(text, 'individual', {...map, observed: 'observed'});
  assert.equal(Engine.prepare(csv, 'individual').issues.some(x => x.code === 'IMMATURE_OBSERVATION'), true);
});
console.log('column_mapping_smoke: ' + passed + ' tests passed');
