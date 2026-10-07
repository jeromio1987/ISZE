"""Coverage grid: which distributor reported which month, from the panel."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007")
rows = list(csv.DictReader((OUT / "kpi_panel.csv").open(encoding="utf-8")))

MONTHS = [f"2026-{m:02d}" for m in range(1, 13)]

# a distributor "reported" a month if it has any non-text KPI value that month
def has_value(v: str) -> bool:
    s = v.strip().upper()
    if not s or s in ("N/D", "N/A", "NA", "-", "--", "NODATA.", "NO DATA."):
        return False
    if s.startswith("NA ") or s.startswith("NO DATA") or s.startswith("NOT AVAILABLE"):
        return False
    return True


grid: dict[str, dict[str, str]] = defaultdict(dict)
for r in rows:
    if not r["period"].startswith("2026"):
        continue
    d = r["distributor"]
    if d.startswith("Isuzu OE /"):
        # shared-stock rows: label by country sub-name
        d = "Isuzu OE (" + d.split("/", 1)[1].strip() + ")"
    prev = grid[d].get(r["period"])
    mark = "Y" if has_value(r["value"]) else "n"
    if prev == "Y":
        continue
    grid[d][r["period"]] = mark

dist_sorted = sorted(grid)

# Distributors the consolidated master carries but which never produced a
# numeric value in any primary sheet: named explicitly (a non-reporter is a
# finding, not a blank).
NEVER_REPORTED = ["Greece", "UMI", "WAE (not in primary files)"]
for d in NEVER_REPORTED:
    grid.setdefault(d, {})
dist_sorted = sorted(grid)
lines = ["# Coverage grid - which distributor reported which month",
         "",
         "`Y` = at least one numeric KPI value for that month; "
         "`n` = the month is present but every KPI is N/D or free text; "
         "blank = the month does not appear at all.",
         "",
         "| distributor | " + " | ".join(m[5:] for m in MONTHS) + " |",
         "|---|" + "---|" * len(MONTHS)]
for d in dist_sorted:
    cells = []
    for m in MONTHS:
        cells.append(grid[d].get(m, ""))
    lines.append(f"| {d} | " + " | ".join(cells) + " |")

(OUT / "coverage_grid.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
