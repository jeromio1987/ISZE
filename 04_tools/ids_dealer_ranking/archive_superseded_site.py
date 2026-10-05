#!/usr/bin/env python3
"""Move superseded Isuzu / IDS dealer-comparison web files into one dated archive folder.

Jerome, 2026-09-24: "archive all other files of this type".

What counts as superseded (moved into `90_archive/IDS_dealer_web_superseded_2026-09-24/`):
  1. Backups of the dealer-compare files older than the current rebuild baseline
     (`*.bak_20260916`, `*.bak2_20260916`, `*.bak_inline_leaflet_*`, `*.bak_map_triple_*`,
     `*.bak_pre_inline_*`). The current baseline `*.bak_20260924_offline_map` is kept, because the
     bake script reads it to rebuild from a clean source - moving it would make the next rebuild
     stack patches on patches.
  2. The thin August `IDS_2026_dealer_compare.html` (about 1.2 MB, 17 September) that sits in the
     pipeline export and dashboard-report folders. It is not the master and nothing opens it.
  3. The same file inside the 19 August bundles folder, which is a superseded snapshot.

Deliberately NOT moved, because they are load-bearing:
  - `02_dashboards/ids/IDS_2026_dealer_compare.html` - the master.
  - `02_dashboards/ids/IDS_2026_dealer_compare_<Country>.html` - the live per-country files.
  - `02_dashboards/ids/_qa_map_triple/` - the QA fixture that proves the master paints alone.
  - `09_meetings/IDS_2026_Country_Packs_v1.5/` - a different pack family under its own version
    label; archiving or rebuilding it is Jerome's call, not a side effect.
  - `02_dashboards/Data/` - a deploy-compatibility tree some published HTML fetches from relatively.

Nothing is deleted. Every move is a `shutil.move` into the archive, and a manifest records the
original path so anything can be put back.

Usage:  python archive_superseded_site.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
ARCHIVE = ISZE / "90_archive" / "IDS_dealer_web_superseded_2026-09-24"
KEEP_BACKUP_TAGS = ("bak_20260924_offline_map",)

# Superseded backups: any of these tags means a snapshot taken before the 24 September rebuild.
OLD_BACKUP_TAGS = (
    ".bak_20260916",
    ".bak2_20260916",
    ".bak_inline_leaflet_20260916",
    ".bak_map_triple_20260916",
    ".bak_pre_inline_20260921",
    "SUPERSEDED",
)

SKIP_DIR_MARKERS = ("90_archive", "07_deploy", "node_modules", "worktrees", "\\bak")

# Stale copies of the thin August master. Keyed by path, with the reason recorded.
STALE_MASTER_COPIES = [
    ISZE / "01_data/08_Distributor/IDS_2026/_EXPORT/IDS_2026_dealer_compare.html",
    ISZE / "01_data/08_Distributor/IDS_2026/reports/dashboard/IDS_2026_dealer_compare.html",
    ISZE / "02_dashboards/ids/IDS_all_dashboards_2026-08-19/01_overview/IDS_2026_dealer_compare.html",
]


def inside_protected(path: Path) -> bool:
    """Paths that must never be moved.

    The live working files are protected by exact name, not by prefix: `IDS_2026_dealer_compare.html`
    and `IDS_2026_dealer_compare_<Country>.html`. Their *backups* are not protected - those are the
    superseded snapshots this script exists to archive.
    """
    parts = path.parts
    if "IDS_2026_Country_Packs_v1.5" in parts:
        return True
    if "_qa_map_triple" in parts:
        return True
    if path.parent.name == "ids":
        name = path.name
        if name == "IDS_2026_dealer_compare.html":
            return True
        if name.startswith("IDS_2026_dealer_compare_") and "." not in name[len("IDS_2026_dealer_compare_") :]:
            return True
        if name.endswith(".html") and name.startswith("IDS_2026_dealer_compare_") and ".html." not in name:
            return True
    return False


def collect_backups() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    for p in ISZE.rglob("IDS_2026_*"):
        if not p.is_file():
            continue
        if any(m in str(p) for m in SKIP_DIR_MARKERS):
            continue
        name = p.name
        if not any(tag in name for tag in OLD_BACKUP_TAGS):
            continue
        if any(keep in name for keep in KEEP_BACKUP_TAGS):
            continue
        if inside_protected(p):
            continue
        out.append((p, "superseded backup taken before the 24 September offline-map rebuild"))
    return out


def collect_stale_masters() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    for p in STALE_MASTER_COPIES:
        if p.exists() and p.is_file():
            out.append((p, "thin August master copy, superseded by 02_dashboards/ids/IDS_2026_dealer_compare.html"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    moves = collect_backups() + collect_stale_masters()
    moves.sort(key=lambda t: str(t[0]))

    if not moves:
        print("nothing to archive")
        return 0

    manifest: list[dict] = []
    for src, reason in moves:
        try:
            rel = src.relative_to(ISZE)
        except ValueError:
            print(f"  outside the workspace, skipped: {src}")
            continue
        dest = ARCHIVE / rel
        size = src.stat().st_size
        print(f"{'would move' if args.dry_run else 'moving':<11} {rel}")
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
        manifest.append(
            {
                "moved_from": str(src),
                "archive_path": str(dest),
                "relative_path": str(rel),
                "bytes": size,
                "reason": reason,
            }
        )

    if not args.dry_run:
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        readme = ARCHIVE / "README.md"
        readme.write_text(
            "# Superseded Isuzu / IDS dealer-comparison web files\n\n"
            "Archived 2026-09-24 on Jerome's instruction (\"archive all other files of this type\").\n\n"
            "Nothing here was deleted. Each file was moved from the path recorded in\n"
            "`MANIFEST.json`, keeping its folder structure, so any file can be moved back exactly\n"
            "where it came from.\n\n"
            "Two kinds of file are here:\n\n"
            "1. **Superseded backups** of the dealer-compare pages, taken before the offline-map\n"
            "   rebuild. The current rebuild baseline (`*.bak_20260924_offline_map`) was deliberately\n"
            "   left in place, because the build script reads it to rebuild from a clean source.\n"
            "2. **Thin August copies** of the network-wide page (about 1.2 MB), which predate the\n"
            "   embedded street map and are not the master.\n\n"
            "The live files are in `02_dashboards/ids/` and `09_meetings/IDS_2026_Country_Packs_v1.4/`.\n",
            encoding="utf-8",
        )
        (ARCHIVE / "MANIFEST.json").write_text(
            json.dumps(
                {
                    "archived_at": datetime.now().isoformat(timespec="seconds"),
                    "reason": "Jerome 2026-09-24: archive all other files of this type",
                    "file_count": len(manifest),
                    "files": manifest,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\narchived {len(manifest)} file(s) to {ARCHIVE}")
    else:
        print(f"\nwould archive {len(manifest)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
