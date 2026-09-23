"""Take the backup for the partial-year correction. Copies every file byte-for-byte
into original/ and records its sha256 before the change.

Run once, before any edit. Safe to re-run: it refuses to overwrite an existing backup
unless --force is given.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
ORIG = HERE / "original"
SCOPE = json.loads((HERE / "scope.json").read_text(encoding="utf-8"))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


force = "--force" in sys.argv
rows = []
for item in SCOPE["files"]:
    rel = item["rel"]
    src = ROOT / rel
    dst = ORIG / rel
    if not src.exists():
        print(f"MISSING, cannot back up: {rel}")
        raise SystemExit(2)
    if dst.exists() and not force:
        print(f"backup already present, left as is: {rel}")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"backed up {rel}")
    rows.append({"rel": rel, "sha256_before": sha256(src), "bytes_before": src.stat().st_size})

(HERE / "_before.json").write_text(
    json.dumps({"files": rows}, indent=2), encoding="utf-8"
)
print(f"\nrecorded sha256 before -> {HERE / '_before.json'}")
for r in rows:
    print(f"  {r['sha256_before'][:16]}  {r['bytes_before']:>8}  {r['rel']}")
