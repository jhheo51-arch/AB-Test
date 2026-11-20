/* Local explanation layer. Reads verified results; never runs a new test or sends data. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ABNarrative=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const finite=Number.isFinite;
const has=(r,code)=>(r.issues||[]).some(i=>i.code===code);
const text=(code,headline,body,next)=>({code,headline,body,next});
function group(r,g,scope){
 const alpha=.05;
 if(!g||r.status==='invalid')return text('INVALID','입력을 먼저 확인해 주세요','유효한 비교 결과가 없어 판정 이유를 만들지 않았어요.','오류가 표시된 행과 열을 고친 뒤 다시 확인해 주세요.');
 const d=g.diff, direction=finite(d)&&d!==0?(d>0?'B':'A'):null;
 const observed=direction?direction+'의 성공 비율이 더 높게 관측됐어요. ':finite(d)?'두 안의 관측 성공 비율은 같아요. ':'';
 if(!finite(g.p_adjusted)||g.winner==='not_tested'){
  if(!r.inference_allowed){
   if(has(r,'EMPTY_ARM'))return text('EMPTY_ARM','한쪽 안의 분모가 없어요','A/B 전체 분모가 모두 양수여야 이 비교를 추론할 수 있어요. 분모가 없는 안의 성공 비율은 정의하지 않아요.','A/B 배정 집계와 누락을 확인해 주세요. 관측되지 않은 사람을 자동으로 실패 처리하지 마세요.');
   if(has(r,'ARM_LIMIT')||r.status==='unsupported')return text('UNSUPPORTED','지원 범위 밖이라 판정하지 않았어요','관측 수치는 볼 수 있지만, 이 입력·설계는 현재 검정 경로의 범위를 벗어나요.','계산 방법·가정·원천의 제한 코드를 확인해 지원 가능한 분석 경로를 검토하세요.');
   return text('ASSUMPTIONS','설계 조건이 확인되지 않았어요','무작위 배정·독립된 참여자·관측 완료·종료 규칙 중 확인되지 않은 조건이 있어 기술 통계만 보여드려요.','배정·관측 기록을 확인해 주세요. 확인할 수 없다면 체크를 추정해서 켜지 말고 기술 통계로 남겨 주세요.');
  }
  if(scope==='segment'&&g.exploratory){
   if(has(r,'SEGMENT_INFERENCE_BLOCKED'))return text('EXPLORATORY','탐색 집단이며 집단 결측 제한도 있어요',observed+'집단 기준의 사전성이 확인되지 않아 확증 승패를 내리지 않았어요. 또한 집단 정보가 누락된 참여자는 전체에 포함했지만 집단별 검정은 제한했어요.','기존 사전 계획과 누락된 집단 정보의 의미를 각각 확인해 주세요. 사전 계획이 확인되어도 결측 제한은 남아요. 사후 기준은 탐색으로 유지하고, 유리한 결과를 만들려고 참여자를 제외하지 마세요.');
   return text('EXPLORATORY','이 집단은 탐색 결과예요',observed+'집단 기준의 사전성이 확인되지 않아 확증 승패를 내리지 않았어요.','기존 사전 계획이 있었는지 확인하고, 사후에 고른 기준이면 탐색 결과로 유지해 주세요.');
  }
  if(has(r,'SEGMENT_INFERENCE_BLOCKED'))return text('MISSING_SEGMENT','집단 정보가 빠져 판정을 제한했어요','집단이 누락된 참여자는 전체에 포함했지만 집단별 검정에서는 근거를 확정하지 않았어요.','누락된 집단 정보의 의미를 확인하세요. 유리한 결과를 만들려고 참여자를 제외하지 마세요.');
  if(scope==='segment'){
   const empty=['A','B'].filter(a=>g[a]?.total===0);
   if(empty.length)return text('GROUP_UNSUPPORTED','이 집단의 '+empty.join('·')+' 분모가 0이에요','이 집단의 '+empty.map(a=>a+' 분모가 0').join(', ')+'이라 해당 안의 성공 비율은 정의되지 않아요. 양쪽 안의 분모가 모두 양수여야 이 집단을 검정할 수 있어요.','이 집단의 A/B 배정 집계와 누락 여부를 확인해 주세요. 관측되지 않은 사람을 실패로 채우거나 없는 자료를 만들어 넣지 마세요.');
  }
  return text('GROUP_UNSUPPORTED','이 집단은 판정 조건을 충족하지 못했어요',observed+'양쪽 안의 분모와 지원 조건을 충족하는지 확인이 필요해요.','빈 군·집단 수·입력 제한을 확인해 주세요. 없는 자료나 결과를 만들어 채우지 않아요.');
 }
 if(g.winner==='A'||g.winner==='B')return text('SUPERIOR',g.winner+'의 통계적 우세 근거가 있어요',observed+'선택한 방법과 조건, 비교 가족 안에서 엔진의 우세 기준을 충족했어요.','최소 관심 효과·비용·보호 조건·적용 대상을 별도로 확인한 뒤 실제 적용 여부를 결정하세요.');
 if(g.winner!=='hold')return text('UNKNOWN','판정 상태를 다시 확인해 주세요','지원되는 엔진 판정과 설명 상태가 일치하는지 확인이 필요해요.','원래 계산 결과와 제한 코드를 우선 확인하세요.');
 if(finite(g.p_raw)&&g.p_raw<=alpha&&g.p_adjusted>alpha&&(r.family?.m||0)>1)return text('HOLM_HOLD','여러 비교를 고려하면 승패 보류예요',observed+'개별 검정만 보면 기준을 충족하지만, 여러 질문을 함께 검토한 보정 기준에서는 우세를 확정하지 못했어요.','명목 구간은 가족 동시 구간이 아니며 Fisher 검정과 완전히 쌍대도 아니에요. 구간만으로 승리를 정하지 말고 조정 p값과 원래 분석 계획을 함께 확인하세요.');
 return text('HOLD','우열을 정할 근거가 아직 충분하지 않아요',observed+'관측 차이만으로 통계적 승패를 확정할 수는 없어요. 보류는 효과가 없거나 두 안이 동등·안전하다는 증명이 아니에요.','정한 관측·표본 계획을 충족했는지, 남은 불확실성이 실제 선택을 바꾸는지 검토하세요. 유의할 때까지 임의로 연장하지 마세요.');
}
function interaction(r){
 if(r.status==='invalid'||r.overall===null)return text('INTERACTION_BLOCKED','입력을 먼저 확인해 주세요','유효한 수치 결과가 없어 전체 비교와 집단 간 직접 차이에 사용할 수치가 없어요.','오류가 표시된 행과 열을 먼저 고친 뒤 다시 분석해 주세요. 수정 전 결과의 수치를 판단에 사용하지 마세요.');
 const i=r.interaction||{};
 if(!r.inference_allowed)return text('INTERACTION_BLOCKED','직접 차이도 추론하지 않았어요','전체 추론의 입력·설계 조건이나 지원 범위를 먼저 확인해야 해요.','제한 코드와 배정·관측 기록을 확인하고, 조건 미확인 상태에서는 기술 통계만 사용해 주세요.');
 if(!finite(i.p_adjusted)){
  if(i.status==='not_requested')return text('INTERACTION_NOT_REQUESTED','집단 간 직접 차이는 검토하지 않았어요','집단 하나만 유의하다는 사실로 고객군별 효과가 다르다고 결론 내릴 수 없어요.','집단 정보와 사전 계획이 있고 이 비교가 실제 결정에 필요할 때 지원 범위 안에서 검토하세요.');
  return text('INTERACTION_UNSUPPORTED','고객군 간 차이는 판정하지 못했어요','사전 집단·결측·각 셀의 성공과 실패 수 등 직접 비교 조건을 충족하지 못했어요.','집단별 조건과 제한 코드를 확인하세요. 한 집단만 유의하다는 이유로 효과 차이를 확정하지 마세요.');
 }
 if(i.p_adjusted<=.05)return text('INTERACTION_SUPPORTED','고객군 간 효과 차이의 근거가 있어요','두 집단의 B−A 위험차를 직접 비교한 결과예요. 어느 고객군에 어느 안을 적용할지는 별도 판단이에요.','집단별 효과 방향과 보호 조건, 사전 정의한 적용 범위를 함께 확인하세요.');
 return text('INTERACTION_HOLD','고객군별 효과가 다르다고 정하기는 어려워요','직접 비교의 보정 기준에서 차이 근거가 충분하지 않아요. 두 집단의 효과가 같다는 증명은 아니에요.','고객군마다 정책을 달리할 근거가 충분한지 검토하고, 추가 확인이 실제 선택을 바꾸는지 기록하세요.');
}
function card(x){return '<section class="decision-reason" data-reason="'+escape(x.code)+'"><h3>'+escape(x.headline)+'</h3><p>'+escape(x.body)+'</p><p class="next-check"><strong>다음 확인</strong> '+escape(x.next)+'</p></section>';}
function context(m){const val=(key,fallback)=>escape(m[key]?.trim()||fallback);return '<section class="experiment-context"><h2>무엇을 비교했나요?</h2><p class="small">사용자가 기록한 실험 맥락이에요. 설계의 독립 인증은 아니에요.</p><div class="policy-pair"><div><span>A 정책</span><strong>'+val('policyA','설명 미기록')+'</strong></div><div><span>B 정책</span><strong>'+val('policyB','설명 미기록')+'</strong></div></div><dl class="context-facts"><dt>성공 사건</dt><dd>'+val('metric','미기록')+'</dd><dt>관측 기간</dt><dd>'+val('window','미기록')+'</dd><dt>분석 대상</dt><dd>'+val('audience','대상 미기록 — 집단 이름으로 추정하지 않음')+'</dd><dt>비교 목적</dt><dd>'+val('purpose','미기록')+'</dd></dl></section>';}
return {group,interaction,card,context,escape,VERSION:'0.4.0'};
});
