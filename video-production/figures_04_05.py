from PIL import Image,ImageDraw,ImageFilter

from make_shorts import heading
from render import A,B,INK,LINE,MUTED,ORANGE,PAPER,WHITE
from storyboards_04_05 import gap, interval, SMALL, LARGE, observed, probabilities, tail_percent

def _soften(board, pane, regions):
    if not regions:
        return
    source=board.image
    faded=Image.blend(source,Image.new("RGB",source.size,PAPER),0.42)
    mask=Image.new("L",source.size)
    draw=ImageDraw.Draw(mask)
    draw.rectangle(pane,fill=255)
    for bounds in regions:
        draw.rectangle(bounds,fill=0)
    source.paste(faded,(0,0),mask.filter(ImageFilter.GaussianBlur(3)))

def plot(board,title,kind,focus):
    x,r=board.left,board.right
    top,bottom=(250,669) if board.vertical else (123,407)
    heading(board,title,x,132 if board.vertical else 42,r-x,40)
    board.text(x,215 if board.vertical else 93,"교육용 가상 데이터",15,MUTED)
    board.box(x,top,r,bottom,WHITE,12,LINE)
    marks = _p_chart(board,x,top,r,bottom,focus) if kind=="p" else _ci_chart(board,x,top,r,bottom)
    if focus is not None and focus not in marks:
        raise ValueError(f"강조할 그래프 영역이 없습니다: {kind}, {focus}")
    selected = marks.get(focus)
    if selected:
        _soften(board,(x,top,r,bottom),[*selected, *marks["reference"]])

def _p_chart(board,x,y,r,d,focus):
    cx=(x+r)//2
    # Every odd difference is possible here because total observed conversions is odd.
    values=[(point,p) for point,p in probabilities.items() if abs(point)<=15]
    left,right=x+34,r-35
    base=y+(257 if board.vertical else 188)
    height=154 if board.vertical else 122
    step=(right-left)/len(values)
    bar_w=step*0.68
    peak=max(probabilities.values())
    board.text(x+17,y+15,"화면 효과가 없다고 가정",23,INK,True)
    board.text(x+18,y+51,"배정 확률 (%)",19,INK,True)
    for percent in (5,10,15):
        gy=base-height*(percent/100)/peak
        board.draw.line((left,gy,right,gy),fill=LINE,width=1)
        board.text(left-6,gy,str(percent),15,INK,True,"rm")
    board.draw.line((left,base,right,base),fill=MUTED,width=1)
    xcoord={}
    for i,(point,p) in enumerate(values):
        bx=left+(i+.5)*step
        xcoord[point]=bx
        h=max(1,round(height*p/peak))
        color=A if point<=-observed else B if point>=observed else "#A6B1B7"
        board.box(bx-bar_w/2,base-h,bx+bar_w/2,base,color,2)
    for point in (-9,-3,3,9):
        board.text(xcoord[point],base+10,f"{point:+g}",22 if abs(point)==3 else 17,
                   ORANGE if abs(point)==3 else INK,True,"mt")
    board.text(cx,base+38,"B - A 전환율 차이 (%포인트)",20,INK,True,"mt")
    if board.vertical:
        board.text(left,base+11,"A",16,A,True)
        board.text(right,base+11,"B",16,B,True,"rt")
    else:
        board.text(left,base+11,"A가 더 높음",16,A,True)
        board.text(right,base+11,"B가 더 높음",16,B,True,"rt")
    for point in (-observed, observed):
        xx = xcoord[point]
        board.draw.line((xx,base-8,xx,base+4),fill=ORANGE,width=3)
    if focus=="p_value":
        if board.vertical:
            board.text(cx,d-68,f"p값 약 0.66 ({tail_percent}%)",37,ORANGE,True,"mt")
        else:
            board.text(r-24,y+17,f"p값 약 0.66 ({tail_percent}%)",24,ORANGE,True,"rt")
    box_top=base-height-12
    left_band=(left-3,box_top,xcoord[-observed]+step*.48,base+29)
    right_band=(xcoord[observed]-step*.48,box_top,right+3,base+29)
    center_band=(xcoord[-1]-step*.49,box_top,xcoord[1]+step*.49,base+10)
    value_box=(x+60,d-73,r-58,d-20) if board.vertical else (r-258,y+14,r-12,y+52)
    return {
        "plot": (), "left_tail":[left_band], "right_tail":[right_band], "tails":[left_band,right_band],
        "center":[center_band], "p_value":[value_box],
        "reference":[(x+10,y+10,x+281,y+79),(x+10,base-7,r-10,base+66)],
    }

def _ci_chart(board,x,y,r,d):
    left,right=x+40,r-35
    cx=(x+r)//2
    ymin,ymax=-5,10
    def px(value):
        return left+(value-ymin)/(ymax-ymin)*(right-left)
    positions=(y+137,y+228) if board.vertical else (y+117,y+178)
    base=y+(294 if board.vertical else 217)
    heading(board,"B - A의 근사 95% 신뢰구간",x+16,y+15,r-x-32,23)
    board.text(px(0),y+49,"0 변화 없음",20,INK,True,"mt")
    for dashed in range(y+75,base,12):
        board.draw.line((px(0),dashed,px(0),min(dashed+7,base)),fill=MUTED,width=3)
    board.draw.line((left,base,right,base),fill=MUTED,width=1)
    for value in (-5,0,3,10):
        board.draw.line((px(value),base-4,px(value),base+5),fill=MUTED,width=1)
        board.text(px(value),base+11,f"{value:+g}" if value else "0",19,INK,True,"mt")
    board.text(cx,base+36,"전환율 차이 (%포인트)",21,INK,True,"mt")
    bands=[]
    for n,color,cy in zip((SMALL,LARGE),(B,A),positions):
        low,high=interval(n)
        name = f"각 {n:,}명 | {'넓음' if n == SMALL else '좁음'}"
        bounds = f"{low:+.1f} ~ {high:+.1f}"
        board.draw.rectangle((left-4,cy-38,left+161,cy-10),fill=WHITE)
        board.text(left,cy-35,name,21,color,True)
        board.text(right,cy-32,bounds,23,INK,True,"rt")
        board.draw.line((px(low),cy,px(high),cy),fill=color,width=5)
        for edge in (low,high):
            board.draw.line((px(edge),cy-7,px(edge),cy+7),fill=color,width=2)
        board.draw.ellipse((px(gap)-6,cy-6,px(gap)+6,cy+6),fill=color,outline=WHITE,width=1)
        bands.append((left-3,cy-38,right+3,cy+9))
    return {
        "plot":(),"small":[bands[0]],"large":[bands[1]],
        "reference":[(x+13,y+11,r-13,y+43),(px(0)-63,y+45,px(0)+63,y+75),
                     (px(0)-4,y+76,px(0)+4,base+5),(x+10,base-2,r-10,base+65)],
        "point":[(px(gap)-12,cy-12,px(gap)+12,cy+12) for cy in positions],
        "zero":[(px(0)-15,y+57,px(0)+15,base+32),bands[0]],
    }
