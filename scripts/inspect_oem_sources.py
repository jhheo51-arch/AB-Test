"""Verify official OEM files locally, retaining source and access limits."""
import hashlib
import io
import json
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CACHE=Path.home()/'AppData/Local/hermes/profiles/mira/cache/scratch/oem_sources'
CACHE.mkdir(parents=True,exist_ok=True)
urls={
'hyundai_sales_by_model':'https://www.hyundai.com/content/dam/hyundai/ww/en/images/company/investor-relations/ir-resources/sales-results-report/2026/hmc-sales-by-model-october-y2026.xlsx',
 'toyota_customer_service_report':'https://global.toyota/pages/global_toyota/sustainability/report/sdb/sdb25_en.pdf'
}
report={}
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
for key,url in urls.items():
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=60) as r: raw=r.read();final=r.url
        path=CACHE/url.rsplit('/',1)[1]
        path.write_bytes(raw)
        info={'url':url,'final_url':final,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cached_file':str(path),'rights':'Commercial reuse and redistribution not yet reviewed; raw file not committed.'}
        if url.endswith('.xlsx'):
            z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
            shared=[]
            if 'xl/sharedStrings.xml' in z.namelist():
                shared=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
            wb=ET.fromstring(z.read('xl/workbook.xml'))
            info['sheet_names']=[s.attrib['name'] for s in wb.findall('m:sheets/m:sheet',ns)]
            info['worksheet_previews']={}
            for name in sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'))[:2]:
                xml=ET.fromstring(z.read(name)); out=[]
                for row in xml.findall('m:sheetData/m:row',ns)[:12]:
                    cells=[]
                    for cell in row.findall('m:c',ns):
                        v=cell.find('m:v',ns)
                        text=v.text if v is not None else ''.join(cell.find('m:is',ns).itertext()) if cell.find('m:is',ns) is not None else ''
                        if cell.attrib.get('t')=='s' and text: text=shared[int(text)]
                        if text: cells.append({'cell':cell.attrib.get('r'),'value':text})
                    if cells: out.append(cells)
                info['worksheet_previews'][name]=out
            info['verified']='Downloaded valid XLSX; inspected workbook sheets and initial cell rows. Aggregate sales, not individual CRM experiment logs.'
        else:
            assert raw.startswith(b'%PDF')
            info['verified']='Downloaded PDF magic verified. Page-specific customer metrics not independently extracted in this parent check.'
        report[key]=info
    except Exception as e:
        report[key]={'url':url,'error':str(e),'verified':False}
(ROOT/'e-book/references/OEM_SOURCE_ACCESS_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
