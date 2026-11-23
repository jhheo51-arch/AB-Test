"""Compose real browser recording + separate licensed-font caption band. No fabricated UI.
Run after record_walkthrough.py. FFmpeg and ffprobe must be on PATH.
"""
import os,sys,json,math,shutil,hashlib,subprocess
from pathlib import Path
from tutorial_paths import ROOT, WORK, RUNTIME, HELP
from fontTools.ttLib import TTFont
from PIL import Image,ImageDraw,ImageFont
OUT=WORK/'evidence'
FONT=WORK/'licensed_fonts';FONT.mkdir(exist_ok=True)
f=TTFont(RUNTIME/'fonts/PretendardVariable.woff2');f.flavor=None;f.save(FONT/'PretendardVariable.ttf')
shutil.copyfile(RUNTIME/'fonts/LICENSE.txt',FONT/'LICENSE.txt')
ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
 if p.returncode:raise RuntimeError(p.stderr)
 return p
raw=OUT/'actual_app_recording.webm'
rawprobe=json.loads(run([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(raw)]).stdout)
duration=float(rawprobe['format']['duration']); fps=25; frames=math.ceil(duration*fps)
cues=json.loads((OUT/'timeline.json').read_text('utf-8'))
cues[0]['start']=0.0;cues[-1]['end']=frames/fps
(HELP/'walkthrough.timeline.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2),encoding='utf-8')
def stamp(t):
 ms=round(t*1000); h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02},{ms:03}'
(HELP/'walkthrough.ko.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n',encoding='utf-8')
label=ImageFont.truetype(str(FONT/'PretendardVariable.ttf'),18)
font=ImageFont.truetype(str(FONT/'PretendardVariable.ttf'),24)
labeltext='합성 자료 기능 시연 / 실제 실험 인증 아님'
images=[]; bboxes=[]
for i,c in enumerate(cues):
 im=Image.new('RGB',(1280,100),'#202B3A'); d=ImageDraw.Draw(im)
 d.text((640,16),labeltext,font=label,fill='white',anchor='mm')
 boxes=[]
 for n,line in enumerate(c['text'].splitlines()):
  box=d.textbbox((640,48+n*30),line,font=font,anchor='mm');boxes.append(box)
  assert box[0]>=18 and box[2]<=1262 and box[1]>=30 and box[3]<=98,(i,box,line)
  d.text((640,48+n*30),line,font=font,fill='white',anchor='mm')
 images.append(im.tobytes());bboxes.append({'cue':i,'boxes':boxes})
 im.save(OUT/f'caption_{i:02}.png')
captionvideo=OUT/'caption_band.mp4'
cmd=[ffmpeg,'-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x100','-framerate','25','-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(captionvideo)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
idx=0
for n in range(frames):
 t=n/fps
 while idx+1<len(cues) and t>=cues[idx+1]['start']:idx+=1
 p.stdin.write(images[idx])
p.stdin.close();err=p.stderr.read();ret=p.wait()
if ret:raise RuntimeError(err.decode(errors='replace'))
video=HELP/'walkthrough.mp4'
run([ffmpeg,'-y','-v','error','-i',str(raw),'-i',str(captionvideo),'-filter_complex','[0:v]fps=25,scale=1280:800:flags=lanczos,setsar=1[top];[top][1:v]vstack=inputs=2[v]','-map','[v]','-an','-t',str(frames/fps),'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(video)])
probe=json.loads(run([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(video)]).stdout)
(OUT/'ffprobe.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
decode=run([ffmpeg,'-v','error','-i',str(video),'-f','null','-'])
(OUT/'full_decode.txt').write_text(f'returncode={decode.returncode}\nstdout={decode.stdout}\nstderr={decode.stderr}',encoding='utf-8')
# Actual encoded frames, not mockups. Named by cue content for visual inspection.
selection=[0,3,8,10,11,14,18,19,21,24,len(cues)-1]
for i in selection:
 c=cues[i];t=min(c['start']+max(.5,(c['end']-c['start'])/2),duration-.2)
 run([ffmpeg,'-y','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1',str(OUT/f'frame_{i:02}.png')])
def linear(v):
 v=v/255;return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
bg=sum(w*linear(v) for w,v in zip((.2126,.7152,.0722),(32,43,58)))
contrast=1.05/(bg+.05)
(OUT/'composition.json').write_text(json.dumps({'width':1280,'app_height':800,'caption_height':100,'fps':25,'frames':frames,'duration':frames/fps,'silent':True,'caption_font':'Converted licensed PretendardVariable.woff2 (OFL)','caption_foreground':'#FFFFFF','caption_background':'#202B3A','wcag_contrast':contrast,'caption_bboxes':bboxes,'sample_frame_cues':selection},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'video':str(video),'bytes':video.stat().st_size,'duration':probe['format']['duration'],'streams':[{'codec':s['codec_name'],'fps':s.get('r_frame_rate'),'width':s.get('width'),'height':s.get('height')} for s in probe['streams']],'contrast':contrast,'decode_returncode':decode.returncode},ensure_ascii=False,indent=2))
