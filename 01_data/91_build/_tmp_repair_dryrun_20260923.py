"""Dry-run the edited builder into a temp directory and diff all four of its outputs.

Nothing under 01_data/00_derived is written. Used to confirm, before the real run:
  * the neutral table is untouched by this repair
  * the legacy file moves only the intended rows
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
    tmp = Path(tempfile.mkdtemp(prefix="bandapp_repair_"))
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
    if patched == text:
        print("FAIL: no output path replaced")
        return 2
    script = tmp / "run.py"
    script.write_text(patched, encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    print("exit", r.returncode)
    print(r.stdout[-1800:])
    if r.stderr.strip():
        print("STDERR:", r.stderr[-1200:])

    print()
    print("=" * 96)
    print("DIFF AGAINST THE FILES ON DISK")
    print("=" * 96)
    for made_name, live in (("vehicle_band_applicability.csv", DER / "vehicle_band_applicability.csv"),
                            ("vehicle_band_applicability.meta.json",
                             DER / "vehicle_band_applicability.meta.json"),
                            ("tonnage_capable_categories.csv",
                             DER / "tonnage_capable_categories.csv"),
                            ("tonnage_capable_part_numbers.csv",
                             DER / "tonnage_capable_part_numbers.csv")):
        made = tmp / made_name
        if not made.is_file():
            print(f"  {made_name:42s} NOT PRODUCED")
            continue
        same = made.read_bytes() == live.read_bytes()
        print(f"  {made_name:42s} {'IDENTICAL' if same else 'DIFFERS'}"
              f"   made {made.stat().st_size:,} B  live {live.stat().st_size:,} B")
        if not same:
            a = made.read_text(encoding="utf-8", errors="replace").splitlines()
            b = live.read_text(encoding="utf-8", errors="replace").splitlines()
            print(f"      lines made {len(a):,}  live {len(b):,}")
            shown = 0
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print(f"      line {i + 1}:")
                    print(f"        made: {x[:150]}")
                    print(f"        live: {y[:150]}")
                    shown += 1
                    if shown >= 20:
                        break
    print()
    print(f"temp dir {tmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
