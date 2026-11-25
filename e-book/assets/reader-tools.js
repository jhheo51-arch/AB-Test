(() => {
 'use strict';
 const reading=document.querySelector('.reading'),sourceToc=document.querySelector('nav.contents');
 if(!reading||!sourceToc||typeof HTMLDialogElement==='undefined')return;
 const skip=document.createElement('a');skip.className='reader-skip';skip.href='#reading-content';skip.textContent='본문으로 건너뛰기';reading.tabIndex=-1;
 const bar=document.createElement('nav');bar.className='reader-toolbar';bar.setAttribute('aria-label','독서 설정');
 const label=document.createElement('span');label.className='reader-toolbar-label';label.textContent='읽기 설정';bar.append(label);
 function button(text,aria,fn){const b=document.createElement('button');b.type='button';b.textContent=text;b.setAttribute('aria-label',aria);b.addEventListener('click',fn);bar.append(b);return b;}
 let size=16,smaller,larger;
 function setSize(next){size=Math.max(16,Math.min(22,next));reading.style.setProperty('--reader-size',size+'px');smaller.disabled=size===16;larger.disabled=size===22;}
 function dialog(id,title){
  const d=document.createElement('dialog');d.id=id;d.className='reader-dialog';d.setAttribute('aria-labelledby',id+'-heading');
  const head=document.createElement('div');head.className='reader-dialog-header';const h=document.createElement('h2');h.id=id+'-heading';h.textContent=title;const close=document.createElement('button');close.type='button';close.textContent='닫기';head.append(h,close);d.append(head);document.body.append(d);
  let opener=null,position=null;
  function shut(){d.close();}
  close.addEventListener('click',shut);
  d.addEventListener('close',()=>{if(opener){opener.focus({preventScroll:true});if(position)window.scrollTo({left:position.x,top:position.y,behavior:'instant'});opener=null;position=null;}});
  return {element:d,show(trigger,restore=true){opener=trigger;position=restore?{x:scrollX,y:scrollY}:null;d.showModal();close.focus({preventScroll:true});},close:shut};
 }
 const toc=dialog('reader-toc-dialog','목차');const links=document.createElement('nav');links.className='reader-toc-links';links.setAttribute('aria-label','책의 장과 참고 해설');
 for(const original of sourceToc.querySelectorAll('a[href^="#"]')){
  const a=document.createElement('a');a.href=original.getAttribute('href');a.textContent=original.querySelector('span')?.textContent||original.textContent;
  a.addEventListener('click',e=>{const target=document.getElementById(decodeURIComponent(a.hash.slice(1)));if(!target)return;e.preventDefault();toc.close();requestAnimationFrame(()=>{target.scrollIntoView({block:'start'});history.replaceState(null,'',a.hash);target.tabIndex=-1;target.focus({preventScroll:true});});});links.append(a);
 }
 toc.element.append(links);
 button('목차','책 목차 열기',e=>toc.show(e.currentTarget));smaller=button('작게','본문 글자 작게',()=>setSize(size-2));larger=button('크게','본문 글자 크게',()=>setSize(size+2));button('기본','본문 글자 크기 기본값',()=>setSize(16));setSize(16);
 const note=dialog('reader-note-dialog','각주');const noteBody=document.createElement('p');noteBody.id='reader-note-body';note.element.setAttribute('aria-describedby','reader-note-body');note.element.append(noteBody);
 for(const span of reading.querySelectorAll('.footnote[data-note-id]')){
  const number=span.dataset.noteId.replace('fn-',''),call=document.createElement('button');call.type='button';call.className='reader-note-call';call.textContent='주 '+number;call.setAttribute('aria-label','각주 '+number+' 읽기');call.setAttribute('aria-haspopup','dialog');
  call.addEventListener('click',()=>{note.element.querySelector('h2').textContent='각주 '+number;noteBody.textContent=span.textContent;note.show(call);});span.before(call);
 }
 document.body.prepend(skip,bar);document.documentElement.classList.add('reader-enhanced');
})();
