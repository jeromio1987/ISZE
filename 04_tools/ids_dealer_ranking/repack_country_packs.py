#!/usr/bin/env python3
"""Repack the IDS country packs so they carry the map-carrying HTML.

Background
----------
The country compare files now have their street map built in, but the hand-off zips still held the
15 August versions, which needed an internet connection for the map. Three things are refreshed:

  1. `IDS_2026_<Country>_v1.4.zip` - the per-country pack: HTML + README + launcher
  2. `IDS_2026_country_dashboards_DB_level.zip` - every country HTML, flat
  3. `IDS_2026_Country_Packs_v1.4_ALL.zip` - the master bundle of the country zips

Method: read each zip's existing entry list and write the current file from disk for every entry
that has one on disk, carrying the old bytes forward where it does not. The layout is unchanged, so
nothing is added or dropped except the launcher, which the ship gate requires beside an HTML.

Text that said the map needs internet is corrected, since the pack now contradicts it.

Usage:  python repack_country_packs.py [--dry-run] [--skip-all]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
V14 = ISZE / "09_meetings" / "IDS_2026_Country_Packs_v1.4"
IDS_DIR = ISZE / "02_dashboards" / "ids"
STAMP = "20260924_offline_map"

# Country folder name -> the file stem inside it. Israel differs: the folder is `Israel`
# but the file is `Israel_LCV`.
FOLDER_TO_FILE_STEM = {"Israel": "Israel_LCV"}

# Corrections applied to README / manifest / INDEX text inside the packs.
TEXT_EDITS = [
    (
        "Open the HTML with an internet connection so map tiles can load.",
        "The HTML carries its own street map, so it opens with no internet connection.",
    ),
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


def fix_text(raw: bytes) -> tuple[bytes, list[str]]:
    """Apply the wording corrections to a text file, leaving everything else byte-identical."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw, []
    applied = []
    for old, new in TEXT_EDITS:
        if old in text:
            text = text.replace(old, new)
            applied.append(old[:52])
    return text.encode("utf-8"), applied


def launcher_bytes(html_name: str) -> bytes:
    return f'@echo off\r\nstart "" "%~dp0{html_name}"\r\n'.encode("ascii")


def repack(zip_path: Path, root: Path, dry: bool, extras: dict[str, Path] | None = None) -> dict:
    backup = zip_path.with_suffix(zip_path.suffix + f".bak_{STAMP}")
    src = backup if backup.exists() else zip_path
    if not src.exists():
        return {"zip": str(zip_path), "skipped": "missing"}

    old = zipfile.ZipFile(src)
    entries = list(old.namelist())
    live_extras = {k: v for k, v in (extras or {}).items() if v.exists()}
    for name in live_extras:
        if name not in entries:
            entries.append(name)

    tmp = zip_path.with_suffix(".zip.tmp")
    replaced: list[str] = []
    carried: list[str] = []
    edits: list[str] = []

    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in entries:
            if name.endswith("/"):
                z.writestr(zipfile.ZipInfo(name), b"")
                continue

            target = root / name.replace("\\", "/")
            if not target.exists() and extras:
                target = extras.get(name, target)

            if not target.exists():
                z.writestr(name, old.read(name))
                carried.append(name)
                continue

            data = target.read_bytes()
            if target.suffix.lower() in (".md", ".json"):
                data, applied = fix_text(data)
                edits.extend(applied)
            z.writestr(name, data)
            replaced.append(name)

    old.close()
    if dry:
        tmp.unlink(missing_ok=True)
    else:
        if not backup.exists():
            shutil.copy2(zip_path, backup)
        tmp.replace(zip_path)

    return {
        "zip": str(zip_path),
        "bytes": 0 if dry else zip_path.stat().st_size,
        "replaced": replaced,
        "carried": carried,
        "edits": sorted(set(edits)),
        "dry_run": dry,
    }


def rebuild_all_bundle(dry: bool) -> dict:
    """The master bundle holds the per-country zips by reference to the folder, so it is rebuilt
    last, after the country zips are current."""
    path = V14 / "IDS_2026_Country_Packs_v1.4_ALL.zip"
    backup = path.with_suffix(path.suffix + f".bak_{STAMP}")
    src = backup if backup.exists() else path
    if not src.exists():
        return {"zip": str(path), "skipped": "missing"}

    old = zipfile.ZipFile(src)
    entries = list(old.namelist())
    tmp = path.with_suffix(".zip.tmp")
    replaced, carried, edits = [], [], []

    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in entries:
            target = V14 / name.replace("\\", "/")
            if not target.exists():
                z.writestr(name, old.read(name))
                carried.append(name)
                continue
            data = target.read_bytes()
            if target.suffix.lower() in (".md", ".json"):
                data, applied = fix_text(data)
                edits.extend(applied)
            z.writestr(name, data)
            replaced.append(name)
    old.close()

    if dry:
        tmp.unlink(missing_ok=True)
        size = 0
    else:
        if not backup.exists():
            shutil.copy2(path, backup)
        tmp.replace(path)
        size = path.stat().st_size

    return {
        "zip": str(path),
        "bytes": size,
        "replaced": replaced,
        "carried": carried,
        "edits": sorted(set(edits)),
        "dry_run": dry,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-all", action="store_true", help="do not rebuild the master bundle")
    args = ap.parse_args()

    report: list[dict] = []

    # 1. per-country zips
    for folder in sorted(p for p in V14.iterdir() if p.is_dir()):
        stem = FOLDER_TO_FILE_STEM.get(folder.name, folder.name)
        html = folder / f"IDS_2026_dealer_compare_{stem}.html"
        if not html.exists():
            print(f"  {folder.name}: no compare HTML - skipped")
            continue
        cmd_name = "OPEN_IDS_2026_Portugal.cmd" if folder.name == "Portugal" else "OPEN_IDS_2026_dealer_compare.cmd"
        cmd = folder / cmd_name
        if not cmd.exists() and not args.dry_run:
            cmd.write_bytes(launcher_bytes(html.name))
        zip_path = V14 / f"IDS_2026_{folder.name}_v1.4.zip"
        info = repack(zip_path, folder, args.dry_run, extras={cmd_name: cmd})
        info["country"] = folder.name
        report.append(info)
        print(
            f"  {folder.name:<13} replaced {len(info.get('replaced', [])):>2}  "
            f"carried {len(info.get('carried', [])):>2}  {info.get('bytes', 0)/1e6:.2f} MB  "
            f"edits={len(info.get('edits', []))}"
        )

    # 2. the flat DB-level zip: every country HTML, no README
    db_zip = V14 / "IDS_2026_country_dashboards_DB_level.zip"
    db_extras = {
        p.name: p for p in IDS_DIR.glob("IDS_2026_dealer_compare_*.html") if ".bak" not in p.name
    }
    info = repack(db_zip, IDS_DIR, args.dry_run, extras=db_extras)
    print(
        f"  {'DB_level':<13} replaced {len(info.get('replaced', [])):>2}  "
        f"{info.get('bytes', 0)/1e6:.2f} MB"
    )
    report.append(info)

    # 3. the master bundle, last, so it carries the refreshed country zips
    if not args.skip_all:
        info = rebuild_all_bundle(args.dry_run)
        print(
            f"  {'ALL bundle':<13} replaced {len(info.get('replaced', [])):>2}  "
            f"{info.get('bytes', 0)/1e6:.2f} MB"
        )
        report.append(info)

    if not args.dry_run:
        out = V14 / f"REPACK_REPORT_{STAMP}.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("report", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
