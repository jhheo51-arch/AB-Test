"""Offline-only reader zoom and explicit worksheet transfer. No storage or network."""
from pathlib import Path
import re
from record_print_v22 import PRINT_CSS,PRINT_JS
ZOOM_CSS='''
.figure-zoom-button{display:block;margin:8px 0 0;padding:8px 14px;min-height:44px;border:1px solid #4F625F;background:#FFFFFF;color:#142D32;font:16px ReaderSans;cursor:pointer}
.figure-zoom-button:focus-visible,.figure-zoom-dialog button:focus-visible{outline:3px solid #125E59;outline-offset:3px}
.figure-zoom-dialog{box-sizing:border-box;width:calc(100vw - 24px);max-width:1320px;max-height:calc(100dvh - 24px);padding:16px;border:1px solid #4F625F;background:#FFFFFF;color:#142D32;font:16px/1.5 ReaderSans}
.figure-zoom-dialog::backdrop{background:rgba(20,45,50,.72)}
.figure-zoom-toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px}.figure-zoom-toolbar h2{margin:0;font:600 18px ReaderSans}.figure-zoom-toolbar button{min-width:64px;min-height:44px;padding:8px 14px;border:0;background:#142D32;color:#FFFFFF;font:16px ReaderSans;cursor:pointer}
.figure-zoom-help{margin:8px 0;font:16px/1.5 ReaderSans;text-indent:0}.figure-zoom-stage{overflow:auto;max-height:calc(100dvh - 180px);overscroll-behavior:contain}.figure-zoom-stage svg{display:block;width:var(--original-width);max-width:none;height:auto}
@media print{.figure-zoom-button,.figure-zoom-dialog{display:none!important}}
'''
ZOOM_JS=r'''
(()=>{
 const dialog=document.createElement('dialog');dialog.className='figure-zoom-dialog';dialog.setAttribute('aria-labelledby','figure-zoom-heading');dialog.setAttribute('aria-describedby','figure-zoom-help');
 dialog.innerHTML='<div class="figure-zoom-toolbar"><h2 id="figure-zoom-heading">그림 원래 크기로 보기</h2><button type="button" autofocus>닫기</button></div><p id="figure-zoom-help" class="figure-zoom-help">작은 화면에서는 그림 안을 가로와 세로로 움직여 읽으세요. 닫으면 읽던 위치로 돌아갑니다.</p><div class="figure-zoom-stage" tabindex="0" aria-label="확대한 그림, 스크롤하여 읽기"></div>';
 document.body.append(dialog);const stage=dialog.querySelector('.figure-zoom-stage');let saved=null;
 function restore(){if(!saved)return;const s=saved;saved=null;if(s.bodyStyle===null)document.body.removeAttribute('style');else document.body.setAttribute('style',s.bodyStyle);stage.replaceChildren();s.opener.focus({preventScroll:true});window.scrollTo({left:s.x,top:s.y,behavior:'instant'});requestAnimationFrame(()=>window.scrollTo({left:s.x,top:s.y,behavior:'instant'}));}
 function close(){dialog.close();restore()}
 dialog.querySelector('button').addEventListener('click',close);dialog.addEventListener('cancel',e=>{e.preventDefault();close()});dialog.addEventListener('close',restore);
 dialog.addEventListener('click',e=>{const r=dialog.getBoundingClientRect();if(e.target===dialog&&(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom))close()});
 document.querySelectorAll('figure[data-figure]').forEach((fig,index)=>{
  const svg=fig.querySelector('svg');if(!svg)return;const button=document.createElement('button');button.type='button';button.className='figure-zoom-button';button.textContent='그림 확대';button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-label',`${index+1}번째 그림 확대`);fig.append(button);
  function open(){if(saved)return;saved={x:scrollX,y:scrollY,opener:button,bodyStyle:document.body.getAttribute('style')};const copy=svg.cloneNode(true),ids=new Map();copy.querySelectorAll('[id]').forEach(el=>ids.set(el.id,'zoom-'+index+'-'+el.id));if(copy.id)ids.set(copy.id,'zoom-'+index+'-'+copy.id);
   [copy,...copy.querySelectorAll('*')].forEach(el=>{for(const a of [...el.attributes]){let v=a.value;if(a.name==='id'&&ids.has(v))v=ids.get(v);else if(a.name==='aria-labelledby'||a.name==='aria-describedby')v=v.split(/\s+/).map(t=>ids.get(t)||t).join(' ');else for(const [old,n] of ids){v=v.replaceAll('url(#'+old+')','url(#'+n+')');if(v==='#'+old)v='#'+n}el.setAttribute(a.name,v)}});
   const width=svg.viewBox.baseVal.width||svg.width.baseVal.value||1200;copy.style.setProperty('--original-width',width+'px');copy.setAttribute('role','img');copy.setAttribute('aria-label',fig.querySelector('figcaption')?.textContent||'확대한 그림');stage.replaceChildren(copy);stage.scrollLeft=stage.scrollTop=0;
   Object.assign(document.body.style,{position:'fixed',top:-saved.y+'px',left:-saved.x+'px',width:'100%'});dialog.showModal();dialog.querySelector('button').focus({preventScroll:true});
  }
  button.addEventListener('click',open);svg.addEventListener('click',open);svg.style.cursor='zoom-in';
 });
})();
'''
RECORD_JS=r'''
(()=>{
 const main=document.querySelector('main'),controls=document.createElement('div');controls.className='record-transfer';
 controls.innerHTML='<button type="button" id="record-copy">기록 복사</button><button type="button" id="record-export">텍스트 파일로 저장</button><p id="record-transfer-status" role="status" aria-live="polite"></p><p></p>';
 controls.querySelector('#record-copy').textContent='기록 복사';controls.querySelector('#record-export').textContent='텍스트 파일로 저장';controls.lastElementChild.textContent='입력은 자동 저장되지 않습니다. 새로고침하거나 창을 닫기 전에 복사하거나 파일로 저장하세요. 파일을 공유하기 전에는 고객 정보와 내부 링크를 확인하세요.';
 main.append(controls);const status=controls.querySelector('[role=status]');
 function record(){const fields=[...document.querySelectorAll('.meta input')].map(e=>[e.getAttribute('aria-label'),e.value]),notes=[...document.querySelectorAll('.field textarea')].map(e=>[document.querySelector('label[for="'+e.id+'"]').textContent,e.value]);return 'TRI-V 실전 기록 v0.22\n내보낸 시각: '+new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Seoul',dateStyle:'short',timeStyle:'medium'}).format(new Date())+' (Asia/Seoul)\n이 파일의 저장은 실험 실행이나 발송 승인이 아닙니다.\n\n'+[...fields,...notes].map(([k,v])=>k+'\n'+(v||'(미입력)')).join('\n\n')+'\n';}
 controls.querySelector('#record-copy').addEventListener('click',async()=>{const text=record();try{if(!navigator.clipboard?.writeText)throw Error('Clipboard unavailable');await navigator.clipboard.writeText(text);status.textContent='현재 입력을 클립보드에 복사했습니다. 필요한 곳에 붙여 넣어 보관하세요.'}catch{let box=document.getElementById('record-copy-fallback');if(!box){box=document.createElement('textarea');box.id='record-copy-fallback';box.readOnly=true;box.setAttribute('aria-label','수동으로 복사할 기록');controls.append(box)}box.value=text;box.focus();box.select();status.textContent='브라우저가 자동 복사를 허용하지 않았습니다. 선택된 기록을 직접 복사하거나 텍스트 파일로 저장하세요.'}});
 controls.querySelector('#record-export').addEventListener('click',()=>{const blob=new Blob(['\uFEFF'+record()],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='TRI-V_record_v22.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);status.textContent='텍스트 파일 다운로드를 요청했습니다. 브라우저의 다운로드 목록에서 저장 여부를 확인하세요.'});
})();
'''
def install(out:Path):
 reader=out/'ebook_review_v22.html';s=reader.read_text(encoding='utf-8');assert 'figure-zoom-dialog' not in s;s=s.replace('</head>','<style>'+ZOOM_CSS+'</style></head>').replace('</body>','<script>'+ZOOM_JS+'</script></body>');reader.write_text(s,encoding='utf-8',newline='\n')
 record=out/'MINIMUM_RECORD.html';s=record.read_text(encoding='utf-8');s=re.sub(r'<title>.*?</title>','<title>TRI-V 실전 기록 v0.22</title>',s);s=s.replace('</head>','<style>.record-transfer p{font-size:16px;color:#4F625F}.record-transfer button{margin-right:8px}.record-transfer textarea{height:180px}@media print{.record-transfer{display:none}}</style></head>');s=s.replace('</head>',PRINT_CSS+'</head>').replace('</body>','<script>'+RECORD_JS+'</script>'+PRINT_JS+'</body>');record.write_text(s,encoding='utf-8',newline='\n')
if __name__=='__main__':install(Path(__file__).resolve().parents[1]/'e-book/exports/v22')
