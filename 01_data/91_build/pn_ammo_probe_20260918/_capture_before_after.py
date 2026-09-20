"""Before/after: what the band-interval correction did to capture, per market and category.

Compares the pre-fix file (backed up) with the rebuilt one, so the size of the change is visible
before any dashboard quotes it.
"""

import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
before = pd.read_csv(DER + r"\pms_capture_by_db_year.csv.bak_pre_band_intervals_20260918")
after = pd.read_csv(DER + r"\pms_capture_by_db_year.csv")

KEY = ["distributor_code", "pms_category", "year", "line_type"]
COLS = {"expected_qty": "expected", "actual_qty": "actual", "capture_rate": "capture",
        "revenue_gap_eur": "gap_eur"}

b = before[KEY + list(COLS)].rename(columns=COLS)
a = after[KEY + list(COLS)].rename(columns=COLS)
m = b.merge(a, on=KEY, suffixes=("_before", "_after"))

tot = m[m.line_type == "total"].copy()
tot["exp_pct"] = (100 * (tot.expected_after / tot.expected_before - 1)).round(1)
tot["cap_pp"] = (100 * (tot.capture_after - tot.capture_before)).round(1)
tot["gap_delta"] = (tot.gap_eur_after - tot.gap_eur_before).round(0)

print("=" * 104)
print("EXPECTED DEMAND: how much each market's denominator moved")
print("=" * 104)
g = (tot.groupby("distributor_code")
     .agg(expected_before=("expected_before", "sum"), expected_after=("expected_after", "sum"))
     .round(0))
g["change_pct"] = (100 * (g.expected_after / g.expected_before - 1)).round(1)
print(g.sort_values("change_pct").to_string())

print()
print("=" * 104)
print("CAPTURE MOVES, weighted over the year (2025 shown — the year every dashboard quotes)")
print("=" * 104)
y = tot[tot.year == 2025].copy()
y["cap_before_pct"] = (100 * y.capture_before).round(1)
y["cap_after_pct"] = (100 * y.capture_after).round(1)
show = (y.groupby("distributor_code")
        .apply(lambda d: pd.Series({
            "cap_before_avg": d.cap_before_pct.mean().round(1),
            "cap_after_avg": d.cap_after_pct.mean().round(1),
            "move_pp": (d.cap_after_pct.mean() - d.cap_before_pct.mean()).round(1),
        }), include_groups=False))
print(show.sort_values("move_pp", ascending=False).to_string())

print()
print("=" * 104)
print("THE BIGGEST SINGLE CATEGORY MOVES (2025, top 15 by absolute capture change)")
print("=" * 104)
y = y.assign(abs_move=(y.capture_after - y.capture_before).abs())
big = y.sort_values("abs_move", ascending=False).head(15).copy()
big["cap_before_pct"] = (100 * big.capture_before).round(1)
big["cap_after_pct"] = (100 * big.capture_after).round(1)
big["move_pp"] = (100 * (big.capture_after - big.capture_before)).round(1)
print(big[["distributor_code", "pms_category", "cap_before_pct", "cap_after_pct", "move_pp",
           "expected_before", "expected_after"]].round(0).to_string(index=False))

print()
print("=" * 104)
print("ITUK SPECIFICALLY — the market whose two intervals started this")
print("=" * 104)
it = tot[(tot.distributor_code == "ITUK") & (tot.year == 2025)].copy()
it["cap_before_pct"] = (100 * it.capture_before).round(1)
it["cap_after_pct"] = (100 * it.capture_after).round(1)
it["move_pp"] = (100 * (it.capture_after - it.capture_before)).round(1)
print(it[["pms_category", "expected_before", "expected_after", "cap_before_pct", "cap_after_pct",
          "move_pp"]].round(0).to_string(index=False))
print()
print(f"  ITUK expected demand total: {it.expected_before.sum():,.0f} -> "
      f"{it.expected_after.sum():,.0f} "
      f"({100*(it.expected_after.sum()/it.expected_before.sum()-1):+.1f}%)")
print(f"  ITUK revenue gap: EUR {it.gap_eur_before.sum():,.0f} -> "
      f"EUR {it.gap_eur_after.sum():,.0f}")

print()
print("=" * 104)
print("ISRAEL / UTI — the Israel interval")
print("=" * 104)
ut = tot[(tot.distributor_code == "UTI") & (tot.year == 2025)].copy()
ut["cap_before_pct"] = (100 * ut.capture_before).round(1)
ut["cap_after_pct"] = (100 * ut.capture_after).round(1)
ut["move_pp"] = (100 * (ut.capture_after - ut.capture_before)).round(1)
print(ut[["pms_category", "expected_before", "expected_after", "cap_before_pct", "cap_after_pct",
          "move_pp"]].round(0).to_string(index=False))
