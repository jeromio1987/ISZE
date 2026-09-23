#!/usr/bin/env python3
"""Member-by-member diff of two zips: what changed, added or removed.

Usage: python _zip_diff.py <old.zip> <new.zip>
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ARCHIVE_ROOT = "BVDB_PBI_Data_Upload_2026-09-23"


def members(zp: Path) -> dict[str, tuple[int, int]]:
    with zipfile.ZipFile(zp) as zf:
        return {i.filename: (i.file_size, i.CRC) for i in zf.infolist()}


def main() -> int:
    old, new = Path(sys.argv[1]), Path(sys.argv[2])
    a, b = members(old), members(new)
    print("old member examples:", list(a)[:3])
    print("new member examples:", list(b)[:3])

    # strip the archive-root prefix from EITHER side, when present, so that a
    # difference in wrapper folder does not masquerade as a content difference.
    def base(k: str) -> str:
        return k.split("/", 1)[1] if k.split("/")[0] == ARCHIVE_ROOT else k

    a2 = {base(k): v for k, v in a.items()}
    b2 = {base(k): v for k, v in b.items()}
    print(f"old {old.name}: {len(a)} members")
    print(f"new {new.name}: {len(b)} members")
    print("\nCHANGED (same path, different bytes):")
    for k in sorted(set(a2) & set(b2)):
        if a2[k] != b2[k]:
            print(f"  {k}   {a2[k][0]} -> {b2[k][0]} bytes   crc {a2[k][1]:08x} -> {b2[k][1]:08x}")
    print("\nADDED:")
    for k in sorted(set(b2) - set(a2)):
        print(f"  {k}  {b2[k][0]} bytes")
    print("\nREMOVED:")
    for k in sorted(set(a2) - set(b2)):
        print(f"  {k}  {a2[k][0]} bytes")
    print("\nIDENTICAL (same path, same CRC): ", end="")
    same = [k for k in sorted(set(a2) & set(b2)) if a2[k] == b2[k]]
    print(len(same))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
