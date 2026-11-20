"""Prepare checks that replay all three v20 stages in their approved order."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'scripts'
s=(S/'verify_v19_integration.py').read_text(encoding='utf-8');tail=s[s.index("lookup=load('e-book/exports/v19/LOOKUP.json')"):]
tail=tail.replace('v19','v20').replace('V19','V20').replace('v0.19','v0.20').replace('e-book/exports/v18/LOOKUP.json','e-book/exports/v19/LOOKUP.json').replace('e-book/build-inputs/v18/LOOKUP.json','e-book/exports/v19/LOOKUP.json')
tail=tail.replace("'reading_layer_edits':len(edits),'worked_insertions':len(ops)","'compression_edits':len(edits),'guided_and_transfer_edits':len(ops)")
prefix='''"""Verify actual v20 content replay, protected statistics and layout."""
from pathlib import Path
from collections import Counter
import json,re,hashlib,math,xml.etree.ElementTree as ET
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'e-book/exports/v20';D=R/'e-book/manuscript/development_v20';checks=[]
def load(p):return json.loads((R/p).read_text(encoding='utf-8'))
def check(name,ok):checks.append({'check':name,'pass':bool(ok)});assert ok,name
def compact(s):return re.sub(r'\\s+','',s)
def near(a,b):return math.isclose(float(a),float(b),abs_tol=1e-9,rel_tol=1e-10)
relocation=load('e-book/manuscript/development_v20/BASELINE_RELOCATION.json') if (D/'BASELINE_RELOCATION.json').exists() else {'paths':[]}
relocated={row['original_path']:row['current_path'] for row in relocation['paths']}
for path,h in load('e-book/manuscript/development_v20/BASELINE.json')['hashes'].items():check('Frozen '+path,hashlib.sha256((R/relocated.get(path,path)).read_bytes()).hexdigest()==h)
old=(R/'e-book/exports/v19/ebook_review_v19.md').read_text(encoding='utf-8');new=(O/'ebook_review_v20.md').read_text(encoding='utf-8');expected=old.split('# 찾아보기')[0];all_stages=[]
numeric=lambda t:Counter(re.findall(r'(?<![A-Za-z])[-+]?\\d[\\d,]*(?:\\.\\d+)?',t))
for name in ['01_COMPRESSION','02_GUIDED_RECORD','03_TRANSFER']:
 items=load('e-book/manuscript/development_v20/'+name+'.json');before=expected
 for e in items:check('Replay '+e['id'],expected.count(e['before'])==1 and e['before']!=e['after']);expected=expected.replace(e['before'],e['after'])
 if name=='01_COMPRESSION':check('Repeated exposition actually compressed',sum(len(e['after']) for e in items)<sum(len(e['before']) for e in items))
 if name=='03_TRANSFER':check('Transferred problem design preserves numerical multiset',numeric(before)==numeric(expected))
 all_stages.append({'name':name,'edits':items,'before_characters':len(before),'after_characters':len(expected)})
edits=all_stages[0]['edits'];ops=all_stages[1]['edits']+all_stages[2]['edits']
def clean(s):
 s=re.sub(r'<a id="[gb]-[^\"]+\"></a>\\s*','',s);s=re.sub(r'\\[사례 자료 길잡이\\]\\([^\\n]+\\)\\s*','',s)
 return compact(s.replace('_v20.svg','_v19.svg'))
check('Exact full main-text replay',clean(expected)==clean(new.split('# 찾아보기')[0]))
m=load('e-book/exports/v20/MANUSCRIPT_CHANGES.json');check('All three stages applied in order',m['prototype'] is False and m['stages']==all_stages and m['stage_order']==[t['name'] for t in all_stages])
check('One record revised across chapters two to four',{e['chapter'] for e in all_stages[1]['edits']}=={2,3,4})
def chapter(t,n):return re.search(r'^# '+str(n)+r'장 .*?(?=^# |\\Z)',t,re.M|re.S).group()
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
'''
(S/'verify_v20_integration.py').write_text(prefix+tail,encoding='utf-8',newline='\n')
print('v20 ordered-content, preserved-numbers and inherited visual regression checks prepared')
