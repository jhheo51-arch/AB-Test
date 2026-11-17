"""Build a larger, planned synthetic OEM trial; preserve earlier versions."""
import csv
import hashlib
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'e-book/virtual-data/v03'
planpath=OUT/'experiment_plan.json'
plan=json.loads(planpath.read_text(encoding='utf-8'))
DATA=OUT/'data';DATA.mkdir(exist_ok=True)
target=DATA/'jh_motors_v03.sqlite'
staging=DATA/'jh_motors_v03.building.sqlite'
if target.exists() or staging.exists():raise SystemExit('Output exists, refusing overwrite')
prng=random.Random(plan['seeds']['population'])
arng=random.Random(plan['seeds']['assignment'])
drng=random.Random(plan['seeds']['delivery'])
orng=random.Random(plan['seeds']['outcomes'])
trng=random.Random(plan['seeds']['timing'])
con=sqlite3.connect(staging);con.execute('PRAGMA foreign_keys=ON')
con.executescript('''
CREATE TABLE customers(customer_id TEXT PRIMARY KEY,region TEXT NOT NULL,interest_model TEXT NOT NULL,lifecycle TEXT NOT NULL,sms_consent INTEGER NOT NULL CHECK(sms_consent IN(0,1)),prior_drive INTEGER NOT NULL CHECK(prior_drive IN(0,1)),dealer_id TEXT NOT NULL,lead_source TEXT NOT NULL);
CREATE TABLE assignments(assignment_id TEXT PRIMARY KEY,customer_id TEXT UNIQUE NOT NULL REFERENCES customers,arm TEXT NOT NULL CHECK(arm IN('A','B','H')),assigned_day INTEGER NOT NULL CHECK(assigned_day>=0),probability REAL NOT NULL);
CREATE TABLE messages(message_id TEXT PRIMARY KEY,assignment_id TEXT UNIQUE NOT NULL REFERENCES assignments,attempt_day INTEGER NOT NULL,delivered INTEGER NOT NULL CHECK(delivered IN(0,1)));
CREATE TABLE events(event_id INTEGER PRIMARY KEY,assignment_id TEXT NOT NULL REFERENCES assignments,event_type TEXT NOT NULL CHECK(event_type IN('booking','test_drive_completed','contract_signed','consent_withdrawn')),event_day INTEGER NOT NULL);
CREATE TABLE contracts(contract_id TEXT PRIMARY KEY,assignment_id TEXT UNIQUE NOT NULL REFERENCES assignments,signed_day INTEGER NOT NULL,synthetic_contract_value INTEGER NOT NULL,synthetic_contribution INTEGER NOT NULL);
CREATE TABLE external_sources(source_id TEXT PRIMARY KEY,url TEXT NOT NULL,grain TEXT NOT NULL,allowed_analytic_role TEXT NOT NULL,restriction TEXT NOT NULL);
CREATE TABLE generation_manifest(key TEXT PRIMARY KEY,value_json TEXT NOT NULL);
CREATE INDEX ix_events_assignment ON events(assignment_id,event_type);
CREATE VIEW outcomes AS SELECT a.assignment_id,a.customer_id,a.arm,a.assigned_day,
 MAX(CASE WHEN e.event_type='booking' AND e.event_day<=a.assigned_day+28 THEN 1 ELSE 0 END) AS booked_28,
 MAX(CASE WHEN e.event_type='test_drive_completed' AND e.event_day<=a.assigned_day+28 THEN 1 ELSE 0 END) AS completed_28,
 MAX(CASE WHEN e.event_type='consent_withdrawn' AND e.event_day<=a.assigned_day+28 THEN 1 ELSE 0 END) AS withdrawn_28,
 MAX(CASE WHEN e.event_type='contract_signed' AND e.event_day<=a.assigned_day+180 THEN 1 ELSE 0 END) AS contracted_180
 FROM assignments a LEFT JOIN events e USING(assignment_id) GROUP BY a.assignment_id;
CREATE VIEW early_snapshot_day28 AS SELECT a.assignment_id,a.arm,a.assigned_day,
 CASE WHEN a.assigned_day+28<=28 THEN 1 ELSE 0 END AS primary_window_mature,
 CASE WHEN a.assigned_day+180<=28 THEN 1 ELSE 0 END AS contract_window_mature,
 MAX(CASE WHEN e.event_type='test_drive_completed' AND e.event_day<=28 THEN 1 ELSE 0 END) AS completion_observed_so_far
 FROM assignments a LEFT JOIN events e USING(assignment_id) WHERE a.assigned_day<=28 GROUP BY a.assignment_id;
''')
# Freeze the population before drawing any assignments or outcomes.
customers=[]
for i in range(1,plan['population_n']+1):
    customers.append((f'JH{i:07d}',prng.choices(['수도권','중부','남부'],weights=[.55,.25,.20])[0],prng.choice(['SUV','Sedan','Crossover']),'prospect' if prng.random()<.8 else 'owner',int(prng.random()<.85),int(prng.random()>=.8),f'D{prng.randint(1,24):02d}',prng.choice(['website','event','referral'])))
con.executemany('INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)',customers)
eligible=[c for c in customers if c[3]=='prospect' and c[4]==1 and c[5]==0]
assign=[]
for i,c in enumerate(eligible):
    assign.append((f'V3A{i+1:07d}',c[0],arng.choice(['A','B','H']),i//plan['enroll_per_day_cap'],1/3))
con.executemany('INSERT INTO assignments VALUES (?,?,?,?,?)',assign)
counts=Counter(a[2] for a in assign)
required=next(x['n_each_numeric_power'] for x in plan['sample_size_grid'] if x['scenario']=='drive_primary' and x['family_comparisons']==3)
assert min(counts.values())>=required,'Planned primary sample infeasible; stop rather than generate winner'
msgs=[];events=[];contracts=[]
probs=plan['probability_assumptions'];cost=plan['economics_assumptions']
for aid,cid,arm,day,prob in assign:
    if arm!='H':msgs.append((f'M{aid}',aid,day,int(drng.random()<probs['delivery'])))
    # Policy-level outcomes can occur organically even after non-delivery.
    if orng.random()<probs['booking'][arm]:
        booked=day+trng.randint(1,7);events.append((aid,'booking',booked))
        if orng.random()<probs['completion_given_booking']:
            complete=booked+trng.randint(1,21);events.append((aid,'test_drive_completed',complete))
            if orng.random()<probs['contract_given_completion'][arm]:
                signed=complete+trng.randint(30,150);events.append((aid,'contract_signed',signed))
                contracts.append((f'K{aid}',aid,signed,cost['vehicle_revenue'],cost['contribution_before_campaign']))
    if orng.random()<probs['opt_out'][arm]:events.append((aid,'consent_withdrawn',day+trng.randint(1,28)))
con.executemany('INSERT INTO messages VALUES (?,?,?,?)',msgs)
con.executemany('INSERT INTO events(assignment_id,event_type,event_day) VALUES (?,?,?)',events)
con.executemany('INSERT INTO contracts VALUES (?,?,?,?,?)',contracts)
sources=[('hyundai_sales','https://www.hyundai.com/worldwide/en/company/ir/ir-resources/sales-results','model/month aggregate','business context only','Not CRM conversions, assignments, campaign effects or individual customer mix'),('kia_sales','https://worldwide.kia.com/en/company/investor-relations/library/performance-and-plans','monthly sales library','public context and proposed experiments','Individual download contents not checked in this version'),('toyota_service','https://global.toyota/pages/global_toyota/sustainability/report/sdb/sdb25_en.pdf','service/survey aggregates','service workflow and response bias questions','Not a randomized CRM dataset; no customer-level linkage')]
con.executemany('INSERT INTO external_sources VALUES (?,?,?,?,?)',sources)
manifest={'plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),'population_frozen_before_assignments':True,'independent_random_streams':plan['seeds'],'observation_cutoff_day':240,'time_unit':'integer days since hypothetical campaign launch; no actual calendar or real campaign','probabilities_are_policy_level_ITT':True,'background_withdrawal_H':'Organic consent withdrawal without experimental message, other campaign contacts not modeled','economic_status':'Synthetic contract values, not delivered/recognized vehicle revenue. No actual manufacturer costs.','rows':{'customers':len(customers),'eligible':len(eligible),'arms':dict(counts),'messages':len(msgs),'events':len(events),'contracts':len(contracts)}}
for k,v in manifest.items():con.execute('INSERT INTO generation_manifest VALUES (?,?)',(k,json.dumps(v,ensure_ascii=False)))
con.commit()
checks={
'integrity':con.execute('PRAGMA integrity_check').fetchone()[0]=='ok',
'foreign_key_errors':len(con.execute('PRAGMA foreign_key_check').fetchall()),
'ineligible':con.execute("SELECT COUNT(*) FROM assignments JOIN customers USING(customer_id) WHERE lifecycle!='prospect' OR sms_consent!=1 OR prior_drive!=0").fetchone()[0],
'holdout_message_leaks':con.execute("SELECT COUNT(*) FROM messages JOIN assignments USING(assignment_id) WHERE arm='H'").fetchone()[0],
'event_before_assignment':con.execute('SELECT COUNT(*) FROM events JOIN assignments USING(assignment_id) WHERE event_day<assigned_day').fetchone()[0],
'incomplete_primary_windows':con.execute('SELECT COUNT(*) FROM assignments WHERE assigned_day+28>240').fetchone()[0],
'incomplete_contract_windows':con.execute('SELECT COUNT(*) FROM assignments WHERE assigned_day+180>240').fetchone()[0],
'completion_without_prior_booking':con.execute("SELECT COUNT(*) FROM events e WHERE event_type='test_drive_completed' AND NOT EXISTS (SELECT 1 FROM events b WHERE b.assignment_id=e.assignment_id AND b.event_type='booking' AND b.event_day<=e.event_day)").fetchone()[0],
'contract_without_prior_completion':con.execute("SELECT COUNT(*) FROM events e WHERE event_type='contract_signed' AND NOT EXISTS (SELECT 1 FROM events b WHERE b.assignment_id=e.assignment_id AND b.event_type='test_drive_completed' AND b.event_day<=e.event_day)").fetchone()[0]}
assert checks['integrity'] and all(v==0 for k,v in checks.items() if k!='integrity'),checks
objects=[x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
CSV=DATA/'csv';CSV.mkdir(exist_ok=True)
for name in objects+['outcomes','early_snapshot_day28']:
    cur=con.execute('SELECT * FROM '+name+' ORDER BY 1')
    with (CSV/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(cur)
    with (CSV/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:csvcount=sum(1 for _ in csv.reader(f))-1
    assert csvcount==con.execute('SELECT COUNT(*) FROM '+name).fetchone()[0]
summary=[dict(zip(['arm','n','booked','completed','withdrawn','contracted'],r)) for r in con.execute('SELECT arm,COUNT(*),SUM(booked_28),SUM(completed_28),SUM(withdrawn_28),SUM(contracted_180) FROM outcomes GROUP BY arm ORDER BY arm')]
early=dict(zip(['enrolled_by_day28','mature_primary','observed_completions_so_far'],con.execute('SELECT COUNT(*),SUM(primary_window_mature),SUM(completion_observed_so_far) FROM early_snapshot_day28').fetchone()))
con.close();staging.rename(target)
# Exact-target readback after promotion.
with sqlite3.connect(f'file:{target.as_posix()}?mode=ro',uri=True) as verify:
    assert verify.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert verify.execute('SELECT COUNT(*) FROM customers').fetchone()[0]==plan['population_n']
report={'database':str(target),'rows':manifest['rows'],'summary':summary,'structural_checks':checks,'early_snapshot':early,'database_bytes':target.stat().st_size,'limitations':plan['limitations']}
(OUT/'generation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
