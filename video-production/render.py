import argparse
from bisect import bisect_right
import asyncio
import json
import math
import os
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from episode_data import DATA, ROOT, VALUES as V, a, b, n, probabilities, tail
from episode_data import audio_path, lines, synthesize

INK, MUTED, PAPER, WHITE = "#17232B", "#46545B", "#F4F5F2", "#FFFFFF"
A, B, ORANGE = "#215885", "#9B4053", "#9A3B21"
A_PALE, B_PALE, LINE = "#E8F1F8", "#F8EBED", "#C9D1D4"
FPS, SAMPLE_RATE = 25, 48000
SHORT_COVER_FRAMES = 30
COLORS = {"A": A, "B": B, "해설": "#FFB984"}
TITLES = {
    "hook": ["전환율이 3%포인트 높으면", "B가 이긴 걸까?"],
    "setup": ["무엇을 비교했을까?"],
    "assign": ["방문자를 무작위로 나눕니다"],
    "compare": ["가입을 완료한 사람은?"],
    "gap": ["관찰한 차이"],
    "assume": ["화면 효과가 없다고", "가정해 봅시다"],
    "shuffle1": ["배정을 다시 섞어 보면"],
    "shuffle2": ["배정을 다시 섞어 보면"],
    "dist": ["이 정도 차이는 얼마나 흔할까?"],
    "close": ["B가 이긴 걸까?"],
    "decision": ["실제 적용을 결정할 때"],
}

@lru_cache
def font(size, bold=False):
    path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "NotoSansKR-VF.ttf"
    if path.is_file():
        face = ImageFont.truetype(str(path), size)
        face.set_variation_by_axes([780 if bold else 480])
        return face
    fallback = "malgunbd.ttf" if bold else "malgun.ttf"
    return ImageFont.truetype(str(path.with_name(fallback)), size)

@lru_cache
def mascot(letter, size):
    directory = os.environ.get("VIDEO_MASCOT_DIR")
    if not directory:
        return None
    asset = Path(directory) / f"{letter}_soft.png"
    with Image.open(asset) as original:
        image = original.convert("RGBA")
    image = image.crop(image.getbbox())
    width = round(image.width * size / image.height)
    return image.resize((width, size), Image.Resampling.LANCZOS)

class Board:
    def __init__(self, vertical):
        self.vertical = vertical
        self.width, self.height = (540, 960) if vertical else (960, 540)
        self.image = Image.new("RGB", (self.width, self.height), PAPER)
        self.draw = ImageDraw.Draw(self.image)
        self.left, self.right = (36, 460) if vertical else (48, 912)
        self.center = (self.left + self.right) // 2
        accent_y = 81 if vertical else 14
        self.draw.line((self.left, accent_y, self.left+51, accent_y), fill=ORANGE, width=4)

    def text(self, x, y, label, size, color=INK, bold=False, anchor="lt"):
        self.draw.text((x, y), label, font=font(size, bold), fill=color, anchor=anchor)

    def box(self, x1, y1, x2, y2, fill, radius=10, outline=None):
        self.draw.rounded_rectangle((x1,y1,x2,y2), radius=min(radius, 12), fill=fill, outline=outline, width=1)

    def put_mascot(self, x, y, letter, size):
        image = mascot(letter, size)
        if image is None:
            self.text(x, y, letter, round(size * 0.74), A if letter == "A" else B, True, "mm")
        else:
            self.image.paste(image, (round(x-image.width/2), round(y-image.height/2)), image)

    def subtitle(self, speaker, line):
        y = 729 if self.vertical else 424
        h = 119 if self.vertical else 104
        size = 24
        speaker_size = size + 11 if speaker in {"A", "B"} else size
        separator = " | "
        speaker_width = self.draw.textlength(speaker, font=font(speaker_size, True))
        separator_width = self.draw.textlength(separator, font=font(size))
        prefix_width = speaker_width + separator_width
        max_width = self.right-self.left-32
        rows = []
        for sentence in line.splitlines():
            rows.append("")
            for word in sentence.split():
                prefix = prefix_width if len(rows) == 1 else 0
                merged = f"{rows[-1]} {word}".strip()
                if rows[-1] and self.draw.textlength(merged, font=font(size)) + prefix > max_width:
                    rows.append(word)
                else:
                    rows[-1] = merged
        widths = [self.draw.textlength(row, font=font(size)) for row in rows]
        widths[0] += prefix_width
        if len(rows) > (3 if self.vertical else 2) or max(widths) > max_width:
            raise ValueError(f"지정된 글자 크기와 줄 간격에 맞춰 자막을 줄여 주세요: {line}")
        self.box(self.left, y, self.right, y+h, INK, radius=17)
        speaker_color = {"A": "#A8D3FA", "B": "#FFB9C9"}.get(speaker, COLORS["해설"])
        line_height = 34
        first_bounds = [
            self.draw.textbbox((0,0), word, font=face, anchor="ls")
            for word, face in [
                (speaker, font(speaker_size, True)), (separator, font(size)), (rows[0], font(size))
            ]
        ]
        last = self.draw.textbbox((0,0), rows[-1], font=font(size), anchor="ls")
        top = min(box[1] for box in first_bounds)
        bottom = max(max(box[3] for box in first_bounds), (len(rows)-1)*line_height + last[3])
        baseline = y + (h - top - bottom)/2
        speaker_x = self.center - widths[0]/2
        self.text(speaker_x,baseline,speaker,speaker_size,speaker_color,True,"ls")
        self.text(speaker_x+speaker_width,baseline,separator,size,"#D2DBDF",False,"ls")
        self.text(speaker_x+prefix_width,baseline,rows[0],size,WHITE,False,"ls")
        for index, row in enumerate(rows[1:],start=1):
            self.text(self.center-widths[index]/2,baseline+index*line_height,row,size,WHITE,False,"ls")

    def header(self, scene, current):
        y = 104 if self.vertical else 25
        step = {"hook":"오늘의 질문", "setup":"실험 설정", "assign":"실험 설정", "compare":"가입률 계산",
                "gap":"가입률 계산", "assume":"우연을 가정해 보기", "shuffle1":"배정 예시 1",
                "shuffle2":"배정 예시 2", "dist":"가능한 배정 전체", "close":"이번 실험의 판단",
                "decision":"실제 적용을 결정할 때"}[scene]
        if self.vertical and scene == "shuffle2":
            step = "배정 바꾸기"
        self.text(self.left,y,step,17,ORANGE,True)
        text = TITLES[scene]
        if scene == "hook":
            text = [f"전환율이 {V['gap']}%포인트 높으면", "B가 이긴 걸까?"]
        if not self.vertical:
            text = [" ".join(text)]
        size = 39 if self.vertical else 41
        while any(self.draw.textlength(row, font=font(size, True)) > self.right-self.left for row in text):
            size -= 1
        for i,row in enumerate(text):
            self.text(self.left,y+26+i*42,row,size,INK,True)
        self.text(self.left,218 if self.vertical else 98,"교육용 가상 데이터",15,MUTED)

    def pair(self, mode, speaker="해설"):
        if self.vertical:
            boxes = [(self.left,252,self.right,449),(self.left,472,self.right,669)]
        else:
            boxes = [(48,124,465,405),(495,124,912,405)]
        for index,(x,y,r,d) in enumerate(boxes):
            letter, fill, color, rate, count = (( "A", A_PALE, A, V["rate_a"], a),
                                               ("B", B_PALE, B, V["rate_b"], b))[index]
            self.box(x,y,r,d,fill,12,color if speaker==letter else LINE)
            self.draw.line((x+18,y+16,x+18,y+42), fill=color,width=4)
            self.text(x+30,y+17,"기존 화면 A" if index==0 else "새 화면 B",23,color,True)
            if letter == "B" and mode in {"hook", "compare"}:
                self.box(r-160,y+16,r-17,y+48,B,8)
                label = " | 이번 결과 1위"
                b_width = self.draw.textlength("B", font=font(23, True))
                label_width = self.draw.textlength(label, font=font(16, True))
                badge_x = r-88-(b_width+label_width)/2
                self.text(badge_x,y+32,"B",23,WHITE,True,"lm")
                self.text(badge_x+b_width,y+32,label,16,WHITE,True,"lm")
            if mode in {"hook","setup"}:
                if self.vertical:
                    self.put_mascot(x+87,y+109,letter,116)
                    label_x, label_y = x+177,y+78
                else:
                    self.put_mascot(x+123,y+150,letter,150)
                    label_x, label_y=x+223,y+103
                if mode=="hook":
                    self.text(label_x,label_y,f"{rate}%",67,color,True)
                    self.text(label_x+1,label_y+76,"가입 완료율",17,MUTED)
                else:
                    self.box(label_x,label_y-14,label_x+150,label_y+73,WHITE,9,LINE)
                    self.draw.line((label_x+14,label_y+6,label_x+124,label_y+6), fill=LINE,width=3)
                    self.draw.line((label_x+14,label_y+20,label_x+110,label_y+20), fill=LINE,width=3)
                    self.box(label_x+13,label_y+34,label_x+137,label_y+61,color,6)
                    self.text(label_x+75,label_y+40,"가입하기",15,WHITE,True,"mt")
            else:
                self.grid(x+23,y+60 if not self.vertical else y+56,count if mode=="compare" else 0,color,fill)
                self.text(x+195,y+75 if self.vertical else y+98,
                          f"{rate}%" if mode=="compare" else f"{n}명",56,color,True)
                if mode=="compare":
                    self.text(x+197,y+140 if self.vertical else y+168,f"{count}명 가입 / {n}명 방문",16,MUTED)
                else:
                    self.text(x+197,y+139 if self.vertical else y+169,"무작위 배정",17,MUTED)

    def grid(self,x,y,count,color,fill):
        # Each cell is one visitor in this episode's fixed 100-person group.
        cols=10
        spacing=13 if self.vertical else 15
        for i in range(n):
            xx,yy = x+(i%cols)*spacing, y+(i//cols)*spacing
            hit = i < count
            self.draw.ellipse((xx,yy,xx+10,yy+10),
                              fill=color if hit else WHITE,outline=color if hit else LINE)
            if hit:
                self.draw.line((xx+2,yy+5,xx+4,yy+7,xx+8,yy+3),fill=WHITE,width=1)

    def metric(self, scene, speaker):
        x,y,r,d=(self.left,270,self.right,669) if self.vertical else (48,124,912,405)
        self.box(x,y,r,d,WHITE,24,LINE)
        cx=(x+r)//2
        if scene=="gap":
            self.text(cx,y+60 if self.vertical else y+42,f"{V['rate_b']}%  -  {V['rate_a']}%",45,INK,True,"mt")
            self.text(cx,y+147 if self.vertical else y+107,f"+{V['gap']}%포인트",60,ORANGE,True,"mt")
            self.text(cx,y+246 if self.vertical else y+201,"이번 실험에서 B가 앞선 폭",19,MUTED,False,"mt")
        elif scene=="assume":
            self.text(cx,y+37,"가입을 완료한 사람",25,INK,True,"mt")
            self.text(cx,y+86,f"{V['joined']}명",62,ORANGE,True,"mt")
            size=17
            step=25
            for i in range(V["joined"]):
                row,col=divmod(i,12)
                spread=min(12,V["joined"]-row*12)
                xx=cx-(spread*step-step+size)/2+col*step
                yy=y+164+row*25
                self.draw.ellipse((xx,yy,xx+size,yy+size),fill="#FFD4AD")
                self.draw.line((xx+4,yy+8,xx+7,yy+12,xx+13,yy+5),fill=INK,width=2)
            self.text(cx,y+238 if not self.vertical else y+267,"가입자 수를 고정하고 배정표만 섞습니다",19,MUTED,False,"mt")
        elif scene in {"close","decision"}:
            on_close=scene=="close"
            self.text(cx,y+46,"이번 결과 1위" if on_close else "차이의 불확실성",24,MUTED,True,"mt")
            self.text(cx,y+88,f"B +{V['gap']}%포인트" if on_close else "효과 추정 범위 확인",45,ORANGE,True,"mt")
            split=y+(219 if self.vertical else 161)
            self.draw.line((x+25,split,r-25,split), fill=LINE,width=2)
            self.text(cx,split+24,"실험 해석" if on_close else "실제 적용 가치",22,MUTED,True,"mt")
            self.text(cx,split+66,"화면 효과 판단 보류" if on_close else "바꿀 만큼 큰 개선인가?",39,INK,True,"mt")
            if on_close and not self.vertical and speaker in {"A","B"}:
                self.put_mascot(r-91,y+147,speaker,130)

    def shuffle(self, scene):
        example=1 if scene=="shuffle1" else 2
        ca,cb=(V["first_a"],V["first_b"]) if example==1 else (V["second_a"],V["second_b"])
        x,y,r,d=(self.left,255,self.right,681) if self.vertical else (48,124,912,405)
        self.box(x,y,r,d,WHITE,26,LINE)
        self.text(self.center,y+23,f"가입 완료 {V['joined']}명 고정",23,INK,True,"mt")
        for index,(letter,count,color,fill) in enumerate([("A",ca,A,A_PALE),("B",cb,B,B_PALE)]):
            bx,by,w,h=(x+19,y+75+index*126,r-x-38,109) if self.vertical else (x+28+index*414,y+75,394,134)
            self.box(bx,by,bx+w,by+h,fill,17)
            self.text(bx+17,by+14,letter,31,color,True)
            self.text(bx+65,by+18,f"가입 {count}명",29,color,True)
            for i in range(count):
                px,py=bx+18+(i%14)*18,by+69+(i//14)*18
                self.box(px,py,px+12,py+12,color,3)
                self.draw.line((px+2,py+6,px+5,py+9,px+10,py+3),fill=WHITE,width=1)
        delta=cb-ca
        leader="B" if delta>0 else "A"
        self.text(self.center,d-45,f"{leader}가 {abs(delta)}%포인트 앞선 배정",21,INK,True,"mt")

    def redistribution(self, scene, progress):
        x, y, r, d = (self.left,255,self.right,681) if self.vertical else (48,124,912,405)
        self.box(x,y,r,d,WHITE,24,LINE)
        total = V["joined"]
        counts = {"A": V["first_a"], "B": V["first_b"]} if scene=="shuffle1" else {"A": V["second_a"], "B": V["second_b"]}
        self.text(self.center,y+20,f"가입 완료 {total}명 고정",24,INK,True,"mt")

        moved = progress >= 1
        targets = {}
        boxes = (
            [(x+19,386,r-19),(x+19,499,r-19)]
            if self.vertical else [(x+25,236,463),(497,236,r-25)]
        )
        for (letter,color,fill),(bx,top,br) in zip([("A",A,A_PALE),("B",B,B_PALE)],boxes):
            count = counts[letter]
            self.box(bx,top,br,top+100,fill,12,LINE)
            self.text(bx+20,top+13,letter,31,color,True)
            if moved:
                self.text(bx+67,top+18,f"가입 {count}명",23,color,True)
            targets[letter] = [
                ((bx+br)/2+(i-(count-1)/2)*21,top+73) for i in range(count)
            ]

        for i in range(total):
            row, col = divmod(i,12)
            row_size = min(12,total-row*12)
            sx = self.center+(col-(row_size-1)/2)*21
            sy = y+(75 if self.vertical else 64)+row*24
            # Mix destination labels across the tray, preserving the same 23 markers.
            assigned_a = (i+1)*counts["A"]//total
            if assigned_a > i*counts["A"]//total:
                letter, target = "A", targets["A"][assigned_a-1]
            else:
                letter, target = "B", targets["B"][i-assigned_a]
            delay = (i%12)*0.016 + row*0.12
            t = max(0,min(1,(progress-delay)/0.62))
            ease = t*t*(3-2*t)
            px = sx+(target[0]-sx)*ease
            py = sy+(target[1]-sy)*ease
            ink = (A if letter=="A" else B) if t>=1 else ORANGE
            self.draw.ellipse((px-7,py-7,px+7,py+7),fill=ink,outline=WHITE,width=1)
            self.draw.line((px-3,py,px-1,py+3,px+4,py-3),fill=WHITE,width=1)

        message = (f"A {counts['A']}명 + B {counts['B']}명 = {total}명" if moved
                   else "같은 가입자를 A와 B에 다시 배정")
        self.text(self.center,d-45,message,21,INK,True,"mt")

    def distribution(self, show_result):
        x,y,r,d=(self.left,256,self.right,671) if self.vertical else (48,119,912,407)
        self.box(x,y,r,d,WHITE,24,LINE)
        self.text(x+23,y+17,"화면 효과가 없다고 가정",18,MUTED,True)
        self.text(r-22,y+17,f"양쪽 합계 약 {V['tail']}%" if show_result else "A와 B의 가입률 차이",20,ORANGE,True,"rt")
        self.text(x+23,y+50,"배정 확률 (%)",14,MUTED)
        gx,gr=x+56,r-38
        gy=y+(304 if self.vertical else 205)
        h=155 if self.vertical else 124
        shown=[(k,p) for k,p in probabilities.items() if p>=0.0004]
        peak=max(probabilities.values())
        step=(gr-gx)/len(shown)
        for percent in (5, 10, 15):
            yy=gy-h*(percent/100)/peak
            self.draw.line((gx,yy,gr,yy),fill=LINE,width=1)
            self.text(gx-7,yy,str(percent),12,MUTED,False,"rm")
        self.draw.line((gx,gy,gr,gy),fill=MUTED,width=1)
        for i,(gap,p) in enumerate(shown):
            mid=gx+(i+.5)*step
            barh=max(1,round(h*p/peak))
            extreme=abs(gap)>=b-a
            fill=(A if gap<0 else B) if extreme else "#9DA8AC"
            self.box(mid-step*.32,gy-barh,mid+step*.32,gy,fill,min(4,barh//2))
            if abs(gap) in {b-a,b-a+6}:
                pp=100*gap/n
                self.text(mid,gy+9,f"{pp:+g}",13,MUTED,False,"mt")
        self.text(gx,gy+36,"A가 더 높음",17,A,True)
        self.text(gr,gy+36,"B가 더 높음",17,B,True,"rt")
        self.text(self.center,gy+37,"차이 (%포인트)",15,MUTED,False,"mt")

def compose(board):
    # Apply the same outer inset on all four sides; center the usable layout inside it.
    crop = (34, 77, 463, 851) if board.vertical else (46, 10, 915, 530)
    margin = 60 if board.vertical else 31
    content = ImageOps.contain(
        board.image.crop(crop),
        (board.width-2*margin, board.height-2*margin),
        Image.Resampling.LANCZOS,
    )
    image = Image.new("RGB", board.image.size, PAPER)
    image.paste(content, ((board.width-content.width)//2,(board.height-content.height)//2))
    return image

def short_cover():
    board = Board(True)
    center = board.center
    board.text(center,177,"전환율 A/B 실험",23,ORANGE,True,"mt")
    board.text(center,232,f"{V['gap']}%포인트 차이",51,INK,True,"mt")
    board.text(center,303,"B가 이긴 걸까?",54,INK,True,"mt")
    for letter, x, color, tint, rate in [
        ("A",139,A,A_PALE,V["rate_a"]),("B",357,B,B_PALE,V["rate_b"])
    ]:
        board.draw.ellipse((x-83,414,x+83,580),fill=tint,outline=color,width=2)
        board.put_mascot(x,496,letter,115)
        board.text(x,604,f"{rate}%",44,color,True,"mt")
    board.text(center,716,"교육용 가상 데이터",18,MUTED,False,"mt")
    return compose(board)

def focus_diagram(board, scene, focus):
    left, right, center = board.left, board.right, board.center
    upper, lower = (left,251,right,450), (left,470,right,671)
    groups = {
        "hook": {"winner": [(right-165,484,right-13,525),(left+172,543,right-16,646)],
                 "b_rate": [(left+170,543,right-16,646)], "pair": [upper,lower]},
        "compare": {"pair": [upper,lower], "a_card": [upper], "b_card": [lower]},
        "assume": {"fixed": [(left+45,305,right-45,494)]},
        "shuffle2": {"motion": [(left+17,268,right-17,606)],
                     "a_card": [(left+18,384,right-18,488)],
                     "b_card": [(left+18,497,right-18,601)],
                     "sum": [(left+18,627,right-18,670)],
                     "pair": [(left+17,384,right-17,602)]},
        "close": {"result": [(left+31,310,right-31,414)],
                  "meaning": [(left+20,505,right-20,596)]},
    }
    if not board.vertical:
        upper,lower=(48,124,465,405),(495,124,912,405)
        both=[upper,lower]
        groups={
            "hook":{"winner":[(747,137,901,176),(711,223,889,324)],
                    "pair":both,"a_card":[upper],"b_card":[lower]},
            "setup":{"pair":both},
            "compare":{"pair":both,"a_card":[upper],"b_card":[lower]},
            "assign":{"pair":both,"a_card":[upper],"b_card":[lower]},
            "assume":{"assumption":[(315,156,645,197)],"fixed":[(292,157,668,329)]},
            "dist":{"curve":[(73,164,895,375)],"center":[(410,168,553,369)],
                    "tails":[(84,174,433,369),(528,174,891,369)],
                    "assumption":[(66,130,368,160)],"total":[(681,127,899,164)]},
            "close":{"result":[(275,167,682,264)],"meaning":[(266,296,692,401)]},
            "decision":{"result":[(245,163,714,265)],"meaning":[(245,294,717,402)]}
        }
        for name in ("shuffle1","shuffle2"):
            groups[name]={"motion":[(68,143,893,338)],"a_card":[(69,233,465,338)],
                          "b_card":[(494,233,889,338)],"sum":[(295,141,666,174),(288,353,676,385)],
                          "pair":[(69,232,889,339)]}
    if scene == "gap":
        face=font(45,True)
        b_width=board.draw.textlength(f"{V['rate_b']}%",font=face)
        a_width=board.draw.textlength(f"{V['rate_a']}%",font=face)
        separator=board.draw.textlength("  -  ",font=face)
        start=center-(a_width+b_width+separator)/2
        a_start=start+b_width+separator
        number_top,number_bottom=(323,380) if board.vertical else (162,222)
        groups["gap"]={
            "a_rate":[(a_start-7,number_top,a_start+a_width+7,number_bottom)],
            "b_rate":[(start-7,number_top,start+b_width+7,number_bottom)],
            "difference":[(left+33,408,right-33,548) if board.vertical else (289,226,670,354)],
        }

    # Soften the diagram only. Keep the title and caption fully readable.
    original=board.image
    dimmed=Image.blend(original,Image.new("RGB",original.size,PAPER),0.42)
    veil=Image.new("L",original.size,0)
    mask=ImageDraw.Draw(veil)
    mask.rectangle((left,243,right,689) if board.vertical else (left,116,right,410),fill=255)
    for bounds in groups[scene][focus]:
        mask.rounded_rectangle(bounds,radius=9,fill=0)
    original.paste(dimmed,(0,0),veil.filter(ImageFilter.GaussianBlur(4)))

def frame(scene, speaker, line, vertical, prior, progress=1, focus=None):
    board = Board(vertical)
    board.header(scene, speaker)
    if scene in {"hook","setup","assign","compare"}:
        board.pair(scene, speaker)
    elif scene in {"shuffle1","shuffle2"}:
        if vertical and scene=="shuffle1":
            board.shuffle(scene)
        else:
            board.redistribution(scene,progress)
    elif scene == "dist":
        board.distribution(prior >= 2)
    else:
        board.metric(scene,speaker)
    if focus is not None:
        focus_diagram(board, scene, focus)
    board.subtitle(speaker,line)
    return compose(board)

def run(*args, capture=False):
    return subprocess.run(args,check=True,stdout=subprocess.PIPE if capture else None).stdout

def timecode(milliseconds):
    seconds,ms=divmod(milliseconds,1000)
    minutes,seconds=divmod(seconds,60)
    hours,minutes=divmod(minutes,60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"

def render(version, destination, *, storyboard=None, stem=None, focus_schedule=None):
    vertical=version=="short"
    resolution="1080:1920" if vertical else "1920:1080"
    stem=stem or ("ep01-short" if vertical else "ep01-long")
    scenes, draw_frame, make_cover = storyboard or (lines(version), frame, short_cover)
    schedule = focus_schedule if focus_schedule is not None else ({} if storyboard else DATA.get(f'{version}_focus',{}))
    with tempfile.TemporaryDirectory(prefix="ab-render-",dir=destination) as temp:
        work=Path(temp)
        audio=work/"voice.wav"
        playlist=["ffconcat version 1.0"]
        subtitles=[]
        shots=[]
        offset=0
        seen={}
        with wave.open(str(audio),"wb") as wav:
            wav.setparams((1,2,SAMPLE_RATE,0,"NONE","not compressed"))
            if vertical:
                cover_duration=SHORT_COVER_FRAMES/FPS
                make_cover().save(work/"cover.png")
                playlist.extend(["file 'cover.png'", f"duration {cover_duration:.6f}"])
                shots.append({"scene":"cover","start_seconds":0,"duration_seconds":cover_duration})
            for i,(scene,speaker,line) in enumerate(scenes):
                prior=seen.get(scene,0)
                seen[scene]=prior+1
                cover_overlap=SHORT_COVER_FRAMES if vertical and i==0 else 0
                trim=["-af","silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB"] if cover_overlap else []
                pcm=run("ffmpeg","-v","error","-i",str(audio_path(speaker,line)),*trim,"-ar",str(SAMPLE_RATE),
                        "-ac","1","-f","s16le","pipe:1",capture=True)
                if not pcm:
                    raise RuntimeError(f"음성이 비어 있습니다: {line}")
                lead=0 if cover_overlap else 3 if i==0 else 2
                pause=(16 if not vertical else 6) if i+1==len(scenes) or scenes[i+1][0]!=scene else 4
                samples_per_frame=SAMPLE_RATE//FPS
                count=max(cover_overlap+1,lead+math.ceil(len(pcm)/2/samples_per_frame)+pause)
                total_samples=count*samples_per_frame
                wav.writeframesraw(bytes(2*lead*samples_per_frame)+pcm+
                                   bytes(2*(total_samples-lead*samples_per_frame)-len(pcm)))
                visible_frames=count-cover_overlap
                animate = prior==0 and (scene=="shuffle2" or (not vertical and scene=="shuffle1"))
                motion_frames=min(76 if vertical else 34,visible_frames-1) if animate else 0
                focus_key = f"{scene}:{prior+1}" if prior else scene
                focus_cues = schedule.get(focus_key,[])
                focus_by_frame = {
                    (0 if seconds == 0 else max(0,lead+round(seconds*FPS)-cover_overlap)): target
                    for seconds,target in focus_cues
                    if lead+round(seconds*FPS)-cover_overlap < visible_frames
                }
                focus_frames=sorted(focus_by_frame)
                cuts=sorted({0,visible_frames,motion_frames,*range(0,motion_frames,2),*focus_frames})
                for position,following in zip(cuts,cuts[1:]):
                    focus_index=bisect_right(focus_frames,position)-1
                    current_focus=focus_by_frame[focus_frames[focus_index]] if focus_index>=0 else None
                    motion_hold = 18 if vertical else 3
                    progress=1 if position>=motion_frames else max(0,(position-motion_hold)/max(1,motion_frames-motion_hold-2))
                    name=f"frame-{i:02d}-{position:03d}.png"
                    draw_frame(scene,speaker,line,vertical,prior,progress,current_focus).save(work/name)
                    playlist.extend([f"file '{name}'",f"duration {(following-position)/FPS:.6f}"])
                start_ms=round((offset+lead)*1000/FPS)
                stop_ms=round((offset+lead+len(pcm)/2/samples_per_frame)*1000/FPS)
                subtitles.append(f"{i+1}\n{timecode(start_ms)} --> {timecode(stop_ms)}\n{speaker} | {line}\n")
                shot={"scene":scene,"start_seconds":(offset+cover_overlap)/FPS,
                      "duration_seconds":visible_frames/FPS}
                if motion_frames:
                    shot["animation_seconds"]=motion_frames/FPS
                if focus_frames:
                    shot["focus_cues"]=[
                        {"start_seconds":p/FPS,"target":focus_by_frame[p]} for p in focus_frames
                    ]
                shots.append(shot)
                offset+=count
        playlist.append(f"file '{name}'")
        (work/"scenes.ffconcat").write_text("\n".join(playlist)+"\n",encoding="ascii")
        (work/"captions.srt").write_text("\n".join(subtitles),encoding="utf-8")
        (work/"shots.json").write_text(json.dumps(shots,ensure_ascii=False,indent=2),encoding="utf-8")
        run("ffmpeg","-v","error","-f","concat","-safe","0","-i",str(work/"scenes.ffconcat"),
            "-i",str(audio),"-vf",f"fps={FPS},scale={resolution}:flags=lanczos,format=yuv420p",
            "-c:v","libx264","-threads","4","-preset","veryfast","-crf","19","-c:a","aac","-b:a","128k",
            "-movflags","+faststart","-t",f"{offset/FPS:.3f}",str(work/"video.mp4"))
        for src,ext in [("video.mp4","mp4"),("captions.srt","srt"),("shots.json","json")]:
            (work/src).replace(destination/f"{stem}.{ext}")
        print(f"{stem}: {offset/FPS:.2f}초",flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--version",choices=("both","long","short"),default="both")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    destination=(args.output or ROOT/"renders").resolve()
    destination.mkdir(parents=True,exist_ok=True)
    versions=("long","short") if args.version=="both" else (args.version,)
    if n!=100 or V["joined"]>24 or max(V["first_a"],V["first_b"],V["second_a"],V["second_b"])>28:
        raise ValueError("이 장면의 격자는 그룹당 100명, 전체 가입 24명까지 표시합니다.")
    if any((destination/f"ep01-{v}.{ext}").exists() for v in versions for ext in ("mp4","srt","json")):
        parser.error("기존 결과를 보관하려면 --output에 새 폴더를 지정하세요.")
    asyncio.run(synthesize(versions))
    for version in versions:
        render(version,destination)

if __name__=="__main__":
    main()
