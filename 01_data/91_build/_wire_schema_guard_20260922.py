"""Apply the two remaining edits via temp-file + os.replace.

Both target files refuse a truncating open on this machine (OSError [Errno 22] Invalid argument),
so every rewrite goes through a temp file in the same directory and os.replace().
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

FX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\verification_fixtures.yaml")
VER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\scripts\verify_derived_pipeline.py")


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp_schema_guard")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, path)


def main() -> int:
    # 1. fixtures: drop the stray optional key I left in the appended block.
    fx = FX.read_text(encoding="utf-8")
    if "required_columns_optional" in fx:
        fx = fx.replace("      required_columns_optional: []\n", "")
        atomic_write(FX, fx)
        print("fixtures: removed required_columns_optional")
    else:
        print("fixtures: nothing to remove")

    # 2. verifier: call the schema guard next to the freshness check.
    ver = VER.read_text(encoding="utf-8")
    if "schema_guard" in ver:
        print("verifier: schema_guard already wired")
        return 0

    anchor = """    from modules.freshness import check as check_freshness  # noqa: PLC0415

    check_freshness(report, fx, DERIVED_DIR, _chk)
"""
    if anchor not in ver:
        print("verifier: ANCHOR NOT FOUND - aborting, no change")
        return 1

    replacement = """    from modules.freshness import check as check_freshness  # noqa: PLC0415

    check_freshness(report, fx, DERIVED_DIR, _chk)
    # Schema guard next to freshness: freshness asks whether a file is current, the guard asks
    # whether it still carries the columns it is supposed to. A column that has disappeared is a
    # fail, not a warn - it is never deliberate.
    from modules.schema_guard import check as check_schema  # noqa: PLC0415

    check_schema(report, fx, DERIVED_DIR, _chk)
"""
    ver = ver.replace(anchor, replacement, 1)
    atomic_write(VER, ver)
    print("verifier: schema_guard wired next to check_freshness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
