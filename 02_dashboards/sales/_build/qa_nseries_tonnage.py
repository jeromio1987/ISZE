#!/usr/bin/env python3
"""
Ship-gate check for the N-series tonnage level on the deep family page.

Drives the page in headless Chrome, reads back the band numbers the page has actually drawn,
and ties every one of them to `01_data/00_derived/nseries_tonnage_evolution.csv` — the file the
build writes. A band that does not tie is a FAIL, not a warning.

It also checks the three things that decide whether the level is honest:
  * the exclusive lines (fits-only, shared-once, weight-not-stated) add up to the N-series total,
  * the overlapping band lines are marked as overlapping rather than silently repeated,
  * the page states, on the band itself, how much of that band is shared.

Usage:
    python 02_dashboards/sales/_build/qa_nseries_tonnage.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_Deep.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_family_deep"
EVO = ROOT / "01_data" / "00_derived" / "nseries_tonnage_evolution.csv"
BANDED = ROOT / "01_data" / "00_derived" / "epc_decode_nseries_banded.csv"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

ALL18 = ["IUK", "ITUK", "UTI", "UMI", "BELGIUM", "GERMANY", "NORWAY", "SWEDEN", "IRELAND",
         "PORTUGAL", "GREECE", "CYPRUS", "HUNGARY", "ROMANIA", "DENMARK", "FINLAND", "MALTA",
         "ICELAND"]

DRIVER = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    var out={panels:{}, steps:[], fail:[]};
    function check(cond,msg){ if(!cond) out.fail.push(msg); return !!cond; }
    try{
      if(!window.__deepTest||!window.__deepTest.zonePanel){
        out.fail.push('the page carries no tonnage test hook');
      } else {
        /* the whole network, on both clocks, with the N-series in force */
        var st=window.__deepTest.set({cust:ALL18, fam:'n_series_truck', clock:'CY'});
        out.steps.push({tag:'N-series, all 18 markets, CY', state:st});
        out.panels.CY_ALL=window.__deepTest.zonePanel();

        window.__deepTest.set({clock:'FY'});
        out.panels.FY_ALL=window.__deepTest.zonePanel();

        /* one market on its own, so the market cut is exercised too */
        window.__deepTest.set({cust:['ITUK'], clock:'CY'});
        out.panels.CY_ITUK=window.__deepTest.zonePanel();

        /* walk the click-through: the ten band lines, then the service families inside a band */
        window.__deepTest.set({cust:ALL18, fam:'n_series_truck', clock:'CY', reset:true});
        var lv1=window.__deepTest.state();
        check(lv1.bandCards>=3,'fewer than three band cards were drawn: '+lv1.bandCards);
        check(lv1.bandSplitRows>=6,'the exclusive-versus-shared table has too few rows: '+lv1.bandSplitRows);
        check(lv1.bandEvRows>=9,'the sourced series table has too few rows: '+lv1.bandEvRows);
        out.steps.push({tag:'band level drawn', state:lv1});

        /* click the 3.5 t fits-only bar (index 0) and read the level beneath it */
        window.__deepTest.clickBar('c_drill',0);
        var lv2=window.__deepTest.state();
        check(lv2.drillBand==='3.5t_N35','clicking the 3.5 t band did not open it: '+lv2.drillBand);
        check(lv2.bread.indexOf('3.5')>=0,'the breadcrumb does not name the band: '+lv2.bread);
        check(lv2.drillInk&&lv2.drillInk.pct>0.4,
              'the drill canvas went blank inside the band: '+(lv2.drillInk?lv2.drillInk.pct:'null'));
        out.steps.push({tag:'opened the 3.5 t band', state:lv2});

        var labelled=window.__deepTest.labels('c_drill')||[];
        check(labelled.length>0,'the band has no service families');
        window.__deepTest.clickBar('c_drill',0);
        var lv3=window.__deepTest.state();
        check(lv3.pnRows>0,'opening a service family inside the band produced no part numbers');
        var tbl=document.querySelector('#t_pn').textContent;
        check(tbl.indexOf('weight band it fits')>=0,
              'the part-number table does not carry the band column');
        out.steps.push({tag:'opened a service family inside the band', state:lv3,
                        tableHead:tbl.slice(0,180)});

        /* the shared-across-bands line, opened by name */
        var shared=window.__deepTest.chooseBand('__shared_bands__');
        check(shared.drillBand==='__shared_bands__','could not reach the shared-across-bands line');
        check(shared.drillInk&&shared.drillInk.pct>0.4,'the shared line drew a blank canvas');
        out.steps.push({tag:'shared across bands', state:shared});
      }
    }catch(e){ out.fail.push('driver threw: '+String(e&&e.message?e.message:e)); }
    var el=document.createElement('script');
    el.type='application/json'; el.id='ton-out';
    el.textContent=JSON.stringify(out);
    document.body.appendChild(el);
  }, 3400);
});
</script>
"""


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    driver = DRIVER.replace("ALL18", json.dumps(ALL18))
    page = QA / "_tonnage.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", driver + "</body>"),
                    encoding="utf-8")
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1440,3000", "--virtual-time-budget=35000", "--dump-dom",
                        page.as_uri()], capture_output=True, text=True, timeout=420)
    m = re.search(r'<script type="application/json" id="ton-out">(.*?)</script>', r.stdout, re.S)
    if not m:
        print("TONNAGE QA FAIL: the driver did not run to completion")
        print((r.stderr or "")[:900])
        return 1
    out = json.loads(m.group(1))

    ev = pd.read_csv(EVO)
    fam = pd.read_csv(ROOT / "01_data" / "00_derived" / "pms_family_evolution_both_clocks.csv")
    fam["family"] = fam.family.replace({"unattributed": "no_vehicle_reference"})

    # zone id -> (tonnage_band, membership) in the evolution file, or a whole-family name
    ZMAP = {
        "n35_single": ("3.5t_N35", "single_band_only"),
        "n35_also": ("3.5t_N35", "also_fits_band"),
        "n55_single": ("5.5t_N50_N55", "single_band_only"),
        "n55_also": ("5.5t_N50_N55", "also_fits_band"),
        "n75_single": ("7.5t_N50_N62_N75", "single_band_only"),
        "n75_also": ("7.5t_N50_N62_N75", "also_fits_band"),
        "n_shared_bands": ("shared_across_bands", "pooled_all_bands"),
        "n_series_unresolved": ("unresolved_series", "series_unresolved"),
    }
    FAMZONE = ["heavy_truck", "light_vehicle", "shared_across_families",
               "no_vehicle_reference"]
    NS_EXCLUSIVE = ["n35_single", "n55_single", "n75_single", "n_shared_bands",
                    "n_series_unresolved"]

    def want_zone(key: str, zid: str, period: int) -> tuple[float, float, str]:
        sub = ev[(ev.clock == key[:2]) & ev.distributor_code.isin(ALL18 if key.endswith("ALL")
                                                                 else ["ITUK"])
                 & (ev.period == period)]
        if zid in ZMAP:
            band, mem = ZMAP[zid]
            g = sub[(sub.tonnage_band == band) & (sub.membership == mem)]
            return float(g.billed_eur.sum()), float(g.units.sum()), f"{band}/{mem}"
        if zid in FAMZONE:
            g = fam[(fam.clock == key[:2])
                    & fam.distributor_code.isin(ALL18 if key.endswith("ALL") else ["ITUK"])
                    & (fam.period == period) & (fam.family == zid)
                    & (fam.scope == "service_parts_only")]
            return float(g.billed_eur.sum()), float(g.units.sum()), f"family {zid}"
        return float("nan"), float("nan"), "not in the evolution file"

    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str) -> None:
        checks.append((name, bool(ok), detail))

    print("TONNAGE LEVEL, tied to the derived file")
    print("=" * 108)
    for key, panel in out["panels"].items():
        period = int(panel["latest"])
        print(f"\n  [{key}]  clock {panel['clock']}, latest complete period {period}")
        print(f"    {'line':30s} {'page EUR':>13s}  {'file EUR':>13s}  {'delta':>8s}  "
              f"{'page units':>11s}  source")
        for zid, v in panel["zones"].items():
            w, wu, src = want_zone(key, zid, period)
            if w != w:
                print(f"    {zid:30s} {v['eur']:13,.0f}  {'n/a':>13s}  {'':>8s}  {v['units']:11,.0f}  {src}")
                continue
            print(f"    {zid:30s} {v['eur']:13,.0f}  {w:13,.0f}  {abs(w - v['eur']):8,.1f}  "
                  f"{v['units']:11,.0f}  {src}")
            ck(f"{key}.{zid}.eur", abs(w - v["eur"]) <= 1.0,
               f"page EUR {v['eur']:,.2f} vs file EUR {w:,.2f} ({src})")
            ck(f"{key}.{zid}.units", abs(wu - v["units"]) <= 1.0,
               f"page {v['units']:,.1f} vs file {wu:,.1f} ({src})")
        for band, v in panel["bands"].items():
            tag = band.split("t_")[0].replace("3.5", "35").replace("5.5", "55").replace("7.5", "75")
            single = want_zone(key, f"n{tag}_single", period)[0]
            also = want_zone(key, f"n{tag}_also", period)[0]
            w = single + also
            ck(f"{key}.band.{band}.eur", abs(w - v["eur"]) <= 1.0,
               f"page band EUR {v['eur']:,.2f} vs file {w:,.2f}")

    # the exclusive N-series lines must add up to the N-series total, on that same period
    for key in ("CY_ALL", "FY_ALL"):
        panel = out["panels"][key]
        period = int(panel["latest"])
        sub = ev[(ev.clock == key[:2]) & ev.distributor_code.isin(ALL18) & (ev.period == period)]
        excl_file = float(sub[sub.sums_to_n_series_total == "yes"].billed_eur.sum())
        page_excl = sum(panel["zones"][z]["eur"] for z in NS_EXCLUSIVE if z in panel["zones"])
        ck(f"{key}.exclusive.sums_to_total", abs(excl_file - page_excl) <= 1.0,
           f"file exclusive N-series rows EUR {excl_file:,.2f} vs page exclusive lines "
           f"EUR {page_excl:,.2f}")

    # overlap marking: every also_fits zone must be flagged, and shared must be flagged as summing
    p = out["panels"]["CY_ALL"]
    for zid, v in p["zones"].items():
        if v["membership"] == "also_fits_band":
            ck(f"overlap.{zid}.not_summed", not v["sums"], "an overlapping band line claims to sum")
        else:
            ck(f"overlap.{zid}.sums", v["sums"], "an exclusive line does not sum")

    print()
    for tag in out.get("steps", []):
        s = tag.get("state") or {}
        print(f"  [walk] {tag['tag']:44s} band={s.get('drillBand')} "
              f"inks drill={((s.get('drillInk') or {}).get('pct'))} "
              f"band={((s.get('bandInk') or {}).get('pct'))}")

    fails = [c for c in checks if not c[1]]
    print()
    print(f"checks: {len(checks)} run, {len(fails)} failed")
    if out["fail"]:
        print("DRIVER FAILURES:")
        for f in out["fail"]:
            print("  - " + f)
    if fails:
        print("TIE-OUT FAILURES:")
        for n, _ok, d in fails:
            print(f"  - {n}: {d}")
    (QA / "deep_tonnage_qa.json").write_text(
        json.dumps({"checks": [{"id": n, "ok": o, "detail": d} for n, o, d in checks],
                    "driver_failures": out["fail"], "steps": out.get("steps", []),
                    "panels": out["panels"]}, indent=2), encoding="utf-8")
    if fails or out["fail"]:
        print("TONNAGE QA FAIL")
        return 1
    print("TONNAGE QA PASS: every band on the page ties to the derived file, the exclusive lines "
          "sum to the N-series total, the overlapping lines are marked and never summed, and the "
          "band level walks through to its part numbers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
