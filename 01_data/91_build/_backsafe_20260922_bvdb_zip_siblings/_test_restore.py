#!/usr/bin/env python3
"""Test the restore for real, as the previous pass did.

Round-trip: copy a file aside, restore it from the backup, confirm the hash matches
the recorded original, then put my corrected version back. Finally -Verify the whole
set and report changed vs matching, so the tool's own semantics are shown working.

Usage: python _test_restore.py [--files-only]
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
ORIG = HERE / "original"
RESTORE = HERE / "restore.ps1"
PS = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RESTORE)]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    before = json.loads((HERE / "_before.json").read_text(encoding="utf-8"))

    print("=" * 100)
    print("A. -Verify (no writes): which files differ from their recorded original?")
    print("=" * 100)
    r = subprocess.run(PS + ["-Verify"], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout)
    if r.stderr.strip():
        print("stderr:", r.stderr)
    print("exit code:", r.returncode)

    print("=" * 100)
    print("B. Real round-trip on one file: corrupt it, restore it, prove the hash")
    print("=" * 100)
    rel = "01_data/00_derived/gps_spu_by_family.csv"
    target = ROOT / rel
    clean = target.read_bytes()
    expected = before[rel]["sha256_before"]

    with target.open("wb") as fh:
        fh.write(b"# deliberately corrupted by _test_restore.py\n")
    print(f"   corrupted  {rel}  hash now {sha256(target)[:16]}")

    r = subprocess.run(PS + ["-File", rel.replace("\\", "/")],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout)
    if r.stderr.strip():
        print("stderr:", r.stderr)
    print("   restore exit code:", r.returncode)
    got = sha256(target)
    print(f"   after restore  hash {got[:16]}  matches original: {got == expected}")
    if got != expected:
        print("   RESTORE FAILED - putting my corrected copy back and stopping")
        with target.open("wb") as fh:
            fh.write(clean)
        return 1

    print(f"   (the restored file is the pre-change original; re-applying my fix)")
    with target.open("wb") as fh:
        fh.write(clean)
    print(f"   corrected version back: hash {sha256(target)[:16]}")

    print()
    print("=" * 100)
    print("C. -WhatIf: what would a full restore do, without writing?")
    print("=" * 100)
    r = subprocess.run(PS + ["-WhatIf"], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout)
    if r.stderr.strip():
        print("stderr:", r.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
