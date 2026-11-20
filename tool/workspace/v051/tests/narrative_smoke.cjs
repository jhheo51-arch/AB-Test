'use strict';
const assert=require('node:assert/strict'),E=require('../engine.js'),N=require('../narrative.js');
const plan={randomized:true,independent:true,mature:true,fixedStop:true,includeSegments:false,segmentPrespecified:true,alpha:.05};
const run=(csv,p={})=>E.analyze(E.prepare(csv,'aggregate'),{...plan,...p});
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const passedTests=[],r02Cases=[];
let passed=0;function test(name,f){f();passed++;passedTests.push(name);console.log('PASS '+name);}
function evidence(id,csv,p,check){
 const r=run(csv,p),before=JSON.stringify(r);
 const explanations=check(r);
 assert.equal(JSON.stringify(r),before,'narrative must not mutate engine results');
 r02Cases.push({id,input:csv,plan:{...plan,...p},engine_result:r,explanations,result_unchanged:true});
}
const two='arm,success,total\nA,10,100\nB,30,100';
const segmented='arm,success,total,segment\nA,50,500,new\nB,75,500,new\nA,80,500,existing\nB,75,500,existing';
test('whole hold reason from actual results',()=>{let r=run('arm,success,total\nA,130,1000\nB,150,1000');assert.equal(N.group(r,r.overall,'overall').code,'HOLD');});
test('B superior remains statistical not application approval',()=>{let r=run(two),n=N.group(r,r.overall,'overall');assert.equal(n.code,'SUPERIOR');assert.match(n.headline,/B/);assert.match(n.next,/別|별도로/);});
test('A superior is not biased to B',()=>{let r=run('arm,success,total\nA,30,100\nB,10,100');assert.match(N.group(r,r.overall,'overall').headline,/A/);});
test('Holm reversal explained from actual raw and adjusted p',()=>{let r=run(segmented,{includeSegments:true});assert.equal(N.group(r,r.segments[0],'segment').code,'HOLM_HOLD');});
test('unconfirmed assumptions do not create an inference',()=>{let r=run(two,{randomized:false});assert.equal(N.group(r,r.overall,'overall').code,'ASSUMPTIONS');assert.equal(N.interaction(r).code,'INTERACTION_BLOCKED');});
test('arm cap is unsupported not a winner',()=>{let r=run('arm,success,total\nA,100,200001\nB,101,200001');assert.equal(N.group(r,r.overall,'overall').code,'UNSUPPORTED');});
test('posthoc descriptive group is labelled exploratory',()=>{let r=run(segmented,{includeSegments:true,segmentPrespecified:false});assert.equal(N.group(r,r.segments[0],'segment').code,'EXPLORATORY');});
test('missing segment blocks group inference not overall counts',()=>{let r=run('arm,success,total,segment\nA,10,100,new\nB,20,100,new\nA,5,50,\nA,5,50,old\nB,10,50,old',{includeSegments:true});assert.equal(N.group(r,r.segments[0],'segment').code,'MISSING_SEGMENT');});
test('empty group arm has separate explanation',()=>{let r=run('arm,success,total,segment\nA,0,0,x\nB,10,100,x\nA,10,100,y\nB,10,100,y',{includeSegments:true});assert.equal(N.group(r,r.segments[0],'segment').code,'GROUP_UNSUPPORTED');});
test('insufficient interaction information does not imply equality',()=>{let r=run('arm,success,total,segment\nA,1,20,x\nB,4,20,x\nA,2,20,y\nB,4,20,y',{includeSegments:true});assert.equal(N.interaction(r).code,'INTERACTION_UNSUPPORTED');});
test('actual interaction hold is not proof of no difference',()=>{let r=run(segmented,{includeSegments:true}),n=N.interaction(r);assert.equal(n.code,'INTERACTION_HOLD');assert.match(n.body,/증명은 아니/);});
test('supported direct difference is not an A or B treatment winner',()=>{let r=run('arm,success,total,segment\nA,10,100,x\nB,70,100,x\nA,40,100,y\nB,35,100,y',{includeSegments:true});assert.equal(N.interaction(r).code,'INTERACTION_SUPPORTED');assert.match(N.interaction(r).body,/별도 판단/);});
test('unrequested interaction stays unrequested',()=>{let r=run(two);assert.equal(N.interaction(r).code,'INTERACTION_NOT_REQUESTED');});
test('invalid input produces no invented comparison',()=>{let r=run('arm,success,total\nA,110,100\nB,1,100');assert.equal(N.group(r,r.overall,'overall').code,'INVALID');});
test('context missing values never infer audience',()=>{let h=N.context({});assert.match(h,/설명 미기록/);assert.match(h,/추정하지 않음/);});
test('all free context values HTML escaped',()=>{let h=N.context({policyA:'<img src=x onerror=1>',policyB:'</script>',purpose:'<iframe>',audience:'A&B'});assert(!h.includes('<img'));assert(!h.includes('</script>'));assert(h.includes('&lt;img'));assert(h.includes('A&amp;B'));});
test('explanation card escapes arbitrary text',()=>{let h=N.card({code:'X',headline:'<script>',body:'<img>',next:'<iframe>'});assert(!h.includes('<script>'));assert(h.includes('&lt;script&gt;'));});
test('zero overall denominator is not falsely called unknown design',()=>{let r=run('arm,success,total\nA,0,0\nB,1,10');assert.equal(N.group(r,r.overall,'overall').code,'EMPTY_ARM');});
test('R02 N01 posthoc and missing segment constraints both remain explicit',()=>{
 evidence('N01_missing_posthoc','arm,success,total,segment\nA,10,100,x\nB,20,100,x\nA,10,100,y\nB,20,100,y\nA,1,10,',{includeSegments:true,segmentPrespecified:false},r=>{
  assert.equal(r.inference_allowed,true);assert.equal(r.overall.A.total,210);assert.equal(r.overall.A.success,21);assert.equal(r.overall.B.total,200);
  for(const code of ['POSTHOC_SEGMENTS','SEGMENT_INFERENCE_BLOCKED'])assert(r.issues.some(i=>i.code===code));
  return r.segments.map(g=>{const n=N.group(r,g,'segment');assert.equal(g.p_raw,null);assert.equal(n.code,'EXPLORATORY');assert.match(n.body,/사전성/);assert.match(n.body,/누락된 참여자는 전체에 포함/);assert.match(n.body,/집단별 검정은 제한/);assert.match(n.next,/사전 계획이 확인되어도 결측 제한은 남/);assert.match(n.next,/참여자를 제외하지/);assert.match(N.card(n),/data-reason="EXPLORATORY"/);return n;});
 });
});
for(const [id,a,b] of [['A',0,100],['B',100,0],['A_B',0,0]])test('R02 N02 exact empty segment arm '+id,()=>{
 evidence('N02_empty_'+id,`arm,success,total,segment\nA,${a?10:0},${a},x\nB,${b?10:0},${b},x\nA,10,100,y\nB,10,100,y`,{includeSegments:true},r=>{
  assert.equal(r.inference_allowed,true);assert(r.overall.A.total>0&&r.overall.B.total>0);assert(r.issues.some(i=>i.code==='EMPTY_SEGMENT_ARM'));
  const g=r.segments[0],n=N.group(r,g,'segment');assert.equal(n.code,'GROUP_UNSUPPORTED');assert.equal(g.p_raw,null);
  for(const arm of ['A','B']){if(g[arm].total===0){assert.equal(g[arm].rate,null);assert(n.body.includes(arm+' 분모가 0'));}else assert(!n.body.includes(arm+' 분모가 0'));}
  assert.match(n.body,/성공 비율은 정의되지 않/);assert.match(n.next,/없는 자료를 만들어 넣지/);assert.match(N.card(n),/data-reason="GROUP_UNSUPPORTED"/);
  const other=N.group(r,r.segments[1],'segment');assert.equal(r.segments[1].inference_allowed,true);assert.notEqual(other.code,'GROUP_UNSUPPORTED');return [n,other];
 });
});
for(const [id,csv,issue] of [
 ['counts','arm,success,total\nA,11,10\nB,1,10','SUCCESS_GT_TOTAL'],
 ['header','arm,success\nA,1\nB,1','MISSING_HEADER'],
 ['parse','arm,success,total\nA,"1,10','CSV_UNCLOSED_QUOTE']
])test('R02 N03 invalid '+id+' requires input correction not descriptive statistics',()=>{
 evidence('N03_invalid_'+id,csv,{},r=>{
  assert.equal(r.status,'invalid');assert.equal(r.overall,null);assert(r.issues.some(i=>i.code===issue));
  const n=N.interaction(r);assert.equal(n.code,'INTERACTION_BLOCKED');assert.match(n.body,/유효한 수치 결과가 없/);assert.match(n.body,/사용할 수치가 없/);assert.match(n.next,/먼저 고친 뒤 다시 분석/);assert.match(n.next,/수치를 판단에 사용하지/);assert(!JSON.stringify(n).includes('기술 통계'));assert.match(N.card(n),/data-reason="INTERACTION_BLOCKED"/);
  assert.equal(N.group(r,r.overall,'overall').code,'INVALID');return [n,N.group(r,r.overall,'overall')];
 });
});
test('R02 valid unconfirmed assumptions retain descriptive-statistics guidance',()=>{
 evidence('N03_valid_assumptions_control',two,{randomized:false},r=>{assert.notEqual(r.overall,null);assert.notEqual(r.status,'invalid');const n=N.interaction(r);assert.equal(n.code,'INTERACTION_BLOCKED');assert.match(n.next,/기술 통계만 사용/);return [n];});
});
console.log('RESULT '+passed+' narrative groups passed.');
if(process.argv.includes('--evidence')){
 const root=path.resolve(__dirname,'..');
 const files=['narrative.js','engine.js','tests/narrative_smoke.cjs'];
 const hashes=Object.fromEntries(files.map(file=>[file,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex')]));
 const report={task:'R02',generated_at:new Date().toISOString(),runtime:process.version,command:'node tests/narrative_smoke.cjs --evidence',status:'passed',passed,failed:0,tests:passedTests,actual_engine_cases:r02Cases,source_sha256:hashes,reason_code_compatibility:{N01:'EXPLORATORY preserved; compound body adds missing-segment restriction.',N02:'GROUP_UNSUPPORTED preserved; exact zero-denominator arm comes only from g.A.total/g.B.total.',N03:'INTERACTION_BLOCKED preserved; invalid/no-overall input gets correction-first wording.'},scope_note:'Actual local prepare/analyze results only; no new statistics in narrative. No browser or independent statistical audit claimed.'};
 fs.writeFileSync(path.join(root,'R02_VERIFICATION.json'),JSON.stringify(report,null,2)+'\n');
 console.log('EVIDENCE R02_VERIFICATION.json');
}
