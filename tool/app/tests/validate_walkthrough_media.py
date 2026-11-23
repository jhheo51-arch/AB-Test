"""Validate the intentional tutorial replacement, real caption paths and full decode."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, datetime
EXPECTED = 'ffe7cd998e4a875b44ef45130e12a4d931b12d542c06b0276abfe5aa0978eabd'
def verify(root):
    root=Path(root); video=root/'help/walkthrough.mp4'
    digest=hashlib.sha256(video.read_bytes()).hexdigest()
    assert digest==EXPECTED, 'Unexpected replacement video bytes'
    cues=json.loads((root/'help/walkthrough.timeline.json').read_text('utf-8'))
    srt=(root/'help/walkthrough.ko.srt').read_text('utf-8')
    assert len(cues)==26 and cues[0]['start']==0 and cues[-1]['end']==160.16
    for a,b in zip(cues,cues[1:]): assert a['end']==b['start'] and a['end']>a['start']
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    expected='\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n'
    assert srt==expected, 'SRT differs from real timeline'
    assert all(c['text'].strip() and 0<=c['start']<c['end']<=160.16 for c in cues)
    assert 'http://' not in srt and 'https://' not in srt
    def run(cmd):
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=120)
        assert result.returncode==0,result.stderr
        return result
    probe=json.loads(run([shutil.which('ffprobe') or 'ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]).stdout)
    assert len(probe['streams'])==1
    stream=probe['streams'][0]
    assert (stream['codec_name'],stream['width'],stream['height'],stream['r_frame_rate'])==('h264',1280,900,'25/1')
    assert float(probe['format']['duration'])==160.16
    decode=run([shutil.which('ffmpeg') or 'ffmpeg','-v','error','-i',str(video),'-f','null','-'])
    assert not decode.stderr.strip()
    result={'status':'PASS','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':digest,'duration_seconds':160.16,'cue_count':len(cues),'codec':'h264','width':1280,'height':900,'fps':'25/1','audio_streams':0,'full_decode_returncode':decode.returncode,'full_decode_stderr':decode.stderr,'caption_timeline_match':True,'historical_video_preserved':False,'scope':'Current media bytes + ffprobe + full ffmpeg decode; separate from browser assertion count'}
    (root/'evidence').mkdir(exist_ok=True)
    (root/'evidence/tutorial_media_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
if __name__=='__main__': print(json.dumps(verify(Path(__file__).resolve().parents[1]),indent=2))
