"""Negative metadata guards and STATUS ownership checks on an isolated copy."""
from pathlib import Path
import argparse, copy, json, os, shutil, tempfile
from verify_release_metadata import verify

def run(root):
    root=Path(root)
    with tempfile.TemporaryDirectory(prefix='tutorial_metadata_guards_',dir=os.environ['TMPDIR']) as temp:
        target=Path(temp)/'app';shutil.copytree(root,target,ignore=shutil.ignore_patterns('__pycache__'))
        # Isolated copy must include the exact owned status, not a neighboring file.
        from release_status import target as status_target,sync as sync_status
        owned=status_target(root)
        if owned:shutil.copy2(owned,target/'STATUS.json')
        original=json.loads((target/'verification.json').read_text('utf-8'))
        verify(target)
        def omit_source(s): s['source_sha256'].pop('server.py')
        def stale_source(s): s['source_sha256']['index.html']='0'*64
        def wrong_script_count(s): s['integration_suite']['scripts']+=1
        def wrong_semantic_count(s): s['semantic_regressions']['cases']+=1
        def skip_control(s): s['preserved_baseline_bytes'].pop('worker.js')
        def rewrite_baseline(s): s['baseline']['controls']['worker.js']['sha256']='0'*64
        def old_video(s): s['video']['sha256']=s['baseline']['controls']['help/walkthrough.mp4']['sha256']
        def stale_caption(s): s['video']['asset_sha256']['help/walkthrough.ko.srt']='0'*64
        def profile_omitted_source(s): s['source_sha256'].pop('column-profile.js')
        def profile_stale_source(s): s['source_sha256']['profile-ui.js']='0'*64
        def profile_privacy_flag(s): s['column_profile']['raw_headers_stored']=True
        def profile_tutorial_claim(s): s['column_profile']['tutorial_covers_profiles']=True
        def profile_fixture_hash(s): s['column_profile']['fixture_sha256']='0'*64
        def stale_native_schema(s):s['storage']['schema']=7
        def stale_upstream_engine(s):s['upstream_integration']['preserved_bytes']['engine.js']=False
        def stale_current_counts(s):s['current_verified_counts']['scripts']-=1
        def profile_missing_preserved(s): s['column_profile']['preserved_sha256'].pop('help/walkthrough.mp4')
        rows=[]
        for mutation in [omit_source,stale_source,wrong_script_count,wrong_semantic_count,skip_control,rewrite_baseline,old_video,stale_caption,profile_omitted_source,profile_stale_source,profile_privacy_flag,profile_tutorial_claim,profile_fixture_hash,profile_missing_preserved,stale_current_counts,stale_native_schema,stale_upstream_engine]:
            data=copy.deepcopy(original);mutation(data)
            (target/'verification.json').write_text(json.dumps(data),encoding='utf-8')
            try: verify(target)
            except AssertionError: rows.append({'guard':mutation.__name__,'rejected':True})
            else: raise AssertionError('Guard accepted '+mutation.__name__)
        (target/'verification.json').write_text(json.dumps(original),encoding='utf-8')
        status=target/'STATUS.json'
        if not status.exists():status.write_text(json.dumps({'app':'tool/app','release_metadata':'tool/app/verification.json'}),encoding='utf-8')
        sync_status(target,original);saved=json.loads(status.read_text('utf-8'))
        saved['current_verified_counts']['scripts']-=1;status.write_text(json.dumps(saved),encoding='utf-8')
        try:verify(target)
        except AssertionError:rows.append({'guard':'stale_STATUS','rejected':True})
        else:raise AssertionError('stale STATUS accepted')
        sync_status(target,original);wrong=json.loads(status.read_text('utf-8'));wrong['conditions']['storage_schema']=7;status.write_text(json.dumps(wrong),encoding='utf-8')
        try:verify(target)
        except AssertionError:rows.append({'guard':'stale_STATUS_storage_schema','rejected':True})
        else:raise AssertionError('stale STATUS storage accepted')
        saved['extra_nested']={'keep':['sentinel',0]};saved['human_observations']=0;status.write_text(json.dumps(saved),encoding='utf-8')
        sync_status(target,original);updated=json.loads(status.read_text('utf-8'))
        assert {k:v for k,v in updated.items() if k!='current_verified_counts'}=={k:v for k,v in saved.items() if k!='current_verified_counts'}
        rows.append({'guard':'preserve_unrelated_STATUS_fields','pass':True})
        status.unlink();neighbor=target.parent/'STATUS.json';neighbor.write_text('UNRELATED_DO_NOT_TOUCH',encoding='utf-8')
        assert sync_status(target,original)=={'status':'ABSENT','written':False}
        verify(target);assert not status.exists() and neighbor.read_text('utf-8')=='UNRELATED_DO_NOT_TOUCH'
        rows.append({'guard':'absent_target_never_writes_arbitrary_parent','pass':True})
    return {'status':'PASS','negative_guards':len(rows)-2,'status_safety_checks':2,'count':len(rows),'checks':rows,'source_untouched':True}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=run(args.root)
    if args.output: args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
