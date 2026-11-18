# -*- coding: utf-8 -*-
"""v0.12 AI 별도 코드 검수. 기존 분석 모듈은 import/exec/call하지 않는다.
실행: uv run --with scipy --with statsmodels --with numpy python <이 파일>
종료: 0=모든 검사 passed, 1=mismatch 또는 blocked, 2=실행 예외.
"""
from pathlib import Path
import sys, os, json, math, hashlib, sqlite3, platform, subprocess, traceback
from datetime import datetime, timedelta, timezone
from statistics import NormalDist
import numpy as np
import scipy
from scipy import stats
import statsmodels
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep, proportion_confint

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CHECKS = []
RESULT = {'review_type': 'AI 검토 및 기존 분석 함수를 재사용하지 않은 별도 코드 원자료 재계산',
          'scope': '기본 A/B, v03 A/B/H 및 고객별 탐색 손익. 사람 검수/출판 단계 아님.',
          'checks': CHECKS}

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def check(name, expected, actual, atol=0, rtol=0, status=None, note=''):
    def same(x, y):
        if isinstance(x, dict):
            return isinstance(y, dict) and x.keys() == y.keys() and all(same(x[k], y[k]) for k in x)
        if isinstance(x, (list, tuple)):
            return isinstance(y, (list, tuple)) and len(x) == len(y) and all(same(a, b) for a, b in zip(x, y))
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return math.isclose(x, y, abs_tol=atol, rel_tol=rtol)
        return x == y
    CHECKS.append({'name': name, 'expected': expected, 'actual': actual,
                   'tolerance': {'absolute': atol, 'relative': rtol},
                   'status': status or ('passed' if same(expected, actual) else 'mismatch'), 'note': note})

def rows(c, sql):
    return [dict(r) for r in c.execute(sql)]

def wilson(x, n, alpha):
    z = NormalDist().inv_cdf(1-alpha/2)
    p = x/n
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return center-half, center+half

def binary(g, high, low, metric, alpha=.05, family=1):
    x, n = g[high][metric], g[high]['n']
    y, m = g[low][metric], g[low]['n']
    p, q = x/n, y/m
    pooled = (x+y)/(n+m)
    z = (p-q)/math.sqrt(pooled*(1-pooled)*(1/n+1/m))
    pv = math.erfc(abs(z)/math.sqrt(2))
    l1,u1 = wilson(x,n,alpha)
    l0,u0 = wilson(y,m,alpha)
    lo = p-q-math.sqrt((p-l1)**2+(u0-q)**2)
    hi = p-q+math.sqrt((u1-p)**2+(q-l0)**2)
    label = f'{metric} {high}-{low} alpha={alpha}'
    zl,pl = proportions_ztest([x,y],[n,m],alternative='two-sided',prop_var=False)
    check(label+' pooled z vs statsmodels', [float(zl),float(pl)], [z,pv], 0, 1e-11)
    check(label+' Newcombe vs statsmodels', list(confint_proportions_2indep(x,n,y,m,method='newcomb',alpha=alpha)),[lo,hi],1e-13)
    for a,b in [(x,n),(y,m)]:
        check(label+f' Wilson {a}/{b}',list(proportion_confint(a,b,alpha=alpha,method='wilson')),list(wilson(a,b,alpha)),1e-14)
    return {'n_A':m,'n_B':n,'events_A':y,'events_B':x,'rate_A':q,'rate_B':p,
            'diff_pp':100*(p-q),'relative_lift':(p-q)/q,'p_raw':pv,'ci_level':1-alpha,
            'ci_low_pp':100*lo,'ci_high_pp':100*hi,
            **({'comparison':f'{high}-{low}','p_family':min(1,family*pv)} if family>1 else {})}

def compare_tree(expected, actual, prefix):
    for k, value in expected.items():
        if isinstance(value,(int,float)):
            check(prefix+'/'+k,value,actual.get(k),1e-8 if 'krw' in k else (1e-10 if not k.startswith('p_') else 0),1e-10)
        elif isinstance(value,dict):
            compare_tree(value,actual.get(k,{}),prefix+'/'+k)
        elif isinstance(value,list):
            for i,v in enumerate(value):
                if isinstance(v,dict):
                    compare_tree(v,actual[k][i],prefix+f'/{k}/{i}')


def audit_db(version, path, plan):
    c=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    check(version+' SQLite query_only',1,c.execute('PRAGMA query_only').fetchone()[0])
    check(version+' integrity_check',['ok'],[r[0] for r in c.execute('PRAGMA integrity_check')])
    check(version+' foreign_key_check',[],[list(r) for r in c.execute('PRAGMA foreign_key_check')])
    assignments=rows(c,'SELECT * FROM assignments')
    customers={r['customer_id']:r for r in rows(c,'SELECT * FROM customers')}
    messages=rows(c,'SELECT * FROM messages')
    v3=version=='v03'
    events=rows(c,'SELECT * FROM '+('events' if v3 else 'journey_events'))
    byid={a['assignment_id']:a for a in assignments}
    arms=['A','B','H'] if v3 else ['A','B']
    names={'booking':'booked','test_drive_completed':'completed',
           ('consent_withdrawn' if v3 else 'opt_out'):('withdrawn' if v3 else 'opted_out')}
    if v3: names['contract_signed']='contracted'
    check(version+' assignment ID uniqueness',len(assignments),len(byid))
    check(version+' assigned customer uniqueness',len(assignments),len({a['customer_id'] for a in assignments}))
    prior='prior_drive' if v3 else 'prior_test_drive'
    eligible={k for k,v in customers.items() if v['lifecycle']=='prospect' and v['sms_consent']==1 and v[prior]==0}
    check(version+' assigned eligibility violations',0,sum(a['customer_id'] not in eligible for a in assignments))
    check(version+' eligible population fully assigned',len(eligible),len({a['customer_id'] for a in assignments}&eligible))
    check(version+' assignment arm set',arms,sorted({a['arm'] for a in assignments}))
    check(version+' assignment probabilities',0,sum(not math.isclose(a['probability'],1/len(arms),abs_tol=1e-15) for a in assignments))
    date=lambda s:datetime.fromisoformat(s)
    start=lambda a:a['assigned_day'] if v3 else date(a['assigned_at'])
    cutoff=json.loads(c.execute("SELECT value_json FROM generation_manifest WHERE key='observation_cutoff_day'").fetchone()[0]) if v3 else date(plan['data_cutoff'])
    metrics={aid:{m:0 for m in names.values()} for aid in byid}
    audits={}
    for typ in sorted({e['event_type'] for e in events}):
        subset=[e for e in events if e['event_type']==typ]
        window=180 if typ=='contract_signed' else (28 if v3 else plan['outcome_window_days'])
        deltas=[]; lower=upper=beyond=orphan=0
        valid_customers=set(); valid_rows=0
        for e in subset:
            a=byid.get(e['assignment_id'])
            if a is None: orphan+=1; continue
            when=e['event_day'] if v3 else date(e['event_at'])
            d=when-start(a) if v3 else (when-start(a)).total_seconds()/86400
            deltas.append(d)
            lower+=int(d<0);upper+=int(d>window);beyond+=int(when>cutoff)
            if 0<=d<=window:
                valid_rows+=1;valid_customers.add(a['customer_id'])
                if typ in names: metrics[a['assignment_id']][names[typ]]=1
        audit={'window_days':window,'rule':'0 <= event-assignment <= window (양끝 포함)',
               'raw_rows':len(subset),'valid_rows':valid_rows,'valid_unique_customers':len(valid_customers),
               'min_lag_days':min(deltas) if deltas else None,'max_lag_days':max(deltas) if deltas else None,
               'below_lower':lower,'above_upper':upper,'after_cutoff':beyond,'orphan':orphan}
        audits[typ]=audit
        for k in ['below_lower','above_upper','after_cutoff','orphan']:
            check(version+' '+typ+' '+k,0,audit[k])
        check(version+' '+typ+' duplicate customer events',0,valid_rows-len(valid_customers),note='현재 데이터에서의 중복 사건 검사. 분석은 반복 사건이 있어도 고객당 최대 1로 집계한다.')
        check(version+' '+typ+' complete observation windows',0,sum((cutoff-start(a) if v3 else (cutoff-start(a)).total_seconds()/86400)<window for a in assignments))
    # Raw event EXISTS SQL; neither stored view nor saved analysis counts are inputs.
    cols=[]
    for typ,m in names.items():
        w=180 if typ=='contract_signed' else (28 if v3 else plan['outcome_window_days'])
        bounds=f'e.event_day>=a.assigned_day AND e.event_day<=a.assigned_day+{w}' if v3 else f'julianday(e.event_at)>=julianday(a.assigned_at) AND julianday(e.event_at)<=julianday(a.assigned_at)+{w}'
        cols.append(f"EXISTS(SELECT 1 FROM {'events' if v3 else 'journey_events'} e WHERE e.assignment_id=a.assignment_id AND e.event_type='{typ}' AND {bounds}) AS {m}")
    rawsql='SELECT a.assignment_id,'+','.join(cols)+' FROM assignments a'
    sqlrows=rows(c,rawsql)
    check(version+' Python raw-event flags vs independent raw SQL',0,sum(any(r[m]!=metrics[r['assignment_id']][m] for m in names.values()) for r in sqlrows))
    viewname='outcomes' if v3 else 'experiment_outcomes'
    viewrows=rows(c,'SELECT * FROM '+viewname)
    suffix={'booked':'booked_28','completed':'completed_28','withdrawn':'withdrawn_28','contracted':'contracted_180'} if v3 else {m:m for m in names.values()}
    check(version+' stored view vs lower-and-upper-bounded raw flags',0,sum(any(r[suffix[m]]!=metrics[r['assignment_id']][m] for m in names.values()) for r in viewrows))
    viewsql=c.execute("SELECT sql FROM sqlite_master WHERE name=?",(viewname,)).fetchone()[0]
    if v3:
        # Predicate gap is reported separately from actual-data agreement.
        has_lower='e.event_day>=a.assigned_day' in ''.join(viewsql.split()).lower()
        check('v03 stored outcomes view contains assignment lower bound',True,has_lower,
              note='원래 뷰는 상한만 검사한다. 현재 원사건에는 배정 전 사건이 없어 실제 집계는 일치하지만 미래/오염 자료에서는 위험. 원본 수정 안 함.')
    attempts={aid:0 for aid in byid}
    for m in messages:
        if m['assignment_id'] in attempts: attempts[m['assignment_id']]+=1
    check(version+' orphan messages',0,sum(m['assignment_id'] not in byid for m in messages))
    check(version+' unique message IDs',len(messages),len({m['message_id'] for m in messages}))
    check(version+' per-assignment messages: A/B exactly 1, H exactly 0',0,sum(attempts[a['assignment_id']]!=(0 if a['arm']=='H' else 1) for a in assignments))
    badtime=0;baddel=0
    for m in messages:
        a=byid[m['assignment_id']]
        t=m['attempt_day'] if v3 else date(m['attempted_at'])
        badtime+=int(t<start(a) or t>cutoff)
        if not v3 and m['delivered_at']:
            baddel+=int(date(m['delivered_at'])<t or date(m['delivered_at'])>cutoff)
    check(version+' message time after assignment and before cutoff violations',0,badtime)
    check(version+' delivery timestamp violations',0,baddel)
    groups={arm:{'arm':arm,'n':0,**{m:0 for m in names.values()}} for arm in arms}
    msgstats={arm:{'attempts':0,'delivered':0} for arm in arms}
    for a in assignments:
        g=groups[a['arm']];g['n']+=1
        for m in names.values():g[m]+=metrics[a['assignment_id']][m]
    for m in messages:
        g=msgstats[byid[m['assignment_id']]['arm']];g['attempts']+=1
        g['delivered']+=int(m['delivered'] if v3 else m['status']=='delivered')
    if v3:check('v03 H no experimental messages',0,msgstats['H']['attempts'])
    # Allocation is Bernoulli, not forced exact equality. SRM is a diagnostic, not effect significance.
    counts=[groups[a]['n'] for a in arms]
    chi=sum((n-sum(counts)/len(arms))**2/(sum(counts)/len(arms)) for n in counts)
    srm={'chi_square':chi,'df':len(arms)-1,'p':float(stats.chi2.sf(chi,len(arms)-1)),'role':'배정 진단; 0.001은 검수 경보 기준이며 원계획 성공조건 아님'}
    check(version+' allocation SRM diagnostic p>=0.001',True,srm['p']>=.001)
    info={'path':str(path),'uri_mode':'ro','raw_tables': ['assignments','customers','messages','events' if v3 else 'journey_events'],
          'population':len(customers),'eligible':len(eligible),'assigned':len(assignments),'groups':groups,
          'event_windows':audits,'message_counts':msgstats,'raw_sql':rawsql,'stored_view_sql':viewsql,'srm':srm,
          'observation_cutoff':cutoff if v3 else cutoff.isoformat()}
    if v3:
        contracts=rows(c,'SELECT * FROM contracts')
        contractmap={r['assignment_id']:r for r in contracts}
        check('v03 contract IDs unique',len(contracts),len({r['contract_id'] for r in contracts}))
        check('v03 contracts one per assignment',len(contracts),len(contractmap))
        check('v03 contracts vs valid contract-event flags',sorted(contractmap),sorted(k for k,v in metrics.items() if v['contracted']))
        contractevents={(e['assignment_id'],e['event_day']) for e in events if e['event_type']=='contract_signed'}
        check('v03 contract signed_day vs event_day',0,sum((r['assignment_id'],r['signed_day']) not in contractevents for r in contracts))
        econ=plan['economics_assumptions']
        check('v03 contractual synthetic contribution vs plan',0,sum(r['synthetic_contribution']!=econ['contribution_before_campaign'] for r in contracts))
        check('v03 contractual synthetic value vs plan',0,sum(r['synthetic_contract_value']!=econ['vehicle_revenue'] for r in contracts))
        check('v03 contract table window [0,180] violations',0,sum(not 0<=r['signed_day']-byid[r['assignment_id']]['assigned_day']<=180 for r in contracts))
        values={arm:[] for arm in arms}
        for a in assignments:
            aid=a['assignment_id'];arm=a['arm'];m=metrics[aid]
            val=econ['contribution_before_campaign']*m['contracted']-econ['drive_operating_cost']*m['completed']-econ['message_attempt_cost']*attempts[aid]
            if arm=='B':val-=econ['B_fixed_setup_cost']/groups['B']['n']
            values[arm].append(val)
        info['economics_assumptions']=econ
        info['financial_means']={a:float(np.mean(v)) for a,v in values.items()}
        info['financial_exploratory']=[]
        for high,low in [('B','A'),('A','H'),('B','H')]:
            x=np.asarray(values[high]);y=np.asarray(values[low])
            nx,ny=len(x),len(y);vx=float(x.var(ddof=1));vy=float(y.var(ddof=1))
            se=math.sqrt(vx/nx+vy/ny);diff=float(x.mean()-y.mean())
            df=(vx/nx+vy/ny)**2/((vx/nx)**2/(nx-1)+(vy/ny)**2/(ny-1))
            t=diff/se;pv=float(2*stats.t.sf(abs(t),df));q=float(stats.t.ppf(.975,df))
            lib=stats.ttest_ind(x,y,equal_var=False,alternative='two-sided')
            ci=lib.confidence_interval(.95)
            check('v03 Welch '+high+'-'+low+' t/df/p vs scipy',[float(lib.statistic),float(lib.df),float(lib.pvalue)],[t,df,pv],1e-10,1e-10)
            check('v03 Welch '+high+'-'+low+' interval vs scipy',[float(ci.low),float(ci.high)],[diff-q*se,diff+q*se],1e-7)
            item={'comparison':high+'-'+low,'currency':'KRW','diff_krw':diff,'ci95_low_krw':diff-q*se,'ci95_high_krw':diff+q*se,'p_unadjusted':pv,'welch_df':df,'standard_error_krw':se,'t':t}
            info['financial_exploratory'].append(item)
        info['financial_sensitivity']=[]
        for contribution in [500000,1000000,2000000,3000000]:
            means={arm:(contribution*g['contracted']-econ['drive_operating_cost']*g['completed']-econ['message_attempt_cost']*msgstats[arm]['attempts']-(econ['B_fixed_setup_cost'] if arm=='B' else 0))/g['n'] for arm,g in groups.items()}
            info['financial_sensitivity'].append({'assumed_contribution_per_contract':contribution,'means_krw':means,'B_minus_H_krw':means['B']-means['H']})
        for arm,g in groups.items():
            closed=(econ['contribution_before_campaign']*g['contracted']-econ['drive_operating_cost']*g['completed']-econ['message_attempt_cost']*msgstats[arm]['attempts']-(econ['B_fixed_setup_cost'] if arm=='B' else 0))/g['n']
            check('v03 customer net vs aggregate accounting '+arm,closed,info['financial_means'][arm],1e-7)
    else:
        costs={r['cost_key']:r['amount'] for r in rows(c,'SELECT * FROM cost_assumptions')}
        check('v01 costs DB vs manifest',plan['cost_assumptions_KRW'],costs)
        info['costs_KRW']={arm:{'total':costs['attempted_sms']*msgstats[arm]['attempts']+costs['completed_test_drive']*g['completed']+(costs['B_fixed_setup'] if arm=='B' else 0)} for arm,g in groups.items()}
        info['financial_scope_note']='기본 A/B에는 계약/매출/기여액이 없어 비용만 산출한다. 손익 추정은 v03만 수행하며 v01 매출을 꾸며내지 않는다.'
    c.close()
    return info


def book_audit(book, r1, r3):
    lines=book.splitlines()
    def parse(s):
        return float(s.replace(',','').replace('원','').replace('명','').strip())
    def row(prefix, occurrence=0):
        found=[(i+1,s) for i,s in enumerate(lines) if s.startswith(prefix)]
        return found[occurrence]
    def numeric(name,expected,actual,tol=0,rel=0):check('본문 '+name,expected,actual,tol,rel)
    for label,m in [('완료, 주지표','completed'),('예약, 진단','booked'),('철회, 보호','opted_out')]:
        ln,text=row('| '+label+' |');cells=[s.strip() for s in text.strip('|').split('|')];v=r1[m]
        for col,arm in [(1,'A'),(2,'B')]:
            pair=[parse(s) for s in cells[col].split('/')]
            numeric(f'L{ln} {label} {arm} 사건/배정',pair,[v['events_'+arm],v['n_'+arm]])
        numeric(f'L{ln} {label} diff',parse(cells[3]),v['diff_pp'],.00500001)
        bounds=[parse(s) for s in cells[4].strip('[]').split(',')]
        numeric(f'L{ln} {label} CI',bounds,[v['ci_low_pp'],v['ci_high_pp']],.00500001)
        numeric(f'L{ln} {label} p',parse(cells[5]),v['p_raw'],.000050001)
    for v in r3['primary_family']:
        ln,text=row('| '+v['comparison']+' |');cells=[s.strip() for s in text.strip('|').split('|')]
        numeric(f'L{ln} 완료 {v["comparison"]} diff',parse(cells[1]),v['diff_pp'],.00500001)
        bounds=[parse(s) for s in cells[2].strip('[]').split(',')]
        numeric(f'L{ln} 완료 CI',bounds,[v['ci_low_pp'],v['ci_high_pp']],.00500001)
        numeric(f'L{ln} 완료 보정 p',parse(cells[3]),v['p_family'],0,5e-6)
    for arm in ['A','B','H']:
        ln,text=next((i+1,s) for i,s in enumerate(lines) if s.startswith('| '+arm+' |') and i>next(j for j,t in enumerate(lines) if t.startswith('## 사례 3 ')));numeric(f'L{ln} {arm} 손익평균',parse(text.strip('|').split('|')[1]),r3['financial_means'][arm],.500001)
    for v in r3['financial_exploratory']:
        ln,text=row('| '+v['comparison']+' |',1);cells=[s.strip() for s in text.strip('|').split('|')]
        numeric(f'L{ln} {v["comparison"]} 손익차이',parse(cells[1]),v['diff_krw'],.500001)
        # Thousands commas are not separators; parse the comma+space between CI endpoints.
        bounds=[parse(s) for s in cells[2].replace('원','').strip().strip('[]').split(', ')]
        numeric(f'L{ln} 손익 CI',bounds,[v['ci95_low_krw'],v['ci95_high_krw']],.500001)
    for v in r3['financial_sensitivity']:
        ln,text=row('| '+format(v['assumed_contribution_per_contract'],',')+'원 |')
        cells=[s.strip() for s in text.strip('|').split('|')]
        numeric(f'L{ln} 손익 민감도',[parse(s) for s in cells[1:]],list(v['means_krw'].values())+[v['B_minus_H_krw']],.500001)
    # Read prose values, rather than using old ledger as computational inputs.
    import re
    ln,text=next((i+1,s) for i,s in enumerate(lines) if s.startswith('철회에서도 별도의 판단'))
    pattern=r'A는 약 ([\d.]+)%, B는 약 ([\d.]+)%이고 차이는 약 \+([\d.]+)pp.*?\[(-?[\d.]+),\+([\d.]+)\]pp이며 p는 약 ([\d.]+)'
    mat=re.search(pattern,text)
    check(f'본문 L{ln} 철회 수치 추출',True,mat is not None)
    if mat:
        v=r3['guardrail_exploratory'];actual=[100*v['rate_A'],100*v['rate_B'],v['diff_pp'],v['ci_low_pp'],v['ci_high_pp'],v['p_raw']]
        for i,(e,a) in enumerate(zip(map(float,mat.groups()),actual)):
            numeric(f'L{ln} 철회 항목{i}',e,a,.000050001 if i==5 else .000500001)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # uv Windows child-process execution of bundled git may be denied (WinError 5).
    # Hash existing filesystem sources directly; no git subprocess or source modification.
    protected=[]
    for base, dirs, files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','__pycache__','node_modules'} and not (Path(base)/d).relative_to(ROOT).as_posix().startswith('e-book/review')]
        for name in files:
            protected.append((Path(base)/name).relative_to(ROOT).as_posix())
    protected.sort()
    head=(ROOT/'.git/HEAD').read_text().strip()
    if head.startswith('ref: '):
        ref=head[5:]
        refpath=ROOT/'.git'/ref
        if refpath.exists():head=refpath.read_text().strip()
        else:
            packed=(ROOT/'.git/packed-refs').read_text().splitlines()
            head=next(line.split()[0] for line in packed if line.endswith(' '+ref))
    before={p:sha(ROOT/p) for p in protected}
    RESULT['source_hashes_before']=before
    RESULT['environment']={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__,
        'started_at':datetime.now(timezone.utc).isoformat(),'git_head':head,
        'command':'uv run --with scipy --with statsmodels --with numpy python "'+str(Path(__file__).resolve())+'"',
        'sqlite':sqlite3.sqlite_version}
    try:
        check('Git HEAD expected','eefdd4ee9ea026c06d65a760706a742e02407bce',RESULT['environment']['git_head'])
        p1=ROOT/'e-book/virtual-data/v01/data/manifest.json';p3=ROOT/'e-book/virtual-data/v03/experiment_plan.json'
        plan1,plan3=load(p1),load(p3)
        RESULT['plan_paths']=[str(p1),str(p3)]
        v1=audit_db('v01',ROOT/'e-book/virtual-data/v01/data/oem_crm.sqlite',plan1)
        v3=audit_db('v03',ROOT/'e-book/virtual-data/v03/data/jh_motors_v03.sqlite',plan3)
        RESULT['v01']=v1;RESULT['v03']=v3
        check('v03 plan confirmatory family',['B-A completed','A-H completed','B-H completed'],plan3['confirmatory_family'])
        v1['case1']={m:binary(v1['groups'],'B','A',m) for m in ['completed','booked','opted_out']}
        alpha=plan3['family_alpha']/len(plan3['confirmatory_family'])
        v3['primary_family']=[binary(v3['groups'],hi,lo,'completed',alpha,3) for hi,lo in [('B','A'),('A','H'),('B','H')]]
        v3['guardrail_exploratory']=binary(v3['groups'],'B','A','withdrawn')
        # Boundary fixtures test inclusion at zero/upper and exclusion before/after,
        # even when actual data have no boundary events.
        for w in [28,180]:
            for d,expected in [(-1,False),(0,True),(w,True),(w+1,False)]:
                check(f'boundary integer SQL window {w} lag {d}',expected,bool(sqlite3.connect(':memory:').execute('SELECT ? >= 0 AND ? <= ?',(d,d,w)).fetchone()[0]))
        for d,expected in [(-1,False),(0,True),(28*86400,True),(28*86400+1,False)]:
            origin=datetime(2026,1,1,tzinfo=timezone.utc);end=origin+timedelta(seconds=d)
            check(f'boundary timestamp SQL 28d lag seconds {d}',expected,bool(sqlite3.connect(':memory:').execute('SELECT julianday(?)>=julianday(?) AND julianday(?)<=julianday(?)+28',(end.isoformat(),origin.isoformat(),end.isoformat(),origin.isoformat())).fetchone()[0]))
        # The saved ledger is opened only after independent calculations have completed.
        ledgerpath=ROOT/'e-book/analysis/winner_v04/core_results.json'
        bookpath=ROOT/'e-book/exports/v12/ebook_review_v12.md'
        ledger=load(ledgerpath)
        RESULT['comparison_paths']=[str(ledgerpath),str(bookpath)]
        actual={'case1':v1['case1'],'groups':list(v3['groups'].values()),'primary_family':v3['primary_family'],
                'guardrail_exploratory':v3['guardrail_exploratory'],'financial_means':v3['financial_means'],
                'financial_exploratory':v3['financial_exploratory'],'financial_sensitivity':v3['financial_sensitivity']}
        compare_tree({k:ledger[k] for k in actual},actual,'core_results.json')
        check('v03 raw plan SHA256 vs ledger',ledger['source_plan_sha256'],sha(p3),
              note='정확한 바이트 해시는 불일치. 현재 LF 파일을 메모리에서 CRLF로만 변환하면 기존 장부 해시와 일치함을 별도 검사했다. 줄바꿈 직렬화 차이이며 내용 변조의 증거로 해석하지 않는다. 원파일은 수정하지 않았다.')
        lf=p3.read_bytes().replace(b'\r\n',b'\n')
        crlf_hash=hashlib.sha256(lf.replace(b'\n',b'\r\n')).hexdigest()
        check('v03 plan CRLF-only representation matches stored ledger hash',ledger['source_plan_sha256'],crlf_hash,
              note='해시 변환은 진단만 수행하며 기존 정확 바이트 검사 mismatch를 passed로 바꾸지 않는다.')
        con=sqlite3.connect((ROOT/'e-book/virtual-data/v03/data/jh_motors_v03.sqlite').as_uri()+'?mode=ro',uri=True)
        db_plan_hash=json.loads(con.execute("SELECT value_json FROM generation_manifest WHERE key='plan_sha256'").fetchone()[0]);con.close()
        check('v03 DB generation plan hash vs ledger',ledger['source_plan_sha256'],db_plan_hash)
        RESULT['plan_hash_diagnosis']={'current_raw_sha256':sha(p3),'stored_ledger_sha256':ledger['source_plan_sha256'],
             'stored_db_sha256':db_plan_hash,'CRLF_representation_sha256':crlf_hash,
             'conclusion':'현재 LF 직렬화와 과거 CRLF 직렬화의 차이로 정확히 설명됨. 정확 바이트 불일치는 보존.'}
        book_audit(bookpath.read_text(encoding='utf-8'),v1['case1'],v3)
    except Exception:
        RESULT['execution_error']=traceback.format_exc()
        check('execution completed','all calculations complete',RESULT['execution_error'],status='blocked')
    finally:
        after={p:sha(ROOT/p) if (ROOT/p).is_file() else None for p in protected}
        RESULT['source_hashes_after']=after
        check('all protected source hashes unchanged',before,after)
        RESULT['protected_source_count']=len(before)
    RESULT['status_counts']={s:sum(c['status']==s for c in CHECKS) for s in ['passed','mismatch','blocked']}
    RESULT['exit_status']=2 if 'execution_error' in RESULT else (1 if RESULT['status_counts']['mismatch'] or RESULT['status_counts']['blocked'] else 0)
    RESULT['limitations']=['합성 데이터 및 교육용 비용; 실제 OEM 매출/회계 손익 검증 아님.',
        '개인 독립, 고정 관측, 군집/간섭 없음에 조건부. 가구/지점 독립성을 DB 고유성만으로 입증하지 않음.',
        '철회는 미보정 탐색. 사전 안전 비열등성 설계와 한계가 없어 정식 안전 통과/실패를 계산하지 않음.',
        '손익 Welch는 미보정 탐색이며 계약/완료의 고객별 결합과 고정 비용 가정에 조건부.',
        '기본 A/B에는 계약이 없으므로 비용만 계산; v03의 계약 수익을 기본 A/B에 대입하지 않음.',
        '기존 분석 코드 함수를 가져오거나 실행하지 않았으며 기존 소스/책/DB/이전 결과는 수정하지 않음.',
        '검수 스크립트 내부 재계산은 기존 분석 코드와 별개이나 별도 사람 검수 또는 외부 검증을 뜻하지 않음.']
    (OUT/'RESULTS.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    write_review()
    print(json.dumps({'output':str(OUT),'status_counts':RESULT['status_counts'],'exit_status':RESULT['exit_status']},ensure_ascii=False))
    return RESULT['exit_status']


def write_review():
    s=RESULT['status_counts']
    lines=['# v0.12 AI 및 별도 코드 재계산 검수 — 기본 A/B·v03 A/B/H·손익','',
           f"검사: passed {s['passed']}, mismatch {s['mismatch']}, blocked {s['blocked']}. 실행 종료상태: {RESULT['exit_status']}.",
           '', '## 핵심 발견',
           '- v03 `outcomes` 뷰에는 사건 창의 배정일 하한 검사가 없다. 재계산에서는 하한·상한을 모두 적용한다. 실제 자료의 배정 전 사건 유무 및 숫자 일치 여부는 아래 검사와 RESULTS.json에 남긴다.',
           '- 계획 파일의 정확 바이트 SHA256은 장부/DB에 저장된 값과 다르다. 현재 LF 파일을 메모리에서 CRLF로만 바꾸면 저장 해시와 정확히 일치한다. 내용 변경이 아니라 줄바꿈 직렬화 차이로 설명되지만 원래 정확 바이트 검사의 mismatch는 보존한다.',
           '- 구조적 문제·바이트 해시 차이를 통계 숫자 불일치와 구별하며 실패를 숨기지 않도록 mismatch가 있으면 종료 1을 반환한다. 장부/본문 숫자의 일치 여부는 검사별 표에 기재한다.',
           '', '## 실행 중 문제 및 해결',
           '- 최초 실행은 uv Python의 bundled git 하위 프로세스 실행에서 WinError 5로 중단됐다. git 호출을 제거하고 기존 파일을 직접 읽어 SHA256 및 .git/HEAD를 확인하는 방식으로 수정한 뒤 실제 재실행했다.',
           '- 중간 검증에서 본문의 앞선 배정 표를 손익 표로 잘못 선택한 검수 파서 오류 3건을 확인했다. 사례 3 아래의 손익 표로 범위를 제한하여 수정한 후 재실행했으며 원문은 수정하지 않았다.',
           '', '## 원자료·방법',
           '- SQLite URI `mode=ro` 및 `PRAGMA query_only=ON`. 원배정/고객/원사건/메시지를 직접 읽어 Python 고객별 플래그를 만들고 별도 원사건 EXISTS SQL과 대조했다. 저장 뷰는 입력이 아니라 대조 대상이다.',
           '- 28일/180일 창은 `[배정, 배정+창]` 양끝 포함. 모든 종류의 원사건별 실제 최소/최대 경과일, 하한 미만/상한 초과/관측 종료 이후/고아/중복 건수를 기록했다. 날짜·정수 SQL의 경계 fixture도 검사했다.',
           '- 두 이항비율 pooled z = 차이 / sqrt(pooled×(1-pooled)×(1/n1+1/n0)); 양측 p는 erfc로 직접 계산했다.',
           '- Wilson 폐형식과 Newcombe 제곱합 결합식을 직접 구현하고 statsmodels pooled z/Wilson/Newcombe와 대조했다. v03 완료 가족만 alpha=0.05/3 및 min(1,3p). 철회는 alpha=0.05 미보정 탐색이다.',
           '- 고객당 순기여액 = 계약×계획 기여액 − 완료×계획 운영비 − 발송시도×계획 단가 − B고정비/nB. 고객별 결합을 유지하여 표본분산, Welch-Satterthwaite df, t구간을 계산하고 scipy ttest_ind(equal_var=False)와 대조했다. t분포 CDF/역CDF는 scipy를 사용한다.',
           '- 먼저 원자료에서 계산하고 이후 core_results.json을 읽어 숫자를 대조했다. 본문 사례 1~3 표와 철회 문장의 숫자를 파싱하여 반올림 허용오차로 대조했다.',
           '', '## 환경', '```json',json.dumps(RESULT.get('environment',{}),ensure_ascii=False,indent=2),'```','',
           f"기존 보호 소스 {RESULT.get('protected_source_count',0)}개 SHA256 전후 대조. 개별 해시는 RESULTS.json에 수록한다. 기존 파일 전체(review, .git, .venv, __pycache__, node_modules 제외)를 보호 대상으로 삼았다.",'',
           '## 계산 요약']
    for v in ['v01','v03']:
        if v not in RESULT:continue
        r=RESULT[v];lines += [f'### {v}',f"원자료: `{r['path']}`",f"모집단 {r['population']}, 적격 {r['eligible']}, 배정 {r['assigned']}.",'```json',json.dumps(r['groups'],ensure_ascii=False,indent=2),'```','메시지: `'+json.dumps(r['message_counts'],ensure_ascii=False)+'`']
        for key in ['case1','primary_family','guardrail_exploratory','financial_means','financial_exploratory','costs_KRW']:
            if key in r:lines += [f'#### {key}','```json',json.dumps(r[key],ensure_ascii=False,indent=2),'```']
    lines+=['','## 검사별 expected / actual / tolerance / status',
            '큰 해시 사전은 JSON 참조. 상대오차는 희귀 p값을 절대오차로 무시하지 않도록 사용했다. 본문 pp 2자리 ±0.005pp, 원 단위 ±0.5원 등 표시 정밀도에 따른 허용오차를 적용했다.','',
            '| 검사 | expected | actual | tolerance | status |','|---|---|---|---|---|']
    for c in CHECKS:
        def fmt(x):
            text=json.dumps(x,ensure_ascii=False)
            return (text if len(text)<1500 else 'RESULTS.json 해당 검사 참조').replace('|','\\|').replace('\n',' ')
        lines.append('| '+' | '.join([c['name'],fmt(c['expected']),fmt(c['actual']),fmt(c['tolerance']),c['status']])+' |')
        if c['note']:lines.append(f"\n> {c['name']}: {c['note']}\n")
    lines+=['','## 해석과 범위 제한']+['- '+x for x in RESULT['limitations']]
    lines+=['','완료/손익/철회는 별도 판단이다. 검수 완료가 실제 정책 채택, 사람 검수 또는 다음 출판 단계의 진행을 뜻하지 않는다.']
    if 'execution_error' in RESULT:lines+=['','## 실행 예외','```',RESULT['execution_error'],'```']
    (OUT/'REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    sys.exit(main())
