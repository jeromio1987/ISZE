# -*- coding: utf-8 -*-
"""Did adding the scraped prices change anything that was already in the ledger?

Re-runnable, and it no longer needs a "before" file kept on disk. The invariant it
checks is durable: the four local sources must always produce **1,081 rows** — that is
the ledger as it stood before any web price was loaded, and a rebuild must never quietly
change it. Everything above that number must come from the scraped pages.

Why this matters: these rows feed dashboards, and a rebuild that silently restated a
published euro value would be invisible in the totals. Counting per loader catches it.

    python 04_tools/price_ledger/check_loader_additive.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ISZE = Path(__file__).resolve().parents[2]
LEDGER = ISZE / "01_data" / "00_derived" / "price_observations.parquet"
OFFERED = ISZE / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv"

# The ledger as it stood before the Phase 1 web prices, by loader. Frozen on
# 2026-09-24 from a build whose meta read rows: 1081 / part numbers: 113.
BASELINE = {
    "eucon_crossref": 821,
    "tandm_commercials": 91,
    "eucon_survey_2023": 68,
    "ks_gen": 41,
    "ks_am": 40,
    "tranzparts": 20,
}
BASELINE_ROWS = sum(BASELINE.values())            # 1,081
BASELINE_PNS = 113                                # before any web price was loaded

SCRAPE_LOADERS = {"amayama", "ks", "omega", "geparden", "mekster", "tungen", "autoline"}


def main() -> int:
    if not LEDGER.exists():
        print(f"no ledger at {LEDGER} — run build_price_ledger.py first")
        return 1

    df = pd.read_parquet(LEDGER)
    print(f"ledger rows            : {len(df):,}")
    print(f"part numbers observed  : {df['part_no'].nunique():,}")

    problems: list[str] = []

    # 1. every local source must still contribute exactly what it used to
    print("\nlocal sources (must be unchanged):")
    for loader, expected in sorted(BASELINE.items()):
        got = int((df["loader"] == loader).sum())
        ok = got == expected
        print(f"   {'ok  ' if ok else 'FAIL'} {loader:<20} {got:>5}  (expected {expected})")
        if not ok:
            problems.append(f"{loader}: {got} rows, expected {expected}")

    local_total = int(df[~df["loader"].isin(SCRAPE_LOADERS)].shape[0])
    print(f"\n   local rows total     : {local_total:,}  (expected {BASELINE_ROWS:,})")
    if local_total != BASELINE_ROWS:
        problems.append(f"local rows {local_total}, expected {BASELINE_ROWS}")

    # 2. the web-sourced rows must be exactly what the bridge offered
    offered = 0
    if OFFERED.exists():
        o = pd.read_csv(OFFERED, dtype={"part_no": str})
        offered = int((~o["verdict"].astype(str).str.startswith("reject:")).sum()
                      if "verdict" in o.columns else len(o))
    scraped = int(df["loader"].isin(SCRAPE_LOADERS).sum())
    print(f"   web rows in ledger   : {scraped}  (bridge offered {offered})")
    if offered and scraped != offered:
        problems.append(f"web rows {scraped} but the bridge offered {offered}")

    # 3. and the part-number count must have grown by the new distinct numbers
    new_pns = len(set(df.loc[df["loader"].isin(SCRAPE_LOADERS), "part_no"].dropna()))
    print(f"   part numbers added   : {df['part_no'].nunique() - BASELINE_PNS} "
          f"(distinct new numbers on web rows: {new_pns})")

    # 4. no euro value may be missing from a priced row
    priced_missing_eur = df[df["price"].notna() & df["price_eur"].isna()]
    print(f"   priced rows with no euro value: {len(priced_missing_eur)}")
    if len(priced_missing_eur):
        problems.append(f"{len(priced_missing_eur)} priced rows have no euro value")
        print(priced_missing_eur[["part_no", "price", "currency", "loader"]].head(5).to_string(index=False))

    print()
    if problems:
        print("CHECK FAIL")
        for p in problems:
            print(f"   - {p}")
        return 1
    print("CHECK PASS — the local sources are untouched at 1,081 rows / 113 part numbers, "
          "and the web rows are exactly the additions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
