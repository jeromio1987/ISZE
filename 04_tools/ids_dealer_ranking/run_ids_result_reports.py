#!/usr/bin/env python3
"""Build IDS Evaluation Result Reports for all countries with dealer data."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ids_paths import DATA_ROOT, discover_country_folders

COUNTRIES = (
    "BE",
    "NL",
    "Poland",
    "Petros",
    "RSA",
    "IUK",
    "ITUK",
    "Israel",
    "Malta",
    "Cyprus",
    "Romania",
    "Portugal",
    "Hungary",
)

# No per-dealer evaluation workbooks in inbox (ranking-only export)
SKIP = {"Denmark", "MIDI"}

# MIDI CodDivs get dedicated result reports via --midi
MIDI_CODS = ("FR", "IT", "ES", "CH")


def main() -> int:
    root = Path(__file__).resolve().parent
    available = set(discover_country_folders(DATA_ROOT))
    todo = [c for c in COUNTRIES if c in available]
    for c in sorted(available):
        if c not in todo and c not in SKIP:
            todo.append(c)

    rc = 0
    for country in todo:
        if country in SKIP:
            print(f"\n=== {country} === SKIP (no per-dealer eval files)")
            continue
        print(f"\n=== {country} ===")
        cmd = [
            sys.executable,
            str(root / "build_ids_result_report.py"),
            "--country",
            country,
            "--qa",
        ]
        r = subprocess.run(cmd, cwd=root)
        if r.returncode != 0:
            rc = r.returncode

    # IBX Benelux = BE + NL (+ LX when available)
    print("\n=== Benelux (IBX: BE+NL) ===")
    be_dir = DATA_ROOT / "BE"
    nl_dir = DATA_ROOT / "NL"
    cmd = [
        sys.executable,
        str(root / "build_ids_result_report.py"),
        "--country",
        "Benelux",
        "--input-dir",
        str(be_dir),
        "--extra-input-dir",
        str(nl_dir),
        "--qa",
    ]
    r = subprocess.run(cmd, cwd=root)
    if r.returncode != 0:
        rc = r.returncode

    # MIDI country summaries
    for cod in MIDI_CODS:
        label = f"MIDI_{cod}"
        print(f"\n=== {label} ===")
        cmd = [
            sys.executable,
            str(root / "build_ids_result_report.py"),
            "--country",
            label,
            "--midi",
            cod,
            "--qa",
        ]
        r = subprocess.run(cmd, cwd=root)
        if r.returncode != 0:
            rc = r.returncode

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
