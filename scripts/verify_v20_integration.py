"""Verify actual v20 content replay, protected statistics and layout."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,math,xml.etree.ElementTree as ET
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v20';D=R/'e-book/manuscript/development_v20';checks=[]
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def check(name,ok):checks.append({'check':name,'pass':bool(ok)});assert ok,name
def compact(s):return re.sub(r'\s+','',s)
def near(a,b):return math.isclose(float(a),float(b),abs_tol=1e-9,rel_tol=1e-10)
relocation=load('e-book/manuscript/development_v20/BASELINE_RELOCATION.json') if (D/'BASELINE_RELOCATION.json').exists() else {'paths':[]}
relocated={row['original_path']:row['current_path'] for row in relocation['paths']}
for path,h in load('e-book/manuscript/development_v20/BASELINE.json')['hashes'].items():check('Frozen '+path,hashlib.sha256((R/relocated.get(path,path)).read_bytes()).hexdigest()==h)
old=(R/'e-book/exports/v19/ebook_review_v19.md').read_text(encoding='utf-8');new=(O/'ebook_review_v20.md').read_text(encoding='utf-8');expected=old.split('# 찾아보기')[0];all_stages=[]
numeric=lambda t:Counter(re.findall(r'(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?',t))
for name in ['01_COMPRESSION','02_GUIDED_RECORD','03_TRANSFER']:
 items=load('e-book/manuscript/development_v20/'+name+'.json');before=expected
 for e in items:check('Replay '+e['id'],expected.count(e['before'])==1 and e['before']!=e['after']);expected=expected.replace(e['before'],e['after'])
 if name=='01_COMPRESSION':check('Repeated exposition actually compressed',sum(len(e['after']) for e in items)<sum(len(e['before']) for e in items))
 if name=='03_TRANSFER':check('Transferred problem design preserves numerical multiset',numeric(before)==numeric(expected))
 all_stages.append({'name':name,'edits':items,'before_characters':len(before),'after_characters':len(expected)})
edits=all_stages[0]['edits'];ops=all_stages[1]['edits']+all_stages[2]['edits']
def clean(s):
 s=re.sub(r'<a id="[gb]-[^"]+"></a>\s*','',s);s=re.sub(r'\[사례 자료 길잡이\]\([^\n]+\)\s*','',s)
 return compact(s.replace('_v20.svg','_v19.svg'))
check('Exact full main-text replay',clean(expected)==clean(new.split('# 찾아보기')[0]))
m=load('e-book/exports/v20/MANUSCRIPT_CHANGES.json');check('All three stages applied in order',m['prototype'] is False and m['stages']==all_stages and m['stage_order']==[t['name'] for t in all_stages])
check('One record revised across chapters two to four',{e['chapter'] for e in all_stages[1]['edits']}=={2,3,4})
def chapter(t,n):return re.search(r'^# '+str(n)+r'장 .*?(?=^# |\Z)',t,re.M|re.S).group()
for n in [1,5,6,7,11]:check('Unedited chapter preserved '+str(n),clean(chapter(old,n))==clean(chapter(new,n)))
old_record=chapter(old,12).split('**완성된 한 장 결정문 예시**')[1];new_record=chapter(new,12).split('**완성된 한 장 결정문 예시**')[1]
check('Standalone completed decision preserved',clean(old_record)==clean(new_record))
old_context=load('e-book/manuscript/development_v19/READING_LAYERS.json')
for e in old_context:check('Earlier technical source retained '+str(e['chapter'])+' '+e['before'][:25],e['before'] in new.split('# 부록 A 계산과 자료')[1])
check('Transfer asks before classification',new.index('두 표를 모두 읽은 뒤 해설로 넘어가기 전에')<new.index('| 조건 | A 완료와 배정 |')<new.index('조건 가에서는 현재 대상과 정책 범위'))
problem=chapter(new,8).split('| 조건 | A와 B의 철회 |')[1].split('조건 가에서는')[0];check('Judgments hidden from problem table','실행 후보' not in problem and '현재 판단' not in problem)
check('Changed-condition reuse task has feedback',new.index('해설을 읽기 전에 이전 기록에서')<new.index('자신의 답에서 정책과 고객 및 사건의 정의'))
for name in ['MINIMUM_RECORD.pdf','MINIMUM_RECORD.html','MINIMUM_RECORD.md','MINIMUM_RECORD_WORKED.md','analysis_report_v13.json','COUNTEREXAMPLE_RESULTS.json','PLANNING_EXAMPLE.json','REGRESSION_CHECK.json','PROVENANCE.json']:
 check('Preserved companion '+name,(O/name).read_bytes()==(R/'e-book/exports/v19'/name).read_bytes())
for name in ['winner_effect.svg','guardrail_effect.svg','measurement_v06.svg','segments_v06.svg','capacity_v06.svg']:
 check('Unchanged data graphic '+name,(O/name).read_bytes()==(R/'e-book/exports/v19'/name).read_bytes())
lookup=load('e-book/exports/v20/LOOKUP.json');previous=load('e-book/exports/v19/LOOKUP.json');check('Definitions unchanged',{t['id']:t['definition'] for t in lookup['terms']}=={t['id']:t['definition'] for t in previous['terms']})
v=load('e-book/exports/v20/validation_v20.json');geom=load('e-book/exports/v20/visual_geometry_v20.json')
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
figdata=load('e-book/exports/v20/FIGURE_DATA_V20.json');check('Five data-derived graphics, no new inference',figdata['count']==len(figdata['charts'])==5 and figdata['new_inference_performed'] is False)
for p,h in figdata['frozen_inputs'].items():check('Exact plotting input '+p,hashlib.sha256((R/p).read_bytes()).hexdigest()==h)
with pymupdf.open(O/'ebook_review_v20.pdf') as d:
 check('Final PDF identity',len(d)==v['pdf_pages'] and hashlib.sha256((O/'ebook_review_v20.pdf').read_bytes()).hexdigest()==v['pdf_sha256'])
 text=''.join(p.get_text() for p in d);check('No prohibited separators in PDF',not any(c in text for c in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'))
 for page in d:
  for link in page.get_links():
   if link['kind']==pymupdf.LINK_GOTO:check('Valid PDF internal destination',0<=link['page']<len(d))
report={'status':'passed','version':'v0.20','checks_passed':len(checks),'checks':checks,'compression_edits':len(edits),'guided_and_transfer_edits':len(ops),'final_pages':v['pdf_pages'],'worked_decision_page':worked[0]['page'],'backmatter_pages':back,'scope':'Registered text replay, frozen bytes, plotted canonical values, layout, footnotes and navigation. Not new full statistical recalculation, independent human review or actual reader testing.','actual_reader_test':False,'human_approved':False}
(O/'integration_validation_v20.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
