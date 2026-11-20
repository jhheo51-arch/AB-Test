'use strict';
// Read-only engine verification through prepare/analyze; no private helper access.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const enginePath = path.join(__dirname, '..', 'engine.js');
const referencePath = path.join(__dirname, 'golden_reference.json');
const engine = require(enginePath);
const fixture = JSON.parse(fs.readFileSync(referencePath, 'utf8'));
const ABS = 1e-10, REL = 1e-7;
const plan = {randomized:true, independent:true, mature:true, fixedStop:true,
  includeSegments:false, segmentPrespecified:true, alpha:0.05};
const failures = [], metrics = {};
function check(row, field, actual, expected, p = false) {
  let pass, absolute_error = null, relative_error = null;
  let tolerance = 'exact';
  if (typeof expected === 'number') {
    pass = typeof actual === 'number' && Number.isFinite(actual);
    if (pass) {
      absolute_error = Math.abs(actual - expected);
      if (expected !== 0) relative_error = absolute_error / Math.abs(expected);
      if (p && expected > 0 && expected < ABS) {
        tolerance = 'relative<=1e-7; positive required';
        pass = actual > 0 && relative_error <= REL;
      } else if (p && expected === 0) {
        tolerance = 'binary64 zero only; not mathematical zero'; pass = actual === 0;
      } else { tolerance = 'absolute<=1e-10'; pass = absolute_error <= ABS; }
      const m = metrics[field] || (metrics[field] = {count:0, max_absolute_error:0,
        max_relative_error:0, max_tiny_p_relative_error:0});
      m.count++;
      m.max_absolute_error = Math.max(m.max_absolute_error, absolute_error);
      if (relative_error !== null) m.max_relative_error = Math.max(m.max_relative_error, relative_error);
      if (p && expected > 0 && expected < ABS) m.max_tiny_p_relative_error = Math.max(m.max_tiny_p_relative_error, relative_error);
    }
  } else pass = actual === expected;
  const result = {field, actual:actual === undefined ? null : actual, expected,
    pass, tolerance, absolute_error, relative_error};
  row.checks.push(result);
  if (!pass) failures.push({section:row.section, id:row.id, ...result});
}
function interval(row, field, actual, expected) {
  if (expected === null) return check(row, field, actual, null);
  check(row, field+'.length', Array.isArray(actual) ? actual.length : null, 2);
  expected.forEach((v,i) => check(row, field+'['+i+']', actual && actual[i], v));
}
function run(input, segmented) {
  const groups = segmented ? [input.g1,input.g2] : [input];
  const lines = ['arm,success,total'+(segmented ? ',segment' : '')];
  groups.forEach((g,i) => ['a','b'].forEach(a => lines.push(
    [a.toUpperCase(),g[a+'_success'],g[a+'_total']].join(',')+(segmented ? ',G'+(i+1) : ''))));
  return engine.analyze(engine.prepare(lines.join('\n'),'aggregate'), {...plan,includeSegments:segmented});
}
// Independent definition: adjusted p_i = max_{p_j <= p_i in stable order}
// min(1, (m-rank_j)*p_j). Not imported/copied from the engine.
function independentHolm(values) {
  const order = values.map((p,i)=>({p,i})).sort((a,b)=>a.p-b.p || a.i-b.i);
  return values.map((_,i) => {
    const stop = order.findIndex(x=>x.i===i);
    return Math.min(1, Math.max(...order.slice(0,stop+1).map((x,j)=>(values.length-j)*x.p)));
  });
}
function familyChecks(row,out,segmented) {
  const targets = segmented ? [out.overall,...out.segments,out.interaction] : [out.overall];
  const keys = segmented ? ['overall','G1','G2','interaction'] : ['overall'];
  check(row,'family.m',out.family.m,keys.length);
  check(row,'family.method',out.family.method,'Holm');
  check(row,'family.alpha',out.family.alpha,0.05);
  check(row,'family.hypotheses.length',out.family.hypotheses.length,keys.length);
  const adjusted = independentHolm(targets.map(t=>t.p_raw === null ? 1 : t.p_raw));
  keys.forEach((key,i) => {
    const h = out.family.hypotheses[i] || {};
    const target = targets[i];
    check(row,`family.${key}.key`,h.key,key);
    check(row,`family.${key}.included`,h.included,true);
    check(row,`family.${key}.supported`,h.supported,target.p_raw !== null);
    check(row,`family.${key}.p_raw`,h.p_raw,target.p_raw,true);
    const expectedAdjusted = target.p_raw === null ? null : adjusted[i];
    check(row,`family.${key}.p_adjusted`,h.p_adjusted,expectedAdjusted,true);
    check(row,`target.${key}.p_adjusted`,target.p_adjusted,expectedAdjusted,true);
    const winner = target.p_raw === null ? 'not_tested' :
      adjusted[i] <= 0.05 && target.diff !== 0 ?
        (key === 'interaction' ? (target.diff > 0 ? 'G1' : 'G2') : (target.diff > 0 ? 'B' : 'A')) : 'hold';
    check(row,`target.${key}.winner`,target.winner,winner);
  });
  row.family_actual = out.family;
}
function makeRow(section,c) { return {section,id:c.id,input:c.input,checks:[]}; }
const groups = fixture.cases.map(c => {
  const row = makeRow('cases',c), out = run(c.input,false), e = c.expected;
  row.engine_status = out.status;
  check(row,'status',out.status,'ok');
  check(row,'inference_allowed',out.inference_allowed,true);
  check(row,'fisher_p',out.overall.p_raw,e.fisher_p,true);
  interval(row,'wilson_a',out.overall.A.ci,e.wilson_a);
  interval(row,'wilson_b',out.overall.B.ci,e.wilson_b);
  interval(row,'newcombe_diff_ci',out.overall.ci,e.newcombe_diff_ci);
  check(row,'diff',out.overall.diff,e.diff);
  familyChecks(row,out,false);
  row.pass = row.checks.every(x=>x.pass); return row;
});
const interactions = fixture.interaction_cases.map(c => {
  const row = makeRow('interaction_cases',c), out = run(c.input,true), e = c.expected;
  row.engine_status = out.status; row.engine_issues = out.issues;
  row.engine_interaction = out.interaction;
  const armLimit = out.issues.some(x=>x.code==='ARM_LIMIT');
  row.blocked_by_public_api_limit = armLimit;
  const expectedApiLimit = ['a','b'].some(a=>c.input.g1[a+'_total']+c.input.g2[a+'_total']>200000);
  row.expected_public_api_limit = expectedApiLimit;
  if (expectedApiLimit) {
    row.validation_scope = 'public_api_boundary_only_no_numeric_comparison';
    row.diagnosis = '원래 입력과 수학 기준은 변경하지 않음. 전체 군별 합 400000은 계약 상한 200000 초과이므로 수치 대조가 아니라 추론 차단을 검증. 최초 비교 실패는 ENGINE_REFERENCE_INITIAL_FAILURE.json에 보존.';
    row.unexercised_mathematical_reference = e;
    check(row,'public_limit.issue',armLimit,true);
    check(row,'public_limit.status',out.status,'unsupported');
    check(row,'public_limit.inference_allowed',out.inference_allowed,false);
    check(row,'public_limit.overall_p',out.overall.p_raw,null);
    check(row,'public_limit.interaction_p',out.interaction.p_raw,null);
    check(row,'public_limit.interaction_adjusted_p',out.interaction.p_adjusted,null);
    check(row,'public_limit.interaction_winner',out.interaction.winner,'not_tested');
    check(row,'public_limit.no_holm_executed',out.family.hypotheses.length,0);
    row.pass=row.checks.every(x=>x.pass);return row;
  }
  row.validation_scope = e.supported ? 'numeric_comparison' : 'information_condition_gate';
  row.diagnosis = null;
  check(row,'within_public_api_limit',armLimit,false);
  check(row,'interaction.supported',out.interaction.status==='tested',e.supported);
  check(row,'interaction.diff',out.interaction.diff,e.diff);
  interval(row,'interaction.ci',out.interaction.ci,e.ci);
  check(row,'interaction.p_raw',out.interaction.p_raw,e.p_raw,true);
  check(row,'status',out.status,e.supported ? 'ok' : 'limited');
  check(row,'interaction.holm_input_p',out.interaction.p_raw === null ? 1 : out.interaction.p_raw,e.holm_input_p,true);
  if (!armLimit) familyChecks(row,out,true);
  else row.family_validation = 'not_exercised: API returned before inference and Holm';
  row.pass = row.checks.every(x=>x.pass); return row;
});
const holm = fixture.holm_cases.map(c => {
  const row = makeRow('holm_cases_independent_algorithm_only',c);
  const values = c.input.p_values.map((p,i)=>c.input.unsupported_indices.includes(i) ? 1 : p);
  const adjusted = independentHolm(values);
  row.engine_api_exercised = false;
  adjusted.forEach((p,i)=>{
    check(row,`p_adjusted[${i}]`,p,c.expected.p_adjusted[i],true);
    check(row,`reject[${i}]`,p<=fixture.alpha,c.expected.reject[i]);
  });
  row.pass = row.checks.every(x=>x.pass); return row;
});
function summary(rows) { return {total:rows.length,passed:rows.filter(x=>x.pass).length,failed:rows.filter(x=>!x.pass).length}; }
const countRow = {section:'coverage',id:'expected_fixture_counts',checks:[]};
check(countRow,'cases.count',groups.length,224);
check(countRow,'interaction_cases.count',interactions.length,11);
check(countRow,'holm_cases.count',holm.length,8);
const hash = p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const report = {
  status:failures.length ? 'FAIL' : 'PASS', generated_at:new Date().toISOString(),
  command:'node tests/compare_reference.cjs', node_version:process.version, engine_version:engine.VERSION,
  provenance:{engine_sha256:hash(enginePath),golden_reference_sha256:hash(referencePath)},
  scope:{api:'prepare(text, aggregate) -> analyze(prepared, explicit plan)',
    engine_modified:false,private_helpers_exported_or_called:false,
    arbitrary_holm_fixtures:'8개는 독립 알고리즘 대 fixture 대조만 수행. 임의 p를 공개 API에 주입하지 않았으며 엔진 8개 직접 통과로 주장하지 않음.',
    actual_engine_holm:'224개 m=1 및 공개 API가 허용한 상호작용 10개 m=4의 실제 family와 대상 p_adjusted/winner를 독립 Holm 계산으로 검증. 원 p는 이 검증 축에서 엔진 출력 사용.',
    limits:['상호작용 large는 전체 군별 합 400000으로 API 상한 200000 초과. 입력·수학 기준을 바꾸지 않고 경계 차단 시험으로 분류. 수치 대조하지 않았으며 최초 실패는 별도 보존.',
      'SE와 z는 공개 반환 필드가 아니므로 직접 대조하지 않음; 반환 diff/ci/p/support 대조.',
      'underflow 기준 0은 binary64 0만 허용; 수학적 확률 0 또는 임의 정밀도 검증을 의미하지 않음.',
      '파서 전체, UI, 실제 무작위배정/독립성/관측성숙/고정중단 및 실무 효용 검증은 아님.']},
  tolerances:{absolute:ABS,tiny_positive_p_relative:REL,tiny_threshold:ABS,positive_reference_zero_forbidden:true,underflow_zero:'exact binary64 zero'},
  summary:{cases:summary(groups),interaction_cases:summary(interactions),holm_independent_only:summary(holm),
    interaction_numeric:summary(interactions.filter(x=>x.validation_scope==='numeric_comparison')),
    interaction_information_gates:summary(interactions.filter(x=>x.validation_scope==='information_condition_gate')),
    interaction_api_boundary:summary(interactions.filter(x=>x.validation_scope==='public_api_boundary_only_no_numeric_comparison')),
    actual_engine_family:{m1:groups.length,m4:interactions.filter(x=>!x.blocked_by_public_api_limit).length},
    failed_checks:failures.length}, metrics,coverage:countRow,failures,
  cases:groups,interaction_cases:interactions,holm_cases_independent_algorithm_only:holm
};
fs.writeFileSync(path.join(__dirname,'ENGINE_REFERENCE_VERIFICATION.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,summary:report.summary,failures:report.failures},null,2));
process.exitCode = failures.length ? 1 : 0;
