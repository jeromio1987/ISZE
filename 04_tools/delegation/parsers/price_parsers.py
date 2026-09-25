# -*- coding: utf-8 -*-
"""Compatibility shim — kept because `run_price_ledger_weekly.bat` calls
`price_parsers.py --selftest` and older notes reference `parse_amayama`.

The real parsers now live one per site:

    site_amayama.py   proven against a live page
    site_ks.py        KS International
    site_omega.py     Omega
    site_geparden.py  geparden.no
    site_mekster.py   mekster.no
    site_tungen.py    tungen-bil.no
    site_autoline.py  autoline.dk

Each exposes `SITE`, `PROBE_PAGE`, `parse()` and `selftest()`. `registry.py`
discovers them; `run_probe.py` parses every saved page without touching the network.

This file does NOT parse anything itself. It re-exports, so a caller that only knows
the old names keeps working, and `--selftest` now runs every site's selftest rather
than the one that used to be here.

Fetching is NOT done here either. If a caller needs to fetch, it goes through
`fetch_polite.py`, which runs the consent gate first (see that file).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.insert(0, str(HERE))

import registry                                                    # noqa: E402
from ledger_schema import COLUMNS, PRICE_TYPES, MATCH_METHODS      # noqa: E402,F401

# Old names kept working. Imported lazily so one broken site module cannot stop the
# others from being importable.
try:
    from site_amayama import parse as parse_amayama                # noqa: F401
except Exception:                                                  # noqa: BLE001
    parse_amayama = None


def parsers() -> dict:
    """{site_name: parse_function} for every site module that imports cleanly."""
    found = {}
    for name in registry.site_names():
        try:
            found[name] = registry.load(name).parse
        except Exception:                                          # noqa: BLE001
            continue
    return found


def selftest() -> int:
    """Every site's selftest. Non-zero if any fails."""
    rc = registry.all_selftests()
    print()
    print("Schema this package builds rows against:")
    print(f"  ledger COLUMNS      {len(COLUMNS)}")
    print(f"  ledger PRICE_TYPES  {len(PRICE_TYPES)}")
    print(f"  ledger MATCH_METHODS{sorted(MATCH_METHODS)}")
    return rc


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    print(__doc__)
    print(f"Sites found: {', '.join(registry.site_names()) or '(none)'}")
    print("\nUsage:")
    print("  python 04_tools/delegation/parsers/price_parsers.py --selftest")
    print("  python 04_tools/delegation/parsers/run_probe.py [--site <name>]")
