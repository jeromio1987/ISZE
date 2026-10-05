"""Deliberately corrupt one real file so restore.ps1 can be proven, not assumed.

Round trip:  break -> restore -> compare sha256 -> re-break (leave the marker) .
The caller re-applies the real change afterwards, so this only ever runs where a
deliberate change is expected anyway.

Usage:
    python _test_restore_roundtrip.py probe   # append a marker, print the hash
    python _test_restore_roundtrip.py check   # compare against _before.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
TARGET = "01_data/00_derived/wallet_waterfall.csv"
MARKER = b"\n# restore.ps1 round-trip probe - this line must disappear after a restore\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    target = ROOT / TARGET
    recorded = next(
        f["sha256_before"]
        for f in json.loads((HERE / "_before.json").read_text(encoding="utf-8"))["files"]
        if f["rel"] == TARGET
    )
    if mode == "probe":
        # append, never truncate - truncating writes fail with OSError 22 on some files here
        with target.open("ab") as fh:
            fh.write(MARKER)
        print(f"probe appended. current sha256 = {sha256(target)}")
        print(f"recorded original     sha256 = {recorded}")
        print("now run:  restore.ps1 -File " + TARGET)
        return 0
    now = sha256(target)
    print(f"current  {now}")
    print(f"recorded {recorded}")
    print("MATCH" if now == recorded else "DIFFERENT")
    return 0 if now == recorded else 1


if __name__ == "__main__":
    raise SystemExit(main())
