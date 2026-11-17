"""Educational synthetic OEM CRM database. No external dependencies."""
import csv
import os
import json
import math
import random
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(os.environ.get('OEM_OUTPUT_ROOT', str(Path(__file__).resolve().parents[1] / 'e-book' / 'virtual-data' / 'v01')))
DATA = ROOT / 'data'
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / 'oem_crm.sqlite'
if DB.exists():
    raise SystemExit('Database already exists; refusing to overwrite. Use a fresh project copy.')
SEED = 20261116
rng = random.Random(SEED)
manifest = {
    'version': '0.1', 'author': '허재혁', 'synthetic': True,
    'company': 'JH Motors (교육용 작업명, 상표 미검증)', 'seed': SEED,
    'timezone': 'Asia/Seoul', 'currency': 'KRW',
    'customers': 12000, 'experiment_id': 'EXP_TD_001',
    'enrollment': '2026-09-01 through 2026-09-28',
    'data_cutoff': '2026-10-26T23:59:59+09:00', 'outcome_window_days': 28,
    'design': 'Independent Bernoulli randomization, P(B)=0.5; intention-to-treat analysis.',
    'eligibility': 'Marketing SMS consent, prospect lifecycle, no completed test drive at baseline.',
    'primary': 'At least one completed test drive within 28 days of assignment, among all assigned customers.',
    'secondary': 'Booked test drive within 28 days.',
    'guardrail': 'Opt out within 28 days; excludes later messages in a real deployment.',
    'arm_A': 'Vehicle value focused invitation', 'arm_B': 'Booking convenience focused invitation',
    'delivery_probability': 0.96,
    'booking_probability_if_delivered': {'A': 0.12, 'B': 0.15},
    'booking_probability_condition': 'Delivered and not opted out in the preceding synthetic event stage.',
    'completion_probability_given_booking': 0.75,
    'optout_probability_if_delivered': {'A': 0.008, 'B': 0.010},
    'cost_assumptions_KRW': {'attempted_sms': 20, 'completed_test_drive': 15000, 'B_fixed_setup': 200000},
    'limitations': [
        'Probabilities and costs are instructional assumptions, not market benchmarks.',
        'The conditional booking and completion mechanism is deliberately simplified.',
        'No generated heterogeneity of treatment effect by segment.',
        'No orders, vehicle revenue, LTV or causal sales uplift is inferred.',
        'Capacity, spillovers, households and repeated experiments are not modeled.',
        'No planned power or business effect threshold has been validated for this dataset.',
        'This is a post-generated teaching dataset, not a preregistered real experiment.'
    ]
}
con = sqlite3.connect(DB)
con.execute('PRAGMA foreign_keys=ON')
con.executescript('''
CREATE TABLE company(company_id TEXT PRIMARY KEY, name TEXT NOT NULL, synthetic INTEGER NOT NULL CHECK(synthetic=1));
CREATE TABLE dealerships(dealer_id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES company, region TEXT NOT NULL);
CREATE TABLE vehicle_models(model_id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES company, body_style TEXT NOT NULL);
CREATE TABLE customers(customer_id TEXT PRIMARY KEY, dealer_id TEXT NOT NULL REFERENCES dealerships, model_id TEXT NOT NULL REFERENCES vehicle_models, lifecycle TEXT NOT NULL CHECK(lifecycle IN ('prospect','owner')), sms_consent INTEGER NOT NULL CHECK(sms_consent IN (0,1)), prior_test_drive INTEGER NOT NULL CHECK(prior_test_drive IN (0,1)), lead_source TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE experiments(experiment_id TEXT PRIMARY KEY, name TEXT NOT NULL, primary_metric TEXT NOT NULL, window_days INTEGER NOT NULL, data_cutoff TEXT NOT NULL);
CREATE TABLE assignments(assignment_id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL REFERENCES experiments, customer_id TEXT NOT NULL REFERENCES customers, arm TEXT NOT NULL CHECK(arm IN ('A','B')), assigned_at TEXT NOT NULL, probability REAL NOT NULL CHECK(probability>0 AND probability<1), UNIQUE(experiment_id,customer_id));
CREATE TABLE messages(message_id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL UNIQUE REFERENCES assignments, attempted_at TEXT NOT NULL, delivered_at TEXT, status TEXT NOT NULL CHECK(status IN ('delivered','failed')));
CREATE TABLE journey_events(event_id INTEGER PRIMARY KEY, assignment_id TEXT NOT NULL REFERENCES assignments, event_type TEXT NOT NULL CHECK(event_type IN ('booking','test_drive_completed','booking_cancelled','opt_out')), event_at TEXT NOT NULL);
CREATE TABLE cost_assumptions(cost_key TEXT PRIMARY KEY, amount REAL NOT NULL CHECK(amount>=0), currency TEXT NOT NULL, basis TEXT NOT NULL, source TEXT NOT NULL);
CREATE INDEX ix_events_assignment_type ON journey_events(assignment_id,event_type);
CREATE VIEW experiment_outcomes AS
SELECT a.assignment_id,a.experiment_id,a.customer_id,a.arm,a.assigned_at,c.dealer_id,c.model_id,c.lead_source,
MAX(CASE WHEN e.event_type='booking' THEN 1 ELSE 0 END) AS booked,
MAX(CASE WHEN e.event_type='test_drive_completed' THEN 1 ELSE 0 END) AS completed,
MAX(CASE WHEN e.event_type='opt_out' THEN 1 ELSE 0 END) AS opted_out
FROM assignments a JOIN customers c USING(customer_id)
LEFT JOIN journey_events e ON e.assignment_id=a.assignment_id
AND julianday(e.event_at)>=julianday(a.assigned_at)
AND julianday(e.event_at)<=julianday(a.assigned_at)+28
GROUP BY a.assignment_id;
''')
con.execute('INSERT INTO company VALUES (?,?,?)', ('CO_001','JH Motors',1))
for i in range(12):
    con.execute('INSERT INTO dealerships VALUES (?,?,?)',(f'D{i+1:02d}','CO_001',['수도권','중부','남부'][i%3]))
for model,body in [('M01','SUV'),('M02','Sedan'),('M03','Crossover')]:
    con.execute('INSERT INTO vehicle_models VALUES (?,?,?)',(model,'CO_001',body))
con.execute('INSERT INTO experiments VALUES (?,?,?,?,?)',('EXP_TD_001','시승 편의 안내 A/B',manifest['primary'],28,manifest['data_cutoff']))
for key,amount in manifest['cost_assumptions_KRW'].items():
    con.execute('INSERT INTO cost_assumptions VALUES (?,?,?,?,?)',(key,amount,'KRW',key,'교육용 가정; 실제 가격 아님'))

def stamp(dt):
    return dt.isoformat(timespec='seconds')+'+09:00'

start = datetime(2026,9,1,10)
assignment_no = 0
for i in range(1,12001):
    cid=f'C{i:06d}'
    lifecycle='prospect' if rng.random()<0.8 else 'owner'
    consent=int(rng.random()<0.85)
    prior=int(rng.random()<0.2)
    con.execute('INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)',(
        cid,f'D{rng.randint(1,12):02d}',rng.choice(['M01','M02','M03']),lifecycle,consent,prior,
        rng.choice(['website','event','referral']),stamp(start-timedelta(days=rng.randint(1,120)))))
    if lifecycle!='prospect' or not consent or prior:
        continue
    assignment_no+=1
    aid=f'AS{assignment_no:06d}'
    arm='B' if rng.random()<0.5 else 'A'
    at=start+timedelta(days=rng.randrange(28),minutes=rng.randrange(480))
    con.execute('INSERT INTO assignments VALUES (?,?,?,?,?,?)',(aid,'EXP_TD_001',cid,arm,stamp(at),0.5))
    sent=at+timedelta(minutes=1)
    delivered=rng.random()<0.96
    con.execute('INSERT INTO messages VALUES (?,?,?,?,?)',(f'MSG{assignment_no:06d}',aid,stamp(sent),stamp(sent+timedelta(seconds=3)) if delivered else None,'delivered' if delivered else 'failed'))
    if not delivered:
        continue
    # Opt-outs precede booking here; opted-out customers receive no additional messages.
    if rng.random()<manifest['optout_probability_if_delivered'][arm]:
        con.execute('INSERT INTO journey_events(assignment_id,event_type,event_at) VALUES (?,?,?)',(aid,'opt_out',stamp(sent+timedelta(hours=rng.randint(1,20)))))
        continue
    if rng.random()<manifest['booking_probability_if_delivered'][arm]:
        booked=sent+timedelta(days=rng.randint(1,7))
        con.execute('INSERT INTO journey_events(assignment_id,event_type,event_at) VALUES (?,?,?)',(aid,'booking',stamp(booked)))
        event='test_drive_completed' if rng.random()<0.75 else 'booking_cancelled'
        con.execute('INSERT INTO journey_events(assignment_id,event_type,event_at) VALUES (?,?,?)',(aid,event,stamp(booked+timedelta(days=rng.randint(1,14)))))
con.commit()
checks={}
checks['integrity_ok']=con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
checks['foreign_key_violations']=len(con.execute('PRAGMA foreign_key_check').fetchall())
checks['ineligible_assignments']=con.execute("SELECT COUNT(*) FROM assignments JOIN customers USING(customer_id) WHERE lifecycle!='prospect' OR sms_consent!=1 OR prior_test_drive!=0").fetchone()[0]
checks['event_time_violations']=con.execute('SELECT COUNT(*) FROM journey_events e JOIN assignments a USING(assignment_id) WHERE julianday(e.event_at)<julianday(a.assigned_at) OR julianday(e.event_at)>julianday(a.assigned_at)+28').fetchone()[0]
checks['unmatured_assignments']=con.execute('SELECT COUNT(*) FROM assignments WHERE julianday(assigned_at)+28>julianday(?)',(manifest['data_cutoff'],)).fetchone()[0]
checks['completion_without_booking']=con.execute("SELECT COUNT(*) FROM journey_events e WHERE event_type='test_drive_completed' AND NOT EXISTS (SELECT 1 FROM journey_events b WHERE b.assignment_id=e.assignment_id AND b.event_type='booking' AND julianday(b.event_at)<=julianday(e.event_at))").fetchone()[0]
checks['message_status_violations']=con.execute("SELECT COUNT(*) FROM messages WHERE (status='delivered' AND delivered_at IS NULL) OR (status='failed' AND delivered_at IS NOT NULL)").fetchone()[0]
checks['rows_outcome_equals_assignments']=con.execute('SELECT COUNT(*) FROM experiment_outcomes').fetchone()[0]==assignment_no
objects=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name")]
counts={name:con.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] for name in objects}
summary=[dict(zip(['arm','assigned','booked','completed','opted_out'],row)) for row in con.execute('SELECT arm,COUNT(*),SUM(booked),SUM(completed),SUM(opted_out) FROM experiment_outcomes GROUP BY arm ORDER BY arm')]
for row in summary:
    row['completion_rate']=row['completed']/row['assigned']
# Two-sided normal approximation to binomial allocation test; screening only.
a,b=[row['assigned'] for row in summary]
z=(b-(a+b)*0.5)/math.sqrt((a+b)*0.25)
srm_p=math.erfc(abs(z)/math.sqrt(2))
checks['allocation_screen_p_normal_approx']=srm_p
checks['all_structural_checks_pass']=checks['integrity_ok'] and checks['rows_outcome_equals_assignments'] and all(checks[k]==0 for k in ['foreign_key_violations','ineligible_assignments','event_time_violations','unmatured_assignments','completion_without_booking','message_status_violations'])
assert checks['all_structural_checks_pass'], checks
CSV=DATA/'csv'
CSV.mkdir(exist_ok=True)
for name in objects:
    cur=con.execute(f'SELECT * FROM {name} ORDER BY 1')
    with (CSV/f'{name}.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        writer.writerow([x[0] for x in cur.description])
        writer.writerows(cur)
report={'checks':checks,'row_counts':counts,'experiment_summary':summary,'interpretation':'Descriptive results only; not an approved rollout decision or evidence of real OEM performance.'}
for file,obj in [('manifest.json',manifest),('validation.json',report)]:
    (DATA/file).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
con.close()
print(json.dumps({'database':str(DB),'report':report},ensure_ascii=False,indent=2))
