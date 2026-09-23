"""Rebuild the band-applicability builder to a temporary path and diff against the file on disk.

The builder writes four files with hard-coded paths. This makes a patched copy of the SCRIPT (the
original is never opened for writing) whose four output paths point into a temp directory, runs it,
and compares the two files the neutrality question rests on. Nothing in 01_data/00_derived is
touched by this.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SRC = ROOT / "01_data" / "91_build" / "pn_ammo_probe_20260918" / "_vehicle_band_applicability.py"
DER = ROOT / "01_data" / "00_derived"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="bandapp_rebuild_"))
    print(f"temp dir: {tmp}")
    text = SRC.read_text(encoding="utf-8")
    patched = (text
               .replace('OUT_APPLICABILITY = DER / "vehicle_band_applicability.csv"',
                        f'OUT_APPLICABILITY = Path(r"{tmp}") / "vehicle_band_applicability.csv"')
               .replace('OUT_LEGACY = DER / "tonnage_capable_part_numbers.csv"',
                        f'OUT_LEGACY = Path(r"{tmp}") / "tonnage_capable_part_numbers.csv"')
               .replace('OUT_CATS = DER / "tonnage_capable_categories.csv"',
                        f'OUT_CATS = Path(r"{tmp}") / "tonnage_capable_categories.csv"')
               .replace('OUT_META = DER / "vehicle_band_applicability.meta.json"',
                        f'OUT_META = Path(r"{tmp}") / "vehicle_band_applicability.meta.json"'))
    assert patched != text, "no output path was replaced"
    script = tmp / "run_applicability.py"
    script.write_text(patched, encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    print("exit", r.returncode)
    print(r.stdout[-2500:])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-1500:])

    print()
    print("=" * 96)
    print("DIFF AGAINST THE FILES ON DISK")
    print("=" * 96)
    pairs = [
        (tmp / "vehicle_band_applicability.csv", DER / "vehicle_band_applicability.csv"),
        (tmp / "tonnage_capable_part_numbers.csv", DER / "tonnage_capable_part_numbers.csv"),
        (tmp / "tonnage_capable_categories.csv", DER / "tonnage_capable_categories.csv"),
        (tmp / "vehicle_band_applicability.meta.json", DER / "vehicle_band_applicability.meta.json"),
    ]
    same_all = True
    for made, live in pairs:
        if not made.is_file():
            print(f"  {live.name:42s} NOT PRODUCED")
            same_all = False
            continue
        a, b = made.read_bytes(), live.read_bytes()
        same = a == b
        same_all &= same
        print(f"  {live.name:42s} {'IDENTICAL' if same else 'DIFFERENT'}"
              f"   made {len(a):,} B  live {len(b):,} B")
        if not same:
            ta = made.read_text(encoding="utf-8", errors="replace").splitlines()
            tb = live.read_text(encoding="utf-8", errors="replace").splitlines()
            print(f"      lines made {len(ta):,}  live {len(tb):,}")
            shown = 0
            for i, (x, y) in enumerate(zip(ta, tb)):
                if x != y:
                    print(f"      line {i+1}:")
                    print(f"        made: {x[:170]}")
                    print(f"        live: {y[:170]}")
                    shown += 1
                    if shown >= 8:
                        break
    print()
    print(f"ALL FOUR IDENTICAL: {same_all}")
    print(f"live applicability sha256 {sha(DER / 'vehicle_band_applicability.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
