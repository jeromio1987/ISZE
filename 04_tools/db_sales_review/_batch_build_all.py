"""Batch-build all enabled DB sales-review packs (skip PORTUGAL/UTI/ITUK)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable

# Order: core first, then nordics, then rest
ORDER = [
    "IUK", "ISD", "IBX", "PETROS", "IRELAND", "UMI",
    "NORWAY", "SWEDEN", "HUNGARY", "FINLAND", "DENMARK", "ICELAND",
    "ROMANIA", "CYPRUS", "MALTA",
]


def run(cmd: list[str]) -> int:
    print("\n>>>", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(HERE))


def main():
    results = []
    for db in ORDER:
        print("\n" + "#" * 72 + f"\n# {db}\n" + "#" * 72, flush=True)
        rc_pf = run([PY, "preflight.py", "--db", db])
        rc_pa = run([PY, "build_parts_analysis.py", "--db", db])
        if rc_pa != 0:
            results.append((db, "FAIL parts", rc_pa))
            continue
        rc_dk = run([PY, "build_deck.py", "--db", db])
        if rc_dk != 0:
            results.append((db, "FAIL deck", rc_dk))
            continue
        pptx = HERE.parent.parent / "09_meetings" / f"{db}_Sales_Review_2026" / f"ISZE_{db}_Sales_Review_FY2027.pptx"
        if not pptx.exists():
            # also check Downloads legacy
            alt = Path.home() / "Downloads" / f"ISZE_{db}_Sales_Review_FY2027.pptx"
            pptx = alt if alt.exists() else pptx
        rc_qa = run([PY, "qa_contact_sheet.py", "--pptx", str(pptx)])
        status = "OK" if rc_pf == 0 and rc_qa == 0 else ("BUILT_WARN" if rc_dk == 0 else "FAIL")
        if rc_pf != 0:
            status = "BUILT_PF_WARN" if rc_dk == 0 else status
        if rc_qa != 0:
            status = "BUILT_QA_FAIL"
        results.append((db, status, pptx if pptx.exists() else None))

    print("\n" + "=" * 72)
    print("BATCH SUMMARY")
    for db, status, path in results:
        print(f"  {db:10} {status:16} {path or ''}")
    fails = [r for r in results if "FAIL" in r[1]]
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
