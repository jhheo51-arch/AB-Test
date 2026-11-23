"""Version-free UI and embedded-help regression, using synthetic inputs only.

Run explicitly against a server you started yourself:
    python tests/verify_current_interface.py --url http://127.0.0.1:PORT
Install Playwright and Chromium first, or pass --browser-path /path/to/chrome.
No server is started and no model request is made. Read-only local /api/status is allowed. Evidence is written only on
an explicit --url run. A failed run records completed checks and its failure.
"""
from pathlib import Path
import argparse
import json
import re
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LABEL_VERSION = re.compile(
    r"\bv\s*\d+(?:\.\d+)*|로컬\s*작업실\s*v|엔진\s*(?:버전\s*)?\d+\.\d+"
    r"|engine\s*(?:version\s*)?\d+\.\d+|계획\s*[·/]\s*입력\s*v\d+",
    re.IGNORECASE,
)
RAW = (
    "variant,converted,participants,usernotes\n"
    "control,10,100,SYNTHETIC_USERNOTE_CONTROL\n"
    "treatment,20,100,SYNTHETIC_USERNOTE_TREATMENT"
)
SNAPSHOT = """() => ({
    state: JSON.stringify(state),
    forms: [...document.querySelectorAll('input,textarea,select')]
      .filter(e => !e.closest('#demo-dialog') && e.type !== 'file')
      .map(e => ({id:e.id,value:e.value,checked:e.checked,disabled:e.disabled})),
    text: Object.fromEntries(['input-view','results-view','share-view',
      'mapping-error','prepare-state','source-badge','revision','engine-status']
      .map(id => [id,document.getElementById(id)?.textContent])),
    views: ['input-view','results-view','share-view','analysis-options','mapping-panel']
      .map(id => ({id,hidden:document.getElementById(id)?.hidden})),
    url: location.href, timeOrigin: performance.timeOrigin
})"""


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='Existing app URL; never starts a server')
    parser.add_argument('--browser-path', help='Optional Chrome/Chromium executable')
    parser.add_argument('--headed', action='store_true')
    args = parser.parse_args()
    target = urlsplit(args.url)
    if target.scheme not in ('http', 'https') or not target.hostname:
        parser.error('--url must be an explicit http(s) URL')
    if target.username or target.password:
        parser.error('Credentials in --url are not supported')
    return args


def run(args):
    # Deferred import keeps --help / missing --url side-effect free and portable.
    from playwright.sync_api import sync_playwright, expect

    checks, page_errors, blocked, metadata = [], [], [], []
    evidence = ROOT / 'evidence'
    evidence.mkdir(exist_ok=True)
    result = {'status': 'FAIL', 'url': args.url, 'checks': checks,
              'javascript_errors': page_errors, 'blocked_requests': blocked,
              'video_metadata': metadata, 'scope': 'synthetic local browser regression',
              'no_actual_llm_call': True}
    browser = page = None

    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
        if not condition:
            raise AssertionError(name)
        print('PASS', name, flush=True)

    def poll_locator(locator, expression, seconds=20):
        # Locator evaluation works under strict CSP; wait_for_function does not.
        deadline = time.monotonic() + seconds
        last = None
        while time.monotonic() < deadline:
            last = locator.evaluate(expression)
            if last:
                return last
            time.sleep(0.1)
        raise AssertionError(f'Bounded locator polling timed out: {expression}; last={last!r}')

    def snapshot():
        return page.evaluate(SNAPSHOT)

    def help_cycle(label, escape=False, mobile=False):
        before = snapshot()
        page.locator('#demo-help').click()
        dialog = page.locator('#demo-dialog')
        expect(dialog).to_be_visible()
        check(label + ': native modal is open', dialog.evaluate('e => e.open && e.matches(":modal")'))
        video = page.locator('#demo-video')
        check(label + ': local embedded video source', video.evaluate(
            'e => new URL(e.currentSrc || e.src, location.href).pathname === "/help/walkthrough.mp4"'
            ' && new URL(e.currentSrc || e.src, location.href).origin === location.origin'))
        poll_locator(video, 'e => e.readyState >= 1 && e.videoWidth > 0 && Number.isFinite(e.duration) && e.duration > 10')
        info = video.evaluate('e => ({width:e.videoWidth,height:e.videoHeight,duration:e.duration,readyState:e.readyState})')
        metadata.append({'case': label, **info})
        check(label + ': real video metadata', info['width'] > 0 and info['duration'] > 10)
        # Muted play is permitted without sending any request to an AI provider.
        video.evaluate('async e => { e.muted = true; await e.play(); }')
        check(label + ': video really starts', not video.evaluate('e => e.paused'))
        if mobile:
            check(label + ': modal fits 390px', dialog.evaluate(
                'e => { const r=e.getBoundingClientRect(); return r.left>=-1 && r.right<=innerWidth+1 && e.scrollWidth<=e.clientWidth+1; }'))
            page.screenshot(path=str(evidence / 'current_interface.png'), full_page=True)
        # Observe the native close event after the production scroll-restoration handler.
        # Keep the immediate pause assertion below: waiting first would mask a pause regression.
        dialog.evaluate('e => { e.__testCloseObserved = false; e.addEventListener("close", () => { e.__testCloseObserved = true; }, {once:true}); }')
        if escape:
            page.keyboard.press('Escape')
        else:
            page.locator('#close-demo').click()
        expect(dialog).not_to_be_visible()
        check(label + ': close pauses video', video.evaluate('e => e.paused'))
        check(label + ': exact state/input/prepared/result/consent preserved', snapshot() == before)
        if mobile:
            poll_locator(dialog, 'e => e.__testCloseObserved === true')
            check(label + ': body scrolling unlocked', page.evaluate(
                'getComputedStyle(document.body).overflow !== "hidden" && getComputedStyle(document.documentElement).overflow !== "hidden"'))
            page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
            check(label + ': page remains scrollable', page.evaluate(
                'document.documentElement.scrollHeight <= innerHeight || scrollY > 0'))

    def download_json():
        with page.expect_download() as event:
            page.locator('#save-project').click()
        return json.loads(Path(event.value.path()).read_text(encoding='utf-8-sig'))

    def analyze():
        for field in ('randomized', 'independent', 'mature', 'fixed-stop'):
            page.locator('#' + field).check()
        page.locator('#confirm-input').check()
        page.locator('#analyze').click()
        expect(page.locator('#results-view')).to_be_visible()

    def select_file(value, name):
        page.locator('#project-file').set_input_files({
            'name': name, 'mimeType': 'application/json',
            'buffer': json.dumps(value, ensure_ascii=False).encode('utf-8')})

    try:
        with sync_playwright() as pw:
            launch = {'headless': not args.headed}
            if args.browser_path:
                launch['executable_path'] = args.browser_path
            browser = pw.chromium.launch(**launch)
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
            origin = urlsplit(args.url)

            def guard(route):
                request = route.request
                target = urlsplit(request.url)
                same_origin = (target.scheme, target.hostname, target.port) == (origin.scheme, origin.hostname, origin.port)
                # Fail closed: model/credential calls and every remote origin are blocked.
                if not same_origin or request.method not in ('GET', 'HEAD') or (target.path.startswith('/api/') and target.path != '/api/status'):
                    blocked.append({'method': request.method, 'url': request.url})
                    route.abort()
                else:
                    route.continue_()

            context.route('**/*', guard)
            page = context.new_page()
            page.set_default_timeout(15000)
            page.on('pageerror', lambda error: page_errors.append(str(error)))
            page.goto(args.url, wait_until='networkidle')
            expect(page.locator('#engine-status')).not_to_contain_text('확인 중')
            check('exact version-free document title', page.title() == 'A/B 테스트 작업실')
            check('header has no visible product version', not LABEL_VERSION.search(page.locator('.app-header').inner_text())
                  and page.locator('.app-header .version:visible').count() == 0)
            check('engine status hides numeric version', not LABEL_VERSION.search(page.locator('#engine-status').inner_text())
                  and not re.search(r'\d+\.\d+(?:\.\d+)?', page.locator('#engine-status').inner_text()))
            check('revision uses input edit count', bool(re.fullmatch(r'입력 수정 \d+회', page.locator('#revision').inner_text().strip())))
            help_cycle('initial button close')
            help_cycle('initial Escape close', escape=True)

            page.locator('#purpose').fill('SYNTHETIC: embedded-help state preservation')
            page.locator('#data-text').fill(RAW)
            page.locator('#prepare').click()
            expect(page.locator('#mapping-panel')).to_be_visible()
            check('custom CSV roles default correctly', all(
                page.locator('#map-' + key).input_value() == value
                for key, value in {'arm': 'variant', 'success': 'converted', 'total': 'participants', 'segment': ''}.items()))
            page.locator('#arm-value-a').fill('control')
            page.locator('#arm-value-b').fill('treatment')
            page.locator('#mapping-confirm').check()
            page.locator('#apply-mapping').click()
            expect(page.locator('#analysis-options')).to_be_visible()
            check('mapping preserves original synthetic notes and produces correct cells',
                  page.locator('#data-text').input_value() == RAW and page.evaluate(
                      'state.prepared.cells.some(c=>c.arm==="A" && c.success===10 && c.total===100)'
                      ' && state.prepared.cells.some(c=>c.arm==="B" && c.success===20 && c.total===100)'))
            help_cycle('prepared input button close')
            analyze()
            check('confirmed conditions allow real inference', page.evaluate('state.result.inference_allowed === true'))
            page.locator('#llm-consent').check()
            help_cycle('analyzed result Escape close', escape=True)
            page.locator('nav [data-view=share]').click()
            page.locator('#decision').fill('SYNTHETIC_USERNOTE_DECISION: no real approval')
            page.locator('#share-groups').check()
            page.locator('#share-confirm').check()
            help_cycle('share with both consents button close')
            help_cycle('share with both consents Escape close', escape=True)
            saved = download_json()
            check('native project JSON retains schema 6 and engine compatibility',
                  saved['version'] == 6 and saved['format'] == 'ab-local-project'
                  and saved['engine_version'] == page.evaluate('state.result.version')
                  and bool(re.fullmatch(r'\d+\.\d+\.\d+', saved['engine_version'])))
            check('native project JSON retains transformation version',
                  bool(saved['lineage']['transformation']['version']))
            with page.expect_download() as event:
                page.locator('#export-report').click()
            html = Path(event.value.path()).read_text(encoding='utf-8-sig')
            # Inspect rendered report text rather than CSS decimal values.
            report_page = context.new_page()
            report_page.set_content(html)
            report_text = report_page.locator('body').inner_text()
            report_page.close()
            check('exported report has no engine/revision/transformation version labels',
                  not LABEL_VERSION.search(report_text)
                  and saved['engine_version'] not in report_text
                  and saved['lineage']['transformation']['version'] not in report_text
                  and not re.search(r'엔진\s*버전|변환\s*버전|transformation.version', report_text, re.I))
            check('report still includes result and method', 'Fisher' in report_text and '전체 결과' in report_text)

            # Native import validity is exercised through the file control, not mocked APIs.
            before = snapshot()
            select_file({}, 'synthetic-invalid.json')
            expect(page.locator('#toast')).to_contain_text('복원 실패')
            check('invalid native JSON rejected without changing analysis', snapshot() == before)
            select_file(saved, 'synthetic-valid.json')
            expect(page.locator('#source-badge')).to_contain_text('집계 복원')
            page.locator('#prepare').click()
            expect(page.locator('#analysis-options')).to_be_visible()
            check('valid native JSON restores counts', page.evaluate(
                'state.prepared.cells.some(c=>c.arm==="B" && c.success===20 && c.total===100)'))
            for field in ('randomized', 'independent', 'mature', 'fixed-stop'):
                page.locator('#' + field).uncheck()
            page.locator('#confirm-input').check()
            page.locator('#analyze').click()
            expect(page.locator('#results-view')).to_be_visible()
            check('functional inference guard remains active without conditions', page.evaluate(
                'state.result.inference_allowed === false && state.result.overall.p_raw == null'))

            page.locator('nav [data-view=input]').click()
            page.locator('#data-text').fill(RAW)
            page.locator('#prepare').click()
            expect(page.locator('#mapping-panel')).to_be_visible()
            # Deliberately keep the default A/B labels: control/treatment cannot match.
            page.locator('#arm-value-a').fill('A')
            page.locator('#arm-value-b').fill('B')
            page.locator('#mapping-confirm').check()
            page.locator('#apply-mapping').click()
            expect(page.locator('#mapping-error')).not_to_be_empty()
            check('mapping error blocks stale analysis and keeps synthetic usernotes',
                  page.locator('#analyze').is_disabled() and page.locator('#data-text').input_value() == RAW
                  and page.evaluate('state.prepared === null && state.result === null'))
            help_cycle('mapping error button close')
            help_cycle('mapping error Escape close', escape=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            check('390px mapping-error page has no horizontal overflow', page.evaluate(
                'document.documentElement.scrollWidth <= innerWidth'))
            help_cycle('390px error button close', mobile=True)
            help_cycle('390px error Escape close', escape=True, mobile=True)
            check('no uncaught JavaScript errors', not page_errors)
            check('no remote/model/credential requests attempted', not blocked)
            result['status'] = 'PASS'
            browser.close()
            browser = None
    except Exception as error:
        result['failure'] = f'{type(error).__name__}: {error}'
        print('FAIL', result['failure'], flush=True)
        if page and not page.is_closed():
            try:
                page.screenshot(path=str(evidence / 'current_interface.png'), full_page=True)
            except Exception:
                pass
    finally:
        result['count'] = len(checks)
        result['passed_count'] = sum(item['pass'] for item in checks)
        result['failed_count'] = sum(not item['pass'] for item in checks)
        result['screenshot'] = str(evidence / 'current_interface.png') if (evidence / 'current_interface.png').exists() else None
        (ROOT / 'interface_verification.json').write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"RESULT {result['status']}: {result['passed_count']}/{result['count']} recorded checks", flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(run(arguments()))
