"""Independently recalculate educational fixtures, not human learning outcomes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import csv,json,hashlib,re,math,platform
import scipy,statsmodels
from scipy.stats import norm
from statsmodels.stats.proportion import proportions_ztest,confint_proportions_2indep,proportion_confint
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'e-book/review/reader_test_v01'
data=json.loads((D/'FIXTURE_CALCULATIONS.json').read_text(encoding='utf-8'))
participant=(D/'PARTICIPANT_PACKET.md').read_text(encoding='utf-8');key=(D/'FACILITATOR_KEY.md').read_text(encoding='utf-8')
compact_participant=re.sub(r'\s','',participant);compact_key=re.sub(r'\s','',key)
rows=[]
for scenario,metrics in data['fixtures'].items():
 for metric,m in metrics.items():
  a,b,na,nb=(m[x] for x in ['events_A','events_B','n_A','n_B'])
  assert all(isinstance(x,int) for x in [a,b,na,nb]) and 0<=a<=na and 0<=b<=nb
  pa,pb=a/na,b/nb;diff=100*(pb-pa)
  ci=[100*float(x) for x in confint_proportions_2indep(b,nb,a,na,method='newcomb',compare='diff',alpha=.05)]
  z,p=proportions_ztest([b,a],[nb,na],alternative='two-sided',prop_var=False)
  pooled=(a+b)/(na+nb);z2=(pb-pa)/math.sqrt(pooled*(1-pooled)*(1/na+1/nb));p2=float(2*norm.sf(abs(z2)))
  la,ua=proportion_confint(a,na,alpha=.05,method='wilson');lb,ub=proportion_confint(b,nb,alpha=.05,method='wilson')
  ci2=[100*(pb-pa-math.sqrt((pb-lb)**2+(ua-pa)**2)),100*(pb-pa+math.sqrt((ub-pb)**2+(pa-la)**2))]
  assert abs(float(p)-p2)<1e-12
  assert all(abs(x-y)<1e-10 for x,y in zip(ci,ci2))
  assert abs(100*pa-m['rate_A_pct'])<1e-10 and abs(100*pb-m['rate_B_pct'])<1e-10
  assert abs(diff-m['difference_B_minus_A_pp'])<1e-10 and abs(float(p)-m['p_two_sided_pooled_z'])<1e-12
  assert all(abs(x-y)<1e-10 for x,y in zip(ci,m['ci95_newcombe_pp']))
  tokens=[f'{a}/{na}',f'{b}/{nb}',f'{pa*100:.2f}%',f'{pb*100:.2f}%',f'{diff:+.2f}pp',f'[{ci[0]:+.2f},{ci[1]:+.2f}]pp',f'{float(p):.6f}']
  for token in tokens:
   assert token in compact_participant,(scenario,metric,'participant',token)
   assert token in compact_key,(scenario,metric,'key',token)
  rows.append({'scenario':scenario,'metric':metric,'difference_pp':diff,'ci95_pp':ci,'p':float(p),'document_tokens_matched':True})
assert len(rows)==5
assert len(re.findall(r'^\| C[1-6] \|',key,re.M))==6
assert len(re.findall(r'^\| F[1-4] ',key,re.M))==4
with (D/'OBSERVATION_TEMPLATE.csv').open(encoding='utf-8-sig',newline='') as f:
 records=list(csv.DictReader(f))
assert records==[],'Real observations must never be fabricated during preparation'
for p in list(D.glob('*.md'))+[ROOT/'e-book/review/publication/CLAIM_SCOPE_AND_SYNTHETIC_AUDIT.md']:
 assert not any(x in p.read_text(encoding='utf-8') for x in '\u00b7\u2022\u2027\u318d\u22c5\u30fb'),p
baseline=[]
for source in data['source_design']['sources_read']:
 p=ROOT/source['path'];h=hashlib.sha256(p.read_bytes()).hexdigest()
 baseline.append({'path':source['path'],'recorded_at_task_development':source['sha256'],'current_sha256':h,'same_as_recorded':h==source['sha256'],'scope':'Recorded development baseline. The publication brief was subsequently updated to record approved terminology; current reading assignment is v08.'})
book=ROOT/'e-book/exports/v08/ebook_review_v08.pdf';v=json.loads((book.parent/'validation_v08.json').read_text(encoding='utf-8'));assert hashlib.sha256(book.read_bytes()).hexdigest()==v['pdf_sha256']
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.is_file() and p.name!='PREPARATION_VALIDATION.json'}
report={'status':'preparation verified; recruitment and actual task performance NOT conducted','checked_at_seoul':datetime.now(timezone(timedelta(hours=9),'Asia/Seoul')).isoformat(),'assigned_reading_candidate':{'path':book.relative_to(ROOT).as_posix(),'sha256':v['pdf_sha256'],'version':'0.8 author review','approval':'recruitment and exact reading/packet version still require human approval'},'environment':{'python':platform.python_version(),'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},'calculated_fixture_metrics':rows,'competencies':6,'critical_error_rules':4,'observation_rows':len(records),'source_baselines':baseline,'file_sha256':files,'scope':'Counts, proportions/effects, inferential outputs and document display matching; not independent human review, validation of scoring cutoffs or measurement of learning effect'}
(D/'PREPARATION_VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
