/* User assertions only: never independent validation of experiment execution. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ABConditions=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const KEYS=['randomized','independent','mature','fixedStop','segmentPrespecified'],MAX_EVIDENCE=1000;
const IDS={randomized:'randomized',independent:'independent',mature:'mature',fixedStop:'fixed-stop',segmentPrespecified:'segment-prespecified'};
const LABELS={randomized:'무작위 배정',independent:'분석 단위의 독립',mature:'개인별 관측 완료',fixedStop:'사전에 정한 고정 종료',segmentPrespecified:'집단 기준의 사전 지정'};
function empty(){return Object.fromEntries(KEYS.map(k=>[k,{status:'unknown',evidence:'',origin:'user_statement'}]));}
function normalize(x){
 if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).length!==KEYS.length)throw Error('조건 기록이 유효하지 않습니다.');
 const out={};for(const k of KEYS){const v=x[k];if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).sort().join(',')!=='evidence,origin,status'||!['yes','no','unknown'].includes(v.status)||typeof v.evidence!=='string'||v.evidence.length>MAX_EVIDENCE||!['user_statement','legacy_user_confirmation','legacy_unconfirmed','synthetic_assumption'].includes(v.origin))throw Error('조건 상태·근거가 유효하지 않습니다: '+k);
 if(v.origin==='legacy_user_confirmation'&&(v.status!=='yes'||v.evidence!=='' )||v.origin==='legacy_unconfirmed'&&(v.status!=='unknown'||v.evidence!==''))throw Error('구형 조건 기록이 일치하지 않습니다.');out[k]={status:v.status,evidence:v.evidence,origin:v.origin};}return out;
}
function legacy(plan){const out=empty();for(const k of KEYS){if(typeof plan[k]!=='boolean')throw Error('구형 설계 상태가 유효하지 않습니다.');out[k]={status:plan[k]?'yes':'unknown',evidence:'',origin:plan[k]?'legacy_user_confirmation':'legacy_unconfirmed'};}return out;}
function booleans(x){const n=normalize(x);return Object.fromEntries(KEYS.map(k=>[k,n[k].status==='yes']));}
return {KEYS,IDS,LABELS,MAX_EVIDENCE,empty,normalize,legacy,booleans};
});
