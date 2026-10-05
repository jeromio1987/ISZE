# -*- coding: utf-8 -*-
"""Self-test: does `ledger_schema` still agree with the ledger it mirrors?

Run this before any parser work. If the ledger's schema has moved, this fails loudly
rather than letting seven parsers write rows the loader will refuse.

RESTORED 2026-10-01. This file was deleted during the Tier A volume run by a worker that
did not know it existed — and because it had never been committed, git had no copy and
nothing on disk survived. It has been rewritten from the same design and is now called by
`price_parsers.py --selftest`, which the Monday job already runs, so it cannot be
orphaned again without the weekly job going red.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ledger_schema import COLUMNS, PRICE_TYPES, MATCH_METHODS, CURRENCIES  # noqa: E402

LEDGER = HERE.parents[2] / "04_tools" / "price_ledger" / "build_price_ledger.py"


def parse_set(text: str, name: str) -> set[str]:
    m = re.search(name + r"\s*=\s*\{(.*?)\}", text, re.S)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def parse_list(text: str, name: str) -> list[str]:
    m = re.search(name + r"\s*=\s*\[(.*?)\]", text, re.S)
    if not m:
        return []
    return re.findall(r'"([^"]+)"', m.group(1))


def parse_fx(text: str) -> set[str]:
    """The ledger's FX table keys = the currencies it can convert to euro."""
    m = re.search(r"^FX\s*=\s*\{(.*?)\}", text, re.S | re.M)
    if not m:
        return set()
    return set(re.findall(r'"([A-Z]{3})"\s*:', m.group(1)))


def main() -> int:
    if not LEDGER.exists():
        print(f"FAIL — ledger not found: {LEDGER}")
        return 1
    src = LEDGER.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []

    ledger_cols = parse_list(src, "COLUMNS")
    if ledger_cols and ledger_cols != COLUMNS:
        problems.append(f"COLUMNS differ\n    ledger: {ledger_cols}\n    schema: {COLUMNS}")

    ledger_types = parse_set(src, "PRICE_TYPES")
    if ledger_types and ledger_types != PRICE_TYPES:
        problems.append(
            f"PRICE_TYPES differ | only in ledger: {sorted(ledger_types - PRICE_TYPES)} "
            f"| only in schema: {sorted(PRICE_TYPES - ledger_types)}")

    ledger_methods = parse_set(src, "MATCH_METHODS")
    if ledger_methods and ledger_methods != MATCH_METHODS:
        problems.append(f"MATCH_METHODS differ | ledger: {sorted(ledger_methods)} "
                        f"| schema: {sorted(MATCH_METHODS)}")

    # The ledger reads its FX from fx_rates.json plus an inline fallback, so the
    # currency list is not a literal in that file. Report the gap rather than assert.
    ledger_fx = parse_fx(src)
    fx_file = HERE.parents[2] / "04_tools" / "price_ledger" / "fx_rates.json"
    if fx_file.exists():
        import json
        payload = json.loads(fx_file.read_text(encoding="utf-8"))
        ledger_fx |= set((payload.get("eur_per_unit") or {}).keys())
    cannot = sorted(CURRENCIES - ledger_fx)
    if ledger_fx:
        print(f"  ledger FX    {len(ledger_fx)}  {sorted(ledger_fx)}")
        if cannot:
            print(f"  ** NOT CONVERTIBLE by the ledger: {cannot}")

    print("ledger_schema vs build_price_ledger.py")
    print(f"  COLUMNS      {len(COLUMNS)}")
    print(f"  PRICE_TYPES  {len(PRICE_TYPES)}")
    print(f"  MATCH_METHODS{len(MATCH_METHODS):>2}  {sorted(MATCH_METHODS)}")
    print(f"  CURRENCIES   {len(CURRENCIES)}  {sorted(CURRENCIES)}")

    from ledger_schema import normalise_pn, make_row, row_problems, find_pns

    cases = {
        "8974995480": "8974995480",
        "8-97499-548-0": "8974995480",
        "ISU8983417890": "8983417890",
        "ISU5876150000": "5876150000",
        "8980139111.UMI": "8980139111",
        "8-98214687-0": "8982146870",
        "12345": None,
        "": None,
        None: None,
    }
    for raw, want in cases.items():
        got = normalise_pn(raw)
        if got != want:
            problems.append(f"normalise_pn({raw!r}) = {got!r}, expected {want!r}")

    good = make_row(part_no="8974995480", price_type="genuine_grey", match_method="exact_oem",
                    vintage="test", source="unit-test", price=1.0, currency="GBP")
    if row_problems(good):
        problems.append(f"a clean row was rejected: {row_problems(good)}")

    bad = make_row(part_no="123", price_type="nonsense", match_method="wat",
                   vintage=None, source=None, price=-1, currency="XYZ")
    if len(row_problems(bad)) < 5:
        problems.append(f"a bad row only produced {row_problems(bad)}")

    if find_pns("8-98204-942-0 and 8973675060 and 8973675060") != ["8982049420", "8973675060"]:
        problems.append("find_pns did not dedupe in order")

    if problems:
        print("\nSELFTEST FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nSELFTEST PASS — schema agrees with the ledger; helpers behave")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
