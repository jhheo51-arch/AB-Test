"""Build scratch reproduction evidence; never rewrite original capture evidence."""
import datetime, hashlib, json
from tutorial_paths import ROOT, WORK, RUNTIME, HELP
OUT=WORK/'evidence'
def read(p): return json.loads(p.read_text('utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
browser=read(OUT/'browser_evidence.json'); playback=read(OUT/'playback_verification.json')
probe=read(OUT/'ffprobe.json'); cues=read(HELP/'walkthrough.timeline.json')
assert all(browser['checks'].values()) and all(playback['checks'].values())
assert (OUT/'full_decode.txt').read_text('utf-8').startswith('returncode=0')
assert cues[0]['start']==0 and abs(cues[-1]['end']-float(probe['format']['duration']))<.001
for a,b in zip(cues,cues[1:]): assert a['end']==b['start']
manifest={p.relative_to(WORK).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in WORK.rglob('*') if p.is_file() and not any(x in ('__pycache__','raw') for x in p.parts) and p.name not in ('EVIDENCE.json','EVIDENCE.sha256')}
data={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'New scratch reproduction, not original committed capture; source app read-only','app_dir':str(RUNTIME),'captured_source_sha256':browser['source_sha256'],'video_sha256':sha(HELP/'walkthrough.mp4'),'probe':probe,'cue_count':len(cues),'recording_assertions':len(browser['checks']),'playback_assertions':len(playback['checks']),'full_decode_returncode':0,'server_stopped':playback['server_stopped'],'human_observations':0,'live_llm_calls':0,'all_output_sha256':manifest,'limits':['Synthetic assumptions are not real experiment certification','Scene timing, not frame-exact synchronization','No human usability or learning-effect validation','New runtime/bytes can differ from original capture']}
path=WORK/'EVIDENCE.json';path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'EVIDENCE.sha256').write_text(sha(path)+'  EVIDENCE.json\n',encoding='utf-8')
print(json.dumps({'evidence':str(path),'files':len(manifest),'video_sha256':data['video_sha256']},indent=2))
