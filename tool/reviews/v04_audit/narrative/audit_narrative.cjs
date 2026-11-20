'use strict';
// Synthetic, read-only source audit; writes only beside this script.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const ROOT='C:/Users/Administrator/Downloads/AB_Test_Workspace_v04',OUT=__dirname;
const digest=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
function snapshot(dir){let o={};for(const d of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,d.name);if(d.isDirectory())Object.assign(o,snapshot(p));else if(d.isFile())o[path.relative(ROOT,p).replaceAll('\\','/')]=digest(p);}return o;}
const before=snapshot(ROOT),E=require(path.join(ROOT,'engine.js')),N=require(path.join(ROOT,'narrative.js'));
const BASE={randomized:true,independent:true,mature:true,fixedStop:true,includeSegments:false,segmentPrespecified:true,alpha:.05};
const records=[],failures=[],checks={fisher:0,holm:0,group_semantics:0,arm_swap:0,segment_swap:0,boundary:0};
function check(ok,kind,detail){checks[kind]++;if(!ok)failures.push({kind,detail});}
function choose(n,k){if(k<0||k>n)return 0;let x=1;for(let i=1;i<=k;i++)x=x*(n-i+1)/i;return x;}
function fisher(a,na,b,nb){let probs=[];for(let x=Math.max(0,a+b-nb);x<=Math.min(na,a+b);x++)probs.push([x,choose(na,x)*choose(nb,a+b-x)/choose(na+nb,a+b)]);const observed=probs.find(x=>x[0]===a)[1];return probs.filter(x=>x[1]<=observed*(1+1e-10)).reduce((s,x)=>s+x[1],0);}
function csv(cells,seg){return 'arm,success,total'+(seg?',segment':'')+'\n'+cells.map(c=>[c[0],c[1],c[2],...(seg?[c[3]]:[])].join(',')).join('\n');}
function run(id,input,overrides={},keep=true){let plan={...BASE,...overrides},r=E.analyze(E.prepare(input,'aggregate'),plan);let n={overall:N.group(r,r.overall,'overall'),segments:r.segments.map(g=>N.group(r,g,'segment')),interaction:N.interaction(r)};if(keep)records.push({id,input,plan,result:r,narrative:n});return {r,n};}
function close(a,b){return a===b||(Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<1e-10);}
function validate(id,r,n){if(r.overall){[r.overall,...r.segments].forEach((g,i)=>{let x=i?n.segments[i-1]:n.overall;if(g.inference_allowed){let expected=g.winner==='A'||g.winner==='B'?'SUPERIOR':g.p_raw<=.05&&g.p_adjusted>.05&&r.family.m>1?'HOLM_HOLD':'HOLD';check(x.code===expected,'group_semantics',{id,i,expected,observed:x.code});if(x.code==='SUPERIOR')check(x.headline.startsWith(g.winner),'group_semantics',{id,i,headline:x.headline,winner:g.winner});}});}
if(r.family.hypotheses.length){let h=r.family.hypotheses.map((x,i)=>({...x,i})).sort((a,b)=>(a.p_raw??1)-(b.p_raw??1)||a.i-b.i),v=0;h.forEach((x,i)=>{v=Math.max(v,Math.min(1,(h.length-i)*(x.p_raw??1)));if(x.p_raw!==null)check(close(v,x.p_adjusted),'holm',{id,key:x.key,expected:v,actual:x.p_adjusted});});}}
// Frozen enumeration: all success counts for both denominators 0..5.
for(let na=0;na<=5;na++)for(let nb=0;nb<=5;nb++)for(let a=0;a<=na;a++)for(let b=0;b<=nb;b++){
 let id=`small_${a}_${na}_${b}_${nb}`,input=csv([['A',a,na],['B',b,nb]],false),{r,n}=run(id,input);validate(id,r,n);
 if(na&&nb)check(close(r.overall.p_raw,fisher(a,na,b,nb)),'fisher',{id,expected:fisher(a,na,b,nb),actual:r.overall.p_raw});
 let swapped=run(id+'_swap',csv([['B',a,na],['A',b,nb]],false),{},false);check(close(r.overall.p_raw,swapped.r.overall.p_raw)&&close(r.overall.diff,r.overall.diff===null?null:-swapped.r.overall.diff)&&n.overall.code===swapped.n.overall.code,'arm_swap',{id});
}
// Fixed 5^4 cell success grid includes 0/all and each side of interaction minimum 5.
const counts=[0,4,5,6,10];
for(const a of counts)for(const b of counts)for(const c of counts)for(const d of counts){let cells=[['A',a,10,'x'],['B',b,10,'x'],['A',c,10,'y'],['B',d,10,'y']],id=`segment_${a}_${b}_${c}_${d}`,p={includeSegments:true},q=run(id,csv(cells,true),p);validate(id,q.r,q.n);
const swapA=run(id+'_arm',csv(cells.map(x=>[x[0]==='A'?'B':'A',...x.slice(1)]),true),p,false);
check(close(q.r.overall.p_adjusted,swapA.r.overall.p_adjusted)&&close(q.r.interaction.p_adjusted,swapA.r.interaction.p_adjusted)&&close(q.r.interaction.diff,-swapA.r.interaction.diff)&&q.n.interaction.code===swapA.n.interaction.code,'arm_swap',{id});
const swapS=run(id+'_segment',csv(cells.slice(2).concat(cells.slice(0,2)),true),p,false);
check(close(q.r.overall.p_adjusted,swapS.r.overall.p_adjusted)&&close(q.r.interaction.p_adjusted,swapS.r.interaction.p_adjusted)&&close(q.r.interaction.diff,-swapS.r.interaction.diff)&&q.n.interaction.code===swapS.n.interaction.code&&q.n.segments[0].code===swapS.n.segments[1].code,'segment_swap',{id});
check((q.r.interaction.status==='tested')===[a,b,c,d].every(x=>x===5),'boundary',{id,status:q.r.interaction.status});}
// Additional fixed non-sparse grid: every interaction is supported, including sign reversals.
for(const a of [10,30,50,70,90])for(const b of [10,30,50,70,90])for(const c of [10,30,50,70,90])for(const d of [10,30,50,70,90]){
const cells=[['A',a,100,'x'],['B',b,100,'x'],['A',c,100,'y'],['B',d,100,'y']],id=`dense_${a}_${b}_${c}_${d}`,p={includeSegments:true},q=run(id,csv(cells,true),p);validate(id,q.r,q.n);
const sa=run(id+'_arm',csv(cells.map(x=>[x[0]==='A'?'B':'A',...x.slice(1)]),true),p,false),ss=run(id+'_segment',csv(cells.slice(2).concat(cells.slice(0,2)),true),p,false);
check(close(q.r.interaction.p_adjusted,sa.r.interaction.p_adjusted)&&close(q.r.interaction.diff,-sa.r.interaction.diff)&&q.n.interaction.code===sa.n.interaction.code,'arm_swap',{id});
check(close(q.r.interaction.p_adjusted,ss.r.interaction.p_adjusted)&&close(q.r.interaction.diff,-ss.r.interaction.diff)&&q.n.interaction.code===ss.n.interaction.code&&q.n.segments[0].code===ss.n.segments[1].code,'segment_swap',{id});
check(q.r.interaction.status==='tested'&&q.n.interaction.code===(q.r.interaction.p_adjusted<=.05?'INTERACTION_SUPPORTED':'INTERACTION_HOLD'),'boundary',{id});}
const good='arm,success,total,segment\nA,10,100,x\nB,70,100,x\nA,40,100,y\nB,35,100,y';
const scenarios=[['normal',good,{includeSegments:true}],['posthoc',good,{includeSegments:true,segmentPrespecified:false}],['missing','arm,success,total,segment\nA,10,100,x\nB,20,100,x\nA,10,100,y\nB,20,100,y\nA,1,10,',{includeSegments:true}],['missing_posthoc','arm,success,total,segment\nA,10,100,x\nB,20,100,x\nA,10,100,y\nB,20,100,y\nA,1,10,',{includeSegments:true,segmentPrespecified:false}],['zero_segment','arm,success,total,segment\nA,0,0,x\nB,10,100,x\nA,10,100,y\nB,10,100,y',{includeSegments:true}],['one_segment','arm,success,total,segment\nA,10,100,x\nB,20,100,x',{includeSegments:true}],['three_segments',good+'\nA,5,10,z\nB,5,10,z',{includeSegments:true}],['invalid','arm,success,total\nA,11,10\nB,1,10',{}],['holm','arm,success,total,segment\nA,50,500,x\nB,75,500,x\nA,80,500,y\nB,75,500,y',{includeSegments:true}]];
for(const key of ['randomized','independent','mature','fixedStop'])for(const value of [false,undefined,'true',1])scenarios.push(['flag_'+key+'_'+String(value),good,{includeSegments:true,[key]:value}]);
for(const key of ['sequential','adaptive','repeated','crossover','clustered','sharedCapacity','multiplePolicies'])scenarios.push(['unsupported_'+key,good,{[key]:true}]);
scenarios.push(['alpha',good,{alpha:.1}],['outcome',good,{outcomeType:'continuous'}]);
for(const total of [199999,200000,200001])scenarios.push(['limit_'+total,`arm,success,total\nA,5,${total}\nB,6,${total}`,{}]);
for(const [id,input,p]of scenarios){let q=run(id,input,p);validate(id,q.r,q.n);if(id.startsWith('limit_'))check(q.r.inference_allowed===(Number(id.slice(6))<=200000),'boundary',{id,status:q.r.status});}
const findings=[{id:'N-01',severity:'낮음',category:'부족한 설명 (수학 오류 아님)',repro_id:'missing_posthoc',source:'narrative.js:19-20',observed:'집단 설명 EXPLORATORY가 먼저 반환되어 SEGMENT_INFERENCE_BLOCKED 및 누락 참여자의 전체 포함 사실을 알리지 않음.',expected:'탐색 지위와 별개로 집단 누락이 추가 제한임을 함께 안내. 사전 계획을 확인해도 누락 문제는 남음.'},{id:'N-02',severity:'낮음',category:'부족한 설명 (수학 오류 아님)',repro_id:'zero_segment',source:'narrative.js:21',observed:'실제 EMPTY_SEGMENT_ARM에 대해 GROUP_UNSUPPORTED: 빈 군·집단 수·입력 제한을 포괄 나열. 원인인 x 집단 A 분모 0과 비율 미정의를 직접 밝히지 않음.',expected:'전체 EMPTY_ARM과 구별하면서 해당 집단의 빈 안 및 분모 0을 특정.'},{id:'N-03',severity:'낮음',category:'부정확할 수 있는 범용 문구 (수학 오류 아님)',repro_id:'invalid',source:'narrative.js:30',observed:'잘못된 입력(SUCCESS_GT_TOTAL)에 직접 차이 설명은 INTERACTION_BLOCKED이며 다음 확인에 조건 미확인 상태에서는 기술 통계만 사용하라고 안내. 엔진은 invalid, overall=null로 기술 통계도 제공하지 않음.',expected:'invalid일 때는 입력 수정 전 수치 사용 불가를 직접 안내. group()의 INVALID와 정렬.'}];
const after=snapshot(ROOT),unchanged=JSON.stringify(before)===JSON.stringify(after);
let codes={};for(const r of records)for(const n of [r.narrative.overall,...r.narrative.segments,r.narrative.interaction])codes[n.code]=(codes[n.code]||0)+1;
const summary={synthetic_only:true,mutated_result_objects:0,engine:E.VERSION,narrative:N.VERSION,record_count:records.length,checks,check_count:Object.values(checks).reduce((a,b)=>a+b,0),failure_count:failures.length,failures,source_tree_unchanged:unchanged,source_file_count:Object.keys(before).length,source_hashes_before:before,source_hashes_after:after,codes,findings,limitations:['브라우저 렌더·공유·ZIP 실행은 이번 하위 감사 범위 밖','독립 Fisher 기준은 작은 비세그먼트 셀에 한정; 대규모 p값 정밀도 검증으로 확대하지 않음','interaction 정규 근사 p값의 독립 고정밀 기준은 이번 범위 밖; 문구/부호/경계/교환 불변성만 검증']};
fs.writeFileSync(path.join(OUT,'narrative_results.json'),JSON.stringify({summary,records},null,2));
fs.writeFileSync(path.join(OUT,'narrative_summary.json'),JSON.stringify(summary,null,2));
console.log(JSON.stringify({...summary,source_hashes_before:undefined,source_hashes_after:undefined},null,2));
if(failures.length||!unchanged)process.exitCode=1;
