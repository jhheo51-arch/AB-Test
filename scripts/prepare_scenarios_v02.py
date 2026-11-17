"""Create a versioned synthetic workbook; preserve v0.1 unchanged."""
import csv
import os
import hashlib
import json
import math
import random
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'e-book' / 'virtual-data' / 'v02'
if OUT.exists():
    raise SystemExit('scenarios_v02 already exists; refusing overwrite')
OUT.mkdir()
NAME = 'JH Motors'
source = (ROOT/'scripts/build_db.py').read_text(encoding='utf-8')
source = source.replace('JH Motors', NAME)
answers = {}
configs = [
    ('01_baseline','A/B 메시지 비교 기본 실습',False),
    ('02_null','배정군 간 생성 확률이 같은 실습',True),
]
for key,title,null in configs:
    folder=OUT/key
    (folder/'scripts').mkdir(parents=True)
    code=source
    if null:
        code=code.replace('SEED = 20261116','SEED = 20261117')
        code=code.replace("{'A': 0.12, 'B': 0.15}","{'A': 0.12, 'B': 0.12}")
        code=code.replace("{'A': 0.008, 'B': 0.010}","{'A': 0.008, 'B': 0.008}")
    path=folder/'scripts/build_db.py'
    path.write_text(code,encoding='utf-8')
    result=subprocess.run([sys.executable,str(path)],capture_output=True,text=True,encoding='utf-8',env=dict(os.environ, OEM_OUTPUT_ROOT=str(folder)))
    if result.returncode:
        raise RuntimeError(result.stderr)
    manifest_path=folder/'data/manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest.update({'version':'0.2','scenario':key,'scenario_title':title,'name_status':'상표 미확인 교육용 임시 명칭'})
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    answers[key]={'type':'null' if null else 'baseline','injection':None,'causal_truth':'Equal arm outcome distributions by construction; a nonsignificant result is not proof of equivalence.' if null else 'Arm-specific probabilities intentionally differ; no real-world evidence.'}

base=OUT/'01_baseline/data'
for key,title in [('03_srm','배정 기록 오류'),('04_missing','시승 완료 이벤트 선택적 누락')]:
    folder=OUT/key/'data'
    folder.mkdir(parents=True)
    shutil.copy2(base/'oem_crm.sqlite',folder/'oem_crm.sqlite')
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    manifest.update({'scenario':key,'scenario_title':title,'quality':'Intentionally corrupted exercise; consult instructor answer before any inference.'})
    con=sqlite3.connect(folder/'oem_crm.sqlite')
    rng=random.Random(20261118 if key=='03_srm' else 20261119)
    if key=='03_srm':
        ids=[r[0] for r in con.execute("SELECT assignment_id FROM assignments WHERE arm='A' ORDER BY assignment_id")]
        chosen=rng.sample(ids,len(ids)//5)
        con.executemany("UPDATE assignments SET arm='B' WHERE assignment_id=?",[(x,) for x in chosen])
        injection={'kind':'assignment_label_corruption','count':len(chosen),'ids':chosen,'explanation':'20% (rounded down) of original A labels overwritten as B; messages and events not regenerated. Intended allocation remains 50:50; not a valid unequal allocation experiment.'}
    else:
        ids=[r[0] for r in con.execute("SELECT event_id FROM journey_events e JOIN assignments a USING(assignment_id) WHERE a.arm='B' AND e.event_type='test_drive_completed' ORDER BY event_id")]
        chosen=rng.sample(ids,len(ids)//4)
        injection={'kind':'selective_completion_event_loss','count':len(chosen),'event_ids':chosen,'explanation':'25% (rounded down) of B completion rows removed. Reference outcomes are in instructor reference file. Ordinary foreign-key and booking checks need not detect this.'}
        con.executemany('DELETE FROM journey_events WHERE event_id=?',[(x,) for x in chosen])
    con.commit()
    con.close()
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    answers[key]={'type':'quality_fault','injection':injection,'interpretation':'Resolve the injected data issue before treatment inference; no rollout recommendation.'}

# Truth reference is instructor material, deliberately separate from learner DBs.
instructor=OUT/'instructor'
instructor.mkdir()
shutil.copy2(base/'csv/experiment_outcomes.csv',instructor/'baseline_reference_outcomes.csv')
summary=[]
for folder in sorted(OUT.glob('0*')):
    data=folder/'data'
    con=sqlite3.connect(f'file:{(data/"oem_crm.sqlite").as_posix()}?mode=ro',uri=True)
    assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not con.execute('PRAGMA foreign_key_check').fetchall()
    assert con.execute('SELECT name FROM company').fetchone()[0]==NAME
    objects=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts={}
    csvdir=data/'csv'
    csvdir.mkdir(exist_ok=True)
    for table in objects:
        cur=con.execute('SELECT * FROM '+table+' ORDER BY 1')
        rows=cur.fetchall()
        counts[table]=len(rows)
        with (csvdir/(table+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f); w.writerow([x[0] for x in cur.description]); w.writerows(rows)
        with (csvdir/(table+'.csv')).open(newline='',encoding='utf-8-sig') as f:
            assert sum(1 for _ in csv.reader(f))-1==len(rows)
    arms=[dict(zip(['arm','assigned','booked','completed','opted_out'],r)) for r in con.execute('SELECT arm,COUNT(*),SUM(booked),SUM(completed),SUM(opted_out) FROM experiment_outcomes GROUP BY arm ORDER BY arm')]
    n=sum(a['assigned'] for a in arms)
    z=(arms[1]['assigned']-n/2)/math.sqrt(n/4)
    p=math.erfc(abs(z)/math.sqrt(2))
    # Independent aggregation directly from event rows, not the outcome view.
    direct={r[0]:r[1] for r in con.execute("SELECT a.arm,COUNT(DISTINCT a.assignment_id) FROM assignments a JOIN journey_events e USING(assignment_id) WHERE e.event_type='test_drive_completed' AND julianday(e.event_at) BETWEEN julianday(a.assigned_at) AND julianday(a.assigned_at)+28 GROUP BY a.arm")}
    assert all(a['completed']==direct.get(a['arm'],0) for a in arms)
    con.close()
    is_srm=folder.name=='03_srm'
    assert (p<0.001) if is_srm else (p>=0.001)
    if folder.name=='04_missing':
        truth=next(x for x in summary if x['scenario']=='01_baseline')
        lost=truth['arms'][1]['completed']-arms[1]['completed']
        assert lost==answers[folder.name]['injection']['count']
    report={'scenario':folder.name,'counts':counts,'arms':arms,'integrity':'ok','csv_counts_verified':True,'direct_event_aggregation_matches':True,'srm_p_normal_approx':p,'srm_screen_threshold':0.001,'srm_flag':p<0.001,'scope':'Structural checks and SQL cross-check only; no primary-effect test, power validation or deployment approval.'}
    (data/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary.append(report)
(instructor/'answer_key.json').write_text(json.dumps(answers,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
readme='''# JH Motors: 전자책 합성 데이터 v0.2
저자: 허재혁. 기업명은 사용자 확정 전 임시 작업명이며 상표 미검증. 실제 OEM·고객·시장 자료가 아닙니다.

## 실습 순서
1. 01_baseline: A 차량 가치 안내 / B 시승 편의 안내. 사전 속성과 28일 관측 결과를 읽습니다.
2. 02_null: 두 군의 전달·수신 거부·예약·시승 생성 확률이 같습니다. 표본 수치가 같아야 한다는 뜻은 아니며, 비유의성이 동등성을 입증하지 않습니다.
3. 03_srm: 배정 기록 오류가 주입됐습니다. 구조 무결성이 정상이어도 실험 결과를 믿을 수 없습니다.
4. 04_missing: 일부 시승 완료 이벤트가 누락됐습니다. 배정 비율 검사만으로 발견할 수 없습니다.

각 폴더 data/oem_crm.sqlite가 DB, data/csv가 스프레드시트용 CSV입니다. manifest.json에 생성 가정, validation.json에 실제 검사 결과가 있습니다.
instructor/에는 오류 정답지와 누락 검증용 원본 집계가 있습니다. 학습 시 먼저 열지 않는 것을 권합니다. scenarios_v02는 실습 시나리오 묶음이지 서로 합칠 동일 실험 데이터가 아닙니다. 같은 customer_id는 시나리오 간 중복될 수 있습니다.

주지표: 배정 후 28일 이내 시승 완료 여부, 분모는 발송 실패까지 포함한 배정 고객 전체입니다. 무발송군은 없으므로 무발송 대비 효과를 말할 수 없습니다. 매출·계약·LTV는 생성하지 않았습니다.
주 분석 검정·검정력·의사결정 기준의 검증은 아직 완료되지 않았습니다. 구조 검사와 SRM 점검 통과는 타당성을 보증하지 않습니다. 오류 시나리오는 의도적으로 문제가 있으며 결과에 따라 출시하면 안 됩니다.

재현: 상위 scripts/prepare_scenarios_v02.py를 원본 scripts/build_db.py와 함께 사용합니다. 기존 scenarios_v02가 있으면 덮어쓰지 않습니다. Python 표준 라이브러리만 사용하며 정확한 재현에는 생성 시 Python 버전을 참고합니다.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
files=sorted(f for f in OUT.rglob('*') if f.is_file())
hashes={str(f.relative_to(OUT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
(OUT/'checksums.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8')
zip_path=ROOT/'jh_motors_synthetic_data_v02.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob('*')):
        if f.is_file(): z.write(f,f.relative_to(ROOT))
    z.write(Path(__file__),'scripts/prepare_scenarios_v02.py')
    z.write(ROOT/'scripts/build_db.py','scripts/build_db.py')
    z.write(ROOT/'e-book/virtual-data/DATA_DICTIONARY.md','V01_SCHEMA_REFERENCE.md')
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    count=len(z.namelist())
print(json.dumps({'zip':str(zip_path),'archive_files':count,'python':sys.version,'scenarios':[{'scenario':s['scenario'],'customers':s['counts']['customers'],'assigned':s['counts']['assignments'],'events':s['counts']['journey_events'],'arms':s['arms'],'srm_flag':s['srm_flag']} for s in summary]},ensure_ascii=False,indent=2))
