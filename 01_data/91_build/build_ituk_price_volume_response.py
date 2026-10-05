# -*- coding: utf-8 -*-
"""
ITUK dealer sell-out volume response to list price change, 2023 -> 2025.

This is a genuine two-period, part-number-level panel:
  quantity   = ITUK dealer sell-out, CY2023 vs CY2025 (network_pn grain)
  price      = IE40 PR00 list price, 2023 vs 2025 vintage

Both quantities are measured. No proxy, no fitted demand curve.

Outputs a distribution of implied arc elasticities by AIM family and by
price-class, plus the reconciliation against the quantity total.

Run: python 01_data/91_build/build_ituk_price_volume_response.py
Writes: 01_data/00_derived/ituk_price_volume_response.csv
        01_data/00_derived/ituk_price_volume_response_meta.json
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ISZE, "01_data", "00_derived")


def say(m):
    print(m)
    sys.stdout.flush()


# ---------------------------------------------------------------- 1. quantity
say("Loading ITUK dealer sell-out 2023 and 2025 ...")
qty = {}
for yr, f, gr in [(2023, "dealer_sellout_long_ITUK_CY2023.csv", "network_pn"),
                  (2025, "dealer_sellout_long_ITUK_CY2025.csv", "dealer_pn")]:
    d = pd.read_csv(os.path.join(D, f))
    d = d[d["grain"] == gr]
    d["pn"] = d["part_number"].astype(str).str.strip().str.zfill(10)
    d["qty"] = pd.to_numeric(d["qty"], errors="coerce")
    g = d.groupby("pn")["qty"].sum()
    qty[yr] = g
    say(f"  {yr}: {len(d):,} rows -> {len(g):,} part numbers, qty {g.sum():,.0f}")

q = pd.DataFrame({"q2023": qty[2023], "q2025": qty[2025]}).fillna(0.0)
say(f"  union of part numbers: {len(q):,}")

# ---------------------------------------------------------------- 2. price
say("Loading IE40 PR00 list, 2023 and 2025 vintage ...")
pr = {}
for yr, f in [(2023, "pricing_pr00_ie40_2023.parquet"),
              (2025, "pricing_pr00_ie40_2025.parquet")]:
    d = pd.read_parquet(os.path.join(D, f))
    d["pn"] = d["Material"].astype(str).str.strip().str.zfill(10)
    d["price"] = pd.to_numeric(d["Price_EUR"], errors="coerce")
    d = d[d["price"] > 0]
    g = d.groupby("pn")["price"].last()
    pr[yr] = g
    say(f"  {yr}: {len(d):,} rows -> {len(g):,} part numbers priced")

p = pd.DataFrame({"p2023": pr[2023], "p2025": pr[2025]})

# ---------------------------------------------------------------- 3. panel
df = q.join(p, how="inner")
say(f"  panel after join: {len(df):,} part numbers with both quantity and both prices")

# Only parts with real volume on both sides and a real price move.
# Requiring q2023 > 0 keeps the ratio interpretable.
core = df[(df["q2023"] > 0) & (df["q2025"] > 0) & (df["p2023"] > 0) & (df["p2025"] > 0)].copy()
say(f"  positive on both quantity and price: {len(core):,}")

core["price_pct"] = core["p2025"] / core["p2023"] - 1.0
core["qty_pct"] = core["q2025"] / core["q2023"] - 1.0
# arc elasticity, midpoint form
core["arc_elast"] = ((core["q2025"] - core["q2023"]) / (core["q2025"] + core["q2023"])) / \
                    ((core["p2025"] - core["p2023"]) / (core["p2025"] + core["p2023"]))

core = core.replace([np.inf, -np.inf], np.nan).dropna(subset=["arc_elast"])
say(f"  with a computable elasticity: {len(core):,}")

# ---------------------------------------------------------------- 4. AIM family
say("Attaching AIM family and price class ...")
aim = pd.read_csv(os.path.join(D, "aim_pn_classification_v2.csv"), dtype=str,
                  usecols=["part_number", "catalog_l1", "catalog_l2"])
aim["pn"] = aim["part_number"].astype(str).str.strip().str.zfill(10)
aim = aim.drop_duplicates("pn")
core = core.join(aim.set_index("pn")[["catalog_l1", "catalog_l2"]], how="left")

cls = pd.read_parquet(os.path.join(D, "pricing_list_pn.parquet"),
                      columns=["part_number", "price_class", "gm", "is_superseded_row"])
cls = cls[cls["is_superseded_row"] != True]          # noqa: E712
cls["pn"] = cls["part_number"].astype(str).str.strip().str.zfill(10)
cls = cls.drop_duplicates("pn")
core = core.join(cls.set_index("pn")[["price_class", "gm"]], how="left")


def bucket(g):
    """Volume-weighted summary of a slice of the panel."""
    w = g["q2023"]
    return pd.Series({
        "part_numbers": len(g),
        "qty_2023": g["q2023"].sum(),
        "qty_2025": g["q2025"].sum(),
        "qty_change_pct": 100 * (g["q2025"].sum() / g["q2023"].sum() - 1),
        "median_price_change_pct": 100 * g["price_pct"].median(),
        "median_elasticity": g["arc_elast"].median(),
        "weighted_elasticity": np.average(g["arc_elast"], weights=w) if w.sum() > 0 else np.nan,
        "share_elastic_lt_minus1": 100 * (g["arc_elast"] < -1).mean(),
    })


say("")
say("=" * 78)
say("HEADLINE: ITUK dealer sell-out volume against IE40 list price, 2023 -> 2025")
say("=" * 78)
tot = bucket(core)
for k, v in tot.items():
    say(f"  {k:28s} {v:,.3f}")
say("")
say("  Weighted quantity moved %.1f%% while list price moved a median %.1f%%."
    % (tot["qty_change_pct"], tot["median_price_change_pct"]))
say("")

say("--- by price class (the current pricing mechanism) ---")
byc = core.groupby("price_class").apply(bucket, include_groups=False)
byc = byc.sort_values("qty_2023", ascending=False)
say(byc.to_string(float_format=lambda v: f"{v:,.2f}"))
say("")

say("--- by AIM family, largest first ---")
byf = core.groupby("catalog_l1").apply(bucket, include_groups=False)
byf = byf.sort_values("qty_2023", ascending=False).head(16)
say(byf.to_string(float_format=lambda v: f"{v:,.2f}"))
say("")

# ---------------------------------------------------------------- 5. write
out = core.reset_index().rename(columns={"index": "pn"})
out.to_csv(os.path.join(D, "ituk_price_volume_response.csv"), index=False)

meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "distributor": "ITUK",
    "basis": {
        "quantity": "ITUK dealer sell-out, CY2023 (network_pn) vs CY2025 (dealer_pn rolled to network)",
        "price": "IE40 PR00 list EUR, 2023-12-31 vs 2025-12-31 vintage",
        "note": "Both sides measured. No fitted demand curve and no proxy.",
    },
    "panel": {
        "part_numbers_total": int(len(core)),
        "arc_elasticity_median": float(core["arc_elast"].median()),
        "arc_elasticity_weighted": float(tot["weighted_elasticity"]),
        "qty_2023": float(core["q2023"].sum()),
        "qty_2025": float(core["q2025"].sum()),
        "median_price_change_pct": float(100 * core["price_pct"].median()),
        "share_elastic_lt_minus1_pct": float(100 * (core["arc_elast"] < -1).mean()),
    },
    "caveats": [
        "Two periods only. A single difference cannot separate price response from parc, "
        "mix, model change, promotion or competitive entry. This is a cross-section of "
        "observed outcomes, not an estimated demand curve.",
        "The 2025 quantity file is dealer grain and has been rolled to network; the 2023 file "
        "is already network grain. Level differences between the two files are possible.",
        "Cars are not in scope here: this is ITUK CV only.",
        "A part number with rising volume and rising price contributes a positive elasticity, "
        "which is why the distribution is not expected to be centred on the truth.",
    ],
}
with open(os.path.join(D, "ituk_price_volume_response_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say(f"wrote {len(out):,} rows to ituk_price_volume_response.csv")
say("BUILD_OK")
