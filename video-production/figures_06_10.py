from make_shorts import heading
from render import A, B, INK, LINE, MUTED, ORANGE, WHITE

from figures_04_05 import _soften
from storyboards_06_10 import ALPHA, CI, ERROR_LIMIT, ERROR_RESULT, LOOKS, OPTIONS, POWERS, REPEATED, SIZES, TARGET

KINDS = {"interval", "repeat", "power80", "power_sizes", "practical", "overlap", "peeking", "decision"}


def plot(board, title, kind, focus):
    x, r = board.left, board.right
    y, bottom = (250, 669) if board.vertical else (123, 407)
    heading(board, title, x, 132 if board.vertical else 42, r-x, 40)
    board.text(x, 215 if board.vertical else 93, "교육용 가상 데이터", 15, MUTED)
    board.box(x, y, r, bottom, WHITE, 12, LINE)
    if kind in {"interval", "repeat", "practical", "overlap"}:
        marks = intervals(board, kind, x, y, r, bottom)
    elif kind in {"power80", "power_sizes"}:
        marks = power_dots(board, kind, x, y, r, bottom)
    elif kind == "peeking":
        marks = peeking(board, x, y, r, bottom)
    else:
        marks = decision(board, x, y, r, bottom)
    if focus not in {None, "all"}:
        _soften(board, (x, y, r, bottom), [*marks[focus], *marks.get("reference", [])])


def dashed(board, x, y, end, color):
    for start in range(y, end, 10):
        board.draw.line((x, start, x, min(start+6, end)), fill=color, width=3)


def line_mark(board, scale, y, low, high, color, point):
    board.draw.line((scale(low), y, scale(high), y), fill=color, width=5)
    for edge in (low, high):
        board.draw.line((scale(edge), y-5, scale(edge), y+5), fill=color, width=2)
    cx = scale(point)
    board.draw.ellipse((cx-5, y-5, cx+5, y+5), fill=color, outline=WHITE)


def axis(board, left, right, base, domain, ticks, label):
    def scale(value):
        return left+(value-domain[0])/(domain[1]-domain[0])*(right-left)

    board.draw.line((left, base, right, base), fill=MUTED, width=1)
    for value in ticks:
        x = scale(value)
        board.draw.line((x, base-3, x, base+4), fill=MUTED)
        board.text(x, base+8, f"{value:g}", 19, INK, True, "mt")
    if label:
        board.text((left+right)/2, base+31, label, 21, INK, True, "mt")
    return scale


def intervals(board, kind, x, y, r, bottom):
    left, right, base = x+40, r-36, bottom-72
    reference = [(x+10,base-3,r-10,bottom-6)]
    plot_top = y+68
    if kind == "repeat":
        plot_top = y+99
        scale = axis(board, left, right, base, (-1, 8), (-1, 0, 3, 5, 8), "전환율 차이 (%포인트)")
        board.text(x+18, y+15, "8줄은 설명용 예시", 24, INK, True)
        dashed(board, scale(3), plot_top-12, base, ORANGE)
        board.text(scale(3), plot_top-17, "가정한 실제 차이 +3", 22, ORANGE, True, "mb")
        bands = []
        for i, (low, high) in enumerate(REPEATED):
            row_y = round(plot_top+(i+.5)*(base-plot_top)/len(REPEATED))
            hit = low <= 3 <= high
            line_mark(board, scale, row_y, low, high, A if hit else B, (low+high)/2)
            bands.append((scale(low)-8, row_y-8, scale(high)+8, row_y+8))
        return {"hit": [bands[1]], "miss": [bands[3]], "example": [(x+11,y+9,r-11,y+49)],
                "reference": [*reference, (x+11,y+9,x+245,y+48),
                              (scale(3)-133,y+51,scale(3)+133,plot_top-12),
                              (scale(3)-4,plot_top-12,scale(3)+4,base)],
                "truth": [(scale(3)-93, y+45, scale(3)+93, plot_top-12),
                          (scale(3)-6, plot_top-12, scale(3)+6, base+22)]}
    if kind == "interval":
        scale = axis(board, left, right, base, (-1, 7), (0, 1, 3, 5, 7), "전환율 차이 (%포인트)")
        row = (plot_top+base)//2
        board.text(x+18, y+17, "그룹당 2,000명", 22, INK, True)
        line_mark(board, scale, row, *CI, A, 3)
        for value, name in ((CI[0], f"{CI[0]:+g}"), (3, "+3"), (CI[1], f"{CI[1]:+g}")):
            board.text(scale(value), row-50, name, 32, ORANGE if value == 3 else A, True, "mt")
        box = (scale(CI[0])-29, row-55, scale(CI[1])+29, row+10)
        return {"sample": [box], "point": [(scale(3)-28, row-55, scale(3)+28, row+10)],
                "reference": reference}

    scale = axis(board, left, right, base, (-.7, 4.7), (0, 1, 2, 3, 4), "전환율 차이 (%포인트)")
    for value, label, color in ((0, "0 변화 없음", INK), (TARGET, "+2 적용 기준", ORANGE)):
        dashed(board, scale(value), plot_top-8, base, color)
        board.text(scale(value), plot_top-42, label, 22, color, True, "mt")
    rows = ((.7, 3.3),) if kind == "overlap" else OPTIONS
    marks = {"zero": [(scale(0)-52, plot_top-47, scale(0)+52, base+22)],
             "goal": [(scale(TARGET)-63, plot_top-47, scale(TARGET)+63, base+22)],
             "reference": [*reference,
                           (scale(0)-52,plot_top-47,scale(0)+52,plot_top-15),
                           (scale(TARGET)-63,plot_top-47,scale(TARGET)+63,plot_top-15),
                           (scale(0)-3,plot_top-14,scale(0)+3,base),
                           (scale(TARGET)-3,plot_top-14,scale(TARGET)+3,base)]}
    for (low, high), key, color, fraction in zip(
            rows, ("middle",) if kind == "overlap" else ("low", "high"), (A, B),
            (.47,) if kind == "overlap" else (.31, .77)):
        row = round(plot_top+(base-plot_top)*fraction)
        line_mark(board, scale, row, low, high, color, (low+high)/2)
        board.text((scale(low)+scale(high))/2, row-34, f"{low:+g} ~ {high:+g}", 24, color, True, "mt")
        mid = (scale(low)+scale(high))/2
        marks[key] = [(min(mid-79,scale(low)-10),row-39,max(mid+79,scale(high)+10),row+10)]
    return marks


def power_dots(board, kind, x, y, r, bottom):
    cx = (x+r)//2
    if kind == "power80":
        step = 25 if board.vertical else 16
        top = y+(48 if board.vertical else 35)
        left = cx-4.5*step
        for i in range(100):
            row, column = divmod(i, 10)
            dx, dy = left+column*step, top+row*step
            color = A if i < 80 else B
            board.draw.ellipse((dx-5, dy-5, dx+5, dy+5), fill=color if i < 80 else WHITE, outline=color, width=2)
        labels_y = top+10*step+14
        board.text(cx-96, labels_y, "약 80회 감지", 26, A, True, "mt")
        board.text(cx+96, labels_y, "약 20회 놓침", 26, B, True, "mt")
        board.text(cx, labels_y+39, "같은 실험 100번을 가정", 20, INK, True, "mt")
        return {"detected": [(left-9, top-9, cx+128, top+7*step+8),
                             (cx-181, labels_y-4, cx-13, labels_y+36)],
                "miss": [(left-9, top+8*step-8, cx+128, top+9*step+8),
                         (cx+13, labels_y-4, cx+181, labels_y+36)],
                "reference": [(cx-128,labels_y+37,cx+128,labels_y+68)]}
    marks = {}
    for i, (n, value, color, key) in enumerate(zip(SIZES, POWERS, (A, B), ("first", "second"))):
        if board.vertical:
            left, right = x+34, r-34
            top = y+36+i*188
        else:
            left, right = x+38+i*(cx-x), cx-38+i*(cx-x)
            top = y+42
        panel_x = (left+right)//2
        board.text(panel_x, top, f"그룹당 {n:,}명", 27, color, True, "mt")
        board.text(panel_x, top+40, f"약 {value}%", 50, color, True, "mt")
        board.box(left, top+103, right, top+126, LINE, 6)
        board.box(left, top+103, left+(right-left)*value/100, top+126, color, 6)
        board.text(panel_x, top+142, "가정한 효과를 감지할 확률", 20, INK, True, "mt")
        marks[key] = [(left-8, top-8, right+8, top+163)]
    return marks


def peeking(board, x, y, r, bottom):
    left, right, base = x+65, r-39, bottom-76
    top = y+55
    xs = (left+17, (left+right)/2, right-20)
    def py(p):
        return base-p/.14*(base-top)

    for p in (0, ALPHA):
        cy = py(p)
        board.draw.line((left, cy, right, cy), fill=ORANGE if p == ALPHA else LINE, width=3 if p == ALPHA else 1)
        board.text(left-9, cy, f"{p:.2f}", 19, ORANGE if p == ALPHA else INK, True, "rm")
    board.text(x+19, y+14, "p값", 23, INK, True)
    board.text(r-22, y+14, "판정선 0.05", 22, ORANGE, True, "rt")
    points = [(px, py(p)) for px, p in zip(xs, LOOKS)]
    board.draw.line(points, fill=MUTED, width=2)
    threshold = [(x+11,py(ALPHA)-13,right+9,py(ALPHA)+6),
                 (r-172,y+10,r-12,y+42)]
    marks = {"threshold": threshold, "reference": [*threshold, (x+10,y+9,x+92,y+40)]}
    for (px, cy), p, title, key in zip(points, LOOKS, ("첫 확인", "중간 확인", "최종 확인"), ("first", "middle", "last")):
        color = B if p < ALPHA else A
        board.draw.ellipse((px-7, cy-7, px+7, cy+7), fill=color, outline=WHITE)
        dy, anchor = (14, "mt") if key == "middle" else (-14, "mb")
        board.text(px, cy+dy, f"{p:.2f}", 29, color, True, anchor)
        board.text(px, base+14, title, 21, INK, True, "mt")
        marks[key] = [(px-31, cy-50 if key != "middle" else cy-9, px+31, cy+47 if key == "middle" else cy+9),
                      (px-50, base+9, px+50, base+42)]
    return marks


def decision(board, x, y, r, bottom):
    marks = {"reference": []}
    cx = (x+r)//2
    for i, (key, title, limit, result, color, max_value) in enumerate((
            ("gain", "가입률 개선", TARGET, (CI[0], 3, CI[1]), A, 6),
            ("safety", "결제 오류 증가", ERROR_LIMIT, ERROR_RESULT, B, 1.8))):
        if board.vertical:
            left, right = x+27, r-28
            top = y+18+i*192
        else:
            left, right = x+30+i*(cx-x), cx-30+i*(cx-x)
            top = y+32
        mid = (left+right)//2
        low, point, high = result
        board.text(mid, top, title, 24, INK, True, "mt")
        board.text(mid, top+33, f"{point:+g}%포인트", 37, color, True, "mt")
        base = top+(151 if board.vertical else 159)
        max_tick = int(max_value) if max_value > 2 else 1.5
        unit = "" if board.vertical and i == 0 else "%포인트"
        scale = axis(board, left, right, base, (0,max_value), (0,max_tick), unit)
        cut = scale(limit)
        dashed(board, cut, top+91, top+121, ORANGE)
        label = "허용" if key == "safety" else "기준"
        board.text(cut, top+91, f"{label} +{limit:g}", 22, ORANGE, True, "mb")
        line_mark(board, scale, top+109, low, high, color, point)
        for edge in (low, high):
            board.text(scale(edge), top+124, f"{edge:+g}", 22, color, True, "mt")
        marks[key] = [(left-8, top-2, right+8, top+70),
                      (scale(low)-20, top+100, scale(high)+21, top+152)]
        threshold = [(cut-57, top+67, cut+57, top+94), (cut-4, top+94, cut+4, base)]
        marks[key+"_limit"] = [*threshold, *marks[key]]
        marks["reference"].extend([*threshold, (left-10,base-3,right+12,base+58)])
    return marks
