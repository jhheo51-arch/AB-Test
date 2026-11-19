import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import edge_tts
from PIL import Image, ImageDraw, ImageFilter

from make_shorts import cover, heading, visuals
from episode_data import DATA, PITCH, RATE, ROOT, audio_path, spoken
from render import A, A_PALE, B, B_PALE, INK, LINE, MUTED, ORANGE, PAPER, WHITE, Board, compose, render
from storyboards import episodes
from storyboards_04_05 import next_episodes
from figures_04_05 import plot
from figures_06_10 import KINDS, plot as new_plot
from storyboards_06_10 import lessons

async def speech_timing(segments):
    limit=asyncio.Semaphore(5)
    pairs={(speaker,line) for _,speaker,line in segments}

    async def read(speaker,line):
        mp3=audio_path(speaker,line)
        metadata=mp3.with_suffix(".words.json")
        if metadata.exists() and mp3.is_file() and mp3.stat().st_size>1000:
            return (speaker,line),json.loads(metadata.read_text(encoding="utf8"))
        mp3.parent.mkdir(exist_ok=True)
        temp=mp3.with_suffix(".timing.tmp")
        async with limit:
            for attempt in range(3):
                try:
                    words=[]
                    engine=edge_tts.Communicate(spoken(line),DATA["voices"][speaker],rate=RATE,
                                                pitch=PITCH[speaker],boundary="WordBoundary")
                    with temp.open("wb") as audio:
                        async for chunk in engine.stream():
                            if chunk["type"]=="audio":
                                audio.write(chunk["data"])
                            elif chunk["type"]=="WordBoundary":
                                words.append((chunk["offset"]/10_000_000,chunk["text"]))
                    if not words or temp.stat().st_size<=1000:
                        raise RuntimeError("음성 또는 단어 시각을 받지 못했습니다.")
                    if not mp3.is_file() or mp3.stat().st_size<=1000:
                        temp.replace(mp3)
                    metadata.write_text(json.dumps(words,ensure_ascii=False),encoding="utf8")
                    return (speaker,line),words
                except Exception:
                    if attempt==2:
                        raise
                    await asyncio.sleep(attempt+1)
                finally:
                    temp.unlink(missing_ok=True)

    result=dict(await asyncio.gather(*(read(speaker,line) for speaker,line in pairs)))
    print(f"음성 및 단어 시각 {len(result)}개 확인",flush=True)
    return result

def cues_for(cues,words):
    result=[]
    cursor=0
    for phrase,target in cues:
        if not phrase:
            result.append((0,target))
            continue
        compact=phrase.replace(" ","")
        hit=next((i for i in range(cursor,len(words))
                  if phrase in words[i][1] or "".join(w[1] for w in words[i:i+4]).replace(" ","").startswith(compact)),None)
        if hit is None:
            raise ValueError(f"강조할 단어를 찾을 수 없습니다: {phrase} / {words}")
        cursor=hit+1
        result.append((round(max(0,words[hit][0]-0.03),3),target))
    return result

def dots(board,center,y,total,activated,color):
    # Keep denominator and numerator visible, using smaller markers for 100 visitors.
    columns=20
    step=10 if total>20 else 12
    radius=3 if total>20 else 4
    for i in range(total):
        row,col=divmod(i,columns)
        remaining=min(columns,total-row*columns)
        x=center+(col-(remaining-1)/2)*step
        cy=y+row*step
        board.draw.ellipse((x-radius,cy-radius,x+radius,cy+radius),
                           fill=color if i<activated else WHITE,
                           outline=color if i<activated else LINE,width=1)

def wide_visuals(board,title,cards,dot_specs):
    left,right,center=board.left,board.right,board.center
    heading(board,title,left,42,right-left,40)
    board.text(left,93,"교육용 가상 데이터",15,MUTED)
    if len(cards)==1:
        label,value,note=cards[0]
        board.box(left,121,right,407,WHITE,12,LINE)
        heading(board,label,center,152,right-left-40,29,MUTED,"mt")
        heading(board,value,center,199,right-left-48,64,ORANGE,"mt")
        heading(board,note,center,292,right-left-48,23,MUTED,"mt")
        if dot_specs:
            dots(board,center,353,*dot_specs[0],ORANGE)
        return
    for i,(label,value,note) in enumerate(cards):
        x,r=((48,467),(493,912))[i]
        fill,color=(A_PALE,A) if i==0 else (B_PALE,B)
        board.box(x,123,r,407,fill,12,LINE)
        heading(board,label,x+22,146,r-x-43,26,color)
        heading(board,value,(x+r)//2,210,r-x-40,57,color,"mt")
        heading(board,note,(x+r)//2,288,r-x-40,21,MUTED,"mt")
        if dot_specs:
            dots(board,(x+r)//2,340,*dot_specs[i],color)

def dim(board,count,target):
    if target=="both":
        return
    x,r=board.left,board.right
    if board.vertical:
        pane=(x,245,r,674)
        regions={"first":(x,250,r,449),"second":(x,470,r,669),
                 "label":(x+18,324,r-18,373),"value":(x+12,387,r-12,468),
                 "note":(x+18,503,r-18,548)}
    else:
        pane=(x,116,r,410)
        regions={"first":(48,123,467,407),"second":(493,123,912,407),
                 "label":(x+28,142,r-28,191),"value":(x+28,193,r-28,280),
                 "note":(x+28,283,r-28,326)}
    if (count==1) != (target in {"label","value","note"}):
        raise ValueError(f"도표와 강조 위치가 맞지 않습니다: {target}")
    source=board.image
    faded=Image.blend(source,Image.new("RGB",source.size,PAPER),0.42)
    mask=Image.new("L",source.size,0)
    paint=ImageDraw.Draw(mask)
    paint.rectangle(pane,fill=255)
    paint.rounded_rectangle(regions[target],radius=10,fill=0)
    source.paste(faded,(0,0),mask.filter(ImageFilter.GaussianBlur(4)))

def prepare(content,title,vertical):
    segments=[(f"part-{i}",item[0],item[1]) for i,item in enumerate(content)]

    def draw(scene,speaker,line,portrait,prior,progress,focus):
        i=int(scene.rsplit("-",1)[-1])
        _,_,label,cards,_,dot_specs,*special=content[i]
        board=Board(portrait)
        if special:
            chart = new_plot if special[0] in KINDS else plot
            chart(board,label,special[0],focus)
        elif portrait:
            visuals(board,label,cards)
            # One line of dots for cached small-group visuals in the lower card area.
            if len(cards)==1 and dot_specs:
                dots(board,board.center,582,*dot_specs[0],ORANGE)
            elif dot_specs and all(total<=20 for total,_ in dot_specs):
                for j,(total,active) in enumerate(dot_specs):
                    dots(board,board.center,432+220*j,total,active,(A,B)[j])
        else:
            wide_visuals(board,label,cards,dot_specs)
        if not special and focus is not None:
            dim(board,len(cards),focus)
        board.subtitle(speaker,line)
        return compose(board)

    for scene,speaker,line in segments:
        draw(scene,speaker,line,vertical,0,1,None)
    return segments,draw,lambda:cover(title)

def main():
    destination=ROOT/(sys.argv[1] if len(sys.argv)>1 else "renders-v03")
    destination.mkdir(exist_ok=True)
    jobs=[]
    selection=sys.argv[2] if len(sys.argv)>2 else "2-3"
    batches = {"2-3": episodes, "4-5": next_episodes, "6-10": lessons}
    if selection not in batches:
        raise ValueError("회차 묶음은 2-3, 4-5 또는 6-10으로 지정하세요.")
    episode_args = [arg for arg in sys.argv[3:] if arg != "--short-only"]
    selected = {int(ep) for ep in episode_args}
    versions = ("short",) if "--short-only" in sys.argv[3:] else ("short", "long")
    for ep,title,short,long in batches[selection]():
        if selected and ep not in selected:
            continue
        for version in versions:
            content = short if version == "short" else long
            stem=f"ep{ep:02d}-{version}"
            if any((destination/f"{stem}.{ext}").exists() for ext in ("mp4","srt","json")):
                raise FileExistsError(destination/stem)
            jobs.append((stem,version,content,prepare(content,title,version=="short")))
    words=asyncio.run(speech_timing(segment for _,_,_,job in jobs for segment in job[0]))
    resolved=[]
    for stem,version,content,job in jobs:
        schedule = {}
        for (scene,speaker,line),shot in zip(job[0],content,strict=True):
            try:
                schedule[scene] = cues_for(shot[4], words[speaker,line])
            except ValueError as exc:
                raise ValueError(f'{stem} {scene}: {exc}') from exc
        resolved.append((stem,version,job,schedule))
    if not resolved:
        raise ValueError('렌더링할 회차가 없습니다.')
    if len(resolved) > 1:
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = [pool.submit(render, version, destination, stem=stem,
                                   storyboard=job, focus_schedule=schedule)
                       for stem,version,job,schedule in resolved]
            for item in pending:
                item.result()
    else:
        for stem,version,job,schedule in resolved:
            render(version,destination,stem=stem,storyboard=job,focus_schedule=schedule)

if __name__=="__main__":
    main()
