"""Visual QA for ISZE_DB_Leakage_Review_CY2025.html

Renders with the real Chrome binary (not the headless shell). Captures
full-page at four widths, per-section zooms, a hover state, and every toggle
combination. Writes PNGs to sales\\_qa_db_leakage\\ and prints a manifest.

Run: python 02_dashboards\\_build\\qa_db_leakage_review.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_DB_Leakage_Review_CY2025.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_db_leakage"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = HTML.as_uri()

QA.mkdir(parents=True, exist_ok=True)
# clear previous run
for f in QA.glob("*.png"):
    f.unlink()

WIDTHS = [(390, 900), (1024, 800), (1280, 900), (1440, 950)]
COMBOS = [
    ("cy-db-inc", "Calendar 2025", "db", "Included"),
    ("cy-db-exc", "Calendar 2025", "db", "Excluded"),
    ("cy-dealer-inc", "Calendar 2025", "dealer", "Included"),
    ("cy-dealer-exc", "Calendar 2025", "dealer", "Excluded"),
    ("fy-db-inc", "Fiscal 2025", "db", "Included"),
    ("fy-db-exc", "Fiscal 2025", "db", "Excluded"),
    ("fy-dealer-inc", "Fiscal 2025", "dealer", "Included"),
    ("fy-dealer-exc", "Fiscal 2025", "dealer", "Excluded"),
]

shots: list[dict] = []
problems: list[str] = []


def snap(page, name: str, clip=None):
    p = QA / f"{name}.png"
    page.screenshot(path=str(p), full_page=(clip is None), clip=clip)
    shots.append({"name": name, "file": str(p), "bytes": p.stat().st_size})
    return p


def set_combo(page, period, direction, warr):
    for t, v in (("period", "cy" if period.startswith("Calendar") else "fy"),
                 ("dir", direction),
                 ("warr", "inc" if warr == "Included" else "exc")):
        page.click(f'.tgl button[data-t="{t}"][data-v="{v}"]')
    page.wait_for_timeout(260)


def element_shot(page, selector, name):
    """Screenshot one element; skipped (and recorded) when it is not visible."""
    el = page.query_selector(selector)
    if not el:
        return False
    try:
        if not el.is_visible():
            return False
        el.scroll_into_view_if_needed(timeout=5000)
        page.wait_for_timeout(160)
        p = QA / f"{name}.png"
        el.screenshot(path=str(p), timeout=15000)
        shots.append({"name": name, "file": str(p), "bytes": p.stat().st_size})
        return True
    except Exception as e:  # noqa: BLE001
        problems.append({"element_shot_failed": name, "why": str(e)[:160]})
        return False


def overflow_report(page, tag):
    """Any element wider than the viewport (ignoring intentional scroll boxes),
    or text clipped inside a box, or light-on-light text."""
    return page.evaluate(
        """(tag) => {
        const vw = document.documentElement.clientWidth;
        const out = {tag:tag, docScroll:document.documentElement.scrollWidth, vw:vw, wide:[], clipped:[], lowContrast:[]};
        const inScroll = (el) => { let n = el; while (n && n !== document.body) { if (n.classList && n.classList.contains('scroll')) return true; n = n.parentElement; } return false; };
        document.querySelectorAll('body *').forEach(el=>{
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) return;
          if ((r.right > vw + 1.5 || r.left < -1.5) && !inScroll(el)) {
            const st = getComputedStyle(el);
            if (st.position === 'absolute' || st.position === 'fixed') return;
            out.wide.push({sel: el.tagName + (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ').filter(Boolean).join('.') : ''),
                           right: Math.round(r.right), left: Math.round(r.left), w: Math.round(r.width),
                           txt: (el.textContent||'').trim().slice(0,48)});
          }
          const st = getComputedStyle(el);
          if (el.children.length === 0 && el.textContent && el.textContent.trim() &&
              st.overflow !== 'visible' && st.overflow !== 'auto' && st.overflow !== 'scroll') {
            if (el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2) {
              out.clipped.push({sel: el.tagName + (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ')[0] : ''),
                                sh: el.scrollHeight, ch: el.clientHeight, sw: el.scrollWidth, cw: el.clientWidth,
                                txt: (el.textContent||'').trim().slice(0,60)});
            }
          }
        });
        document.querySelectorAll('td,th,.dbfocus,.note,.callout,.chart,.hstat .v,.hstat .l,li,p.small').forEach(el=>{
          const st = getComputedStyle(el);
          const m = st.color.match(/\\d+/g); if(!m) return;
          const lum = 0.299*+m[0] + 0.587*+m[1] + 0.114*+m[2];
          if (lum > 185) {
            let bg = 'rgba(0, 0, 0, 0)', node = el;
            while (node && (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent')) { bg = getComputedStyle(node).backgroundColor; node = node.parentElement; }
            const bm = bg.match(/[\\d.]+/g);
            if (bm && bm.length >= 3) {
              const bl = 0.299*+bm[0] + 0.587*+bm[1] + 0.114*+bm[2];
              if (bl > 175) out.lowContrast.push({sel: el.tagName, color: st.color, bg: bg,
                txt: (el.textContent||'').trim().slice(0,40)});
            }
          }
        });
        return out;
      }""", tag)


def assert_page(page):
    """Numeric + structural assertions on the rendered default page."""
    return page.evaluate(
        """() => {
        const q = (s) => document.querySelector(s);
        const txt = (s) => { const e = q(s); return e ? e.textContent.trim() : null; };
        const rows = document.querySelectorAll('#league-tbody tr').length;
        const foot = document.querySelectorAll('#league-foot tr').length;
        const c1 = document.querySelectorAll('#c1-rows .brow').length;
        const c2 = document.querySelectorAll('#c2-rows .brow').length;
        const c3 = document.querySelectorAll('#c3-rows .brow').length;
        const c4 = document.querySelectorAll('#c4-rows .brow').length;
        const c5 = document.querySelectorAll('#c5-rows .brow').length;
        const c6 = document.querySelectorAll('#c6-rows .brow').length;
        // any em dash leaking as literal text? any unresolved placeholder?
        const body = document.body.innerText;
        return {
          hero_gap: txt('.hstats .hstat:nth-child(1) .v'),
          hero_nb: txt('#hero-nb'),
          hero_billed: txt('#hero-billed'),
          hero_rep: txt('#hero-rep'),
          league_rows: rows, league_foot: foot,
          charts: {c1:c1, c2:c2, c3:c3, c4:c4, c5:c5, c6:c6},
          null_cells: document.querySelectorAll('#league-tbody td.null').length,
          kpi_cells: document.querySelectorAll('.kpi').length,
          tips: document.querySelectorAll('.tip').length,
          literal_amp: (body.match(/&[a-z]+;/g)||[]).length,
          literal_39: (body.match(/&#39;/g)||[]).length,
          literal_mdash: (body.match(/&mdash;/g)||[]).length,
          undefined_txt: (body.match(/undefined|NaN|\\[object/g)||[]).length,
          banned_words: ['sell-out','sellout','parc','wallet','mass-demand'].filter(w => body.toLowerCase().includes(w)),
          external_refs: Array.from(document.querySelectorAll('link[href],script[src],img[src]'))
              .map(e => e.getAttribute('href')||e.getAttribute('src')).filter(u => /^https?:/i.test(u)),
          actions: document.querySelectorAll('section .note ol li').length,
          caveats: document.querySelectorAll('section .note ul li').length,
          story_cards: document.querySelectorAll('.dbfocus').length,
        };
      }"""
    )


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, headless=True,
                                 args=["--force-color-profile=srgb", "--hide-scrollbars",
                                       "--disable-lcd-text", "--font-render-hinting=none"])
    ctx = browser.new_context(device_scale_factor=1)
    page = ctx.new_page()
    console: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
    page.goto(URL, wait_until="load")
    page.wait_for_timeout(700)
    problems.append({"console": console})
    problems.append({"assertions_default": assert_page(page)})

    # 1) full page at each width, default combo
    for w, h in WIDTHS:
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(400)
        snap(page, f"full_{w}_default")
        problems.append({"width": w, **(overflow_report(page, f"w{w}"))})

    # 2) section zooms at 1280
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(350)
    for sid in ["c1", "c2", "c3", "c4", "c5", "c6"]:
        if not element_shot(page, f"#{sid}", f"zoom_{sid}"):
            problems.append({"missing_or_hidden_chart": sid})

    # hero + league table + availability banner
    for sel, nm in [(".hero", "zoom_hero"), ("#league", "zoom_league"),
                    ("section:nth-of-type(3) .callout", "zoom_callout_leak3"),
                    ("section:nth-of-type(2) .g3", "zoom_storycards"),
                    ("section:nth-of-type(5)", "zoom_actions")]:
        if not element_shot(page, sel, nm):
            problems.append({"missing_or_hidden": nm})

    # section slices: every h2 block, top and bottom half
    for i, (sid, nm) in enumerate([("s-league", "league"), ("s-repl", "repl"),
                                   ("s-mix", "mix"), ("s-price", "price"),
                                   ("s-story", "story"), ("s-actions", "actions"),
                                   ("s-caveats", "caveats")]):
        pass  # sections are captured via the zooms + full page above

    # 3) hover state on a tooltip
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(250)
    cell = page.query_selector("#league-tbody tr:nth-child(2) td:nth-child(2) .kpi")
    if cell:
        try:
            cell.scroll_into_view_if_needed(timeout=5000)
            cell.hover(timeout=5000, force=True)
            page.wait_for_timeout(400)
            vis = page.evaluate("() => { const t=document.querySelector('#league-tbody tr:nth-child(2) td:nth-child(2) .tip'); "
                                "return t ? getComputedStyle(t).display : 'none'; }")
            problems.append({"tooltip_display": vis})
            box = page.evaluate("""() => {
                const t = document.querySelector('#league-tbody tr:nth-child(2) td:nth-child(2) .tip');
                if (!t) return null; const r = t.getBoundingClientRect();
                return {x:r.x, y:r.y, w:r.width, h:r.height};
            }""")
            if box and box["w"] > 0:
                pad = 8
                clip = {"x": max(0, box["x"] - pad), "y": max(0, box["y"] - pad),
                        "width": min(1280 - max(0, box["x"] - pad), box["w"] + 2 * pad),
                        "height": box["h"] + 2 * pad}
                p = QA / "hover_tooltip.png"
                page.screenshot(path=str(p), clip=clip)
                shots.append({"name": "hover_tooltip", "file": str(p), "bytes": p.stat().st_size})
        except Exception as e:  # noqa: BLE001
            problems.append({"hover_failed": str(e)[:200]})

    # 4) every toggle combination, full page
    for name, period, direction, warr in COMBOS:
        page.set_viewport_size({"width": 1280, "height": 900})
        page.wait_for_timeout(200)
        set_combo(page, period, direction, warr)
        page.wait_for_timeout(420)
        snap(page, f"combo_{name}")
        element_shot(page, "#league", f"combo_{name}_league")
        element_shot(page, "#avail", f"combo_{name}_avail")
        element_shot(page, "#c3", f"combo_{name}_c3")
        problems.append({"combo": name, **(overflow_report(page, name))})
        problems.append({f"assert_{name}": assert_page(page)})

    # 5) mobile under a hard toggle combination (worst case)
    page.set_viewport_size({"width": 390, "height": 900})
    set_combo(page, "Fiscal 2025", "dealer", "Excluded")
    page.wait_for_timeout(450)
    snap(page, "mobile_fy_dealer_exc")
    problems.append({"combo": "mobile_fy_dealer_exc", **(overflow_report(page, "mobile_fy"))})
    for sid in ["c1", "c2", "c4"]:
        element_shot(page, f"#{sid}", f"mobile_{sid}")
    problems.append({"combo": "mobile_fy_dealer_exc", **(overflow_report(page, "mobile_fy"))})

    # 6) runtime errors / console
    browser.close()

(QA / "_manifest.json").write_text(json.dumps({"shots": shots, "problems": problems}, indent=1), encoding="utf-8")
print(f"SCREENSHOTS TAKEN: {len(shots)}")
for s in shots:
    print("  ", s["name"], f"{s['bytes']/1024:.0f} KB")
print("\nASSERTIONS / PROBLEMS:")
for p in problems:
    if "assertions_default" in p or any(k.startswith("assert_") for k in p):
        k = list(p.keys())[0]
        print(f"  [{k}] {json.dumps(p[k])}")
        continue
    if "console" in p:
        print(f"  [console] {p['console'] or 'clean'}")
        continue
    wide = p.get("wide") or []
    clip = p.get("clipped") or []
    lc = p.get("lowContrast") or []
    if wide or clip or lc or p.get("missing_or_hidden") or p.get("missing_or_hidden_chart") or p.get("hover_failed"):
        print(f"  [{p.get('width') or p.get('combo')}] docScroll={p.get('docScroll')} vw={p.get('vw')} "
              f"wide={len(wide)} clipped={len(clip)} lowContrast={len(lc)}")
        for w in wide[:5]:
            print("     WIDE", w)
        for c in clip[:5]:
            print("     CLIP", c)
        for x in lc[:5]:
            print("     CONTRAST", x)
