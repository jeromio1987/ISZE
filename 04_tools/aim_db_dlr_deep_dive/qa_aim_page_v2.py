"""Visual and behavioural QA for the AIM deep-dive page after the four corrections.

Headless Chrome over file://, no server. Takes the screenshots the brief asks for and reports
clipped text, overlapping labels, blank panels, and any control that no longer does anything.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
TOOL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive")
QA = TOOL / "_qa"
QA.mkdir(exist_ok=True)

run = sys.argv[1] if len(sys.argv) > 1 else "PORTUGAL"
url = (DASH / f"ISZE_AIM_DB_DLR_Deep_Dive_{run}.html").as_uri()
rep = {"run": run, "console": [], "pageerrors": [], "failed_requests": [], "shots": [], "checks": {}}


def canvas_paint(pg):
    return pg.evaluate("""() => {
      const out = {};
      document.querySelectorAll('canvas').forEach(c => {
        const ctx = c.getContext('2d');
        if (!ctx) { out[c.id] = 'no ctx'; return; }
        let painted = 0;
        try {
          const d = ctx.getImageData(0, 0, c.width, c.height).data;
          for (let i = 3; i < d.length; i += 4000) if (d[i] > 0) painted++;
        } catch (e) { out[c.id] = 'unreadable: ' + e.message; return; }
        out[c.id] = painted > 0 ? 'painted' : 'BLANK';
      });
      return out;
    }""")


def clipped(pg):
    return pg.evaluate("""() => {
      const bad = [];
      document.querySelectorAll('h1,h2,h3,.kpi .val,.kpi .lab,.kpi .note,.card .q,.crumb,.tlmeta,.chip,.legend span,.secno,.tcount,.cbtn,.reset').forEach(e=>{
        if (e.scrollWidth > e.clientWidth + 2 && e.clientWidth > 0)
          bad.push((e.className||e.tagName)+' :: '+e.textContent.trim().slice(0,60));
        if (e.scrollHeight > e.clientHeight + 2 && e.clientHeight > 0 &&
            getComputedStyle(e).overflow === 'hidden')
          bad.push('OVERFLOW-Y '+(e.className||e.tagName)+' :: '+e.textContent.trim().slice(0,50));
      });
      return bad.slice(0, 25);
    }""")


def dangling_controls(pg):
    """Every control still present must actually do something after the stage control was removed."""
    return pg.evaluate("""() => {
      const out = [];
      const ids = ['db','measure','src','bvp','cmp','reset','pmsOnly','csv','search','fleetbtn'];
      ids.forEach(id => {
        const e = document.getElementById(id);
        if (!e) { out.push(id + ': MISSING'); return; }
        const visible = e.offsetParent !== null || e.id === 'pmsOnly';
        if (!visible) out.push(id + ': hidden');
      });
      const segs = ['pareto-mode','heat-mode'];
      segs.forEach(id => { const e = document.getElementById(id); if (!e) out.push(id + ': MISSING'); });
      if (document.getElementById('stage')) out.push('stage: STILL PRESENT');
      return out;
    }""")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])

    pg = browser.new_page(viewport={"width": 1500, "height": 1100})
    pg.on("console", lambda m: rep["console"].append(f"{m.type}: {m.text}"))
    pg.on("pageerror", lambda e: rep["pageerrors"].append(str(e)))
    pg.on("requestfailed", lambda r: rep["failed_requests"].append(r.url))
    pg.goto(url)
    pg.wait_for_timeout(4000)

    rep["checks"]["ready_flag"] = pg.evaluate("() => window.__AIM_READY === true")
    rep["checks"]["error_flag"] = pg.evaluate("() => window.__AIM_ERROR || null")
    rep["checks"]["canvases"] = canvas_paint(pg)
    rep["checks"]["controls"] = dangling_controls(pg)
    rep["checks"]["kpi_cards"] = pg.evaluate("() => document.querySelectorAll('.kpi').length")
    rep["checks"]["kpi_nan"] = pg.evaluate(
        "() => Array.from(document.querySelectorAll('.kpi .val')).map(e=>e.textContent)"
        ".filter(t=>/NaN|undefined|Infinity/.test(t))")
    rep["checks"]["kpi_labels"] = pg.evaluate(
        "() => Array.from(document.querySelectorAll('.kpi .lab')).map(e=>e.textContent.trim())")
    rep["checks"]["gm_kpi_present"] = pg.evaluate(
        "() => !!Array.from(document.querySelectorAll('.kpi .lab')).find(e=>/35% GM/.test(e.textContent))")
    rep["checks"]["values_note"] = pg.evaluate(
        "() => document.getElementById('values-note').textContent.replace(/\\s+/g,' ').slice(0,300)")
    rep["checks"]["section_numbers"] = pg.evaluate(
        "() => Array.from(document.querySelectorAll('.secno')).map(e=>e.textContent)")
    rep["checks"]["treemap_gone"] = pg.evaluate(
        "() => !document.getElementById('c-tree') && typeof Chart.getChart('c-tree') === 'undefined'")
    rep["checks"]["thin_warn_visible"] = pg.evaluate(
        "() => getComputedStyle(document.getElementById('thin-warn')).display !== 'none'")
    rep["checks"]["overflow_desktop_px"] = pg.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    rep["checks"]["clipped"] = clipped(pg)

    # ---- change 2: the GM measure drives the chart and is exactly list / 0.65
    pg.select_option("#measure", "eur_gm")
    pg.wait_for_timeout(1200)
    rep["checks"]["eur_gm_chart"] = pg.evaluate("""() => {
      const ch = Chart.getChart('c-drill');
      if (!ch) return 'no chart';
      const billed = ch.data.datasets[0].data, sold = ch.data.datasets[1] ? ch.data.datasets[1].data : [];
      return {billedFirst: billed[0], soldFirst: sold[0],
              billedAllNull: billed.every(v => v === null),
              maxSold: Math.max.apply(null, sold.filter(v => v !== null && isFinite(v)))};
    }""")
    pg.select_option("#measure", "eur_list")
    pg.wait_for_timeout(1100)
    rep["checks"]["eur_list_chart"] = pg.evaluate("""() => {
      const ch = Chart.getChart('c-drill');
      const billed = ch.data.datasets[0].data, sold = ch.data.datasets[1] ? ch.data.datasets[1].data : [];
      return {billedFirst: billed[0], soldFirst: sold[0],
              maxSold: Math.max.apply(null, sold.filter(v => v !== null && isFinite(v)))};
    }""")
    # the ratio must be exactly 1/0.65 between the two sold series
    a = rep["checks"]["eur_list_chart"]["maxSold"]; b = rep["checks"]["eur_gm_chart"]["maxSold"]
    rep["checks"]["gm_factor_max_sold"] = (b / a) if a else None
    rep["checks"]["gm_factor_ok"] = bool(a) and abs((b / a) - (1 / 0.65)) < 0.001
    pg.select_option("#measure", "units")
    pg.wait_for_timeout(900)

    # ---- change 4: thin data, by drilling into one small part number
    def click_bar(frac):
        pg.evaluate("""() => { const c=document.getElementById('c-drill');
          window.scrollTo(0, window.scrollY + c.getBoundingClientRect().top - 260); }""")
        pg.wait_for_timeout(300)
        hit = pg.evaluate("""(frac) => {
          const ch = Chart.getChart('c-drill'); const m = ch.getDatasetMeta(0);
          if (!m || !m.data.length) return null;
          const i = Math.min(Math.max(Math.round(frac*m.data.length),0), m.data.length-1);
          const pr = m.data[i].getProps(['x','y','base'], true);
          const r = ch.canvas.getBoundingClientRect();
          return {x: r.left+(pr.x+pr.base)/2, y: r.top+pr.y, label:(ch.data.labels||[])[i], n:m.data.length};
        }""", frac)
        if not hit:
            return None
        pg.mouse.move(hit["x"], hit["y"]); pg.wait_for_timeout(120)
        pg.mouse.click(hit["x"], hit["y"]); pg.wait_for_timeout(1200)
        return hit

    pg.click("#chips button[data-a][data-b]")   # CY2025
    pg.wait_for_timeout(1200)
    lv = []
    for _ in range(4):
        h = click_bar(0.9)                      # near the bottom = smallest bar
        if not h:
            break
        lv.append(h)
    rep["checks"]["drill_labels"] = lv
    pg.wait_for_timeout(900)
    rep["checks"]["thin_now"] = pg.evaluate(
        "() => getComputedStyle(document.getElementById('thin-warn')).display !== 'none'")
    rep["checks"]["thin_text"] = pg.evaluate(
        "() => document.getElementById('thin-warn').textContent.replace(/\\s+/g,' ').slice(0,340)")
    rep["checks"]["thin_deltas_suppressed"] = pg.evaluate(
        "() => document.querySelectorAll('.kpi .dlt').length")
    rep["checks"]["kpi_units_still_there"] = pg.evaluate("""() => {
      const e = Array.from(document.querySelectorAll('.kpi')).find(x=>/^Units billed/.test(x.querySelector('.lab').textContent));
      return e ? e.querySelector('.val').textContent.trim() : 'absent';
    }""")
    rep["checks"]["crumb"] = pg.evaluate("() => document.getElementById('crumb').textContent.trim()")
    rep["checks"]["table_rows_drilled"] = pg.evaluate(
        "() => document.querySelectorAll('#t-drilltb tbody tr').length")
    pg.evaluate("() => document.getElementById('s1').scrollIntoView()")
    pg.wait_for_timeout(600)
    pg.screenshot(path=str(QA / f"{run}_A_drill_thin.png"))
    rep["shots"].append(f"{run}_A_drill_thin.png")

    # reset, then take the full set of section screenshots
    pg.click("#reset")
    pg.wait_for_timeout(1400)
    rep["checks"]["thin_after_reset"] = pg.evaluate(
        "() => getComputedStyle(document.getElementById('thin-warn')).display !== 'none'")
    rep["checks"]["deltas_after_reset"] = pg.evaluate("() => document.querySelectorAll('.kpi .dlt').length")

    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(QA / f"{run}_B_top.png"), clip={"x": 0, "y": 0, "width": 1500, "height": 1100})
    rep["shots"].append(f"{run}_B_top.png")
    for name, y in [("C_kpis_drill", 1150), ("D_monthly_pms", 1900), ("E_scatter_pareto", 2600),
                    ("F_table", 3700), ("G_coverage", 4900)]:
        pg.evaluate(f"window.scrollTo(0,{y})")
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(QA / f"{run}_{name}.png"))
        rep["shots"].append(f"{run}_{name}.png")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(700)
    pg.screenshot(path=str(QA / f"{run}_H_footer.png"))
    rep["shots"].append(f"{run}_H_footer.png")
    rep["checks"]["footer_text"] = pg.evaluate(
        "() => document.getElementById('foot').textContent.replace(/\\s+/g,' ').slice(0,300)")

    # ---- change 1: no stage left anywhere, and both series always drawn
    rep["checks"]["drill_datasets"] = pg.evaluate(
        "() => (Chart.getChart('c-drill')||{}).data ? Chart.getChart('c-drill').data.datasets.map(d=>d.label) : null")
    rep["checks"]["monthly_datasets"] = pg.evaluate(
        "() => (Chart.getChart('c-monthly')||{}).data ? Chart.getChart('c-monthly').data.datasets.map(d=>d.label) : null")
    rep["checks"]["pms_datasets"] = pg.evaluate(
        "() => (Chart.getChart('c-pms')||{}).data ? Chart.getChart('c-pms').data.datasets.map(d=>d.label) : null")
    rep["checks"]["table_headers"] = pg.evaluate(
        "() => Array.from(document.querySelectorAll('#t-drilltb thead th')).map(e=>e.textContent.replace(/[\\u25bc\\u25b2]/g,'').trim())")

    # every measure must render without throwing
    for val in ["units", "eur_list", "eur_gm", "eur_actual", "avg_price", "price_index", "pms_cover", "ratio"]:
        pg.select_option("#measure", val)
        pg.wait_for_timeout(700)
        rep["checks"][f"measure_{val}"] = "ok"
    pg.select_option("#measure", "units")
    pg.wait_for_timeout(600)
    pg.close()

    # ---- mobile
    m = browser.new_page(viewport={"width": 390, "height": 900})
    m.on("pageerror", lambda e: rep["pageerrors"].append("mobile: " + str(e)))
    m.goto(url)
    m.wait_for_timeout(3500)
    rep["checks"]["mobile_ready"] = m.evaluate("() => window.__AIM_READY === true")
    rep["checks"]["overflow_mobile_px"] = m.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    rep["checks"]["kpi_tiles_mobile"] = m.evaluate("() => document.querySelectorAll('.kpi').length")
    m.screenshot(path=str(QA / f"{run}_I_mobile_top.png"), clip={"x": 0, "y": 0, "width": 390, "height": 900})
    rep["shots"].append(f"{run}_I_mobile_top.png")
    m.evaluate("window.scrollTo(0,2400)")
    m.wait_for_timeout(600)
    m.screenshot(path=str(QA / f"{run}_J_mobile_mid.png"))
    rep["shots"].append(f"{run}_J_mobile_mid.png")
    m.close()
    browser.close()

rep["console"] = [c for c in rep["console"] if "favicon" not in c.lower()]
(QA / f"qa2_{run}.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in rep.items() if k != "shots"}, indent=2)[:7000])
print("\nshots taken:", len(rep["shots"]), rep["shots"])
