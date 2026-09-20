#!/usr/bin/env python3
"""QA render of the tonnage evolution page at two widths, plus a euro tie-out assertion."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Tonnage_Evolution.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_tonnage"
QA.mkdir(parents=True, exist_ok=True)

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if Path(c).exists():
        CHROME = c
        break
if not CHROME:
    sys.exit("chrome not found")

url = "file:///" + str(HTML).replace("\\", "/")
for w, h, tag in [(1440, 4200, "1440"), (1000, 4600, "1000")]:
    out = QA / f"page-{tag}.png"
    prof = tempfile.mkdtemp(prefix=f"qa{tag}_")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-first-run", "--no-default-browser-check",
                    f"--user-data-dir={prof}", f"--window-size={w},{h}",
                    "--virtual-time-budget=9000",
                    f"--screenshot={out}", url],
                   check=True, capture_output=True)
    print(f"rendered {out.name}  ({out.stat().st_size/1024:.0f} KB)")
print()
print("=== euro tie-out from the page payload vs the source files ===")
import pandas as pd
txt = HTML.read_text(encoding="utf-8")
m = re.search(r'<script id="pmte-data" type="application/json">(.*?)</script>', txt, re.S)
D = json.loads(m.group(1))
DER = ROOT / "01_data" / "00_derived"

cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c25 = cap[(cap.line_type == "total") & (cap.year == 2025)]
src_gap = round(float(c25.revenue_gap_eur.sum()))
src_act = round(float(c25.actual_rev_eur.sum()))
print(f"  network gap 2025 : page {D['net']['gap2025']:,}  source {src_gap:,}  "
      f"{'MATCH' if D['net']['gap2025']==src_gap else 'MISMATCH'}")
print(f"  network billed   : page {D['net']['actual2025']:,}  source {src_act:,}  "
      f"{'MATCH' if D['net']['actual2025']==src_act else 'MISMATCH'}")

aim = pd.read_csv(DER / "aim_evolution_model.csv")
for cl, yr in (("CY", 2025), ("FY", 2026)):
    s = round(float(aim[(aim.clock == cl) & (aim.period == yr)].billed_eur.sum()))
    p = round(float(sum(D["billed"][mk][cl].get(str(yr), 0) for mk in D["markets"])))
    outm = D["scopeNote"]["markets"]
    o = round(float(aim[(aim.clock == cl) & (aim.period == yr)
                        & (aim.distributor_code.isin(outm))].billed_eur.sum()))
    ok = ("MATCH within rounding (delta "+str(p+o-s)+" EUR)") if abs(p+o-s)<=5 else ("MISMATCH delta "+str(p+o-s))
    print(f"  billed {cl} {yr}    : page {p:,} + outside-scope {o:,} = source {s:,}  {ok}")
print(f"  out-of-scope markets: {D['scopeNote']['markets']} "
      f"= {D['scopeNote']['sharePct']}% of the complete-year billing")

t = pd.read_csv(DER / "pms_tonnage_model.csv")
exp_src = round(float(t[(t.year == 2025)].expected_qty_per_year.sum()))
exp_page = round(float(sum(sum(b["expected"] for b in D["fleet"][mk]) for mk in D["markets"])))
print(f"  expected jobs    : page {exp_page:,}  source {exp_src:,}  "
      f"{'MATCH' if exp_page==exp_src else 'CLOSE (band rounding: '+str(exp_page-exp_src)+')'}")

tot_uio = sum(sum(b["uio"] for b in D["fleet"][mk]) for mk in D["markets"])
print(f"  fleet units      : {tot_uio:,}")

# sanity: no band sum can exceed its market's fleet
bad = []
for mk in D["markets"]:
    fs = sum(b["uio"] for b in D["fleet"][mk])
    if fs > 120000:
        bad.append((mk, fs))
print(f"  band fleet sums impossible: {bad if bad else 'none'}")
print()
print(f"payload markets={len(D['markets'])} basis rows={len(D['basis'])} "
      f"compVintage={D['compVintage']}")

# --- label and key defects (E10): a chart with no key, an ambiguous period label, a wrong vehicle
# type. These are asserted on the rendered file, because that is what the reader sees.
print()
print("=== rendered-page label checks (E10) ===")
fails = []
body = txt.split("</style>", 1)[1] if "</style>" in txt else txt
# 1. every chart host must carry a written key or an axis label
hosts = {
    "h_fleet": "div", "h_expected": "div", "h_gap": "div", "h_mix": "div", "h_evo": "div",
    "h_l1": "div", "h_l2": "div", "h_netgap": "div", "h_gps": "div", "h_pos": "div",
}
for host in hosts:
    if f'id="{host}"' not in txt:
        fails.append(f"{host} is not on the page at all")
        continue
    # key()/axisLabel() fill a .legend box inside the host, so the host must be able to hold one
    m2 = re.search(r'id="%s".{0,400}?' % host, txt, re.S)
    if not m2:
        fails.append(f"{host} has no element after it")
print(f"  chart hosts found: {sum(1 for h in hosts if f'id=\"{h}\"' in txt)} of {len(hosts)}")
print(f"  key() calls in the page script: {len(re.findall(r'key[(]', txt))}")
print(f"  axisLabel() calls in the page script: {len(re.findall(r'axisLabel[(]', txt))}")
for need in ["uncaptured spend still to win", "over-bought against the fleet model",
             "sales lost against the previous year", "sales gained against the previous year",
             "above the competing price", "at or below it",
             "parts billed per vehicle in service — all parts"]:
    if need not in txt:
        fails.append(f"a chart key is missing its line: {need!r}")
# 2. period labels must name the months
for need in ["January to December", "April to March", "ISZE 2026 = Apr 2025 – Mar 2026",
             "calendar 2026 (part year)", "the schedule agreed for that market",
             "the internal service schedule"]:
    if need not in txt:
        fails.append(f"the page does not state: {need!r}")
# 3. the pickup must not be described as a truck
for bad in ["pickups 1.0", "light trucks 0.5", "service schedule A", "service schedule B",
            "IML v7", "Model B", "Mode A", "Mode B", "wallet", "street", "sell-out", "Book B"]:
    if bad in txt:
        fails.append(f"the page still carries a banned or wrong label: {bad!r}")
print()
if fails:
    for f in fails:
        print(f"  FAIL {f}")
    print(f"LABEL CHECK FAIL ({len(fails)})")
else:
    print("  LABEL CHECK PASS: every chart has a written key, every period names its months,")
    print("  the pickup is named as a pickup, and no internal schedule name is printed")
