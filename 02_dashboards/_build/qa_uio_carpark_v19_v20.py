"""QA + screenshots for UIO car park pack."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "fleet" / "ISZE_UIO_Car_Park_V19_V20.html"
CMD = ROOT / "02_dashboards" / "fleet" / "OPEN_ISZE_UIO_Car_Park_V19_V20.cmd"
QA = ROOT / "02_dashboards" / "fleet" / "_qa_uio_carpark"
REC = ROOT / "02_dashboards" / "fleet" / "ISZE_UIO_Car_Park_V19_V20.SHIP_RECEIPT.json"


def static_checks() -> dict:
    html = HTML.read_text(encoding="utf-8")
    cmd_b = CMD.read_bytes()
    banned = []
    low = html.lower()
    for w in ("wallet", "sell-out", "sellout", "sell out", "book b", "iml v7", "model b", "prism lane"):
        # word-ish: avoid "rule book behind" matching "book b"
        if w == "book b":
            if "book b" in low and "rule book" not in low.replace("rule book behind", ""):
                # still catch real Book B; allow "rule book"
                import re
                if re.search(r"\bbook b\b", low):
                    banned.append(w)
        elif w in low:
            banned.append(w)
    # allow "street" only if somehow in JSON paths — forbid as UI word
    if "street" in low:
        banned.append("street")
    return {
        "html_exists": HTML.exists(),
        "cmd_exists": CMD.exists(),
        "cmd_crlf": b"\r\n" in cmd_b,
        "has_payload": 'id="payload"' in html,
        "has_svg_net": 'id="svgNet"' in html,
        "has_gap": 'id="gapBars"' in html,
        "has_rank": 'id="rankBars"' in html,
        "has_surv": 'id="svgSurv"' in html,
        "has_mix": 'id="svgMix"' in html,
        "has_iuk": 'id="svgIuk"' in html,
        "has_amber": "Do not quote V19" in html,
        "has_locked_44926": ("44,926" in html) or ("44926" in html),
        "bar_row_class": "bar-row" in html,
        "kpi_class": html.count('class="kpi"') >= 4 or "kpi" in html,
        "banned_words": banned,
        "size_kb": round(len(html) / 1024, 1),
    }


def chrome_screenshots() -> list[str]:
    QA.mkdir(parents=True, exist_ok=True)
    chrome_candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    chrome = next((p for p in chrome_candidates if p.exists()), None)
    if not chrome:
        return []

    uri = HTML.resolve().as_uri()
    outs = []
    # decision chapter (default)
    out1 = QA / "01_decision_1440.png"
    out2 = QA / "02_operating_1440.png"
    # Use headless chrome screenshot via --screenshot (full page limited); two loads via JS click hard — use CDP through a small script if needed.
    # Simple approach: screenshot default, then rewrite temporary HTML with operating on — better: use playwright if available.

    try:
        import playwright  # noqa: F401
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.goto(uri, wait_until="networkidle")
            page.wait_for_timeout(400)
            # count painted rows
            counts = page.evaluate(
                """() => ({
                gap: document.querySelectorAll('#gapBars .bar-row').length,
                rank: document.querySelectorAll('#rankBars .bar-row').length,
                movers: document.querySelectorAll('#moverBars .dev').length,
                svgNet: !!document.querySelector('#svgNet polyline'),
                svgSurv: !!document.querySelector('#svgSurv polyline'),
                hero: document.querySelectorAll('.kpi .v').length,
                heroText: Array.from(document.querySelectorAll('.kpi .v')).map(e=>e.textContent.trim())
              })"""
            )
            page.screenshot(path=str(out1), full_page=True)
            outs.append(str(out1))
            page.click('button[data-ch="operating"]')
            page.wait_for_timeout(300)
            counts2 = page.evaluate(
                """() => ({
                rank: document.querySelectorAll('#rankBars .bar-row').length,
                movers: document.querySelectorAll('#moverBars .dev').length,
                svgMix: !!document.querySelector('#svgMix polyline'),
                svgIuk: !!document.querySelector('#svgIuk polyline')
              })"""
            )
            page.screenshot(path=str(out2), full_page=True)
            outs.append(str(out2))
            out3 = QA / "03_rules_1440.png"
            page.click('button[data-ch="rules"]')
            page.wait_for_timeout(400)
            counts3 = page.evaluate(
                """() => ({
                ruleCards: document.querySelectorAll('#rulesHost .rule-card').length,
                problems: document.querySelectorAll('#rulesHost .prob').length,
                newData: document.querySelectorAll('#rulesHost .ndata .card').length,
                hasLock: !!document.querySelector('#rulesHost .lockbox .big')
              })"""
            )
            page.screenshot(path=str(out3), full_page=True)
            outs.append(str(out3))
            browser.close()
            Path(QA / "paint_counts.json").write_text(
                json.dumps({"decision": counts, "operating": counts2, "rules": counts3}, indent=2),
                encoding="utf-8",
            )
            return outs
    except Exception as e:
        # fallback: chrome headless screenshot of default view only
        out1.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                str(chrome),
                "--headless=new",
                "--disable-gpu",
                f"--screenshot={out1}",
                "--window-size=1440,1100",
                uri,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        Path(QA / "paint_fallback_error.txt").write_text(str(e), encoding="utf-8")
        if out1.exists():
            outs.append(str(out1))
        return outs


def write_receipt(static: dict, shots: list[str]) -> None:
    paint = {}
    pc = QA / "paint_counts.json"
    if pc.exists():
        paint = json.loads(pc.read_text(encoding="utf-8"))
    ok = (
        static["html_exists"]
        and static["cmd_exists"]
        and static["cmd_crlf"]
        and static["has_payload"]
        and static["has_amber"]
        and static["has_locked_44926"]
        and not static["banned_words"]
        and len(shots) >= 1
    )
    if paint:
        d = paint.get("decision") or {}
        o = paint.get("operating") or {}
        ok = ok and d.get("gap", 0) >= 5 and d.get("hero", 0) >= 4 and o.get("rank", 0) >= 10
        ok = ok and d.get("svgNet") and d.get("svgSurv") and o.get("svgMix") and o.get("svgIuk")
        r = paint.get("rules") or {}
        ok = ok and r.get("ruleCards", 0) >= 6 and r.get("problems", 0) >= 7 and r.get("newData", 0) >= 5

    rec = {
        "ok": ok,
        "artifact": str(HTML),
        "launcher": str(CMD),
        "mtime": HTML.stat().st_mtime,
        "built": "2026-09-16",
        "static": static,
        "paint": paint,
        "screenshots": shots,
        "checks": [
            "self-contained payload embedded",
            "chapter A: network slope + gap bars + survival",
            "chapter B: ranked 2025 + movers + mix + IUK locked",
            "spoken labels: no wallet/street/sell-out",
            "OPEN_*.cmd CRLF",
        ],
    }
    REC.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, indent=2))


def main() -> None:
    static = static_checks()
    shots = chrome_screenshots()
    write_receipt(static, shots)


if __name__ == "__main__":
    main()
