"""Read-only probe of the current state of every file in scope. Writes nothing."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

TARGETS = [
    ROOT / "01_data/00_derived/gps_spu_by_distributor.csv",
    ROOT / "01_data/15_gpt_safe/gps_spu_by_distributor.csv",
    ROOT / "03_analytics/Isuzu/prism/evidence-app/data/derived/gps_spu_by_distributor.csv",
    ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_distributor.csv",
    ROOT / "01_data/00_derived/network_percentile.csv",
    ROOT / "01_data/00_derived/aim_gps_matrix.csv",
    ROOT / "03_analytics/Isuzu/prism/scripts/enrich_gps_spu_v9.py",
]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


for p in TARGETS:
    print("=" * 100)
    print(p.relative_to(ROOT))
    if not p.exists():
        print("  MISSING")
        continue
    print(f"  exists  sha256={sha(p)[:16]}  bytes={p.stat().st_size}")
    if p.suffix != ".csv":
        continue
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("  (no data rows)")
        continue
    cols = list(rows[0].keys())
    print(f"  rows={len(rows)} cols={len(cols)}")
    print(f"  columns={cols}")
    ycol = "year"
    if ycol not in cols:
        print("  no year column")
        continue
    for yr in sorted({r[ycol] for r in rows}):
        sel = [r for r in rows if r[ycol] == yr]
        cap = [r for r in sel if (r.get("gps_capture_vs_max") or "").strip()]
        tl: dict[str, int] = {}
        for r in sel:
            k = (r.get("traffic_light_v9") or "").strip() or "<blank>"
            tl[k] = tl.get(k, 0) + 1
        extra = ""
        if yr == "2026":
            for c in ("period_basis", "coverage_note"):
                present = c in cols
                n_nonblank = sum(1 for r in sel if (r.get(c) or "").strip())
                extra += f"  {c}: present={present} nonblank={n_nonblank}"
        print(f"  {yr}: n={len(sel)} with_capture={len(cap)} lights={tl}{extra}")
        if yr == "2026":
            for r in sel:
                print(
                    "       ",
                    r.get("distributor_code"),
                    "| sales", r.get("total_sales_eur"),
                    "| max", r.get("max_spend_eur"),
                    "| cap", r.get("gps_capture_vs_max"),
                    "| tl", r.get("traffic_light_v9"),
                )
