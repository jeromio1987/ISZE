# -*- coding: utf-8 -*-
"""The real Jeep/VW codes that were masquerading as Isuzu part numbers.

Every one of these was ACCEPTED by the old normalise_pn (strip all non-digits) and must
now be REFUSED, together with every genuine Isuzu shape that must still be accepted.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ledger_schema import normalise_pn                                   # noqa: E402

MUST_ACCEPT = {
    "8974995480": "8974995480",            # bare
    "8-97499-548-0": "8974995480",         # dashed
    "ISU8983417890": "8983417890",         # geparden slug prefix
    "ISU5876150000": "5876150000",
    "8980139111.UMI": "8980139111",        # savion suffix
    "8-98214687-0": "8982146870",          # tungen 1-8-1 grouping
    "8-97368-919-0": "8973689190",         # autoline
    "8 98204 942 0": "8982049420",         # space separated
    "05876150000": "5876150000",           # 11 digits with a leading zero
    "5876150021": "5876150021",            # a real short-form Isuzu number
    "1095833700": "1095833700",
    "0550047337": "0550047337",
}

MUST_REFUSE = {
    "00K82213890": "Jeep part from Omega: K removed would leave 10 digits",
    "K82213890": "Jeep part, lettered",
    "3B2880261D84L": "VW Passat part",
    "7E0-847-758-AA-9B9": "VW Transporter part",
    "3B2 880 261 D": "VW part with spaces",
    "0707723G": "KS internal SKU",
    "TP2268CL3533": "ClimAir sku",
    "LUCACP01114": "Lucas sku",
    "0011765K": "Omega aftermarket MPN",
    "12345": "too short",
    "": "empty",
    "8-98204-942-0-EXTRA": "trailing letters",
}

problems = []
print("MUST ACCEPT")
for raw, want in MUST_ACCEPT.items():
    got = normalise_pn(raw)
    ok = got == want
    print(f"   {'ok  ' if ok else 'FAIL'} {raw!r:<24} -> {got!r}  (expected {want!r})")
    if not ok:
        problems.append(f"{raw!r} -> {got!r}, expected {want!r}")

print("\nMUST REFUSE")
for raw, why in MUST_REFUSE.items():
    got = normalise_pn(raw)
    ok = got is None
    print(f"   {'ok  ' if ok else 'FAIL'} {raw!r:<24} -> {got!r}   ({why})")
    if not ok:
        problems.append(f"{raw!r} should be refused, got {got!r}")

print()
if problems:
    print(f"FAIL ({len(problems)})")
    for p in problems:
        print(f"   - {p}")
    raise SystemExit(1)
print("PASS — every genuine Isuzu shape accepted, every competitor code refused")
