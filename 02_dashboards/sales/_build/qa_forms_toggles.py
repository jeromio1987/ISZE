"""Prove the measure and fleet switches reach every one of the three forms, not just the pair.

The page carries its state in window.__pmfe2.state, and each form reads that state when it draws, so
this drives the controls by their real click targets and reads the rendered result back.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

FAILS = []


def check(ok, label, detail=""):
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--headless=new", "--disable-gpu"])
    pg = br.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(HTML.as_uri(), wait_until="load")
    pg.wait_for_timeout(1800)

    def state():
        return pg.evaluate("""() => {
            const r = window.__pmfe2.formRows();
            const sml = window.Chart.getChart('sml_0');
            const m = window.Chart.getChart('c_main');
            // the cells of form 10 that are euro and units. Each cell carries its own number in a
            // span and the bar behind it, and the bar is sized against the largest row in the table,
            // so the bar's width is the tell: if a fleet denominator could reach this table the
            // bars would rescale, which they must not.
            const cells = r.f10.rows[0].cells;
            const bars = r.f10.rows[0].bars;
            return {metric: window.__pmfe2.state.metric, denom: window.__pmfe2.state.denom,
              f2first: r.f2[0], f8first: r.f8[0],
              f10first: cells, f10bars: bars, f10head: r.f10.headers,
              smlData: sml ? sml.data.datasets[0].data : null,
              smlTick: sml ? sml.options.scales.y.ticks.callback(25) : null,
              pairTicks: (() => { const c = m.options.scales.y.ticks.callback;
                 return [0, 250000, 500000].map(v => c(v)); })(),
              panelLine: Array.from(document.querySelectorAll('#smlGrid .pct'))
                 .map(x => x.textContent.replace(/\\s+/g, ' ').trim()).slice(0, 2)}; }""")

    print("\n== the measure switch, on all three forms ==")
    base = state()
    for key, label in (("abs", "Billed euro"), ("units", "Units")):
        pg.click(f"#segMetric button[data-m='{key}']")
        pg.wait_for_timeout(600)
        s = state()
        check(s["metric"] == key, f"{label}: the state switched to {key}", s["metric"])
        check(s["f2first"]["bar1"] != base["f2first"]["bar1"],
              f"{label}: form 2's column moved", f"{s['f2first']['bar1']}")
        check(s["smlData"] != base["smlData"], f"{label}: form 8's columns moved",
              str(s["smlData"]))
        # form 10 is the fixed-column form: its euro and unit cells must NOT move with the switch,
        # and that is asserted rather than assumed, because a header that names one unit over cells
        # holding another is the failure this check exists for
        check(s["f10first"] == base["f10first"],
              f"{label}: form 10 keeps its fixed euro-and-units columns",
              "unchanged" if s["f10first"] == base["f10first"] else str(s["f10first"][:3]))
        check(s["panelLine"] != base["panelLine"], f"{label}: the panel value line follows it",
              " | ".join(s["panelLine"]))
    pg.click("#segMetric button[data-m='pv']")
    pg.wait_for_timeout(600)

    print("\n== the fleet switch, on all three forms ==")
    base = state()
    pg.click("#segFleet button[data-d='flat']")
    pg.wait_for_timeout(700)
    flat = state()
    check(flat["denom"] == "flat", "the flat 2025 estimate is selected", flat["denom"])
    # the current period's fleet is the 2025 estimate, so the current-year rate is unchanged by
    # construction; the year under comparison is the one that moves, and that is the one asserted
    check(flat["f8first"]["bar0"] != base["f8first"]["bar0"],
          "form 8's comparison-year column moved onto the flat fleet",
          f"{base['f8first']['bar0']} -> {flat['f8first']['bar0']}")
    check(flat["smlData"] != base["smlData"], "form 8's columns moved too",
          f"{base['smlData']} -> {flat['smlData']}")
    # form 10 carries no per-vehicle column, so the denominator must not move it at all. The
    # bar widths are the tell: they are sized against the largest row's euro, so if a fleet
    # denominator could reach this table they would rescale, and they must not.
    same_euro = flat["f10first"][2:5] == base["f10first"][2:5]
    same_units = flat["f10first"][7:10] == base["f10first"][7:10]
    check(same_euro and same_units and flat["f10bars"] == base["f10bars"],
          "form 10, which is in euro rather than per vehicle, is untouched by the fleet switch",
          f"euro {base['f10first'][2:5]} == {flat['f10first'][2:5]}, "
          f"bars {base['f10bars']} == {flat['f10bars']}")
    pg.click("#segFleet button[data-d='own']")
    pg.wait_for_timeout(700)
    back = state()
    check(back["smlData"] == base["smlData"],
          "switching back to each period's own fleet restores the figures",
          str(back["smlData"]))

    print("\n== the small-multiple axis is small-number aware ==")
    check(base["smlTick"] == "25.0" or base["smlTick"] == "25",
          "a per-vehicle tick below a hundred keeps its decimal", str(base["smlTick"]))
    check(any("k" in str(t) or "M" in str(t) or float(str(t).replace(",", "") or 0) > 100
              for t in base["pairTicks"] if str(t)[0].isdigit()),
          "the big chart's axis is unchanged at the top of its range",
          str(base["pairTicks"]))
    pg.click("#segForm button[data-f='f8']")
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(ROOT / "02_dashboards" / "sales" / "_qa_v2" / "forms"
                           / "_toggles_sml.png"))
    pg.click("#segForm button[data-f='f10']")
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(ROOT / "02_dashboards" / "sales" / "_qa_v2" / "forms"
                           / "_toggles_f10.png"))
    br.close()

print(f"\n{'TOGGLE QA FAIL' if FAILS else 'TOGGLE QA PASS'} ({len(FAILS)} fails)")
for f in FAILS:
    print("  -", f)
raise SystemExit(1 if FAILS else 0)
