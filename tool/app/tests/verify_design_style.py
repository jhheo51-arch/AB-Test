from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];E=R/'design-evidence';a=argparse.ArgumentParser();a.add_argument('--url',required=True);url=a.parse_args().url
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=b.new_page();bad=[];remote=[]
 p.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 p.on('request',lambda r:remote.append(r.url) if not r.url.startswith(url) else None)
 p.goto(url,wait_until='networkidle');p.click('nav [data-view=design]');p.click('#begin-design')
 colors=p.evaluate("""() => ['#design-view .heading p','#design-view .note','#design-fields label','#design-situation','#design-fields select','#begin-design'].map(s=>{const e=document.querySelector(s),c=getComputedStyle(e);let a=e,bg;while(a){bg=getComputedStyle(a).backgroundColor;if(bg!=='rgba(0, 0, 0, 0)')break;a=a.parentElement;}return {selector:s,foreground:c.color,background:bg,fontSize:c.fontSize}})""")
 # Script-like text is rendered as plain data.
 p.fill('#design-answer','<img src=x onerror=window.BAD=1>');p.click('#design-next');assert p.locator('#design-fields img').count()==0 and p.evaluate('window.BAD===undefined')
 assert not bad and not remote
 out={'status':'PASS','computed_colors':colors,'http_errors':bad,'remote_requests':remote,'escaped_text':True};(E/'BROWSER_STYLE_NETWORK.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2));b.close()
