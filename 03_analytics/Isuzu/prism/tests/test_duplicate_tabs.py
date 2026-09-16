"""Duplicate-tab trim — §8 item 2 + IA phase 3 merge (2026-08-20).

The duplicate tabs were dropped 2026-08-18; the 6 pages that carried them were
merged into `network_intelligence.py` 2026-08-20 (5_Insights, 5_Strategic,
12_Offset, 7_AIM_Review, 8_ASP_Monitor, 16_AIM_GPS_Matrix → pages/_archive/).
These assertions now target the merged page: the dropped/duplicated views must
NOT reappear there, and the surviving cross-links must be present.
"""

from __future__ import annotations

from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
PAGES = PRISM_ROOT / "pages"


def test_bvp_dropped_home_page_duplicates():
    src = (PAGES / "4_BVP.py").read_text(encoding="utf-8")
    assert '"PMS capture"' not in src
    assert '"GPS / SPU"' not in src
    assert '"AIM risk"' not in src
    assert "pages/3_PMS.py" in src
    assert "pages/2_GPS.py" in src


def test_network_intelligence_dropped_duplicates():
    """The merged page must not resurrect the dropped views."""
    src = (PAGES / "network_intelligence.py").read_text(encoding="utf-8")
    # BVP × Capture quadrant and basket-correlation are dropped/parked.
    assert "BVP × Capture" not in src
    assert "render_bvp_capture_quadrant" not in src
    assert "render_basket_correlation" not in src
    # Triple threat is superseded by Early Warning.
    assert "Most exposed (triple threat)" not in src
    assert "render_triple_threat" not in src
    # Surviving cross-link to the call list.
    assert "Early Warning" in src
