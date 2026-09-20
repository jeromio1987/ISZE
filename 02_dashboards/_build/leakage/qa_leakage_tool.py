"""Distributor leakage tool - rendered paint QA.

Static text checks cannot prove a panel draws. This opens each artefact in real Chrome from
a file:// URL, exactly as Jerome will, and asserts:

  1. No JavaScript error on load. A runtime error is what turns a panel into a blank card.
  2. Every panel renders visible content with a real chart or table inside it.
  3. No panel renders the "failed to draw" banner.
  4. Headline figures are actually on the page as text.
  5. Nothing overflows its container or clips at four widths.
  6. No white-on-pale header (house contrast rule).
  7. Screenshots written to _qa/ for a human to look at.

Run:  python 02_dashboards\\_build\\leakage\\qa_leakage_tool.py
Exit code 0 only when every rendered check passes.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.environ.get("ISZE_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SALES = os.path.join(ROOT, "02_dashboards", "sales")
PACKS = os.path.join(SALES, "leakage_packs")
QA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_qa")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    return None


ARTIFACTS = [
    ("cockpit", os.path.join(SALES, "ISZE_Leakage_Cockpit.html"), 11,
     ["evolution", "dynamics", "gps", "pms", "mix", "aim", "subgroup", "unbilled",
      "actions", "league", "honesty"]),
    ("ITUK", os.path.join(PACKS, "ISZE_Sales_Performance_Review_ITUK.html"), 10,
     ["evolution", "dynamics", "gps", "pms", "mix", "aim", "subgroup", "unbilled",
      "actions", "honesty"]),
    ("SWEDEN", os.path.join(PACKS, "ISZE_Sales_Performance_Review_SWEDEN.html"), 10,
     ["evolution", "dynamics", "gps", "pms", "mix", "aim", "subgroup", "unbilled",
      "actions", "honesty"]),
    ("BELGIUM", os.path.join(PACKS, "ISZE_Sales_Performance_Review_BELGIUM.html"), 10,
     ["evolution", "dynamics", "gps", "pms", "mix", "aim", "subgroup", "unbilled",
      "actions", "honesty"]),
]

WIDTHS = [(1440, 1000), (1280, 1000), (1024, 900), (390, 844)]

# Each panel must contain at least one of these to count as painted.
PAINT_SELECTORS = ".hb-row, .kpi, tr, .tr-row, .stk-col, .donut svg, .cb2-bar, .lc svg, .banner, p.note"

failures: list[str] = []
notes: list[str] = []


def fail(m: str) -> None:
    failures.append(m)


def ok(m: str) -> None:
    notes.append("  ok   " + m)


def probe(page) -> dict:
    """Read the DOM back: what painted, what went wrong, and what is clipped."""
    return page.evaluate("""() => {
      const out = { panels: [], banners: [], overflow: [], contrast: [], errors: [], clipped: [] };
      for (const sec of document.querySelectorAll('section[id^="sec-"]')) {
        const host = sec.querySelector('[id^="mod-"]');
        const txt = (host ? host.innerText : '').trim();
        const chartish = host ? host.querySelectorAll(
          '.hb-row, .kpi, table, .tr-row, .stk-col, .donut svg, .cb2-bar, .lc svg').length : 0;
        out.panels.push({
          id: sec.id.replace('sec-', ''),
          chars: txt.length,
          chartish: chartish,
          failed: txt.includes('failed to draw'),
          head: txt.slice(0, 90),
        });
        const b = host ? host.querySelector('.banner.rose') : null;
        if (b) out.banners.push(sec.id + ': ' + b.innerText.slice(0, 120));
      }

      // Text that is cut off by its own box. This is the failure the review caught on the
      // change bars, so it is checked directly rather than inferred from layout.
      for (const el of document.querySelectorAll('main *')) {
        if (!el.childNodes.length) continue;
        const cs = getComputedStyle(el);
        if (cs.overflow === 'visible' && cs.overflowY === 'visible') {
          // visible overflow cannot clip, so nothing to test
        }
        const clipsY = ['hidden', 'clip'].includes(cs.overflowY);
        const clipsX = ['hidden', 'clip'].includes(cs.overflowX);
        if (!clipsY && !clipsX) continue;
        if (!el.innerText || !el.innerText.trim()) continue;
        const dy = el.scrollHeight - el.clientHeight;
        const dx = el.scrollWidth - el.clientWidth;
        if ((clipsY && dy > 2) || (clipsX && dx > 2)) {
          out.clipped.push({
            tag: el.tagName, cls: String(el.className).slice(0, 44),
            dy: dy, dx: dx, text: el.innerText.slice(0, 44),
            sec: el.closest('section') ? el.closest('section').id : '',
          });
        }
      }

      // Any element whose text is taller than its own line box, i.e. a squeezed label.
      for (const el of document.querySelectorAll('.cb2-val, .hb-val, .kpi-v, .stk-tot, .tr-val')) {
        if (el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0) {
          out.clipped.push({ tag: el.tagName, cls: String(el.className).slice(0, 44),
            dy: el.scrollHeight - el.clientHeight, dx: 0,
            text: el.innerText.slice(0, 44),
            sec: el.closest('section') ? el.closest('section').id : '' });
        }
      }

      const de = document.documentElement;
      out.overflow.push({ w: de.clientWidth, sw: de.scrollWidth });
      const lum = (c) => {
        const m = c.match(/\\d+/g); if (!m) return null;
        const [r, g, b] = m.map(Number);
        return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
      };
      for (const el of document.querySelectorAll('th, .banner, .kpi, td, header.top, nav.mods a')) {
        const cs = getComputedStyle(el);
        const bg = lum(cs.backgroundColor), fg = lum(cs.color);
        if (bg === null || fg === null) continue;
        if (bg > 0.72 && fg > 0.72) out.contrast.push(el.tagName + '.' + el.className + ' ' + cs.backgroundColor + '/' + cs.color);
        if (bg < 0.3 && fg < 0.3) out.contrast.push(el.tagName + '.' + el.className + ' ' + cs.backgroundColor + '/' + cs.color);
      }
      return out;
    }""")


def check_rendered_text(page, name: str, audience: str) -> None:
    """Read the painted text of every panel and sweep it for the failures that a structural
    check cannot see: an unresolved JavaScript value, or internal vocabulary on a page that
    leaves the building. The honesty panel once rendered the word "undefined" for every figure
    on it, and no amount of counting chart primitives noticed."""
    body = page.inner_text("body")
    low = body.lower()

    for tok in ("undefined", "nan", "null", "infinity", "[object"):
        if re.search(rf"(?<![a-z]){re.escape(tok)}(?![a-z])", low):
            fail(f"{name}: the page renders the literal '{tok}' - an unresolved value")
    ok(f"{name}: no unresolved values rendered")

    # Internal vocabulary is allowed in the internal cockpit, which is exactly where those
    # concepts are the subject. It must never appear on a page that goes to a distributor.
    if audience == "customer":
        internal = ["thresholds", "defection", "undercut", "early_warning", "risk_score",
                    "health_alert", "account_health", "unsourced", "book b", "pr00"]
        hits = [w for w in internal if w in low]
        if hits:
            fail(f"{name}: internal vocabulary rendered on a customer page -> {hits}")
        else:
            ok(f"{name}: no internal vocabulary rendered")
    else:
        ok(f"{name}: internal page, internal vocabulary permitted")


def main() -> int:
    chrome = find_chrome()
    if not chrome:
        print("NO_CHROME_FOUND - cannot verify paint. Install Chrome or run on Jerome's PC.")
        return 1
    print(f"browser: {chrome}\n")
    # One folder per build so a full sweep does not overwrite the last one.
    sweep = os.path.join(QA, "sweep")
    os.makedirs(QA, exist_ok=True)
    os.makedirs(sweep, exist_ok=True)

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=chrome, headless=True,
                                args=["--no-sandbox", "--allow-file-access-from-files"])
        for name, path, n_panels, panel_ids in ARTIFACTS:
            if not os.path.exists(path):
                fail(f"{name}: artefact missing {path}")
                continue
            print(f"--- {name}")
            ctx = br.new_context(viewport={"width": 1440, "height": 1000})
            page = ctx.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}")
                    if m.type == "error" else None)

            page.goto(Path(path).as_uri(), wait_until="load")
            page.wait_for_timeout(900)

            # 1. JS errors
            if errors:
                fail(f"{name}: JavaScript error on load -> {errors[:3]}")
            else:
                ok(f"{name}: no JavaScript error on load")

            r = probe(page)

            # 2. every panel painted
            empty = [p for p in r["panels"] if p["chars"] < 40 or p["chartish"] == 0]
            if len(r["panels"]) != n_panels:
                fail(f"{name}: expected {n_panels} panels in the DOM, found {len(r['panels'])}")
            if empty:
                fail(f"{name}: {len(empty)} panel(s) painted nothing -> "
                     f"{[(p['id'], p['chars'], p['chartish']) for p in empty]}")
            else:
                ok(f"{name}: all {len(r['panels'])} panels painted content and a chart or table")

            # 3. no failure banner
            drawn_failed = [p for p in r["panels"] if p["failed"]]
            if drawn_failed or r["banners"]:
                fail(f"{name}: panel draw failure -> {r['banners'] or [p['id'] for p in drawn_failed]}")
            else:
                ok(f"{name}: no panel reported a draw failure")

            # 4. headline labels present as text. KPI labels render uppercase via CSS, so the
            # comparison is case-insensitive: this checks content, not letter case.
            body = page.inner_text("body").lower()
            must = {
                "cockpit": ["parts revenue", "target spend", "service families", "partner league",
                            "what this does not claim"],
                "ITUK": ["parts revenue", "target spend", "service families", "part-group risk",
                         "what this does not claim"],
                "SWEDEN": ["parts revenue", "target spend", "service families"],
                "BELGIUM": ["parts revenue", "target spend", "service families"],
            }[name]
            missing = [m for m in must if m not in body]
            if missing:
                fail(f"{name}: headline labels absent from the rendered page -> {missing}")
            else:
                ok(f"{name}: headline labels present ({len(must)})")

            # a euro sign and a percent sign must both render: the page is euro led
            if "€" not in body:
                fail(f"{name}: no euro figure rendered anywhere")
            else:
                ok(f"{name}: euro figures rendered")
            if "%" not in body:
                fail(f"{name}: no percentage rendered anywhere")
            else:
                ok(f"{name}: percentages rendered")

            # 5. contrast
            if r["contrast"]:
                fail(f"{name}: contrast problem -> {r['contrast'][:4]}")
            else:
                ok(f"{name}: no white-on-pale or dark-on-dark text")

            # 5b. clipping: this is the failure the review caught on the change bars.
            if r["clipped"]:
                fail(f"{name}: {len(r['clipped'])} clipped element(s) -> "
                     f"{[(c['sec'], c['cls'], c['dy'], c['text']) for c in r['clipped'][:4]]}")
            else:
                ok(f"{name}: no clipped text")

            # 5c. selectors must exist where a panel declares one, and must drive the panel.
            # Tested on a single-market view where one exists, because a multi-market panel has
            # one selector per market and the first one may not be the one that changes.
            sel = page.query_selector_all("select[id^='sel-']")
            if sel:
                s = sel[0]
                sid = s.get_attribute("id") or ""
                # id format is sel-<moduleId>-<key>, and a module id may contain a hyphen, so
                # the module is taken from the option's own redraw call rather than by splitting.
                mid = s.evaluate("""el => {
                  const m = (el.getAttribute('onchange') || '').match(/'([a-z_]+)'\\s*,/);
                  return m ? m[1] : '';
                }""")
                opts = s.eval_on_selector_all("option", "els => els.map(e => e.value)")
                if mid and len(opts) > 1:
                    before = page.inner_text(f"#mod-{mid}")
                    page.select_option(f"#{sid}", opts[-1])
                    page.wait_for_timeout(320)
                    after = page.inner_text(f"#mod-{mid}")
                    if after == before:
                        fail(f"{name}: selector on '{mid}' did not change the panel")
                    else:
                        ok(f"{name}: selector on '{mid}' changes the panel "
                           f"({len(opts)} options)")
                    page.select_option(f"#{sid}", opts[0])
                    page.wait_for_timeout(220)
                else:
                    fail(f"{name}: selector found but could not be identified")
            else:
                ok(f"{name}: no in-panel selector declared")

            # 5d. did every panel actually resolve its values?
            check_rendered_text(page, name, "customer" if name != "cockpit" else "internal")

            # 6. widths
            for w, h in WIDTHS:
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(320)
                ov = page.evaluate("""() => ({ c: document.documentElement.clientWidth,
                                               s: document.documentElement.scrollWidth })""")
                if ov["s"] > ov["c"] + 4:
                    fail(f"{name}: horizontal overflow at {w}px ({ov['s']} > {ov['c']})")
            ok(f"{name}: no horizontal overflow at {len(WIDTHS)} widths")

            # 7. screenshots for a human to look at: EVERY panel at desktop and phone width,
            # because the clipping failure mode is per-panel and cannot be inferred from a
            # full-page shot.
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.wait_for_timeout(350)
            page.screenshot(path=os.path.join(QA, f"{name}_top_1440.png"))
            page.screenshot(path=os.path.join(QA, f"{name}_full_1440.png"), full_page=True)
            for pid in panel_ids:
                el = page.query_selector(f"#sec-{pid}")
                if el:
                    el.screenshot(path=os.path.join(sweep, f"{name}_{pid}_1440.png"))
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(350)
            page.screenshot(path=os.path.join(QA, f"{name}_mobile_390.png"))
            for pid in panel_ids:
                el = page.query_selector(f"#sec-{pid}")
                if el:
                    el.screenshot(path=os.path.join(sweep, f"{name}_{pid}_390.png"))
            ok(f"{name}: {len(panel_ids) * 2} panel screenshots written to _qa/sweep/")
            ctx.close()
            print()

        br.close()

    print("=" * 72)
    for n in notes:
        print(n)
    print()
    if failures:
        print(f"QA FAILED with {len(failures)} problem(s):")
        for f in failures:
            print("  FAIL " + f)
        return 1
    print(f"PAINT_OK - {len(notes)} rendered checks passed, 0 failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
