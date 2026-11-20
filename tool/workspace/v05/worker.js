'use strict';
importScripts('engine.js');
self.postMessage({type:'ready',version:ABEngine.VERSION});
self.onmessage=function(event){
 const m=event.data;
 try{
  if(m.type==='prepare'){
   const p=ABEngine.prepare(m.text,m.format);
   self.postMessage({id:m.id,prepared:{cells:p.cells||[],issues:p.issues||[],format:p.format||m.format,sourceRowCount:p.sourceRowCount||0}});
  }else if(m.type==='analyze'){
   self.postMessage({id:m.id,analysis:ABEngine.analyze(m.prepared,m.plan)});
  }else{
   self.postMessage({id:m.id,error:{code:'UNKNOWN_OPERATION',message:'지원하지 않는 계산 작업입니다.'}});
  }
 }catch(e){self.postMessage({id:m.id,error:{code:e.code||'ENGINE_ERROR',message:String(e.message||e)}});}
};
