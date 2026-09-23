#!/usr/bin/env python3
"""Read the actual members of a zip. Never trusts the folder on disk.

Usage: python _zip_probe.py <zip path> [<extract dir>]
Prints every member with size + CRC, and if asked, extracts to a temp dir and
re-reads the GPS file's column count and its 2026 capture cells FROM THE ZIP.
"""
from __future__ import annotations

import sys
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd


def main() -> int:
    zp = Path(sys.argv[1])
    print(f"=== {zp}")
    print(f"exists={zp.is_file()} bytes={zp.stat().st_size} "
          f"kb={zp.stat().st_size/1024:.1f} "
          f"mtime={pd.Timestamp(zp.stat().st_mtime, unit='s', tz='UTC').tz_convert('Europe/Amsterdam')}")
    with zipfile.ZipFile(zp) as zf:
        names = zf.namelist()
        print(f"members: {len(names)}  (dir entries: {sum(1 for n in names if n.endswith('/'))})")
        for i in zf.infolist():
            print(f"  {i.file_size:>9}  {i.CRC:08x}  {i.filename}")

        # --- GPS distributor file, read FROM THE ARCHIVE ---
        gps_names = [n for n in names if n.endswith("02_GPS/gps_spu_by_distributor.csv")]
        if gps_names:
            raw = zf.read(gps_names[0])
            df = pd.read_csv(BytesIO(raw))
            print(f"\n--- in-zip GPS file: {gps_names[0]}")
            print(f"    bytes={len(raw)}  rows={len(df)}  cols={len(df.columns)}")
            print(f"    columns={list(df.columns)}")
            print(f"    has period_basis={'period_basis' in df.columns}  "
                  f"has coverage_note={'coverage_note' in df.columns}")
            y26 = df[df["year"] == 2026]
            print(f"    2026 rows={len(y26)}")
            for c in ("gps_capture_vs_max", "traffic_light_v9",
                      "gps_capture_ex_warranty_vs_max", "traffic_light_v9_ex_warranty"):
                if c in df.columns:
                    print(f"    {c}: non-null on 2026 = {int(y26[c].notna().sum())}"
                          + (f"  values={sorted(set(y26[c].dropna().astype(str)))}"
                             if c.startswith('traffic') else ""))
            show = [c for c in ("year", "distributor_code", "total_sales_eur", "uio_units",
                                "spend_per_unit_eur", "max_spend_eur", "gps_capture_vs_max",
                                "traffic_light_v9", "period_basis") if c in df.columns]
            print(y26[show].head(6).to_string(index=False))
        else:
            print("\n!! no 02_GPS/gps_spu_by_distributor.csv inside the archive")

        h = [n for n in names if n.endswith("HOW_TO.md")]
        if h:
            txt = zf.read(h[0]).decode("utf-8", "replace")
            print(f"\n--- in-zip HOW_TO.md: {len(txt)} chars")
            print("    mentions 'part year':", "part year" in txt.lower())
            print("    mentions 'period_basis':", "period_basis" in txt)
            print("    mentions 'January to August':", "January to August" in txt)
            print("    mentions '178,453':", "178,453" in txt)

        m = [n for n in names if n.endswith("_pack_meta.json")]
        if m:
            print(f"\n--- in-zip _pack_meta.json:\n{zf.read(m[0]).decode('utf-8','replace')}")

    # extract for real, then re-read from the extraction
    if len(sys.argv) > 2:
        ex = Path(sys.argv[2])
        ex.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zp) as zf:
            zf.extractall(ex)
        files = [p for p in ex.rglob("*") if p.is_file()]
        print(f"\n=== extracted to {ex}: {len(files)} files")
        g = list(ex.rglob("gps_spu_by_distributor.csv"))
        if g:
            df = pd.read_csv(g[0])
            print(f"    re-read from extraction: cols={len(df.columns)} rows={len(df)}")
            print(f"    columns={list(df.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
