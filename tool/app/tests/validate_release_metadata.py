"""Eight negative metadata guards on an isolated copy; never edit the release."""
from pathlib import Path
import argparse, copy, json, os, shutil, tempfile
from verify_release_metadata import verify

def run(root):
    root=Path(root)
    with tempfile.TemporaryDirectory(prefix='tutorial_metadata_guards_',dir=os.environ['TMPDIR']) as temp:
        target=Path(temp)/'app';shutil.copytree(root,target,ignore=shutil.ignore_patterns('__pycache__'))
        original=json.loads((target/'verification.json').read_text('utf-8'))
        verify(target)
        def omit_source(s): s['source_sha256'].pop('server.py')
        def stale_source(s): s['source_sha256']['index.html']='0'*64
        def wrong_script_count(s): s['integration_suite']['scripts']+=1
        def wrong_semantic_count(s): s['semantic_regressions']['cases']+=1
        def skip_control(s): s['preserved_baseline_bytes'].pop('engine.js')
        def rewrite_baseline(s): s['baseline']['controls']['worker.js']['sha256']='0'*64
        def old_video(s): s['video']['sha256']=s['baseline']['controls']['help/walkthrough.mp4']['sha256']
        def stale_caption(s): s['video']['asset_sha256']['help/walkthrough.ko.srt']='0'*64
        def profile_omitted_source(s): s['source_sha256'].pop('column-profile.js')
        def profile_stale_source(s): s['source_sha256']['profile-ui.js']='0'*64
        def profile_privacy_flag(s): s['column_profile']['raw_headers_stored']=True
        def profile_tutorial_claim(s): s['column_profile']['tutorial_covers_profiles']=True
        def profile_fixture_hash(s): s['column_profile']['fixture_sha256']='0'*64
        def profile_missing_preserved(s): s['column_profile']['preserved_sha256'].pop('help/walkthrough.mp4')
        rows=[]
        for mutation in [omit_source,stale_source,wrong_script_count,wrong_semantic_count,skip_control,rewrite_baseline,old_video,stale_caption,profile_omitted_source,profile_stale_source,profile_privacy_flag,profile_tutorial_claim,profile_fixture_hash,profile_missing_preserved]:
            data=copy.deepcopy(original);mutation(data)
            (target/'verification.json').write_text(json.dumps(data),encoding='utf-8')
            try: verify(target)
            except AssertionError: rows.append({'guard':mutation.__name__,'rejected':True})
            else: raise AssertionError('Guard accepted '+mutation.__name__)
    return {'status':'PASS','negative_guards':len(rows),'checks':rows,'source_untouched':True}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=run(args.root)
    if args.output: args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
