/* Shared storage contract. Storage limits never relax statistical inference gates. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory(require('./lineage.js'),require('./design.js'),require('./conditions.js'));else root.ABProject=factory(root.ABLineage,root.ABDesign,root.ABConditions);})(typeof globalThis!=='undefined'?globalThis:this,function(Lineage,Design,Conditions){
'use strict';
const MAX_BYTES=8*1024*1024,MAX_CSV_BYTES=2*1024*1024,MAX_CELLS=50000;
const bytes=x=>new TextEncoder().encode(x).length;
const cell=x=>{const s=String(x??'');return /[",\r\n\t]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
function csv(cells){if(!cells.length)return '';const segmented=cells.some(c=>c.segment!==null&&c.segment!==undefined);return 'arm,success,total'+(segmented?',segment':'')+'\n'+cells.map(c=>[c.arm,c.success,c.total,...(segmented?[c.segment??'']:[])].map(cell).join(',')).join('\n');}
function normalize(x){
 if(!x||typeof x!=='object'||x.format!=='ab-local-project'||![2,3,4,5,6,7].includes(x.version)||!Array.isArray(x.cells)||x.cells.length>MAX_CELLS||!x.plan||typeof x.plan!=='object'||Array.isArray(x.plan))throw Error('이 버전의 프로젝트 파일이 아닙니다.');
 const p={},bools=['randomized','independent','mature','fixedStop','includeSegments','segmentPrespecified'];
 for(const k of bools){if(typeof x.plan[k]!=='boolean')throw Error('설계 상태가 유효하지 않습니다.');p[k]=x.plan[k];}
 const conditions=x.version===7?Conditions.normalize(x.conditions):Conditions.legacy(p);
 const projected=Conditions.booleans(conditions);
 if(x.version===7)for(const k of Conditions.KEYS)if(p[k]!==projected[k])throw Error('조건 기록과 분석 계획이 일치하지 않습니다: '+k);
 Object.assign(p,projected);
 for(const k of ['purpose','metric','window','policyA','policyB','audience']){
  const v=k==='audience'&&x.version===2&&x.plan[k]===undefined?'':x.plan[k];
  if(typeof v!=='string'||v.length>(k==='audience'?300:1500))throw Error('계획 필드가 유효하지 않습니다.');p[k]=v;
 }
 if(x.plan.alpha!==undefined&&x.plan.alpha!==.05)throw Error('현재 분석 계획은 alpha=0.05만 지원합니다.');
 if(['sequential','adaptive','repeated','crossover','clustered','sharedCapacity','multiplePolicies'].some(k=>x.plan[k]===true)||(x.plan.outcomeType!==undefined&&x.plan.outcomeType!=='binary'))throw Error('선언한 분석 설계를 이 프로젝트 형식으로 바꾸어 복원하지 않습니다.');
 p.alpha=.05;
 const seen=new Set(),sums={A:0,B:0};
 const cells=x.cells.map(c=>{
  if(!c||!['A','B'].includes(c.arm)||!Number.isSafeInteger(c.success)||!Number.isSafeInteger(c.total)||c.success<0||c.total<c.success||c.segment!=null&&typeof c.segment!=='string')throw Error('저장된 집계가 유효하지 않습니다.');
  const segment=c.segment??null,key=JSON.stringify([c.arm,segment]);if(seen.has(key))throw Error('중복된 군·집단 집계입니다.');seen.add(key);sums[c.arm]+=c.total;
  if(!Number.isSafeInteger(sums[c.arm]))throw Error('군별 합계가 안전한 정수 저장 범위를 벗어났습니다.');
  return {arm:c.arm,segment,success:c.success,total:c.total};
 });
 const table=csv(cells);if(bytes(table)>MAX_CSV_BYTES)throw Error('복원할 집계 표가 2MiB를 넘습니다. 내용을 자르지 않고 저장을 중단합니다.');
 const kind=x.source_kind??'project';if(typeof kind!=='string'||kind.length>80)throw Error('자료 출처 표기가 유효하지 않습니다.');if(x.source_digest!=null&&(typeof x.source_digest!=='string'||!/^([a-fA-F0-9]{64})$/.test(x.source_digest)))throw Error('원천 해시 형식이 유효하지 않습니다.');
 const result={format:'ab-local-project',version:7,conditions,source_kind:kind,synthetic:x.synthetic===true||String(x.source_kind||'').startsWith('synthetic'),source_digest:typeof x.source_digest==='string'?x.source_digest:null,plan:p,cells,decision:'',revisit:'',engine_version:typeof x.engine_version==='string'?x.engine_version:null};
 const j=x.version>=4?x.judgment:{direction:'',checks:''};
 if(!j||typeof j!=='object'||Array.isArray(j)||!['','review_a','review_b','keep','defer','more_data'].includes(j.direction)||typeof j.checks!=='string'||j.checks.length>1500)throw Error('판단 방향·확인 조건이 유효하지 않습니다.');
 result.judgment={direction:j.direction,checks:j.checks};
 result.lineage=x.version>=5?Lineage.normalize(x.lineage):Lineage.legacy(x.source_digest);
 if(x.version>=5&&result.lineage.current&&result.source_digest!==result.lineage.current.digest)throw Error('현재 입력 해시의 중복 기록이 일치하지 않습니다.');
 for(const k of ['decision','revisit']){if(x[k]!==undefined&&(typeof x[k]!=='string'||x[k].length>1500))throw Error('판단 기록이 유효하지 않습니다.');result[k]=x[k]??'';}
 result.design=x.version>=6?Design.normalize(x.design):null;
  if(result.design)for(const k of ['purpose','metric','window','policyA','policyB','audience'])if(result.design.fields[k].value!==p[k])throw Error('설계 기록과 분석 맥락이 일치하지 않습니다: '+k);
  return result;
}
function stringify(x){const text=JSON.stringify(normalize(x),null,2);if(bytes(text)>MAX_BYTES)throw Error('저장 파일이 8MiB를 넘습니다. 내용을 자르지 않고 저장을 중단합니다.');return text;}
function parse(text){if(typeof text!=='string'||bytes(text)>MAX_BYTES)throw Error('프로젝트 파일은 UTF-8 8MiB 이하여야 합니다.');const result=normalize(JSON.parse(text));if(bytes(JSON.stringify(result))>MAX_BYTES)throw Error('프로젝트 파일이 너무 큽니다.');return result;}
return {VERSION:'0.7',MAX_BYTES,MAX_CSV_BYTES,MAX_CELLS,normalize,stringify,parse,csv};
});
