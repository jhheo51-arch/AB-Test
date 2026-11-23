"""Current a0-based merge handoff; never changes Git state or historical proofs."""
from pathlib import Path
import hashlib,json,os,socket,zipfile
R=Path(__file__).resolve().parents[1];T=R.parent;E=R/'integration-evidence'
def load(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def closed(port):
 with socket.socket() as s:s.settimeout(.3);return s.connect_ex(('127.0.0.1',port))!=0
if __name__=='__main__':
 baseline=load(E/'BASELINE.json');assert baseline['base_commit']=='a0b506c2e9e199a3d00832b0411a49da35c3302d'
 source=load(R/'verification.json');extracted=load(R/'evidence/package/EXTRACTED_VERIFICATION.json');package=load(T/'downloads/package_verification.json');assert source['status']==extracted['status']==package['status']=='PASS'
 assert source['current_verified_counts']==extracted['current_verified_counts']
 archive=T/'downloads/AB_Test_Workspace.zip';assert sha(archive)==package['sha256']
 allow=load(T/'downloads/PACKAGE_ALLOWLIST.json')['members']
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None and sorted(z.namelist())==sorted(row['member'] for row in allow)
  assert all(z.read(row['member'])==(T/row['source']).read_bytes() and sha(T/row['source'])==row['sha256'] for row in allow)
 extract=Path(package['extraction'])/'AB_Test_Workspace'
 controls={n:{'upstream_sha256':baseline['controls'][n]['sha256'],'source_sha256':sha(R/n),'extracted_sha256':sha(extract/n)} for n in baseline['preserved_controls']}
 assert all(len(set(row.values()))==1 for row in controls.values())
 conflicts={n:sha(R/n) for n in ['launch.py','tests/rebuild_package.py']}
 assert all('<<<<<<<' not in (R/n).read_text('utf-8') and '>>>>>>>' not in (R/n).read_text('utf-8') for n in conflicts)
 files={p.relative_to(T).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in T.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p!=E/'HANDOFF.json'}
 modified={n:{**row,'upstream':baseline['all_upstream_tool_files'].get(n)} for n,row in files.items() if n not in baseline['all_upstream_tool_files'] or row['sha256']!=baseline['all_upstream_tool_files'][n]['sha256']}
 ports=[int(load(p)['url_during_tests'].rsplit(':',1)[1]) for p in [R/'integration_verification.json',R/'evidence/package/EXTRACTED_INTEGRATION.json']]+[int(package['separate_extracted_server'].rsplit(':',1)[1])]
 port_checks={str(p):closed(p) for p in set(ports)};assert all(port_checks.values())
 status=load(T/'STATUS.json');py_fallback=load(R/'r08-evidence/PY_FALLBACK_HTTP.json');assert py_fallback['status']=='PASS' and py_fallback['tested_zip_sha256']==package['sha256'];assert status['conditions']['storage_schema']==8 and status['conditions']['csv_plan_storage_schema']==7 and status['current_base_commit']==baseline['base_commit'] and status['human_observations']==0
 result={'status':'PASS','base_commit':baseline['base_commit'],'previous_R08_base':baseline['previous_R08_base'],'previous_R08_local_commit':baseline['previous_R08_local_commit'],'baseline_manifest_sha256':sha(E/'BASELINE.json'),'upstream_archive_sha256':baseline['upstream_archive_sha256'],'resolved_conflict_files_sha256':conflicts,'current_upstream_control_comparison':controls,'modified_and_new_tool_relative_to_upstream':modified,'source_counts':source['current_verified_counts'],'extracted_counts':extracted['current_verified_counts'],'not_double_counted':True,'additional_py_fallback_http':py_fallback,'storage':source['storage'],'source_environment_checks':load(R/'r08-evidence/ENVIRONMENT_VERIFICATION.json')['count'],'extracted_environment_checks':load(R/'evidence/package/EXTRACTED_R08_ENVIRONMENT.json')['count'],'provided_examples':load(E/'PROVIDED_EXAMPLES.json'),'source_metadata_guards':load(R/'evidence/package/SOURCE_METADATA_GUARDS.json'),'zip_metadata_guards':load(R/'evidence/package/ZIP_METADATA_GUARDS.json'),'package':{k:package[k] for k in ['sha256','bytes','members','CRC','all_member_bytes_match_source','server_stopped']},'owned_main_package_ports_closed':port_checks,'actual_model_calls':0,'human_observations':0,'scope':'file edits and execution only; rebase remains parent-owned; no stage/commit/rebase-continue/push; no root/book edits; handoff excludes its own hash and Python caches'}
 (E/'HANDOFF.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['modified_and_new_tool_relative_to_upstream','current_upstream_control_comparison','source_metadata_guards','zip_metadata_guards','provided_examples']},ensure_ascii=False,indent=2));print('MODIFIED_OR_NEW',len(modified));print('PRESERVED_CURRENT_UPSTREAM_CONTROLS',len(controls));print('HANDOFF_SHA256',sha(E/'HANDOFF.json'))
