#!/usr/bin/env python3
"""One place that says which parts file is current.

WHY THIS EXISTS
---------------
`aim_pn_classification_v2.csv` is read by 23 live scripts, each of which hardcodes the
filename. There is no shared definition anywhere in the workspace, which is why two
different things (the parts-tree file and the master) both carried a "v2" in the name and
nobody could tell which was a revision of what. A version number in a filename is a symptom
of not having this file.

WHAT THIS DOES
--------------
Names the current file ONCE. A reader asks for a role and gets a path:

    import sys; sys.path.insert(0, r"...\\04_tools\\_shared")
    from classification_paths import tree_file
    aim = pd.read_csv(tree_file(), dtype=str)

It resolves to the dated file (`aim_pn_classification_YYYYMMDD.csv`). It does NOT fall back
to a `_v2` name: the two older files are kept only so the not-yet-migrated scripts keep
working, and they are not what new work reads.

NON-DESTRUCTIVE. This module reads the folder and returns paths. It moves, renames and
deletes nothing, and never writes a data file.

Naming convention (2026-09-20)
------------------------------
Deliverable data files are named for WHAT they hold and WHEN they were made, not for a
version: `aim_pn_classification_20260920.csv`, not `..._v2.csv`. If a file needs a version
label to be understood, the label belongs in the sidecar meta, not the filename.
"""
from __future__ import annotations

import re
from pathlib import Path

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

# The released file: the one the safety gate and the taxonomies were signed off on.
RELEASED = DERIVED / "aim_pn_classification_20260920.csv"

# Kept on disk only so the not-yet-migrated scripts keep running. Never returned by
# tree_file(). These are the two files whose names carried a version suffix.
RETIRED = (
    DERIVED / "aim_pn_classification_v2.csv",
    DERIVED / "aim_pn_classification.csv",
)

# The master's name still carries the suffix too. Recorded here so there is one place that
# states it, rather than 38 scripts each spelling it out.
MASTER = DERIVED / "aim_master_v2.csv"

_DATE_RE = re.compile(r"^aim_pn_classification_(\d{8})\.csv$")


def available() -> list[Path]:
    """Every dated classification file on disk, oldest first."""
    out = []
    for p in DERIVED.glob("aim_pn_classification_*.csv"):
        if _DATE_RE.match(p.name):
            out.append(p)
    return sorted(out, key=lambda p: _DATE_RE.match(p.name).group(1))  # type: ignore[union-attr]


def tree_file() -> Path:
    """The current parts-tree file. This is what a reader should use."""
    if RELEASED.is_file():
        return RELEASED
    files = available()
    if not files:
        raise FileNotFoundError(
            f"no dated classification file in {DERIVED}. "
            "Build one with 01_data/91_build/build_aim_classification_20260920.py"
        )
    return files[-1]


def master_file() -> Path:
    """The AIM master. Still carries the suffix; see MASTER above."""
    return MASTER


def meta_file() -> Path:
    return tree_file().with_suffix(".meta.json")


def gate_file() -> Path:
    return tree_file().with_suffix(".gate.json")


RELEASES_DIR = DERIVED / "_releases"
FIGKEY_EXPORT_PREFIX = "AIM_Master_PN_Categories_Figkey_release_"


def _release_guard():
    """The workspace's release guard, loaded from its one home (never re-written here)."""
    import importlib.util

    path = RELEASES_DIR / "check_classification_release.py"
    if not path.is_file():
        raise FileNotFoundError(f"release guard missing: {path}")
    spec = importlib.util.spec_from_file_location("isze_classification_release", path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def approved_release() -> tuple[Path, dict]:
    """(path, register entry) of the release RELEASES.json marks APPROVED.

    Fail closed: raises if nothing is APPROVED, or if the file's sha256 no longer equals
    the register (assert_release). A NOT_RELEASED candidate is never returned.
    """
    guard = _release_guard()
    entry = guard.find_approved_release(guard.load_releases())
    if not entry:
        raise RuntimeError(f"no APPROVED release in {RELEASES_DIR / 'RELEASES.json'}")
    path = Path(guard.resolve_release_path(entry))
    guard.assert_release(str(path))
    return path, entry


def figkey_export_for_release() -> tuple[Path, dict]:
    """The AIM figure-key export built FROM the approved release, verified by its sidecar.

    Built by 01_data/91_build/export_aim_pn_categories_figkey_xlsx.py. The sidecar
    <csv>.release.json must name the same release id and sha256 the register approves;
    otherwise this raises, so a page can never be built from an export of another file.
    """
    import json

    _, entry = approved_release()
    csv = DERIVED / f"{FIGKEY_EXPORT_PREFIX}{entry['release_id']}.csv"
    side = csv.with_suffix(".release.json")
    if not csv.is_file() or not side.is_file():
        raise FileNotFoundError(
            f"{csv.name} (+ .release.json) missing: run "
            "01_data/91_build/export_aim_pn_categories_figkey_xlsx.py first")
    rec = json.loads(side.read_text(encoding="utf-8"))
    if (rec.get("release_id") != entry["release_id"]
            or str(rec.get("release_sha256", "")).lower() != entry["sha256"].lower()):
        raise RuntimeError(
            f"{side.name} records release {rec.get('release_id')} "
            f"{str(rec.get('release_sha256', ''))[:12]}, register approves "
            f"{entry['release_id']} {entry['sha256'][:12]}: rebuild the export")
    import hashlib

    h = hashlib.sha256()
    with csv.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() != str(rec.get("export_sha256", "")).lower():
        raise RuntimeError(f"{csv.name} bytes differ from its sidecar: rebuild the export")
    return csv, entry


def describe() -> str:
    """Plain-English line for a report or a console header."""
    return f"{tree_file().name} (parts tree) + {master_file().name} (master)"


if __name__ == "__main__":
    print("current tree file :", tree_file())
    print("master            :", master_file())
    print("meta              :", meta_file())
    print("gate              :", gate_file())
    print()
    print("dated files on disk:")
    for p in available():
        mark = "  <- current" if p == tree_file() else ""
        print(f"  {p.name}{mark}")
    print()
    print("retired (kept for un-migrated scripts, not used for new work):")
    for p in RETIRED:
        print(f"  {p.name}  [{'present' if p.is_file() else 'absent'}]")
