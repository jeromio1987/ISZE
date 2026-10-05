# -*- coding: utf-8 -*-
"""Record the Tier A volume run and the part-number strictness fix."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parent
BOARD = R / "00_docs" / "agent" / "DELEGATOR_BOARD.md"

ROW = (
    "| 2026-10-01 17:40 | cursor (Tier A volume run + a false-match bug) | "
    "**Tier A read at volume, and a wrong-number bug caught doing it.** "
    "**(1) The run:** 1,246 pages fetched over 47 minutes across the 3 queryable shops "
    "(KS 487, Omega 487, Amayama 282 of 487 — the other 205 are clean 404s, Amayama does not "
    "stock them). Zero consent refusals. Parsed into the ledger through the existing manifest path: "
    "ledger **1,093 -> 1,944 rows, 133 -> 392 part numbers**. Tier A coverage: **21 of 491 parts "
    "carried a rival price this morning, 304 do now (62%)**, worth **EUR 11.55M of Tier A's "
    "EUR 21.31M (54.2%)**. "
    "**(2) A real false-match bug, found by the verbatim check.** The Omega parser emitted three "
    "Isuzu part numbers that were not on their pages: `0082213890` off a **Jeep Cherokee door mirror "
    "cover**, `3288026184` off a **VW Passat trim cover**, `7084775899` off a **VW Transporter window "
    "glass**. Cause: `normalise_pn` stripped EVERY non-digit, so Jeep's `00K82213890` lost its K and "
    "became ten digits, and VW's `3B2880261D84L` and `7E0-847-758-AA-9B9` did the same by accident. "
    "All three looked like clean Isuzu numbers and were Jeep/VW parts — the Mekonomen failure mode "
    "again, and it would have put three wrong prices against three real part numbers. "
    "`normalise_pn` is now strict: it removes only the separators a part number really carries "
    "(`-`, space, `.`, `/`) plus the recognised `ISU` prefix and `.UMI` suffix, and **refuses any "
    "other letter**. New `check_pn_strictness.py` pins 12 genuine shapes that must still pass and 12 "
    "competitor codes that must now be refused. Verbatim check: **892/892 clean** (was 894/904). "
    "**(3) A second classifier fix:** Amayama parts that exist but are out of stock carry no price; "
    "4 pages were being reported as broken. Out-of-stock is a real answer, not a fault. "
    "| `04_tools/delegation/parsers/ledger_schema.py`, `check_pn_strictness.py`, "
    "`04_tools/price_ledger/build_scraped_observations.py`, `page_manifest.csv`, "
    "`01_data/00_derived/price_observations.parquet` "
    "| Tier B is the next tier down (1,809 parts); the run cost 47 min and ~1 GB of cache. "
    "The two real price movements are still the only two, so a second pass now has value. |\n"
)


def main() -> int:
    lines = BOARD.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if any("Tier A volume run" in ln for ln in lines[:40]):
        print("row already present")
        return 0
    at = None
    for i, ln in enumerate(lines[:40]):
        if ln.startswith("| Time | Agent | What changed"):
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].lstrip().startswith("|---"):
                    at = j + 1
                    break
            break
    if at is None:
        print("FAIL — rows table not found")
        return 1
    lines.insert(at, ROW)
    BOARD.write_text("".join(lines), encoding="utf-8")
    print(f"inserted at line {at + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
