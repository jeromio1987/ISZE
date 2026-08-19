"""
Smoke test — every registered page renders with zero exceptions.

Baseline for the IA restructure (docs/DASHBOARD_IA.md §6): run this against the
current 19-page layout first, then again after each merge phase to prove no
insight silently dropped. Uses real derived data (no mocks) — matches how the
app actually runs; a page that only breaks on real CSVs would pass a mocked test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PRISM_ROOT = Path(__file__).resolve().parent.parent

PAGES = sorted(
    p for p in (PRISM_ROOT / "pages").glob("*.py") if not p.name.startswith("_")
)

# Generous timeout — several pages load Excel/parquet on first cache miss.
RUN_TIMEOUT = 90.0


@pytest.mark.parametrize("page_path", [PRISM_ROOT / "app.py"] + PAGES, ids=lambda p: p.name)
def test_page_renders_without_exception(page_path: Path):
    at = AppTest.from_file(str(page_path), default_timeout=RUN_TIMEOUT)
    at.run(timeout=RUN_TIMEOUT)
    assert not at.exception, (
        f"{page_path.name} raised on initial render:\n"
        + "\n".join(f"  {e.value!r}" for e in at.exception)
    )
