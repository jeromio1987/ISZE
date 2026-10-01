# -*- coding: utf-8 -*-
"""Did adding the scraped prices change anything that was already in the ledger?

The invariant: the **Eucon and KS sources must never move**. Those are the two big
blocks (821 + 81 rows) and they are the ones a pricing decision reads. A rebuild must not
silently restate them.

The two category-crawl sources (`tandm_commercials`, `tranzparts`) are a different case:
they are re-scraped on a schedule and their row count legitimately changes between runs.
On 2026-10-01 this check failed because T&M Commercials had gone from 91 rows to 62 —
the scheduled scraper had rewritten `tmc_results.csv` on 28 September, removing 29 rows
that carried a placeholder-level price. **That was the scraper working, not a regression**,
and the old fixed expectation simply predated it. They are now reported with their
previous value rather than asserted against it, so a real change is visible without a
scheduled refresh looking like a fault.

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

# Sources that must not move. Frozen 2026-09-24; Eucon and KS are what a pricing
# decision reads, and nothing in the web-pricing work should touch either.
BASELINE_STABLE = {
    "eucon_crossref": 821,
    "eucon_survey_2023": 68,
    "ks_gen": 41,
    "ks_am": 40,
}
STABLE_ROWS = sum(BASELINE_STABLE.values())            # 970

# Re-scraped on a schedule, so the count moves by design. Recorded, not asserted.
# (previous value, when it was last observed)
VOLATILE = {
    "tandm_commercials": (91, "2026-09-24 -> 62 after the 2026-09-28 scrape"),
    "tranzparts": (20, "2026-09-24"),
}
BASELINE_PNS = 113                                      # before any web price was loaded

SCRAPE_LOADERS = {"amayama", "ks", "omega", "geparden", "mekster", "tungen", "autoline"}


def main() -> int:
    if not LEDGER.exists():
        print(f"no ledger at {LEDGER} — run build_price_ledger.py first")
        return 1

    df = pd.read_parquet(LEDGER)
    print(f"ledger rows            : {len(df):,}")
    print(f"part numbers observed  : {df['part_no'].nunique():,}")

    problems: list[str] = []

    print("\nstable sources (must not move):")
    for loader, expected in sorted(BASELINE_STABLE.items()):
        got = int((df["loader"] == loader).sum())
        ok = got == expected
        print(f"   {'ok  ' if ok else 'FAIL'} {loader:<20} {got:>5}  (expected {expected})")
        if not ok:
            problems.append(f"{loader}: {got} rows, expected {expected}")

    print("\nre-scraped sources (change by design — recorded, not asserted):")
    for loader, (prev, note) in sorted(VOLATILE.items()):
        got = int((df["loader"] == loader).sum())
        moved = "" if got == prev else f"  (was {prev})"
        print(f"   info {loader:<20} {got:>5}{moved}   {note}")

    stable_total = int(df[df["loader"].isin(BASELINE_STABLE)].shape[0])
    volatile_total = int(df[df["loader"].isin(VOLATILE)].shape[0])
    print(f"\n   stable rows (Eucon+KS) : {stable_total:,}  (expected {STABLE_ROWS:,})")
    print(f"   re-scraped rows        : {volatile_total:,}")
    if stable_total != STABLE_ROWS:
        problems.append(f"stable rows {stable_total}, expected {STABLE_ROWS}")

    offered = 0
    if OFFERED.exists():
        o = pd.read_csv(OFFERED, dtype={"part_no": str})
        offered = int((~o["verdict"].astype(str).str.startswith("reject:")).sum()
                      if "verdict" in o.columns else len(o))
    scraped = int(df["loader"].isin(SCRAPE_LOADERS).sum())
    print(f"   web rows in ledger     : {scraped}  (bridge offered {offered})")
    if offered and scraped != offered:
        problems.append(f"web rows {scraped} but the bridge offered {offered}")

    priced_missing_eur = df[df["price"].notna() & df["price_eur"].isna()]
    print(f"   priced rows with no euro value: {len(priced_missing_eur)}")
    if len(priced_missing_eur):
        problems.append(f"{len(priced_missing_eur)} priced rows have no euro value")

    print()
    if problems:
        print("CHECK FAIL")
        for p in problems:
            print(f"   - {p}")
        return 1
    print(f"CHECK PASS — the stable sources are untouched at {STABLE_ROWS:,} rows, "
          f"and the web rows are exactly the additions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
