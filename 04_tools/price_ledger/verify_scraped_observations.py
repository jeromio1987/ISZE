# -*- coding: utf-8 -*-
"""Plan §5, check 1 — the verbatim check, on every loaded row, not a sample.

The plan says: *"every extracted price string and every part number must appear as a
substring of the source text sent. Fail -> rejects/."* A hand-assembled 5% sample is
weaker than that, and now that the source pages are on disk it is also unnecessary:
for each loaded row we can confirm the price and the part number are actually written
on the page the parser was given, so a parser that invents a number, reads the wrong
field, or carries a stale page is caught mechanically.

How it works — and why it is driven by OFFERED_ROWS.csv
-------------------------------------------------------
`build_scraped_observations.py` records, per row, the page file the parser was handed.
This script verifies THOSE rows against that page, then confirms each verified row is
present in the ledger.

An earlier version joined the ledger to the offered rows on `obs_id`. That was wrong:
the ledger recomputes `obs_id` from its own key, so the two ids are not guaranteed to
match, and a planted row was rejected for a page-lookup failure rather than for its
price. Reading the offered rows directly removes that coupling. Found by the planted-row
self-test (`_prove_verify_can_fail.py`), not by reasoning.

    python 04_tools/price_ledger/verify_scraped_observations.py
    python 04_tools/price_ledger/verify_scraped_observations.py --csv out.csv

Exit 0 only if every row verifies. A failure prints the reason and the exact form that
could not be found, so the fix is to add the missing form or correct the parser — never
to loosen the check.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[1]
PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
LEDGER = ISZE / "01_data" / "00_derived" / "price_observations.parquet"
OFFERED = HERE / "OFFERED_ROWS.csv"

# The loaders whose rows came from a saved web page. The rest are local files with
# their own provenance, already covered by the ledger's own notes.
SCRAPE_LOADERS = {"amayama", "ks", "omega", "geparden", "mekster", "tungen", "autoline"}


def price_forms(price: float, currency: str | None) -> list[str]:
    """Every way this site could have written the price. Any one exact match is enough."""
    forms: set[str] = set()
    for dp in (2, 1, 0):
        s = f"{price:.{dp}f}"
        forms.add(s)
        forms.add(s.replace(".", ","))
        if price >= 1000:
            forms.add(f"{price:,.{dp}f}")
            forms.add(f"{price:,.{dp}f}".replace(",", ".").replace(".", " ", 1))
            forms.add(f"{price:,.{dp}f}".replace(",", " "))
            forms.add(f"{price:,.{dp}f}".replace(",", ""))
    if abs(price - round(price)) < 1e-9:
        forms.add(str(int(round(price))))
    out = {f for f in forms if f}
    if currency:
        cur = currency.upper()
        sym = {"GBP": "£", "EUR": "€", "USD": "$"}.get(cur)
        for f in list(out):
            out.add(f"{f} {cur}")
            out.add(f"{cur} {f}")
            if sym:
                out.add(f"{sym}{f}")
                out.add(f"{sym} {f}")
    return sorted(out)


GRADED = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
_EDGES: set | None = None


def _key(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _usable_edges() -> set:
    """{(competitor key, isuzu part_no)} for graded edges tiered confirmed or likely."""
    global _EDGES
    if _EDGES is None:
        _EDGES = set()
        if GRADED.exists():
            g = pd.read_csv(GRADED, dtype=str)
            g = g[g["tier"].isin(["confirmed", "likely"])]
            _EDGES = {(_key(k), str(p)) for k, p in zip(g["cpn_key"], g["part_no"])}
    return _EDGES


def pn_forms(pn: str) -> list[str]:
    """Bare, dashed and prefixed ways an Isuzu number gets written.

    Sites group the same number differently — geparden writes `8982705240`, Tungen
    writes `8-98214687-0`, autoline writes `8-98204-942-0` — so the common groupings are
    enumerated. A number written in a grouping nobody thought of is reported, and that is
    correct: a human adds the grouping rather than the check being quietly loosened.
    """
    pn = str(pn)
    if len(pn) != 10:
        return [pn]
    return sorted({
        pn,
        f"ISU{pn}", f"isu{pn}", f"{pn}.UMI",
        f"{pn[0]}-{pn[1:6]}-{pn[6:9]}-{pn[9]}",      # 8-98214-687-0
        f"{pn[0]}-{pn[1:9]}-{pn[9]}",                # 8-98214687-0
        f"{pn[:3]}-{pn[3:5]}-{pn[5:9]}-{pn[9]}",     # 898-21-4687-0
        f"{pn[:3]}-{pn[3:6]}-{pn[6:]}",              # 898-270-5240
        f"{pn[:5]} {pn[5:]}",
    })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="write the per-row result here")
    a = ap.parse_args()

    if not OFFERED.exists():
        print(f"no offered rows at {OFFERED} — run build_scraped_observations.py first")
        return 1
    offered = pd.read_csv(OFFERED, dtype={"part_no": str, "page_file": str})
    offered = offered[offered["loader"].isin(SCRAPE_LOADERS)].copy()
    # Rows the bridge rejected are NOT loaded on purpose (a price at the placeholder
    # floor, a missing part number). Checking them against the ledger reports "not
    # present" every time and buries the real failures. They are counted, then separated.
    rejected = pd.DataFrame()
    if "verdict" in offered.columns:
        rej = offered["verdict"].astype(str).str.startswith("reject:")
        rejected = offered[rej]
        offered = offered[~rej]
    print(f"offered rows to verify : {len(offered)}")
    if len(rejected):
        print(f"rejected by the bridge : {len(rejected)} "
              f"(not loaded by design — {rejected['verdict'].str.slice(7, 60).iloc[0]})")

    ledger = pd.read_parquet(LEDGER)
    print(f"ledger rows total      : {len(ledger):,}")
    print()

    results = []
    fails = 0
    for _, r in offered.iterrows():
        page_file = str(r.get("page_file") or "").strip()
        row = {"loader": r["loader"], "part_no": r["part_no"], "price": r["price"],
               "currency": r["currency"], "price_type": r["price_type"],
               "page": page_file, "price_found": "", "pn_found": "",
               "in_ledger": "", "verdict": ""}

        if not page_file:
            row["verdict"] = "FAIL:no source page recorded for this row"
            fails += 1
            results.append(row)
            continue
        page = PROBE / page_file
        if not page.exists():
            row["verdict"] = f"FAIL:page not on disk ({page_file})"
            fails += 1
            results.append(row)
            continue

        text = page.read_text(encoding="utf-8", errors="replace")

        # --- the price must appear verbatim, unless the row has none -------------
        if pd.isna(r["price"]):
            row["price_found"] = "n/a (price-on-request row)"
            price_ok = True
        else:
            found = [f for f in price_forms(
                float(r["price"]),
                r["currency"] if pd.notna(r["currency"]) else None) if f in text]
            row["price_found"] = found[0] if found else ""
            price_ok = bool(found)

        # --- the part number must appear, unless the row is a category row -------
        pn_why = ""
        if pd.isna(r["part_no"]) or not str(r["part_no"]).strip():
            row["pn_found"] = "n/a (category row, no part number)"
            pn_ok = True
        elif str(r.get("match_method")) == "crossref":
            # A competitor's page never prints OUR number (mekster, since the 2026-10-02
            # fix). The verbatim test is then: the competitor number is written on the page,
            # AND a graded edge (confirmed/likely) links that number to this part_no.
            # Not a loosening: both halves must hold, and either one failing fails the row.
            cpn = str(r.get("competitor_pn") or "").strip()
            on_page = bool(cpn) and cpn in text
            edge_ok = (_key(cpn), str(r["part_no"])) in _usable_edges()
            row["pn_found"] = (f"competitor {cpn} on page; graded edge -> {r['part_no']}"
                               if on_page and edge_ok else "")
            pn_ok = on_page and edge_ok
            if not pn_ok:
                why = [] if on_page else [f"competitor number {cpn!r} not on page"]
                why += [] if edge_ok else [f"no confirmed/likely edge {cpn!r} -> {r['part_no']}"]
                pn_why = "; ".join(why)
        else:
            found = [f for f in pn_forms(str(r["part_no"])) if f in text]
            row["pn_found"] = found[0] if found else ""
            pn_ok = bool(found)

        # --- and the row must actually be in the ledger -------------------------
        same = ledger[(ledger["loader"] == r["loader"]) &
                      (ledger["price_type"] == r["price_type"]) &
                      (ledger["observed_at"].astype(str) == str(r["observed_at"]))]
        if pd.isna(r["price"]):
            same = same[same["price"].isna()]
        else:
            same = same[(same["price"] - float(r["price"])).abs() < 0.005]
        if pd.notna(r["part_no"]) and str(r["part_no"]).strip():
            same = same[same["part_no"].astype(str) == str(r["part_no"])]
        row["in_ledger"] = "yes" if len(same) else "NO"
        ledger_ok = len(same) > 0

        problems = []
        if not price_ok:
            problems.append(f"price {r['price']} {r['currency']} not written on the page")
        if not pn_ok:
            problems.append(pn_why or f"part number {r['part_no']} not written on the page")
        if not ledger_ok:
            problems.append("row is not present in the ledger")
        row["verdict"] = "PASS" if not problems else "FAIL:" + "; ".join(problems)
        if problems:
            fails += 1
        results.append(row)

        mark = "ok  " if not problems else "FAIL"
        print(f"  {mark} {r['loader']:<9} {str(r['part_no'] or '(none)'):<12} "
              f"{str(r['price']):>9} {str(r['currency'] or ''):<4} "
              f"price_as={row['price_found'] or '-':<14} pn_as={row['pn_found'] or '-'}")
        for p in problems:
            print(f"        {p}")

    print()
    print("=" * 78)
    print(f"verified: {len(offered) - fails}/{len(offered)}   failed: {fails}")
    by_loader: dict[str, list[int]] = {}
    for row in results:
        by_loader.setdefault(row["loader"], [0, 0])
        by_loader[row["loader"]][0] += 1
        if row["verdict"] != "PASS":
            by_loader[row["loader"]][1] += 1
    for k in sorted(by_loader):
        total, bad = by_loader[k]
        print(f"   {k:<10} {total - bad}/{total}")

    if a.csv:
        with open(a.csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(results[0].keys()) if results else [])
            w.writeheader()
            w.writerows(results)
        print(f"\nwrote {a.csv}")

    if fails:
        print(f"\nVERBATIM CHECK FAILED on {fails} row(s) — do not trust those rows")
        return 1
    print("\nVERBATIM CHECK PASS — every price and part number is written on its source "
          "page, and every row is in the ledger")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
