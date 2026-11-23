'use strict';
/* Optional local column-profile UI; never part of a project, report or data lineage. */
function currentMapping(){return Object.fromEntries([...document.querySelectorAll('[data-map-target]')].map(e=>[e.dataset.mapTarget,e.value||null]));}
function updateArmGuidance(){
 let node=$('#arm-guidance');if(!node){node=document.createElement('p');node.id='arm-guidance';node.className='note';$('#mapping-fields').after(node);}
 const general='A/B는 정책 설명이 아니라 원본 군 열에 있는 정확한 값입니다. 대소문자·공백을 임의로 바꾸지 마세요. 예: 원본 값이 control / treatment이면 A=control, B=treatment로 직접 지정합니다. 추천은 제한된 열 이름 별칭일 뿐 의미·무작위배정 인증이 아닙니다. 세 군 이상이면 행을 버리지 말고 원본과 실험 범위를 확인하세요.';
 try{const table=ABEngine.parseTable(mappingDraft.raw),h=$('#map-arm')?.value,n=table.headers.indexOf(h);const values=n<0?[]:[...new Set(table.rows.map(r=>r[n]))];node.textContent=general+' 현재 군 열의 값 '+values.length+'종: '+values.slice(0,12).map(v=>JSON.stringify(String(v).slice(0,200))).join(' / ')+(values.length>12?' (처음 12종만 표시)':'')+'. 표시 길이 제한은 원본 값을 바꾸지 않습니다.';}catch(e){node.textContent=general;}
}
async function exportColumnProfile(){
 if(!$('#profile-consent').checked){$('#profile-status').textContent='저장 항목과 위험을 확인하고 내려받기에 동의해 주세요.';return;}
 const raw=normalizeSimpleSentence($('#data-text').value),mode=$('#format').value;
 if(!mappingDraft||mappingDraft.raw!==raw||mappingDraft.format!==mode||!$('#mapping-confirm').checked){$('#profile-status').textContent='현재 CSV의 열 연결·A/B 값을 먼저 직접 확인해 주세요.';return;}
 const mapping=currentMapping(),ticket=startInput('profile-export',false);
 $('#profile-status').textContent='현재 선택한 열의 지문을 계산하는 중입니다.';
 try{
  const info=ABColumnMapping.inspect(raw,mode);
  ABColumnMapping.convert(raw,mode,mapping,{A:$('#arm-value-a').value,B:$('#arm-value-b').value});
  const profile=await ABColumnProfile.create(info.headers,mapping,mode);
  if(!ownsInput(ticket)||!$('#profile-consent').checked)return;
  download('AB_COLUMN_PROFILE.json',ABColumnProfile.stringify(profile),'application/json;charset=utf-8');
  $('#profile-consent').checked=false;
  $('#profile-status').textContent='열 지문과 역할만 별도 파일로 내려받았습니다. 원본 군 값과 조건은 저장하지 않았습니다. 파일과 메타데이터를 공유 전에 검토하세요.';
 }catch(e){if(ownsInput(ticket))$('#profile-status').textContent='내려받기 실패: '+e.message;}finally{finishInput(ticket);}
}
async function importColumnProfile(file){
 const ticket=startInput('profile-import',false),raw=normalizeSimpleSentence($('#data-text').value),mode=$('#format').value;
 $('#profile-status').textContent='템플릿을 현재 CSV와 대조하는 중입니다.';
 try{
  if(file.size>ABColumnProfile.MAX_BYTES)throw Error('템플릿은 8KiB 이하여야 합니다.');
  const bytes=await file.arrayBuffer();if(!ownsInput(ticket))return;
  const profile=ABColumnProfile.decode(bytes),info=ABColumnMapping.inspect(raw,mode);
  const mapping=await ABColumnProfile.resolve(profile,info.headers,mode);if(!ownsInput(ticket))return;
  // Commit only the fully validated current-owner candidate. No inherited evidence.
  clearAssumptions();markChanged(true);renderMapping({...info,suggestions:mapping},raw,true);
  $('#arm-value-a').value='';$('#arm-value-b').value='';$('#mapping-confirm').checked=false;
  $('#profile-consent').checked=false;$('#profile-status').textContent='현재 CSV의 역할 후보를 채웠습니다. 군 값 A/B를 새로 입력하고 역할·제외 열을 확인한 뒤 연결 적용을 누르세요. 조건은 모름으로 초기화했습니다.';
  $('#prepare-state').textContent='템플릿은 후보일 뿐입니다. 새 원본 군 값과 열 연결을 직접 확인하세요.';
 }catch(e){if(ownsInput(ticket))$('#profile-status').textContent='가져오기 실패 (기존 입력·연결·결과는 유지): '+e.message;}finally{finishInput(ticket);}
}
function initProfiles(){
 $('#profile-export').onclick=exportColumnProfile;
 $('#profile-file').onchange=e=>{const file=e.target.files?.[0];e.target.value='';if(file)importColumnProfile(file);};
 $('#profile-consent').onchange=()=>{if(inputTask?.kind==='profile-export')cancelInput();};
}
