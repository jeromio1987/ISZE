#!/usr/bin/env python3
"""Migrate away from version-suffixed data-file names. DRY-RUN BY DEFAULT.

Why
---
Two different files carried "v2" and nobody could tell which was a revision of what:

    aim_master_v2.csv            (28 MB, read by 38 scripts)
    aim_pn_classification_v2.csv (24 MB, read by 23 scripts)

plus their predecessors `aim_master_v1.csv` and `aim_pn_classification.csv`. Jerome,
2026-09-20: "you can't have 2 references so do it everywhere."

Naming convention adopted
-------------------------
Deliverable data files are named for WHAT they hold and WHEN they were made:

    aim_master.csv                  current master
    aim_master_20260917.csv         the prior master (was aim_master_v1.csv)
    aim_pn_classification_20260918.csv   (was aim_pn_classification.csv)
    aim_pn_classification_20260920.csv   current (already dated)

Usage
-----
    python migrate_off_versioned_names.py            # dry run, changes nothing
    python migrate_off_versioned_names.py --apply    # performs the rename + edits

Safety
------
  - Refuses to run if a destination already exists.
  - COPIES the file, then MOVES the original to 01_data/92_archive/versioned_names_20260920/,
    so nothing is destroyed.
  - Edits only files in CODE_ROOTS, and only on lines that reference the old name.
  - Leaves .SHIP_RECEIPT.json untouched: a receipt is a historical record of what was
    verified on a date, and rewriting it would be falsifying that record. Those are
    reported instead, as carrying a stale path.
  - Prints every change it would make, and a manifest of every edit.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import sys
from datetime import datetime, timezone

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
ARCHIVE = os.path.join(ISZE, "01_data", "92_archive", "versioned_names_20260920")

# old filename -> new filename
RENAMES = {
    "aim_master_v2.csv": "aim_master.csv",
    "aim_master_v1.csv": "aim_master_20260917.csv",
    "aim_pn_classification_v2.csv": "aim_pn_classification_20260918_v2sep.csv",
    "aim_pn_classification.csv": "aim_pn_classification_20260918.csv",
}
# sidecars that travel with each file
SIDECARS = {
    "aim_master_v2.meta.json": "aim_master.meta.json",
    "aim_master_v1.meta.json": "aim_master_20260917.meta.json",
    "aim_pn_classification_v2.meta.json": "aim_pn_classification_20260918_v2sep.meta.json",
}

CODE_ROOTS = ["02_dashboards", "03_analytics", "04_tools", "01_data\\91_build", "00_docs"]
CODE_EXT = {".py", ".mjs", ".js", ".ps1", ".yaml"}
JSON_EXT = {".json"}
SKIP_DIR_PARTS = ("worktrees", "__pycache__", "07_deploy", "92_archive")
# build artifacts that legitimately embed a source path: update them
JSON_UPDATE_OK = {"DELEGATOR_STATE.json", "OVERNIGHT_LOCKED_BASELINE.json",
                  "payload.json", "_figkey_panel.json"}
# a receipt is a record of what was verified on a date: never rewritten
def is_receipt(name: str) -> bool:
    return name.endswith(".SHIP_RECEIPT.json")


def walk():
    for root in CODE_ROOTS:
        base = os.path.join(ISZE, root)
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in SKIP_DIR_PARTS]
            if any(s in dp for s in SKIP_DIR_PARTS):
                continue
            for f in fn:
                yield os.path.join(dp, f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually do it")
    args = ap.parse_args()
    mode = "APPLY" if args.apply else "DRY RUN (nothing will change)"
    print("=" * 78)
    print(f"AIM file-name migration - {mode}")
    print("=" * 78)

    # ---------------------------------------------------------------- preflight
    print("\n1. preflight")
    blockers = []
    for old, new in list(RENAMES.items()) + list(SIDECARS.items()):
        src = os.path.join(DERIVED, old)
        dst = os.path.join(DERIVED, new)
        if not os.path.isfile(src):
            print(f"   [skip]  {old}  (not on disk)")
            continue
        if os.path.exists(dst):
            blockers.append(f"destination exists: {new}")
            print(f"   [BLOCK] {old} -> {new}  DESTINATION ALREADY EXISTS")
        else:
            print(f"   [ok]    {old} -> {new}")
    if blockers:
        print("\n   refusing to run:")
        for b in blockers:
            print("     - %s" % b)
        return 2

    # ---------------------------------------------------------------- file edits
    print("\n2. references to update")
    edits = []
    receipts = []
    name_re = re.compile("|".join(re.escape(k) for k in list(RENAMES) + list(SIDECARS)))
    for path in walk():
        ext = os.path.splitext(path)[1].lower()
        if ext not in CODE_EXT | JSON_EXT:
            continue
        base = os.path.basename(path)
        try:
            txt = io.open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if not name_re.search(txt):
            continue
        rel = os.path.relpath(path, ISZE)
        hits = [i for i, l in enumerate(txt.splitlines(), 1) if name_re.search(l)]
        if ext in JSON_EXT:
            if is_receipt(base):
                receipts.append((rel, len(hits)))
                continue
            if base not in JSON_UPDATE_OK:
                receipts.append((rel, len(hits)))
                continue
        edits.append((rel, hits, path))

    print("   %d file(s) to edit, %d reference line(s)" % (
        len(edits), sum(len(h) for _, h, _ in edits)))
    for rel, hits, _ in sorted(edits):
        print("     %-74s %d line(s)" % (rel[:74], len(hits)))
    if receipts:
        print("\n   NOT rewritten (%d file(s)) - historical records or data artifacts:" % len(receipts))
        for rel, n in sorted(receipts):
            print("     %-74s %d line(s)" % (rel[:74], n))
        print("     -> these keep the old path and will read as stale; that is deliberate.")

    # ---------------------------------------------------------------- apply
    if not args.apply:
        print("\n" + "=" * 78)
        print("DRY RUN. Re-run with --apply to perform it.")
        print("=" * 78)
        return 0

    os.makedirs(ARCHIVE, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = []

    print("\n3. renaming (copy new, archive original)")
    for old, new in list(RENAMES.items()) + list(SIDECARS.items()):
        src = os.path.join(DERIVED, old)
        if not os.path.isfile(src):
            continue
        shutil.copy2(src, os.path.join(DERIVED, new))
        shutil.move(src, os.path.join(ARCHIVE, old))
        manifest.append(f"{old} -> {new}")
        print(f"   {old} -> {new}   (original archived)")

    print("\n4. editing references")
    for rel, hits, path in edits:
        txt = io.open(path, encoding="utf-8", errors="replace").read()
        for old, new in list(RENAMES.items()) + list(SIDECARS.items()):
            txt = txt.replace(old, new)
        io.open(path, "w", encoding="utf-8").write(txt)
        manifest.append(f"edited {rel} ({len(hits)} lines)")
        print(f"   {rel}  ({len(hits)} lines)")

    mpath = os.path.join(ARCHIVE, f"_MIGRATION_MANIFEST_{stamp}.txt")
    io.open(mpath, "w", encoding="utf-8").write("\n".join(manifest) + "\n")
    print(f"\n   manifest: {mpath}")
    print("\nDONE. Now re-run: python 01_data/91_build/verify_aim_classification.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
