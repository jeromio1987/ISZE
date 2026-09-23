"""Verify the three contained copies: annotation present, 2026 blank/unknown,
protected columns and every other column unchanged vs the backup."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BAK = ROOT / "01_data/91_build/_backsafe_20260922_partial_year/original"

FILES = [
    "01_data/15_gpt_safe/gps_spu_by_distributor.csv",
    "03_analytics/Isuzu/prism/evidence-app/data/derived/gps_spu_by_distributor.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_distributor.csv",
    "01_data/00_derived/gps_spu_by_distributor.csv",
]
CAPTURE = ("gps_capture_vs_max", "gps_capture_ex_warranty_vs_max")
LIGHT = ("traffic_light_v9", "traffic_light_v9_ex_warranty")
DERIVED = set(CAPTURE) | set(LIGHT) | {"period_basis", "coverage_note"}


def read(p: Path):
    raw = p.read_bytes()
    enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
    with p.open(encoding=enc, newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd), ("utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8")


for rel in FILES:
    cur = ROOT / rel
    bak = BAK / rel
    cols, rows, enc = read(cur)
    bcols, brows, benc = read(bak)
    key = lambda r: (r["year"], r["distributor_code"])
    b = {key(r): r for r in brows}
    a = {key(r): r for r in rows}

    print("=" * 100)
    print(rel)
    print(f"  rows {len(brows)}->{len(rows)}  cols {len(bcols)}->{len(cols)}  encoding {benc}->{enc}")
    added = [c for c in cols if c not in bcols]
    removed = [c for c in bcols if c not in cols]
    print(f"  columns added={added} removed={removed}")
    assert not removed, "a column disappeared"
    assert set(b) == set(a), "row set changed"
    assert enc == benc and len(brows) == len(rows)

    # 2026 must be blank/unknown with annotation
    bad = []
    for k, r in sorted(a.items()):
        if k[0] != "2026":
            continue
        for c in CAPTURE:
            if (r.get(c) or "").strip():
                bad.append(f"{k} {c}={r[c]!r}")
        for c in LIGHT:
            if (r.get(c) or "").strip() not in ("", "unknown"):
                bad.append(f"{k} {c}={r[c]!r}")
        if (r.get("period_basis") or "").strip() != "partial_year":
            bad.append(f"{k} basis={r.get('period_basis')!r}")
        if not (r.get("coverage_note") or "").strip():
            bad.append(f"{k} empty note")
    print("  2026 rows: " + ("FAIL " + "; ".join(bad[:8]) if bad else "OK - 22/22 blank capture, unknown light, annotated"))

    # everything else unchanged
    diffs = []
    for k in sorted(set(a) & set(b)):
        for c in bcols:
            if c in DERIVED:
                continue
            if (b[k].get(c) or "") != (a[k].get(c) or ""):
                diffs.append((k, c))
    print(f"  all non-derived cells unchanged: {not diffs}" + (f"  DIFFS={diffs[:10]}" if diffs else ""))

    # protected columns explicitly
    prot = ("total_sales_eur", "max_spend_eur", "uio_units", "spend_per_unit_eur")
    pd_ = [(k, c) for k in sorted(a) for c in prot if (b[k].get(c) or "") != (a[k].get(c) or "")]
    print(f"  protected columns (sales/target/fleet/per-truck) unchanged: {not pd_}" + (f" {pd_[:8]}" if pd_ else ""))

    # counts per year
    for y in sorted({r["year"] for r in rows}):
        sel = [r for r in rows if r["year"] == y]
        ncap = sum(1 for r in sel if (r.get("gps_capture_vs_max") or "").strip())
        tl = {}
        for r in sel:
            v = (r.get("traffic_light_v9") or "").strip() or "<blank>"
            tl[v] = tl.get(v, 0) + 1
        print(f"    {y}: n={len(sel)} with_capture={ncap} lights={tl}")
