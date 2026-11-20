"""Start this local app without reading credentials or changing Hermes config."""
from pathlib import Path
import argparse,os,shutil,webbrowser
from server import AppServer,Handler
ROOT=Path(__file__).resolve().parent

def find_hermes():
    configured=os.environ.get('AB_HERMES_EXE')
    if configured and Path(configured).is_file():return configured
    for name in ['hermes','hermes.exe']:
        found=shutil.which(name)
        if found:return found
    if os.name=='nt':
        windows_apps=Path(os.environ.get('ProgramFiles','C:/Program Files'))/'WindowsApps'
        try:
            candidates=list(windows_apps.glob('NousResearchInc.HermesAgent_*/app/resources/agent-payload/bin/hermes.EXE'))
            candidates=[p for p in candidates if p.is_file()]
            if candidates:return str(max(candidates,key=lambda p:p.stat().st_mtime))
        except OSError:pass
    return None

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--no-browser',action='store_true');parser.add_argument('--port',type=int,default=0);parser.add_argument('--profile',default='mira');args=parser.parse_args()
    missing=[n for n in ['index.html','styles.css','app.js','engine.js','worker.js','narrative.js','project-schema.js','lineage.js','engine-issue-codes.json','column-mapping.js','workflow-v05.js','workflow-v05.css','decision-v04.css'] if not (ROOT/n).is_file()]
    if missing:raise SystemExit('Missing app files: '+', '.join(missing))
    hermes=find_hermes()
    with AppServer(('127.0.0.1',args.port),Handler,hermes,args.profile) as server:
        url='http://127.0.0.1:'+str(server.server_port)
        print('AB_LOCAL_URL='+url,flush=True)
        print('LLM CLI found: '+str(bool(hermes))+'; real request still required to verify authentication.',flush=True)
        print('Keep this window open. Press Ctrl+C to stop. CSV stays in your browser.',flush=True)
        if not args.no_browser:webbrowser.open(url)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
