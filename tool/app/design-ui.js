'use strict';
let design=null;
const designMeta={purpose:'purpose',metric:'metric',window:'window',policyA:'policy-a',policyB:'policy-b',audience:'audience'};
function designRender(){
 $('#design-start').hidden=!!design;$('#design-work').hidden=!design;if(!design)return;
 $('#design-state').textContent='계획 수정 '+design.revision+'회'+' / 설계 초안 — 효과·승자 생성 안 함 / '+(design.changedAfterResult?'결과 열람 후 수정 포함':design.resultSeen?'결과 열람 기록 있음':'도구의 결과 열람 기록 없음 / 외부 열람 여부 미확인 — 사전 등록 인증 아님');
 const key=ABDesign.questions[design.step];$('#design-question').textContent=key?ABDesign.fields[key]:'답변을 바탕으로 비교 후보를 선택하세요';$('#design-answer').hidden=!key;$('#design-answer').maxLength=key==='audience'?300:1500;$('#design-answer').value=key?design.fields[key].value:'';$('#design-next').hidden=!key;$('#design-back').disabled=design.step===0;
 $('#design-candidates').hidden=design.step<6;$('#design-fields').innerHTML=Object.entries(ABDesign.fields).map(([k,label])=>'<div class="design-field"><label for="design-'+k+'">'+esc(label)+'</label><textarea id="design-'+k+'" data-design-key="'+k+'" maxlength="'+(k==='audience'?300:1500)+'">'+esc(design.fields[k].value)+'</textarea><label for="status-'+k+'">기록 상태</label><select id="status-'+k+'" data-design-status="'+k+'"><option value="unknown">미확인</option><option value="proposed">제안 / 수정 중</option><option value="confirmed">내가 확인함 / 인증 아님</option></select></div>').join('');
 for(const k of Object.keys(ABDesign.fields))$('#status-'+k).value=design.fields[k].status;
 $('#design-candidate-state').textContent=design.candidate?'선택한 초안: '+ABDesign.candidates.find(c=>c.id===design.candidate).label:'아직 후보를 고르지 않았습니다.';
}
function designApply(){if(!design)return;for(const [k,id]of Object.entries(designMeta))$('#'+id).value=design.fields[k].value;}
function designChange(k,value){ABDesign.edit(design,k,value);markChanged(false);designApply();}
function designOpen(){if(!design){design=ABDesign.empty();for(const [k,id]of Object.entries(designMeta)){const v=$('#'+id).value;if(v)ABDesign.edit(design,k,v);}if(state.result)design.resultSeen=true;}designRender();go('design');}
function initDesign(){
 $('#begin-design').onclick=designOpen;
 $('#design-next').onclick=()=>{const k=ABDesign.questions[design.step];designChange(k,$('#design-answer').value);design.step++;designRender();};
 $('#design-back').onclick=()=>{if(design.step>0){design.step--;designRender();}};
 $('#design-answer').oninput=()=>{const k=ABDesign.questions[design.step];if(k){designChange(k,$('#design-answer').value);$('#design-'+k).value=design.fields[k].value;for(const key of Object.keys(ABDesign.fields))$('#status-'+key).value=design.fields[key].status;}};
 $('#design-fields').oninput=e=>{const k=e.target.dataset.designKey;if(!k)return;designChange(k,e.target.value);if(ABDesign.questions[design.step]===k)$('#design-answer').value=e.target.value;for(const key of Object.keys(ABDesign.fields))$('#status-'+key).value=design.fields[key].status;$('#design-state').textContent='계획 수정 '+design.revision+'회'+' / 수정됨 — 영향받는 확인 해제'+(design.changedAfterResult?' / 결과 열람 후 수정':'');};
 $('#design-fields').onchange=e=>{const k=e.target.dataset.designStatus;if(!k)return;const f=design.fields[k];if(!f.value.trim()){e.target.value='unknown';notify('빈 항목은 확인할 수 없습니다. 모르면 미확인으로 남겨 주세요.');return;}markChanged(false);f.status=e.target.value;design.revision++;if(design.resultSeen)design.changedAfterResult=true;};
 $('#design-candidates').innerHTML=ABDesign.candidates.map(c=>'<button type="button" data-candidate="'+c.id+'">'+esc(c.label)+'</button>').join('');
 $('#design-candidates').onclick=e=>{const id=e.target.dataset.candidate;if(!id)return;if(design.candidate&&!confirm('후보를 바꾸면 A/B·측정·배정·판정 초안을 교체하고 확인을 해제합니다. 계속할까요?'))return;ABDesign.propose(design,id);markChanged(false);designApply();designRender();};
 $('#design-to-input').onclick=()=>{designApply();clearAssumptions();markChanged(false);go('input');notify('같은 실험 계획으로 결과 입력을 엽니다. 실제 배정·관측·집단 기준과 계획의 일치 여부는 별도로 확인하세요.');};
 for(const [k,id]of Object.entries(designMeta))$('#'+id).addEventListener('input',()=>{if(design){ABDesign.edit(design,k,$('#'+id).value);designRender();}});
 designRender();
}
