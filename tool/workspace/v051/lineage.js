/* Typed local hash records. Digests are not proof of authenticity or anonymity. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ABLineage=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const recordKinds=['analysis_csv_utf8','restored_aggregate_csv_utf8'];
function digest(v){if(typeof v!=='string'||!/^([a-fA-F0-9]{64})$/.test(v))throw Error('SHA-256 기록 형식이 유효하지 않습니다.');return v;}
function keys(o,allowed){if(!o||typeof o!=='object'||Array.isArray(o)||Object.keys(o).some(k=>!allowed.includes(k)))throw Error('해시 계보의 필드가 유효하지 않습니다.');}
function record(r){if(r===null)return null;keys(r,['kind','digest']);if(!recordKinds.includes(r.kind))throw Error('계산 입력 해시의 종류가 유효하지 않습니다.');return {kind:r.kind,digest:digest(r.digest)};}
function empty(){return {version:1,algorithm:'SHA-256',origin:{kind:'unknown',digest:null},previous:null,current:null,transformation:{name:'none',version:'0.5.1'}};}
function legacy(oldDigest){const x=empty();if(oldDigest!==undefined&&oldDigest!==null)x.origin={kind:'legacy_untyped',digest:digest(oldDigest)};return x;}
function normalize(x){
 keys(x,['version','algorithm','origin','previous','current','transformation']);if(x.version!==1||x.algorithm!=='SHA-256')throw Error('지원하는 해시 계보 형식이 아닙니다.');keys(x.origin,['kind','digest']);
 if(!['unknown','input_text_utf8','legacy_untyped'].includes(x.origin.kind))throw Error('원본 해시의 종류가 유효하지 않습니다.');
 const origin={kind:x.origin.kind,digest:x.origin.kind==='unknown'?null:digest(x.origin.digest)};if(origin.kind==='unknown'&&x.origin.digest!==null)throw Error('종류 미확인 해시에 값을 붙이지 않습니다.');
 const previous=record(x.previous),current=record(x.current);keys(x.transformation,['name','version']);
 if(!['none','identity','column_mapping','fixed_sentence','aggregate_restore'].includes(x.transformation.name)||x.transformation.version!=='0.5.1')throw Error('지원하는 변환 기록이 아닙니다.');
 if((current===null)!==(x.transformation.name==='none'))throw Error('계산 입력과 변환 기록이 일치하지 않습니다.');
 return {version:1,algorithm:'SHA-256',origin,previous,current,transformation:{name:x.transformation.name,version:x.transformation.version}};
}
function build(rawDigest,canonicalDigest,transform,restored){
 const x=empty();x.origin=restored?normalize(restored).origin:{kind:'input_text_utf8',digest:digest(rawDigest)};
 x.previous=restored?normalize(restored).current:null;
 x.current={kind:restored?'restored_aggregate_csv_utf8':'analysis_csv_utf8',digest:digest(canonicalDigest)};x.transformation={name:restored?'aggregate_restore':transform,version:'0.5.1'};
 return normalize(x);
}
return {VERSION:'1',empty,legacy,normalize,build};
});
