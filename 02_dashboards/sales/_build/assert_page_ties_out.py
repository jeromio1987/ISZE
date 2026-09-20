"""Assert every euro figure on the page ties back to its source file.

The page embeds its payload as JSON. This reads that payload straight out of the built HTML and
recomputes each headline figure from the derived CSVs, so a number that drifted between the
calculation and the page is caught rather than trusted.

Usage:
    python 02_dashboards/sales/_build/assert_page_ties_out.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution.html"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"


def main() -> int:
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r'<script id="pmfe-data" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        print("FAIL: the page carries no embedded payload")
        return 1
    D = json.loads(m.group(1))

    core = pd.read_csv(DER / "pms_capture_by_family.csv")
    evo = pd.read_csv(DER / "pms_family_evolution_both_clocks.csv")
    pub = pd.read_csv(DER / "pms_capture_by_db_year.csv")
    gps = pd.read_csv(DER / "gps_spu_by_distributor.csv")
    buckets = pd.read_csv(PRISM / "data" / "uio_by_model_bucket.csv")

    checks, fails = [], []

    def check(name: str, page_val, source_val, tol=1.0, unit="EUR"):
        ok = (page_val is None and source_val is None) or (
            page_val is not None and source_val is not None
            and abs(float(page_val) - float(source_val)) <= tol)
        checks.append((name, page_val, source_val, ok))
        if not ok:
            fails.append(name)

    # 1. network billed euro, 2025, page vs the core file and vs the published capture file
    src = float(core[core.year == 2025].billed_eur.sum())
    check("net.billed_eur vs pms_capture_by_family.csv", D["net"]["billed_eur"], src)
    pubsrc = float(pub[(pub.line_type == "total") & (pub.year == 2025)
                       & (pub.distributor_code.isin(D["markets"]))].actual_rev_eur.sum())
    check("net.billed_eur vs pms_capture_by_db_year.csv", D["net"]["billed_eur"], pubsrc)

    # 2. network implied euro, 2025
    check("net.expected_eur vs pms_capture_by_family.csv", D["net"]["expected_eur"],
          float(core[core.year == 2025].expected_eur.sum()))

    # 3. each customer's per-family billed euro
    for db in D["markets"]:
        for f in D["cust"][db]["families"]:
            s = float(core[(core.distributor_code == db) & (core.year == 2025)
                           & (core.family == f["family"])].billed_eur.sum())
            check(f"{db}/{f['family']} billed", f["billed_eur"], s)
            e = float(core[(core.distributor_code == db) & (core.year == 2025)
                           & (core.family == f["family"])].expected_eur.sum())
            check(f"{db}/{f['family']} implied", f["expected_eur"], e)

    # 4. every trend point on both clocks, service parts, 18 markets
    for clock in ("CY", "FY"):
        T = D["trend"][clock]["service_parts_only"]
        for fam, blk in T["family"].items():
            for p, v in blk["eur"].items():
                s = evo[(evo.clock == clock) & (evo.scope == "service_parts_only")
                        & (evo.family == fam) & (evo.period == int(p))
                        & (evo.distributor_code.isin(D["markets"]))].billed_eur.sum()
                check(f"trend {clock}/{fam}/{p} eur", v, float(s))

    # 5. the small multiples
    for clock in ("CY", "FY"):
        ct = D["custTrend"][clock]["n_series_truck"]
        for p, per_market in ct.items():
            for db, v in per_market.items():
                if v is None:
                    continue
                s = evo[(evo.clock == clock) & (evo.scope == "service_parts_only")
                        & (evo.family == "n_series_truck") & (evo.period == int(p))
                        & (evo.distributor_code == db)].billed_eur.sum()
                check(f"custTrend {clock}/NS/{db}/{p}", v, float(s), tol=1.0)

    # 6. the fleet numbers
    for db in D["markets"]:
        b = buckets[buckets.distributor_code == db]
        if b.empty:
            continue
        check(f"{db} fleet N-series", D["fleet"][db]["n_series"], float(b.cv_std_uio.iloc[0]))
        check(f"{db} fleet heavy", D["fleet"][db]["heavy"], float(b.f_series_uio.iloc[0]))
        check(f"{db} fleet light", D["fleet"][db]["light"], float(b.lcv_uio.iloc[0]))

    # 7. spend per vehicle
    for r in D["gap"]:
        g = gps[(gps.distributor_code == r["db"]) & (gps.year == 2025)]
        if g.empty:
            continue
        check(f"{r['db']} spend per vehicle", r["spu"], float(g.spend_per_unit_eur.iloc[0]), tol=0.05)

    # 8. the two interval schedules must survive into the payload untouched
    lanes = sorted(set(D["lane"].values()))
    if lanes != ["IML v7 (ITUK)", "PRISM network"]:
        fails.append(f"payload lanes {lanes}")

    ok_n = sum(1 for c in checks if c[3])
    print("=" * 96)
    print(f"EURO AND FLEET TIE-OUT: {ok_n} of {len(checks)} checks pass")
    print("=" * 96)
    for name, pv, sv, ok in checks:
        if not ok:
            print(f"  FAIL {name:52s} page {pv}  source {sv}")
    print()
    print(f"  network 2025 billed  page EUR {D['net']['billed_eur']:,}  "
          f"source EUR {src:,.0f}  published EUR {pubsrc:,.0f}")
    print(f"  network 2025 implied page EUR {D['net']['expected_eur']:,}")
    print(f"  checks per clock     CY {sum(1 for c in checks if c[0].startswith('trend CY'))}  "
          f"FY {sum(1 for c in checks if c[0].startswith('trend FY'))}")
    print()
    if fails:
        print(f"TIE-OUT FAIL: {len(fails)} mismatch(es)")
        return 1
    print("TIE-OUT PASS: every euro, fleet and spend figure on the page ties to its source file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
