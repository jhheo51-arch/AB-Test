from render import A,A_PALE,B,B_PALE,INK,LINE,MUTED,ORANGE,WHITE,Board,compose,font

def rate(part,total):
    return f"{part*100/total:g}%"

def fields(title, value, note):
    return title,value,note

# The synthetic assignment example uses the same response to either screen.
regular=(12,20)
new=(4,20)
mixed=(regular[0]//2+new[0]//2,(regular[1]+new[1])//2)
n=100
a,b=10,13
a_rate,b_rate=rate(a,n),rate(b,n)
points=(b-a)*100//n
relative=(b-a)*100//a

EPISODES=[
    ("ep02-short",("A/B 테스트는 왜","무작위로 나눌까?"),[
        ("A","두 화면의 가입률이 크게 달랐어요. 화면 때문일까요?",
         "가입률이 왜 다를까?",
         [fields("A에 배정","단골만","가입할 가능성이 높은 방문자"),
          fields("B에 배정","신규만","처음 방문한 사람")]),
        ("해설","가상 예제입니다. 어떤 화면을 봐도 단골은 스무 명 중 열두 명, 신규는 네 명이 가입해요.",
         "화면 효과가 없다고 가정",
         [fields("단골","12 / 20","가입 완료"),fields("신규","4 / 20","가입 완료")]),
        ("해설",f"단골을 전부 A에, 신규를 전부 B에 넣으면 {rate(*regular)}와 {rate(*new)}가 나옵니다.",
         "방문자가 한쪽으로 쏠리면",
         [fields("A (단골 20명)",rate(*regular),"12명 가입"),fields("B (신규 20명)",rate(*new),"4명 가입")]),
        ("B","같은 방문자를 무작위로 나눠 봅시다. 예를 들어 두 그룹에 단골과 신규가 열 명씩 들어갔어요.",
         "가능한 무작위 배정 한 가지",
         [fields("A","단골 10명","신규 10명"),fields("B","단골 10명","신규 10명")]),
        ("해설",f"이 배정에서는 두 그룹 모두 스무 명 중 여덟 명이 가입해서 {rate(*mixed)}입니다.",
         "두 그룹에 같은 구성",
         [fields("A",rate(*mixed),"20명 중 8명 가입"),fields("B",rate(*mixed),"20명 중 8명 가입")]),
        ("A","무작위 배정은 치우침을 줄이지만, 작은 실험에서는 우연한 불균형이 남을 수 있어요.",
         "비교할 두 그룹을 만드는 법",
         [fields("실험 설계","무작위 배정","방문자 특성이 체계적으로 한쪽에 몰리는 것을 줄여요")]),
    ]),
    ("ep03-short",("10%에서 13%,","3%포인트일까 30%일까?"),[
        ("B",f"A가 {a_rate}, B가 {b_rate}라면, 얼마나 높아진 걸까요?",
         "같은 결과를 두 방식으로 읽기",
         [fields("기존 화면 A",a_rate,"100명 중 10명"),fields("새 화면 B",b_rate,"100명 중 13명")]),
        ("해설",f"두 전환율을 빼면 차이가 나옵니다. {b_rate}에서 {a_rate}를 빼면 {points}%포인트입니다.",
         "방법 1 | 전환율끼리 빼기",
         [fields(f"{b_rate} - {a_rate}",f"+{points}%포인트","전환율의 절대 차이")]),
        ("A","그 차이가 A의 전환율에 비해 얼마나 큰지도 계산할 수 있어요.",
         "방법 2 | A를 기준으로 비교",
         [fields("기준이 되는 값",a_rate,"A의 전환율"),fields("늘어난 폭",f"{points}%포인트","B의 전환율에서 A를 뺀 값")]),
        ("해설",f"차이인 {points}%포인트를 기존 전환율 {a_rate}로 나누면 상대적으로 {relative}% 높아요.",
         "늘어난 폭을 기준값으로 나누기",
         [fields(f"{points}%포인트 ÷ {a_rate}",f"+{relative}%","A의 전환율 대비 상대 차이")]),
        ("B",f"둘 다 같은 결과예요. 무엇을 기준으로 계산했는지 말해 주면 읽는 사람이 바로 이해할 수 있죠.",
         "두 표현을 같이 적으면",
         [fields("두 전환율의 차이",f"+{points}%포인트","B의 전환율 - A의 전환율"),
          fields("A를 기준으로 본 차이",f"+{relative}%","A 대비 B의 전환율")]),
    ])
]

def heading(board, text, x, y, limit, size, fill=INK, anchor="lt"):
    while board.draw.textlength(text,font=font(size,True))>limit:
        size-=1
    board.text(x,y,text,size,fill,True,anchor)

def cover(title):
    board=Board(True)
    board.text(board.center,176,"A/B 실험노트",22,ORANGE,True,"mt")
    for row,text in enumerate(title):
        heading(board,text,board.center,233+65*row,board.right-board.left-18,49,anchor="mt")
    for x,letter,color,fill in [(139,"A",A,A_PALE),(357,"B",B,B_PALE)]:
        board.draw.ellipse((x-81,427,x+81,589),fill=fill,outline=color,width=2)
        board.put_mascot(x,508,letter,105)
    board.text(board.center,667,"교육용 가상 데이터",18,MUTED,False,"mt")
    return compose(board)

def visuals(board, heading_text, conditions):
    heading(board,heading_text,board.left,132,board.right-board.left,40)
    board.text(board.left,215,"교육용 가상 데이터",15,MUTED)
    x,r=board.left,board.right
    if len(conditions)==1:
        y,d=270,656
        label,main,foot=conditions[0]
        board.box(x,y,r,d,WHITE,12,LINE)
        heading(board,label,board.center,y+67,r-x-24,29,MUTED,"mt")
        heading(board,main,board.center,y+130,r-x-26,60,ORANGE,"mt")
        heading(board,foot,board.center,y+241,r-x-26,22,MUTED,"mt")
        return
    for i,(label,main,foot) in enumerate(conditions):
        y=251+220*i
        fill,color=(A_PALE,A) if i==0 else (B_PALE,B)
        board.box(x,y,r,y+197,fill,12,LINE)
        heading(board,label,x+19,y+16,r-x-35,24,color)
        heading(board,main,board.center,y+62,r-x-30,54,color,"mt")
        heading(board,foot,board.center,y+142,r-x-30,21,MUTED,"mt")
