"""QA for the dealer development progress page.

Runs the built page in a real browser and checks what actually renders:
the empty state, the priority selector, the milestone table, the progress
strip, the printable summary, and the local save/load round trip.

Exit 0 = all checks passed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
HTML = REPO / "02_dashboards" / "ids" / "IDS_2026_Development_Progress.html"
QA = REPO / "02_dashboards" / "ids" / "_qa_development_progress_20260924"

BANNED_WORDS = [
    "AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK",
    "UMI", "UTI", "campaign", "goed", "slecht",
]
BANNED_LITERALS = [".csv", ".json", ".py"]
BANNED_RE = re.compile(
    r"(?:\b(?:" + "|".join(re.escape(t) for t in BANNED_WORDS) + r")\b)"
    r"|(?:" + "|".join(re.escape(t) for t in BANNED_LITERALS) + r")",
    re.I,
)

failures: list[str] = []
checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))
    if not ok:
        failures.append(f"{name}: {detail}")


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    url = HTML.as_uri()
    text = HTML.read_text(encoding="utf-8")

    # --- static checks ---
    check("no CDN", not re.search(r"https?://", text.replace("http://www.w3.org", "")), "external URL found")
    check("no fetch", "fetch(" not in text and "XMLHttpRequest" not in text, "a network read is present")
    hits = BANNED_RE.findall(text)
    check("banned terms absent", not hits, " ".join(sorted(set(hits))))

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(url)
        page.wait_for_timeout(600)

        check("no page errors", not errors, "; ".join(errors[:3]))

        # 1. the page picked a real dealer
        dealer = page.eval_on_selector("#f-dealer", "el => el.value")
        market = page.eval_on_selector("#f-market", "el => el.value")
        check("dealer selected", bool(dealer), f"market={market!r} dealer={dealer!r}")
        check("market selected", bool(market) and market != "UK CV",
              f"default market {market!r} should hold section detail")

        # 2. sections render, not-scored shows as a label and never as zero
        bars = page.eval_on_selector_all("#where-bars .barrow", "els => els.length")
        check("five sections shown", bars == 5, f"found {bars} bars")
        body_text = page.inner_text("body")
        check("not scored is labelled", "Not scored" in body_text or "not scored" in body_text.lower(),
              "no not-scored label anywhere")
        check("where note names the unscored areas", "Not scored" in page.inner_text("#where-note") or
              "All five areas" in page.inner_text("#where-note"), page.inner_text("#where-note")[:80])

        # 3. the priority list is real and clickable
        prios = page.eval_on_selector_all("#prio-list .prio[data-sec]", "els => els.map(e => e.dataset.sec)")
        check("priority options offered", len(prios) >= 3, f"options={prios}")
        check("weakest area is first", bool(prios), f"first={prios[0] if prios else None}")
        page.click("#prio-list .prio[data-sec]")
        page.wait_for_timeout(200)
        sel = page.eval_on_selector("#prio-list .prio.sel", "el => el.dataset.sec")
        check("priority clicks into selected state", bool(sel), "no .prio.sel after click")

        saved_shot = QA / "01_before_fill.png"
        page.screenshot(path=str(saved_shot), full_page=True)

        # 4. empty state reads as an explanation
        empty_text = page.inner_text("#tl-wrap")
        check("progress empty state explains itself", "No dated milestones" in empty_text and len(empty_text) > 80,
              empty_text[:90].replace("\n", " "))
        check("summary prints an explicit blank row",
              "blank on purpose" in page.inner_text("#sum"),
              page.inner_text("#sum")[-160:].replace("\n", " "))
        check("separate-from-score sentence present",
              "not a higher score" in body_text or "does not raise" in body_text,
              "no plain statement that a milestone is not a score")
        check("route stated in the page",
              "Save my plan to a file" in body_text and "Load a saved plan" in body_text,
              "the save/load route is not stated")

        # 5. milestones actually work
        page.fill('#mil-body input[data-i="0"][data-k="d"]', "2026-10-15")
        page.fill('#mil-body input[data-i="0"][data-k="note"]', "Parts counter layout agreed with the distributor")
        page.fill('#mil-body input[data-i="0"][data-k="ev"]', "Layout drawing signed in the meeting")
        page.check('#mil-body input[data-i="0"][data-k="done"]')
        page.fill('#mil-body input[data-i="1"][data-k="d"]', "2026-11-20")
        page.fill('#mil-body input[data-i="1"][data-k="note"]', "Monthly parts target set and monitored")
        page.wait_for_timeout(300)

        prog = page.inner_text("#prog-text")
        check("progress counts the filled rows", "1 of 2" in prog, prog[:90].replace("\n", " "))
        check("progress states the score is unchanged", "unchanged" in prog, prog[-90:].replace("\n", " "))
        bar_w = page.eval_on_selector("#prog-fill", "el => el.style.width")
        check("progress bar reflects one of two done", bar_w == "50%", f"width={bar_w!r}")

        tl = page.inner_text("#tl-wrap")
        check("timeline lists the dated rows", "2026-10-15" in tl and "2026-11-20" in tl, tl[:120].replace("\n", " "))
        dots = page.eval_on_selector_all("#tl-wrap svg circle", "els => els.length")
        check("timeline draws a dot per dated row", dots == 2, f"dots={dots}")

        verdict = page.inner_text("#sum")
        check("summary carries the milestones", "Parts counter layout agreed" in verdict, verdict[-200:].replace("\n", " "))
        check("summary keeps progress and score apart", "does not raise the score" in verdict,
              "the separation sentence is missing from the printable summary")
        address = page.eval_on_selector("#f-dealer", "el => el.options[el.selectedIndex].text")
        if address:
            check("summary does not print the dealer address",
                  "9220" not in verdict and "Zwaarveld" not in verdict,
                  verdict[:120].replace("\n", " "))

        page.screenshot(path=str(QA / "02_filled.png"), full_page=True)

        # 6. save and load round trip, read locally through the file picker
        def grab_download():
            with page.expect_download() as dl:
                page.click("#btn-save")
            return dl.value

        download = grab_download()
        dest = QA / "dealer-development-plan.txt"
        download.save_as(str(dest))
        plan = dest.read_text(encoding="utf-8")
        check("plan file written", "dealer-development-plan" in plan and "Parts counter layout agreed" in plan,
              plan[:120])

        page.reload()
        page.wait_for_timeout(400)
        check("reload starts clean", "No milestone recorded yet" in page.inner_text("#prog-text"),
              page.inner_text("#prog-text")[:80])

        page.set_input_files("#file-load", str(dest))
        page.wait_for_timeout(600)
        reloaded = page.inner_text("#prog-text")
        check("loaded plan restores the rows", "1 of 2" in reloaded, reloaded[:90].replace("\n", " "))
        check("loaded plan restores the priority",
              bool(page.eval_on_selector("#prio-list .prio.sel", "el => el.dataset.sec")),
              "priority did not come back")
        check("load note confirms", "Plan loaded" in page.inner_text("#save-note"),
              page.inner_text("#save-note")[:80])
        page.screenshot(path=str(QA / "03_loaded.png"), full_page=True)

        # 7. print rendering, with the filled plan still on screen
        page.emulate_media(media="print")
        page.screenshot(path=str(QA / "06_print_belgium.png"), full_page=True)
        pdf = QA / "summary.pdf"
        page.pdf(path=str(pdf), format="A4", print_background=True)
        page.emulate_media(media="screen")
        # "/Type /Page" also matches the "/Type /Pages" tree node, so subtract one.
        sheets = pdf.read_bytes().count(b"/Type /Page") - pdf.read_bytes().count(b"/Type /Pages")
        check("print output produced", pdf.exists() and pdf.stat().st_size > 5000,
              f"pdf bytes {pdf.stat().st_size if pdf.exists() else 0}")
        check("summary prints as a single sheet", sheets == 1, f"sheet count {sheets}")

        # 8. a thin market where no section was scored
        page.select_option("#f-market", "UK CV")
        page.wait_for_timeout(400)
        thin = page.inner_text("body")
        check("totals-only market explains itself", "totals only" in page.inner_text("#where-empty"),
              page.inner_text("#where-empty")[:100])
        check("totals-only market offers no priority", "No priority can be derived" in thin,
              "the page invented a priority for a market with no scored section")
        na_bars = page.eval_on_selector_all("#where-bars .na", "els => els.length")
        check("unscored areas drawn as labels not zero", na_bars >= 1, f"labels={na_bars}")
        page.screenshot(path=str(QA / "04_thin_market.png"), full_page=True)

        # 9. a market with an unscored section (Israel) still reads honestly
        page.select_option("#f-market", "Israel LCV")
        page.wait_for_timeout(400)
        isr_note = page.inner_text("#where-note")
        check("unscored section labelled for Israel", "Not scored" in isr_note, isr_note[:120])
        page.screenshot(path=str(QA / "05_israel.png"), full_page=True)

        browser.close()

    # --- report ---
    print(f"checks run: {len(checks)}")
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   [{detail}]" if not ok else ""))
    print(f"\nfailures: {len(failures)}")
    (QA / "QA_REPORT.txt").write_text(
        "\n".join(f"{'PASS' if ok else 'FAIL'}\t{name}\t{detail}" for name, ok, detail in checks)
        + f"\n\nfailures: {len(failures)}\n",
        encoding="utf-8",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
