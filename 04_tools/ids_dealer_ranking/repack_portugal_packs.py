#!/usr/bin/env python3
"""Repack the Portugal hand-off zips so they carry the map-carrying HTML.

Two zips are refreshed, content-for-content:
  1. 09_meetings/IDS_2026_Country_Packs_v1.4/IDS_2026_Portugal_v1.4.zip   (HTML + README)
  2. 09_meetings/Imotors_Portugal_IDS_2026/Imotors_Portugal_IDS_2026_pack.zip
     (HTML + dealer map page/xlsx + README + dealer_fiches tree + fiches zip)

Method: read the existing entry list, and for every entry write the current file from disk where
one exists, otherwise carry the old bytes forward. That keeps the zip layout byte-for-byte in
shape while swapping the HTML inside. Nothing is added or removed.

README lines that said the map needs internet are corrected, and the banned "Mode A" phrasing in
the v1.4 README (still present in the zip, already fixed on disk) is replaced with "shared".

Usage:  python repack_portugal_packs.py [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
V14 = ISZE / "09_meetings" / "IDS_2026_Country_Packs_v1.4"
IMOTORS = ISZE / "09_meetings" / "Imotors_Portugal_IDS_2026"
STAMP = "20260924_offline_map"

# README corrections: (old, new). Plain-ASCII anchors, so encoding elsewhere is untouched.
README_EDITS = [
    (
        "- Map: Leaflet + OpenStreetMap / CARTO (needs internet when opening HTML)",
        "- Map: **the street map is stored inside the HTML**, so it works with no internet. "
        "Live street tiles are used when the network allows them.",
    ),
    (
        "- Map base layer: Leaflet CDN + OpenStreetMap/CARTO tiles (needs internet when opening the HTML).",
        "- Map base layer: **the street map is stored inside the HTML**, so it opens with no internet. "
        "Live street tiles are used when the network allows them.",
    ),
    ("**Mode A colleague pack**", "**shared colleague pack**"),
    ("Mode A colleague pack", "shared colleague pack"),
]


def fix_readme(text: str) -> tuple[str, list[str]]:
    applied = []
    for old, new in README_EDITS:
        if old in text:
            text = text.replace(old, new)
            applied.append(old[:48])
    return text, applied


def disk_for(entry: str, root: Path) -> Path | None:
    """Map a zip entry name to the current file on disk."""
    clean = entry.replace("\\", "/")
    if clean.endswith("/"):
        return None
    cand = root / clean
    if cand.exists():
        return cand
    # zips written on Windows may use backslashes
    cand = root / Path(clean)
    return cand if cand.exists() else None


def launcher_text(html_name: str) -> str:
    return f'@echo off\r\nstart "" "%~dp0{html_name}"\r\n'


def ensure_launcher(root: Path, html_name: str, cmd_name: str) -> Path:
    path = root / cmd_name
    data = launcher_text(html_name)
    if not path.exists() or path.read_bytes() != data.encode("ascii"):
        path.write_bytes(data.encode("ascii"))
        print(f"    wrote {cmd_name}")
    return path


def repack(zip_path: Path, root: Path, dry: bool, extras: list[tuple[str, Path]] | None = None) -> dict:
    backup = zip_path.with_suffix(zip_path.suffix + f".bak_{STAMP}")
    src = backup if backup.exists() else zip_path
    if not src.exists():
        raise SystemExit(f"missing {src}")

    old = zipfile.ZipFile(src)
    entries = old.namelist()
    for name, path in extras or []:
        if name not in entries and path.exists():
            entries.append(name)
    out_path = zip_path
    tmp = zip_path.with_suffix(".zip.tmp")

    replaced, carried, edits = [], [], []
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in entries:
            if name.endswith("/"):
                z.writestr(zipfile.ZipInfo(name), b"")
                continue
            target = disk_for(name, root)
            if target is None and extras:
                for ename, epath in extras:
                    if ename == name:
                        target = epath
                        break
            if target is None:
                z.writestr(name, old.read(name))
                carried.append(name)
                continue
            data = target.read_bytes()
            if target.suffix.lower() == ".md":
                text, applied = fix_readme(data.decode("utf-8"))
                if applied:
                    edits.extend(applied)
                    data = text.encode("utf-8")
            z.writestr(name, data)
            replaced.append(name)
            try:
                before_n = len(old.read(name))
                print(f"    {name}: {before_n:,} -> {len(data):,} bytes")
            except KeyError:
                print(f"    {name}: added, {len(data):,} bytes")
    old.close()

    if dry:
        tmp.unlink(missing_ok=True)
    else:
        if not backup.exists():
            shutil.copy2(zip_path, backup)
        tmp.replace(out_path)

    return {
        "zip": str(out_path),
        "backup": str(backup),
        "replaced": replaced,
        "carried": carried,
        "readme_edits": sorted(set(edits)),
        "dry_run": dry,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # keep the Imotors README on disk in step with the zip
    readme = IMOTORS / "README.md"
    text, applied = fix_readme(readme.read_text(encoding="utf-8"))
    if applied:
        if not args.dry_run:
            readme.write_text(text, encoding="utf-8")
        print(f"  README {'updated' if not args.dry_run else 'would be updated'}: {applied}")

    jobs = [
        (V14 / "IDS_2026_Portugal_v1.4.zip", V14 / "Portugal", "IDS_2026_dealer_compare_Portugal.html"),
        (IMOTORS / "Imotors_Portugal_IDS_2026_pack.zip", IMOTORS, "IDS_2026_dealer_compare_Portugal.html"),
    ]
    for zip_path, root, html_name in jobs:
        cmd_name = "OPEN_IDS_2026_Portugal.cmd"
        ensure_launcher(root, html_name, cmd_name)
        print(f"  repacking {zip_path.name} from {root}")
        info = repack(zip_path, root, args.dry_run, extras=[(cmd_name, root / cmd_name)])
        print(f"    replaced {len(info['replaced'])}, carried {len(info['carried'])}, edits {info['readme_edits']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
