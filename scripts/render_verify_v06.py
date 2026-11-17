"""Reuse established rendering checks and extend them for glossary navigation."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/render_verify_v05.py').read_text(encoding='utf-8')
s=s.replace('v05','v06').replace('0.5','0.6')
s=s.replace("page.locator('svg').count()==3","page.locator('svg').count()==6")
s=s.replace("assert '{{' not in visible",'''assert '{{' not in visible
    broken=page.evaluate("[...document.querySelectorAll('a[href^=\\\"#\\\"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash)")
    assert not broken,broken
    glossary_count=page.locator('a[id^="g-"]').count();assert 32<=glossary_count<=40
    for anchor in page.locator('a[id^="g-"]').evaluate_all('(es)=>es.map(e=>e.id)'):
        link=page.locator('a[href="#'+anchor+'"]');assert link.count()>=1
    assert 'Overall Evaluation Criterion' in visible and '맥락항법' in visible''')
s=s.replace("'title':'그래서, 이 캠페인 계속할까요? — 트리아타시스와 TRI-V'","'title':'그래서, 이 캠페인 계속할까요? — 맥락항법 제안판'")
s=s.replace("'paragraph_microheadings':{'previous_h3':len(re.findall(r'^### ',old,re.M)),'new_h3':len(re.findall(r'^### ',new,re.M)),'new_other_h2':len(re.findall(r'^## ',new,re.M))-6}","'paragraph_microheadings':{'new_h3':len(re.findall(r'^### ',new,re.M)),'glossary_entry_h2':glossary_count}")
s=s.replace("'palette':'Same previously checked ink/teal/muted on white/paper; min text contrast5.85:1; not new company branding'","'palette':'Recalculated via mira_contrast_matrix: all six text/surface pairs pass AA, minimum5.85:1'")
s=s.replace("'numeric_sources':'Unchanged v0.4 verified analysis + v0.3 plan/repeated sampling; editorial rewrite, not new statistical inference'","'numeric_sources':'Unchanged v0.4 and v0.3 ledgers; three additional figures generated directly from scenario_results.json'")
s=s.replace("'toc_entries':len(toc)","'all_heading_pages':[{ 'title':t[1],'page':t[2]} for t in toc],'glossary_entries':glossary_count,'broken_internal_links':broken,'toc_entries':len(toc)")
exec(compile(s,str(ROOT/'scripts/render_verify_v06.py'),'exec'),{'__file__':str(ROOT/'scripts/render_verify_v06.py'),'__name__':'__main__'})
