/* Optional local metadata file. No storage, rows, labels, filenames or network. */
(function(root,factory){
 'use strict';
 if(typeof module==='object'&&module.exports)module.exports=factory(require('node:crypto').webcrypto);
 else root.ABColumnProfile=factory(root.crypto);
}(typeof globalThis!=='undefined'?globalThis:this,function(crypto){
 'use strict';
 const MAX_BYTES=8192,FORMAT='ab-column-profile',VERSION=1;
 const roles={aggregate:['arm','success','total','segment'],individual:['arm','subject_id','outcome','segment','observed']};
 const required={aggregate:['arm','success','total'],individual:['arm','subject_id','outcome']};
 function fail(message){throw Error('열 연결 템플릿: '+message);}
 function object(x){return x&&typeof x==='object'&&!Array.isArray(x);}
 function mode(m){if(!Object.hasOwn(roles,m))fail('지원하지 않는 표 종류입니다.');return roles[m];}
 function exactKeys(x,keys){if(!object(x)||Object.keys(x).length!==keys.length||Object.keys(x).some(k=>!keys.includes(k)))fail('허용되지 않은 항목 또는 누락 항목입니다.');}
 function validate(x){
  exactKeys(x,['format','version','mode','roles']);
  if(x.format!==FORMAT||x.version!==VERSION)fail('지원하지 않는 파일 형식입니다.');
  const keys=mode(x.mode);exactKeys(x.roles,keys);
  const seen=new Set();
  for(const k of keys){const d=x.roles[k];if(d===null&&!required[x.mode].includes(k))continue;
   if(typeof d!=='string'||!/^sha256:[0-9a-f]{64}$/.test(d))fail('정확한 소문자 SHA-256 지문이 필요합니다.');
   if(seen.has(d))fail('여러 역할에 같은 지문을 사용할 수 없습니다.');seen.add(d);
  }
  return x;
 }
 function parse(text){
  if(typeof text!=='string'||new TextEncoder().encode(text).length>MAX_BYTES)fail('파일은 8KiB 이하여야 합니다.');
  let x;try{x=JSON.parse(text);}catch(e){fail('올바른 JSON이 아닙니다.');}
  // Reject duplicate JSON object keys before accepting JSON.parse's last-key behavior.
  const tokens=text.match(/"(?:[^"\\]|\\.)*"|[{}\[\]:,]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/g)||[];let i=0;
  function value(){const t=tokens[i++];if(t==='{'){const seen=new Set();if(tokens[i]==='}'){i++;return;}while(i<tokens.length){const key=JSON.parse(tokens[i++]);if(seen.has(key))fail('JSON 항목이 중복됩니다.');seen.add(key);i++;value();if(tokens[i++]==='}')return;}}else if(t==='['){if(tokens[i]===']'){i++;return;}while(i<tokens.length){value();if(tokens[i++]===']')return;}}}
  value();return validate(x);
 }
 function stringify(x){const text=JSON.stringify(validate(x),null,2);parse(text);return text;}
 function decode(buffer){if(buffer.byteLength>MAX_BYTES)fail('파일은 8KiB 이하여야 합니다.');return parse(new TextDecoder('utf-8',{fatal:true}).decode(buffer));}
 async function digest(h){
  if(!crypto?.subtle)fail('안전한 localhost의 WebCrypto SHA-256을 사용할 수 없습니다. 로컬 실행기를 사용하세요.');
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(h));
  return 'sha256:'+Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join('');
 }
 async function fingerprints(headers){
  if(!Array.isArray(headers)||headers.length<3||headers.length>100||headers.some(h=>typeof h!=='string')||new Set(headers).size!==headers.length)fail('현재 CSV 열이 누락되었거나 중복됩니다.');
  const out=await Promise.all(headers.map(digest));if(new Set(out).size!==out.length)fail('열 지문이 중복됩니다.');return out;
 }
 function observation(headers,mapping,m){if(m==='individual'&&headers.some(h=>['observed','관측','관측여부','관측 여부'].includes(h.trim().toLowerCase())&&mapping.observed!==h))fail('현재 CSV의 관측 완료 열을 생략하거나 다른 열로 바꿀 수 없습니다.');}
 async function create(headers,mapping,m){
  const keys=mode(m),ds=await fingerprints(headers),selected={};
  exactKeys(mapping,keys);
  for(const k of keys){const h=mapping[k];if(h===null)selected[k]=null;else {const n=headers.indexOf(h);if(n<0)fail('현재 CSV에 없는 열입니다.');selected[k]=ds[n];}}
  observation(headers,mapping,m);return validate({format:FORMAT,version:VERSION,mode:m,roles:selected});
 }
 async function resolve(profile,headers,m){
  validate(profile);mode(m);if(profile.mode!==m)fail('현재 표 종류와 다릅니다.');
  const ds=await fingerprints(headers),mapping={};
  for(const k of roles[m]){const d=profile.roles[k];if(d===null){mapping[k]=null;continue;}const n=ds.indexOf(d);if(n<0)fail('현재 CSV에 정확히 일치하는 열이 없습니다.');mapping[k]=headers[n];}
  observation(headers,mapping,m);return mapping;
 }
 return {MAX_BYTES,parse,stringify,decode,create,resolve,digest};
}));
