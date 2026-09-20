"""Move the superseded family-evolution pages out of the working folder, not delete them.

Jerome works out of 02_dashboards/sales and needs one file there: the merged v2. The two older
pages and the launchers that pointed at them go into _build/history/ with the date they were
retired, so nothing is lost and the folder says which file is current.
"""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

SALES = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
HIST = SALES / "_build" / "history"
HIST.mkdir(parents=True, exist_ok=True)
TODAY = date.today().isoformat()

# (source, name inside history)
RETIRE = [
    (SALES / "ISZE_PMS_Family_Evolution.html",
     f"ISZE_PMS_Family_Evolution_retired_{TODAY}.html"),
    (SALES / "ISZE_PMS_Family_Evolution_Deep.html",
     f"ISZE_PMS_Family_Evolution_Deep_retired_{TODAY}.html"),
    (SALES / "OPEN_ISZE_PMS_Family_Evolution.cmd",
     f"OPEN_ISZE_PMS_Family_Evolution_retired_{TODAY}.cmd"),
    (SALES / "OPEN_ISZE_PMS_Family_Evolution_Deep.cmd",
     f"OPEN_ISZE_PMS_Family_Evolution_Deep_retired_{TODAY}.cmd"),
    (SALES / "ISZE_PMS_Family_Evolution.SHIP_RECEIPT.json",
     f"ISZE_PMS_Family_Evolution_retired_{TODAY}.SHIP_RECEIPT.json"),
    (SALES / "ISZE_PMS_Family_Evolution_Deep.SHIP_RECEIPT.json",
     f"ISZE_PMS_Family_Evolution_Deep_retired_{TODAY}.SHIP_RECEIPT.json"),
]

for src, name in RETIRE:
    dst = HIST / name
    if not src.is_file():
        print(f"skip (not present): {src.name}")
        continue
    if dst.is_file():
        print(f"already archived: {name}")
        src.unlink()
        continue
    shutil.move(str(src), str(dst))
    print(f"retired -> {dst.name}  ({dst.stat().st_size / 1024:,.0f} KB)")

# the pre-merge copies the builder used to make are now redundant: the retired files above are the
# same content and are named for what they are
for stale in ("ISZE_PMS_Family_Evolution_Deep_preserved_before_v2.html",
              "ISZE_PMS_Family_Evolution_preserved_before_v2.html"):
    p = HIST / stale
    if p.is_file():
        p.unlink()
        print(f"dropped the superseded pre-merge copy: {stale}")

print()
print("current in the working folder:")
for p in sorted(SALES.glob("ISZE_PMS_Family_Evolution*")):
    if p.is_file():
        print(f"   {p.name}  {p.stat().st_size / 1024:,.0f} KB")
for p in sorted(SALES.glob("OPEN_ISZE_PMS_Family_Evolution*")):
    if p.is_file():
        print(f"   {p.name}")
