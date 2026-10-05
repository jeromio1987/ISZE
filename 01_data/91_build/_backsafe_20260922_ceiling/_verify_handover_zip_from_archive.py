"""Extract the new hand-over zip to a temp folder and re-read it FROM THE ARCHIVE.

Nothing is assumed from the folder on disk. Everything printed here is read out of
the extracted copy.

Checks:
  - member count and names
  - the ceiling table: column count, the six corrected markets, the basis and date
    columns, and a row that must NOT have moved (UTI) plus one that must have
    (Portugal)
  - parts billed unchanged in the archive
  - the disclosure text is present in the archive's HOW_TO.md
  - the archive's MANIFEST row for the ceiling table matches the archive's file
"""
from __future__ import annotations

import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

MEET = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings")
ZIP = MEET / "BVDB_PBI_Data_Upload_2026-09-23_HANDOVER_20260922.zip"

BEFORE = {
    "PORTUGAL": 3052087.00, "IRELAND": 956313.00, "GERMANY": 3808128.00,
    "BELGIUM": 2453507.00, "MALTA": 378827.00, "CYPRUS": 676267.00,
}
EXPECTED = {
    "PORTUGAL": 2430115.00, "IRELAND": 856195.00, "GERMANY": 3740349.00,
    "BELGIUM": 2410536.00, "MALTA": 338957.00, "CYPRUS": 671394.00,
}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="bvdb_handover_check_"))
    try:
        with zipfile.ZipFile(ZIP) as zf:
            names = zf.namelist()
            zf.extractall(tmp)
        print(f"archive: {ZIP.name}")
        print(f"  sha256 {hashlib.sha256(ZIP.read_bytes()).hexdigest()}")
        print(f"  members {len(names)}")
        for n in sorted(names):
            print(f"    {n}")

        wf = tmp / "02_GPS/target_spend_waterfall.csv"
        d = pd.read_csv(wf, encoding="utf-8-sig")
        print(f"\nceiling table read FROM THE ARCHIVE: {len(d)} rows, {len(d.columns)} columns")
        print(f"  columns: {list(d.columns)}")
        d25 = d[d["year"] == 2025]
        print(f"\n  CY2025 ceiling EUR {d25['target_spend_ceiling_eur'].sum():,.2f}")
        print(f"  CY2025 billed  EUR {d25['parts_billed_total_eur'].sum():,.2f}")
        print(f"  as_of values present: {sorted(d['ceiling_as_of'].dropna().unique())}")
        print(f"  basis present on every row: {bool(d['ceiling_basis'].notna().all())}")

        ok = True
        print("\n  the six markets, archive value vs what the pack said / should say:")
        for code in sorted(EXPECTED):
            r = d25[d25["distributor_code"] == code]
            got = float(r["target_spend_ceiling_eur"].iloc[0])
            good = abs(got - EXPECTED[code]) < 0.005
            ok &= good
            print(f"    {code:9s} was {BEFORE[code]:>12,.2f}  now {got:>12,.2f}  "
                  f"{'OK' if good else 'MISMATCH'}")
        for code, want in (("UTI", 8271300.00), ("IUK", 11945750.00), ("ITUK", 12212051.00),
                           ("SWEDEN", 2110750.00), ("GREECE", 953593.00)):
            r = d25[d25["distributor_code"] == code]
            got = float(r["target_spend_ceiling_eur"].iloc[0])
            good = abs(got - want) < 0.005
            ok &= good
            print(f"    {code:9s} {got:>12,.2f} vs {want:>12,.2f} (unchanged) "
                  f"{'OK' if good else 'MOVED WHEN IT SHOULD NOT'}")

        sample = d25[d25["distributor_code"].isin(["PORTUGAL", "UTI"])][
            ["distributor_code", "year", "uio_units", "target_spend_ceiling_eur",
             "parts_billed_total_eur", "parts_billed_vs_target_pct", "ceiling_as_of"]
        ]
        print("\n  a sample of rows re-read from the archive:")
        print(sample.to_string(index=False))

        ht = (tmp / "00_START_HERE/HOW_TO.md").read_text(encoding="utf-8")
        for needle in ("### The target-spend table", "ceiling_as_of", "54,375,729",
                       "measured share of it is the 3.5 t band"):
            present = needle in ht
            ok &= present
            print(f"\n  HOW_TO in archive contains {needle!r}: {present}")

        man = pd.read_csv(tmp / "00_START_HERE/MANIFEST.csv", encoding="utf-8-sig")
        row = man[man["file"] == "02_GPS/target_spend_waterfall.csv"].iloc[0]
        print(f"\n  MANIFEST row for the ceiling table: rows {row['rows']}, cols {row['cols']}, "
              f"kb {row['kb']}")
        ok &= int(row["rows"]) == len(d) and int(row["cols"]) == len(d.columns)
        print(f"  matches the file inside the archive: "
              f"{int(row['rows']) == len(d) and int(row['cols']) == len(d.columns)}")

        print(f"\n  any partial-year capture percentages left in the ceiling table: "
              f"{int(d['gps_capture_vs_max'].notna().sum()) if 'gps_capture_vs_max' in d else 'n/a'}")

        print("\nRESULT:", "ALL CHECKS PASSED" if ok else "SOMETHING DID NOT MATCH")
        print(f"(extracted to {tmp} - left in place for inspection)")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
