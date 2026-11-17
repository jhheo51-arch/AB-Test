"""Read the supplied public Notion study page; never use credentials.
uv run --with playwright scripts/retrieve_notion_study_v06.py
"""
import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e-book/references/study_v06';OUT.mkdir(parents=True,exist_ok=True)
url='https://app.notion.com/p/Studying-41b629822d0b802c9b26e955044690eb?source=copy_link'
seen={};records=[]
with sync_playwright() as p:
    b=p.chromium.launch(channel='chrome',headless=True)
    page=b.new_page(viewport={'width':1280,'height':2000})
    page.goto(url,wait_until='domcontentloaded',timeout=60000);page.wait_for_timeout(2500)
    scroller=page.locator('.notion-scroller.vertical').first
    assert scroller.count(),page.locator('body').inner_text()[:300]
    scroller.evaluate('(e)=>e.scrollTop=0');page.wait_for_timeout(700)
    last_top=-1
    for step in range(60):
        page.wait_for_timeout(600)
        state=scroller.evaluate('(e)=>({top:e.scrollTop,height:e.clientHeight,total:e.scrollHeight})')
        blocks=page.locator('[data-block-id]').evaluate_all('es=>es.map(e=>({id:e.getAttribute("data-block-id"),type:e.className,text:e.innerText,links:[...e.querySelectorAll("a[href]")].map(a=>({text:a.innerText,url:a.href}))}))')
        records.append({'state':state,'blocks':blocks})
        for block in blocks:
            if block['text'].strip() and 'notion-page-block' not in block['type']:seen[block['id']]=block
        (OUT/'notion_read_progress.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        if state['top']+state['height']>=state['total']-3:break
        if state['top']==last_top and step>1:raise RuntimeError('Scroll stopped before page end; partial extraction')
        last_top=state['top'];scroller.evaluate('(e)=>e.scrollTop+=e.clientHeight*.75')
    else:raise RuntimeError('Page extraction step limit reached')
    title=page.title();final_body=page.locator('body').inner_text();b.close()
result={'source_url':url,'title':title,'checked_at_seoul':datetime.now(timezone(timedelta(hours=9),'Asia/Seoul')).isoformat(),'blocks':list(seen.values()),'block_count':len(seen),'snapshots':len(records),'reached_page_end':state['top']+state['height']>=state['total']-3,'final_scroll_state':state,'limits':'Visible public page content only; linked videos and documents not automatically read or watched.'}
(OUT/'notion_studying_source.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
text='\n\n'.join(x['text'] for x in seen.values())
(OUT/'notion_studying_source.txt').write_text(text,encoding='utf-8')
print(json.dumps({'block_count':len(seen),'characters':len(text),'snapshots':len(records),'end':result['reached_page_end'],'last_state':state,'source':str(OUT/'notion_studying_source.json')},ensure_ascii=False,indent=2))
print(text)
