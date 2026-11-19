"""Measure figure text collisions, label regions and container centering."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v17'
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);q=b.new_page(viewport={'width':1200,'height':900});q.goto((O/'ebook_review_v17.html').as_uri());q.evaluate('document.fonts.ready')
 rows=q.evaluate('''()=>[...document.querySelectorAll('figure[data-figure]')].map(f=>{const svg=f.querySelector('svg'),rr=f.getBoundingClientRect(),pr=f.parentElement.getBoundingClientRect();let ts=[...svg.querySelectorAll('text')],collisions=[],regions=[];for(let i=0;i<ts.length;i++){let a=ts[i].getBoundingClientRect();if(ts[i].dataset.region){let [x,y,w,h]=JSON.parse(ts[i].dataset.region),z=ts[i].getBBox();if(z.x<x-1||z.y<y-1||z.x+z.width>x+w+1||z.y+z.height>y+h+1)regions.push(ts[i].textContent)}for(let j=i+1;j<ts.length;j++){let bb=ts[j].getBoundingClientRect(),ix=Math.min(a.right,bb.right)-Math.max(a.left,bb.left),iy=Math.min(a.bottom,bb.bottom)-Math.max(a.top,bb.top);if(ix>1&&iy>1)collisions.push([ts[i].textContent,ts[j].textContent])}}return {file:f.dataset.figure,centering_error_css_px:Math.abs((rr.left+rr.right-pr.left-pr.right)/2),text_collisions:collisions,outside_intended_regions:regions}})''');b.close()
report={'scope':'Actual browser text boxes; conceptual labels additionally checked against declared panels. Not a reader study or a complete accessibility audit.','figures':rows,'issues':[r for r in rows if r['centering_error_css_px']>.6 or r['text_collisions'] or r['outside_intended_regions']]}
(O/'visual_geometry_v17.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,ensure_ascii=False,indent=2));assert not report['issues']
