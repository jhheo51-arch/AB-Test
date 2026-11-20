'use strict';
// All fixtures are synthetic. No user data, IDs, or filesystem writes in tests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const engine = require('../engine.js');
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('PASS '+name); }
function near(a,b,tol=1e-12) { assert.ok(Number.isFinite(a) && Math.abs(a-b)<=tol, `${a} != ${b}; tolerance ${tol}`); }
const plan = {randomized:true, independent:true, mature:true, fixedStop:true, alpha:0.05, includeSegments:false, segmentPrespecified:true};
function prep(text,format='aggregate') { return engine.prepare(text,format); }
function run(sa,na,sb,nb,p=plan) { return engine.analyze(prep(`arm,success,total\nA,${sa},${na}\nB,${sb},${nb}`),p); }
function code(p,c) { return p.issues.some(x=>x.code===c); }
function segmented(values,p={}) { return engine.analyze(prep('arm,success,total,segment\n'+values.map(r=>r.join(',')).join('\n')), {...plan,includeSegments:true,...p}); }
function choose(n,k) { let v=1; for(let i=1;i<=k;i++) v=v*(n-i+1)/i; return v; }
function bruteFisher(sa,na,sb,nb) { const k=sa+sb,N=na+nb; const pr=x=>choose(na,x)*choose(nb,k-x)/choose(N,k); let p=0; const observed=pr(sa); for(let x=Math.max(0,k-nb);x<=Math.min(na,k);x++) if(pr(x)<=observed*(1+1e-12)) p+=pr(x); return Math.min(1,p); }

test('UMD browser global / Node API',()=>{
  assert.equal(typeof engine.VERSION,'string');
  for(const k of ['parseTable','prepare','analyze']) assert.equal(typeof engine[k],'function');
  const sandbox={}; vm.runInNewContext(fs.readFileSync(require.resolve('../engine.js'),'utf8'),sandbox);
  assert.equal(sandbox.ABEngine.VERSION,engine.VERSION);
  near(sandbox.ABEngine.analyze(sandbox.ABEngine.prepare('arm,success,total\nA,1,10\nB,5,10','aggregate'),plan).overall.diff,0.4);
});
test('CSV BOM, CRLF, quotes, escaped quotes and quoted newline',()=>{
  const p=engine.parseTable('\uFEFFarm,success,total,segment\r\n"A",1,10,"x,\r\ny""z"\r\nB,2,10,q\r\n');
  assert.deepEqual(p.headers,['arm','success','total','segment']);
  assert.equal(p.rows.length,2); assert.equal(p.rows[0][3],'x,\r\ny"z');
});
test('TSV with quoted tabs and embedded newline',()=>{
  const p=engine.parseTable('arm\tsuccess\ttotal\tsegment\nA\t1\t2\t"s\tt\nu"\nB\t0\t2\tx');
  assert.equal(p.rows[0][3],'s\tt\nu'); assert.equal(p.rows[1][1],'0');
});
test('coded parser exceptions and prepare conversion',()=>{
  for(const [s,c] of [['arm,success,total\nA,"1,10','CSV_UNCLOSED_QUOTE'],['arm,success,total\nA,"1"x,10','CSV_AFTER_QUOTE'],['arm,success,total\nA,1"x,10','CSV_QUOTE'],['','EMPTY_INPUT']]) {
    assert.throws(()=>engine.parseTable(s),e=>e.code===c); assert.ok(code(prep(s),c));
  }
  assert.throws(()=>engine.parseTable(null),e=>e.code==='INPUT_TYPE');
});
test('headers exact, missing, duplicate, unknown; invalid format',()=>{
  assert.ok(code(prep('Arm,success,total\nA,1,2'),'UNKNOWN_HEADER'));
  assert.ok(code(prep('arm,total\nA,2'),'MISSING_HEADER'));
  assert.ok(code(prep('arm,success,total,total\nA,1,2,2'),'DUPLICATE_HEADER'));
  assert.ok(code(prep('arm,success,total\nA,1,2','guess'),'FORMAT'));
});
test('strict integer validation and every invalid row retained as issues',()=>{
  const vals=['1.0','1e2','-1','NaN','Infinity','','9007199254740992'];
  const p=prep('arm,success,total\n'+vals.map(v=>'A,'+v+',10').join('\n')+'\nC,20,10\nB,1,2,extra');
  assert.equal(p.sourceRowCount,9);
  assert.equal(p.issues.filter(x=>x.code==='INVALID_INTEGER').length,7);
  assert.ok(code(p,'INVALID_ARM')); assert.ok(code(p,'SUCCESS_GT_TOTAL')); assert.ok(code(p,'COLUMN_COUNT'));
  assert.equal(engine.analyze(p,plan).status,'invalid');
});
test('aggregate 2 and 4 cells, duplicate cell rejection',()=>{
  assert.equal(prep('arm,success,total\nA,1,10\nB,2,10').cells.length,2);
  assert.ok(code(prep('arm,success,total\nA,1,10\nA,2,20'),'DUPLICATE_CELL'));
  const r=segmented([['A',5,20,'x'],['B',10,20,'x'],['A',10,20,'y'],['B',5,20,'y']]);
  assert.equal(r.overall.A.total,40); assert.equal(r.family.m,4); assert.equal(r.segments.length,2);
});
test('individual aggregation, ID/raw rows never returned',()=>{
  const text='subject_id,arm,outcome,segment,observed\nSECRET_1,A,1,x,1\nSECRET_2,A,0,x,1\nSECRET_3,B,1,x,1\nSECRET_4,B,0,x,1';
  const p=prep(text,'individual'); assert.equal(p.cells.length,2); assert.deepEqual(p.cells[0],{arm:'A',segment:'x',success:1,total:2});
  const s=JSON.stringify([p,engine.analyze(p,plan)]); assert.ok(!s.includes('SECRET_')); assert.ok(!s.includes('subject_id')); assert.ok(!s.includes('rows'));
  const bad=prep('subject_id,arm,outcome,observed\nPRIVATE,A,,0\nPRIVATE,B,2,\n,A,0,1','individual');
  for(const c of ['MISSING_OUTCOME','IMMATURE_OBSERVATION','DUPLICATE_ID','INVALID_OUTCOME','MISSING_ID']) assert.ok(code(bad,c));
  assert.ok(!JSON.stringify(bad).includes('PRIVATE'));
});
test('four assumptions must each be boolean true',()=>{
  for(const key of ['randomized','independent','mature','fixedStop']) for(const val of [false,undefined,1,'true',null]) {
    const r=run(1,10,8,10,{...plan,[key]:val}); assert.equal(r.inference_allowed,false); assert.equal(r.overall.p_raw,null); assert.equal(r.overall.ci,null); assert.equal(r.overall.winner,'not_tested'); near(r.overall.diff,0.7);
  }
});
test('unsupported design, alpha, arm cap and positive denominators',()=>{
  for(const p of [{sequential:true},{clustered:true},{outcomeType:'revenue'},{alpha:0.1}]) assert.equal(run(5,20,10,20,{...plan,...p}).status,'unsupported');
  assert.equal(run(5,200001,10,20).status,'unsupported');
  assert.equal(run(0,0,1,10).inference_allowed,false);
});
test('Fisher known 2x2 golden and small exhaustive combinatorial oracle',()=>{
  near(run(1,10,11,14).overall.p_raw,0.0027594561852200836);
  let n=0;
  for(let na=1;na<=8;na++) for(let nb=1;nb<=8;nb++) for(let sa=0;sa<=na;sa++) for(let sb=0;sb<=nb;sb++) { near(run(sa,na,sb,nb).overall.p_raw,bruteFisher(sa,na,sb,nb),2e-12); n++; }
  console.log('  independent exact-combination comparisons: '+n);
});
test('Wilson and B minus A Newcombe intervals, relative-change boundary',()=>{
  const g=run(10,100,20,100).overall;
  near(g.A.ci[0],0.05522913706067509); near(g.A.ci[1],0.17436566150491345);
  near(g.B.ci[0],0.1333669333310325); near(g.B.ci[1],0.2888291655931589);
  near(g.ci[0],g.diff-Math.sqrt((g.B.rate-g.B.ci[0])**2+(g.A.ci[1]-g.A.rate)**2));
  near(g.ci[1],g.diff+Math.sqrt((g.B.ci[1]-g.B.rate)**2+(g.A.rate-g.A.ci[0])**2));
  near(g.relative_change,1); assert.equal(run(0,10,1,10).overall.relative_change,null);
  const rev=run(20,100,10,100).overall; near(rev.ci[0],-g.ci[1]); near(rev.ci[1],-g.ci[0]);
});
test('zero events, all successes, extreme and maximum arm bounds',()=>{
  for(const [a,n,b,m] of [[0,10,0,10],[10,10,10,10],[0,200000,0,200000],[200000,200000,200000,200000]]) { const g=run(a,n,b,m).overall; near(g.p_raw,1); assert.equal(g.winner,'hold'); }
  assert.equal(run(0,200000,200000,200000).overall.winner,'B');
  const g=run(99900,200000,100100,200000).overall; assert.ok(g.p_raw>0 && g.p_raw<1); near(g.p_raw,run(100100,200000,99900,200000).overall.p_raw,1e-10);
});
test('Holm m=4 and Wald direct difference / accurate normal tail',()=>{
  const r=segmented([['A',20,100,'x'],['B',50,100,'x'],['A',40,100,'y'],['B',20,100,'y']]);
  assert.equal(r.interaction.status,'tested'); near(r.interaction.diff,0.5);
  const se=Math.sqrt((.2*.8+.5*.5+.4*.6+.2*.8)/100);
  near(r.interaction.ci[0],.5-1.959963984540054*se);
  const sorted=r.family.hypotheses.slice().sort((a,b)=>a.p_raw-b.p_raw); let previous=0;
  sorted.forEach((h,i)=>{ previous=Math.max(previous,Math.min(1,(4-i)*h.p_raw)); near(h.p_adjusted,previous); });
  // Independent numerical integration of the standard normal density (Simpson).
  const z=.5/se, steps=10000, h=z/steps; let integral=0;
  for(let i=0;i<=steps;i++) integral+=(i===0||i===steps?1:i%2?4:2)*Math.exp(-((i*h)**2)/2)/Math.sqrt(2*Math.PI);
  near(r.interaction.p_raw,1-2*integral*h/3,2e-13);
});
test('unsupported planned hypotheses stay in Holm as internal p=1 only',()=>{
  const r=segmented([['A',0,100,'x'],['B',5,100,'x'],['A',10,100,'y'],['B',20,100,'y']]);
  assert.equal(r.family.m,4); assert.equal(r.interaction.p_raw,null); assert.equal(r.interaction.p_adjusted,null); assert.equal(r.interaction.winner,'not_tested'); assert.equal(r.status,'limited');
  const hs=r.family.hypotheses.slice().sort((a,b)=>(a.p_raw??1)-(b.p_raw??1)); let prev=0;
  hs.forEach((v,i)=>{prev=Math.max(prev,Math.min(1,(4-i)*(v.p_raw??1))); if(v.supported) near(v.p_adjusted,prev); else assert.equal(v.p_raw,null);});
});
test('post-hoc segment exploration: m=1 overall only',()=>{
  const r=segmented([['A',10,100,'x'],['B',80,100,'x'],['A',50,100,'y'],['B',10,100,'y']],{segmentPrespecified:false});
  assert.equal(r.family.m,1); assert.notEqual(r.overall.p_raw,null); r.segments.forEach(g=>{ assert.equal(g.p_raw,null);assert.equal(g.ci,null);assert.equal(g.winner,'not_tested'); }); assert.equal(r.interaction.p_raw,null);
});
test('missing segment stays overall and blocks all segment inference',()=>{
  const r=segmented([['A',10,100,'x'],['B',20,100,'x'],['A',10,100,'y'],['B',20,100,'y'],['A',3,10,''],['B',2,10,'']]);
  assert.equal(r.overall.A.total,210); assert.equal(r.overall.A.success,23); assert.equal(r.family.m,4); assert.notEqual(r.overall.p_raw,null); assert.ok(code(r,'SEGMENT_INFERENCE_BLOCKED')); r.segments.forEach(g=>assert.equal(g.p_raw,null));
});
test('three segments forbid inference; zero segment arm is limited',()=>{
  const r=segmented([['A',5,10,'x'],['B',6,10,'x'],['A',5,10,'y'],['B',6,10,'y'],['A',5,10,'z'],['B',6,10,'z']]);
  assert.equal(r.inference_allowed,false); assert.equal(r.status,'unsupported');
  const z=segmented([['A',0,0,'x'],['B',6,10,'x'],['A',5,10,'y'],['B',6,10,'y']]); assert.equal(z.status,'limited'); assert.equal(z.family.m,4); assert.equal(z.segments[0].p_raw,null);
});
test('limits: 2 MiB and 50000 rows; large invalid set retains all issues',()=>{
  assert.throws(()=>engine.parseTable('x'.repeat(2*1024*1024+1)),e=>e.code==='FILE_TOO_LARGE');
  assert.throws(()=>engine.parseTable('arm,success,total\n'+'A,0,1\n'.repeat(50001)),e=>e.code==='TOO_MANY_ROWS');
  const lines='subject_id,arm,outcome\n'+Array.from({length:50000},(_,i)=>'SYNTH_'+i+','+(i%2?'A':'B')+',0').join('\n');
  const p=prep(lines,'individual'); assert.equal(p.sourceRowCount,50000); assert.equal(p.issues.length,0); assert.equal(p.cells[0].total,25000);
  const invalid=prep('arm,success,total\n'+'C,x,y\n'.repeat(5000)); assert.equal(invalid.issues.length,19999); // 3 issues/row plus duplicate cells from row 2 onward.
});
console.log(`RESULT: ${passed} smoke groups passed.`);
