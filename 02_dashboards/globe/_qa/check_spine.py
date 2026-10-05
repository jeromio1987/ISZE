"""check_spine.py — verify the built market_spine.json is sound.

Re-runnable. Asserts the things the README and the page both claim, so a future
rebuild cannot quietly break them:

  - the reporting year is a complete year, not a part year
  - every drawn column has both measures populated
  - the two markets that share a coordinate in the source are still spread apart
  - markets with no target spend are still present and still marked as missing
  - the configured metrics resolve against the metric registry
  - no column is left with a zero or missing fleet denominator unlabelled

Exit code 0 means every assertion held.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPINE = HERE.parent / "data" / "market_spine.json"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "ok  " if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(label)


data = json.loads(SPINE.read_text(encoding="utf-8"))
settings = data["settings"]
columns = data["columns"]
unmodelled = data["unmodelled"]

print("=" * 72)
print("market_spine.json integrity check")
print("=" * 72)
print(f"generated: {data['generated']}")

print("\nperiod")
years = {c["year"] for c in columns} | {c["year"] for c in unmodelled}
check("a single reporting year is present", len(years) == 1, f"years={sorted(years)}")
year = sorted(years)[0]
check("the year is 2025 (most recent full year with a target spend)", year == 2025, f"year={year}")
check("only full_year rows are on the map",
      all(c["period_basis"] == "full_year" for c in columns),
      f"bases={sorted({c['period_basis'] for c in columns})}")
check("no partial_year row carries a column",
      not any(c["period_basis"] == "partial_year" for c in columns))

print("\ncolumns")
check("18 columns drawn", len(columns) == 18, f"n={len(columns)}")
check("every column has a euro gap",
      all(c["gap_eur"] is not None for c in columns))
check("every column has a capture value",
      all(c["capture_vs_max"] is not None for c in columns))
check("gap equals target spend minus parts billed (within 1 euro)",
      all(abs(c["gap_eur"] - (c["max_spend_eur"] - c["total_sales_eur"])) < 1.0
          for c in columns))
check("every column has geometry", all(c.get("geometry", {}).get("coordinates") for c in columns))

print("\nmetrics the page will paint")
for role in ("height_metric", "color_metric"):
    field = settings[role]
    check(f"{role} '{field}' exists in the metric registry",
          field in settings["metrics"])
    populated = sum(1 for c in columns if c.get(field) is not None)
    check(f"{role} '{field}' is populated on every column",
          populated == len(columns), f"{populated}/{len(columns)}")
    check(f"{role} '{field}' has a height reference",
          settings["metrics"][field].get("height_reference") is not None)

print("\nmarkets with no target spend")
check("4 markets carry no column", len(unmodelled) == 4, f"n={len(unmodelled)}")
codes = sorted(c["distributor_code"] for c in unmodelled)
check("they are the expected four", codes == ["ARMENIA", "KAZAKHSTAN", "PALESTINE", "UKRAINE"],
      str(codes))
check("they are marked as missing, not as zero",
      all(c["gap_eur"] is None and c["max_spend_eur"] is None for c in unmodelled))
check("they still carry their parts billed figure so the panel is not blank",
      all(c["total_sales_eur"] is not None for c in unmodelled))
check("their missing fleet denominator is flagged",
      all(c["uio_missing"] for c in unmodelled))

print("\nfleet denominator")
missing_uio = [c["distributor_code"] for c in columns if c["uio_missing"]]
check("no drawn column is silently missing its fleet count", not missing_uio, str(missing_uio))
check("every drawn column has a positive fleet count",
      all(isinstance(c["uio_units"], int) and c["uio_units"] > 0 for c in columns))

print("\nshared coordinates")
# In the source, ITUK and IUK share 54.0/-2.0, and UMI and UTI share 31.05/34.85.
pairs = {"ITUK": "IUK", "IUK": "ITUK", "UMI": "UTI", "UTI": "UMI"}
by_code = {c["distributor_code"]: c for c in columns}
for code, partner in pairs.items():
    c = by_code.get(code)
    check(f"{code} is on the map", c is not None)
    if c:
        check(f"{code} is flagged as sharing a coordinate",
              partner in c["coord_shared_with"], str(c["coord_shared_with"]))
        check(f"{code} explains the offset in its notes",
              any("same coordinate" in n for n in c["notes"]))
coords = {}
for c in columns:
    coords.setdefault((round(c["lat"], 3), round(c["lon"], 3)), []).append(c["distributor_code"])
clashes = {k: v for k, v in coords.items() if len(v) > 1}
check("no two columns sit on the identical point after spreading", not clashes, str(clashes))

# the pair must be far enough apart to read as two columns
if by_code.get("ITUK") and by_code.get("IUK"):
    import math
    a, b = by_code["ITUK"], by_code["IUK"]
    d = abs(a["lon"] - b["lon"]) * 111.320 * math.cos(math.radians(a["lat"]))
    check("the UK pair is spread at least 150 km apart", d >= 150, f"{d:.0f} km")

print("\nIsrael entity split")
umis = [c for c in columns if c["distributor_code"] == "UMI"]
utis = [c for c in columns if c["distributor_code"] == "UTI"]
check("UMI Israel is on the map", len(umis) == 1)
check("UTI Israel is on the map", len(utis) == 1)
if umis and utis:
    check("UMI and UTI are separate columns, never blended",
          umis[0]["id"] != utis[0]["id"])
    check("they have different labels", umis[0]["label"] != utis[0]["label"])

print("\nnot-yet-wired list")
items = {n["item"] for n in data["not_included"]}
for want in ("Warranty parts", "Fleet size workbook (UIO)", "Price revision",
             "Live tenders", "Sales to dealer"):
    check(f"'{want}' is declared as not included", want in items,
          "" if want in items else str(sorted(items)))
check("every not-included entry explains why",
      all(n.get("why") for n in data["not_included"]))

print("\npanel numbers")
check("every column carries parts-market-scan figures",
      all(c["pms"] is not None and c["pms"].get("total") for c in columns))
check("no panel is genuine-only (total capture is always present)",
      all(c["pms"].get("total") for c in columns if c["pms"]))

print()
print("=" * 72)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("all checks passed")
sys.exit(0)
