# -*- coding: utf-8 -*-
"""U26 delivery-basis — read the corrected coverage outputs back from disk and compare.

Reads the two files from disk (not the build log), side by side:
  * the backup taken before the change   (.bak_<ts>_before_delivery_col)
  * the file as rewritten in place

Reports, per market and family, EUROS FIRST then rows, with the three counts side by side:
  raw focus rows / usable rows / empty numbers and their billed euros.

Also answers the UK 79-row question specifically: of the 79 focus rows, how many carry a
delivery basis, how many became eligible, and which exclusion now blocks the rest.

Run:
    python 04_tools/price_ledger/_u26_delivery_before_after.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "01_data" / "00_derived"
TS = "20261007T081251Z"
BEFORE = D / f"market_data_gap_coverage_{TS[:8]}.metrics.json.bak_{TS}_before_delivery_col"
NOW = D / "market_data_gap_coverage_20261007.metrics.json"
BEFORE_CSV = D / f"market_data_gap_coverage_{TS[:8]}.csv.bak_{TS}_before_delivery_col"
NOW_CSV = D / "market_data_gap_coverage_20261007.csv"
# The billed-euros table travels in the META file, not the metrics file.
BEFORE_META = D / f"market_data_gap_coverage_{TS[:8]}.meta.json.bak_{TS}_before_delivery_col"
NOW_META = D / "market_data_gap_coverage_20261007.meta.json"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def family_eur(p: Path) -> dict:
    """Billed euros per (distributor, family), from the meta file's euros table."""
    m = load(p)
    out = {}
    for r in m.get("euros_2025_billed_line_type_all") or []:
        out[(r["distributor_code"], r["pms_category"])] = r["net_sales_eur"]
    return out


def family_empty_pns(csv_path: Path) -> dict:
    """Empty numbers per family from the coverage CSV (one row per number x market)."""
    d = pd.read_csv(csv_path)
    counts = {}
    for (market, fam), sub in d.groupby(["market", "pms_category"]):
        counts[(market, fam)] = {
            "rows": int(len(sub)),
            "eligible": int(sub["eligible_count"].sum()),
            "ledger_rows": int(sub["ledger_rows"].sum()),
        }
    return counts


def main() -> int:
    if not BEFORE.exists() or not NOW.exists():
        raise SystemExit(f"missing metrics file(s): {BEFORE} / {NOW}")
    b, a = load(BEFORE), load(NOW)
    print("=" * 96)
    print("METRICS READ BACK FROM DISK")
    print(f"  before : {BEFORE.name}")
    print(f"  now    : {NOW.name}")
    print()

    dists = {"UK": "ITUK", "PT": "PORTUGAL"}
    beur, aeur = family_eur(BEFORE_META), family_eur(NOW_META)
    print("=" * 96)
    print("PER MARKET AND FAMILY — EUROS FIRST, THEN ROWS")
    print(f"{'market':<6} {'dist':<9} {'family':<11} {'billed EUR FY2025':>18} "
          f"{'empty numb. EUR before':>23} {'empty numb. EUR now':>21}")
    print("-" * 96)
    for market, dist in dists.items():
        bm, am = b["by_market"][market], a["by_market"][market]
        first = True
        for fam in ("brake_pad", "oil_filter"):
            v = aeur.get((dist, fam))
            print(f"{market if first else '':<6} {dist if first else '':<9} {fam:<11} "
                  f"{(v if v is not None else float('nan')):>18,.2f} "
                  f"{(bm['empty_pns_billed_eur'] if first else float('nan')):>23,.2f} "
                  f"{(am['empty_pns_billed_eur'] if first else float('nan')):>21,.2f}")
            first = False
        # eligible euros per family, from the metrics detail
        per = {}
        for d in am.get("eligible_pns_detail") or []:
            per[d["pms_category"]] = per.get(d["pms_category"], 0.0) + (d.get("eur_all_billed") or 0)
        print(f"{'':<6} {'':<9} {'  eligible EUR':<11} "
              f"brake_pad {per.get('brake_pad', 0.0):,.2f} / oil_filter {per.get('oil_filter', 0.0):,.2f}")
    print(f"  billed EUR, ALL markets, focus list: {a['billed_eur_all_markets_focus']:,.2f}")
    print()
    print("=" * 96)
    print("THE THREE COUNTS SIDE BY SIDE (raw focus rows / usable rows / empty numbers + EUR)")
    print(f"{'market':<6} {'build':<10} {'raw focus':>10} {'usable':>8} {'status':>13} "
          f"{'empty_pns':>10} {'empty EUR':>16}")
    print("-" * 96)
    for market in dists:
        bm, am = b["by_market"][market], a["by_market"][market]
        for label, m in (("before", bm), ("now", am)):
            raw = m.get("focus_rows")
            use = m.get("usable_rows", m.get("eligible_rows"))
            st = m.get("sufficiency_status", m.get("focus_rows_status"))
            print(f"{market:<6} {label:<10} {raw:>10} {use:>8} {st:>13} "
                  f"{m['empty_pns']:>10} {m['empty_pns_billed_eur']:>16,.2f}")
    print()

    print("=" * 96)
    print("EXCLUSION REASONS BY COUNT")
    for market in dists:
        for label, m in (("before", b["by_market"][market]), ("now", a["by_market"][market])):
            rs = ", ".join(f"{r['reason']}={r['rows']}" for r in m["exclusions_by_reason"])
            print(f"  {market} {label:<7} {rs or '(none)'}")
    print()

    print("=" * 96)
    print("UK — THE 79-ROW QUESTION")
    am = a["by_market"]["UK"]
    print(f"  raw focus rows                     : {am['focus_rows']}")
    print(f"  usable (eligible) rows             : {am['usable_rows']}")
    print(f"  focus rows excluded                : {am.get('focus_rows_excluded')}")
    print(f"  rows stating a delivery basis      : {am.get('rows_stating_a_delivery_basis')}")
    print(f"  eligible part numbers              : {am['eligible_pns']}")
    print(f"  billed EUR of eligible numbers     : {am['billed_eur_of_eligible_pns']:,.2f}")
    print(f"  empty numbers / billed EUR         : {am['empty_pns']} / {am['empty_pns_billed_eur']:,.2f}")
    print()

    cov_b, cov_a = family_empty_pns(BEFORE_CSV), family_empty_pns(NOW_CSV)
    print("per market/family, from the COVERAGE CSV (numbers that have at least one row):")
    for key in sorted(set(cov_b) | set(cov_a)):
        cb, ca = cov_b.get(key, {}), cov_a.get(key, {})
        print(f"  {key[0]:<4} {key[1]:<11} numbers_with_rows {cb.get('rows','-'):>4} -> "
              f"{ca.get('rows','-'):>4}   eligible {cb.get('eligible','-'):>3} -> "
              f"{ca.get('eligible','-'):>3}   ledger_rows {cb.get('ledger_rows','-'):>5} -> "
              f"{ca.get('ledger_rows','-'):>5}")
    print()
    print("=" * 96)
    print("SUFFICIENCY LABEL — WHAT CHANGED")
    for market in dists:
        bm, am = b["by_market"][market], a["by_market"][market]
        print(f"  {market}: before '{bm.get('focus_rows_status')}' on {bm.get('focus_rows')} RAW "
              f"rows -> now '{am.get('sufficiency_status')}' on {am.get('usable_rows')} USABLE rows "
              f"(raw {am.get('focus_rows')} retained)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
