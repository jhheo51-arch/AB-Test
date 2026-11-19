"""Build only the four v16 conceptual illustrations and their verification files."""
from pathlib import Path
import base64
import html
import json
import re
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'e-book/design/v16/illustrations'
FONT = ROOT / 'e-book/exports/v15/assets/reader-sans.woff2'
INK, TEAL, MUTED = '#142D32', '#125E59', '#4F625F'
WHITE, CREAM, GREEN, PEACH, WARN = '#FFFFFF', '#F5F1E8', '#E3EEE8', '#FAE9DD', '#8D4029'
FAMILY = 'ReaderSans,Noto Sans KR,sans-serif'
FORBIDDEN = '\u00b7\u0387\u2022\u2027\u2219\u22c5\u30fb\uff65'

class Figure:
    def __init__(self, name, height, title, desc):
        self.name, self.height, self.title, self.desc = name, height, title, desc
        self.parts, self.edges = [], []
    def box(self, x, y, w, h, color=GREEN):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{color}" stroke="{TEAL}" stroke-width="2"/>')
    def text(self, x, y, text, size=28, weight=400, color=INK, region=None):
        region_attr = f' data-region="{html.escape(json.dumps(region))}"' if region else ''
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}"{region_attr}>{html.escape(text)}</text>')
    def arrow(self, path, source, target, kind='forward'):
        self.edges.append({'from': source, 'to': target, 'kind': kind, 'path': path})
        dash = ' stroke-dasharray="8 7"' if kind == 'return' else ''
        self.parts.append(f'<path d="{path}" fill="none" stroke="{TEAL}" stroke-width="3" marker-end="url(#{self.name}-arrow)"{dash}/>')
    def header(self, title):
        self.text(36, 44, title, 36, 700)
        self.text(36, 82, '개념 설명 | 실제 고객이나 성과 데이터가 아님', 28, color=MUTED)
    def write(self):
        fid = self.name
        data = base64.b64encode(FONT.read_bytes()).decode()
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{fid}-title {fid}-desc" viewBox="0 0 900 {self.height}" width="900" height="{self.height}">
<title id="{fid}-title">{html.escape(self.title)}</title><desc id="{fid}-desc">{html.escape(self.desc)} 모든 도형과 태그는 개념 설명이며 실제 관측 데이터가 아니다.</desc>
<defs><style>@font-face{{font-family:ReaderSans;src:url(data:font/woff2;base64,{data}) format('woff2');font-weight:100 900}}text{{font-family:{FAMILY}}}</style><marker id="{fid}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="{TEAL}"/></marker></defs>
<rect width="900" height="{self.height}" fill="{WHITE}"/>
<g font-family="{FAMILY}">{''.join(self.parts)}</g></svg>'''
        assert not any(c in svg for c in FORBIDDEN)
        ET.fromstring(svg)
        path = OUT / f'{fid}.svg'
        path.write_text(svg, encoding='utf-8')
        return path

def workflow():
    f = Figure('tri_v_workflow_v16', 1050, 'TRI-V 실제 판단 흐름', '비교와 가능한 선택부터 정하고 V1의 비교 근거와 측정 상태, V2의 적용 범위, V3의 성과와 사업 및 보호 상태를 나누어 검토한다. 근거가 달라지면 필요한 질문으로 돌아간다. 정보 부족이 모든 선택의 자동 보류를 뜻하지는 않는다.')
    f.header('비교에서 현재 선택까지')
    f.box(100, 104, 764, 84, CREAM)
    f.text(122, 143, '무엇을 비교하고 무엇을 선택할까?', 32, 700)
    f.text(122, 174, '전환, 범위가 정해진 적용, 현행 유지, 새 검증')
    f.arrow('M480 188V212', 'comparison_and_options', 'V1')
    f.box(100, 218, 764, 174)
    f.text(122, 255, 'V1 정화 | Purification / Variable Control', 28, 700)
    f.text(122, 295, '비교 근거와 측정 상태를 먼저 확인한다', 30, 700)
    f.text(122, 334, '해석 가능 / 일부 지표 제한 / 비교 보류')
    f.text(122, 374, '측정과 추론을 구분하고 의존하는 주장만 제한')
    f.arrow('M480 392V416', 'V1', 'V2')
    f.box(100, 422, 764, 164)
    f.text(122, 457, 'V2 해체와 입체화 | Prism', 28, 700)
    f.text(122, 492, 'Vector Segmentation', 28, 700)
    f.text(122, 531, '기본은 현재 전체 범위의 적용 근거 확인', 30, 700)
    f.text(122, 570, '선택에 중요할 때만 세분화와 대상 차이 검토')
    f.arrow('M480 586V610', 'V2', 'V3')
    f.box(100, 616, 764, 156, PEACH)
    f.text(122, 650, 'V3 언어의 전환 | Translation', 28, 700)
    f.text(122, 685, 'Value-Linked Decision', 28, 700)
    f.text(122, 724, '성과 판단 / 사업 조건 / 보호 상태를 나눈다', 30, 700)
    f.text(122, 758, '부족한 근거가 있는 질문으로 돌아간다')
    f.arrow('M100 710H54V308H96', 'V3', 'V1', 'return')
    f.arrow('M54 504H96', 'V3', 'V2', 'return')
    f.arrow('M480 772V793', 'V3', 'current_choice')
    for x,y,label in [(100,800,'실행 후보 또는 조건부 후보'),(490,800,'추가 확인'),(100,852,'미확대'),(490,852,'보호 대응 또는 운영 중단')]:
        f.box(x,y,374,44,CREAM)
        f.text(x+16,y+32,label,28,700)
    f.text(100, 935, '실행 후보 ≠ 실제 승인', 30, 700, WARN)
    f.text(100, 977, '추가 분석 종료 ≠ 통계적 실험 종료', 28, 700, WARN)
    f.text(100, 1019, '통계적 실험 종료 ≠ 보호 운영 중단', 28, 700, WARN)
    return f

def judgments():
    f=Figure('three_judgments_v16',660,'같은 결과를 읽는 서로 다른 문장','관측은 기록에서 본 차이를, 추론은 설계와 불확실성 아래 말할 수 있는 효과를, 사업과 보호 선택은 실행 조건과 책임을 표현한다. TRI-V에 새로운 세 축을 추가한 그림이 아니다.')
    f.header('본 것과 말할 수 있는 것, 선택할 것')
    items=[(120,'관측 문장','기록에서 본 차이를 말한다','“배정 고객의 시승 완료를 비교했다.”',GREEN), (284,'추론 문장','설계와 불확실성 아래 효과를 말한다','“어디까지 효과라고 말할 수 있을까?”',CREAM),(448,'사업과 보호 선택 문장','비용, 용량, 동의와 안전을 따로 본다','“어떤 범위와 조건으로 선택할까?”',PEACH)]
    for y,title,sub,quote,bg in items:
        f.box(40,y,820,138,bg)
        f.text(66,y+38,title,32,700)
        f.text(66,y+79,sub,30)
        f.text(66,y+118,quote,28,color=TEAL)
    f.arrow('M450 258V279','observation','inference')
    f.arrow('M450 422V443','inference','business_and_protection_choice')
    f.text(40,633,'서로 대신할 수 없는 문장 | 실행 후보는 승인이 아님',28,700,WARN)
    return f

def maturity():
    f=Figure('observation_maturity_v16',650,'모집 중지와 관측 창의 성숙','시간축에서 앞서 배정된 고객과 늦게 배정된 고객의 같은 길이 관측 창을 보여준다. 모집이 멈춰도 늦게 배정된 고객의 관측은 계속된다. 선의 위치와 길이는 개념 설명이며 날짜나 실제 기간이 아니다.')
    f.header('모집을 멈춰도 관측은 이어진다')
    f.arrow('M75 146H834','earlier_time','later_time')
    f.text(76,129,'시간의 흐름',28,700)
    f.parts.append(f'<path d="M540 163V464" fill="none" stroke="{TEAL}" stroke-width="3" stroke-dasharray="8 8"/>')
    f.box(560,172,290,56,PEACH)
    f.text(580,210,'모집 중지 시점',30,700)
    for y,start,end,label in [(280,90,450,'먼저 배정된 고객'),(400,360,720,'늦게 배정된 고객')]:
        f.text(76,y-29,label,30,700)
        f.box(start,y,end-start,52,GREEN)
        f.text(start+22,y+36,'같은 길이의 관측 창',28)
        f.parts.append(f'<circle cx="{start}" cy="{y+26}" r="7" fill="{TEAL}"/><circle cx="{end}" cy="{y+26}" r="7" fill="{TEAL}"/>')
        f.text(end+18,y+36,'성숙',28,700)
    f.box(40,498,820,118,CREAM)
    f.text(64,536,'늦게 들어온 고객도 정한 관측 기회를 채운다',30,700)
    f.text(64,573,'아직 미성숙한 상태를 미완료로 확정하지 않는다',28)
    f.text(64,606,'모집 중지와 통계적 종료, 보호 대응은 별도 판단',28,700,WARN)
    return f

def record():
    f=Figure('decision_record_v16',840,'기존 여섯 칸 기록의 연결','같은 실험 식별자 아래 지금 결정할 것, V1 근거와 제한, V2 적용 대상, V3 현재 선택과 승인 상태, 추가 확인 또는 생략, 다시 검토할 조건을 연결한다. 새 양식이나 일곱 번째 칸이 아니다.')
    f.header('기존 여섯 칸으로 판단을 잇는다')
    cells=[('지금 결정할 것','가능한 선택과 범위'),('V1 믿고 쓸 근거와 제한','결과 위치와 제한할 주장'),('V2 적용 대상','같은 대상인지, 다른 근거인지'),('V3 현재 선택','선택과 실제 승인 상태 구분'),('추가 확인 또는 생략','행동을 바꿀 질문과 책임'),('다시 검토할 조건','관측이나 가정이 바뀌는 때')]
    for i,(title,sub) in enumerate(cells):
        y=116+i*104
        f.box(92,y,756,84,GREEN if i<3 else CREAM)
        f.text(116,y+35,title,30,700)
        f.text(116,y+69,sub,28)
        if i<5:
            f.arrow(f'M470 {y+84}V{y+101}',str(i+1),str(i+2))
    f.arrow('M92 678H46V157H88','6','1','return')
    f.text(92,777,'같은 실험 식별자로 기존 계획과 결과를 참조',28,700)
    f.text(92,818,'여섯 칸의 연결 설명이며 새 작성 양식이 아님',28,color=MUTED)
    return f

PLACEMENTS=[
 {'file':'tri_v_workflow_v16.svg','anchor':'1장 TRI-V 공통 운용 기준, 여섯 항목 표 직전','why':'선택부터 출발하는 최소 경로와 되돌아갈 질문을 먼저 보여줘 모든 심화 분석을 자동 요구하는 오독을 막는다.','replace_recommendation':'기존 tri_v_method.svg를 대체하고 인접한 세 단계 설명 그림과 중복 삽입하지 않는다.','source_lines':'89-118'},
 {'file':'three_judgments_v16.svg','anchor':'4장 통계적 우위와 실행 선택은 서로 다른 기록이라는 문단 뒤','why':'관측한 기록, 추론 가능한 효과, 사업과 보호 선택을 다른 문장으로 읽게 한다. 새 축을 더하지 않는다.','replace_recommendation':'독립적으로 삽입하되 같은 내용을 반복하는 개념 카드가 있으면 그 카드를 대체한다. winner_effect.svg와 guardrail_effect.svg의 정량 사례를 대체하지 않는다.','source_lines':'178-197'},
 {'file':'observation_maturity_v16.svg','anchor':'2장 개인별 관측 기간 설명 뒤, 또는 6장 등록 종료일과 최종 결과 확정일 설명 뒤 중 한 곳만','why':'모집을 멈춘 달력 시점과 개인별 결과가 성숙하는 시점의 차이를 한눈에 보여준다.','replace_recommendation':'본문의 기간 개념 그림이 있으면 대체한다. 같은 그림을 두 장에 반복하지 않는다.','source_lines':'146,300-304,324-326'},
 {'file':'decision_record_v16.svg','anchor':'1장 공통 운용 기준의 기존 여섯 항목 표 뒤 또는 8장 결정 기록 도입 중 한 곳만','why':'기존 자료를 참조하며 선택에서 재검토까지 연결함을 설명한다. 입력 칸을 늘리지 않는다.','replace_recommendation':'기존 여섯 칸 표와 작성용 양식은 유지한다. 별도의 기록 연결 그림이 있다면 그 그림만 대체한다.','source_lines':'93-102'}]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figures=[workflow(),judgments(),maturity(),record()]
    paths=[f.write() for f in figures]
    assert len(paths)==4 and len(set(p.name for p in paths))==4
    manifest={'kind':'conceptual_illustrations_not_data','source':'e-book/exports/v15/ebook_review_v15.md','source_read_scope':'방법론 1-4장과 공통 기준, 관측 성숙 관련 6장','author':'허재혁','print_width_mm':156,'svg_width_units':900,'font_family':FAMILY,'minimum_font_size_px':28,'minimum_print_pt':28*156/900*72/25.4,'scale_calculation':'SVG font units * (156 mm / 900 units) * (72 pt / 25.4 mm). 28 px = 13.7575 pt; 25 px = 12.2835 pt. No downstream shrink below the stated 156 mm width.','render_engine':'Playwright Chromium, actual screenshot at device_scale_factor=2','new_colors_are_illustration_surfaces_only':True,'figures':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':900,'height':1100},device_scale_factor=2)
        for f,path in zip(figures,paths):
            page.goto(path.as_uri())
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(100)
            report=page.evaluate('''() => {const s=document.querySelector('svg'), v=s.viewBox.baseVal; const t=[...s.querySelectorAll('text')].map(e=>{const b=e.getBBox();return {text:e.textContent,x:b.x,y:b.y,width:b.width,height:b.height,size:parseFloat(getComputedStyle(e).fontSize)}}); return {fontLoaded:document.fonts.check('28px ReaderSans'),textCount:t.length,minFont:Math.min(...t.map(x=>x.size)),overflow:t.filter(b=>b.x<0||b.y<0||b.x+b.width>v.width||b.y+b.height>v.height),textBounds:t};}''')
            detail=page.evaluate('''() => { const texts=[...document.querySelectorAll('text')].map(e=>({text:e.textContent,b:e.getBBox()})); const boxes=[...document.querySelectorAll('rect[rx]')].map(e=>e.getBBox()); const panelOverflow=[]; const overlaps=[]; for (let i=0;i<texts.length;i++){ const a=texts[i].b; const center={x:a.x+a.width/2,y:a.y+a.height/2}; const container=boxes.find(b=>center.x>=b.x&&center.x<=b.x+b.width&&center.y>=b.y&&center.y<=b.y+b.height); if(container&&(a.x<container.x||a.x+a.width>container.x+container.width||a.y<container.y||a.y+a.height>container.y+container.height)) panelOverflow.push(texts[i].text); for(let j=i+1;j<texts.length;j++){const b=texts[j].b; if(Math.min(a.x+a.width,b.x+b.width)>Math.max(a.x,b.x)&&Math.min(a.y+a.height,b.y+b.height)>Math.max(a.y,b.y))overlaps.push([texts[i].text,texts[j].text]);}} return {panelOverflow,textOverlaps:overlaps}; }''')
            report.update(detail)
            assert not report['panelOverflow'], report['panelOverflow']
            report['line_metric_bbox_intersections'] = report.pop('textOverlaps')
            report['line_metric_note'] = 'SVG font metric boxes include unused ascent and descent; intersections are not painted glyph overlap. All four PNGs also require visual inspection.'
            assert report['fontLoaded']
            assert not report['overflow'], report['overflow']
            assert report['minFont']>=28
            png=OUT / f'{f.name}.png'
            page.locator('svg').screenshot(path=str(png))
            from PIL import Image
            with Image.open(png) as im: actual=list(im.size)
            manifest['figures'].append({'svg':path.name,'png':png.name,'viewBox':[0,0,900,f.height],'actual_png_size':actual,'svg_bytes':path.stat().st_size,'png_bytes':png.stat().st_size,'minimum_font_size_px':report['minFont'],'flowedges':f.edges,'verification':report})
        browser.close()
    manifest['verified_figure_count']=len(manifest['figures'])
    manifest['checks']={'all_four_rendered':len(manifest['figures'])==4,'all_fonts_loaded':all(x['verification']['fontLoaded'] for x in manifest['figures']),'canvas_text_overflow':sum(len(x['verification']['overflow']) for x in manifest['figures']),'middle_dot_characters':0,'svg_xml_valid':True,'workflow_height_at_most_1050':figures[0].height<=1050,'no_book_or_color_token_files_modified_by_script':True}
    (OUT/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'PLACEMENT.json').write_text(json.dumps({'status':'insertion_recommendations_only_parent_handles_insertion','placements':PLACEMENTS},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(OUT),'count':len(figures),'checks':manifest['checks'],'minimum_print_pt':manifest['minimum_print_pt']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
