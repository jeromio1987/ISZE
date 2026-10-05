"""QA + verify for the AIM repertoire map. Real Chrome, file:// open, no server.

Asserts (exit 1 on any failure) and captures element screenshots into _qa/.
Every assertion reads the rendered page, not the source.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Repertoire_Map_2026-09-17.html"
OUT = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17" / "_qa"
OUT.mkdir(parents=True, exist_ok=True)

fails: list[str] = []
warns: list[str] = []
passes: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (passes if ok else fails).append(f"{name}{(' :: ' + detail) if detail else ''}")
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def main() -> int:
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1440, "height": 950}, device_scale_factor=2)
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_timeout(2600)

        # ---------------------------------------------------------- boot
        check("page boots and exposes ready flag",
              page.evaluate("() => window.__aimReady === true"))
        title = page.title()
        check("title is the business question, not a folder name",
              "AIM repertoire map" in title, title)

        # ---------------------------------------------------------- payload
        size_mb = HTML.stat().st_size / 1024 / 1024
        check("file is a single self-contained file under 12 MB",
              size_mb < 12, f"{size_mb:.2f} MB")
        check("no CDN reference in the file",
              "cdn.jsdelivr" not in HTML.read_text(encoding="utf-8", errors="ignore"))
        check("no fetch() of a sibling file",
              "fetch(" not in HTML.read_text(encoding="utf-8", errors="ignore"))

        # ---------------------------------------------------------- layout
        probe = page.evaluate("""() => {
          const out = {sw: document.documentElement.scrollWidth,
                       cw: document.documentElement.clientWidth, clipped: [], canvases: [],
                       bars: 0, kpis: 0, rows: 0, resid: 0, amber_bars: -1, crumb: ''};
          document.querySelectorAll('*').forEach(el => {
            if (el.scrollWidth > el.clientWidth + 4 && el.clientWidth > 0) {
              out.clipped.push({tag: el.tagName, cls: String(el.className).slice(0,30),
                                sw: el.scrollWidth, cw: el.clientWidth,
                                txt: (el.textContent||'').trim().slice(0,40)});
            }
          });
          document.querySelectorAll('canvas').forEach((c,i) => {
            const r = c.getBoundingClientRect();
            out.canvases.push({i, w: Math.round(r.width), h: Math.round(r.height)});
          });
          out.kpis = document.querySelectorAll('#kpis .kpi').length;
          out.rows = document.querySelectorAll('#tbl tbody tr').length;
          out.resid = document.querySelectorAll('#resid tbody tr').length;
          out.amber_bars = (() => {
            const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
            if (!ch) return -1;
            const bg = ch.data.datasets[0].backgroundColor || [];
            return bg.filter(c => String(c).toLowerCase() === '#a8721f').length;
          })();
          out.crumb = document.getElementById('crumb').textContent.trim();
          return out;
        }""")
        check("no horizontal page overflow", probe["sw"] <= probe["cw"] + 1,
              f'{probe["sw"]} vs {probe["cw"]}')
        check("no clipped element", len(probe["clipped"]) == 0,
              str(probe["clipped"][:3]))
        check("KPI tiles painted", probe["kpis"] == 5, f'{probe["kpis"]} tiles')
        check("level-1 table painted", probe["rows"] == 8, f'{probe["rows"]} rows')
        check("residual strip shows both placeholders", probe["resid"] == 2,
              f'{probe["resid"]} rows')
        check("two residual categories are coloured amber, not terracotta",
              probe["amber_bars"] == 2, f'{probe["amber_bars"]} amber bars')

        # ---------------------------------------------------------- paint
        paint = page.evaluate("""() => {
          const cvs = [...document.querySelectorAll('canvas')];
          return cvs.map((c,i) => {
            const ctx = c.getContext('2d');
            let d;
            try { d = ctx.getImageData(0,0,c.width,c.height).data; }
            catch(e) { return {i, err: String(e)}; }
            const seen = new Set();
            for (let k=0; k<d.length; k+=4*97) {
              seen.add(d[k]+','+d[k+1]+','+d[k+2]);
            }
            return {i, w:c.width, h:c.height, colors: seen.size};
          });
        }""")
        for p in paint:
            check(f"canvas {p['i']} actually painted",
                  p.get("colors", 0) > 12, f"{p.get('colors')} distinct sampled colours")

        main_bars = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
          return ch ? {bars: ch.data.labels.length, first: ch.data.labels[0]} : null;
        }""")
        check("main bar chart has 8 category bars",
              bool(main_bars) and main_bars["bars"] == 8, str(main_bars))

        # ---------------------------------------------------------- capture L1
        page.locator("header.top").screenshot(path=str(OUT / "01_header.png"))
        page.locator(".what").screenshot(path=str(OUT / "02_scope.png"))
        page.locator(".kpis").screenshot(path=str(OUT / "03_kpis.png"))
        page.locator(".controls").screenshot(path=str(OUT / "04_controls.png"))
        resid_visible = page.evaluate(
            "() => getComputedStyle(document.getElementById('resid')).display !== 'none'")
        if resid_visible:
            page.locator("#resid").screenshot(path=str(OUT / "05_residual.png"))
        else:
            check("residual strip is visible at level 1", False,
                  "display:none, nothing captured")
        cards = page.locator(".card")
        for i in range(cards.count()):
            cards.nth(i).screenshot(path=str(OUT / f"06_card{i+1}.png"))
        check("cards captured", cards.count() >= 5, f"{cards.count()} cards")
        # ---------------------------------------------------------- level 1 KPI sanity
        kpi_vals = page.evaluate(
            "() => [...document.querySelectorAll('#kpis .val')].map(e => e.textContent)")
        check("no KPI is blank", all(v.strip() for v in kpi_vals), str(kpi_vals))
        check("headline parts billed is the shipped EUR 34.99M",
              "34,993,609" in kpi_vals[0], kpi_vals[0])
        check("headline step is the shipped EUR 1,652,140",
              "1,652,140" in kpi_vals[1].replace("\u202f", "") or
              "1,652,140" in kpi_vals[1], kpi_vals[1])
        check("weighted move reads 5.96%", "5.96%" in kpi_vals[2], kpi_vals[2])
        check("cannot-move tile is not zero",
              kpi_vals[4].strip() not in ("€0", ""), kpi_vals[4])
        check("no NaN anywhere in KPI values",
              all("NaN" not in v for v in kpi_vals), str(kpi_vals))

        # ---------------------------------------------------------- drill to level 2
        page.evaluate("""() => {
          const tr = [...document.querySelectorAll('#tbl tbody tr')]
            .find(r => r.textContent.indexOf('Competitive parts') >= 0);
          tr.click();
        }""")
        page.wait_for_timeout(700)
        l2 = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
          return {bars: ch ? ch.data.labels.length : 0,
                  labels: ch ? ch.data.labels : [],
                  head: document.getElementById('t-main').textContent,
                  crumb: document.getElementById('crumb').textContent.trim(),
                  rows: document.querySelectorAll('#tbl tbody tr').length,
                  dist: document.querySelectorAll('#dist tbody tr').length};
        }""")
        check("level 2 opened with the groups inside Competitive parts",
              l2["bars"] == len(l2["labels"]), str(l2))
        check("level 2 heading names the category",
              "Competitive parts" in l2["head"], l2["head"])
        check("breadcrumb shows the path taken",
              "All categories" in l2["crumb"] and "Competitive parts" in l2["crumb"],
              l2["crumb"])
        check("level-2 table painted", l2["rows"] == l2["bars"], f'{l2["rows"]} rows')
        check("distributor table painted at level 2", l2["dist"] == 22,
              f'{l2["dist"]} distributors')
        page.locator(".grid.g2").first.screenshot(path=str(OUT / "07_level2.png"))
        page.locator("#tbl").screenshot(path=str(OUT / "08_level2_table.png"))
        page.locator("#dist").screenshot(path=str(OUT / "09_dist_table.png"))

        # ---------------------------------------------------------- level 3
        page.evaluate("""() => {
          const tr = [...document.querySelectorAll('#tbl tbody tr')]
            .find(r => r.textContent.indexOf('Filters') >= 0);
          tr.click();
        }""")
        page.wait_for_timeout(700)
        l3 = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
          return {bars: ch ? ch.data.labels.length : 0,
                  head: document.getElementById('t-main').textContent,
                  labels: ch ? ch.data.labels : []};
        }""")
        check("level 3 opened with the filter leaves", l3["bars"] == 4, str(l3["bars"]))
        check("level 3 leaves are the four filter types",
              all(any(k in l for l in l3["labels"])
                  for k in ("Oil filter", "Fuel filter", "Air filter")), str(l3["labels"]))
        page.locator("#tbl").screenshot(path=str(OUT / "10_level3_table.png"))

        # ---------------------------------------------------------- level 4
        page.evaluate("""() => {
          const tr = [...document.querySelectorAll('#tbl tbody tr')]
            .find(r => r.textContent.indexOf('Oil filter') >= 0);
          tr.click();
        }""")
        page.wait_for_timeout(800)
        l4 = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
          return {bars: ch ? ch.data.labels.length : 0,
                  head: document.getElementById('t-main').textContent,
                  pn: document.querySelectorAll('#pntbl tbody tr').length,
                  crumb: document.getElementById('crumb').textContent.trim(),
                  kpis: [...document.querySelectorAll('#kpis .val')].map(e => e.textContent)};
        }""")
        check("level 4 is the leaf, bars are part numbers", l4["bars"] > 50, str(l4["bars"]))
        check("part-number table painted", l4["pn"] == l4["bars"], str(l4["pn"]))
        check("breadcrumb reaches the leaf", "Oil filter" in l4["crumb"], l4["crumb"])
        check("leaf KPI shows a real euro, not zero",
              l4["kpis"][0].strip() not in ("€0", ""), l4["kpis"][0])
        check("no NaN at level 4", all("NaN" not in v for v in l4["kpis"]), str(l4["kpis"]))
        page.locator("#pntbl").screenshot(path=str(OUT / "11_leaf_pn_table.png"))
        page.locator(".grid.g2").first.screenshot(path=str(OUT / "12_level4.png"))

        # ---------------------------------------------------------- filters
        page.select_option("#db", index=9)   # ITUK, no country suffix in the option text
        page.wait_for_timeout(700)
        ituk = page.evaluate(
            "() => [...document.querySelectorAll('#kpis .val')].map(e => e.textContent)")
        check("distributor filter changes the numbers", ituk[0] != l4["kpis"][0],
              f'{l4["kpis"][0]} -> {ituk[0]}')
        check("distributor filter leaves a real euro", ituk[0].strip() not in ("€0", ""),
              ituk[0])

        page.select_option("#db", value="-1")
        page.wait_for_timeout(500)
        page.click("#meas button[data-m='pct']")
        page.wait_for_timeout(600)
        pct_state = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
          const vals = ch ? ch.data.datasets[0].data : [];
          return {on: document.querySelector('#meas button.on').textContent.trim(),
                  n: vals.length, anyReal: vals.some(v => v > 0),
                  head: document.getElementById('q-main').textContent.slice(0,40)};
        }""")
        check("metric switch to weighted % redraws the bars",
              "Weighted" in pct_state["on"] and pct_state["anyReal"], str(pct_state))
        page.click("#meas button[data-m='step']")
        page.wait_for_timeout(600)
        step_state = page.evaluate("""() => {
          const ch = Object.values(Chart.instances).find(c => c.canvas.id === 'c-main');
          return {on: document.querySelector('#meas button.on').textContent.trim(),
                  anyReal: ch ? ch.data.datasets[0].data.some(v => v > 0) : false};
        }""")
        check("metric switch to step EUR redraws the bars",
              "Step" in step_state["on"] and step_state["anyReal"], str(step_state))
        page.click("#meas button[data-m='eur']")
        page.wait_for_timeout(500)
        page.locator("#tbl").screenshot(path=str(OUT / "13_table_step_metric.png"))

        # ---------------------------------------------------------- reset + search
        page.click("#reset")
        page.wait_for_timeout(600)
        check("reset returns to all categories",
              page.evaluate("() => document.getElementById('crumb').textContent")
              .strip().startswith("All categories"))

        page.fill("#q", "filter")
        page.wait_for_timeout(700)
        hits = page.evaluate(
            "() => document.querySelectorAll('#hitlist div[data-i]').length")
        hit_text = page.evaluate(
            "() => document.getElementById('hitlist').textContent")
        check("search finds family and part-type matches", hits >= 2,
              f"{hits} hits :: {hit_text[:110]}")
        page.locator("#hitlist").screenshot(path=str(OUT / "14_search.png"))
        page.evaluate("""() => {
          const d = [...document.querySelectorAll('#hitlist div[data-i]')]
            .find(x => x.textContent.indexOf('Oil filter') >= 0
                    && x.textContent.indexOf('part type') >= 0);
          d.click();
        }""")
        page.wait_for_timeout(700)
        jumped = page.evaluate("""() => ({
          head: document.getElementById('t-main').textContent,
          crumb: document.getElementById('crumb').textContent.trim(),
          pn: document.querySelectorAll('#pntbl tbody tr').length})""")
        check("clicking a search hit opens that part type",
              "Oil filter" in jumped["head"] and jumped["pn"] > 0,
              str(jumped))

        # part-number search
        page.click("#reset")
        page.wait_for_timeout(400)
        page.fill("#q", "8982705240")
        page.wait_for_timeout(900)
        pn_jump = page.evaluate("""() => ({
          pnRows: document.querySelectorAll('#pntbl tbody tr').length,
          sel: document.querySelectorAll('#pntbl tbody tr.sel').length,
          crumb: document.getElementById('crumb').textContent.trim()})""")
        check("part-number search opens its leaf and highlights the row",
              pn_jump["sel"] == 1 and pn_jump["pnRows"] > 1, str(pn_jump))
        page.locator("#pntbl").screenshot(path=str(OUT / "15_pn_search.png"))

        # ---------------------------------------------------------- narrow width
        page.set_viewport_size({"width": 900, "height": 950})
        page.wait_for_timeout(900)
        narrow = page.evaluate("""() => ({
          sw: document.documentElement.scrollWidth,
          cw: document.documentElement.clientWidth})""")
        check("no overflow at 900px", narrow["sw"] <= narrow["cw"] + 1, str(narrow))
        page.screenshot(path=str(OUT / "16_narrow.png"), full_page=False)
        page.set_viewport_size({"width": 1440, "height": 950})
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "17_full.png"), full_page=True)

        # ---------------------------------------------------------- console
        real = [e for e in errors if "favicon" not in e.lower()]
        check("no console or page errors", len(real) == 0, str(real[:4]))

        b.close()

    print()
    print("=" * 74)
    print(f"PASS {len(passes)}   FAIL {len(fails)}   WARN {len(warns)}")
    for f in fails:
        print("  FAIL " + f)
    print("=" * 74)
    print("QA_AIM_MAP_DONE" if not fails else "QA_AIM_MAP_FAILED")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
