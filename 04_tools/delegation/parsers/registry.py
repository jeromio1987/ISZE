# -*- coding: utf-8 -*-
"""Parser registry — finds every `site_*.py` module in this folder.

Each site module exports `SITE`, `PROBE_PAGE`, `COUNTRY`, `parse()` and `selftest()`.
Adding a site means adding one file; nothing here needs editing.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def site_names() -> list[str]:
    """Every `site_<name>.py` in this folder, sorted."""
    return sorted(p.stem[len("site_"):] for p in HERE.glob("site_*.py"))


def load(name: str):
    """Import one site module. Raises ImportError with the real reason on failure."""
    return importlib.import_module(f"site_{name}")


def probe_path(module) -> Path:
    """Where the saved page for this site lives."""
    return PROBE / getattr(module, "PROBE_PAGE")


def probe_html(module) -> str | None:
    """The saved page text, or None if it is not on disk."""
    p = probe_path(module)
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def all_selftests() -> int:
    """Run every site's selftest. Non-zero if any fails."""
    names = site_names()
    if not names:
        print("no site_*.py modules found")
        return 1
    failures = []
    for n in names:
        print("\n" + "=" * 78)
        print(f"SELFTEST {n}")
        try:
            mod = load(n)
            rc = mod.selftest()
        except Exception as e:                                     # noqa: BLE001
            print(f"  EXCEPTION {type(e).__name__}: {e}")
            rc = 1
        if rc != 0:
            failures.append(n)
    print("\n" + "=" * 78)
    if failures:
        print(f"SELFTESTS FAILED: {failures}")
        return 1
    print(f"ALL SELFTESTS PASS ({len(names)} sites: {', '.join(names)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(all_selftests())
