# -*- coding: utf-8 -*-
"""Patch U29b price_observations.parquet from filled UK delivery hand sheet."""
import csv
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

FILLED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UNIVERSE_UK_DELIVERY_TAX_FILLED_20261007.csv")
PARQUET = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet")

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
bak = PARQUET.with_name(f"price_observations.parquet.bak_{stamp}_before_uk_delivery_fill")
shutil.copy2(PARQUET, bak)
print("backup", bak)

fills = list(csv.DictReader(FILLED.open(encoding="utf-8-sig")))
by_id = {r["obs_id"]: r for r in fills}
print("fill rows", len(by_id))

df = pd.read_parquet(PARQUET)
print("parquet rows", len(df), "cols", list(df.columns))
if "obs_id" not in df.columns:
    raise SystemExit("no obs_id column")

# Ensure delivery columns exist
for col in ("delivery_included", "delivery_note"):
    if col not in df.columns:
        df[col] = None

patched = 0
tax_patched = 0
for i, row in df.iterrows():
    oid = str(row["obs_id"])
    if oid not in by_id:
        continue
    f = by_id[oid]
    db = (f.get("delivery_basis") or "").strip().lower()
    note = (f.get("delivery_note_hand") or "").strip()
    tax = (f.get("tax_basis") or "").strip().lower()
    if db in ("yes", "no"):
        df.at[i, "delivery_included"] = db
        if note:
            df.at[i, "delivery_note"] = note
        patched += 1
    if tax == "excluded" and "vat" in df.columns:
        cur = row.get("vat")
        if cur is None or (isinstance(cur, float) and pd.isna(cur)) or str(cur).strip().lower() in ("", "unknown", "nan"):
            df.at[i, "vat"] = "excl"
            tax_patched += 1
        # if already excl, leave; if other value, do not overwrite silently
    elif tax == "included" and "vat" in df.columns:
        cur = row.get("vat")
        if cur is None or (isinstance(cur, float) and pd.isna(cur)) or str(cur).strip().lower() in ("", "unknown", "nan"):
            df.at[i, "vat"] = "incl"
            tax_patched += 1

df.to_parquet(PARQUET, index=False)
print("patched delivery", patched, "tax_patched", tax_patched)

# verify
df2 = pd.read_parquet(PARQUET)
hit = df2[df2["obs_id"].astype(str).isin(by_id.keys())]
stated = hit[hit["delivery_included"].isin(["yes", "no"])]
print("verify stated among filled obs_ids", len(stated), "/", len(hit))
print(stated[["obs_id", "delivery_included", "vat"]].head(12).to_string(index=False))
