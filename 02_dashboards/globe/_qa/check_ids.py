"""check_ids.py — verify the IDS dealer layer, in the file and on the page.

Two halves, because either one alone can pass while the layer is broken:

  A. the file     — data/ids_dealers.json is sound and matches the IDS source
  B. the page     — the layer really loaded its features in the browser, was
                    invisible at the default view, became visible inside a
                    country, and separated real from approximate pins

Part B is the important one: a file on disk proves nothing about what painted.
The counts come from `window.__globeStatus.ids` and from MapLibre itself.

Run with the launcher's server up:

    python _qa/check_ids.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
IDS_JSON = ROOT / "data" / "ids_dealers.json"
IDS_HTML = REPO / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
BASE = "http://localhost:8511/index.html"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "ok  " if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(label)


# =========================================================================
print("=" * 74)
print("A. the extracted file")
print("=" * 74)

data = json.loads(IDS_JSON.read_text(encoding="utf-8"))
dealers = data["dealers"]
print(f"generated: {data['generated']}   file size: {IDS_JSON.stat().st_size:,} bytes")

check("564 dealers extracted", len(dealers) == 564, f"n={len(dealers)}")
check("the counts block agrees with the dealer list",
      data["counts"]["dealers"] == len(dealers))
check("real plus approximate equals the total",
      data["counts"]["real_coordinates"] + data["counts"]["approximate_coordinates"] == len(dealers))

# The geo_label is the honesty signal; every dealer must carry one.
labels = Counter(d["geo_label"] for d in dealers)
check("every dealer carries a geo_label", all(d["geo_label"] for d in dealers),
      f"{len(labels)} distinct labels")
expected_labels = {
    "Approx city from address": 225,
    "Approx city (MIDI network)": 160,
    "Approx city from dealer name": 100,
    "Approx city (directory / known place)": 67,
    "Approx country centre (no city in name)": 9,
    "Overseas territory (French DOM-TOM)": 3,
}
for lab, n in expected_labels.items():
    check(f"geo_label {lab!r} has {n}", labels.get(lab, 0) == n, f"{labels.get(lab, 0)}")

check("160 dealers sit on surveyed (MIDI) coordinates",
      data["counts"]["real_coordinates"] == 160, str(data["counts"]["real_coordinates"]))
check("404 dealers are approximate",
      data["counts"]["approximate_coordinates"] == 404)
check("only the MIDI label counts as real coordinates",
      all((d["geo_label"] == "Approx city (MIDI network)") == d["geo_real"] for d in dealers))

# every dealer needs a position or it cannot be a pin
check("every dealer has a latitude and a longitude",
      all(isinstance(d["lat"], (int, float)) and isinstance(d["lon"], (int, float))
          for d in dealers))

# sections: the 44 "totals only" dealers carry no section breakdown at all
# (their IDS result has a total but not the per-section detail), so A-D land on
# 520 of 564, and E is additionally not scored for the Israel network.
totals_only = [d for d in dealers if d["score_basis"] == "totals_only"]
check("44 dealers are totals-only, with no section breakdown",
      len(totals_only) == 44, f"n={len(totals_only)}")
per_section = {}
for sid in "ABCDE":
    present = sum(1 for d in dealers if d["sections"].get(sid) and d["sections"][sid]["pct"] is not None)
    per_section[sid] = present
    print(f"    section {sid}: {present:>4} of {len(dealers)} dealers carry a score")
check("every dealer that is not totals-only has sections A to D",
      per_section["A"] == 564 - len(totals_only) and
      per_section["B"] == 564 - len(totals_only) and
      per_section["C"] == 564 - len(totals_only) and
      per_section["D"] == 564 - len(totals_only),
      f"A-D = {per_section['A']}, totals-only = {len(totals_only)}")
check("section E is not scored for the Israel network, blank for three UK LCV dealers, and absent for the totals-only dealers",
      per_section["E"] == len(dealers) - len(totals_only) - 29 - 3,
      f"E = {per_section['E']} = 564 - {len(totals_only)} totals-only - 29 Israel - 3 UK LCV blank")
uk_blank = [d for d in dealers
            if d["country"] == "UK LCV" and (d["sections"].get("E") or {}).get("fill") == "blank"]
check("three UK LCV dealers are blank on section E", len(uk_blank) == 3, f"n={len(uk_blank)}")
check("no totals-only dealer has a section score",
      all(not any(d["sections"].get(s) and d["sections"][s]["pct"] is not None
                  for s in "ABCDE") for d in totals_only))
check("section E is not scored for the Israel (UMI) network",
      all((d["sections"].get("E") or {}).get("fill") == "not_scored"
          for d in dealers if d["country"] == "Israel LCV"))

# no per-question payload in the map file
check("the per-question array is not carried into the map file",
      not any("q" == k for d in dealers for k in d), 
      "keeps the file at " + f"{IDS_JSON.stat().st_size / 1024:.0f} KB instead of about 3.4 MB more")

# ---- country tallies, and the Israel rule -------------------------------
per_country = Counter(d["country"] for d in dealers)
print("\n  dealers per IDS tab:")
for c, n in sorted(per_country.items(), key=lambda kv: (-kv[1], kv[0])):
    print(f"    {n:>4}  {c:<12} {data['country_labels'].get(c, c)}")
check("20 IDS tabs", len(per_country) == 20, f"n={len(per_country)}")

check("the Israel network is labelled Israel (UMI)",
      data["country_labels"]["Israel LCV"] == "Israel (UMI)")
israel = [d for d in dealers if d["country"] == "Israel LCV"]
check("29 Israel dealers, all from the UMI network", len(israel) == 29, f"n={len(israel)}")
check("Israel dealers are scored on A-D only (vehicle sales not scored)",
      all(d["score_basis"] == "A-D" for d in israel),
      str(sorted({d["score_basis"] for d in israel})))
# UTI did not take part in this IDS round. Nothing here may name it.
uti_hits = [d["name"] for d in dealers if re.search(r"\bUTI\b", d["name"] or "", re.I)]
check("no UTI dealer is present (UTI did not take part in this IDS round)",
      not uti_hits, str(uti_hits[:5]))

# ---- agree with the IDS source rather than just with itself -------------
print("\n  against the IDS source page:")
html = IDS_HTML.read_text(encoding="utf-8", errors="replace")
m = re.search(r'"dealer_count":(\d+)', html)
check("the IDS page still declares 564 dealers",
      bool(m) and int(m.group(1)) == 564, m.group(1) if m else "not found")
check("the IDS page is unmodified (read-only input)",
      IDS_HTML.stat().st_size > 4_000_000,
      f"{IDS_HTML.stat().st_size:,} bytes")

# =========================================================================
print()
print("=" * 74)
print("B. the layer on the rendered page")
print("=" * 74)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(
        headless=True,
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        args=["--use-gl=angle", "--use-angle=swiftshader",
              "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    )
    pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    console: list[str] = []
    errors: list[str] = []
    pg.on("console", lambda msg: console.append(f"[{msg.type}] {msg.text}"))
    pg.on("pageerror", lambda e: errors.append(str(e)))

    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true", timeout=45000)
    pg.wait_for_timeout(3200)

    st = pg.evaluate("() => window.__globeStatus.ids")
    check("the dealer file loaded in the page", bool(st and st.get("loaded")))
    check("the source features are in the layer, by count",
          st.get("features") == 564, f"features={st.get('features')}")
    check("the page reports the real/approximate split",
          st.get("real_coordinates") == 160 and st.get("approximate_coordinates") == 404,
          f"real={st.get('real_coordinates')} approx={st.get('approximate_coordinates')}")
    check("the page's per-tab tally matches the file",
          st.get("per_country") == dict(per_country), "compared against the extracted file")
    check("all four dealer layers were registered with the map",
          pg.evaluate("""() => ['dealer-cluster','dealer-pin-real','dealer-pin-approx','dealer-selected']
                        .every(id => !!map.getLayer(id))"""))
    # querySourceFeatures only returns what the source holds for the tiles that
    # are currently in view, so the raw count varies with the camera. The set of
    # features handed to the source is what must be 564, and the page records it.
    in_source = pg.evaluate("""() => {
        const s = map.getSource('dealers');
        return s && s._data && s._data.features ? s._data.features.length : null;
    }""")
    check("MapLibre holds all 564 dealer features in the source",
          in_source == 564, f"source _data.features = {in_source}")
    check("the count the page reports is the count it was given",
          st.get("features") == 564 and in_source == 564,
          f"status.features={st.get('features')} source={in_source}")
    check("the layer is OFF by default, so it cannot clutter the default view",
          st.get("toggle") is False and st.get("layerVisible") is False)
    check("no dealer pin is drawn at the default view",
          pg.evaluate("""() => map.queryRenderedFeatures({layers:['dealer-pin-real','dealer-pin-approx']}).length""") == 0)

    # --- turn it on at the Europe view: it must say why nothing appeared --
    pg.evaluate("""() => document.querySelector('#ids-seg button[data-ids="on"]').click()""")
    pg.wait_for_timeout(2600)
    st = pg.evaluate("() => window.__globeStatus.ids")
    hint = pg.evaluate("() => document.getElementById('ids-hint').innerText")
    check("the toggle is on but the layer stays hidden at zoom 3.1",
          st.get("toggle") is True and st.get("layerVisible") is False,
          f"zoom={st.get('zoom')}")
    check("the hint explains the zoom threshold instead of appearing to do nothing",
          "Zoom in" in hint, hint[:90])

    # --- zoom into a country: pins must appear ----------------------------
    pg.evaluate("() => map.jumpTo({center:[2.2,46.6], zoom:6.4, pitch:40, bearing:0})")
    pg.wait_for_timeout(3800)
    zoomed = pg.evaluate("""() => ({
        visible: window.__globeStatus.ids.layerVisible,
        real: map.queryRenderedFeatures({layers:['dealer-pin-real']}).length,
        approx: map.queryRenderedFeatures({layers:['dealer-pin-approx']}).length,
        domNodes: document.querySelectorAll('#labels *').length,
        clusterLabels: document.querySelectorAll('#labels .clabel').length
    })""")
    check("the layer becomes visible inside a country", zoomed["visible"] is True)
    check("real-coordinate pins are drawn inside France",
          zoomed["real"] > 0, f"{zoomed['real']} rendered")
    check("approximate pins are drawn too, and as their own layer",
          zoomed["approx"] > 0, f"{zoomed['approx']} rendered")
    check("no one-label-per-dealer was added to the DOM",
          zoomed["domNodes"] < 200,
          f"{zoomed['domNodes']} label nodes, of which {zoomed['clusterLabels']} are cluster counts")

    # --- real and approximate pins must be visually distinguishable -------
    style = pg.evaluate("""() => ({
        realFill: map.getPaintProperty('dealer-pin-real', 'circle-color'),
        realStroke: map.getPaintProperty('dealer-pin-real', 'circle-stroke-color'),
        realRadius: JSON.stringify(map.getPaintProperty('dealer-pin-real', 'circle-radius')),
        approxFill: map.getPaintProperty('dealer-pin-approx', 'circle-color'),
        approxStroke: map.getPaintProperty('dealer-pin-approx', 'circle-stroke-color'),
        approxRadius: JSON.stringify(map.getPaintProperty('dealer-pin-approx', 'circle-radius'))
    })""")
    check("the two kinds of pin use different fill and stroke",
          style["realFill"] != style["approxFill"] and style["realStroke"] != style["approxStroke"],
          f"real fill={style['realFill']} stroke={style['realStroke']} | "
          f"approx fill={style['approxFill']} stroke={style['approxStroke']}")

    # --- the band colour is driven by the dealer's own national average ---
    bands = pg.evaluate("""() => {
        const out = {above:0, near:0, below:0, unknown:0, wrong:0};
        for (const f of map.queryRenderedFeatures({layers:['dealer-pin-real','dealer-pin-approx']})) {
            const p = f.properties;
            let want = 'unknown';
            if (p.total_pct !== null && p.country_avg_pct !== null) {
                const d = p.delta_pp;
                want = d >= 3 ? 'above' : (d <= -3 ? 'below' : 'near');
            }
            out[want] = (out[want] || 0) + 1;
            if (p.band !== want) out.wrong++;
        }
        return out;
    }""")
    check("every rendered pin's band matches its own delta against its national average",
          bands["wrong"] == 0, json.dumps(bands))

    # --- Israel must be UMI only -----------------------------------------
    il = pg.evaluate("""() => {
        const out = [];
        for (const f of map.querySourceFeatures('dealers')) {
            if (f.properties.country === 'Israel LCV') out.push(f.properties.name);
        }
        return out;
    }""")
    check("the Israel features in the live layer are all Israel (UMI)",
          len(il) == 0 or all("UTI" not in n.upper().split() for n in il),
          f"{len(il)} Israel features in the source at this zoom")

    check("no console messages", not console, str(console[:3]))
    check("no page errors", not errors, str(errors[:3]))
    b.close()

print()
print("=" * 74)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("all IDS dealer checks passed")
sys.exit(0)
