import json, urllib.request, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
urls=[('Microsoft post-experiment','https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/'),('Microsoft during-experiment','https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-during-experiment-stage/'),('NIST randomized blocks','https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm'),('ASA p-value statement','https://www.amstat.org/asa/files/pdfs/pvaluestatement.pdf'),('ICH E9 R1','https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf')]
out=ROOT/'e-book/references/study_v06';out.mkdir(exist_ok=True)
def get(pair):
 title,url=pair
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=45) as r: raw=r.read();status=r.status
  if raw.startswith(b'%PDF'):
   import pymupdf
   doc=pymupdf.open(stream=raw,filetype='pdf');text='\n'.join(p.get_text() for p in doc)
  else:
   from bs4 import BeautifulSoup
   soup=BeautifulSoup(raw,'html.parser')
   for e in soup(['script','style','nav','footer','header']):e.decompose()
   text=soup.get_text('\n',strip=True)
  # Save transformed text for research audit, not vendor binaries.
  file=out/(re.sub('[^a-z0-9]+','_',title.lower())+'.txt');file.write_text(text,encoding='utf-8')
  return {'title':title,'url':url,'status':status,'characters':len(text),'local_text':str(file.relative_to(ROOT)),'read_scope':'retrieved full extracted text; key passages checked separately'}
 except Exception as e:return {'title':title,'url':url,'error':str(e)}
rows=list(ThreadPoolExecutor(5).map(get,urls))
report={'checked_at_seoul':datetime.now(timezone(timedelta(hours=9))).isoformat(),'sources':rows,'caution':'Sources support existing principles, not empirical validation of the author framework.'}
(out/'source_access_v06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
