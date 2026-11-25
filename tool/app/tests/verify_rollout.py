"""Check rollout decisions against the normal local server in Chromium."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from playwright.sync_api import expect, sync_playwright


def verify_shortcuts(page, url):
    page.goto(url)
    section = page.get_by_role("region", name="가상 정기점검 사례 바로 열기")
    decision = page.locator("#rollout-decision")
    status = page.locator("#rollout-example-status")
    cases = [
        ("원래 사례", "확대 보류", "1597", "139", "unknown"),
        ("수치 충족, 운영 미확인", "확대 보류", "1680", "120", "unknown"),
        ("수치와 운영 조건 충족", "확대 검토 가능", "1680", "120", "ready"),
    ]
    for label, *_ in cases:
        expect(section.get_by_role("button", name=label, exact=True)).to_be_in_viewport()
    assert not page.locator("#rollout").evaluate("(element) => element.open")
    raw = "arm,success,total\nA,12,100\nB,20,100"
    page.locator("#data-text").fill(raw)
    for label, verdict, visits, optouts, operations in cases:
        section.get_by_role("button", name=label, exact=True).click()
        expect(status).to_have_text(f"{label} / {verdict}")
        expect(decision).to_be_visible()
        expect(decision).to_have_text(verdict)
        expect(page.locator('[name="visit-b"]')).to_have_value(visits)
        expect(page.locator('[name="optout-b"]')).to_have_value(optouts)
        expect(page.locator('[name="capacity"]')).to_have_value(operations)
        expect(page.locator('[name="cost"]')).to_have_value(operations)
        expect(page.locator("#data-text")).to_have_value(raw)
        expect(page.locator('nav [data-view="share"]')).to_be_enabled()
    assert page.evaluate("document.documentElement.scrollWidth === innerWidth")


def verify(page, url):
    response = page.goto(url)
    assert response.ok
    page.locator("#rollout > summary").click()
    decision = page.locator("#rollout-decision")
    reasons = page.locator("#rollout-reasons")
    expect(decision).to_have_text("판정 대기")
    page.locator("#rollout-example").click()

    expect(decision).to_have_text("확대 보류")
    expect(reasons).to_contain_text("차이 +1.089%p, 보정 하한 +0.286%p / 최소 개선폭 +0.500%p")
    expect(reasons).to_contain_text("차이 +0.058%p, 95% 신뢰구간 상한 +0.265%p / 허용 상한 +0.200%p")
    expect(reasons).to_contain_text("센터 수용량 미확인")
    expect(reasons).to_contain_text("비용 미확인")

    visit = page.locator('[name="visit-b"]')
    optout = page.locator('[name="optout-b"]')
    capacity = page.locator('[name="capacity"]')
    cost = page.locator('[name="cost"]')
    visit.fill("1680")
    expect(reasons.locator("li").nth(0)).to_have_text(
        "충족 — 방문 완료율 차이 +1.621%p, 보정 하한 +0.808%p / 최소 개선폭 +0.500%p"
    )
    optout.fill("120")
    expect(reasons.locator("li").nth(1)).to_have_text(
        "충족 — 수신 철회율 차이 -0.064%p, 95% 신뢰구간 상한 +0.135%p / 허용 상한 +0.200%p"
    )
    expect(decision).to_have_text("확대 보류")
    capacity.select_option("ready")
    expect(decision).to_have_text("확대 보류")
    cost.select_option("ready")
    expect(decision).to_have_text("확대 검토 가능")
    capacity.select_option("unknown")
    expect(decision).to_have_text("확대 보류")
    capacity.select_option("blocked")
    expect(reasons).to_contain_text("센터 수용량 조건 미충족")
    capacity.select_option("ready")
    page.locator('[name="design-confirmed"]').uncheck()
    expect(decision).to_have_text("확대 보류")
    page.locator('[name="design-confirmed"]').check()

    for selector, invalid, valid in [
        ('[name="visit-min"]', "0.90", "0.50"),
        ('[name="optout-max"]', "0.10", "0.20"),
        ('[name="visit-b"]', "15604", "1680"),
        ('[name="optout-b"]', "", "120"),
    ]:
        field = page.locator(selector)
        field.fill(invalid)
        expected = "판정 대기" if selector in ('[name="visit-b"]', '[name="optout-b"]') else "확대 보류"
        expect(decision).to_have_text(expected)
        field.fill(valid)
        expect(decision).to_have_text("확대 검토 가능")

    visit.fill("1450")
    expect(decision).to_have_text("확대 보류")
    expect(reasons).to_contain_text("차이 +0.147%p, 보정 하한 -0.639%p")
    page.locator('[name="comparison"]').select_option("single")
    expect(reasons).to_contain_text("95% 신뢰구간 하한")
    assert page.evaluate("document.documentElement.scrollWidth === innerWidth")


def verify_saved_report(page, url):
    page.goto(url)
    page.locator("#rollout > summary").click()
    page.locator("#rollout-example").click()
    expect(page.locator("#rollout-example-status")).to_have_text("원래 사례 / 확대 보류")
    original = page.locator("#rollout-reasons li").all_text_contents()
    with page.expect_download() as download:
        page.locator("#save-project").click()
    saved = download.value.path().read_bytes()
    project = json.loads(saved)
    assert project["version"] == 8 and project["cells"] == []
    rollout = project["rollout"]
    assert rollout["source"] == "synthetic" and rollout["decision"] == "hold"
    assert rollout["input"] == {
        "total-a": 15482, "visit-a": 1416, "optout-a": 129,
        "total-b": 15603, "visit-b": 1597, "optout-b": 139,
        "visit-min": 0.5, "optout-max": 0.2, "comparison": "three",
        "capacity": "unknown", "cost": "unknown", "design-confirmed": True,
    }
    assert [f'보류 — {check["reason"]}' for check in rollout["reasons"]] == original

    page.reload()
    share = page.locator('nav [data-view="share"]')
    expect(share).to_be_disabled()
    page.locator("#project-file").set_input_files(
        {"name": "revisit.json", "mimeType": "application/json", "buffer": saved}
    )
    expect(page.locator("#rollout-decision")).to_have_text("확대 보류")
    expect(page.locator("#rollout-reasons li")).to_have_text(original)
    page.locator('#rollout-to-report').click()
    expect(page.locator("#csv-share-options")).to_be_hidden()
    preview = page.locator("#report-preview")
    scope = preview.locator(".rollout-scope")
    expect(scope.locator("dt")).to_have_text(["실험 대상", "분석 고객군", "적용 범위"])
    expect(scope.locator("dd").nth(0)).to_contain_text("30일 안에 정기점검")
    expect(scope.locator("dd").nth(1)).to_contain_text("고객군별 효과는 미확인")
    expect(scope.locator("dd").nth(2)).to_contain_text("확대 보류")
    for expected in [
        "확대 보류", "가상 정기점검 사례", "A군: 배정 15,482명, 방문 완료 1,416명, 수신 철회 129명",
        "B군: 배정 15,603명, 방문 완료 1,597명, 수신 철회 139명", *original,
    ]:
        expect(preview).to_contain_text(expected)
    page.locator("#share-confirm").check()
    with page.expect_download() as download:
        page.locator("#export-report").click()
    exported = download.value.path().read_text(encoding="utf-8")
    assert all(expected in exported for expected in ["확대 보류", "15,603명", *original])
    assert all(
        expected in exported
        for expected in ("실험 대상", "분석 고객군", "적용 범위", "고객군별 효과는 미확인")
    )
    page.evaluate("window.print = () => {}")
    page.locator("#print-report").click()
    expect(page.locator("#print-area")).to_contain_text(original[0], use_inner_text=False)
    expect(page.locator("#print-area .rollout-scope")).to_contain_text(
        "고객군별 효과는 미확인", use_inner_text=False
    )

    page.locator('nav [data-view="input"]').click()
    page.locator('[name="visit-b"]').fill("1680")
    share.click()
    expect(page.locator("#share-confirm")).not_to_be_checked()
    expect(page.locator("#export-report")).to_be_disabled()
    expect(preview).to_contain_text("+1.621%p")
    expect(preview).not_to_contain_text("+1.089%p")

    page.locator('nav [data-view="input"]').click()
    page.locator("#data-text").fill("arm,success,total\nA,12,100\nB,20,100")
    page.locator("#prepare").click()
    expect(page.locator("#analysis-options")).to_be_visible()
    for condition in ("randomized", "independent", "mature", "fixed-stop"):
        page.locator(f"#{condition}").select_option("yes")
    page.locator("#confirm-input").check()
    page.locator("#analyze").click()
    expect(page.locator("#results-view")).to_be_visible()
    share.click()
    expect(page.locator("#csv-share-options")).to_be_visible()
    expect(preview).to_contain_text("전체 결과")
    expect(preview).to_contain_text("별도로 입력한 집계")
    expect(preview).to_contain_text("+1.621%p")

    # Restoring an older project must clear the previous project's rollout state.
    project["version"] = 7
    del project["rollout"]
    page.locator("#project-file").set_input_files({
        "name": "legacy.json", "mimeType": "application/json",
        "buffer": json.dumps(project).encode(),
    })
    expect(share).to_be_disabled()
    expect(page.locator('[name="visit-b"]')).to_have_value("")


def verify_plan_first(page, url):
    page.goto(url)
    page.locator("#rollout-start").click()
    expect(page.locator("#rollout-entry")).to_be_hidden()
    page.locator("#rollout-goal-name").fill("예약 완료")
    page.locator("#rollout-guard-name").fill("수신 철회")
    page.locator('[name="visit-min"]').fill("0.50")
    page.locator('[name="optout-max"]').fill("0.20")
    page.locator("#rollout-next").click()
    expect(page.locator("#rollout-criteria-summary")).to_contain_text("예약 완료 비율 최소 +0.5%p")
    with page.expect_download() as saved:
        page.locator("#save-project").click()
    draft = saved.value.path().read_bytes()
    assert json.loads(draft)["version"] == 9

    page.reload()
    page.locator("#project-file").set_input_files(
        {"name": "criteria.json", "mimeType": "application/json", "buffer": draft}
    )
    expect(page.locator('[name="visit-min"]')).to_have_value("0.5")
    expect(page.locator('[name="optout-max"]')).to_have_value("0.2")
    expect(page.locator('[name="visit-b"]')).to_have_value("")
    for name, value in {
        "total-a": 15482, "visit-a": 1416, "optout-a": 129,
        "total-b": 15603, "visit-b": 1597, "optout-b": 139,
    }.items():
        page.locator(f'[name="{name}"]').fill(str(value))
    page.locator('[name="design-confirmed"]').check()
    expect(page.locator("#rollout-decision")).to_have_text("확대 보류")
    page.locator("#rollout-to-report").click()
    expect(page.locator("#report-preview")).to_contain_text("예약 완료 비율")
    expect(page.locator("#report-preview .report-warning")).to_have_count(0)
    page.locator('nav [data-view="input"]').click()
    page.locator('[name="visit-min"]').fill("0.51")
    page.locator("#rollout-to-report").click()
    expect(page.locator("#report-preview .report-warning")).to_be_visible()
    page.locator("#share-confirm").check()
    with page.expect_download() as saved:
        page.locator("#export-report").click()
    html = saved.value.path().read_text(encoding="utf-8")
    assert all(heading in html for heading in (
        "A/B 실험 판단 보고서", "판정 요약", "실험과 적용 범위",
        "승리 조건과 판단 근거", "A/B 결과 입력", "다음 행동", "방법과 한계",
    ))
    assert "최소 개선폭 +0.510%p" in html and 'class="report-warning"' in html
    assert page.evaluate("document.documentElement.scrollWidth === innerWidth")
    with page.expect_download() as saved:
        page.locator("#save-project").click()
    result = saved.value.path().read_bytes()
    assert json.loads(result)["version"] == 9
    page.reload()
    page.locator("#project-file").set_input_files(
        {"name": "result.json", "mimeType": "application/json", "buffer": result}
    )
    page.locator("#rollout-to-report").click()
    expect(page.locator("#report-preview .report-warning")).to_be_visible()
    expect(page.locator("#report-preview")).to_contain_text("예약 완료 비율")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--browser")
    parser.add_argument("--no-record", action="store_true")
    args = parser.parse_args()
    with subprocess.Popen(
        [sys.executable, str(args.app.resolve() / "server.py")],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ) as server:
        try:
            startup = server.stdout.readline().strip()
            assert startup.startswith("AB_LOCAL_URL="), startup
            url = startup.split("=", 1)[1]
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=args.browser)
                checks=[]
                for width in (1440, 375):
                    page = browser.new_page(viewport={"width": width, "height": 900}, accept_downloads=True)
                    verify_shortcuts(page, url)
                    verify(page, url)
                    verify_saved_report(page, url)
                    verify_plan_first(page, url)
                    page.close()
                    checks.append({"name":f"published rollout decision/persistence/report {width}px","pass":True})
                    print(f"PASS {width}px")
                browser.close()
                if not args.no_record:
                    (args.app/"rollout_verification.json").write_text(json.dumps({"status":"PASS","count":len(checks),"checks":checks,"counting":"two viewport flow groups, not individual assertion count","actual_model_calls":0,"human_observations":0},ensure_ascii=False,indent=2),encoding="utf-8")
        finally:
            server.terminate()
            server.wait(timeout=15)
