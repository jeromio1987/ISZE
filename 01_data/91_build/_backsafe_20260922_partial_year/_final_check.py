"""Final Task 6 verification, all in one read-only pass.

Covers: per-file 2023-2025 identity, the percentile values and their driver, the
pack disclosure, and the zip state.
"""
from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BAK = ROOT / "01_data/91_build/_backsafe_20260922_partial_year/original"
PACK = ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23"

COPIES = [
    "01_data/00_derived/gps_spu_by_distributor.csv",
    "01_data/15_gpt_safe/gps_spu_by_distributor.csv",
    "03_analytics/Isuzu/prism/evidence-app/data/derived/gps_spu_by_distributor.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_distributor.csv",
]
CAPTURE = ("gps_capture_vs_max", "gps_capture_ex_warranty_vs_max")
LIGHT = ("traffic_light_v9", "traffic_light_v9_ex_warranty")


def read(p: Path):
    raw = p.read_bytes()
    enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
    with p.open(encoding=enc, newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


print("=" * 100)
print("1. 2023-2025 byte-identity, per file")
for rel in COPIES:
    _, cur = read(ROOT / rel)
    _, old = read(BAK / rel)
    key = lambda r: (r["year"], r["distributor_code"])
    o, n = {key(r): r for r in old}, {key(r): r for r in cur}
    diffs = [
        (k, c, o[k][c], n[k][c])
        for k in sorted(set(o) & set(n))
        if k[0] in ("2023", "2024", "2025")
        for c in o[k]
        if (o[k].get(c) or "") != (n[k].get(c) or "")
    ]
    same = not diffs
    print(f"  {rel}")
    print(f"     2023-2025 cells: {'BYTE-IDENTICAL' if same else 'DIFFER'}"
          + ("" if same else f"  {diffs[:5]}"))

print("=" * 100)
print("2. every 2026 row is blank / unknown / annotated, all files")
for rel in COPIES:
    _, cur = read(ROOT / rel)
    y = [r for r in cur if r["year"] == "2026"]
    bad = []
    for r in y:
        for c in CAPTURE:
            if (r.get(c) or "").strip():
                bad.append(f"{r['distributor_code']}.{c}")
        for c in LIGHT:
            if (r.get(c) or "").strip() not in ("", "unknown"):
                bad.append(f"{r['distributor_code']}.{c}")
        if (r.get("period_basis") or "").strip() != "partial_year":
            bad.append(f"{r['distributor_code']}.period_basis")
        if not (r.get("coverage_note") or "").strip():
            bad.append(f"{r['distributor_code']}.coverage_note")
    print(f"  {rel}: 2026 n={len(y)} -> {'OK' if not bad else 'FAIL ' + str(bad[:6])}")

print("=" * 100)
print("3. network_percentile.csv - the four markets, and what actually moved")
np_now = pd.read_csv(ROOT / "01_data/00_derived/network_percentile.csv", dtype={"year": str})
np_head = pd.read_csv(
    io.StringIO(subprocess.run(
        ["git", "show", "HEAD:01_data/00_derived/network_percentile.csv"],
        cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8-sig")),
    dtype={"year": str},
)
for code in ("IUK", "HUNGARY", "GREECE", "ROMANIA", "UNMAPPED"):
    a = np_head[(np_head.metric == "gps_spu") & (np_head.year == "2026") & (np_head.distributor_code == code)]
    b = np_now[(np_now.metric == "gps_spu") & (np_now.year == "2026") & (np_now.distributor_code == code)]
    av = "absent" if a.empty else str(a.percentile_rank.iloc[0])
    bv = "absent" if b.empty else str(b.percentile_rank.iloc[0])
    print(f"  {code:9} committed={av:22} now={bv:22}")
s = np_now[(np_now.metric == "gps_spu") & (np_now.year == "2026")]
print(f"  2026 rows={len(s)} median={s.network_median.iloc[0]} n_distributors={s.n_distributors.iloc[0]}")

# toggling the UNMAPPED row on the CURRENT values
gps = pd.read_csv(ROOT / COPIES[0], dtype={"year": str})
base = gps[["year", "distributor_code", "spend_per_unit_eur"]].rename(columns={"spend_per_unit_eur": "raw_value"})
unm = pd.DataFrame([{"year": "2026", "distributor_code": "UNMAPPED", "raw_value": np.nan}])


def pct(v):
    n = v.notna().sum()
    if n <= 1:
        return pd.Series(np.nan, index=v.index)
    r = v.rank(method="min", ascending=True)
    return (r - 1) / (n - 1) * 100.0


for lbl, f in (("without row", base), ("with row", pd.concat([base, unm], ignore_index=True))):
    g = f[f.year == "2026"].copy()
    g["p"] = pct(g["raw_value"])
    print(f"  {lbl}: median={g.raw_value.median()} n_nonnull={g.raw_value.notna().sum()} "
          f"IUK={g[g.distributor_code=='IUK'].p.iloc[0]}")

print("=" * 100)
print("4. pack disclosure present")
howto = (PACK / "00_START_HERE/HOW_TO.md").read_text(encoding="utf-8")
for needle in ("2026 rows are a part year", "period_basis", "January–August 2025",
               "excluded_non_parts", "What the GPS rows exclude"):
    print(f"  HOW_TO.md contains {needle!r}: {needle in howto}")
man = (PACK / "00_START_HERE/MANIFEST.csv").read_text(encoding="utf-8-sig")
print(f"  MANIFEST has 'January-August' notes: {man.count('January-August')} rows")
print(f"  MANIFEST GPS cols reads 21: {'gps_spu_by_distributor.csv,88,21' in man}")

print("=" * 100)
print("5. hand-over zip state (NOT rebuilt)")
z = ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23.zip"
zf = zipfile.ZipFile(z)
for n in ("02_GPS/gps_spu_by_distributor.csv", "00_START_HERE/HOW_TO.md"):
    d = zf.read(n)
    print(f"  {n}: {len(d)} bytes sha={hashlib.sha256(d).hexdigest()[:16]}")
print(f"  members={len(zf.namelist())}")
