"""Isolated reproduction for syntactically malformed CSV replacing valid data."""
from pathlib import Path
import json,subprocess,sys
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 server=subprocess.Popen([sys.executable,'server.py','--port','0'],cwd=R,stdout=subprocess.PIPE,text=True)
 try:
  url=server.stdout.readline().strip().split('=',1)[1]
  with sync_playwright() as w:
   b=w.chromium.launch(channel='chrome');p=b.new_page();p.goto(url);p.fill('#data-text','arm,success,total\nA,1,10\nB,2,10');p.click('#prepare');expect(p.locator('#analysis-options')).to_be_visible();p.check('#confirm-input');p.click('#analyze');expect(p.locator('#results-view')).to_be_visible();p.click('nav [data-view=input]')
   expression='JSON.stringify({state,raw:$("#data-text").value,conditions:readConditions()})';before=p.evaluate(expression)
   p.set_input_files('#csv-file',{'name':'MALFORMED.csv','mimeType':'text/csv','buffer':b'arm,success,total\nA,"unterminated'})
   expect(p.locator('#prepare')).to_be_enabled();p.wait_for_timeout(100)
   record={'status':'PASS' if p.evaluate(expression)==before else 'FAIL','case':'malformed CSV file must preserve existing valid input/result','preserved':p.evaluate(expression)==before,'after_raw':p.locator('#data-text').input_value(),'after_has_result':p.evaluate('Boolean(state.result)'),'model_calls':0,'humans':0}
   (R/'r08-evidence/CSV_SYNTAX_BASELINE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(record,ensure_ascii=False));b.close()
 finally:server.terminate();server.wait(timeout=10)
