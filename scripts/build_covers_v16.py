"""Render three original, editable v16 SVG cover proposals and verify bounds."""
from pathlib import Path
import base64
import json
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'e-book/design/v16/covers'
OUT.mkdir(parents=True, exist_ok=True)
INK, TEAL, MUTED, PAPER = '#142D32', '#125E59', '#4F625F', '#F5F1E8'
LIGHT, PEACH, RUST = '#E3EEE8', '#FAE9DD', '#8D4029'
FONT = Path('C:/Windows/Fonts/NotoSansKR-VF.ttf')

def text(x, y, value, size=26, weight=500, fill=INK, extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" {extra}>{value}</text>'

def line(x1,y1,x2,y2,color=INK,width=2):
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'

def title(x, y, size=92, gap=116):
    return ''.join(text(x,y+i*gap,s,size,800) for i,s in enumerate(['그래서,','이 캠페인','계속할까요?']))

def footer(x=66):
    return text(x,1204,'허재혁 지음',26,650) + text(834,1204,'저자 검토본 0.16',20,500,MUTED,'text-anchor="end"')

def wrap(body, name, desc, bg=PAPER):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1280" viewBox="0 0 900 1280" role="img" aria-labelledby="title desc" font-family="ReaderSans,Noto Sans KR,sans-serif"><title id="title">{name}</title><desc id="desc">{desc}</desc><rect width="900" height="1280" fill="{bg}"/>{body}</svg>'''

# A: the title itself is the question in a speech balloon; A/B are abstract alternatives.
a = text(66,88,'CRM A/B 테스트 실무서',25,600)
a += f'<path d="M96 140 H804 Q842 140 842 178 V539 Q842 577 804 577 H258 L180 638 L190 577 H96 Q58 577 58 539 V178 Q58 140 96 140 Z" fill="{PEACH}"/>'
a += title(95,260,91,115)
a += text(70,708,'숫자에서 고객과 실행의 판단까지',30,650)
a += f'<circle cx="340" cy="908" r="149" fill="{LIGHT}" stroke="{TEAL}" stroke-width="3"/><circle cx="559" cy="908" r="149" fill="{PAPER}" stroke="{TEAL}" stroke-width="3"/>'
a += text(305,949,'A',110,650,TEAL) + text(526,949,'B',110,650,TEAL)
a += text(70,1123,'TRI-V',26,750,TEAL) + text(178,1123,'판단을 위한 저자의 방법론',24,500,MUTED)
a += footer()

# B: one question opens into three orderly routes, meeting at a next-action station.
b = text(66,88,'CRM A/B 테스트 실무서',25,600)
b += line(66,120,834,120,TEAL,2)
b += title(65,247,96,119)
b += text(70,568,'숫자에서 고객과 실행의 판단까지',30,550)
b += text(70,655,'TRI-V',31,750,TEAL) + text(188,655,'판단을 위한 세 갈래의 길',25,500,MUTED)
b += f'<path d="M89 713 V1013 M89 737 H159 M89 871 H159 M89 1005 H159" fill="none" stroke="{TEAL}" stroke-width="5" stroke-linecap="round"/>'
for y,label,note in [(737,'정화','무엇을 비교할 수 있는가'),(871,'해체와 입체화','누구에게 어떤 차이인가'),(1005,'언어의 전환','그래서 무엇을 할 것인가')]:
    b += f'<path d="M161 {y} H724 Q780 {y} 780 1062" fill="none" stroke="{TEAL}" stroke-width="5" stroke-linecap="round"/>'
    b += f'<circle cx="161" cy="{y}" r="10" fill="{PAPER}" stroke="{TEAL}" stroke-width="4"/>'
    b += text(190,y-22,label,31,750) + text(190,y+42,note,24,500,MUTED)
b += f'<rect x="639" y="1084" width="194" height="57" rx="28" fill="{TEAL}"/>'
b += text(736,1123,'다음 실행',26,650,PAPER,'text-anchor="middle"')
b += f'<path d="M780 1062 V1084" stroke="{TEAL}" stroke-width="5"/>'
b += footer()

# C: an active editorial notebook, using margins, underlining and one folded sheet.
c = f'<rect x="34" y="49" width="832" height="1124" rx="8" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
c += line(95,72,95,1153,RUST,2)
for y in range(130,1100,110):
    c += f'<path d="M22 {y} C8 {y-18} 8 {y-32} 34 {y-32} H54" fill="none" stroke="{TEAL}" stroke-width="5" stroke-linecap="round"/>'
c += text(128,116,'CRM A/B 테스트 실무서',25,600)
c += text(128,188,'캠페인 옆에 두는 판단 노트',23,650,RUST)
c += title(124,311,88,114)
c += f'<path d="M127 560 Q421 543 779 560" fill="none" stroke="{RUST}" stroke-width="9" stroke-linecap="round"/>'
c += text(130,624,'숫자에서 고객과',30,550) + text(130,668,'실행의 판단까지',30,550)
c += text(130,759,'TRI-V',31,800,TEAL) + text(249,759,'저자의 방법론',25,500,MUTED)
c += line(130,791,792,791,MUTED,1)
c += text(130,842,'정화',31,750) + text(375,842,'비교의 조건을 살피고',25,500,MUTED)
c += text(130,917,'해체와 입체화',31,750) + text(375,917,'고객의 차이를 읽고',25,500,MUTED)
c += text(130,992,'언어의 전환',31,750) + text(375,992,'실행의 말로 바꾼다',25,500,MUTED)
# No empty sticky-note ornament: the notebook outline already conveys the metaphor.
c += text(140,1102,'질문을 남기고, 판단을 기록하다',25,650,TEAL)
c += footer(68)

covers = {
 'A':wrap(a,'그래서, 이 캠페인 계속할까요? — 대화형 표지안','친근한 질문 말풍선과 겹치는 A/B 원. 원의 크기와 겹침은 데이터가 아닌 비교의 개념 표현이다.'),
 'B':wrap(b,'그래서, 이 캠페인 계속할까요? — 경로지도형 표지안','정화, 해체와 입체화, 언어의 전환의 세 경로가 다음 실행으로 모이는 개념 지도. 실측 그래프가 아니다.'),
 'C':wrap(c,'그래서, 이 캠페인 계속할까요? — 편집노트형 표지안','밑줄과 제본선, 노트의 짜임이 판단과 기록이라는 독서 경험을 전한다.',PEACH)
}
font_data = base64.b64encode(FONT.read_bytes()).decode('ascii')
style = f'@font-face{{font-family:ReaderSans;src:url(data:font/ttf;base64,{font_data}) format("truetype");font-weight:100 900}}html,body{{margin:0;width:900px;height:1280px;overflow:hidden}}svg{{display:block}}'
checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    for key,svg in covers.items():
        ET.fromstring(svg)
        (OUT/f'cover_{key}.svg').write_text(svg,encoding='utf-8')
        page=browser.new_page(viewport={'width':900,'height':1280},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.set_content(f'<!doctype html><html lang="ko"><meta charset="utf-8"><style>{style}</style>{svg}</html>')
        page.evaluate('document.fonts.ready')
        assert page.evaluate('document.fonts.check("800 90px ReaderSans")')
        bounds=page.evaluate('''() => [...document.querySelectorAll('svg text')].map(el => {const b=el.getBBox();return {text:el.textContent,x:b.x,y:b.y,width:b.width,height:b.height,clipped:b.x<0||b.y<0||b.x+b.width>900||b.y+b.height>1280}})''')
        assert not any(v['clipped'] for v in bounds),bounds
        assert not errors,errors
        page.screenshot(path=str(OUT/f'cover_{key}.png'))
        checks.append({'cover':key,'text_bounds':bounds,'clipped_texts':0,'page_errors':errors,'font_loaded':True})
        page.close()
    browser.close()

sheet=Image.new('RGB',(1560,900),PAPER)
draw=ImageDraw.Draw(sheet)
label_font=ImageFont.truetype(str(FONT),25)
small=ImageFont.truetype(str(FONT),18)
for i,(key,label) in enumerate([('A','대화형 질문'),('B','세 갈래 경로지도'),('C','편집노트')]):
    x=30+i*515
    draw.text((x,23),f'{key}  {label}',font=label_font,fill=INK)
    im=Image.open(OUT/f'cover_{key}.png').convert('RGB')
    assert im.size==(900,1280)
    sheet.paste(im.resize((480,683),Image.Resampling.LANCZOS),(x,74))
    draw.text((x,783),{'A':'추천: 첫인상과 질문의 친근함','B':'방법론의 세 축을 가장 명확하게','C':'기록하며 읽는 실무서의 활기'}[key],font=small,fill=INK)
draw.text((30,853),'표지 3안 비교  |  가제 유지  |  최종 표지 확정은 사람 승인 대기',font=small,fill=MUTED)
sheet.save(OUT/'covers_comparison.png')
assert len(list(OUT.glob('cover_?.svg')))==3
assert len(list(OUT.glob('cover_?.png')))==3
recommendations={
 'version':'0.16','author':'허재혁','working_title':'그래서, 이 캠페인 계속할까요?',
 'recommended':'A','recommended_svg':'cover_A.svg','approval_status':'pending_human_approval',
 'title_status':'working_title_not_final','summary_lines':[
 'A 추천: 제목을 질문 말풍선에 넣어 친근하게 시작하고, A/B 원으로 비교의 주제를 전한다.',
 'B: 세 축의 경로를 다음 실행으로 연결해 TRI-V 방법론의 구조를 가장 명료하게 보여 준다.',
 'C: 밑줄과 제본 노트로 실무 기록의 활기를 살리며, 최종 표지 확정은 사람 승인 대기다.'
 ],
 'existing_cover_critique':'제목은 선명하지만 직선 분기도와 넓은 중간 공백이 기술 문서의 인상을 만든다. 새 안은 제목 위계를 유지하면서 대화, 경로, 노트로 독서 진입점을 다르게 제시한다.',
 'source_palette_measurement':{'tool':'mira_palette_extract','source':'e-book/design/v15/review/page_001.png','size':[701,995],'dominant':[{'hex':'#F5F1E7','share':0.88},{'hex':'#FDF8ED','share':0.02},{'hex':'#082429','share':0.015}], 'note':'이미지 실측값은 안티앨리어싱 등으로 CSS 원색과 다를 수 있다.'},
 'source_css':{'ink':INK,'teal':TEAL,'muted':MUTED,'paper':PAPER},
 'proposed_extensions':{'light':LIGHT,'peach':PEACH,'attention':RUST},
 'palette_status':'proposal_not_corporate_brand_fact',
 'methodology':'TRI-V는 저자의 방법론. 정화 → 해체와 입체화 → 언어의 전환.',
 'graphics':'Conceptual non-data graphics. No effect sizes, performance claims, guarantees or winner symbols.',
 'font_policy':'Authoritative SVG uses ReaderSans,Noto Sans KR,sans-serif with explicit weights. Chrome PNGs use local NotoSansKR-VF.ttf via in-memory @font-face. Final document font subsetting is handled by parent build.',
 'verification':{'svg_count':3,'png_count':3,'canvas':[900,1280],'clipping':'All SVG text getBBox bounds inside viewport; visual review required as well.','checks':checks},
 'style_audit':{'score':0,'scope':'Narrow template/slop heuristic, not publication readiness.'}
}
(OUT/'recommendations.json').write_text(json.dumps(recommendations,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'output':str(OUT),'svg_count':3,'cover_png_count':3,'comparison':str(OUT/'covers_comparison.png'),'clipped_texts':sum(x['clipped_texts'] for x in checks),'recommended':'A','approval':'pending_human_approval'},ensure_ascii=False))
