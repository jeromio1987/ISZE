# -*- coding: utf-8 -*-
"""Did adding the delivery columns change any row the ledger already held?

Adding columns to a builder can silently re-key, re-order or drop rows. This script
compares the backup taken before the change with the ledger on disk now, row for row,
on every column that existed BEFORE the change. Nothing is inferred: the two files are
read and compared, and any difference is printed with the row it belongs to.

Run:
    python 04_tools/price_ledger/_u26_delivery_parity.py
"""
from __future__ import annotations

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
DERIVED = ROOT / "01_data" / "00_derived"
NOW = DERIVED / "price_observations.parquet"
BEFORE = DERIVED / "price_observations.parquet.bak_20261007T081251Z_before_delivery_col"

# The columns that existed before the delivery change. The comparison is on these only,
# so the two new columns cannot make an unchanged row look changed.
PRE_EXISTING = [
    "obs_id", "part_no", "match_method", "competitor_brand", "competitor_pn", "description",
    "source", "source_url", "country", "observed_at", "vintage",
    "price", "price_avg", "currency", "price_eur", "fx_note", "vat",
    "price_type", "stock", "n_obs", "loader",
]
NEW_COLUMNS = ["delivery_note", "delivery_included"]


def main() -> int:
    if not BEFORE.exists():
        raise SystemExit(f"no backup to compare against at {BEFORE}")
    before = pd.read_parquet(BEFORE)
    after = pd.read_parquet(NOW)
    print(f"before {BEFORE.name}: {len(before):,} rows, {len(before.columns)} columns")
    print(f"now    {NOW.name}: {len(after):,} rows, {len(after.columns)} columns")

    missing = [c for c in PRE_EXISTING if c not in after.columns]
    if missing:
        print(f"\nFAIL — the rebuild DROPPED pre-existing column(s): {missing}")
        return 1
    added = [c for c in after.columns if c not in before.columns]
    print(f"columns added by this change: {added}")
    if sorted(added) != sorted(NEW_COLUMNS):
        print(f"\nFAIL — expected exactly {NEW_COLUMNS} to be added")
        return 1
    if len(after) != len(before):
        print(f"\nFAIL — row count changed: {len(before):,} -> {len(after):,}")
        return 1

    b = before[PRE_EXISTING].fillna("<NA>").astype(str).reset_index(drop=True)
    a = after[PRE_EXISTING].fillna("<NA>").astype(str).reset_index(drop=True)
    diff = (b != a)
    if diff.to_numpy().any():
        rows = sorted(set(diff.index[diff.any(axis=1)]))
        cols = sorted(set(diff.columns[diff.any(axis=0)]))
        print(f"\nFAIL — {len(rows)} row(s) differ on pre-existing columns: {cols}")
        for i in rows[:5]:
            for c in cols:
                if b.at[i, c] != a.at[i, c]:
                    print(f"  row {i} {c}: {b.at[i, c]!r} -> {a.at[i, c]!r}")
        return 1

    # Report what the new columns actually hold, so the parity run also states the answer.
    stated = after[after["delivery_included"].astype(str).isin(["yes", "no"])]
    print("\nPARITY PASS — every pre-existing row is unchanged, row for row "
          "(same count, same order, same values).")
    print(f"new column coverage: {len(stated)} of {len(after):,} rows state a delivery basis "
          f"({sorted(stated['delivery_included'].astype(str).unique()) if len(stated) else 'none'}), "
          f"{len(after) - len(stated):,} are blank (the page stated nothing)")
    print(f"delivery_note filled on {int(after['delivery_note'].notna().sum())} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
