'use strict';
/* UI-only helpers. No new statistical calculations, network calls or raw-data storage. */
let mappingDraft=null;
const judgmentDirections={'':'미기록',review_a:'A 적용 검토 / 승인 아님',review_b:'B 적용 검토 / 승인 아님',keep:'현상 유지 검토',defer:'판단 유보',more_data:'추가 확인 후 재검토'};
function resetMapping(){mappingDraft=null;$('#mapping-panel').hidden=true;$('#mapping-fields').replaceChildren();$('#mapping-preview').replaceChildren();$('#mapping-confirm').checked=false;}
function renderMapping(info,raw,force=false){
 mappingDraft={raw,format:$('#format').value,force};
 const labels={arm:'A/B 구분',success:'성공 수',total:'전체 수 / 분모',segment:'집단 / 선택',subject_id:'가명 참여자 ID',outcome:'성공 여부 0/1',observed:'관측 완료 여부 0/1 / 선택'};
 const targets=mappingDraft.format==='individual'?['arm','subject_id','outcome','segment','observed']:['arm','success','total','segment'];
 $('#mapping-fields').innerHTML=targets.map(k=>'<div><label for="map-'+k+'">'+esc(labels[k])+'</label><select data-map-target="'+k+'" id="map-'+k+'"><option value="">연결하지 않음</option>'+info.headers.map(h=>'<option value="'+esc(h)+'"'+(info.suggestions?.[k]===h?' selected':'')+'>'+esc(h)+'</option>').join('')+'</select></div>').join('');
 $('#mapping-preview').innerHTML='<p>원본 '+info.rowCount+'행 · 처음 5행 미리보기. 긴 값은 표시만 줄이며 처리 값은 바꾸지 않아요.</p><div class="table-wrap"><table><thead><tr>'+info.headers.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+info.rowsPreview.map(row=>'<tr>'+row.map(v=>'<td>'+esc(String(v).slice(0,160))+(String(v).length>160?'…':'')+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 $('#mapping-confirm').checked=false;$('#mapping-error').textContent='';$('#arm-value-a').value='A';$('#arm-value-b').value='B';$('#mapping-panel').hidden=false;
}
function resolveInput(text){
 let info;
 try{info=ABColumnMapping.inspect(text,$('#format').value);}catch(e){$('#mapping-error').textContent=e.message;throw e;}
 if(info.headers.length<3){const e=Error('필요한 열이 부족해요. 첫 행에 열 이름이 있는 표를 넣거나, 안내된 간단 문장 형식을 정확히 사용해 주세요.');e.code='MISSING_HEADER';throw e;}
 if(info.canonical&&!mappingDraft?.force){if(mappingDraft)resetMapping();return text;}
 if(!mappingDraft||mappingDraft.raw!==text||mappingDraft.format!==$('#format').value)renderMapping(info,text);
 if(!$('#mapping-confirm').checked){$('#prepare-state').textContent='열 이름이 달라요. 각 열의 역할을 확인하고 연결해 주세요.';return null;}
 const mapping=Object.fromEntries([...document.querySelectorAll('[data-map-target]')].map(e=>[e.dataset.mapTarget,e.value||null]));
 try{const csv=ABColumnMapping.convert(text,$('#format').value,mapping,{A:$('#arm-value-a').value,B:$('#arm-value-b').value});$('#mapping-error').textContent='';$('#mapping-note').textContent='사용자가 확인한 열 연결로 집계를 읽었어요. 원본은 위 입력에 유지되며 연결·원시 행은 저장/전송하지 않습니다.';return csv;}catch(e){$('#mapping-error').textContent=e.message;throw e;}
}
function summaryMarkup(r){
 const o=r.overall,known=Boolean(o?.A&&o?.B),decision=known?win(o.winner):'판정 불가';
 const next=!known?'입력 오류를 수정하고 다시 확인하세요.':!r.inference_allowed?'배정·독립성·관측·종료 조건과 지원 범위를 확인하세요. 조건을 모르면 기술 통계만 사용하세요.':o.winner==='hold'?'남은 불확실성이 실제 선택을 바꾸는지 검토하세요. 유의할 때까지 임의로 연장하지 마세요.':'최소 관심 효과·비용·보호 조건·적용 대상을 별도로 확인하세요.';
 return '<section class="sheet overview-v05" aria-label="한눈에 보는 결과"><h2>한눈에 보는 결과</h2><dl><div><dt>관측 차이 B−A</dt><dd>'+pp(known?o.diff:null)+'</dd></div><div><dt>통계적 판정</dt><dd>'+esc(decision)+'</dd></div><div><dt>사업·보호 조건</dt><dd>미확인 / 실제 적용 승인 아님</dd></div></dl><p><strong>다음 확인</strong> '+esc(next)+'</p><p class="small">보류는 무효과·동등·안전의 증명이 아니며, 관측 차이와 통계적 우세를 구분합니다.</p></section>';
}
function judgmentObject(){return {direction:$('#decision-direction').value,checks:$('#decision-checks').value};}
function judgmentMarkup(){const j=judgmentObject();return '<p><strong>검토 방향:</strong> '+esc(judgmentDirections[j.direction]||'미기록')+'</p><p><strong>확인할 조건:</strong> '+esc(j.checks||'미기록')+'</p>';}
function renderJudgmentGuide(){
 const r=state.result;if(!r)return;
 const selected=$('#decision-direction').value,w=r.overall?.winner;
 const contrary=selected==='review_a'&&w==='B'||selected==='review_b'&&w==='A';
 $('#judgment-guide').textContent=(contrary?'선택한 검토 방향은 통계적 우세 방향과 달라요. 별도 사업적 근거와 보호 조건을 명시해 주세요. ':'')+'현재 통계 판정: '+win(w)+'. 선택은 검토 방향일 뿐 실제 승인·안전 확인이 아닙니다. 이유와 미확인 조건을 직접 기록하세요.';
}
function initWorkflow(){
 $('#apply-mapping').onclick=prepare;
 $('#open-mapping').onclick=()=>{const text=normalizeSimpleSentence($('#data-text').value);const ticket=startInput('mapping');try{if(!text.trim())throw Error('표를 먼저 넣어 주세요.');renderMapping(ABColumnMapping.inspect(text,$('#format').value),text,true);$('#prepare-state').textContent='열 연결과 A/B 값을 직접 확인해 주세요.';}catch(e){notify(e.message);}finally{finishInput(ticket);}};
 function mappingChanged(){markChanged(true);$('#mapping-confirm').checked=false;$('#mapping-error').textContent='연결을 바꿨습니다. 역할과 제외되는 열을 다시 확인해 주세요.';}
 $('#mapping-fields').addEventListener('change',mappingChanged);
 for(const id of ['arm-value-a','arm-value-b'])$('#'+id).addEventListener('input',mappingChanged);
 $('#mapping-confirm').onchange=()=>{if(state.prepared){markChanged(true);}syncInputControls();};
 for(const id of ['decision-direction','decision-checks'])$('#'+id).addEventListener(id==='decision-direction'?'change':'input',()=>{clearShare();renderReport();});
}
