"""Exercise registered editorial replay, frozen inputs, graph data and final layout.
This is artifact verification, not human statistical or reader validation.
"""
from pathlib import Path
from collections import Counter
import json,re,hashlib,math,xml.etree.ElementTree as ET
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v18';checks=[]
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def check(name,ok):checks.append({'check':name,'pass':bool(ok)});assert ok,name
def compact(s):return re.sub(r'\s+','',s)
def near(a,b):return math.isclose(float(a),float(b),abs_tol=1e-9,rel_tol=1e-10)
for p,h in load('e-book/manuscript/development_v18/BASELINE.json')['hashes'].items():check('Preserved input '+p,hashlib.sha256((R/p).read_bytes()).hexdigest()==h)
old=(R/'e-book/exports/v17/ebook_review_v17.md').read_text(encoding='utf-8');new=(O/'ebook_review_v18.md').read_text(encoding='utf-8');expected=old.split('# 찾아보기')[0]
num=lambda s:re.findall(r'[+-]?\d+(?:[,.]\d+)*(?:e[+-]?\d+)?',s)
english=lambda s:re.findall(r'[A-Za-z][A-Za-z0-9_-]*',s)
edits=[]
for name in ['prose_01_04.json','prose_05_07.json','prose_08_12.json']:edits+=load('e-book/review/editorial_quality_v18/'+name)
check('83 substantive prose edits',len(edits)==83)
for i,e in enumerate(edits,1):
 check('Unique original and retained numerical/English tokens '+str(i),expected.count(e['before'])==1 and num(e['before'])==num(e['after']) and english(e['before'])==english(e['after']))
 expected=expected.replace(e['before'],e['after'])
base=expected;ops=load('e-book/manuscript/development_v18/STRUCTURAL_EDITS.json');groups={};replacements={}
for i,op in enumerate(ops,1):
 if op['operation']=='move_replacement_after':continue
 before=op['before'];check('Exact structural target '+str(i),expected.count(before)==1)
 if op['operation']=='replace':expected=expected.replace(before,op['after']);replacements[before]=op['after']
 else:
  expected=expected.replace(before,'')
  if op['operation']=='move_after':groups.setdefault(op['anchor'],[]).append(before)
for anchor,paragraphs in groups.items():expected=expected.replace(anchor,anchor+'\n\n'+'\n\n'.join(paragraphs))
for op in ops:
 if op['operation']=='move_replacement_after':
  p=replacements[op['replacement_before']];expected=expected.replace(p,'');expected=expected.replace(op['anchor'],op['anchor']+'\n\n'+p)
check('Structural edits retain numeric tokens under registered exercise relocation and English named terms',(Counter(num(base))==Counter(num(expected)) if any(op.get('numeric_reordering') for op in ops) else num(base)==num(expected)) and set(english(base))==set(english(expected)))
def clean(s):
 s=re.sub(r'<a id="[gb]-[^"]+"></a>\s*','',s);s=re.sub(r'\[사례 자료 길잡이\]\([^\n]+\)\s*','',s)
 return compact(s.replace('_v18.svg','_v17.svg'))
check('Final main text equals registered prose plus structural replay',clean(expected)==clean(new.split('# 찾아보기')[0]))
manifest=load('e-book/exports/v18/MANUSCRIPT_CHANGES.json');check('Not a prototype',not manifest['prototype'] and manifest['prose_edit_count']==len(edits) and manifest['structural_operations']==ops)
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','analysis_report_v13.json','COUNTEREXAMPLE_RESULTS.json','PLANNING_EXAMPLE.json','REGRESSION_CHECK.json','PROVENANCE.json']:
 check('Preserved companion '+name,(O/name).read_bytes()==(R/'e-book/exports/v17'/name).read_bytes())
lookup=load('e-book/exports/v18/LOOKUP.json');previous=load('e-book/exports/v17/LOOKUP.json');check('Definitions unchanged',{t['id']:t['definition'] for t in lookup['terms']}=={t['id']:t['definition'] for t in previous['terms']})
v=load('e-book/exports/v18/validation_v18.json');geom=load('e-book/exports/v18/visual_geometry_v18.json')
check('Thirteen centered figures without text collision or overflow',len(geom['figures'])==13 and not geom['issues'])
check('Printed graph labels at least12pt within tolerance',all(f['minimum_label_pt']>=11.9 for f in v['figure_layout']))
for t in lookup['terms']:
 check('Printed term page '+t['id'],t['id'] in v['lookup_pages'])
 if t['body_id']:check('Printed narrative page '+t['id'],t['body_id'] in v['lookup_pages'])
back=v['backmatter_pages'];check('Requested tail section order',list(back)==['찾아보기','용어 해설','참고자료와 계산 범위','부록 A 계산과 자료','부록 B 사례와 자료 길잡이'] and list(back.values())==sorted(back.values()))
for n in v['footnotes']:check('Real matching caller and note '+str(n['number']),n['page']==n['callerPage'] and n['marker_content'].strip('"')==str(n['number'])+'. ' and n['caller_content'].strip('"')==str(n['number']))
units=v['atomic_layout_units'];worked=[u for u in units if 'worked-record' in u['cls']];check('One intact worked decision',len(worked)==1)
check('Three capacity table groups',sum('policy-table' in u['cls'] for u in units)==3)
for ident in {u['unit'] for u in units}:check('Intact unit '+ident,len({u['page'] for u in units if u['unit']==ident})==1)
C=load('e-book/analysis/winner_v04/core_results.json');S=load('e-book/analysis/winner_v04/scenario_results.json')
P=next(r for r in C['primary_family'] if r['comparison']=='B-A');G=C['guardrail_exploratory']
def elements(name,tag):return [e for e in ET.parse(O/name).getroot().iter() if e.tag.endswith('}'+tag)]
def rect_at(name,x,y):return next(e for e in elements(name,'rect') if near(e.get('x',-999),x) and near(e.get('y',-999),y))
for arm,y in [('A',132),('B',202)]:check('Completion bar width '+arm,near(float(rect_at('winner_effect.svg',280,y).get('width'))/480*12,P['rate_'+arm]*100))
for name,point,lo,hi,origin,offset,span,width,stroke in [('winner_effect.svg',P['diff_pp'],P['ci_low_pp'],P['ci_high_pp'],130,.2,2,680,'7'),('guardrail_effect.svg',G['diff_pp'],G['ci_low_pp'],G['ci_high_pp'],100,.15,.5,720,'7')]:
 dot=elements(name,'circle')[0];line=next(e for e in elements(name,'line') if e.get('stroke-width')==stroke)
 decode=lambda x:(float(x)-origin)/width*span-offset
 for label,a,b in [('point',decode(dot.get('cx')),point),('lower',decode(line.get('x1')),lo),('upper',decode(line.get('x2')),hi)]:check('Canonical plotted '+name+' '+label,near(a,b))
for key,left in [('log',80),('truth',538)]:
 for arm,y in [('A',184),('B',258)]:check('Same-scale event bar '+key+arm,near(float(rect_at('measurement_v06.svg',left,y).get('width'))/304*700,S['case4'][key]['groups'][arm]['success']))
a=S['case5'];series=[(a['overall']['stratified_primary']['estimate'],a['overall']['stratified_primary']['wald_ci'])]+[(a['segments'][k]['difference_B_minus_A'],a['segments'][k]['newcombe_ci']) for k in ['new','existing']]
for i,((value,interval),dot,line) in enumerate(zip(series,elements('segments_v06.svg','circle'),[e for e in elements('segments_v06.svg','line') if e.get('stroke-width')=='5'])):
 decode=lambda x:((float(x)-290)/540*16-6)/100
 check('Canonical segment point and interval '+str(i),near(decode(dot.get('cx')),value) and near(decode(line.get('x1')),interval[0]) and near(decode(line.get('x2')),interval[1]))
policies=sorted([r for r in S['case6']['summaries'] if r['capacity_per_day']==60],key=lambda r:['all_A','pilot_10pct_B','all_B'].index(r['policy']))
for i,row in enumerate(policies):
 for key,left,scale in [('completed',220,1600),('net_value_krw',455,2400*10000),('waiting_fraction_of_requests',690,.30)]:check('Canonical zero-based policy bar '+row['policy']+key,near(float(rect_at('capacity_v06.svg',left,214+i*91).get('width'))/180*scale,row[key]))
figdata=load('e-book/exports/v18/FIGURE_DATA_V18.json');check('Five data-derived graphics, no new inference',figdata['count']==len(figdata['charts'])==5 and figdata['new_inference_performed'] is False)
for p,h in figdata['frozen_inputs'].items():check('Exact plotting input '+p,hashlib.sha256((R/p).read_bytes()).hexdigest()==h)
with pymupdf.open(O/'ebook_review_v18.pdf') as d:
 check('Final PDF identity',len(d)==v['pdf_pages'] and hashlib.sha256((O/'ebook_review_v18.pdf').read_bytes()).hexdigest()==v['pdf_sha256'])
 text=''.join(p.get_text() for p in d);check('No prohibited separators in PDF',not any(c in text for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'))
 for page in d:
  for link in page.get_links():
   if link['kind']==pymupdf.LINK_GOTO:check('Valid PDF internal destination',0<=link['page']<len(d))
report={'status':'passed','version':'v0.18','checks_passed':len(checks),'checks':checks,'substantive_prose_edits':len(edits),'additional_structural_and_precision_operations':len(ops),'final_pages':v['pdf_pages'],'worked_decision_page':worked[0]['page'],'backmatter_pages':back,'scope':'Registered text replay, frozen bytes, plotted canonical values, layout, footnotes and navigation. Not new full statistical recalculation, independent human review or actual reader testing.','actual_reader_test':False,'human_approved':False}
(O/'integration_validation_v18.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
