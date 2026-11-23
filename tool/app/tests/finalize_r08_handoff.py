"""Historical pre-rollout 288-base R08 handoff only; current integration uses finalize_combined_handoff.py."""
from pathlib import Path
import hashlib,json,os,socket
R=Path(__file__).resolve().parents[1];T=R.parent

def generate():
 baseline_path=Path(os.environ['TMPDIR'])/'r08_baseline_backup'/'BASELINE_MANIFEST.json'
 baseline=json.loads(baseline_path.read_text('utf-8'))
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 records={p.relative_to(T).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in T.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in {'HANDOFF.json'} and not p.suffix=='.pyc'}
 modified={n:{**v,'baseline':baseline.get(n)} for n,v in records.items() if n not in baseline or v['sha256']!=baseline[n]['sha256']}
 deleted=[n for n in baseline if n not in records and '__pycache__' not in Path(n).parts and not n.endswith('.pyc')]
 controls=['engine-issue-codes.json','tests/semantic_edges.cjs','tests/golden_reference.json','examples/SYNTHETIC_CRM_MAPPING.csv','engine.js','worker.js','project-schema.js','conditions.js','design.js','design-ui.js','lineage.js','narrative.js','column-mapping.js','column-profile.js','profile-ui.js','workflow.js','fonts/PretendardVariable.woff2','fonts/LICENSE.txt','help/walkthrough.mp4','help/walkthrough.ko.srt','help/walkthrough.timeline.json']
 preserved={n:sha(R/n)==baseline['app/'+n]['sha256'] for n in controls};assert all(preserved.values())
 old_status=json.loads((baseline_path.parent/'STATUS.json').read_text('utf-8'));new_status=json.loads((T/'STATUS.json').read_text('utf-8'))
 assert {k:v for k,v in old_status.items() if k!='current_verified_counts'}=={k:v for k,v in new_status.items() if k!='current_verified_counts'}
 source=json.loads((R/'verification.json').read_text('utf-8'));package=json.loads((T/'downloads/package_verification.json').read_text('utf-8'));extracted=json.loads((R/'evidence/package/EXTRACTED_VERIFICATION.json').read_text('utf-8'))
 ports=[]
 for path in [R/'integration_verification.json',R/'evidence/package/EXTRACTED_INTEGRATION.json']:
  record=json.loads(path.read_text('utf-8'));ports.append(int(record['url_during_tests'].rsplit(':',1)[1]))
 ports.append(int(package['separate_extracted_server'].rsplit(':',1)[1]))
 def closed(port):
  with socket.socket() as s:s.settimeout(.3);return s.connect_ex(('127.0.0.1',port))!=0
 closed_ports={str(p):closed(p) for p in set(ports)};assert all(closed_ports.values())
 result={'status':'PASS','baseline_manifest_sha256':sha(baseline_path),'baseline_backup':'active-profile scratch/r08_baseline_backup (outside release)','modified_and_new_tool_relative':modified,'deleted':deleted,'preserved_controls':preserved,'control_sha256':{n:{'baseline':baseline['app/'+n]['sha256'],'current':sha(R/n)} for n in controls},'additional_py_fallback_http':json.loads((R/'r08-evidence/PY_FALLBACK_HTTP.json').read_text('utf-8')),'actual_STATUS_only_count_values_changed':True,'source_counts':source['current_verified_counts'],'extracted_counts':extracted['current_verified_counts'],'source_and_extracted_are_repetitions_not_additional_unique_coverage':True,'environment_checks_source':json.loads((R/'r08-evidence/ENVIRONMENT_VERIFICATION.json').read_text('utf-8'))['count'],'environment_checks_extracted':json.loads((R/'evidence/package/EXTRACTED_R08_ENVIRONMENT.json').read_text('utf-8'))['count'],'package':{k:package[k] for k in ['sha256','bytes','members','CRC','all_member_bytes_match_source','server_stopped']},'owned_integration_package_ports_closed':closed_ports,'actual_model_calls':0,'human_observations':0,'untested':json.loads((R/'r08-evidence/BROWSER_VERIFICATION.json').read_text('utf-8'))['untested'],'scope':'tool only; no Git staging, commit, push or original Downloads repository edits; hashes exclude this self-referential handoff and Python caches'}
 (R/'r08-evidence/HANDOFF.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['modified_and_new_tool_relative','untested']},ensure_ascii=False,indent=2));return result
if __name__=='__main__':generate()
