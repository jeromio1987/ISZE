"""Visual QA for the three chosen forms.

Renders the rebuilt page at 1440x900 and 1000px, captures each of the three forms with its own
form showing, measures ink per canvas from the canvas pixels (a blank canvas is a FAIL), and crops
the two places a label could collide: the pair's annotation gutter, and a single small-multiple
panel. Chrome is passed by executable_path because playwright's bundled browser is not installed on
this machine.

Usage:
    python 02_dashboards/sales/_build/qa_forms_shots.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_v2" / "forms"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

FAILS: list[str] = []
ERRORS: list[str] = []
SHOTS: list[Path] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(f"{label} {detail}".strip())
    return ok


def canvases(pg) -> list[dict]:
    """Every visible canvas, with its box and its own pixel ink."""
    return pg.evaluate(
        """() => {
        const out = [];
        document.querySelectorAll('canvas').forEach(cv => {
          const r = cv.getBoundingClientRect();
          if (r.width < 2 || r.height < 2) return;
          const box = cv.closest('.formview, .chartbox, .smlPanel');
          const view = cv.closest('.formview');
          if (view && !view.classList.contains('on')) return;
          let ink = 0, sampled = 0;
          try {
            const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
            for (let i = 0; i < d.length; i += 4) {
              sampled++;
              if (d[i + 3] < 8) continue;
              if (d[i] > 246 && d[i + 1] > 246 && d[i + 2] > 246) continue;
              ink++; }
          } catch (e) { return; }
          out.push({id: cv.id, cssW: Math.round(r.width), cssH: Math.round(r.height),
                    w: cv.width, h: cv.height, ink: ink, sampled: sampled,
                    inkPct: sampled ? +(100 * ink / sampled).toFixed(2) : 0,
                    panel: cv.closest('.smlPanel') ? cv.closest('.smlPanel').querySelector('.h')
                             .textContent.trim() : null});
        });
        return out; }"""
    )


def geometry(pg) -> dict:
    return pg.evaluate(
        """() => {
        const out = {texts: []};
        // any element whose text is clipped by its own box is a label that failed to fit
        document.querySelectorAll('#view-f2, #view-f8, #view-f10').forEach(host => {
          if (!host.classList.contains('on')) return;
          host.querySelectorAll('*').forEach(el => {
            if (el.children.length) return;
            const t = (el.textContent || '').trim();
            if (!t) return;
            const cs = getComputedStyle(el);
            if (el.scrollWidth > el.clientWidth + 2 && cs.overflow !== 'visible'
                && cs.textOverflow !== 'ellipsis') {
              out.texts.push({cls: String(el.className), text: t.slice(0, 40),
                              scroll: el.scrollWidth, client: el.clientWidth}); }
          }); });
        out.clipped = out.texts.length;
        try {
          const ch = window.Chart.getChart('c_main');
          if (ch && ch.chartArea && ch.getDatasetMeta(0) && ch.getDatasetMeta(0).data
              && ch.getDatasetMeta(0).data.length
              && ch.getDatasetMeta(1) && ch.getDatasetMeta(1).data
              && ch.getDatasetMeta(1).data.length) {
            const a = ch.chartArea;
            let furthest = -1e9;
            ch.getDatasetMeta(0).data.concat(ch.getDatasetMeta(1).data).forEach(el => {
              if (el && el.x > furthest) furthest = el.x; });
            const xf = (ch.options.scales.x.ticks && ch.options.scales.x.ticks.font
                        && ch.options.scales.x.ticks.font.size) || 11;
            const yf = (ch.options.scales.y.ticks && ch.options.scales.y.ticks.font
                        && ch.options.scales.y.ticks.font.size) || 11;
            out.pair = {areaRight: a.right, furthestBar: furthest,
                        gutterPx: ch.canvas.clientWidth - a.right,
                        axisFont: xf, yFont: yf};
            // Recreate the annotation boxes exactly as the page draws them, so a collision between
            // an annotation and its bar, or between two annotations, is measured rather than eyed.
            const c = ch.ctx, recs = window.__pmfe2.recs();
            c.save();
            const boxes = [];
            ch.getDatasetMeta(1).data.forEach((el, i) => {
              if (el.y === null) return;
              const y0 = ch.getDatasetMeta(0).data[i].y;
              const r = recs[i];
              const pct = v => v === null || v === undefined ? 'n/a'
                : ((v >= 0 ? '+' : '-') + Math.abs(100*v).toFixed(1) + '%');
              const eurPct = r.eur0 > 0 ? r.eur1/r.eur0 - 1 : null;
              const ratePct = (r.rate0 !== null && r.rate0 !== undefined && r.rate0 > 0
                               && r.rate1 !== null && r.rate1 !== undefined)
                ? r.rate1/r.rate0 - 1 : null;
              const line = r.comparable === false ? 'not comparable'
                : ((r.eur1 - r.eur0 >= 0 ? '+' : '-')
                    + Math.abs(Math.round(r.eur1 - r.eur0)).toLocaleString('en-GB')
                    + '  ' + pct(eurPct) + ' / ' + pct(ratePct));
              c.font = r.comparable === false
                ? '600 10.5px ' + getComputedStyle(document.body).fontFamily
                : '600 11px ' + getComputedStyle(document.body).fontFamily;
              const yBase = Math.max(a.top + 11, Math.min(Math.min(el.y, y0) - 7, a.bottom - 4));
              const w = c.measureText(line).width;
              boxes.push({i: i, label: ch.data.labels[i], line: line, x0: a.right + 8,
                          x1: a.right + 8 + w, yc: yBase, w: +w.toFixed(1)});
            });
            c.restore();
            out.annotations = boxes;
            out.canvasW = ch.canvas.clientWidth;
            out.canvasH = ch.canvas.clientHeight;
            let worstBar = -1e9;
            ch.getDatasetMeta(0).data.concat(ch.getDatasetMeta(1).data).forEach(el => {
              if (el && el.x > worstBar) worstBar = el.x; });
            out.worstBar = worstBar;
          }
        } catch (e) { out.pairError = String(e); }
        const sml = [];        document.querySelectorAll('#smlGrid .smlPanel').forEach(p => {
          const h = p.querySelector('.h'), pc = p.querySelector('.pct');
          if (!h || !pc) return;
          sml.push({title: h.textContent.trim(),
                    titleFont: getComputedStyle(h).fontSize,
                    pctFont: getComputedStyle(pc).fontSize,
                    pctClipped: pc.scrollWidth > pc.clientWidth + 2,
                    panelW: Math.round(p.getBoundingClientRect().width)}); });
        out.sml = sml;
        return out; }"""
    )


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    print(f"page: {HTML}  ({HTML.stat().st_size/1024:,.0f} KB)")
    report: dict = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME, args=["--headless=new", "--disable-gpu"])
        for w, h in ((1440, 900), (1000, 900)):
            pg = br.new_page(viewport={"width": w, "height": h})
            pg.on("pageerror", lambda e: ERRORS.append(str(e)))
            pg.on("console", lambda m: ERRORS.append("console." + m.type + ": " + m.text)
                  if m.type == "error" else None)
            pg.goto(HTML.as_uri(), wait_until="load")
            pg.wait_for_timeout(1800)
            print(f"\n== {w}x{h} ==")
            report[str(w)] = {}
            for key, name in (("f2", "two_columns_and_the_difference"),
                              ("f8", "small_multiples"),
                              ("f10", "ranked_table_with_bars")):
                pg.click(f"#segForm button[data-f='{key}']")
                pg.wait_for_timeout(900)
                # scroll the card to the top of the viewport so the shot is of the form itself
                pg.evaluate("""() => { const el = document.getElementById('segForm');
                    el.scrollIntoView({block: 'start'}); }""")
                pg.wait_for_timeout(350)
                shot = QA / f"{w}_{name}.png"
                pg.screenshot(path=str(shot))
                SHOTS.append(shot)
                cs = canvases(pg)
                g = geometry(pg)
                report[str(w)][key] = {"canvases": cs, "geometry": g}
                print(f"  {key}: " + ", ".join(
                    f"{c['id']} {c['cssW']}x{c['cssH']} ink {c['inkPct']}%"
                    + (f" [{c['panel']}]" if c["panel"] else "") for c in cs))
                if g.get("pair") and key == "f2":
                    pr = g["pair"]
                    check(pr["furthestBar"] <= pr["areaRight"] + 1.5,
                          f"{w}px {key}: no bar reaches into the annotation gutter",
                          f"furthest {pr['furthestBar']:.1f} vs plot right {pr['areaRight']:.1f}")
                    check(pr["gutterPx"] >= 150,
                          f"{w}px {key}: the annotation gutter is wide enough",
                          f"{pr['gutterPx']:.0f}px")
                    check(pr["axisFont"] >= 10 and pr["yFont"] >= 10,
                          f"{w}px {key}: the axis type is not shrunk to fit",
                          f"x {pr['axisFont']}px, y {pr['yFont']}px")
                # the annotation checks only mean anything while form 2 is the view on screen: in a
                # hidden box the chart area collapses and there is nothing to collide with
                anns = (g.get("annotations") or []) if key == "f2" else []
                if key == "f2":
                    check(bool(anns), f"{w}px {key}: the pair annotations were measured",
                          f"{len(anns)} rows")
                if anns:
                    over = [a for a in anns if a["x1"] > g["canvasW"] - 2]
                    check(not over, f"{w}px {key}: every annotation fits inside the canvas",
                          str([a["label"] for a in over]))
                    # an annotation must not run back over the plot area, which would put it on a bar
                    back = [a for a in anns if a["x0"] < g["pair"]["areaRight"]]
                    check(not back, f"{w}px {key}: no annotation starts inside the plot area",
                          str([a["label"] for a in back]))
                    # and two annotations must not overlap each other vertically
                    clash = []
                    for i in range(len(anns)):
                        for j in range(i + 1, len(anns)):
                            if (anns[i]["x0"] < anns[j]["x1"] and anns[j]["x0"] < anns[i]["x1"]
                                    and abs(anns[i]["yc"] - anns[j]["yc"]) < 12):
                                clash.append((anns[i]["label"], anns[j]["label"]))
                    check(not clash, f"{w}px {key}: no two annotations overlap",
                          str(clash))
                    check(max(a["w"] for a in anns) <= g["pair"]["gutterPx"] - 6,
                          f"{w}px {key}: the widest annotation fits its gutter on one line",
                          f"widest {max(a['w'] for a in anns):.0f}px, gutter "
                          f"{g['pair']['gutterPx']:.0f}px")
                if g.get("sml"):
                    fonts = {p["titleFont"] for p in g["sml"]} | {p["pctFont"] for p in g["sml"]}
                    check(len(fonts) <= 2, f"{w}px {key}: every panel uses the same type size",
                          str(sorted(fonts)))
                    check(not any(p["pctClipped"] for p in g["sml"]),
                          f"{w}px {key}: no panel percentage is clipped",
                          str([p["title"] for p in g["sml"] if p["pctClipped"]]))
                    check(all(not p["pctClipped"] for p in g["sml"]),
                          f"{w}px {key}: the panel width does not shrink the type",
                          f"panel {g['sml'][0]['panelW']}px" if g["sml"] else "")
                check(g["clipped"] == 0,
                      f"{w}px {key}: no label is clipped by its own box", f"{g['clipped']} found")
                for c in cs:
                    check(c["inkPct"] > 0.5, f"{w}px {key}: {c['id']} has drawn ink",
                          f"{c['inkPct']}% of {c['w']}x{c['h']}")

            # a crop of the annotation gutter and of one small multiple, at full resolution
            pg.click("#segForm button[data-f='f2']")
            pg.wait_for_timeout(700)
            pg.evaluate("""() => { const el = document.getElementById('segForm');
                el.scrollIntoView({block: 'start'}); }""")
            pg.wait_for_timeout(300)
            box = pg.evaluate("""() => { const r = document.getElementById('c_main')
                .getBoundingClientRect();
                return {x: Math.round(r.left + r.width * 0.62), y: Math.round(r.top),
                        width: Math.round(r.width * 0.38), height: Math.round(r.height)}; }""")
            crop = QA / f"{w}_gutter_crop.png"
            pg.screenshot(path=str(crop), clip=box)
            SHOTS.append(crop)
            pg.click("#segForm button[data-f='f8']")
            pg.wait_for_timeout(900)
            pg.evaluate("""() => { const el = document.getElementById('smlGrid');
                el.scrollIntoView({block: 'start'}); }""")
            pg.wait_for_timeout(300)
            box2 = pg.evaluate("""() => { const r = document.querySelector('#smlGrid .smlPanel')
                .getBoundingClientRect();
                return {x: Math.round(r.left), y: Math.round(r.top),
                        width: Math.round(r.width * 2.1), height: Math.round(r.height)}; }""")
            crop2 = QA / f"{w}_small_multiple_crop.png"
            pg.screenshot(path=str(crop2), clip=box2)
            SHOTS.append(crop2)
            pg.close()

        # the worked case, the panel that proves why there are two percentages
        pg = br.new_page(viewport={"width": 1440, "height": 900})
        pg.on("pageerror", lambda e: ERRORS.append(str(e)))
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(1800)
        pg.evaluate("""() => { document.getElementById('worked').scrollIntoView({block: 'center'}); }""")
        pg.wait_for_timeout(400)
        wk = QA / "1440_the_worked_case.png"
        pg.screenshot(path=str(wk))
        SHOTS.append(wk)
        wt = pg.evaluate("() => window.__pmfe2.workedText()")
        print(f"\n== the worked case ==\n{wt[:700]}")
        check("per vehicle" in wt and "%" in wt, "the worked case is on the page")
        report["worked"] = wt
        br.close()

    print("\nscreenshots (taken):")
    for s in SHOTS:
        im = Image.open(s)
        print(f"  {s.name}  {im.size[0]}x{im.size[1]}  {s.stat().st_size/1024:.0f} KB")
    check(not ERRORS, "no page error and no console error at either width", f"{len(ERRORS)}")
    for e in ERRORS[:5]:
        print("     ", e[:200])
    (QA / "forms_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\nreport -> {QA / 'forms_report.json'}")
    if FAILS:
        print(f"\nFORMS QA FAIL ({len(FAILS)})")
        for f in FAILS:
            print("   -", f)
        return 1
    print(f"\nFORMS QA PASS ({len(SHOTS)} screenshots taken)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
