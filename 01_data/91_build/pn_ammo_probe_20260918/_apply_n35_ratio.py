"""Correct application of the N35 ratio: scale ONLY the cv_std component of expected demand.

The bug this replaces
--------------------
The first version multiplied the *whole* expected_qty by the market factor:

    expected_qty_new = expected_qty × factor

But expected_qty = cv_component + f_series_component + lcv_component, and the N35 interval ratio
only changes the **cv** component. Multiplying the total therefore inflated the LCV block as well —
which is why Belgium showed +91.8% when its LCV fleet (9,480 of its 9,593 vehicles) should not have
moved at all. Belgium's true move is about +0.5%.

The correction
--------------
For each market and category:

    cv_component = cv_std_uio × 0.5 × category_factor
    new_expected = expected_qty − cv_component + cv_component × market_factor

The category factor and any country override come from pms_capture_config, so this matches exactly
what the engine computes.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))

from modules.pms_capture_config import (  # noqa: E402
    BUCKET_SERVICES_PER_YEAR,
    CONSUMABLE_FACTOR,
    COUNTRY_OVERRIDES,
    LCV_BUCKET_FACTOR_OVERRIDES,
    WEAR_FACTOR,
)

LIVE = DER / "pms_capture_by_db_year.csv"
BAK = DER / "pms_capture_by_db_year.csv.bak_pre_n35_ratio_20260918"
AUDIT = DER / "pms_n35_ratio_applied_20260918.csv"

RATIO = 40_000 / 20_000  # N35 needs double the visits of N75
shares = pd.read_csv(PRISM / "data" / "uio_ld_n35_share.csv")
SHARE = {str(r["distributor_code"]): float(r["n35_share"]) for _, r in shares.iterrows()}
BUCKETS = pd.read_csv(PRISM / "data" / "uio_by_model_bucket.csv").set_index("distributor_code")

BASE_CV_RATE = BUCKET_SERVICES_PER_YEAR["cv_std"]          # 0.5
FACTORS = {**CONSUMABLE_FACTOR, **WEAR_FACTOR}


def market_factor(db: str) -> float:
    """Multiplier on the cv_std *visit rate* for this market. 1.0 = unchanged."""
    s = SHARE.get(db, 0.0)
    # UTI is excluded: its cv_std is an explicit 1.25 override and it has no 3.5 t fleet.
    if s <= 0 or db == "UTI":
        return 1.0
    return 1.0 + s * (RATIO - 1.0)


def cv_component(db: str, category: str) -> float:
    """The cv_std slice of expected demand, exactly as the engine builds it."""
    if db not in BUCKETS.index:
        return 0.0
    cv = float(BUCKETS.loc[db, "cv_std_uio"])
    factor = float(FACTORS.get(category, 0.0))
    override = (COUNTRY_OVERRIDES.get(db) or {}).get("factors") or {}
    if category in override:
        factor = float(override[category])
    return cv * BASE_CV_RATE * factor


# Always start from the pre-change baseline so this script is idempotent.
if not BAK.exists():
    raise SystemExit(f"baseline backup missing: {BAK}")
shutil.copy2(BAK, LIVE)
print(f"restored from {BAK.name}")

df = pd.read_csv(LIVE)
before = df.copy()

# One delta per (market, category), because expected_qty is the same for every year and line type.
pairs = df[["distributor_code", "pms_category"]].drop_duplicates()
deltas = {}
for _, r in pairs.iterrows():
    db, cat = r["distributor_code"], r["pms_category"]
    f = market_factor(db)
    if f == 1.0:
        continue
    cvc = cv_component(db, cat)
    deltas[(db, cat)] = cvc * (f - 1.0)

df["_delta"] = [deltas.get((d, c), 0.0) for d, c in zip(df.distributor_code, df.pms_category)]
df["expected_qty"] = df["expected_qty"] + df["_delta"]
df["capture_rate"] = df["actual_qty"] / df["expected_qty"].where(df["expected_qty"] > 0)
df = df.drop(columns=["_delta"])

# Report.
keep = ["distributor_code", "pms_category", "year", "line_type", "expected_qty", "actual_qty",
        "capture_rate", "revenue_gap_eur"]
audit = before[keep].merge(df[keep], on=["distributor_code", "pms_category", "year", "line_type"],
                           suffixes=("_before", "_after"))
audit["expected_pct"] = (100 * (audit.expected_qty_after / audit.expected_qty_before - 1)).round(2)
audit["capture_pp"] = (100 * (audit.capture_rate_after - audit.capture_rate_before)).round(1)

t = audit[audit.line_type == "total"].copy()
g = (t.groupby("distributor_code")
     .agg(exp_before=("expected_qty_before", "sum"), exp_after=("expected_qty_after", "sum"),
          trucks=("expected_qty_before", "size")).round(0))
g["change_pct"] = (100 * (g.exp_after / g.exp_before - 1)).round(2)
print()
print("=== expected demand: CORRECTED scaling, cv_std component only ===")
print(g.sort_values("change_pct", ascending=False).to_string())

print()
print("=== 2025 capture, per market ===")
y = t[t.year == 2025].copy()
cap = (y.groupby("distributor_code")
       .agg(cap_before=("capture_rate_before", "mean"), cap_after=("capture_rate_after", "mean"))
       .mul(100).round(1))
cap["move_pp"] = (cap.cap_after - cap.cap_before).round(1)
print(cap.sort_values("move_pp", ascending=False).to_string())

print()
print("=== Belgium, category by category (the market that exposed the bug) ===")
bz = y[y.distributor_code == "BELGIUM"].copy()
bz["cap_before_pct"] = (100 * bz.capture_rate_before).round(1)
bz["cap_after_pct"] = (100 * bz.capture_rate_after).round(1)
print(bz[["pms_category", "expected_qty_before", "expected_qty_after", "expected_pct",
          "cap_before_pct", "cap_after_pct"]].to_string(index=False))

print()
print("=== ITUK, category by category ===")
it = y[y.distributor_code == "ITUK"].copy()
it["cap_before_pct"] = (100 * it.capture_rate_before).round(1)
it["cap_after_pct"] = (100 * it.capture_rate_after).round(1)
print(it[["pms_category", "expected_qty_before", "expected_qty_after", "expected_pct",
          "cap_before_pct", "cap_after_pct"]].to_string(index=False))

df.to_csv(LIVE, index=False)
audit.to_csv(AUDIT, index=False)
print()
print(f"written -> {LIVE.name}")
print(f"audit   -> {AUDIT.name}")
