"""Inspect a public research dataset locally; do not redistribute raw data."""
import csv
import hashlib
import io
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

cache=Path.home()/'AppData/Local/hermes/profiles/mira/cache/scratch/ab_test_public_data'
cache.mkdir(parents=True,exist_ok=True)
name='Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
urls=['https://www.minethatdata.com/'+name,'http://www.minethatdata.com/'+name]
failures=[]
for url in urls:
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=45) as response:
            raw=response.read()
            final=response.url
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        required={'segment','visit','conversion','spend'}
        if not rows or not required.issubset(rows[0]):
            raise ValueError('Unexpected CSV schema')
        target=cache/name
        target.write_bytes(raw)
        report={'source':url,'final_url':final,'local_raw_file':str(target),'rows':len(rows),'columns':list(rows[0]),'groups':dict(Counter(r['segment'] for r in rows)),'sha256':hashlib.sha256(raw).hexdigest(),'open_available':'open' in rows[0],'click_available':'click' in rows[0],'rights_status':'Original source publicly offers dataset for analysis; commercial book reuse and raw redistribution not yet cleared. Do not upload raw data.','failed_attempts':failures}
        break
    except Exception as e:
        failures.append({'url':url,'error':str(e)})
else:
    report={'download_success':False,'failed_attempts':failures}
print(json.dumps(report,ensure_ascii=False,indent=2))
root=Path(__file__).resolve().parents[1]
(root/'e-book/references/HILLSTROM_ACCESS_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
