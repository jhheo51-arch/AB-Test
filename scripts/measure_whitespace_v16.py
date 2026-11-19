"""Measure unused bottom space separately from normal book margins."""
from pathlib import Path
import argparse,json,statistics,math
import pymupdf
p=argparse.ArgumentParser();p.add_argument('pdf');p.add_argument('output');p.add_argument('--top',type=float,default=17);p.add_argument('--bottom',type=float,default=18);a=p.parse_args()
d=pymupdf.open(a.pdf);toc=d.get_toc();start=next((x[2] for x in toc if x[1]=='들어가며'),4);rows=[]
for number,page in enumerate(d,1):
 if number<start:continue
 top=a.top*72/25.4;bottom=page.rect.height-a.bottom*72/25.4
 words=[w for w in page.get_text('words') if w[1]>=top-1 and w[3]<=bottom+1]
 if not words:continue
 end=max(w[3] for w in words);gap=max(0,bottom-end)*25.4/72
 rows.append({'page':number,'words':len(words),'last_content_y_mm':round(end*25.4/72,2),'remaining_bottom_space_mm':round(gap,2),'at_least_30mm_unused':gap>=30})
gaps=sorted(r['remaining_bottom_space_mm'] for r in rows);result={'pdf':str(Path(a.pdf)),'pdf_pages':len(d),'scope':'Text-bearing content extent including figure labels and footnotes; excludes cover and contents. Measures bottom leftover in the defined frame, not total white-pixel percentage. Natural final-page tails are not automatically layout errors.','frame_margin_top_mm':a.top,'frame_margin_bottom_mm':a.bottom,'median_remaining_bottom_mm':statistics.median(gaps),'p90_remaining_bottom_mm':gaps[min(len(gaps)-1,math.ceil(.9*len(gaps))-1)],'pages_with_at_least_30mm_unused':[r['page'] for r in rows if r['at_least_30mm_unused']],'rows':rows}
Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
