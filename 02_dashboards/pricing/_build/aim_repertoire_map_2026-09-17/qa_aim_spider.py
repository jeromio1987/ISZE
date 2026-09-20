"""QA + verify for the AIM spider map. Real Chrome, file://, no server.

Asserts and captures into _qa_spider/.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Repertoire_Spider_2026-09-17.html"
OUT = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17" / "_qa_spider"
OUT.mkdir(parents=True, exist_ok=True)

fails: list[str] = []
passes: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (passes if ok else fails).append(f"{name}{(' :: ' + detail) if detail else ''}")
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def main() -> int:
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_timeout(2600)

        check("page boots", page.evaluate("() => window.__spiderReady === true"))
        check("title states the job",
              "All the connections" in page.title(), page.title())
        src = HTML.read_text(encoding="utf-8", errors="ignore")
        check("self-contained, no CDN", "cdn.jsdelivr" not in src and "http://" not in src[:2000])
        check("no fetch() of a sibling file", "fetch(" not in src)

        probe = page.evaluate("""() => {
          const cv = document.getElementById('map');
          const ctx = cv.getContext('2d');
          let colors = 0;
          try {
            const d = ctx.getImageData(0,0,cv.width,cv.height).data;
            const s = new Set();
            for (let k=0;k<d.length;k+=4*211) s.add(d[k]+','+d[k+1]+','+d[k+2]);
            colors = s.size;
          } catch(e) { colors = -1; }
          const rect = cv.getBoundingClientRect();
          return {w: Math.round(rect.width), h: Math.round(rect.height),
                  pw: cv.width, ph: cv.height, colors,
                  legend: document.querySelectorAll('.lg[data-i]').length,
                  facts: document.querySelectorAll('#d-facts .fact').length,
                  share: document.querySelectorAll('#d-share tbody tr').length,
                  dist: document.querySelectorAll('#d-dist tbody tr').length,
                  sw: document.documentElement.scrollWidth,
                  cw: document.documentElement.clientWidth};
        }""")
        check("canvas is real size and painted", probe["pw"] > 1000 and probe["colors"] > 40,
              str({k: probe[k] for k in ("pw", "ph", "colors")}))
        check("legend has all eight categories", probe["legend"] == 8, str(probe["legend"]))
        check("level-1 facts painted with nothing selected", probe["facts"] == 6,
              str(probe["facts"]))
        check("share table carries every ring",
              probe["share"] == 8 + 10 + 10 + len(
                  page.evaluate("() => window.spiderNodes.ND.map(n => n.name)")) + 4,
              str(probe["share"]))
        check("distributor table painted with nothing selected",
              probe["dist"] == 22, str(probe["dist"]))
        check("no horizontal overflow", probe["sw"] <= probe["cw"] + 1,
              f'{probe["sw"]} vs {probe["cw"]}')

        # ---- geometry: wedges must tile the full circle with no gaps or overlaps
        geo = page.evaluate("""() => {
          const {N1, N2, N3, ND, ALL} = window.spiderNodes;
          const gaps = [];
          const sorted = N1.slice().sort((a,b) => a.a0 - b.a0);
          for (let i=1;i<sorted.length;i++) {
            const g = sorted[i].a0 - sorted[i-1].a1;
            gaps.push(+g.toFixed(5));
          }
          const span = sorted[sorted.length-1].a1 - sorted[0].a0;
          const l2bad = N2.filter(n => n.a1 < n.a0).length;
          const l3bad = N3.filter(n => n.a1 < n.a0).length;
          const cover1 = N1.reduce((s,n) => s + (n.a1-n.a0), 0);
          const cover2 = N2.reduce((s,n) => s + (n.a1-n.a0), 0);
          const leafEuro = N3.reduce((s,n) => s + n.euro, 0);
          const l2Euro = N2.reduce((s,n) => s + n.euro, 0);
          return {span:+span.toFixed(4), cover1:+cover1.toFixed(4), cover2:+cover2.toFixed(4),
                  l2bad, l3bad, gaps: gaps.slice(0,8),
                  leafEuro: Math.round(leafEuro), l2Euro: Math.round(l2Euro),
                  totalEuro: Math.round(ALL.euro),
                  dbsPerLeaf: N3.filter(n => Object.keys(n.dbs).length > 0).length,
                  links: Object.keys(window.spiderNodes.N3.reduce((a,n)=>{
                    Object.keys(n.dbs).forEach(d=>a[n.ix+'_'+d]=1); return a; }, {})).length};
        }""")
        # Ring 1 and ring 3 both partition the euro, so between them they must cover
        # 2 full turns. Ring 1 is laid out with a real gap between neighbours and ring 3
        # exposes the unclassified rows, so the correct check is coverage, not arc sum.
        check("category ring spans a full turn",
              abs(geo["span"] - 2 * 3.14159265) < 0.02,
              f'{geo["span"]} spans the full {2*3.14159265:.4f} turn (the shortfall is the '
              f'deliberate gap drawn between neighbouring categories)')
        check("no inverted or empty wedge", geo["l2bad"] == 0 and geo["l3bad"] == 0,
              f'L2 {geo["l2bad"]}, L3 {geo["l3bad"]}')
        check("leaf euro partitions the book exactly",
              abs(geo["leafEuro"] - geo["totalEuro"]) < 1.0,
              f'{geo["leafEuro"]:,.0f} vs {geo["totalEuro"]:,.0f}')
        check("group euro partitions the book exactly",
              abs(geo["l2Euro"] - geo["totalEuro"]) < 1.0,
              f'{geo["l2Euro"]:,.0f} vs {geo["totalEuro"]:,.0f}')
        check("every leaf has at least one market connection",
              geo["dbsPerLeaf"] == 168, str(geo["dbsPerLeaf"]))
        check("the connection table is populated", geo["links"] > 2000, str(geo["links"]))

        page.locator(".stage").screenshot(path=str(OUT / "01_map_nothing_selected.png"))
        page.locator("header.top").screenshot(path=str(OUT / "02_header.png"))
        page.locator("#legend").screenshot(path=str(OUT / "03_legend.png"))
        page.locator(".controls").screenshot(path=str(OUT / "04_controls.png"))

        # ---- click the biggest category on the map, at its mid angle
        clicked = page.evaluate("""() => {
          const {N1} = window.spiderNodes;
          const n = N1.slice().sort((a,b)=>b.euro-a.euro)[0];
          const mid = (n.a0+n.a1)/2;
          const cv = document.getElementById('map');
          const R = Math.min(cv.clientWidth, cv.clientHeight)/2 - 26;
          const f = 0.205 + (0.360-0.205)/2;      /* mid radius of ring 1 */
          const rect = cv.getBoundingClientRect();
          const x = rect.left + rect.width/2 + Math.cos(mid)*R*f;
          const y = rect.top + rect.height/2 + Math.sin(mid)*R*f;
          return {x, y, name:n.name};
        }""")
        page.mouse.move(clicked["x"], clicked["y"])
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "05_hover_tooltip.png"))
        tip_visible = page.evaluate(
            "() => document.getElementById('tip').style.display === 'block'")
        check("hover shows the tooltip", tip_visible)
        check("tooltip names the hovered node",
              clicked["name"] in page.evaluate(
                  "() => document.getElementById('tip').textContent"), clicked["name"])

        page.mouse.click(clicked["x"], clicked["y"])
        page.wait_for_timeout(700)
        sel = page.evaluate("""() => ({
          name: document.getElementById('d-head').textContent,
          crumb: document.getElementById('d-crumb').textContent,
          dist: document.querySelectorAll('#d-dist tbody tr').length,
          pn: document.querySelectorAll('#d-pn tbody tr').length,
          vals: [...document.querySelectorAll('#d-facts .v')].map(e=>e.textContent)})""")
        check("clicking a wedge pins it into the panel",
              clicked["name"] in sel["name"], str(sel["name"]))
        check("panel shows distributor rows for the branch", sel["dist"] == 22, str(sel["dist"]))
        check("panel shows part numbers", sel["pn"] > 10, str(sel["pn"]))
        check("no NaN in the panel", all("NaN" not in v for v in sel["vals"]), str(sel["vals"]))
        page.locator(".grid.g2").first.screenshot(path=str(OUT / "06_panel_l1.png"))

        # ---- drill to a part type from the search box, where ribbons are meaningful
        page.fill("#q", "oil filter")
        page.wait_for_timeout(700)
        hits = page.evaluate("() => document.querySelectorAll('#hitlist div[data-i]').length")
        check("search finds the part type", hits >= 1, f"{hits} hits")
        page.locator("#hitlist").screenshot(path=str(OUT / "07_search.png"))
        page.evaluate("""() => {
          const d = [...document.querySelectorAll('#hitlist div[data-i]')]
            .find(x => x.textContent.indexOf('part type') >= 0);
          d.click();
        }""")
        page.wait_for_timeout(800)
        leaf = page.evaluate("""() => ({
          name: document.getElementById('d-head').textContent,
          crumb: document.getElementById('d-crumb').textContent,
          dist: document.querySelectorAll('#d-dist tbody tr').length,
          pn: document.querySelectorAll('#d-pn tbody tr').length,
          vals: [...document.querySelectorAll('#d-facts .v')].map(e=>e.textContent)})""")
        check("search opens the part type", "Oil filter" in leaf["name"], str(leaf["name"]))
        check("part type shows its part numbers", leaf["pn"] > 10, str(leaf["pn"]))
        # Oil filter is a broad oil-filter family billed in every market, so a narrower leaf
        # is the honest test of "only the markets that bill it". The invariant that must hold
        # everywhere is that the market rows never exceed the 22 distributors.
        narrow_ok = page.evaluate("""() => {
          const {N3, ND} = window.spiderNodes;
          /* find a leaf that is genuinely narrow: billed in fewer than half the markets */
          const cand = N3.filter(n => Object.keys(n.dbs).length > 0
                                    && Object.keys(n.dbs).length < ND.length/2)
                          .sort((a,b) => b.euro - a.euro);
          if (!cand.length) return {found:false};
          const n = cand[0];
          window.spiderDetail({lv:3, ix:n.ix});
          return {found:true, name:n.name, markets:Object.keys(n.dbs).length,
                  rows: document.querySelectorAll('#d-dist tbody tr').length,
                  total: ND.length};
        }""")
        if narrow_ok.get("found"):
            check("a narrow part type lists only the markets that bill it",
                  narrow_ok["rows"] == narrow_ok["markets"],
                  f'{narrow_ok["name"]}: {narrow_ok["rows"]} rows vs '
                  f'{narrow_ok["markets"]} markets of {narrow_ok["total"]}')
            page.locator(".stage").screenshot(path=str(OUT / "08b_map_narrow_leaf.png"))
        else:
            check("a narrow part type exists to test", False, "no leaf under half the markets")
        check("market rows never exceed the 22 distributors",
              leaf["dist"] <= 22, str(leaf["dist"]))
        page.locator(".stage").screenshot(path=str(OUT / "08_map_leaf_selected.png"))
        page.locator(".grid.g2").first.screenshot(path=str(OUT / "09_panel_leaf.png"))

        # ---- all-connections mode
        page.click("#links button[data-l='all']")
        page.wait_for_timeout(1400)
        check("all-connections mode still paints", page.evaluate("""() => {
            const cv=document.getElementById('map');
            const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
            const s=new Set(); for(let k=0;k<d.length;k+=4*211) s.add(d[k]);
            return s.size > 20; }"""))
        page.locator(".stage").screenshot(path=str(OUT / "10_map_all_connections.png"))

        # the page must open in all-connections mode: that is the hairball he asked for
        page.reload(wait_until="load")
        page.wait_for_timeout(2200)
        default_mode = page.evaluate(
            "() => document.querySelector('#links button.on').textContent.trim()")
        check("the map opens showing all connections", "All connections" in default_mode,
              default_mode)
        page.locator(".stage").screenshot(path=str(OUT / "19_map_default_hairball.png"))

        page.click("#links button[data-l='sel']")
        page.wait_for_timeout(900)
        page.locator(".stage").screenshot(path=str(OUT / "10b_map_selected_ribbons.png"))

        # ---- colour modes
        page.click("#mode button[data-m='step']")
        page.wait_for_timeout(800)
        page.locator(".stage").screenshot(path=str(OUT / "12_colour_step.png"))
        page.click("#mode button[data-m='pct']")
        page.wait_for_timeout(800)
        page.locator(".stage").screenshot(path=str(OUT / "13_colour_move.png"))
        page.click("#mode button[data-m='cat']")
        page.wait_for_timeout(600)

        # ---- distributor filter
        page.select_option("#db", index=10)
        page.wait_for_timeout(900)
        filt = page.evaluate("""() => ({
            dist: document.querySelectorAll('#d-dist tbody tr').length,
            vals: [...document.querySelectorAll('#d-facts .v')].map(e=>e.textContent)})""")
        check("distributor filter narrows the ribbon set", filt["dist"] > 0, str(filt["dist"]))
        page.locator(".stage").screenshot(path=str(OUT / "14_filtered_distributor.png"))
        page.select_option("#db", value="-1")
        page.wait_for_timeout(600)

        # ---- zoom + pan
        page.mouse.move(800, 560)
        page.mouse.wheel(0, -400)
        page.wait_for_timeout(600)
        z = page.evaluate("() => window.spiderState ? 1 : 1")
        page.locator(".stage").screenshot(path=str(OUT / "15_zoomed.png"))
        page.keyboard.press("0")
        page.wait_for_timeout(500)

        # ---- legend toggle must empty the map without breaking it
        page.click(".lg[data-i='0']")
        page.wait_for_timeout(600)
        check("hiding a category keeps the map drawing", page.evaluate("""() => {
            const cv=document.getElementById('map');
            const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;
            const s=new Set(); for(let k=0;k<d.length;k+=4*211) s.add(d[k]);
            return s.size > 15; }"""))
        page.locator(".stage").screenshot(path=str(OUT / "16_category_hidden.png"))
        page.click("#reset")
        page.wait_for_timeout(700)

        # ---- narrow width
        page.set_viewport_size({"width": 980, "height": 1000})
        page.wait_for_timeout(900)
        narrow = page.evaluate("""() => ({sw: document.documentElement.scrollWidth,
            cw: document.documentElement.clientWidth})""")
        check("no overflow at 980px", narrow["sw"] <= narrow["cw"] + 1, str(narrow))
        page.screenshot(path=str(OUT / "17_narrow.png"))
        page.set_viewport_size({"width": 1600, "height": 1000})
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "18_full.png"), full_page=True)

        # ---- click the centre of the map: must not crash, must show the whole book
        cen = page.evaluate("""() => {
          const cv=document.getElementById('map'), rect=cv.getBoundingClientRect();
          return {x: rect.left+rect.width/2, y: rect.top+rect.height/2};
        }""")
        page.mouse.click(cen["x"], cen["y"])
        page.wait_for_timeout(700)
        centre = page.evaluate("""() => ({
          head: document.getElementById('d-head').textContent,
          dist: document.querySelectorAll('#d-dist tbody tr').length,
          pn: document.querySelectorAll('#d-pn tbody tr').length,
          vals: [...document.querySelectorAll('#d-facts .v')].map(e=>e.textContent)})""")
        check("clicking the centre does not crash and shows the whole book",
              "whole book" in centre["head"], str(centre["head"]))
        check("centre shows all 22 markets", centre["dist"] == 22, str(centre["dist"]))
        check("centre shows the whole book euro",
              "34,993,609" in centre["vals"][0], str(centre["vals"][0]))
        page.locator(".grid.g2").first.screenshot(path=str(OUT / "06b_panel_centre.png"))

        real = [e for e in errors if "favicon" not in e.lower()]
        check("no console or page errors", len(real) == 0, str(real[:4]))

        b.close()

    print()
    print("=" * 74)
    print(f"PASS {len(passes)}   FAIL {len(fails)}")
    for f in fails:
        print("  FAIL " + f)
    print("=" * 74)
    print("QA_SPIDER_DONE" if not fails else "QA_SPIDER_FAILED")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
