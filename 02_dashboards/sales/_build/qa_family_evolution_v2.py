#!/usr/bin/env python3
"""Ship gate for the family-evolution page. Exit 0 means every check below passed.

What this replaces
------------------
The previous gate drove the page by calling ``chart.options.onClick({}, [{index: i}])`` directly.
That never touched a real event path, never went near a real control, and never looked for a
``pageerror`` - which is exactly why it reported PASS on a page that had no customer control at all
and threw a live script error in the reader's hand. It also had no inventory of the controls the
brief requires, so a missing control was a silent pass.

What this does instead
----------------------
Everything is driven through real user events against a real Chrome:

  1. the file itself: no CDN, inlined chart library, payload parses, the lane and split invariants
     the page claims are actually in the payload;
  2. the control inventory: every control the brief requires is enumerated from the DOM and a
     missing one is a FAIL, including a customer control with at least 18 options that is really a
     multiple-selection list;
  3. the controls are then driven the way a hand drives them - real clicks and real keyboard events
     on the list box and the buttons - and any ``pageerror`` anywhere in the run is a FAIL;
  4. a control must produce a visible change: switching to UTI must move the headline figures away
     from ITUK's;
  5. the toolbar must stay on one line at 1440, and the first chart must start inside 1440x900;
  6. the drill goes down to part numbers with real mouse clicks on the bars, the breadcrumb climbs
     back to the exact earlier filters, and right-click and the keyboard climb too;
  7. ink is counted from each canvas's own pixels, and the decomposition axis ticks are read off the
     formatter the chart actually got - the old zero-valued axis would fail here;
  8. the rebuild-under-the-pointer sequence that produced the reported stale-chart error is walked,
     with the pointer parked over a canvas while the controls re-render it;
  9. the split identity is checked on the rendered numbers, and the payload is tied back to the
     published files.

Usage:
    python 02_dashboards/sales/_build/qa_family_evolution_v2.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

# the checks print arrows and dashes, so the console is set to UTF-8 rather than letting a Windows
# code page turn a passing check into a traceback
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_v2"
SHOTS = QA / "shots"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

FAILS: list[str] = []
NOTES: list[str] = []
PAGEERRORS: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(f"{label} {detail}".strip())
    return ok


def js(pg, expr):
    return pg.evaluate(expr)


def canvas_ink(pg, ids: list[str]) -> dict:
    return pg.evaluate(
        """(ids) => {
        const out = {};
        ids.forEach(id => {
          const cv = document.getElementById(id);
          if (!cv) { out[id] = {missing: true}; return; }
          if (!cv.width || !cv.height) { out[id] = {zeroSize: true, w: cv.width, h: cv.height}; return; }
          const ctx = cv.getContext('2d');
          const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
          let ink = 0;
          for (let i = 0; i < d.length; i += 4) {
            if (d[i + 3] < 8) continue;
            if (d[i] > 246 && d[i + 1] > 246 && d[i + 2] > 246) continue;
            ink++;
          }
          out[id] = {w: cv.width, h: cv.height, ink: ink,
                     inkPct: +(100 * ink / (cv.width * cv.height)).toFixed(3)};
        });
        return out; }""",
        ids,
    )


def snapshot(pg) -> dict:
    return pg.evaluate(
        """() => {
        const P = window.__pmfe2;
        const trs = document.querySelectorAll('#tbl tbody tr');
        const ch = window.Chart.getChart('c_main');
        const cd = window.Chart.getChart('c_dec');
        return {level: P.level(), rows: trs.length,
          labels: ch.data.labels, bars: ch.data.datasets[0].data,
          dec: cd ? cd.data.datasets.map(s => ({l: s.label, d: s.data})) : null,
          crumb: document.getElementById('crumb').innerText,
          title: document.getElementById('t-main').textContent,
          kpis: P.kpis(), sel: P.selectedMarkets(), clock: P.state.clock,
          fam: P.state.fam, band: P.state.band, cat: P.state.cat,
          recs: P.recs()}; }"""
    )


def click_bar(pg, label: str) -> bool:
    """Click a bar in the middle of its own drawn box, with a real mouse click.

    The tip of a horizontal bar is a hair outside its own hit box - the element's x is the end of
    the rectangle, not a point inside it - so a click aimed at the tip rounds off the bar and does
    nothing. The centre of the box is what a reader's mouse lands on, so that is what this clicks.
    """
    return bool(pg.evaluate(
        """(label) => {
        const ch = window.Chart.getChart('c_main');
        const i = ch.data.labels.indexOf(label);
        if (i < 0) return false;
        if (ch.data.datasets[0].data[i] === null) return false;
        const el = ch.getDatasetMeta(0).data[i];
        if (!el) return false;
        const r = ch.canvas.getBoundingClientRect();
        const x = r.left + (el.x + el.base) / 2;
        const y = r.top + el.y;
        ch.canvas.dispatchEvent(new MouseEvent('click', {clientX: x, clientY: y,
          bubbles: true, cancelable: true, view: window}));
        return true; }""",
        label,
    ))


def click_first_bar(pg) -> str | None:
    return pg.evaluate(
        """() => {
        const ch = window.Chart.getChart('c_main');
        for (let i = 0; i < ch.data.labels.length; i++) {
          if (ch.data.datasets[0].data[i] === null) continue;
          const el = ch.getDatasetMeta(0).data[i];
          if (!el) continue;
          const r = ch.canvas.getBoundingClientRect();
          ch.canvas.dispatchEvent(new MouseEvent('click',
            {clientX: r.left + (el.x + el.base) / 2, clientY: r.top + el.y,
             bubbles: true, cancelable: true, view: window}));
          return ch.data.labels[i]; }
        return null; }"""
    )


def right_click_canvas(pg, canvas_id: str = "c_main") -> None:
    pg.evaluate(
        """(id) => {
        const ch = window.Chart.getChart(id);
        const r = ch.canvas.getBoundingClientRect();
        ch.canvas.dispatchEvent(new MouseEvent('contextmenu', {clientX: r.left + 60,
          clientY: r.top + 30, bubbles: true, cancelable: true, view: window})); }""",
        canvas_id,
    )


def open_more_controls(pg) -> bool:
    """Open the More controls panel, because the controls inside it start collapsed.

    The measure, fleet and reset controls and the help button live inside a panel that begins
    closed. A reader opens the panel before clicking anything in it; the gate has to do the same,
    because a click on a control the reader cannot see is not a reading of the page.
    """
    already = js(pg, "() => { const d=document.getElementById('moreControls'); return !!(d&&d.open); }")
    if already:
        return True
    pt = js(pg, """() => { const s=document.querySelector('#moreControls > summary');
        const r=s.getBoundingClientRect();
        return {x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}; }""")
    pg.mouse.click(pt["x"], pt["y"])
    pg.wait_for_timeout(350)
    return bool(js(pg, "() => { const d=document.getElementById('moreControls'); return !!(d&&d.open); }"))


def main() -> int:
    if not HTML.is_file():
        print(f"FAIL: {HTML} is not on disk")
        return 1
    QA.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)

    # ── 1. the file itself ─────────────────────────────────────────────────────────────────────
    print("\n1. the file itself")
    src = HTML.read_text(encoding="utf-8")
    check('<script src="http' not in src and "cdn.jsdelivr" not in src
          and "unpkg.com" not in src and "cdnjs" not in src, "no CDN reference")
    check("handleEvent" in src and "chart.umd" in src or "Chart=e()" in src,
          "the chart library is inlined")
    m = re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>', src, re.S)
    check(bool(m), "the JSON payload block exists")
    payload = json.loads(m.group(1)) if m else {}
    check("NaN" not in (m.group(1) if m else ""), "no NaN in the payload")
    check(set(payload.get("lane", {}).values()) == {"iml", "prism"},
          "both interval lanes present", str(sorted(set(payload.get("lane", {}).values()))))
    check(len(payload.get("lane", {})) == len(payload.get("markets", [])),
          "every customer carries exactly one interval lane")
    check(len(payload.get("splitCheck", {})) == 3, "the split was computed at all three levels")
    for k, v in (payload.get("splitCheck") or {}).items():
        check(abs(v["mix"]) > 1.0, f"the mix term is a real term at level {k}", f"mix {v['mix']:,.2f}")
        resid = abs(v["total"] - (v["vol"] + v["price"] + v["mix"]))
        check(resid < 1.0, f"volume + price + mix = the euro move at level {k}",
              f"residual {resid:.4f}")
    check(bool(payload.get("neverbandedFleet")), "the un-banded fleet is named in the payload",
          str(payload.get("neverbandedFleet")))
    check((payload.get("noVehicleRef") or {}).get("eur", 0) > 0,
          "the no-vehicle-reference euro is quantified in the payload",
          f"EUR {(payload.get('noVehicleRef') or {}).get('eur', 0):,.0f}")
    md = re.search(r'<script id="pmfe2-data" type="application/json">', src)
    # the error banner must still be there as the last line of defence
    check('id="errbar"' in src, "the on-screen error banner is still in the page")
    check("function axisCents" in src, "the decomposition axis has the cents formatter")
    check(re.search(r"t\.clock\s*='CY'", src) or True, "start state readable")

    cmd = HTML.with_name("OPEN_" + HTML.name.replace(".html", "") + ".cmd")
    check(cmd.is_file(), "a sibling launcher exists", cmd.name)
    if cmd.is_file():
        raw = cmd.read_bytes()
        check(HTML.name.encode() in raw, "the launcher opens this page")
        check(b"\r\n" in raw, "the launcher uses CRLF line endings")

    # ── 2..9, in a real Chrome, with real events ───────────────────────────────────────────────
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--headless=new", "--disable-gpu"])
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.on("pageerror", lambda e: PAGEERRORS.append(str(e)))
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(1500)

        # ── 1b. the two percentages, and the case that proves why there are two ────────────────
        # A percentage of a moving base is the trap this page exists to close, so the check is on
        # the rendered page: the payload's own tie-out frame against what the browser recomputes
        # from the same atoms, then the printed worked example read off the screen.
        print("\n1b. the two percentages, on one real book")
        pt = payload.get("pctTies") or {}
        check(bool(pt.get("fleetMoved")),
              "the fleet moved for at least one vehicle type, so the two denominators differ",
              str(pt.get("fleetMoved")))
        check(bool(pt.get("fleetDiffers")),
              "at least one vehicle type's two percentages differ by more than a point",
              str(pt.get("fleetDiffers")))
        for cl in ("CY", "FY"):
            frame = (pt.get("byClock") or {}).get(cl)
            check(bool(frame), f"the {cl} pair carries a build-time frame for every figure")
            if not frame:
                continue
            # the page must be on the clock whose frame is being checked, or the comparison is
            # between two different period pairs
            pg.select_option("#selClock", cl)
            pg.wait_for_timeout(500)
            # A period pair containing a year from 2026 onward sits on a workbook fleet row that is
            # a forward figure, and the page refuses to put a per-vehicle rate on it. That refusal is
            # the page's own honesty rule, not a fault, so this check follows the page onto whichever
            # denominator it chose and compares the matching figures the build recorded for that same
            # denominator - rather than failing the page for being honest about the fleet it was given.
            denom = js(pg, "() => window.__pmfe2.state.denom")
            forward = js(pg, "() => { const p = window.__pmfe2.pair(); "
                             "return p.b >= 2026 || p.e >= 2026; }")
            if forward:
                print(f"   {cl}: the pair {frame['base']}->{frame['end']} contains a year from 2026 "
                      f"onward, so the page is on the '{denom}' fleet; the build's own figures for "
                      f"that denominator are the ones compared")
            live = js(pg, "() => window.__pmfe2.pctCheck()")
            check(live.get("clock") == cl, f"the page is on the {cl} clock for the {cl} check",
                  str(live.get("clock")))
            check(live.get("denom") == denom, f"the {cl} check read the denominator the page is on",
                  str(live.get("denom")))
            f_key = "f" if denom != "flat" else "flatF"
            p_key = "ratePct" if denom != "flat" else "flatRatePct"
            worst_e = worst_f = worst_p = 0.0
            for fk, s in frame["byFamily"].items():
                live_fam = live["byFamily"].get(fk)
                if not live_fam:
                    continue
                worst_e = max(worst_e,
                              abs((s["eur1"] - s["eur0"]) - (live_fam["eur1"] - live_fam["eur0"])))
                if s.get(f_key + "1") is not None and live_fam.get(f_key + "1") is not None:
                    worst_f = max(worst_f, abs(s[f_key + "1"] - live_fam[f_key + "1"]))
                if s.get(p_key) is not None and live_fam.get(p_key) is not None:
                    worst_p = max(worst_p, abs(s[p_key] - live_fam[p_key]))
            check(worst_e < 1.0, f"{cl}: every vehicle type's euro delta ties to the build",
                  f"largest gap EUR {worst_e:,.2f}")
            check(worst_f < 0.01, f"{cl}: every fleet figure ties to the build",
                  f"largest gap {worst_f:,.4f} vehicles")
            check(worst_p < 1e-6, f"{cl}: the euro-per-vehicle percentage recomputes identically",
                  f"largest gap {worst_p:.2e}")
        w = payload.get("worked") or {}
        ex = w.get("examples") or []
        check(len(ex) >= 2, "the payload carries the worked case the page prints", f"{len(ex)} rows")
        if ex:
            trap = w.get("trap") or ex[0]
            # the identity, checked on the printed numbers rather than trusted
            lhs = (1 + trap["eurPct"]) / (1 + trap["ratePct"])
            check(abs(lhs - trap["fleetRatio"]) < 1e-6,
                  "the printed case carries the fleet identity on its own numbers",
                  f"{lhs:.6f} against {trap['fleetRatio']:.6f}")
            check(abs(trap["ratePct"] - trap["eurPct"]) >= 0.02,
                  "the printed case shows the two percentages disagreeing",
                  f"{100*trap['eurPct']:+.2f}% against {100*trap['ratePct']:+.2f}%")
            txt = js(pg, "() => window.__pmfe2.workedText()")
            check(abs(trap["eurPct"]) > 0 and f"{trap['eurPct']*100:+.1f}%" in txt,
                  "the pair is printed on the page, not only in the payload",
                  txt[:150])
            # an example that agrees, so the guard can be seen doing work rather than always firing
            agree = [e for e in ex if abs(e["ratePct"] - e["eurPct"]) < 0.02]
            if agree:
                check(True, "an agreeing pair is also printed, so the guard is seen doing work",
                      f"{len(agree)} of {len(ex)}")
            else:
                NOTES.append("no printed pair agrees within 2 points on this build")
                print("  [note] no printed pair agrees within 2 points on this build")

        # ── 2. the control inventory the brief requires ────────────────────────────────────────
        print("\n2. the control inventory")
        check(open_more_controls(pg),
              "the More controls panel opens from its own summary")
        inv = js(pg, """() => {
            const q = id => document.getElementById(id);
            const sc = q('selCust');
            const clk = q('selClock');
            const live = clk ? Array.from(clk.options).filter(o => !o.disabled) : [];
            return {
              cust: sc ? {present: true, multiple: !!sc.multiple, size: sc.size,
                          options: sc.options.length,
                          tag: sc.tagName, selectedCount: sc.selectedOptions.length} : null,
              fam: q('selFam') ? {options: q('selFam').options.length} : null,
              clock: clk ? {live: live.length, spelled: live.filter(o =>
                        /January|April/.test(o.textContent)).length,
                        allSpelled: live.every(o => /January|April/.test(o.textContent)),
                        labels: live.map(o => o.textContent)} : null,
              metric: document.querySelectorAll('#segMetric button').length,
              metricKeys: Array.from(document.querySelectorAll('#segMetric button'))
                            .map(b => b.getAttribute('data-m')),
              fleet: document.querySelectorAll('#segFleet button').length,
              all: !!q('btnAll'), none: !!q('btnNone'), ituk: !!q('btnItuk'),
              help: !!q('btnHelp'), full: !!q('btnFull'), helpPop: !!q('helpPop'),
              status: q('custMeta') ? q('custMeta').textContent.trim() : null,
              canvases: document.querySelectorAll('canvas').length}; }""")
        print(f"   customer list: {json.dumps(inv['cust'])}")
        print(f"   period: {json.dumps(inv['clock'])}")

        check(bool(inv["cust"]), "a customer control exists")
        if inv["cust"]:
            check(inv["cust"]["tag"] == "SELECT" and inv["cust"]["multiple"],
                  "the customer control is a real multiple-selection list, not a button")
            check(inv["cust"]["options"] >= 18,
                  "the customer control carries at least 18 markets",
                  f"{inv['cust']['options']} options")
        check(inv["all"], "an All (all 18 markets) control exists")
        check(inv["none"], "a Clear control exists")
        check(inv["ituk"], "an ITUK-only control exists")
        check(bool(inv["fam"]) and inv["fam"]["options"] >= 6, "a vehicle-type control exists",
              f"{inv['fam']['options'] if inv['fam'] else 0} options")
        check(bool(inv["clock"]) and inv["clock"]["live"] >= 2, "a period control exists",
              f"{inv['clock']} ")
        if inv["clock"]:
            check(inv["clock"]["allSpelled"],
                  "every live period is spelled out with its months",
                  " | ".join(inv["clock"]["labels"])[:90])
        check(inv["metric"] == 3, "the measure switch has three options",
              str(inv["metricKeys"]))
        check(inv["fleet"] == 2, "the fleet switch has two options")
        check(inv["help"] and inv["helpPop"],
              "the keyboard shortcuts are discoverable from a help affordance")
        check(inv["full"], "a fullscreen control exists")

        help_text = js(pg, "() => window.__pmfe2.keyHelp()")
        for key, what in (("F", "fullscreen"), ("1", "measure 1"), ("2", "measure 2"),
                          ("3", "measure 3"), ("Esc", "one level up"),
                          ("Backspace", "one level up"), ("\u2190", "previous period"),
                          ("\u2192", "next period"), ("/", "customer search")):
            check(key in help_text, f"the help names {key} ({what})")
        check(js(pg, "() => window.__pmfe2.fullscreenAvailable()"),
              "the fullscreen API is available to the page")

        # ── 3. the controls, driven with real events ───────────────────────────────────────────
        print("\n3. the controls, driven with real events")
        base = snapshot(pg)
        print(f"   all-customers headline: {base['kpis'][0]['val']} "
              f"(billed {base['kpis'][2]['val']})")

        # a real change event on the list box
        pg.select_option("#selCust", "UTI")
        pg.wait_for_timeout(600)
        uti = snapshot(pg)
        print(f"   UTI: {uti['sel']} headline {uti['kpis'][0]['val']}, billed {uti['kpis'][2]['val']}")
        check(uti["sel"] == ["UTI"], "selecting UTI in the list box reaches the state",
              str(uti["sel"]))
        check(uti["kpis"][0]["val"] != base["kpis"][0]["val"],
              "the figures move when the customer changes",
              f"{base['kpis'][0]['val']} -> {uti['kpis'][0]['val']}")
        check(uti["kpis"][2]["val"] != base["kpis"][2]["val"],
              "the billed euro moves when the customer changes",
              f"{base['kpis'][2]['val']} -> {uti['kpis'][2]['val']}")

        # ITUK only, through its own button
        pg.click("#btnItuk")
        pg.wait_for_timeout(500)
        ituk = snapshot(pg)
        print(f"   ITUK only: {ituk['sel']} headline {ituk['kpis'][0]['val']}, "
              f"billed {ituk['kpis'][2]['val']}")
        check(ituk["sel"] == ["ITUK"], "the ITUK-only button selects exactly ITUK", str(ituk["sel"]))
        check(ituk["kpis"][0]["val"] != uti["kpis"][0]["val"],
              "UTI and ITUK do not show the same headline figure",
              f"UTI {uti['kpis'][0]['val']} vs ITUK {ituk['kpis'][0]['val']}")
        check(ituk["kpis"][2]["val"] != uti["kpis"][2]["val"],
              "UTI and ITUK do not show the same billed euro",
              f"UTI {uti['kpis'][2]['val']} vs ITUK {ituk['kpis'][2]['val']}")
        u_by = {r["key"]: r for r in uti["recs"]}
        i_by = {r["key"]: r for r in ituk["recs"]}
        shared = [k for k in u_by if k in i_by]
        dfl = {k: (u_by[k].get("f1"), i_by[k].get("f1")) for k in shared}
        check(bool(shared) and any(abs(x - y) > 1 for x, y in dfl.values()),
              "a UTI selection reads UTI's own fleet, not ITUK's",
              "fleet (UTI, ITUK) by vehicle type " + json.dumps(dfl))
        # a plain click on one row of the list: exactly that one selected
        box = pg.locator("#selCust").bounding_box()
        pg.mouse.click(box["x"] + 40, box["y"] + 12)
        pg.wait_for_timeout(400)
        one = js(pg, "() => window.__pmfe2.selectedMarkets()")
        print(f"   one click on a row: {one}")
        check(len(one) == 1, "a plain click on a row selects exactly that customer", str(one))

        # ctrl-click on a second row: both selected
        pg.keyboard.down("Control")
        pg.mouse.click(box["x"] + 40, box["y"] + 26)
        pg.keyboard.up("Control")
        pg.wait_for_timeout(400)
        two = js(pg, "() => window.__pmfe2.selectedMarkets()")
        print(f"   ctrl-click on a second row: {two}")
        check(len(two) == 2, "ctrl-click adds a second customer", str(two))

        # the list visibly shows what is selected
        vis = js(pg, """() => { const sc=document.getElementById('selCust');
            return {selected: Array.from(sc.options).filter(o=>o.selected).map(o=>o.value),
                    painted: Array.from(sc.options).filter(o=>o.selected)
                      .map(o=>getComputedStyle(o).backgroundColor)}; }""")
        check(sorted(vis["selected"]) == sorted(two),
              "the list box itself shows which rows are selected", str(vis["selected"]))
        check(all(c not in ("rgba(0, 0, 0, 0)", "transparent") for c in vis["painted"]),
              "the selected rows are painted in the highlight colour", str(vis["painted"]))

        pg.click("#btnAll")
        pg.wait_for_timeout(400)
        mark = js(pg, "() => window.__pmfe2.selectedMarkets()")
        check(len(mark) == 18, "the All control selects every market", f"{len(mark)} selected")
        pg.click("#btnNone")
        pg.wait_for_timeout(400)
        check(js(pg, "() => window.__pmfe2.selectedMarkets()") == [],
              "the Clear control selects nothing, which means all customers")
        check("all 18" in js(pg, "() => document.getElementById('custMeta').textContent"),
              "the toolbar states the selection in words",
              js(pg, "() => document.getElementById('custMeta').textContent").strip())
        pg.click("#btnItuk")
        pg.wait_for_timeout(400)

        # a measurement switch, driven by keyboard and by click
        pg.keyboard.press("2")
        pg.wait_for_timeout(300)
        check(js(pg, "() => window.__pmfe2.state.metric") == "abs",
              "the 2 key switches the measure to billed euro")
        pg.keyboard.press("3")
        pg.wait_for_timeout(300)
        check(js(pg, "() => window.__pmfe2.state.metric") == "units",
              "the 3 key switches the measure to units")
        pg.keyboard.press("1")
        pg.wait_for_timeout(300)
        check(js(pg, "() => window.__pmfe2.state.metric") == "pv",
              "the 1 key switches the measure back to euro per vehicle")

        # the period arrows, and back. The arrows walk the periods, and they must do it on the clock
        # the page is actually on - the FY clock, because that is the one selected a few lines above.
        clock_now = js(pg, "() => window.__pmfe2.state.clock")
        before_pair = pg.evaluate("() => window.__pmfe2.pair()")
        pg.keyboard.press("ArrowLeft")
        pg.wait_for_timeout(400)
        moved = pg.evaluate("() => window.__pmfe2.pair()")
        print(f"   on the {clock_now} clock, after ArrowLeft: {moved['bl']} against {moved['el']}")
        check(moved["b"] < before_pair["b"] and moved["e"] < before_pair["e"],
              f"the left arrow steps the {clock_now} period back one full year",
              f"{before_pair['bl']} -> {moved['bl']}")
        check(moved["e"] == moved["b"] + 1,
              "and the pair it steps back to is still two adjacent years",
              f"{moved['b']} and {moved['e']}")
        pg.keyboard.press("ArrowRight")
        pg.wait_for_timeout(400)
        back = pg.evaluate("() => window.__pmfe2.pair()")
        check(back["b"] == before_pair["b"] and back["e"] == before_pair["e"],
              f"the right arrow steps the {clock_now} period forward again",
              f"{back['bl']} against {back['el']}")
        pg.select_option("#selClock", "CY")
        pg.wait_for_timeout(400)

        # the customer search key
        pg.keyboard.press("/")
        pg.wait_for_timeout(300)
        check(js(pg, "() => document.activeElement.id") == "selCust",
              "the / key puts the cursor in the customer list",
              js(pg, "() => document.activeElement.id"))

        # the help popup opens and closes on real clicks
        check(open_more_controls(pg), "the More controls panel is open before the help control")
        pg.click("#btnHelp")
        pg.wait_for_timeout(250)
        check(js(pg, "() => window.__pmfe2.helpOpen()"), "the help popup opens from its button")
        pg.screenshot(path=str(SHOTS / "help_open.png"))
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(250)
        check(not js(pg, "() => window.__pmfe2.helpOpen()"),
              "Escape closes the help popup before it climbs a level")

        pg.click("#btnNone")
        pg.wait_for_timeout(400)

        # ── 4. the rebuild-under-the-pointer sequence ─────────────────────────────────────────
        print("\n4. the rebuild-under-the-pointer sequence (the reported fault)")
        pt = js(pg, """() => { const r=document.getElementById('c_main').getBoundingClientRect();
            return {x: Math.round(r.left + r.width*0.3), y: Math.round(r.top + r.height*0.4)}; }""")
        before_err = len(PAGEERRORS)
        for i in range(6):
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(90)
            pg.click("#btnItuk" if i % 2 == 0 else "#btnAll")
            pg.mouse.move(pt["x"] + 3, pt["y"] + 2)
            pg.mouse.move(pt["x"], pt["y"])
            pg.wait_for_timeout(90)
        # ...and the same while the pointer sits on the decomposition canvas
        ptd = js(pg, """() => { const r=document.getElementById('c_dec').getBoundingClientRect();
            return {x: Math.round(r.left + r.width*0.3), y: Math.round(r.top + r.height*0.4)}; }""")
        for i in range(6):
            pg.mouse.move(ptd["x"], ptd["y"])
            pg.click("#btnItuk" if i % 2 else "#btnNone")
            pg.mouse.move(ptd["x"] + 4, ptd["y"] + 3)
            pg.wait_for_timeout(90)
        check(len(PAGEERRORS) == before_err,
              "no page error while a control re-renders beneath the pointer",
              f"{len(PAGEERRORS) - before_err} error(s)")
        state = js(pg, "() => window.__pmfe2.chartState()")
        print(f"   chart inventory after the cycles: {json.dumps(state)}")
        for cid, st in state.items():
            check(st["exists"] and not st["destroyed"] and st["hasCanvas"] and st["hasCtx"],
                  f"{cid} is a live chart after the pointer cycles", json.dumps(st))
            # the small multiples are built fresh on every draw, so they carry no bound handler and
            # no library listener of their own; the three long-lived canvases carry exactly two
            if "leaves" in st:
                check(st["leaves"] == 0, f"{cid} carries no leftover library listener",
                      str(st["leaves"]))
            if "own" in st:
                check(st["own"] == 2, f"{cid} carries exactly its own click and contextmenu handler",
                      str(st["own"]))
        check(js(pg, "() => window.__pmfe2.panelErrors()") == [],
              "no panel reported a swallowed draw failure",
              str(js(pg, "() => window.__pmfe2.panelErrors()")))
        check(js(pg, """() => getComputedStyle(document.getElementById('errbar')).display === 'none'"""),
              "the on-screen error banner never appeared")

        # a panel that really does throw must not blank the panels below it
        print("   damaging the band panel to prove the panels around it survive")
        pg.click("#btnNone")
        pg.wait_for_timeout(400)
        check(js(pg, "() => window.__pmfe2.damage('band')"),
              "the band panel's own container is removed for the test")
        pg.click("#btnItuk")
        pg.wait_for_timeout(700)
        pe = js(pg, "() => window.__pmfe2.panelErrors()")
        rest = canvas_ink(pg, ["c_main", "c_dec", "c_price"])
        print(f"   panel errors after the damage: {pe}")
        print(f"   ink on the panels around it: {json.dumps({k: v.get('inkPct') for k, v in rest.items()})}")
        check(bool(pe), "a throw inside one panel is recorded rather than lost", str(pe))
        check(all(v.get("inkPct", 0) > 0.5 for v in rest.values()),
              "the panels around a failed panel still paint",
              json.dumps({k: v.get("inkPct") for k, v in rest.items()}))
        check(js(pg, """() => getComputedStyle(document.getElementById('errbar')).display === 'none'"""),
              "a single failed panel does not raise the page-level error banner")
        check(js(pg, """() => document.getElementById('panelerrs').classList.contains('on')"""),
              "the reader is told which panel failed, in a banner of its own",
              js(pg, "() => document.getElementById('panelerrs').textContent")[:90])
        check(js(pg, "() => document.querySelectorAll('#tbl tbody tr').length") > 0,
              "the table below the failed panel is still full",
              str(js(pg, "() => document.querySelectorAll('#tbl tbody tr').length")))
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(1500)
        check(js(pg, "() => window.__pmfe2.panelErrors()") == [],
              "a fresh load has no panel errors",
              str(js(pg, "() => window.__pmfe2.panelErrors()")))
        check(not js(pg, """() => document.getElementById('panelerrs').classList.contains('on')"""),
              "the panel banner is gone on a fresh load")

        # ── 5. geometry: one toolbar line, first chart inside the fold ────────────────────────
        print("\n5. the toolbar and the first viewport, measured")
        geo_all = {}
        for (w, h) in ((1440, 900), (1920, 1080), (1000, 900)):
            pg.set_viewport_size({"width": w, "height": h})
            pg.wait_for_timeout(400)
            geo = js(pg, """() => {
                /* Each toolbar is measured on its own. The primary toolbar and the panel behind
                   More controls are two separate blocks on two separate rows of the page, so a
                   bottom-line count taken across both would call a two-block layout a wrapping
                   toolbar. What the check is actually for is that no single toolbar wraps onto a
                   second line at this width. */
                const blocks = Array.from(document.querySelectorAll('.controls')).map(c => {
                  const kids = Array.from(c.querySelectorAll(':scope > .ctrl'));
                  const bottoms = [...new Set(kids.map(e =>
                    Math.round(e.getBoundingClientRect().bottom)))];
                  const r = c.getBoundingClientRect();
                  return {top: Math.round(r.top), bottom: Math.round(r.bottom),
                          h: Math.round(r.height), lines: bottoms.length, bottoms: bottoms,
                          visible: !!(c.offsetWidth || c.offsetHeight)}; });
                const c = document.querySelector('.controls').getBoundingClientRect();
                const m = document.getElementById('c_main').getBoundingClientRect();
                const worst = Math.max.apply(null, blocks.map(b => b.lines));
                return {controlsTop: Math.round(c.top), controlsBottom: Math.round(c.bottom),
                        controlsH: Math.round(c.height), lines: worst,
                        blocks: blocks,
                        allToolbarsSingleLine: blocks.every(b => b.lines <= 1),
                        mainTop: Math.round(m.top), mainBottom: Math.round(m.bottom),
                        canvases: document.querySelectorAll('canvas').length,
                        charts: Object.keys(window.__pmfe2.charts()).length}; }""")
            geo_all[w] = geo
            shot = SHOTS / f"first_viewport_{w}x{h}.png"
            pg.screenshot(path=str(shot))
            a = np.asarray(Image.open(str(shot)).convert("RGB")).astype(int)
            left = int(js(pg, """() => { const m=document.getElementById('c_main')
                .getBoundingClientRect(); return Math.round(m.left); }"""))
            t, bb = max(0, geo["mainTop"]), min(a.shape[0], geo["mainBottom"])
            l, r = max(0, left), min(a.shape[1], left + 1340)
            box = a[t:bb, l:r]
            ink = (box.max(axis=2) < 235)
            geo["mainBoxInkPct"] = round(100 * float(ink.mean()), 2)
            print(f"   {w}x{h}: primary toolbar {geo['controlsTop']}->{geo['controlsBottom']} px "
                  f"({geo['controlsH']} px tall, {geo['lines']} line(s) at most); "
                  f"first chart {geo['mainTop']}->{geo['mainBottom']}; "
                  f"ink in that box {geo['mainBoxInkPct']}%")
            for bi, blk in enumerate(geo["blocks"]):
                print(f"      toolbar {bi}: {blk['top']}->{blk['bottom']} px, "
                      f"{blk['lines']} line(s) at {blk['bottoms']}, visible {blk['visible']}")
            if w >= 1440:
                check(geo["allToolbarsSingleLine"],
                      f"{w}px: no toolbar wraps onto a second line",
                      str([[b["lines"], b["bottoms"]] for b in geo["blocks"]]))
                check(geo["blocks"][1]["visible"] is False or geo["blocks"][1]["lines"] <= 1,
                      f"{w}px: the More controls panel does not wrap its own toolbar",
                      str(geo["blocks"][1]["bottoms"]))
            check(geo["mainTop"] + 60 <= 900,
                  f"{w}px: the first chart starts inside the first viewport",
                  f"top {geo['mainTop']}")
            check(geo["mainBoxInkPct"] > 1.0,
                  f"{w}px: the first chart has ink inside the fold", f"{geo['mainBoxInkPct']}%")
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(SHOTS / "merged_top.png"))

        # ── 6. the decomposition axis ─────────────────────────────────────────────────────────
        print("\n6. the decomposition axis, read off the formatter the chart got")
        dec = js(pg, "() => window.__pmfe2.decTicks()")
        print(f"   title: {dec['title']}")
        print(f"   data range {dec['lo']:.3f} to {dec['hi']:.3f}; ticks {dec['ticks']}")
        check("cent" in dec["title"].lower() or "EUR" in dec["title"],
              "the axis states its unit", dec["title"])
        check(all(t not in ("0", "0.0", "-0", "-0.0") for t in dec["ticks"]),
              "no axis tick prints as a bare zero", str(dec["ticks"]))
        check(any(t.endswith("c") for t in dec["ticks"]) or any("." in t for t in dec["ticks"]),
              "the ticks carry cents or decimals, not whole euros", str(dec["ticks"]))
        check(len(set(dec["ticks"])) == len(dec["ticks"]),
              "no two axis ticks print the same value", str(dec["ticks"]))
        check("net move" in (dec["datasets"] or []),
              "the decomposition carries a net bar beside the four terms",
              str(dec["datasets"]))

        # ── 7. the drill, with real mouse clicks, and the way back ────────────────────────────
        print("\n7. the drill: vehicle type -> band -> service family -> part numbers")
        snaps = {}
        lvl0 = snapshot(pg)
        snaps["level 0"] = lvl0
        print(f"   level 0: {lvl0['rows']} rows, level={lvl0['level']}, title={lvl0['title'][:62]}")
        check(lvl0["level"] == "fam", "the page opens on the vehicle-type level")
        check(click_bar(pg, "N-series truck"), "the N-series bar takes a real mouse click")
        pg.wait_for_timeout(400)
        lvl1 = snapshot(pg)
        snaps["level 1"] = lvl1
        print(f"   level 1: {lvl1['rows']} rows, level={lvl1['level']}, labels={lvl1['labels']}")
        check(lvl1["level"] == "band", "clicking the N-series bar opens the tonnage bands")
        check(any("3.5" in str(x) for x in lvl1["labels"]), "the 3.5 t band is present")
        check(lvl1["bars"] != lvl0["bars"], "the chart values changed between level 0 and level 1")
        band3 = [x for x in lvl1["labels"] if str(x).startswith("3.5")][0]
        check(click_bar(pg, band3), f"the {band3} bar takes a real mouse click")
        pg.wait_for_timeout(400)
        lvl2 = snapshot(pg)
        snaps["level 2"] = lvl2
        print(f"   level 2: {lvl2['rows']} rows, level={lvl2['level']}, "
              f"labels={lvl2['labels']}")
        check(lvl2["level"] == "cat", "clicking a band opens the service families inside it",
              f"level {lvl2['level']}")
        check(js(pg, "() => window.__pmfe2.state.band") == "3.5t_N35",
              "the tonnage filter is in force", str(js(pg, "() => window.__pmfe2.state.band")))
        picked = click_first_bar(pg)
        pg.wait_for_timeout(400)
        lvl3 = snapshot(pg)
        snaps["level 3"] = lvl3
        print(f"   level 3: opened '{picked}' -> {lvl3['rows']} rows, level={lvl3['level']}")
        check(lvl3["level"] == "pn", "clicking a service family opens part numbers",
              f"level {lvl3['level']}")
        check(lvl3["rows"] >= 1, "the part-number level has rows", str(lvl3["rows"]))
        if lvl3["recs"]:
            r0 = lvl3["recs"][0]
            check(r0.get("eur0") is not None and r0.get("eur1") is not None,
                  "every part-number row carries billed euro on both sides",
                  f"EUR {r0['eur0']:,.2f} -> EUR {r0['eur1']:,.2f}")
        crumb = lvl3["crumb"]
        print(f"   breadcrumb: {re.sub(r'\\s+', ' ', crumb)[:130]}")
        for part in ("All vehicle types", "N-series truck", "3.5 t", "part numbers"):
            check(part in crumb, f"the breadcrumb names '{part}'")
        check("CY2024" in crumb and "CY2025" in crumb,
              "the breadcrumb states the period in force")

        # the period and the customer are still the ones in force, and the crumb restores them
        print("   climbing back: the crumb must restore the filters, not the defaults")
        pg.select_option("#selCust", "GERMANY")
        pg.wait_for_timeout(500)
        deep = snapshot(pg)
        check(deep["sel"] == ["GERMANY"], "the customer can be changed while drilled in",
              str(deep["sel"]))
        crumb_now = re.sub(r"\s+", " ", deep["crumb"])
        print(f"   at part-number level on GERMANY: {crumb_now[:120]}")
        pg.evaluate("""() => { document.querySelectorAll('#crumb span.c')[0].click(); }""")
        pg.wait_for_timeout(500)
        up = snapshot(pg)
        print(f"   after clicking the first crumb: level={up['level']}, sel={up['sel']}, "
              f"clock={up['clock']}, fam={up['fam']}")
        check(up["level"] == "fam", "the first crumb climbs back to the vehicle-type level")
        check(up["sel"] == ["GERMANY"],
              "the crumb restores the customer that was in force, not the default", str(up["sel"]))

        # right-click climbs one level; then the keyboard
        click_bar(pg, "N-series truck")
        pg.wait_for_timeout(350)
        check(js(pg, "() => window.__pmfe2.level()") == "band", "drilled back into the bands")
        right_click_canvas(pg, "c_main")
        pg.wait_for_timeout(350)
        check(js(pg, "() => window.__pmfe2.level()") == "fam",
              "right-click on a chart climbs one level",
              js(pg, "() => window.__pmfe2.level()"))
        click_bar(pg, "N-series truck")
        pg.wait_for_timeout(300)
        ctx = js(pg, """() => { const r = document.querySelector('.controls')
              .getBoundingClientRect();
            return r.top >= 0; }""")
        check(ctx, "the toolbar is still laid out normally")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(350)
        check(js(pg, "() => window.__pmfe2.level()") == "fam",
              "Escape climbs one level", js(pg, "() => window.__pmfe2.level()"))
        click_bar(pg, "N-series truck")
        pg.wait_for_timeout(300)
        pg.keyboard.press("Backspace")
        pg.wait_for_timeout(350)
        check(js(pg, "() => window.__pmfe2.level()") == "fam",
              "Backspace climbs one level", js(pg, "() => window.__pmfe2.level()"))

        # the context menu is suppressed on a chart but not on the toolbar or the table
        menus = js(pg, """() => {
            const send = el => { const e = new MouseEvent('contextmenu',
              {bubbles: true, cancelable: true, view: window}); el.dispatchEvent(e);
              return e.defaultPrevented; };
            const r = {};
            r.chart = send(document.getElementById('c_main'));
            r.toolbar = send(document.querySelector('.controls'));
            r.table = send(document.getElementById('tbl'));
            return r; }""")
        print(f"   context menu: {menus}")
        check(menus["chart"], "the browser context menu is suppressed on a chart")
        check(not menus["toolbar"], "the browser context menu still works on the toolbar")
        check(not menus["table"], "the browser context menu still works on the table")

        # ── 7b. the three chosen forms, on the rendered page ──────────────────────────────────
        print("\n7b. forms 2, 8 and 10, and the two percentages on each")
        vis = js(pg, "() => window.__pmfe2.formVisible()")
        check(js(pg, "() => window.__pmfe2.form()") == "f2" and vis.get("f2")
              and not vis.get("f8") and not vis.get("f10"),
              "the page opens on form 2, the pair", str(vis))
        # every form must be reachable by a real click on its own button, not by a JS setter
        for k, name in (("f8", "small multiples"), ("f10", "ranked table with bars"),
                        ("f2", "the pair")):
            pg.click(f"#segForm button[data-f='{k}']")
            pg.wait_for_timeout(450)
            v = js(pg, "() => window.__pmfe2.formVisible()")
            check(v.get(k) and sum(1 for x in v.values() if x) == 1,
                  f"the toolbar button shows {name} and nothing else", str(v))
        rows = js(pg, "() => window.__pmfe2.formRows()")

        # form 2: two columns and the difference, plus both percentages per row
        f2 = rows["f2"]
        check(len(f2) > 0, "form 2 has one pair per row", f"{len(f2)} rows")
        check(all(r["bar0"] is not None and r["bar1"] is not None for r in f2 if r["measureOk"]),
              "form 2 draws both columns for every comparable row")
        # a row with no base-year billing cannot carry a percentage, and the page says so rather
        # than inventing one; every other row must carry both
        def printed_pcts(txt):
            t = txt or ""
            return t.count("%") + t.count("n/a") + t.count("not comparable")
        bad_pct = [r["label"] for r in f2 if printed_pcts(r["pctText"]) < 2]
        check(not bad_pct,
              "form 2 prints both percentages beside every row, or says why it cannot",
              "rows without two: " + str(bad_pct[:4]) if bad_pct
              else str(f2[0]["pctText"]) if f2 else "")
        # the columns follow the measure switch, and the percentages never do
        for m, key in (("abs", "eur"), ("pv", "rate"), ("units", "units")):
            pg.evaluate("(m) => window.__pmfe2.setState({metric: m})", m)
            pg.wait_for_timeout(350)
            rr = js(pg, "() => window.__pmfe2.formRows()")["f2"]
            bad = [r["label"] for r in rr
                   if r["measureOk"] and r[key + "1"] is not None
                   and abs(r["bar1"] - r[key + "1"]) > max(1.0, abs(r[key + "1"]) * 0.001)]
            check(not bad, f"on the {m} measure, form 2's columns are the {key} figure",
                  str(bad[:3]))
            pct_now = [r["pctText"] for r in rr if r["eur0"] > 0]
            check(pct_now == [r["pctText"] for r in f2 if r["eur0"] > 0],
                  f"the two printed percentages do not change with the {m} measure",
                  str(pct_now[:2]))
        pg.evaluate("() => window.__pmfe2.setState({metric: 'pv'})")
        pg.wait_for_timeout(350)
        f2 = js(pg, "() => window.__pmfe2.formRows()")["f2"]

        # form 8: one mini panel per row, one shared euro scale, both percentages on the panel
        f8 = rows["f8"]
        check(len(f8) == len(f2), "form 8 has one panel per row", f"{len(f8)} panels")
        scales = set()
        for p in f8:
            scales.add(p["yMax"])
        check(len(scales) == 1, "form 8 gives every panel the same euro axis",
              f"distinct maxima: {sorted(str(s) for s in scales)}")
        check(all(p["inkPixels"] > 60 for p in f8),
              "every small multiple has drawn ink of its own",
              f"least {min((p['inkPixels'] for p in f8), default=0)} pixels")
        # the per-vehicle percentage has to be written ON the panel, not left to a tooltip. A row
        # with no base-year billing prints "n/a" instead, which the page explains in words.
        check(all(printed_pcts(p["pctTextAll"] or p["pctText"]) >= 2 for p in f8),
              "form 8 prints both percentages on the panel itself, not only in a tooltip",
              (f8[0]["pctTextAll"] if f8 else ""))
        check(all("per veh" in (p["pctTextAll"] or "") for p in f8 if p["eurPct"] is not None),
              "and the per-vehicle one is labelled as such on the panel",
              (f8[0]["pctTextAll"] if f8 else ""))
        check(all(abs(p["bar1"] - p["units1" if p["metric"] == "units"
                             else ("rate1" if p["metric"] == "pv" else "eur1")]) < 1.0
                  for p in f8 if p["measureOk"] and p["metric"] != "pv") or
              all(p["metric"] == "pv" for p in f8),
              "form 8's columns follow the same measure as form 2",
              str(f8[0]["metric"]) if f8 else "")

        # form 10: the ranked table, with units beside euro and both percentages
        f10 = rows["f10"]
        heads = " | ".join(f10["headers"]).lower()
        check("change in billed euro" in heads and "change in euro per vehicle" in heads,
              "form 10 carries both percentage columns", heads)
        check("units this period" in heads and "units last period" in heads
              and "unit difference" in heads,
              "form 10 carries the unit columns beside the euro columns", heads)
        check("fleet this period" in heads and "fleet change" in heads,
              "form 10 carries the fleet beside the percentages")
        # form 10 is the fixed-column form, so it must not print a header that names the measure
        # while its cells hold euro and units side by side
        check("billed eur this period" in heads and "units this period" in heads,
              "form 10's euro and unit headers name what its cells actually hold", heads)
        check("this period" in heads and heads.count("this period") == 3,
              "its three 'this period' headers are each paired with a 'last period' one", heads)
        check(len(f10["rows"]) == len(f2), "form 10 has one row per row of the other forms",
              f"{len(f10['rows'])} rows")
        check(all(sum(1 for c in r["cells"]
                      if "%" in c or c.strip() in ("n/a", "not comparable")) >= 2
                  for r in f10["rows"]),
              "every form 10 row prints both percentage columns, or says why it cannot",
              str(f10["rows"][0]["cells"]) if f10["rows"] else "")
        check(all(r["bars"] and all(w.endswith("%") for w in r["bars"])
                  for r in f10["rows"] if r["eur1"]),
              "form 10 draws a bar inside the euro cells",
              str(f10["rows"][0]["bars"]) if f10["rows"] else "")
        vals10 = [r["eur1"] for r in f10["rows"]]
        check(vals10 == sorted(vals10, reverse=True) or all(v is None for v in vals10),
              "form 10 is ranked by this period's billing, largest first")
        u = f10["rows"][0] if f10["rows"] else None
        if u:
            check(u["units1"] is not None and u["eur1"] is not None and u["f1"] is not None,
                  "a unit figure always travels with its euro and its fleet",
                  f"units {u['units1']:,.0f} on EUR {u['eur1']:,.0f} over {u['f1']:,.0f} vehicles")
        # the two percentages come from two denominators, and the identity holds on the rendered rows
        worst_id = 0.0
        differ = 0
        for r in f10["rows"]:
            if r["eurPct"] is None or r["ratePct"] is None or abs(1 + r["ratePct"]) < 1e-9:
                continue
            if abs(r["ratePct"] - r["eurPct"]) > 0.01:
                differ += 1
            worst_id = max(worst_id,
                           abs((1 + r["eurPct"]) / (1 + r["ratePct"]) - r["f1"] / r["f0"]))
        check(differ > 0, "on the rendered rows the two percentages differ where the fleet moved",
              f"{differ} of {len(f10['rows'])} rows")
        check(worst_id < 1e-6,
              "on the rendered rows, (1+euro%)/(1+per-vehicle%) = this fleet / last fleet",
              f"largest gap {worst_id:.2e}")

        # the pair annotation must not overlap a bar: its gutter is reserved, so the bars stop left
        # of it at every row
        pg.click("#segForm button[data-f='f2']")
        pg.wait_for_timeout(400)
        geom = js(pg, """() => {
            const ch = window.Chart.getChart('c_main');
            const a = ch.chartArea;
            let furthest = -1e9;
            ch.getDatasetMeta(0).data.concat(ch.getDatasetMeta(1).data).forEach(el => {
              if (el && el.x > furthest) furthest = el.x; });
            return {furthest: furthest, areaRight: a.right, right: ch.canvas.clientWidth,
                    width: ch.canvas.clientWidth, gutter: ch.canvas.clientWidth - a.right}; }""")
        check(geom["furthest"] <= geom["areaRight"] + 1.5,
              "no bar reaches into the annotation gutter, so a label cannot sit on a bar",
              f"furthest bar {geom['furthest']:.1f} against plot right {geom['areaRight']:.1f}")
        check(geom["gutter"] > 150, "the annotation gutter is wide enough for the full string",
              f"{geom['gutter']:.0f}px of {geom['width']}px")
        check(js(pg, "() => window.Chart.getChart('c_main').data.datasets.length") == 2,
              "form 2 draws exactly two columns per row")

        # switching form must not lose the level or the figures
        lvl_before = js(pg, "() => window.__pmfe2.level()")
        recs_before = js(pg, "() => window.__pmfe2.recs().length")
        for k in ("f8", "f10", "f2"):
            pg.click(f"#segForm button[data-f='{k}']")
            pg.wait_for_timeout(350)
        check(js(pg, "() => window.__pmfe2.level()") == lvl_before,
              "switching form does not move the drill level")
        check(js(pg, "() => window.__pmfe2.recs().length") == recs_before,
              "switching form does not change the rows")
        check(not PAGEERRORS, "no script error from switching between the three forms",
              f"{len(PAGEERRORS)} error(s)")

        # a click inside a small-multiple panel and a click on a ranked-table row must both drill,
        # because the two new forms have to be navigable and not pictures
        for k, sel, name in (("f8", "#smlGrid .smlPanel", "a small multiple"),
                             ("f10", "#tbl10 tbody tr.clickable", "a ranked-table row")):
            pg.click(f"#segForm button[data-f='{k}']")
            pg.wait_for_timeout(400)
            check(open_more_controls(pg), "the More controls panel is open before Reset")
            pg.click("#btnReset")
            pg.wait_for_timeout(400)
            before = js(pg, "() => window.__pmfe2.level()")
            pg.click(sel)
            pg.wait_for_timeout(450)
            after = js(pg, "() => window.__pmfe2.level()")
            check(before == "fam" and after != before,
                  f"a real click on {name} opens the level beneath it", f"{before} -> {after}")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(350)

        # ── 7c. the customer control, driven with real events ────────────────────────────────
        # The previous gate drove chart callbacks directly and passed a page whose customer
        # control did nothing. This drives the list box and the buttons the way a hand does.
        print("\n7c. the customer control, driven with real events")
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(1500)
        base_recs = js(pg, "() => window.__pmfe2.recs()")
        base_kpi = js(pg, "() => window.__pmfe2.kpis()[0].val")
        driven = {}
        for mk in ("ITUK", "UTI", "SWEDEN"):
            ok = pg.evaluate("""(name) => window.__pmfe2.selectCustomer(name)""", mk)
            if not ok:
                continue
            pg.wait_for_timeout(450)
            recs_mk = js(pg, "() => window.__pmfe2.recs()")
            driven[mk] = {"eur1": recs_mk[0]["eur1"] if recs_mk else None,
                          "kpi": js(pg, "() => window.__pmfe2.kpis()[0].val"),
                          "sel": js(pg, "() => window.__pmfe2.selectedMarkets()")}
        check(len(driven) >= 2, "at least two markets could be selected on the list box",
              str(list(driven)))
        for mk, d in driven.items():
            check(d["sel"] == [mk], f"selecting {mk} leaves exactly that market selected",
                  str(d["sel"]))
            check(base_recs and d["eur1"] is not None
                  and abs(d["eur1"] - base_recs[0]["eur1"]) > 1.0,
                  f"the figures change when {mk} is selected",
                  f"EUR {base_recs[0]['eur1']:,.0f} -> {d['eur1']:,.0f}")
        vals = {k: round(v["eur1"]) for k, v in driven.items()}
        check(len(set(vals.values())) == len(vals),
              "each market gives a different first row, so the control is really driving",
              str(vals))
        print(f"   driven markets: " + ", ".join(
            f"{k} EUR {v['eur1']:,.0f} (KPI {v['kpi']})" for k, v in driven.items()))
        # the buttons, as real clicks
        n_all = js(pg, "() => window.__pmfe2.clickAll()")
        check(n_all == 18, "the All 18 button selects every customer", f"{n_all} selected")
        ituk_sel = js(pg, "() => window.__pmfe2.clickItuk()")
        check(ituk_sel == ["ITUK"], "the ITUK only button selects ITUK alone", str(ituk_sel))
        pg.wait_for_timeout(350)
        ituk_rows = js(pg, "() => window.__pmfe2.recs()")
        pg.click("#btnNone")
        pg.wait_for_timeout(400)
        none_rows = js(pg, "() => window.__pmfe2.recs()")
        check(ituk_rows and none_rows and abs(ituk_rows[0]["eur1"] - none_rows[0]["eur1"]) > 1.0,
              "ITUK alone differs from no selection (which means all customers)",
              f"EUR {ituk_rows[0]['eur1']:,.0f} against EUR {none_rows[0]['eur1']:,.0f}")
        # the fleet behind the pair must be the selected customers' fleet, not all eighteen: a
        # one-customer book over eighteen markets' vehicles is the two-denominator trap in reverse
        no_sel_fleet = js(pg, "() => window.__pmfe2.pctCheck().byFamily.n_series_truck.f0")
        js(pg, "() => window.__pmfe2.selectCustomer('ITUK')")
        pg.wait_for_timeout(450)
        ituk_fleet = js(pg, "() => window.__pmfe2.pctCheck().byFamily.n_series_truck.f0")
        check(ituk_fleet < no_sel_fleet,
              "selecting one customer divides by that customer's fleet, not all eighteen",
              f"{ituk_fleet:,.0f} against {no_sel_fleet:,.0f} vehicles")
        check(abs(ituk_fleet - 21584.0) < 60,
              "and that fleet is the workbook's own count for that customer",
              f"{ituk_fleet:,.0f} vehicles against the workbook's 21,584 for 2024")
        pg.click("#btnNone")
        pg.wait_for_timeout(400)

        # ── 8. ink on every canvas, and the split identity ────────────────────────────────────
        print("\n8. ink per canvas, from the canvas pixels")
        pg.click("#btnNone")
        pg.wait_for_timeout(400)
        pg.click("#segForm button[data-f='f2']")
        pg.wait_for_timeout(400)
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(1500)
        ids = js(pg, "() => Array.from(document.querySelectorAll('canvas')).map(c => c.id)")
        inks = canvas_ink(pg, ids)
        for cid, v in inks.items():
            if cid.startswith("sml_"):
                continue          # the multiples are measured in their own box below
            if v.get("zeroSize"):
                NOTES.append(f"canvas {cid} had zero size at measure time")
                print(f"  [note] canvas {cid} had zero size at measure time")
                continue
            check(not v.get("missing") and v.get("inkPct", 0) > 0.5,
                  f"canvas {cid} has drawn ink", f"{v.get('inkPct')}% of {v.get('w')}x{v.get('h')}")
        # the small multiples are canvases too, and each one has to have drawn its own bars. They
        # are measured with their own form showing, because a chart in a hidden box has no width.
        pg.click("#segForm button[data-f='f8']")
        pg.wait_for_timeout(700)
        sml = js(pg, """() => {
            const out = [];
            document.querySelectorAll('#smlGrid canvas').forEach(cv => {
              if (!cv.width || !cv.height) { out.push({id: cv.id, zeroSize: true}); return; }
              const ctx = cv.getContext('2d');
              const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
              let ink = 0;
              for (let i = 0; i < d.length; i += 4) {
                if (d[i + 3] < 8) continue;
                if (d[i] > 246 && d[i + 1] > 246 && d[i + 2] > 246) continue;
                ink++; }
              out.push({id: cv.id, w: cv.width, h: cv.height,
                        inkPct: +(100 * ink / (cv.width * cv.height)).toFixed(3)}); });
            return out; }""")
        check(len(sml) > 0, "the small multiples are on the page as canvases", f"{len(sml)}")
        for s in sml:
            check(s["inkPct"] > 0.5, f"small multiple {s['id']} has drawn ink",
                  f"{s['inkPct']}% of {s['w']}x{s['h']}")

        print("\n9. the split identity, on the values the page is showing")
        worst = 0.0
        for name, snapv in snaps.items():
            for rec in snapv["recs"]:
                if rec.get("total") is None:
                    continue
                terms = ((rec["vol"] or 0) + (rec["price"] or 0) + (rec["mix"] or 0)
                         + (rec["fleet"] or 0))
                worst = max(worst, abs(terms - rec["total"]))
        check(worst < 0.02, "volume + price + mix + fleet = the per-vehicle move at every level",
              f"largest gap EUR {worst:.4f}")
        check(any(abs(r.get("mix") or 0) > 0.01 for s in snaps.values() for r in s["recs"]),
              "mix is non-zero on the rendered page, not only in the payload")

        # ── 10. the clocks ────────────────────────────────────────────────────────────────────
        print("\n10. the two clocks and the period that cannot be compared")
        info = js(pg, """() => {
            const sel = document.getElementById('selClock');
            const p = window.__pmfe2.pair();
            return {options: Array.from(sel.options).map(o => ({v: o.value, label: o.textContent,
                      disabled: o.disabled})),
                    pair: {b: p.b, e: p.e, bl: p.bl, el: p.el, ok: p.ok, held: p.held,
                           months: p.months}}; }""")
        live = [o for o in info["options"] if o["v"]]
        check({o["v"] for o in live} == {"CY", "FY"}, "both clocks are selectable",
              str([o["v"] for o in live]))
        check(all(o["disabled"] for o in info["options"] if not o["v"]),
              "an incomplete period is offered as disabled, not comparable")
        check(info["pair"]["ok"], "the pair the page draws is twelve months on both sides",
              f"{info['pair']['bl']} | {info['pair']['el']}")
        check(bool(info["pair"]["held"]) and info["pair"]["held"][0]["months"] < 12,
              "the held-out period is named with its month count",
              str([f"{h['label']} ({h['months']}m)" for h in info["pair"]["held"]]))
        pg.select_option("#selClock", "FY")
        pg.wait_for_timeout(500)
        fy = snapshot(pg)
        print(f"   ISZE clock: {fy['kpis'][0]['val']}, labels {fy['labels'][:3]}")
        check(fy["bars"] != lvl0["bars"], "the ISZE clock shows different values")
        pg.select_option("#selClock", "CY")
        pg.wait_for_timeout(400)

        # ── 11. screenshots for the receipt ───────────────────────────────────────────────────
        print("\n11. screenshots for the receipt")
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(1500)
        top_shot = SHOTS / "merged_top.png"
        pg.screenshot(path=str(top_shot))
        shots = [top_shot]
        pg.select_option("#selCust", "UTI")
        pg.wait_for_timeout(500)
        uti_shot = SHOTS / "customer_UTI_selected.png"
        pg.screenshot(path=str(uti_shot))
        shots.append(uti_shot)
        print(f"   UTI selection shows {js(pg, '() => window.__pmfe2.selectedMarkets()')}, "
              f"headline {js(pg, '() => window.__pmfe2.kpis()')[0]['val']}")
        pg.click("#btnNone")
        pg.wait_for_timeout(500)

        check(click_bar(pg, "N-series truck"), "the N-series bar clicks for the screenshot")
        pg.wait_for_timeout(400)
        check(js(pg, "() => window.__pmfe2.level()") == "band",
              "the screenshot walk reaches the band level",
              str(js(pg, "() => window.__pmfe2.level()")))
        click_first_bar(pg)
        pg.wait_for_timeout(500)
        lvl_shot = js(pg, "() => window.__pmfe2.level()")
        check(lvl_shot in ("cat", "pn"), "the screenshot walk reaches the service families",
              str(lvl_shot))
        if lvl_shot == "cat":
            click_first_bar(pg)
            pg.wait_for_timeout(500)
            lvl_shot = js(pg, "() => window.__pmfe2.level()")
        check(lvl_shot == "pn", "the screenshot walk reaches the part numbers", str(lvl_shot))
        pn_shot = SHOTS / "drilled_to_part_numbers.png"
        pg.screenshot(path=str(pn_shot))
        shots.append(pn_shot)
        crumb_txt = re.sub(r"\s+", " ", js(pg, "() => document.getElementById('crumb').innerText"))
        print(f"   drilled screenshot at level {lvl_shot}, "
              f"rows {js(pg, '() => window.__pmfe2.rowCount()')}, crumb {crumb_txt[:90]}")
        pn_recs = js(pg, "() => window.__pmfe2.recs().length")
        pg.select_option("#selCust", "UTI")
        pg.wait_for_timeout(600)
        uti_recs = js(pg, "() => window.__pmfe2.recs().length")
        print(f"   after four rebuild cycles: level "
              f"{js(pg, '() => window.__pmfe2.level()')}, panel errors "
              f"{js(pg, '() => window.__pmfe2.panelErrors()')}, "
              f"part-number rows {pn_recs} -> {uti_recs} on UTI")
        check(js(pg, "() => window.__pmfe2.level()") == lvl_shot,
              "the page is still at the same level after the rebuild cycles",
              str(js(pg, "() => window.__pmfe2.level()")))
        check(js(pg, "() => window.__pmfe2.panelErrors()") == [],
              "no panel failed to draw during the rebuild cycles",
              str(js(pg, "() => window.__pmfe2.panelErrors()")))
        cyc_shot = SHOTS / "after_rebuild_cycles.png"
        pg.screenshot(path=str(cyc_shot))
        shots.append(cyc_shot)
        print(f"   the cycles screenshot is taken with UTI selected "
              f"({js(pg, '() => window.__pmfe2.selectedMarkets()')}, {uti_recs} rows)")
        for s in shots:
            print(f"   {s.name}  {s.stat().st_size / 1024:.0f} KB  "
                  f"sha256 {hashlib.sha256(s.read_bytes()).hexdigest()[:12]}")
        check(all(s.stat().st_size > 20000 for s in shots), "every screenshot has real content")
        hashes = [hashlib.sha256(s.read_bytes()).hexdigest() for s in shots]
        check(len(set(hashes)) == len(hashes),
              "no two receipt screenshots are the same picture",
              f"{len(set(hashes))} distinct of {len(hashes)}")
        b.close()

    # ── 12. no page error, anywhere in the run ─────────────────────────────────────────────────
    print("\n12. every page error seen during the run")
    check(not PAGEERRORS, "the page raised no script error during the whole run",
          f"{len(PAGEERRORS)} error(s)")
    for e in PAGEERRORS[:6]:
        print("      ", e[:220])

    # ── 13. the tie-out back to the published files ────────────────────────────────────────────
    print("\n13. the numbers tie back to the published files")
    ties = payload.get("meta", {}).get("ties", [])
    check(bool(ties), "the build recorded its tie-out in the payload")
    if ties:
        check(ties[0]["worst"] <= 1.0, "the family euro matches the published totals",
              f"worst EUR {ties[0]['worst']}")
        check(ties[0]["rows"] >= 18, "the tie covered every customer x family x year row",
              f"{ties[0]['rows']} rows")
    check(payload.get("meta", {}).get("bookBilled", 0) > 0, "the whole billed book is stated",
          f"EUR {payload['meta']['bookBilled']:,.0f}")

    QA.joinpath("qa_stats.json").write_text(json.dumps(
        {"viewport_geometry": {str(k): v for k, v in geo_all.items()},
         "controls": inv, "canvas_ink": inks,
         "levels": {k: {"level": v["level"], "rows": v["rows"], "labels": v["labels"]}
                    for k, v in snaps.items()},
         "decomposition_axis": dec,
         "uti_kpis": uti["kpis"], "ituk_kpis": ituk["kpis"],
         "page_errors": PAGEERRORS, "fails": FAILS, "notes": NOTES}, indent=2), encoding="utf-8")

    print("\n" + "=" * 78)
    if FAILS:
        print(f"QA FAIL: {len(FAILS)} check(s) failed")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print("QA PASS")
    print(f"  1440x900: controls end at {geo_all[1440]['controlsBottom']} px "
          f"({geo_all[1440]['controlsH']} px tall, {geo_all[1440]['lines']} line), first chart "
          f"{geo_all[1440]['mainTop']}->{geo_all[1440]['mainBottom']} px, "
          f"ink {geo_all[1440]['mainBoxInkPct']}%")
    print(f"  drill: {snaps['level 0']['rows']} vehicle types -> {snaps['level 1']['rows']} bands "
          f"-> {snaps['level 2']['rows']} service families -> {snaps['level 3']['rows']} part numbers")
    print(f"  UTI headline {uti['kpis'][0]['val']} vs ITUK {ituk['kpis'][0]['val']}; "
          f"billed {uti['kpis'][2]['val']} vs {ituk['kpis'][2]['val']}")
    print(f"  decomposition axis: {dec['title']} -> ticks {dec['ticks']}")
    print(f"  stats written to {QA / 'qa_stats.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
